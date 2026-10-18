# Submission guide

Study: Media narratives and consumer sentiment. Research cutoff: 16 October 2026. Media inputs end in July 2026 and sentiment evaluation ends in August 2026.

## Deliverables

| Required item | Submitted file | Scope |
|---|---|---|
| 10–12-page report | [output/report.pdf](output/report.pdf) | 12 pages; six research questions, results, alternative explanations, hypotheses, proposed causal design, limitations and sources. Editable source: `reports/report.md`. |
| Reproducible analytical package | [output/submission.zip](output/submission.zip) when using the repository | The extracted `submission` directory is the package itself. It includes code, categorical data, provenance, prompts, macro release snapshots, labeling guides, results and deliverables. The ZIP does not contain a nested copy of itself. |
| Monitoring dashboard | [output/dashboard.html](output/dashboard.html) | Open the HTML file locally in a browser. Self-contained historical snapshot with filters and CSV export. Rebuilding the snapshot is separate from collecting a new month. |
| 6–8-minute presentation | [output/slides.pptx](output/slides.pptx) and [output/speaker_notes.md](output/speaker_notes.md) | 10 slides with aligned English notes; 908 spoken words. Estimated 6.7–7.3 minutes at 125–135 words per minute; allocated time with pauses is 7 minutes 55 seconds. Actual duration requires rehearsal. |

For financial risk monitoring, the presentation's practical implication is to inspect the forecasting benchmark before interpreting a sentiment gap as new risk information. The same August 2026 observation has a gap of about −14.4 points against the economy-only forecast and −3.5 against prior-sentiment persistence. This is a benchmark comparison, not an investment-return backtest or an estimated causal media effect.

## Where to assess the rubric

| Criterion | Weight | Evidence |
|---|---|---|
| Economic measurement, timing and alternative explanations | 20% | Report pp. 2, 4–6; origin-vintage panel `data/processed/vintage_feature_panel.csv`; snapshot manifest `data/raw/alfred_vintages/manifest.json`. Accumulated prices, income, recent sentiment and survey-mode changes are considered. |
| Corpus design and validated AI measurement | 25% | Report pp. 3, 10; `data/shareable/gpt_core_v3/protocol.json`; `data/shareable/human_reference/protocol.json`; [English labeling guide](labels/HUMAN_LABELING_GUIDE.md), [codebook](labels/CODEBOOK.md), [blank working sheet](labels/annotation_template.csv); archived prompts in `prompts/`; class/platform/source results in `reports/rubric_extension/measurement.json`. |
| Statistical analysis and causal reasoning | 30% | Report pp. 4–9, 11; `reports/gpt_core_v3/analysis.json`; `reports/rubric_extension/statistical_stability.json`; `configs/gpt_core_v3_analysis.json` and `configs/rubric_extension.json`. Forecast comparisons, coverage, longer lags, coefficient stability, dependence and multiple comparisons are reported separately from the proposed experiment. |
| Reproducibility and dashboard quality | 15% | Commands below; `SHA256SUMS.json` in the extracted package; dashboard and [update guide](reports/rubric_extension/UPDATE_GUIDE.md). Dashboard includes forecast gaps, empirical intervals, coverage, factual-status counts, curated events, vintage information and validation/stability panels. |
| Communication, limitations and research ethics | 10% | Report pp. 10–12; slide notes and script; public export boundaries below. Exact model version uncertainty, missing reference labels, exploratory status and lack of observed respondent exposure are stated. |

## Reproduce the analysis

Extract the ZIP, enter its `submission` directory, and run with Python 3 and the dependencies in `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
python scripts/reproduce_submission.py
python -m unittest discover -s tests
python scripts/build_dashboard.py
```

Installing dependencies may require network access. With dependencies already installed, the statistical replay and dashboard rebuild use included files and require no network, credentials or paid model calls. The replay verifies package hashes, supplied labels, 1,005 archived snapshots, original forecasts and the four retrospective extensions. Its receipt is `reproduced/verification.json`; the supplied suite contains 50 tests.

Optional checks:

```powershell
python scripts/check_deliverables.py
node scripts/check_dashboard.mjs
```

The first requires the PDF dependency in `requirements-artifacts.txt`; the second requires Node.js. Artifact authoring is separate from numerical replay. PDF rebuilding uses `scripts/build_report.py` and optional artifact dependencies; its Windows font paths need adaptation elsewhere. PowerPoint authoring uses the local bundled Artifact Tool runtime. Neither authoring environment is required to inspect the submitted PDF/PPTX or reproduce the calculations.

The original study hashes remain in `reports/rubric_extension/baseline_receipt.json`. A later documented presentation wording update is recorded separately in `reports/final_gpt_v3/presentation_rubric_revision.json`; it preserves all eight charts' numerical values and embedded workbooks. Current paths and estimated timing are in `reports/CURRENT_DELIVERABLES.json`.

## Read results with their limits

The evidence includes content descriptions and retrospective forecasts. Psychological mechanisms and causal media effects remain hypotheses. The 40-month primary media experiment, 44-month macro forecast check and separate 30-month lag experiment have different histories; compare models within each experiment. Original intervals are nominal; the additional Holm correction covers the 14 original comparisons, not all possible retrospective checks.

The public package contains item metadata and categorical labels, not private full texts, quotations, author information or annotation rationales. It supports numerical replay, not independent semantic recoding, authentication of the original human annotation or reproduction of private extraction. The reference contains one human annotator's labels, compared with ChatGPT. Unavailable labels and disagreements remain recorded.

All 12 report pages and 10 presentation slides were rendered and visually reviewed. Native PowerPoint execution has not been checked. Dashboard logic was checked locally; browser layout inspection was blocked by the available browser tool's file-URL policy. Presentation timing is estimated. Before presenting, open the actual PPTX in the intended application, check the local HTML in the intended browser, and rehearse once with a timer.
