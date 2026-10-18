# Monitoring dashboard: rebuild and future-update guide

## Rebuild the frozen submission

From the project or extracted `submission` directory:

```powershell
python -m pip install -r requirements.txt
python scripts/reproduce_submission.py
python -m unittest discover -s tests
python scripts/build_dashboard.py
node scripts/check_dashboard.mjs
```

The reproduction command verifies the original calculations and `run_rubric_extension.py --verify` verifies the new diagnostics. The dashboard command rebuilds the self-contained HTML from frozen data. Reopen or reload `output/dashboard.html`. No credentials, private text, paid inference or live requests are required. Node is required for the optional JavaScript logic check.

For deliberate changes to extension code, run `python scripts/run_rubric_extension.py` to regenerate its outputs, review the differences, then rerun verification. The plan is `configs/rubric_extension.json`; source claims and event membership are supplied in `data/shareable/rubric_extension/`. The `--prepare-events` option is a one-time local export requiring private source metadata; public reproduction does not use it.

The report remains twelve pages. `python scripts/build_report.py` requires the optional dependencies in `requirements-artifacts.txt`; its Windows font paths must be adapted on another operating system. Report and slide authoring are separate from network-free statistical replay. A presentation wording update is recorded in `reports/final_gpt_v3/presentation_rubric_revision.json`. Its before/after hashes are checked separately while original labels, forecasts and the extension protocol remain frozen. Current chart values and embedded Excel files are preserved.

For a new deck, scripts/build_slides.mjs uses the current presentation configuration and authoring data. Existing manual layouts may differ from a new build. Validate and visually inspect a separately named output before replacing a delivered artifact. Slide authoring requires the local Artifact Tool runtime; statistical replay does not.

## What a new monthly study requires

1. **Version and freeze first.** Copy the study into a new dated version. Keep the current release snapshots, label files, original forecasts, reference provenance and baseline receipt unchanged. Do not overwrite `baseline_receipt.json` merely to bypass its hash checks. Establish the new research cutoff and evaluation target in a separate configuration before observing the next outcome.
2. **Archive real releases.** Extend the ALFRED vintage manifest and archive the actual origin-date values for the five required series. Record each series, observation period, retrieval time, vintage, URL and hash. A latest-revised series is not a substitute for an origin-time snapshot. Recalculate PCE year-over-year and GDP quarter-over-quarter annualized growth using those snapshots; do not interpolate GDP.
3. **Acquire and document content.** Use authorized access and fixed search/source/time-window rules. Preserve publication and discovery times, source URLs, text scope, duplicate decisions and missingness. Do not infer audience exposure from content counts. New paid collection or inference needs its own explicit authorization; this rebuild procedure performs neither.
4. **Freeze annotation before outcomes.** Apply the documented rubric to the new inputs, retaining uncertain/null values, evidence and source provenance. Keep the human reference and GPT judgments separate, then record discrepancies. An updated human reference requires actual new human labels; existing labels must not be renamed to simulate new review.
5. **Recompute a new analytical version.** Update media start/end, evaluation vintage, source paths and evaluation period in the new study's configuration. Rebuild source-derived features and rolling predictions, keeping chronological information cutoffs. Archive predictions before the next sentiment release. The current `gpt_core_v3` scripts contain fixed historical dates and are not an automatic ingestion service; adapting those paths/dates is an explicit versioned change.
6. **Verify and publish the new snapshot.** Check labels, temporal eligibility, comparisons on identical evaluation months, gap signs, missingness and interval calibration. Recalculate the reference metrics and all prespecified diagnostics. Rebuild the dashboard and report, visually inspect them, and create a fresh checksum/verification log before sharing the new version.

## Panel definitions and update boundaries

- **Forecast filter:** target calendar months. Text panels use the preceding media month. The gap always uses the economic-only out-of-sample model, independent of the selected forecast line.
- **Factual calibration:** original categorical coding counts across selected eligible items. Uncheckable is not false. The five-claim official audit is separate and purposive; it never becomes a whole-corpus accuracy rate.
- **Timeline:** curated economic-release, policy and survey-method examples. Month-only dates remain month-only. It is not a comprehensive economic calendar, event study or causal estimate.
- **Validation:** fixed all/development/held-out reference identities, filtered separately by platform. These panels do not change with the date filter. Source groups below ten valid pairs are descriptive; the X source represents the retrieval endpoint.
- **Lag table and period table:** full experiments, explicitly labeled. The common-lag experiment has 30 test months and different training histories from the original 40-month study. Coefficient charts alone follow the date filter.
- **Statistical inference:** original intervals remain nominal. The extension reports approximate Holm-adjusted p-values for the original fourteen comparisons, not a claim that every retrospective analysis is confirmatory.

The research cutoff remains 16 October 2026. Media stop in July and sentiment evaluation stops in August. Rebuilding this dashboard does not add observations or extend that scope.
