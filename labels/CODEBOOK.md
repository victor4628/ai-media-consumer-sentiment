# Economic narrative codebook

The [human labeling guide](HUMAN_LABELING_GUIDE.md) provides the workflow, examples and export instructions. The [blank working sheet](annotation_template.csv) is available for a future authorized round. These documents do not add labels or revise the existing reference.

## Unit and inclusion

News inputs are individual headlines; X inputs are individual posts. Use the supplied text, item ID, platform, source, publication/discovery timestamps and input identifier. Do not treat a headline as the full article or infer an author's location, political affiliation or exposure.

The primary sample requires substantive economic content, us_relevance=yes, and availability before the next monthly forecast origin. Uncertain geography is excluded. Numerical claims can be compared only with contemporaneous official evidence matching the measure, reference period, units, adjustment and vintage. Missing evidence does not establish that a statement is false.

## Categories

| Field | Values |
|---|---|
| tone | negative / neutral / positive / mixed / uncertain |
| language_style | factual / emotional / mixed / uncertain |
| topics | Any subset of prices / employment / wages / growth / housing / household_finances / other |
| price_frame | levels / changes / both / neither / uncertain |
| scope_frame | household / national / both / neither / uncertain |
| time_frame | current / future / both / neither / uncertain |
| factual_calibration | matches / conflicts / not_checkable / no_numeric_claim |
| political_attribution | credit / blame / both / none / uncertain |
| us_relevance | yes / no / uncertain |

Code economic direction, language style, topics and attribution separately. A negative economic fact can be factual; criticism alone does not establish bias. Mixed tone requires both favorable and unfavorable economic assessments. Emotional wording alone does not make tone mixed. Uncertain is a category; an unavailable record remains missing.

## Human reference and comparison

One independent human annotator supplies 300 reference records, evenly split between news and X. There are 293 valid human–ChatGPT pairs and seven unavailable labels. Labels and provenance are in data/shareable/human_reference/. Original source metadata was corrected on the project owner's declaration without changing categorical values. Annotation identity, dates and independent work logs were not separately authenticated.

All-pair tone agreement is 65.2%, with Cohen's kappa 0.539. The original held-out subset has 196 valid pairs, 63.8% agreement, kappa 0.522 and five-class macro-F1 0.602. Keep the fixed development and held-out identities. Do not replace disagreements or null records to improve agreement. These statistics compare one human reference with ChatGPT and do not establish consensus truth.

## Aggregation and access

For prediction, news tone is averaged within source and then equally across observed sources in each month. X is equally weighted by item. Positive / neutral / negative / mixed map to +1 / 0 / -1 / 0; uncertain tone is omitted from the tone mean. Content shares and tone are separate measures. Multilabel topic shares may overlap. Missing data are not neutral labels.

The primary 1,473 ChatGPT judgments span multiple sessions; exact immutable model versions were not retained. Preserved prompts and coding provenance accompany the release. Public exports omit private texts, quotations and rationales. They permit statistical replay, not independent reconstruction of full input hashes, private duplicate extraction or semantic recoding.
