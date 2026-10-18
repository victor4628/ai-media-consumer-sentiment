"""Protect reference denominators, calendar lags and multiplicity calculations."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from sentiment_project.rubric_extensions import (
    classification_metrics, measurement_group, holm_adjust, segment_bootstrap_indices,
    common_lag_panel, calendar_autocorrelation)


class RubricExtensionTests(unittest.TestCase):
    def test_absent_predictions_and_absent_classes_are_not_perfect_scores(self):
        result = classification_metrics(['negative', 'neutral'], ['negative', 'negative'],
                                        ['negative', 'neutral', 'positive'])
        self.assertIsNone(result['per_class']['neutral']['precision'])
        self.assertEqual(result['per_class']['neutral']['recall'], 0)
        self.assertEqual(result['per_class']['neutral']['F1'], 0)
        self.assertIsNone(result['per_class']['positive']['F1'])
        self.assertAlmostEqual(result['macro_F1_reference_supported'], 1/3)

    def test_missing_reference_is_retained_in_attempted_denominator(self):
        reference = {'a': {'label': None}, 'b': {'label': {'tone': 'neutral'}}}
        gpt = {'a': {'label': {'tone': 'negative'}}, 'b': {'label': {'tone': 'positive'}}}
        result = measurement_group(['a', 'b'], reference, gpt, ['tone'])
        self.assertEqual((result['attempted'], result['valid_pairs'], result['missing_pairs']), (2, 1, 1))
        self.assertEqual(result['dimensions']['tone']['agreement'], 0)

    def test_holm_adjustment_covers_whole_family(self):
        np.testing.assert_allclose(holm_adjust([.01, .04, .03]), [.03, .06, .06])

    def test_blocks_never_move_observations_across_calendar_segments(self):
        draws = segment_bootstrap_indices(['2020-01', '2020-02', '2020-06', '2020-07'], 80, 3, 42)
        self.assertTrue(np.isin(draws[:, :2], [0, 1]).all())
        self.assertTrue(np.isin(draws[:, 2:], [2, 3]).all())

    def test_lags_are_shifted_before_missing_coverage_is_filtered(self):
        panel = pd.DataFrame({'target_month': ['2020-02-01', '2020-03-01', '2020-04-01', '2020-05-01'],
                              'media_month': ['2020-01', '2020-02', '2020-03', '2020-04'],
                              'news_tone': [.1, .2, .3, .4], 'twitter_tone': [.5, .6, .7, .8],
                              'news_scored_n': [1, 0, 1, 1], 'twitter_scored_n': [3, 3, 3, 3]})
        result = common_lag_panel(panel, [1, 2, 3], 1, 3)
        self.assertEqual(result.loc[3, 'news_tone_lag3'], .2)
        self.assertFalse(result.loc[0, 'all_lags_covered'])
        self.assertFalse(result.loc[3, 'all_lags_covered'])
        with self.assertRaises(ValueError):
            common_lag_panel(panel.drop(index=1), [1, 2, 3], 1, 3)

    def test_autocorrelation_does_not_compress_missing_months(self):
        result = calendar_autocorrelation(['2020-01', '2020-02', '2020-05', '2020-06'], [1., 2., 3., 4.])
        self.assertEqual(result['calendar_adjacent_pairs'], 2)
        self.assertIsNone(result['lag1_correlation'])


if __name__ == '__main__':
    unittest.main()
