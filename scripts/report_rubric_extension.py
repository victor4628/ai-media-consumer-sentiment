"""Fit the four rubric additions into the existing twelve-page report."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT/'reports/rubric_extension'/name).read_text(encoding='utf-8'))


def augment_pages(pages, figures):
    measurement = load('measurement.json')
    stability = load('statistical_stability.json')
    events = load('same_event_comparison.json')
    held = measurement['splits']['held_out_200']
    tone = held['dimensions']['tone']
    dictionary = measurement['dictionary_same_item_comparison']['results']['held_out_200']['all']
    multiplicity = next(row for row in stability['multiplicity']['comparisons']
                        if row['comparison'] == 'method_controls_tone_vs_method_controls')
    lag = stability['common_lag_experiment']

    fig, axes = plt.subplots(1, 2, figsize=(7.8, 2.45), gridspec_kw={'width_ratios': [1.25, 1]})
    matrix = np.array(tone['confusion_matrix_rows_reference_columns_prediction'])
    color = LinearSegmentedColormap.from_list('roc', ['#F4F7F5', '#254C45'])
    axes[0].imshow(matrix, cmap=color)
    axes[0].set_xticks(range(5), ['Neg.', 'Neu.', 'Pos.', 'Mix.', 'Unc.'], fontsize=8)
    axes[0].set_yticks(range(5), ['Negative', 'Neutral', 'Positive', 'Mixed', 'Uncertain'], fontsize=8)
    for row in range(5):
        for col in range(5):
            axes[0].text(col, row, str(matrix[row, col]), ha='center', va='center', fontsize=8,
                         color='white' if matrix[row, col] > matrix.max() * .55 else '#252F2A')
    axes[0].set_xlabel('ChatGPT label', fontsize=9)
    axes[0].set_ylabel('Human reference', fontsize=9)
    groups = [('All', held), ('News', held['by_platform']['news']), ('X', held['by_platform']['twitter'])]
    values = [group['dimensions']['tone']['macro_F1_reference_supported'] for _, group in groups]
    axes[1].barh(range(3), values, color=['#254C45', '#A47E43', '#697770'], height=.55)
    axes[1].set_yticks(range(3), [f'{name} (n={group["valid_pairs"]})' for name, group in groups], fontsize=9)
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, 1)
    axes[1].set_xlabel('Tone macro-F1 vs human reference', fontsize=9)
    axes[1].grid(axis='x', alpha=.3)
    axes[1].set_axisbelow(True)
    for index, value in enumerate(values):
        axes[1].text(value + .02, index, f'{value:.3f}', va='center', fontsize=9)
    fig.tight_layout()
    for extension in ['png', 'svg']:
        fig.savefig(figures/f'validation_confusion.{extension}', dpi=190, bbox_inches='tight')
    plt.close(fig)

    event_rows = [['Release benchmark', 'Sources', 'Existing tone / style labels']]
    names = {'gdp_2021q2_advance': 'Q2 2021 GDP: +6.5%',
             'jobs_2023may': 'May 2023 jobs: +339,000', 'pce_2024march': 'Mar. 2024 PCE: 2.7% YoY'}
    for event in events['events']:
        rows = [row for row in event['items'] if row['comparison_role'] == 'straight_news']
        source_names = {'abcnews.go.com': 'ABC', 'reuters.com': 'Reuters', 'bloomberg.com': 'Bloomberg', 'cnn.com': 'CNN'}
        event_rows.append([names[event['id']], ' / '.join(source_names[row['source']] for row in rows),
                           '; '.join(f'{row["tone"]} / {row["language_style"]}' for row in rows)])
    pages[2]['tables'] = [{'rows': event_rows, 'widths': [155, 118, 255]}]
    pages[2]['paras'][-1] = (
        'A new purposive audit matches six straight-news headlines to three official releases, using release date, observation period and source URLs. The table retains the original GPT labels; one same-day commentary is recorded separately. The jobs release combines payroll growth with rising unemployment [4], and the PCE release has distinct headline/core measures [5]. Matching a release therefore does not hold every factual facet constant. These cases illustrate framing differences and agreements, not a population bias rate or a causal source effect. Five earlier numerical checks in four headlines remain illustrative, not a general accuracy estimate.')

    pages[7]['paras'][2] = (
        'After seasonality and survey-mode controls, adding tone reduces MAE from 3.857 to 3.527: a change of −0.330 with nominal interval [−0.585, −0.072]. The new null-centered block-bootstrap comparison gives raw p = '
        f'{multiplicity["bootstrap_p_two_sided"]:.4f} and Holm-adjusted p = {multiplicity["Holm_adjusted_p"]:.3f} across all 14 original recorded comparisons. This exploratory gain does not survive that family adjustment. Its advantage over persistence is −0.198 [−0.791, +0.377], which also fails to establish a reliable win over the simple baseline.')

    lag_rows = [['Separate 30-month experiment', 'MAE', 'Change vs controls']]
    for key, name in [('baseline', 'Controls baseline'), ('media_lag1', 'Add tone: prior month'),
                      ('media_lag2', 'Add tone: two months prior'), ('media_lag3', 'Add tone: three months prior'),
                      ('persistence', 'Carry forward prior sentiment')]:
        increment = lag['metrics'][key]['MAE'] - lag['metrics']['baseline']['MAE']
        lag_rows.append([name, f'{lag["metrics"][key]["MAE"]:.3f}', '—' if key == 'baseline' else f'{increment:+.3f}'])
    pages[8]['lead'] = 'Coverage, lag choice and multiple comparisons limit the forecasting claim.'
    pages[8]['tables'] = [{'rows': lag_rows, 'widths': [315, 95, 118]}]
    pages[8]['paras'] = [
        'The original coverage check gives media MAE changes of −0.330 (40 months), −0.193 (25) and +0.299 (13) as minimum counts rise from 1 news/3 X to 2/5 and 3/5. The strictest estimate reverses. Filtering changes both training and evaluation months; it does not identify an effect of article count.',
        'The new lag experiment uses identical histories and 30 test months for all three lags, after requiring coverage at each calendar lag. Its 54 eligible rows support at least 24 expanding training observations. Two- and three-month lag increments have nominal intervals spanning zero. This sample differs from the original 40-month experiment; their MAE levels must not be compared as if histories were identical.',
        'In the original controls-plus-tone model, standardized news coefficients remain positive (0.477 to 0.997); X coefficients range from −0.641 to 0.964 and change sign three times between observed origins. These are conditional associations on a changing training scale, not causal effects or a formal structural-break test.',
        'Forecast errors have calendar-adjacent lag-one correlation 0.449 across 35 pairs. One-, three- and six-month block checks retain the nominal controls-model gain, but all comparisons with persistence span zero. The new lag tests and block checks are retrospective and exploratory; the 14-comparison Holm family on page 8 covers the original comparisons, not every possible extension.'
    ]

    class_rows = [['Human-reference tone', 'Human n', 'Precision', 'Recall', 'F1']]
    for category, values in tone['per_class'].items():
        class_rows.append([category.title(), str(values['support']), *[f'{values[key]:.3f}' if values[key] is not None else '—' for key in ['precision', 'recall', 'F1']]])
    pages[9].update({
        'title': 'Data, coding and human-reference validation',
        'lead': 'Class-level scores reveal weaknesses hidden by overall agreement.',
        'figure': 'validation_confusion',
        'caption': 'Original held-out identities: 196 valid pairs from 200 items. Rows are the human reference; columns are ChatGPT. Macro-F1 averages classes with human-reference support.',
        'tables': [{'rows': class_rows, 'widths': [215, 70, 81, 81, 81]}],
        'paras': [
            'One human annotator independently labeled a 300-item reference sample: 150 news headlines and 150 X posts. There are 293 valid human–ChatGPT pairs and seven unavailable reference labels. Full-sample tone agreement is 65.2%, kappa 0.539. The original held-out subset has 196 pairs, 63.8% agreement and kappa 0.522. Source attribution follows the project owner’s correction, retained in the provenance protocol.',
            f'Held-out five-class tone macro-F1 is {tone["macro_F1_reference_supported"]:.3f}. Neutral F1 is 0.405 and uncertain recall is 0.385. Undefined class rates remain missing; absent classes are not assigned perfect scores. All categorical dimensions, multilabel topics, platform groups and source groups are supplied in the analytical package. Source groups below ten pairs are flagged as small; the X source denotes a retrieval endpoint, not individual authors.',
            f'On the same {dictionary["n"]} eligible held-out items, three-class macro-F1 is {dictionary["GPT"]["macro_F1_reference_supported"]:.3f} for GPT and {dictionary["dictionary"]["macro_F1_reference_supported"]:.3f} for the simple dictionary. Both coders’ mixed labels map to neutral; uncertain labels and unavailable dictionary rows are excluded explicitly. This subset is not the 196-item five-class test. A single human reference is not consensus truth.',
            'The 1,473 primary GPT judgments span multiple sessions; exact immutable model versions were not retained. Private-input evidence/schema checks and visible, constructed source/name swaps test traceability and example consistency. They do not establish population accuracy. Original labels and predictions remain frozen; no new adjudication or model inference was performed.'
        ]})
    pages[10]['paras'][-1] = (
        '<b>Monitoring implementation.</b> The offline dashboard now displays the economic-model gap, coding-status counts, a separate purposive factual audit, curated release/method events, class-level validation and lag/coefficient diagnostics. A release-vintage table distinguishes observation periods from forecast cutoffs. The update guide separates rebuilding this frozen snapshot from collecting and evaluating a new prospective study. Media still end in July 2026; no final-election-week evidence is added.')
    pages[11]['paras'][0] += (
        ' [4] BLS, May 2023 Employment Situation, https://www.bls.gov/news.release/archives/empsit_06022023.htm. '
        '[5] BEA, March 2024 Personal Income and Outlays, https://www.bea.gov/news/2024/personal-income-and-outlays-march-2024. '
        '[6] BEA, Q2 2021 GDP advance estimate, https://www.bea.gov/news/2021/gross-domestic-product-second-quarter-2021-advance-estimate-and-annual-update.')
    pages[11]['paras'][2] += ' The new event manifest records primary official URLs, curated membership and paraphrased headline emphases; matching is retrospective and not blind.'
    pages[11]['paras'][3] += ' The same command verifies the four additions; python scripts/run_rubric_extension.py --verify runs that check alone. Supplemental tables and methods are in reports/rubric_extension/RESULTS.md and the update guide.'
    pages[11]['paras'][5] = (
        '<b>Reading the evidence.</b> Descriptive fits use 200 months; macro-only forecasts use 44 test months; the primary media comparison uses 40. The common-lag extension uses 30 different matched test months. Original nominal intervals remain unchanged; approximate Holm-adjusted bootstrap p-values additionally cover 14 original paired comparisons. New lag and robustness checks remain exploratory. No consumer-level mechanism, causal media effect, consensus-label accuracy, final-election-week effect or investment-return backtest is established.')
    return pages
