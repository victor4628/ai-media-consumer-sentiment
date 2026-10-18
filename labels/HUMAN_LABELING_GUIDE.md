# Human labeling guide

This companion to [CODEBOOK.md](CODEBOOK.md) documents how to apply the existing economic-content categories. It consolidates the procedure after analysis and does not establish that new annotation, training or adjudication took place. Existing reference labels are unchanged.

The current reference contains 300 selected items labeled by one independent human annotator, with 293 available labels and seven missing labels. Compare those labels with ChatGPT separately. Preserve the existing development/held-out identities in `data/shareable/audit_splits.json`; do not move difficult items between groups or tune labels to improve agreement.

## Materials and unit of analysis

Use the fixed item ID, the original authorized text, platform, source, publication/discovery timestamps and input hash. News items are headlines, not full articles. X items are individual posts. Read only the supplied text and any supplied contemporaneous official evidence. Do not infer a full article's content, an author's residence, political affiliation or audience exposure.

Public exports omit original texts and rationales. They support statistical replay, not a fresh semantic labeling exercise. An authorized source holder must supply the original inputs for a new annotation round. Work with a versioned copy and retain the original labels.

Prompts are preserved in `prompts/economic_coding_v1.txt` and `prompts/economic_coding_v2.txt`. The latter retains its original development-candidate header. The primary coding protocol, prompt identifier and retrospective scope are recorded in `data/shareable/gpt_core_v3/protocol.json`. These files document the study history; they do not make it a prospectively blinded experiment or identify an immutable ChatGPT model version.

## Workflow

1. Fix the sample IDs and codebook version before comparing labels. Read and label each item independently, without looking at ChatGPT's item-level answer or the next sentiment outcome.
2. Identify substantive economic content and the text's geographic subject. No substantive economic topic means `topics=[]`. US relevance must come from the subject of the text; English or a dollar sign alone is insufficient. Keep uncertain geography as `uncertain`.
3. Code each dimension below separately. An adverse economic fact can use factual language. Political criticism does not by itself establish bias.
4. In the private working record, retain up to three literal evidence excerpts of at most 160 characters each and a short rationale of at most 400 characters. Record missingness or unavailable evidence explicitly. Do not invent retrospective missingness reasons for the seven existing null labels.
5. Freeze the human record before comparison. Keep human and ChatGPT labels in separate files and report disagreements. A later correction or adjudication, if actually performed, needs its own dated version and reason; it must not silently replace the reference.

The blank [annotation_template.csv](annotation_template.csv) is an optional working sheet for a future authorized round, not an input required by the current reproduction scripts. Use `status=labeled` only when the categorical record is complete; use `status=missing` when no record is available, leaving the categories blank and recording a known reason if available. An `uncertain` category is a substantive judgment, not a missing record. Keep evidence excerpts and rationales private when sharing the categorical export.

## Category decisions

| Field | Allowed values | Decision rule |
|---|---|---|
| `tone` | `negative`, `neutral`, `positive`, `mixed`, `uncertain` | Assess the economic outlook or condition, not politeness. Negative and positive indicate unfavorable and favorable assessments. Neutral has no clear direction. Mixed explicitly includes both favorable and unfavorable assessments. Uncertain means the direction cannot be determined. |
| `language_style` | `factual`, `emotional`, `mixed`, `uncertain` | Factual uses descriptive language; emotional uses loaded or affective wording; mixed includes both. Factual style does not establish factual accuracy. |
| `topics` | Any subset of `prices`, `employment`, `wages`, `growth`, `housing`, `household_finances`, `other` | Multiple topics may apply. `other` requires another substantive economic topic. An empty list is different from an uncertain tone. In the CSV working sheet, separate multiple topics with semicolons. |
| `price_frame` | `levels`, `changes`, `both`, `neither`, `uncertain` | Levels concern how high/low prices are or an absolute price. Changes concern rising/falling prices or an inflation rate. Both requires both ideas. No price claim is neither. |
| `scope_frame` | `household`, `national`, `both`, `neither`, `uncertain` | Distinguish explicit personal/family finances from economy-wide conditions. Company or local-only coverage need not be either. |
| `time_frame` | `current`, `future`, `both`, `neither`, `uncertain` | Current includes observed/recent conditions. Future requires an expectation, forecast or proposed outcome. Both requires both temporal claims. |
| `factual_calibration` | `matches`, `conflicts`, `not_checkable`, `no_numeric_claim` | Compare numerical economic claims only with supplied official evidence matching the measure, period, unit, adjustment and vintage available at publication. Without an adequate comparison use not_checkable. No numerical economic claim means no_numeric_claim. |
| `political_attribution` | `credit`, `blame`, `both`, `none`, `uncertain` | Require assignment of economic credit/blame to a government, party, officeholder or policy. Mere mention is none. Blaming a company alone is not political attribution. |
| `us_relevance` | `yes`, `no`, `uncertain` | Yes requires a supported US economic subject. No identifies a non-US subject without a US economic connection. Insufficient context remains uncertain. |

For factual calibration, a prediction, personal experience or unsupported number is not automatically a false official statistic. Use contemporaneous evidence, not a later revision. If a numerical claim cannot be checked adequately, do not guess between matches and conflicts.

## Practice examples

These are constructed illustrations, not observations added to the corpus or a new validation set. Judgments below refer to the complete quoted illustration only.

| Constructed text | Decisions illustrated |
|---|---|
| “US inflation is 3 percent.” No official evidence supplied. | `tone=neutral`, `language_style=factual`, `topics=[prices]`, `price_frame=changes`, `scope_frame=national`, `time_frame=current`, `factual_calibration=not_checkable`, `political_attribution=none`, `us_relevance=yes`. A number alone does not establish a favorable or unfavorable assessment. |
| “US job growth is strong, but rising unemployment is a concern.” | `tone=mixed`, `topics=[employment]`, `scope_frame=national`, `time_frame=current`, `factual_calibration=no_numeric_claim`, `political_attribution=none`, `us_relevance=yes`. Both economic assessments are explicit. |
| “Prices here are outrageous.” | `tone=negative`, `language_style=emotional`, `topics=[prices]`, `price_frame=levels`, `factual_calibration=no_numeric_claim`, `us_relevance=uncertain`. Do not infer location from “here.” |
| “US inflation slowed to 3%, but prices remain above 2019.” | `language_style=factual`, `topics=[prices]`, `price_frame=both`, `scope_frame=national`, `time_frame=current`, `factual_calibration=not_checkable` without supplied official evidence, `us_relevance=yes`. Code tone separately from style and price framing. |

## Export and compare

The current categorical reference uses one JSON object per item. The top-level fields include `id`, `input_sha256`, `source`, `platform`, `role=human_reference`, `annotator_id=human_01`, `annotation_method=independent_human`, and `label`. A non-null `label` contains the same ID plus the nine category fields in the table. Existing unavailable records retain `label=null`. Keep original identifiers unchanged; new rounds should have their own provenance rather than reuse a historical annotator identity.

Before comparison, check unique IDs, matching input identifiers, allowed categories, missing records and fixed split membership. Report valid pair counts alongside agreement, kappa, confusion matrices and precision/recall/F1 by class and platform/source. Current results are in `reports/rubric_extension/measurement.json`. Overall agreement is not a substitute for class-level performance. A single reference is a comparator, not consensus truth.

The statistical reproduction command is `python scripts/reproduce_submission.py`. It recalculates supplied categories and archived macroeconomic inputs; it does not rerun reading, authenticate the original labeling process or obtain new human labels.
