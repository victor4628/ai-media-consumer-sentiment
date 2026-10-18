# Media narratives and consumer sentiment

Victor Chen · FRE-GY 7871 · Instructor: Dr. Daniel Rodriguez

This financial research project examines six questions about media narratives, purchasing power and US consumer sentiment. The research cutoff is 16 October 2026. Media inputs cover October 2019–July 2026; sentiment forecasts are evaluated through August 2026.

## Deliverables

| File | Description |
|---|---|
| [Report](output/report.pdf) | 12-page research report with findings, alternative explanations and causal limitations |
| [Presentation](output/slides.pptx) | 10 slides, including a practical implication for financial risk monitoring |
| [Speaker script](output/speaker_notes.md) | 908 English words aligned with slide notes; estimated 6–8 minutes with pauses |
| [Monitoring dashboard](output/dashboard.html) | Self-contained HTML with filters, empirical intervals and CSV export |
| [Submission package](output/submission.zip) | Deliverables, code, categorical data, source snapshots and documentation |

See [SUBMISSION_GUIDE.md](SUBMISSION_GUIDE.md) for the assessment evidence map and reproduction instructions. In an extracted package, the submission directory is the package itself; it does not contain another ZIP.

## Findings

The corpus contains 1,473 directly assigned ChatGPT judgments. The primary analysis retains 230 US-relevant economic news headlines and 829 X posts. A reference sample from one independent human annotator has 293 valid pairs from 300 attempted items. Overall tone agreement is 65.2%, with kappa 0.539; held-out five-class tone macro-F1 is 0.602. These comparisons do not establish consensus-label accuracy.

X uses more emotional language in this sample. Accumulated price pressure reduces the descriptive residual sentiment gap from 28.25 to 7.08 points. Media's forecasting gain depends on the baseline and coverage rule. The method-controls comparison has a Holm-adjusted p-value of 0.147 across 14 original comparisons, and its gain reverses in the smallest strict-coverage sample. The study does not identify a causal media effect or individual psychological mechanisms.

For financial risk monitoring, benchmark choice changes the interpretation of a sentiment gap. In August 2026, observed sentiment is about 14.4 points below the economy-only forecast and 3.5 points below prior-sentiment persistence. Media features require additional predictive value beyond strong economic and recent-sentiment baselines.

## Reproduce

From the repository or extracted submission directory:

```powershell
python -m pip install -r requirements.txt
python scripts/reproduce_submission.py
python -m unittest discover -s tests
python scripts/build_dashboard.py
```

Dependency installation may require a network connection. Once dependencies are installed, replay uses included categorical labels and 1,005 archived macroeconomic snapshots, with no network requests, credentials or paid inference. It recomputes the original models and retrospective extensions. Raw private text extraction and semantic labeling are outside the public reproduction boundary.

## Repository map

- configs/: analysis specifications, presentation script and release inventory.
- data/shareable/: minimized item metadata, categorical labels, provenance and event records.
- data/raw/alfred_vintages/: hashed official release snapshots.
- data/processed/: model panels, forecasts and diagnostic series.
- labels/: [human labeling guide](labels/HUMAN_LABELING_GUIDE.md), [codebook](labels/CODEBOOK.md) and [blank working sheet](labels/annotation_template.csv).
- prompts/: preserved coding prompts.
- reports/: report source, statistical results, figures and verification records.
- scripts/, src/, tests/: reproduction, artifact generation and checks.
- output/: final deliverables.

The [dashboard update guide](reports/rubric_extension/UPDATE_GUIDE.md) distinguishes rebuilding the historical snapshot from collecting a new prospective evaluation. Additional statistical checks are retrospective and exploratory. Exact immutable ChatGPT model versions were not retained. Missing reference labels and disagreements are preserved.

## Quality checks and packaging

```powershell
python scripts/check_deliverables.py
node scripts/check_dashboard.mjs
python scripts/check_release.py
python scripts/package_submission.py
python scripts/verify_submission_package.py
```

Artifact checks require optional dependencies in requirements-artifacts.txt; the JavaScript dashboard check requires Node.js. Report rebuilding uses scripts/build_report.py. Slide authoring uses scripts/build_slides.mjs and the locally installed Artifact Tool runtime, separately from numerical replay. The legacy collector client and its mocked tests are supporting utilities, not the source of the human reference or a requirement for statistical replay.

The report and presentation have been rendered and visually reviewed. Native PowerPoint execution has not been checked. Dashboard logic is verified; target-browser layout and actual 6–8-minute delivery require a local check and timed rehearsal. Source attribution, uncertainty and public-data boundaries are documented in the report and provenance files.
