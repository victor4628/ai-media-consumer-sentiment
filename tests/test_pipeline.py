import json
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.ai_validation import categorical_agreement, classify, compare_labels, validate_items, validate_label, usage_cost_upper_estimate, normalize_response_label
from sentiment_project.baseline import diagnostic_panel, rolling_baseline
from sentiment_project.common import digest
from sentiment_project.corpus import prepare_audit
from sentiment_project.temporal import pce_yoy_as_of, snapshot_as_of
from sentiment_project.twitter import collect_pilot, make_query, normalize_tweet


@contextmanager
def workspace_temp():
    base = (ROOT / "tmp/tests").resolve()
    if not base.is_relative_to(ROOT.resolve()):
        raise ValueError("Temporary test directory escapes workspace")
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=base) as path:
        if not Path(path).resolve().is_relative_to(base):
            raise ValueError("Unsafe temporary path")
        yield path


class TemporalTests(unittest.TestCase):
    def rows(self):
        return pd.DataFrame([
            {"series_id": "pce_index", "period_end": "2020-01-31", "value": 100, "release_date": "2020-02-28", "vintage_date": "2020-02-28", "source_url": "https://example.test/source"},
            {"series_id": "pce_index", "period_end": "2021-01-31", "value": 103, "release_date": "2021-02-26", "vintage_date": "2021-02-26", "source_url": "https://example.test/source"},
            {"series_id": "pce_index", "period_end": "2021-01-31", "value": 110, "release_date": "2021-02-26", "vintage_date": "2021-06-25", "source_url": "https://example.test/source"},
        ])

    def test_future_revision_excluded(self):
        self.assertAlmostEqual(pce_yoy_as_of(self.rows(), "2021-03-01", "2021-01"), 3)
        self.assertAlmostEqual(pce_yoy_as_of(self.rows(), "2021-07-01", "2021-01"), 10)

    def test_unreleased_period_excluded(self):
        self.assertIsNone(pce_yoy_as_of(self.rows(), "2021-02-01", "2021-01"))

    def test_unknown_vintage_rejected(self):
        rows = self.rows()
        rows["vintage_date"] = ""
        with self.assertRaises(ValueError):
            snapshot_as_of(rows, "2021-03-01")

    def test_missing_month_not_previous_row(self):
        rows = []
        for sid in ["sentiment", "unemployment", "pce_yoy"]:
            for d in ["2020-01-31", "2020-03-31", "2020-04-30"]:
                rows.append({"series_id": sid, "period_end": d, "value": 10})
        rows.append({"series_id": "gdp_growth", "period_end": "2019-12-31", "value": 2})
        panel = diagnostic_panel(pd.DataFrame(rows), "2020-04", "2020-05-16")
        self.assertTrue(pd.isna(panel.iloc[0].unemployment))
        self.assertEqual(panel.iloc[0].gdp_growth, 2)

    def test_gdp_not_known_at_quarter_end(self):
        rows = [{"series_id": s, "period_end": "2020-01-31", "value": 1} for s in ["sentiment", "unemployment", "pce_yoy"]]
        rows += [{"series_id": "gdp_growth", "period_end": "2019-12-31", "value": 2}, {"series_id": "gdp_growth", "period_end": "2020-03-31", "value": -5}]
        panel = diagnostic_panel(pd.DataFrame(rows), "2020-04", "2020-05-16")
        self.assertEqual(panel.iloc[0].gdp_growth, 2)

    def test_current_target_does_not_change_prediction_or_band(self):
        rng = np.random.default_rng(8)
        frame = pd.DataFrame({"period_end": pd.date_range("2010-01-31", periods=140, freq="ME"),
                              "sentiment": rng.normal(90, 10, 140), "persistence": rng.normal(90, 10, 140),
                              "unemployment": rng.normal(5, 1, 140), "pce_yoy": rng.normal(2, 1, 140), "gdp_growth": rng.normal(2, 2, 140)})
        a = rolling_baseline(frame, "2015-01-01")
        frame.loc[139, "sentiment"] = 99999
        b = rolling_baseline(frame, "2015-01-01")
        for field in ["economic_prediction", "empirical_low", "empirical_high"]:
            self.assertEqual(a.iloc[-1][field], b.iloc[-1][field])


