"""Reproduce the four rubric additions without changing primary labels or forecasts."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from sentiment_project.common import read_json, read_jsonl, write_json
from sentiment_project.rubric_extensions import (
    classification_metrics, measurement_group, holm_adjust, segment_bootstrap_indices,
    common_lag_panel, calendar_autocorrelation)
import analyze_gpt_core_v3 as a

OUT = ROOT/'reports/rubric_extension'
DATA = ROOT/'data/processed/rubric_extension'
SHARE = ROOT/'data/shareable/rubric_extension'
CFG = read_json(ROOT/'configs/rubric_extension.json')


def hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare_event_manifest():
    """One-time local export of source links; no full headlines, quotes or authors."""
    corpus = {item['id']: item for item in read_jsonl(ROOT/'data/private/core_v1/corpus.jsonl')}
    metadata = {item['id']: item for item in read_jsonl(ROOT/'data/shareable/gpt_core_v3/corpus_metadata.jsonl')}
    rows = []
    for event in read_json(SHARE/'events.json')['events']:
        for member in event.get('members', []):
            item = corpus[member['item_id']]
            rows.append({**member, 'event_id': event['id'],
                         **{key: item[key] for key in ['source', 'url', 'published_at']},
                         'original_input_sha256': metadata[item['id']]['original_input_sha256']})
    write_json(SHARE/'matched_items.json', {
        'scope': 'Curated event membership and paraphrases, not raw headlines; no new semantic labels.',
        'items': rows})


def measurement(items, labels):
    reference = {row['id']: row for row in read_jsonl(ROOT/'data/shareable/human_reference/labels_300.jsonl')}
    splits = read_json(ROOT/'data/shareable/audit_splits.json')
    index = {item['id']: item for item in items}
    result = {'version': CFG['version'], 'scope': CFG['reference'],
              'zero_division': None, 'macro_class_rule': CFG['classification']['macro_F1_classes'], 'splits': {}}
    class_rows, source_rows = [], []
    for split in ['all_300', 'development_100', 'held_out_200']:
        ids = splits[split]
        group = measurement_group(ids, reference, labels)
        group['by_platform'] = {
            platform: measurement_group([item_id for item_id in ids if index[item_id]['platform'] == platform], reference, labels)
            for platform in ['news', 'twitter']}
        group['by_source'] = {}
        for source in sorted({index[item_id]['source'] for item_id in ids}):
            members = [item_id for item_id in ids if index[item_id]['source'] == source]
            detail = measurement_group(members, reference, labels, ['tone', 'language_style'])
            detail['small_sample'] = detail['valid_pairs'] < CFG['classification']['small_source_n']
            group['by_source'][source] = detail
            tone = detail['dimensions']['tone']
            source_rows.append({'split': split, 'source': source, 'attempted': detail['attempted'],
                                'n': detail['valid_pairs'], 'small_sample': detail['small_sample'],
                                'tone_agreement': tone['agreement'] if tone else None,
                                'tone_macro_F1': tone['macro_F1_reference_supported'] if tone else None})
        result['splits'][split] = group
        for group_name, detail in [('all', group), *group['by_platform'].items()]:
            for dimension, metrics in detail['dimensions'].items():
                if metrics:
                    for category, values in metrics['per_class'].items():
                        class_rows.append({'split': split, 'group': group_name, 'dimension': dimension,
                                           'category': category, **values})
    dictionary = {row['id']: row for row in read_jsonl(ROOT/'data/shareable/gpt_core_v3/dictionary_scores.jsonl')}
    comparison = {}
    for split in ['all_300', 'held_out_200']:
        comparison[split] = {}
        for platform in ['all', 'news', 'twitter']:
            candidates = [item_id for item_id in splits[split] if platform == 'all' or index[item_id]['platform'] == platform]
            ids = [item_id for item_id in candidates if item_id in dictionary and reference[item_id]['label'] is not None
                   and reference[item_id]['label']['tone'] in ['negative', 'neutral', 'positive', 'mixed']
                   and labels[item_id]['label']['tone'] in ['negative', 'neutral', 'positive', 'mixed']]
            convert = lambda value: 'neutral' if value == 'mixed' else value
            truth = [convert(reference[item_id]['label']['tone']) for item_id in ids]
            detail = {'n': len(ids), 'candidate_n': len(candidates), 'excluded_n': len(candidates) - len(ids), 'paired_ids': ids}
            for method in ['GPT', 'dictionary']:
                predicted = ([convert(labels[item_id]['label']['tone']) for item_id in ids] if method == 'GPT'
                             else [dictionary[item_id]['dictionary_tone'] for item_id in ids])
                detail[method] = classification_metrics(truth, predicted, ['negative', 'neutral', 'positive']) if ids else None
            comparison[split][platform] = detail
    result['dictionary_same_item_comparison'] = {
        'rule': CFG['classification']['dictionary_comparison'], 'results': comparison,
        'limitation': 'Eligible-text subset; excluded uncertain references and missing dictionary rows change the estimand. This does not validate the dictionary or establish population accuracy.'}
    pd.DataFrame(class_rows).to_csv(DATA/'classification_by_class.csv', index=False)
    pd.DataFrame(source_rows).to_csv(DATA/'classification_by_source.csv', index=False)
    return result


def event_comparison(items, labels):
    index = {item['id']: item for item in items}
    matched = read_json(SHARE/'matched_items.json')['items']
    events = []
    for event in read_json(SHARE/'events.json')['events']:
        if not event.get('members'):
            continue
        rows = []
        for member in matched:
            if member['event_id'] != event['id']:
                continue
            item_id = member['item_id']
            meta, label = index[item_id], labels[item_id]['label']
            assert member['original_input_sha256'] == meta['original_input_sha256']
            assert pd.Timestamp(member['published_at']) >= pd.Timestamp(event['release_utc'])
            assert member['published_at'][:10] == event['date']
            assert a.eligibility(meta, label)
            rows.append({**member, 'primary_eligible': True,
                         'minutes_after_release_metadata': (pd.Timestamp(member['published_at']) - pd.Timestamp(event['release_utc'])).total_seconds() / 60,
                         'tone': label['tone'], 'language_style': label['language_style'],
                         'price_frame': label['price_frame'], 'political_attribution': label['political_attribution']})
        focal = [row for row in rows if row['comparison_role'] == 'straight_news']
        assert len(focal) >= 2 and len({row['source'] for row in focal}) >= 2
        events.append({**event, 'items': rows, 'straight_news_n': len(focal),
                       'tone_differs': len({row['tone'] for row in focal}) > 1,
                       'style_differs': len({row['language_style'] for row in focal}) > 1})
    return {'scope': CFG['same_event'], 'events': events, 'event_n': len(events),
            'straight_news_n': sum(event['straight_news_n'] for event in events),
            'context_only_n': sum(len(event['items']) - event['straight_news_n'] for event in events),
            'tone_differing_events': sum(event['tone_differs'] for event in events),
            'style_differing_events': sum(event['style_differs'] for event in events),
            'inference': 'Release-matched descriptive cases, not identical-fact randomized contrasts or a population estimate of bias. Different facets, publication timing, syndication and genre may explain differences; no source ranking or causal effect is estimated.'}


def stability():
    spec = CFG['forecast']
    panel = pd.read_csv(ROOT/'data/processed/gpt_core_v3/model_panel.csv')
    primary = pd.read_csv(ROOT/'data/processed/gpt_core_v3/predictions.csv')
    analysis = read_json(ROOT/'reports/gpt_core_v3/analysis.json')
    models = a.model_specs()
    lag_panel = common_lag_panel(panel, spec['media_lags_months'], spec['minimum_news_each_lag'], spec['minimum_X_each_lag'])
    lag_models = {'baseline': models[spec['baseline']]}
    for lag in spec['media_lags_months']:
        lag_models[f'media_lag{lag}'] = lag_models['baseline'] + [f'news_tone_lag{lag}', f'twitter_tone_lag{lag}']
    forecasts, _, valid = a.forecast(lag_panel, lag_models, spec['minimum_news_each_lag'], spec['minimum_X_each_lag'])
    assert not forecasts.empty
    for lag in spec['media_lags_months']:
        selected = lag_panel[lag_panel.target_month.isin(valid.target_month)]
        assert all(pd.Period(row[f'media_month_lag{lag}'], freq='M') + lag == pd.Period(row['target_month'], freq='M')
                   for _, row in selected.iterrows())
    forecasts.to_csv(DATA/'common_lag_predictions.csv', index=False)
    lag_panel.to_csv(DATA/'common_lag_panel.csv', index=False)
    lag_results = {'eligible_n': len(valid), 'n': len(forecasts), 'training_history_rule': spec['comparison'],
                   'test_start': forecasts.target_month.min(), 'test_end': forecasts.target_month.max(),
                   'metrics': a.metrics(forecasts, ['persistence', *lag_models]),
                   'media_increments': {f'media_lag{lag}': a.comparison(forecasts, f'media_lag{lag}', 'baseline') for lag in spec['media_lags_months']}}
    coefficients = pd.read_csv(ROOT/'data/processed/gpt_core_v3/coefficients.csv')
    paths, summaries = [], []
    for model in ['economy_tone', 'memory_tone', 'household_tone', 'method_controls_tone']:
        subset = coefficients[coefficients.model == model].sort_values('target_month')
        for feature in ['news_tone', 'twitter_tone']:
            values = subset[feature].to_numpy()
            nonzero = np.sign(values[np.abs(values) > 1e-12])
            summaries.append({'model': model, 'feature': feature, 'n': len(values),
                              'minimum': float(values.min()), 'median': float(np.median(values)), 'maximum': float(values.max()),
                              'positive_share': float(np.mean(values > 1e-12)),
                              'sign_changes_between_observed_origins': int(np.sum(nonzero[1:] != nonzero[:-1]))})
            paths += [{'target_month': row.target_month, 'model': model, 'feature': feature, 'standardized_coefficient': float(row[feature])}
                      for _, row in subset.iterrows()]
    pd.DataFrame(paths).to_csv(DATA/'coefficient_paths.csv', index=False)
    period_results = {}
    for name, subset in [('before_2025', primary[primary.target_month < spec['period_split']]),
                         ('from_2025', primary[primary.target_month >= spec['period_split']])]:
        period_results[name] = {'metrics': a.metrics(subset, ['persistence', 'method_controls', 'method_controls_tone']),
                                'media_increment': a.comparison(subset, 'method_controls_tone', 'method_controls')}
    period_results['by_year'] = {year: {'metrics': a.metrics(subset, ['persistence', 'method_controls', 'method_controls_tone']),
                                       'media_increment': a.comparison(subset, 'method_controls_tone', 'method_controls')}
                                 for year, subset in primary.groupby(primary.target_month.str[:4])}
    block_results = []
    for block in spec['bootstrap_blocks']:
        draws = segment_bootstrap_indices(primary.target_month, spec['bootstrap_repetitions'], block, spec['seed'])
        for left, right in [('method_controls_tone', 'method_controls'), ('method_controls_tone', 'persistence')]:
            delta = (primary[left] - primary.actual).abs().to_numpy() - (primary[right] - primary.actual).abs().to_numpy()
            means = delta[draws].mean(axis=1)
            block_results.append({'left': left, 'right': right, 'block_months_requested': block,
                                  'n': len(primary), 'MAE_difference': float(delta.mean()),
                                  'nominal_interval': np.quantile(means, [.025, .975]).tolist()})
    draws = segment_bootstrap_indices(primary.target_month, spec['bootstrap_repetitions'], 3, spec['seed'])
    comparisons = []
    for pair in sorted(analysis['increments']):
        left, right = pair.split('_vs_')
        delta = (primary[left] - primary.actual).abs().to_numpy() - (primary[right] - primary.actual).abs().to_numpy()
        observed = float(delta.mean())
        null_means = delta[draws].mean(axis=1) - observed
        p_value = (1 + np.sum(np.abs(null_means) >= abs(observed))) / (len(draws) + 1)
        comparisons.append({'comparison': pair, 'MAE_difference': observed, 'bootstrap_p_two_sided': float(p_value)})
    for row, corrected in zip(comparisons, holm_adjust([row['bootstrap_p_two_sided'] for row in comparisons])):
        row['Holm_adjusted_p'] = corrected
    residuals = {'method_controls_tone_error': (primary.method_controls_tone - primary.actual).to_numpy(),
                 'method_controls_error': (primary.method_controls - primary.actual).to_numpy(),
                 'paired_absolute_error_difference': ((primary.method_controls_tone - primary.actual).abs() - (primary.method_controls - primary.actual).abs()).to_numpy()}
    return {'scope': 'Retrospective exploratory checks. Primary labels, forecasts and original reported intervals remain frozen.',
            'common_lag_experiment': lag_results,
            'coefficient_stability': {'scope': spec['coefficient_path'], 'summary': summaries, 'paths': paths},
            'primary_period_stability': period_results, 'block_sensitivity': block_results,
            'bootstrap_scope': 'Calendar segments retained; circular blocks shorten within short segments. These intervals are nominal and exploratory.',
            'multiplicity': {'family': spec['multiple_testing_family'], 'family_n': len(comparisons),
                             'method': spec['p_values'], 'comparisons': comparisons,
                             'limitation': 'Holm correction does not remedy retrospective model selection, measurement error, sparse coverage or unmeasured confounding. Original interval endpoints remain unadjusted.'},
            'autocorrelation': {name: calendar_autocorrelation(primary.target_month, values) for name, values in residuals.items()}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-events', action='store_true', help='One-time private metadata export; not needed for public replay.')
    parser.add_argument('--verify', action='store_true', help='Compare recomputed extension JSON with frozen outputs.')
    args = parser.parse_args()
    if args.prepare_events:
        prepare_event_manifest()
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    from verify_artifact_baseline import verify_baseline
    baseline_check = verify_baseline(ROOT)
    items = read_jsonl(ROOT/'data/shareable/gpt_core_v3/corpus_metadata.jsonl')
    labels = {row['id']: row for row in read_jsonl(ROOT/'data/shareable/gpt_core_v3/GPT_primary_labels.jsonl')}
    outputs = {'measurement.json': measurement(items, labels),
               'same_event_comparison.json': event_comparison(items, labels),
               'statistical_stability.json': stability()}
    for name, data in outputs.items():
        if args.verify:
            from reproduce_submission import close
            close(data, read_json(OUT/name))
        else:
            write_json(OUT/name, data)
    if not args.verify:
        from write_rubric_results import write_results
        write_results(outputs, OUT)
    summary = {'status': 'pass', 'version': CFG['version'], 'human_reference_pairs': outputs['measurement.json']['splits']['all_300']['valid_pairs'],
               'matched_events': outputs['same_event_comparison.json']['event_n'],
               'straight_news_items': outputs['same_event_comparison.json']['straight_news_n'],
               'common_lag_test_months': outputs['statistical_stability.json']['common_lag_experiment']['n'],
               'primary_frozen_hashes_verified': baseline_check['frozen_hashes_verified'],
               'approved_presentation_artifacts_verified': baseline_check['approved_presentation_artifacts_verified'], 'new_paid_API_calls': 0,
               'network_requests_for_reproduction': 0,
               'verification_boundary': 'Recalculates supplied labels, event membership and archived vintages; does not independently authenticate the owner-attested reference source or repeat private-text event matching.'}
    write_json(OUT/'verification.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
