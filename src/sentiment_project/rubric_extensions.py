"""Transparent measurement and forecast diagnostics for the rubric extension."""
from collections import Counter
import numpy as np
import pandas as pd
from .ai_validation import ENUMS, TOPICS


def divide(numerator, denominator):
    return float(numerator / denominator) if denominator else None


def classification_metrics(reference, predicted, classes):
    if len(reference) != len(predicted) or not reference:
        raise ValueError('Classification requires nonempty paired observations')
    if not set(reference + predicted).issubset(set(classes)):
        raise ValueError('Unexpected class')
    matrix = [[sum(a == left and b == right for a, b in zip(reference, predicted))
               for right in classes] for left in classes]
    per_class = {}
    for index, label in enumerate(classes):
        tp = matrix[index][index]
        support, predicted_n = sum(matrix[index]), sum(row[index] for row in matrix)
        fp, fn = predicted_n - tp, support - tp
        per_class[label] = {'support': support, 'predicted_n': predicted_n, 'true_positive': tp,
                            'false_positive': fp, 'false_negative': fn,
                            'precision': divide(tp, tp + fp), 'recall': divide(tp, tp + fn),
                            'F1': divide(2 * tp, 2 * tp + fp + fn)}
    supported = [value for value in per_class.values() if value['support'] > 0]
    agreement = sum(a == b for a, b in zip(reference, predicted)) / len(reference)
    return {'n': len(reference), 'agreement': agreement, 'classes': list(classes),
            'confusion_matrix_rows_reference_columns_prediction': matrix, 'per_class': per_class,
            'macro_F1_reference_supported': float(np.mean([value['F1'] for value in supported])),
            'weighted_F1_reference_support': float(sum(value['support'] * value['F1'] for value in supported) / len(reference)),
            'scope': 'Performance relative to one owner-attested human reference; not consensus truth accuracy. Undefined precision/recall/F1 remain null.'}


def measurement_group(ids, reference, gpt, dimensions=None):
    paired = [item_id for item_id in ids if reference[item_id]['label'] is not None
              and gpt[item_id]['label'] is not None]
    result = {'attempted': len(ids), 'valid_pairs': len(paired), 'missing_pairs': len(ids) - len(paired),
              'dimensions': {}}
    for dimension in dimensions or ENUMS:
        result['dimensions'][dimension] = classification_metrics(
            [reference[item_id]['label'][dimension] for item_id in paired],
            [gpt[item_id]['label'][dimension] for item_id in paired], ENUMS[dimension]) if paired else None
    if paired and dimensions is None:
        topics = {}
        for topic in sorted(TOPICS):
            metrics = classification_metrics(
                [str(topic in reference[item_id]['label']['topics']) for item_id in paired],
                [str(topic in gpt[item_id]['label']['topics']) for item_id in paired], ['False', 'True'])
            topics[topic] = metrics['per_class']['True']
        tp, fp, fn = [sum(value[key] for value in topics.values())
                      for key in ['true_positive', 'false_positive', 'false_negative']]
        supported = [value['F1'] for value in topics.values() if value['support'] > 0]
        result['multilabel_topics'] = {
            'per_topic': topics, 'micro_F1': divide(2 * tp, 2 * tp + fp + fn),
            'macro_F1_reference_supported': float(np.mean(supported)) if supported else None,
            'exact_set_agreement': sum(set(reference[item_id]['label']['topics']) == set(gpt[item_id]['label']['topics'])
                                       for item_id in paired) / len(paired)}
    return result


def holm_adjust(p_values):
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values, kind='stable')
    adjusted = np.empty(len(values))
    running = 0.
    for rank, index in enumerate(order):
        running = max(running, (len(values) - rank) * values[index])
        adjusted[index] = min(1., running)
    return adjusted.tolist()


def segment_bootstrap_indices(months, repetitions, block, seed):
    periods = pd.PeriodIndex(pd.to_datetime(months), freq='M').asi8
    if len(periods) == 0 or np.any(np.diff(periods) <= 0):
        raise ValueError('Unique sorted nonempty calendar months required')
    segments = np.split(np.arange(len(periods)), np.where(np.diff(periods) != 1)[0] + 1)
    rng = np.random.default_rng(seed)
    draws = []
    for segment in segments:
        length = len(segment)
        width = min(block, max(1, length // 2))
        starts = rng.integers(0, length, size=(repetitions, int(np.ceil(length / width))))
        indices = ((starts[:, :, None] + np.arange(width)) % length).reshape(repetitions, -1)[:, :length]
        draws.append(segment[indices])
    return np.concatenate(draws, axis=1)


def common_lag_panel(panel, lags, min_news, min_x):
    result = panel.sort_values('target_month').copy().reset_index(drop=True)
    periods = pd.PeriodIndex(pd.to_datetime(result.target_month), freq='M')
    if len(periods) > 1 and not np.all(np.diff(periods.asi8) == 1):
        raise ValueError('Shift media on the complete calendar grid, before filtering')
    news_counts, x_counts = [], []
    for lag in lags:
        offset = lag - 1  # Existing row already refers to preceding-month media.
        for field in ['news_tone', 'twitter_tone']:
            result[f'{field}_lag{lag}'] = result[field].shift(offset)
        result[f'media_month_lag{lag}'] = result.media_month.shift(offset)
        news_counts.append(result.news_scored_n.shift(offset))
        x_counts.append(result.twitter_scored_n.shift(offset))
    # skipna=False prevents missing early lags from passing coverage.
    result['news_scored_n'] = pd.concat(news_counts, axis=1).min(axis=1, skipna=False)
    result['twitter_scored_n'] = pd.concat(x_counts, axis=1).min(axis=1, skipna=False)
    result['all_lags_covered'] = (result.news_scored_n >= min_news) & (result.twitter_scored_n >= min_x)
    return result


def calendar_autocorrelation(months, values):
    periods = pd.PeriodIndex(pd.to_datetime(months), freq='M').asi8
    lookup = dict(zip(periods, values))
    pairs = [(lookup[period - 1], value) for period, value in zip(periods, values) if period - 1 in lookup]
    coefficient = None
    if len(pairs) >= 3:
        left, right = np.array(pairs).T
        if left.std() > 0 and right.std() > 0:
            coefficient = float(np.corrcoef(left, right)[0, 1])
    return {'calendar_adjacent_pairs': len(pairs), 'lag1_correlation': coefficient,
            'scope': 'Descriptive correlation only; absent calendar months are not treated as adjacent.'}
