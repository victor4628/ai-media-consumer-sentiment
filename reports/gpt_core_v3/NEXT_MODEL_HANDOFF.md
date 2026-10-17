# Handoff after stages 1–2

The user asked to finish stages 1 and 2 only. They plan to use different models for later stages to save tokens. These stages are complete; do not redo annotation or collect more data.

## Read first

1. `reports/gpt_core_v3/STAGES_1_2_FINDINGS.zh-CN.md` — findings, six RQ answers, qualifications, exact numbers and chart links.
2. `reports/gpt_core_v3/analysis.json` and `descriptive.json` — machine-readable authoritative new results.
3. `reports/gpt_core_v3/validation.json`, `stage1_quality.json`, `provenance_addendum` under `data/private/gpt_core_v3/` — actual coding/review source and limitations.
4. `reports/gpt_core_v3/ANALYSIS_EXTENSION_LOG.md` — disclose follow-up robustness after first new result inspection.

## Current version and reproduction

- Active research: `reports/ACTIVE_RESEARCH.json`.
- Primary labels: `data/private/gpt_core_v3/GPT_primary.jsonl` (1,473 records), sealed by `sealed.json`. **No further label changes after analysis.**
- 300 earlier direct GPT labels reused, 1,173 explicitly assigned in JSON batches; no automated dictionary coding and no DeepSeek primary coding.
- Session model identifiers were not completely recorded. Never invent a specific GPT version or claim identical immutable model across all annotation sessions.
- Cached V4 review covers 150 news + 150 X, not 300 news; valid pairs 293. No human validation. Retain truthful provenance.
- Minimal labels for later distribution: `data/shareable/gpt_core_v3/GPT_primary_labels.jsonl`. Private and minimal export hashes are different by design; see export manifest. Do not distribute private texts/excerpts/rationales or credentials.
- `session_composition.json` checks annotation cohorts. The X-versus-news emotional-language difference has the same direction in all three cohorts, but news shares vary approximately 13%–41%. Date and selection composition differ, so neither temporal change nor a model effect is isolated.
- Config: `configs/gpt_core_v3_analysis.json`.
- New data: `data/processed/gpt_core_v3/`.
- Run analysis with bundled Python: `C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe scripts/analyze_gpt_core_v3.py`.
- Run figures with system `python scripts/plot_gpt_core_v3.py` (bundled Python lacks matplotlib; system Python has it).
- Tests: bundled Python `-m unittest discover -s tests` — 44 passed.
- No paid API calls and no new data in this revision.

## What remains

Stage 3: agree/select a findings-oriented narrative for six RQs. Stage 4: rewrite report, deck, and English-only notes/script using new evidence. Stage 5: visual QA, numeric and script alignment, timing, reproduction/package updates.

Existing report/PPT/script/package/dashboard remain historical **Flash-based** artifacts. `reports/CURRENT_DELIVERABLES.json`, `scripts/build_research_questions_report.py`, `scripts/build_research_questions_deck.mjs`, `scripts/reproduce_submission.py`, package allowlist and dashboard have not yet been rewired to the new research. Do not run their old defaults and present those results as new.

## User requirements for later authoring

- 6–8 minutes, findings/evidence/interpretation rather than technical modeling walkthrough.
- Six RQs must be understandable to a reader who has not seen the report; headings/questions and script vocabulary must match exactly.
- Clear graphs, few tables, use new plots in both report and presentation. Eight PNG/SVG plots are in `reports/gpt_core_v3/figures/`; forest green `#254C45`.
- Final main slide is substantive Key Takeaways. Remove generic trading warnings, filler and redundant disclaimers.
- Script English only, natural short connected sentences, minimal jargon, no “SPOKEN ENGLISH” headings, no forced transitions or repeated page ending/next opening.
- User's reference: `C:/Users/Admin/Desktop/Reinforcement_Learning_Speaker_Script_Refined.docx`. Existing style notes: `reports/PRESENTATION_STYLE.zh-CN.md`. Latest user preference is findings-first, not forced storytelling.
- p2 ICS formula rather than arrows; p3 clear sample counts and period; p5 actual sentiment trend; RQ4 use “measure” consistently. Explain forecasting baseline weakness without long formula narration.
- DeepSeek only replaces sampled human review. The user once requested calling AI review human review; that would misrepresent methods and must not be done.
- No new data collection or extra API spending requested. No commit/push/publication requested.

## Crucial new result nuances

- Eligible: 230 news + 829 X, 82 media months; 73 complete and 40 OOS months. Never reuse old 247/733/39 figures.
- Emotional/mixed language: 23.9% news vs 86.1% X. Negative tone: 45.2% vs 53.1%. Political blame/both: 22.6% vs 49.6%. These are sample content shares, not platform causal bias estimates.
- Price-level control reduces descriptive residual decline 28.25 → 7.08 points; linear trend comparison leaves 17.99. Do not turn this into proof of anchoring or causal explained share.
- Ordinary memory model: MAE 4.199 → 4.198 with tone, essentially no gain. **Do not copy old 4.114 → 4.303 result.**
- Seasonality/survey-mode controls: 3.857 → 3.527, nominal paired interval excludes zero. Must report this promising signal, but strictest coverage reverses direction (n=13) and improvement versus persistence is uncertain. Do not falsely summarize that every new interval spans zero or that persistence has the lowest point MAE among every tested model.
- Persistence MAE 3.725 on common 40 months. All content features together MAE 4.737. No confirmed causal media effect.
- Full macro-history sample is a different experiment: 44 test months, economy 17.108, economy + prices 8.712, memory 4.324, memory + prices 3.995, persistence 3.618. Avoid comparing different test/training populations without explanation.
