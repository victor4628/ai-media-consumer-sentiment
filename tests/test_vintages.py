import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sentiment_project.vintages import annual_change, latest_value, parse_snapshot, quarterly_annualized


class VintageTests(unittest.TestCase):
    def test_version_header_must_match(self):
        data = b"observation_date,PCEPI_20200430\n2020-01-01,110\n"
        with self.assertRaises(ValueError):
            parse_snapshot(data, "PCEPI", "2020-05-31")

    def test_future_observation_rejected(self):
        data = b"observation_date,PCEPI_20200430\n2020-05-01,110\n"
        with self.assertRaises(ValueError):
            parse_snapshot(data, "PCEPI", "2020-04-30")

    def test_yoy_is_same_snapshot_and_exact_calendar(self):
        a = {"2019-01-01": 100, "2020-01-01": 103}
        b = {"2019-01-01": 101, "2020-01-01": 106}
        self.assertAlmostEqual(annual_change(a, "2020-02-01")[1], 3)
        self.assertAlmostEqual(annual_change(b, "2020-02-01")[1], (106 / 101 - 1) * 100)
        with self.assertRaises(ValueError):
            annual_change({"2018-12-01": 100, "2020-01-01": 103}, "2020-02-01")

    def test_latest_does_not_take_target_month(self):
        self.assertEqual(latest_value({"2020-01-01": 100, "2020-02-01": 999}, "2020-02-01"), ("2020-01-01", 100))

    def test_quarterly_annualization_crosses_year(self):
        self.assertAlmostEqual(quarterly_annualized({"2019-10-01": 100, "2020-01-01": 101}, "2020-05-01")[1], (1.01 ** 4 - 1) * 100)


if __name__ == "__main__":
    unittest.main()
