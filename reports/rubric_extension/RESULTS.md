# Four rubric additions: methods and results

This supplement was added retrospectively after the original results were known. The extension plan is in `configs/rubric_extension.json`. It is not preregistration or independent confirmation. Primary categorical labels, original predictions and the extension protocol remain frozen; their input hashes are verified on every extension run. A later documented presentation and script wording revision has a separate before/after hash receipt in `reports/final_gpt_v3/presentation_rubric_revision.json`.

## 1. Performance against the human reference

The single independent human-reference attribution follows the project owner's recorded correction. There are 293 valid pairs from 300 attempted items, including 196 of the original held-out 200. Missing labels remain missing. These are comparisons with that supplied reference, not consensus truth accuracy. The original split identities are retained; retrospective coding and earlier visibility of summaries limit a prospective-held-out interpretation.

Precision is TP/(TP+FP), recall is TP/(TP+FN), and F1 is 2TP/(2TP+FP+FN). Undefined ratios remain null. Macro-F1 averages classes having positive human-reference support; each class's support is retained. Topic labels are evaluated separately as multilabel data, not forced into one class.

### Original held-out five-class tone

| Reference class | Human n | Predicted n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- |
| negative | 70 | 80 | 0.725 | 0.829 | 0.773 |
| neutral | 44 | 35 | 0.457 | 0.364 | 0.405 |
| positive | 29 | 37 | 0.676 | 0.862 | 0.758 |
| mixed | 14 | 26 | 0.423 | 0.786 | 0.550 |
| uncertain | 39 | 18 | 0.833 | 0.385 | 0.526 |

Agreement: 63.8%; macro-F1: 0.602; weighted-F1: 0.623.

| Reference \ GPT | negative | neutral | positive | mixed | uncertain |
| --- | --- | --- | --- | --- | --- |
| negative | 58 | 4 | 0 | 7 | 1 |
| neutral | 12 | 16 | 9 | 6 | 1 |
| positive | 0 | 1 | 25 | 2 | 1 |
| mixed | 3 | 0 | 0 | 11 | 0 |
| uncertain | 7 | 14 | 3 | 0 | 15 |

### All categorical dimensions, original held-out identities

| Dimension | Pairs | Agreement | Macro-F1 |
| --- | --- | --- | --- |
| tone | 196 | 0.638 | 0.602 |
| language_style | 196 | 0.612 | 0.403 |
| price_frame | 196 | 0.867 | 0.564 |
| scope_frame | 196 | 0.755 | 0.495 |
| time_frame | 196 | 0.694 | 0.477 |
| factual_calibration | 196 | 0.908 | 0.807 |
| political_attribution | 196 | 0.883 | 0.771 |
| us_relevance | 196 | 0.847 | 0.785 |

### Platform groups and sources

| Platform | Valid pairs | Tone agreement | Tone macro-F1 |
| --- | --- | --- | --- |
| news | 100 | 0.600 | 0.590 |
| twitter | 96 | 0.677 | 0.597 |


