"""Readable supplement to the fixed-length report, generated from extension outputs."""


def write_results(outputs, destination):
    measurement=outputs['measurement.json'];stability=outputs['statistical_stability.json'];events=outputs['same_event_comparison.json']
    held=measurement['splits']['held_out_200'];tone=held['dimensions']['tone']
    def number(value):return f'{value:.3f}' if value is not None else '—'
    def table(headers,rows):
        return '\n| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(str(cell) for cell in row)+' |\n' for row in rows)+'\n'
    text='''# Four rubric additions: methods and results

This supplement was added retrospectively after the original results were known. The extension plan is in `configs/rubric_extension.json`. It is not preregistration or independent confirmation. Primary categorical labels, original predictions and the extension protocol remain frozen; their input hashes are verified on every extension run. A later documented presentation and script wording revision has a separate before/after hash receipt in `reports/final_gpt_v3/presentation_rubric_revision.json`.

## 1. Performance against the human reference

The single independent human-reference attribution follows the project owner's recorded correction. There are 293 valid pairs from 300 attempted items, including 196 of the original held-out 200. Missing labels remain missing. These are comparisons with that supplied reference, not consensus truth accuracy. The original split identities are retained; retrospective coding and earlier visibility of summaries limit a prospective-held-out interpretation.

Precision is TP/(TP+FP), recall is TP/(TP+FN), and F1 is 2TP/(2TP+FP+FN). Undefined ratios remain null. Macro-F1 averages classes having positive human-reference support; each class's support is retained. Topic labels are evaluated separately as multilabel data, not forced into one class.

### Original held-out five-class tone
'''
    text+=table(['Reference class','Human n','Predicted n','Precision','Recall','F1'],[[key,v['support'],v['predicted_n'],*[number(v[k]) for k in ['precision','recall','F1']]] for key,v in tone['per_class'].items()])
    text+=f"Agreement: {tone['agreement']:.1%}; macro-F1: {tone['macro_F1_reference_supported']:.3f}; weighted-F1: {tone['weighted_F1_reference_support']:.3f}.\n"
    text+=table(['Reference \\ GPT',*tone['classes']],[[key,*row] for key,row in zip(tone['classes'],tone['confusion_matrix_rows_reference_columns_prediction'])])
    text+='### All categorical dimensions, original held-out identities\n'
    text+=table(['Dimension','Pairs','Agreement','Macro-F1'],[[key,v['n'],number(v['agreement']),number(v['macro_F1_reference_supported'])] for key,v in held['dimensions'].items()])
    text+='### Platform groups and sources\n'
    text+=table(['Platform','Valid pairs','Tone agreement','Tone macro-F1'],[[key,v['valid_pairs'],number(v['dimensions']['tone']['agreement']),number(v['dimensions']['tone']['macro_F1_reference_supported'])] for key,v in held['by_platform'].items()])
    text+=table(['Source group','Valid pairs','Tone agreement','Macro-F1','Note'],[[key,v['valid_pairs'],number(v['dimensions']['tone']['agreement']) if v['dimensions']['tone'] else '—',number(v['dimensions']['tone']['macro_F1_reference_supported']) if v['dimensions']['tone'] else '—','Below 10 pairs' if v['small_sample'] else 'Descriptive'] for key,v in held['by_source'].items()])
    text+='Small source samples are not ranked. The X source is a retrieval endpoint rather than a group of individual authors. All/development/held-out group results, multilabel topic scores and per-class CSVs are included; the public labels allow arithmetic replay.\n\n### Fair dictionary comparison\n'
    comparison=measurement['dictionary_same_item_comparison']['results']['held_out_200']
    text+=table(['Platform','Identical paired items','GPT macro-F1','Dictionary macro-F1'],[[key,v['n'],number(v['GPT']['macro_F1_reference_supported']),number(v['dictionary']['macro_F1_reference_supported'])] for key,v in comparison.items()])
    text+='Both references and GPT mixed labels map to neutral; uncertain references/GPT labels, missing human labels and unavailable dictionary rows are excluded explicitly. This three-class eligible-text subset differs from the full five-class sample. It is an intentionally simple dictionary and is not a validated production classifier.\n\n## 2. Monitoring dashboard\n\nThe dashboard includes an explicitly defined economic-model gap, origin-time macro periods and data ages, categorical factual-calibration counts, a separate purposive five-claim audit, source coverage, a curated release/method-event timeline, human-reference performance and statistical diagnostics. Unchecked claims are not treated as false, and a purposive match rate is not generalized to the corpus. Static diagnostics state their full evaluation sample rather than pretending to follow the date filter. See `UPDATE_GUIDE.md` for snapshot rebuilding versus a future study.\n\n## 3. Release-matched comparisons\n\nSix existing straight-news headlines span three purposively chosen releases. One commentary is context only. Membership uses the date, economic period, metric and source URL. Labels had been visible, so selection is not blind; no label is changed. Publisher times remain metadata and the three events are not an exhaustive or representative sample.\n'
    for event in events['events']:
        text+=f"\n### {event['title']} — {event['date']}\n\n{event['facts']} [Official release]({event['official_url']}).\n"
        text+=table(['Source','Paraphrased emphasis','Tone','Style','Role'],[[f"[{row['source']}]({row['url']})",row['summary'],row['tone'],row['language_style'],row['comparison_role']] for row in event['items']])
        text+=event['exclusions']+'\n'
    text+='\nThe GDP pair agrees in tone and style. The jobs pair differs in tone while both are factual: the release supports both payroll growth and rising unemployment. The PCE pair shares negative tone but differs in style and focuses on different headline/core facets. These are framing diagnostics; event matching alone does not establish distortion, source bias, audience exposure or effects on sentiment.\n\n## 4. Forecast stability and multiplicity\n\n### Calendar lags with matched histories\n'
    lag=stability['common_lag_experiment']
    text+=f"All lags share {lag['eligible_n']} eligible training/evaluation rows and {lag['n']} common test months ({lag['test_start']} to {lag['test_end']}). Shifts use the complete calendar before filtering; all three lag months must meet 1 news/3 X coverage. This is a separate experiment from the original 40-month analysis. The baseline includes economy, prior sentiment, seasonality and the fixed survey-mode ramp.\n"
    text+=table(['Model','N','MAE','RMSE','Media increment','Nominal interval'],[[key,v['n'],number(v['MAE']),number(v['RMSE']),number(lag['media_increments'][key]['difference']) if key in lag['media_increments'] else '—',str([round(x,3) for x in lag['media_increments'][key]['interval']]) if key in lag['media_increments'] else '—'] for key,v in lag['metrics'].items()])
    text+='### Standardized coefficient paths\n\nThese original expanding-ridge coefficients are conditional on a changing scale and correlated controls; sign or range does not estimate a causal effect or constitute a formal break test. CSV paths retain every observed origin.\n'
    text+=table(['Model','Feature','Min','Median','Max','Positive share','Sign changes'],[[row['model'],row['feature'],number(row['minimum']),number(row['median']),number(row['maximum']),number(row['positive_share']),row['sign_changes_between_observed_origins']] for row in stability['coefficient_stability']['summary']])
    text+='### Periods and block lengths\n'
    text+=table(['Period','N','MAE increment','Nominal interval'],[[key,v['media_increment']['n'],number(v['media_increment']['difference']),str(v['media_increment']['interval'])] for key,v in stability['primary_period_stability'].items() if key!='by_year'])
    text+=table(['Comparison','Requested block months','MAE difference','Nominal interval'],[[row['left']+' vs '+row['right'],row['block_months_requested'],number(row['MAE_difference']),str([round(x,3) for x in row['nominal_interval']])] for row in stability['block_sensitivity']])
    text+='Calendar-contiguous segments retain their observed sizes and never exchange observations across missing-month gaps. Circular block widths shorten in small segments. One-month blocks are an independence sensitivity, not a preferred dependence model. New intervals are nominal and do not replace the original fixed 2,000-draw intervals.\n'
    text+=table(['Error series','Calendar-adjacent pairs','Lag-one correlation'],[[key,v['calendar_adjacent_pairs'],number(v['lag1_correlation'])] for key,v in stability['autocorrelation'].items()])
    text+='### Multiple comparisons\n\nFor each of the original 14 recorded paired comparisons, use the same 3-month calendar-segment resampling indices, center the paired loss differential under a zero-mean null, and compute a two-sided add-one bootstrap p-value with 3,999 draws. Holm adjustment includes the whole family. These are approximate exploratory p-values; Holm does not repair retrospective selection or label/coverage error. New lag comparisons are not claimed to belong to a prospectively fixed confirmatory family.\n'
    text+=table(['Original comparison','MAE difference','Raw p','Holm-adjusted p'],[[row['comparison'],number(row['MAE_difference']),f"{row['bootstrap_p_two_sided']:.4f}",number(row['Holm_adjusted_p'])] for row in stability['multiplicity']['comparisons']])
    text+='The controls-model media gain has adjusted p = 0.147 and does not survive the 5% family threshold. Original predictions, MAEs, price accounting and coverage reversal are unchanged. The additions support retaining cautious interpretation rather than promoting a new winning specification.\n'
    (destination/'RESULTS.md').write_text(text,encoding='utf-8')