class MediaTests(unittest.TestCase):
    def item(self, id="test"):
        return {"id": id, "text": "US inflation is 3 percent.", "published_at": "2026-01-15T10:00:00+00:00", "platform": "news", "source": "synthetic_test"}

    def label(self):
        return {"id": "test", "tone": "neutral", "language_style": "factual", "topics": ["prices"], "price_frame": "changes", "scope_frame": "national", "time_frame": "current", "factual_calibration": "not_checkable", "political_attribution": "none", "us_relevance": "yes", "evidence": ["US inflation is 3 percent."], "rationale": "No official evidence supplied."}

    def test_unsupported_fact_verdict_rejected(self):
        label = self.label()
        label["factual_calibration"] = "matches"
        with self.assertRaises(ValueError):
            validate_label(label, self.item())

    def test_invented_quote_rejected(self):
        label = self.label()
        label["evidence"] = ["inflation is zero"]
        with self.assertRaises(ValueError):
            validate_label(label, self.item())

    def test_agreement_not_accuracy(self):
        result = categorical_agreement(["negative", "positive"], ["positive", "negative"])
        self.assertEqual(result["agreement"], 0)
        self.assertEqual(result["kappa"], -1)
        self.assertIsNone(categorical_agreement(["neutral"], ["neutral"])["kappa"])

    def test_quote_html_entities_are_representation_only(self):
        item = {**self.item(), "text": "Wages &amp; prices rose."}
        label = {**self.label(), "evidence": ["Wages & prices rose."]}
        self.assertEqual(validate_label(label, item), label)
        label["evidence"] = ["Wages and prices rose."]
        with self.assertRaises(ValueError):
            validate_label(label, item)

    def test_display_bounds_do_not_change_labels_or_repair_invented_quotes(self):
        item = {**self.item(), "text": "A" * 200}
        raw = {**self.label(), "evidence": ["A" * 180], "rationale": "x" * 600}
        bounded, changes = normalize_response_label(raw, item)
        self.assertEqual(bounded["tone"], raw["tone"])
        self.assertEqual(len(bounded["evidence"][0]), 160)
        self.assertEqual(len(bounded["rationale"]), 400)
        self.assertEqual(len(changes), 2)
        self.assertEqual(len(raw["rationale"]), 600)
        raw["evidence"] = ["B" * 180]
        with self.assertRaises(ValueError):
            normalize_response_label(raw, item)

    def test_quote_case_restored_only_from_unique_literal_span(self):
        item = {**self.item(), "text": "He mentioned rising prices."}
        label = {**self.label(), "evidence": ["he mentioned rising prices."]}
        normalized, changes = normalize_response_label(label, item)
        self.assertEqual(normalized["evidence"], [item["text"]])
        self.assertIn("literal_excerpt_case_restored_from_source", changes)
        with self.assertRaises(ValueError):
            normalize_response_label({**label, "evidence": ["he mentioned falling prices."]}, item)

    def test_twitter_stops_paging_all_invalid_dates(self):
        with workspace_temp() as td:
            root = Path(td)
            (root / "configs").mkdir()
            cfg = json.loads((ROOT / "configs/twitter_pilot.json").read_text(encoding="utf-8"))
            cfg.update(windows=[{"since": "2026-01-01", "until": "2026-01-02"}], max_pages_per_window=8, request_delay_seconds=0)
            (root / "configs/twitter_pilot.json").write_text(json.dumps(cfg), encoding="utf-8")
            calls = []
            def fake(url, params, key):
                calls.append(params)
                return {"tweets": [{"id": "1", "text": "Wrong date", "createdAt": "2026-01-03T05:00:00Z"}], "has_next_page": True, "next_cursor": "page2"}
            with patch.dict("os.environ", {"TWITTERAPI_IO_KEY": "synthetic_test_key"}):
                result = collect_pilot(True, 1, root, fake)
            self.assertEqual(len(calls), 1)
            self.assertEqual(result["unique_valid_posts"], 0)
            self.assertEqual(result["windows"][0]["status"], "invalid_page_stopped_before_more_paid_requests")

    def test_missing_label_rejected(self):
        row = {"id": "test", "label": self.label(), "input_sha256": digest(self.item())}
        with self.assertRaises(ValueError):
            compare_labels([row], [])

    def test_label_dry_run_no_network(self):
        def bad(*args):
            self.fail("Dry run made a network request")
        result = classify([self.item()], "A", fetch=bad)
        self.assertEqual(result["network_calls"], 0)

    def test_live_label_cache_avoids_duplicate_billing(self):
        with workspace_temp() as td:
            root = Path(td)
            (root / "configs").mkdir()
            (root / "prompts").mkdir()
            (root / "configs/deepseek.json").write_bytes((ROOT / "configs/deepseek.json").read_bytes())
            (root / "prompts/economic_coding_v1.txt").write_bytes((ROOT / "prompts/economic_coding_v1.txt").read_bytes())
            calls = []
            def fake(payload, key, url):
                calls.append(payload)
                return {"model": "test_model", "usage": {"total_tokens": 30}, "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(self.label())}}]}
            with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "synthetic_test_key"}):
                a = classify([self.item()], "A", True, 1, root, fake)
                b = classify([self.item()], "A", True, 1, root, fake)
                changed_metadata = {**self.item(), "retrieved_at": "2026-10-16T12:00:00Z"}
                c = classify([changed_metadata], "A", True, 1, root, fake)
            self.assertEqual(len(calls), 1)
            self.assertEqual(a["output"], b["output"])
            self.assertEqual(b["estimated_new_reserved_usd"], 0)
            current = json.loads(Path(c["output"]).read_text(encoding="utf-8").strip())
            self.assertEqual(current["input_sha256"], digest(changed_metadata))
            self.assertEqual(current["cached_call_input_sha256"], digest(self.item()))

    def test_live_label_budget_stops_before_network(self):
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "synthetic_test_key"}):
            def fake(*args):
                self.fail("Insufficient budget must stop before a paid call")
            with self.assertRaises(ValueError):
                classify([self.item("never_call_test")], "A", True, 0.000001, fetch=fake)

    def test_schema_repair_is_once_and_cached(self):
        with workspace_temp() as td:
            root = Path(td)
            (root / "configs").mkdir()
            (root / "prompts").mkdir()
            (root / "configs/deepseek.json").write_bytes((ROOT / "configs/deepseek.json").read_bytes())
            (root / "prompts/economic_coding_v1.txt").write_bytes((ROOT / "prompts/economic_coding_v1.txt").read_bytes())
            calls = []
            def fake(payload, key, url):
                calls.append(payload)
                label = self.label()
                if len(calls) == 1:
                    label["evidence"] = []
                return {"model": "test_model", "usage": {"prompt_tokens": 100, "completion_tokens": 50}, "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(label)}}]}
            with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "synthetic_test_key"}):
                result = classify([self.item()], "A", True, 1, root, fake)
                resumed = classify([self.item()], "A", True, 1, root, fake)
            self.assertEqual(len(calls), 2)
            self.assertEqual(resumed["estimated_new_cost_upper_usd"], 0)
            row = json.loads(Path(result["output"]).read_text(encoding="utf-8").strip())
            self.assertIn("one_schema_repair_call", row["format_adjustments"])
            cache = [json.loads(p.read_text(encoding="utf-8")) for p in (root / "labels/runs/cache").glob("*.json")]
            self.assertEqual(len(cache), 2)
            self.assertEqual(sum(r["estimated_cost_upper_usd"] for r in cache), result["estimated_new_cost_upper_usd"])

    def test_usage_cost_ignores_discounts_conservatively(self):
        cfg = {"input_usd_per_million": {"m": 1}, "output_usd_per_million": {"m": 2}}
        response = {"usage": {"prompt_tokens": 1000, "completion_tokens": 500, "prompt_cache_hit_tokens": 1000}}
        self.assertEqual(usage_cost_upper_estimate(response, cfg, "m", 0.1), 0.002)
        self.assertEqual(usage_cost_upper_estimate({}, cfg, "m", 0.1), 0.1)

    def test_twitter_cache_and_pagination(self):
        with workspace_temp() as td:
            root = Path(td)
            (root / "configs").mkdir()
            cfg = json.loads((ROOT / "configs/twitter_pilot.json").read_text(encoding="utf-8"))
            cfg["windows"] = [{"since": "2026-01-01", "until": "2026-01-02"}]
            cfg["request_delay_seconds"] = 0
            cfg["max_pages_per_window"] = 2
            (root / "configs/twitter_pilot.json").write_text(json.dumps(cfg), encoding="utf-8")
            calls = []
            def fake(url, params, key):
                calls.append(params["cursor"])
                tweet = {"id": "1", "text": "Synthetic economic test text.", "createdAt": "2026-01-01T05:00:00Z"}
                return {"tweets": [tweet], "has_next_page": not bool(params["cursor"]), "next_cursor": "page2"}
            with patch.dict("os.environ", {"TWITTERAPI_IO_KEY": "synthetic_test_key"}):
                first = collect_pilot(True, 1, root, fake)
                second = collect_pilot(True, 1, root, fake)
            self.assertEqual(calls, ["", "page2"])
            self.assertEqual(first["unique_valid_posts"], 1)
            self.assertEqual(second["new_requests"], 0)
            self.assertAlmostEqual(first["estimated_total_cached_and_new_usd"], 0.0003)

    def test_twitter_date_boundary(self):
        window = {"since": "2026-01-01", "until": "2026-01-02"}
        tweet = {"id": "1", "text": "example", "createdAt": "2026-01-02T00:00:00Z"}
        with self.assertRaises(ValueError):
            normalize_tweet(tweet, window, "2026-10-16")
        tweet["createdAt"] = "2026-01-01T00:00:00Z"
        self.assertEqual(normalize_tweet(tweet, window, "2026-10-16")["id"], "twitter:1")

    def test_twitter_invalid_window(self):
        with self.assertRaises(ValueError):
            make_query({"query": "economy"}, {"since": "2026-01-01", "until": "2026-01-01"})

    def test_twitter_epoch_query_uses_utc(self):
        query = make_query({"query": "economy"}, {"since": "1970-01-02", "until": "1970-01-03"})
        self.assertEqual(query, "economy since_time:86400 until_time:172800")

    def test_pilot_dry_run_no_network(self):
        def bad(*args):
            self.fail("Dry run made a network request")
        self.assertEqual(collect_pilot(fetch=bad)["network_calls"], 0)

    def test_sampling_fails_on_insufficient_real_texts(self):
        with workspace_temp() as td:
            with self.assertRaises(ValueError):
                prepare_audit([self.item()], td)

    def test_frozen_audit_disjoint_groups(self):
        items = [{**self.item(str(i)), "text": f"Synthetic test text number {i}.", "platform": "news" if i % 2 else "twitter"} for i in range(310)]
        with workspace_temp() as td:
            prepare_audit(items, td)
            manifest = json.loads((Path(td) / "manifest.json").read_text(encoding="utf-8"))
            dev = {r["group"] for r in manifest["items"] if r["split"] == "development"}
            audit = {r["group"] for r in manifest["items"] if r["split"] == "audit"}
            self.assertFalse(dev & audit)
            self.assertEqual(len(dev), 100)
            self.assertEqual(len(audit), 200)
            with self.assertRaises(ValueError):
                prepare_audit(items, td)


if __name__ == "__main__":
    unittest.main()