| Source group | Valid pairs | Tone agreement | Macro-F1 | Note |
| --- | --- | --- | --- | --- |
| abcnews.go.com | 4 | 1.000 | 1.000 | Below 10 pairs |
| apnews.com | 7 | 0.714 | 0.617 | Below 10 pairs |
| aspentimes.com | 1 | 1.000 | 1.000 | Below 10 pairs |
| bloomberg.com | 6 | 0.833 | 0.822 | Below 10 pairs |
| bostonglobe.com | 4 | 0.750 | 0.600 | Below 10 pairs |
| chicagotribune.com | 3 | 1.000 | 1.000 | Below 10 pairs |
| cnbc.com | 11 | 0.273 | 0.274 | Descriptive |
| cnn.com | 9 | 1.000 | 1.000 | Below 10 pairs |
| denverpost.com | 3 | 0.667 | 0.833 | Below 10 pairs |
| foxnews.com | 5 | 0.600 | 0.556 | Below 10 pairs |
| latimes.com | 5 | 0.600 | 0.500 | Below 10 pairs |
| marketplace.org | 1 | 0.000 | 0.000 | Below 10 pairs |
| middletownpress.com | 1 | 0.000 | 0.000 | Below 10 pairs |
| mprnews.org | 1 | 1.000 | 1.000 | Below 10 pairs |
| nbcnews.com | 1 | 1.000 | 1.000 | Below 10 pairs |
| nytimes.com | 4 | 0.500 | 0.333 | Below 10 pairs |
| reuters.com | 9 | 0.556 | 0.493 | Below 10 pairs |
| seattletimes.com | 2 | 0.500 | 0.500 | Below 10 pairs |
| sfchronicle.com | 2 | 1.000 | 1.000 | Below 10 pairs |
| startribune.com | 4 | 0.250 | 0.167 | Below 10 pairs |
| tampabay.com | 1 | 0.000 | 0.000 | Below 10 pairs |
| thehill.com | 2 | 1.000 | 1.000 | Below 10 pairs |
| thehour.com | 3 | 0.667 | 0.556 | Below 10 pairs |
| twitter_search | 96 | 0.677 | 0.597 | Descriptive |
| washingtonpost.com | 5 | 0.000 | 0.000 | Below 10 pairs |
| wbur.org | 2 | 1.000 | 1.000 | Below 10 pairs |
| whyy.org | 1 | 0.000 | 0.000 | Below 10 pairs |
| wsj.com | 3 | 0.000 | 0.000 | Below 10 pairs |

Small source samples are not ranked. The X source is a retrieval endpoint rather than a group of individual authors. All/development/held-out group results, multilabel topic scores and per-class CSVs are included; the public labels allow arithmetic replay.

### Fair dictionary comparison

| Platform | Identical paired items | GPT macro-F1 | Dictionary macro-F1 |
| --- | --- | --- | --- |
| all | 112 | 0.777 | 0.199 |
| news | 42 | 0.786 | 0.240 |
| twitter | 70 | 0.766 | 0.169 |

Both references and GPT mixed labels map to neutral; uncertain references/GPT labels, missing human labels and unavailable dictionary rows are excluded explicitly. This three-class eligible-text subset differs from the full five-class sample. It is an intentionally simple dictionary and is not a validated production classifier.

## 2. Monitoring dashboard

The dashboard includes an explicitly defined economic-model gap, origin-time macro periods and data ages, categorical factual-calibration counts, a separate purposive five-claim audit, source coverage, a curated release/method-event timeline, human-reference performance and statistical diagnostics. Unchecked claims are not treated as false, and a purposive match rate is not generalized to the corpus. Static diagnostics state their full evaluation sample rather than pretending to follow the date filter. See `UPDATE_GUIDE.md` for snapshot rebuilding versus a future study.

## 3. Release-matched comparisons

Six existing straight-news headlines span three purposively chosen releases. One commentary is context only. Membership uses the date, economic period, metric and source URL. Labels had been visible, so selection is not blind; no label is changed. Publisher times remain metadata and the three events are not an exhaustive or representative sample.

### BEA: Q2 2021 GDP advance estimate — 2021-07-29

