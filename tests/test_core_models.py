import json
import sys
import unittest
import random
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.media_models import monthly_media, rolling_comparison
from sentiment_project.batch_coding import decode_batch
from sentiment_project.common import digest
import test_pipeline
from sentiment_project.common import read_jsonl, write_jsonl
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_core_corpus import round_robin


class CoreTests(unittest.TestCase):
    def test_audit_covers_all_months_before_extra_outlets(self):
        items = [{"id": str(n), "text": f"Unique item {n}", "source": f"outlet{n % 4}", "published_at": f"{2010 + (n // 4) // 12:04d}-{(n // 4) % 12 + 1:02d}-15T12:00:00Z"} for n in range(400)]
        selected = round_robin(items, 150, random.Random(12), set(), month_balanced=True)
        self.assertEqual(len(selected), 150)
        self.assertEqual({r["published_at"][:7] for r in selected}, {r["published_at"][:7] for r in items})
    def test_jsonl_unicode_separator_preserves_one_record(self):
        with test_pipeline.workspace_temp() as td:
            path = Path(td) / "unicode.jsonl"
            value = {"text": "A\u2028B\u0085C"}
            write_jsonl(path, [value])
            self.assertEqual(read_jsonl(path), [value])
    def test_late_discovery_cannot_enter_previous_month(self):
        item = {"id": "news1", "text": "US prices rose", "platform": "news", "source": "test", "published_at": "2020-01-31T10:00:00Z", "discovered_at": "2020-02-01T01:00:00Z"}
        label = {"id": item["id"], "label": {"us_relevance": "yes", "topics": ["prices"], "tone": "negative"}, "input_sha256": digest(item)}
        frame = monthly_media([item], [label], "2020-01", "2020-01")
        self.assertEqual(frame.iloc[0].news_candidate_n, 1)
        self.assertEqual(frame.iloc[0].news_eligible_n, 0)
        self.assertTrue(pd.isna(frame.iloc[0].news_tone))
        self.assertEqual(frame.iloc[0].target_month, "2020-02-01")

    def test_outlets_equal_weight_and_missing_not_zero(self):
        items, labels = [], []
        for n, (source, tone) in enumerate([("one", "negative"), ("one", "negative"), ("two", "positive")]):
            item = {"id": str(n), "text": str(n), "platform": "news", "source": source, "published_at": "2020-01-15T12:00:00Z"}
            items.append(item)
            labels.append({"id": item["id"], "input_sha256": digest(item), "label": {"us_relevance": "yes", "topics": ["prices"], "tone": tone}})
        frame = monthly_media(items, labels, "2020-01", "2020-02")
        self.assertEqual(frame.iloc[0].news_tone, 0)
        self.assertTrue(pd.isna(frame.iloc[1].news_tone))

    def test_current_scoring_target_does_not_change_forecast(self):
        rng = np.random.default_rng(12)
        dates = pd.date_range("2019-01-01", periods=50, freq="MS")
        frame = pd.DataFrame({"target_month": dates.strftime("%Y-%m-%d"), "information_cutoff": (dates - pd.Timedelta(days=1)).strftime("%Y-%m-%d"), "news_scored_n": 4, "twitter_scored_n": 10})
        for col in ["unemployment", "pce_yoy", "gdp_growth", "sentiment_available", "news_tone", "twitter_tone", "income_yoy"]:
            frame[col] = rng.normal(size=len(frame))
        targets = {d: float(rng.normal()) for d in frame.target_month}
        def labels(vintage):
            return {k: v for k, v in targets.items() if k < vintage}
        a, _, _ = rolling_comparison(frame, labels, targets, 24, "2021-01-01")
        changed = dict(targets)
        changed[frame.iloc[-1].target_month] = 99999
        b, _, _ = rolling_comparison(frame, labels, changed, 24, "2021-01-01")
        for col in ["M1_economic", "M2_add_media", "M3_add_household", "M2_add_media_empirical_low", "M2_add_media_empirical_high"]:
            self.assertEqual(a.iloc[-1][col], b.iloc[-1][col])
        self.assertTrue((a.latest_training_target < a.information_cutoff).all())

    def test_batch_missing_or_duplicate_ids_rejected(self):
        fixture = test_pipeline.MediaTests()
        item, label = fixture.item(), fixture.label()
        def response(values):
            return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"labels": values})}}]}
        self.assertEqual(len(decode_batch(response([label]), [item])), 1)
        with self.assertRaises(ValueError):
            decode_batch(response([]), [item])
        with self.assertRaises(ValueError):
            decode_batch(response([label, label]), [item])
        invalid = {**label, "evidence": ["An invented quote"]}
        result = decode_batch(response([invalid]), [item], allow_invalid=True)
        self.assertEqual(result[0]["label_status"], "invalid_model_response")
        self.assertIsNone(result[0]["label"])


if __name__ == "__main__":
    unittest.main()
