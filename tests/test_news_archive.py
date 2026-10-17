import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sentiment_project.news_archive import parse_gkg


class ArchiveTests(unittest.TestCase):
    def record(self, publication=None, url="https://www.npr.org/2020/test"):
        columns = [""] * 27
        columns[1], columns[3], columns[4] = "20200615160000", "npr.org", url
        columns[26] = "<PAGE_TITLE>US wages &amp; prices rise</PAGE_TITLE>"
        if publication:
            columns[26] += f"<PAGE_PRECISEPUBTIMESTAMP>{publication}</PAGE_PRECISEPUBTIMESTAMP>"
        return "\t".join(columns).encode()

    def parse(self, data):
        return parse_gkg(data, "https://example.test/archive.zip", "hash", "2026-10-16T00:00:00Z")[0]

    def test_missing_pub_not_replaced_with_discovery(self):
        row = self.parse(self.record())[0]
        self.assertIsNone(row["published_at"])
        self.assertEqual(row["publication_timestamp_status"], "missing_publication_timestamp")

    def test_future_and_stale_publication_flagged(self):
        self.assertEqual(self.parse(self.record("20200615170000"))[0]["publication_timestamp_status"], "publication_after_discovery")
        self.assertEqual(self.parse(self.record("20190615150000"))[0]["publication_timestamp_status"], "older_than_31_days")

    def test_valid_title_and_us_subject_not_assumed(self):
        row = self.parse(self.record("20200615150000"))[0]
        self.assertEqual(row["text"], "US wages & prices rise")
        self.assertEqual(row["us_relevance"], "unknown")

    def test_fake_domain_not_accepted(self):
        self.assertEqual(self.parse(self.record(url="https://npr.org.evil.test/test")), [])


if __name__ == "__main__":
    unittest.main()