Real GDP grew 6.5% quarter over quarter at an annualized rate; an advance estimate, not a year-over-year rate. [Official release](https://www.bea.gov/news/2021/gross-domestic-product-second-quarter-2021-advance-estimate-and-annual-update).

| Source | Paraphrased emphasis | Tone | Style | Role |
| --- | --- | --- | --- | --- |
| [abcnews.go.com](https://abcnews.go.com/US/wireStory/us-economy-accelerated-solid-65-rate-quarter-79139521) | ABC emphasizes solid quarterly growth of 6.5%. | positive | factual | straight_news |
| [reuters.com](https://www.reuters.com/world/us/us-economy-grows-solidly-second-quarter-weekly-jobless-claims-fall-2021-07-29/) | Reuters emphasizes solid growth alongside falling weekly jobless claims. | positive | factual | straight_news |
| [reuters.com](https://www.reuters.com/article/us-global-finance-breakingviews/supply-chain-woes-trip-solid-us-economic-growth-idUSKBN2EZ22F) | Reuters commentary emphasizes supply constraints alongside solid growth. | mixed | mixed | commentary_context_only |

The same-day historical pandemic-recession revision concerns a different period; commentary is excluded from the straight-news pair.

### BLS: May 2023 Employment Situation — 2023-06-02

Payrolls rose 339,000 while unemployment rose 0.3 percentage point to 3.7%; these come from different surveys in the same release. [Official release](https://www.bls.gov/news.release/archives/empsit_06022023.htm).

| Source | Paraphrased emphasis | Tone | Style | Role |
| --- | --- | --- | --- | --- |
| [abcnews.go.com](https://abcnews.go.com/Business/wireStory/us-employers-added-robust-339000-jobs-sign-healthy-99786886) | ABC emphasizes robust payroll growth despite rate increases. | positive | factual | straight_news |
| [bloomberg.com](https://www.bloomberg.com/news/articles/2023-06-02/us-payrolls-surge-while-jobless-rate-rises-wages-decelerate) | Bloomberg combines payroll growth with rising unemployment. | mixed | factual | straight_news |

The truncated CNBC headline is not used to infer its substantive framing.

### BEA: March 2024 personal income and outlays — 2024-04-26

Headline PCE inflation was 2.7% year over year, up from 2.5%; core inflation was 2.8% year over year and 0.3% month over month. [Official release](https://www.bea.gov/news/2024/personal-income-and-outlays-march-2024).

| Source | Paraphrased emphasis | Tone | Style | Role |
| --- | --- | --- | --- | --- |
| [bloomberg.com](https://www.bloomberg.com/news/articles/2024-04-26/fed-s-preferred-core-inflation-gauge-rose-at-brisk-pace-in-march) | Bloomberg emphasizes the pace of the core inflation measure. | negative | factual | straight_news |
| [cnn.com](https://www.cnn.com/2024/04/26/economy/pce-inflation-spending-march/) | CNN emphasizes deterioration in the preferred inflation gauge. | negative | mixed | straight_news |

Matching the release does not equate headline and core inflation; different factual facets remain a confounder.

The GDP pair agrees in tone and style. The jobs pair differs in tone while both are factual: the release supports both payroll growth and rising unemployment. The PCE pair shares negative tone but differs in style and focuses on different headline/core facets. These are framing diagnostics; event matching alone does not establish distortion, source bias, audience exposure or effects on sentiment.

## 4. Forecast stability and multiplicity

### Calendar lags with matched histories
All lags share 54 eligible training/evaluation rows and 30 common test months (2023-12-01 to 2026-08-01). Shifts use the complete calendar before filtering; all three lag months must meet 1 news/3 X coverage. This is a separate experiment from the original 40-month analysis. The baseline includes economy, prior sentiment, seasonality and the fixed survey-mode ramp.

| Model | N | MAE | RMSE | Media increment | Nominal interval |
| --- | --- | --- | --- | --- | --- |
| persistence | 30 | 3.720 | 4.641 | — | — |
| baseline | 30 | 3.894 | 4.589 | — | — |
| media_lag1 | 30 | 3.452 | 4.224 | -0.443 | [-0.773, -0.157] |
| media_lag2 | 30 | 3.783 | 4.465 | -0.111 | [-0.515, 0.338] |
| media_lag3 | 30 | 3.673 | 4.392 | -0.222 | [-0.687, 0.237] |

### Standardized coefficient paths

These original expanding-ridge coefficients are conditional on a changing scale and correlated controls; sign or range does not estimate a causal effect or constitute a formal break test. CSV paths retain every observed origin.

| Model | Feature | Min | Median | Max | Positive share | Sign changes |
| --- | --- | --- | --- | --- | --- | --- |
| economy_tone | news_tone | 0.190 | 0.792 | 1.874 | 1.000 | 0 |
| economy_tone | twitter_tone | 1.743 | 2.487 | 3.918 | 1.000 | 0 |
| memory_tone | news_tone | 0.601 | 0.920 | 1.149 | 1.000 | 0 |
| memory_tone | twitter_tone | -0.720 | 0.301 | 0.626 | 0.850 | 3 |
| household_tone | news_tone | 0.664 | 0.987 | 1.194 | 1.000 | 0 |
| household_tone | twitter_tone | -0.759 | 0.415 | 0.773 | 0.875 | 1 |
| method_controls_tone | news_tone | 0.477 | 0.809 | 0.997 | 1.000 | 0 |
| method_controls_tone | twitter_tone | -0.641 | 0.468 | 0.964 | 0.850 | 3 |

### Periods and block lengths

| Period | N | MAE increment | Nominal interval |
| --- | --- | --- | --- |
| before_2025 | 21 | -0.257 | [-0.6760675934107836, 0.12822680161939048] |
| from_2025 | 19 | -0.412 | [-0.7296507315193456, -0.1112015327183986] |


| Comparison | Requested block months | MAE difference | Nominal interval |
| --- | --- | --- | --- |
| method_controls_tone vs method_controls | 1 | -0.330 | [-0.588, -0.074] |
| method_controls_tone vs persistence | 1 | -0.198 | [-0.839, 0.473] |
| method_controls_tone vs method_controls | 3 | -0.330 | [-0.587, -0.082] |
| method_controls_tone vs persistence | 3 | -0.198 | [-0.789, 0.379] |
| method_controls_tone vs method_controls | 6 | -0.330 | [-0.557, -0.11] |
| method_controls_tone vs persistence | 6 | -0.198 | [-0.734, 0.256] |

Calendar-contiguous segments retain their observed sizes and never exchange observations across missing-month gaps. Circular block widths shorten in small segments. One-month blocks are an independence sensitivity, not a preferred dependence model. New intervals are nominal and do not replace the original fixed 2,000-draw intervals.

| Error series | Calendar-adjacent pairs | Lag-one correlation |
| --- | --- | --- |
| method_controls_tone_error | 35 | 0.449 |
| method_controls_error | 35 | 0.415 |
| paired_absolute_error_difference | 35 | -0.061 |

### Multiple comparisons

For each of the original 14 recorded paired comparisons, use the same 3-month calendar-segment resampling indices, center the paired loss differential under a zero-mean null, and compute a two-sided add-one bootstrap p-value with 3,999 draws. Holm adjustment includes the whole family. These are approximate exploratory p-values; Holm does not repair retrospective selection or label/coverage error. New lag comparisons are not claimed to belong to a prospectively fixed confirmatory family.

| Original comparison | MAE difference | Raw p | Holm-adjusted p |
| --- | --- | --- | --- |
| economy_tone_vs_economy | -0.539 | 0.1022 | 1.000 |
| household_tone_vs_household | -0.026 | 0.8772 | 1.000 |
| household_vs_memory | -0.169 | 0.3050 | 1.000 |
| memory_all_content_vs_memory | 0.538 | 0.3063 | 1.000 |
| memory_emotional_share_vs_memory | -0.119 | 0.4158 | 1.000 |
| memory_employment_topic_share_vs_memory | -0.091 | 0.3857 | 1.000 |
| memory_household_share_vs_memory | -0.067 | 0.8532 | 1.000 |
| memory_political_blame_share_vs_memory | 0.048 | 0.6315 | 1.000 |
| memory_price_levels_share_vs_memory | -0.075 | 0.7855 | 1.000 |
| memory_prices_topic_share_vs_memory | 0.299 | 0.1222 | 1.000 |
| memory_tone_vs_memory | -0.001 | 0.9960 | 1.000 |
| memory_vs_persistence | 0.474 | 0.1340 | 1.000 |
| method_controls_tone_vs_method_controls | -0.330 | 0.0105 | 0.147 |
| method_controls_tone_vs_persistence | -0.198 | 0.5055 | 1.000 |

The controls-model media gain has adjusted p = 0.147 and does not survive the 5% family threshold. Original predictions, MAEs, price accounting and coverage reversal are unchanged. The additions support retaining cautious interpretation rather than promoting a new winning specification.
