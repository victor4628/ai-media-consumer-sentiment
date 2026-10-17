"""Build a 12-page final course report from measured results, without API calls."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
G=colors.HexColor('#254C45');INK=colors.HexColor('#252b29');GRAY=colors.HexColor('#626c68')
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Body',fontName='Arial',fontSize=10,leading=14.1,textColor=INK,spaceAfter=8))
styles.add(ParagraphStyle(name='SmallR',fontName='Arial',fontSize=8.4,leading=11.4,textColor=GRAY,spaceAfter=5))
styles.add(ParagraphStyle(name='TitleR',fontName='Arial-Bold',fontSize=26,leading=30,textColor=G,spaceAfter=14))
styles.add(ParagraphStyle(name='H1R',fontName='Arial-Bold',fontSize=19,leading=23,textColor=G,spaceAfter=13))
styles.add(ParagraphStyle(name='H2R',fontName='Arial-Bold',fontSize=11.5,leading=15,textColor=G,spaceBefore=8,spaceAfter=6))
styles.add(ParagraphStyle(name='CellR',fontName='Arial',fontSize=9,leading=12,textColor=INK))
styles.add(ParagraphStyle(name='CellHeadR',fontName='Arial-Bold',fontSize=9,leading=12,textColor=colors.white))
story=[];md=[];page_count=0
def p(t,small=False):
 story.append(Paragraph(t,styles['SmallR' if small else 'Body']));md.append(t.replace('<b>','**').replace('</b>','**'))
def h(t):story.append(Paragraph(t,styles['H2R']));md.extend(['','### '+t,''])
def page(n,t):
 global page_count
 if page_count:story.append(PageBreak())
 page_count+=1;story.append(Paragraph(f'{n:02d} / {t}',styles['H1R']));md.extend(['','## '+t,''])
def table(headers,rows,widths=None):
 values=[[Paragraph(escape(str(x)),styles['CellHeadR']) for x in headers]]+[[Paragraph(escape(str(x)),styles['CellR']) for x in row] for row in rows]
 t=Table(values,colWidths=widths or [481/len(headers)]*len(headers),hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),G),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,1),(-1,-1),.4,colors.HexColor('#d9e0dc')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f5')])]))
 story.extend([t,Spacer(1,10)]);md.append('| '+' | '.join(headers)+' |');md.append('|'+'---|'*len(headers));md.extend('| '+' | '.join(str(x) for x in row)+' |' for row in rows)
def fig(name,height,caption):
 story.append(Image(str(ROOT/'reports/figures'/name),width=481,height=height));p(caption,True)
def load(name):return json.loads((ROOT/'reports'/name).read_text(encoding='utf-8'))
core=load('core_analysis.json');sup=load('supplemental_analysis.json');val=load('core_ai_validation.json');desc=load('core_media_descriptive.json');research=load('final_research.json')

page(1,'Research question and executive findings')
story.append(Paragraph('Economic reality,<br/>media narratives and<br/>consumer sentiment',styles['TitleR']))
p('AI Applications in Finance | Final project | Information cutoff: 16 October 2026',True)
p('<b>Question.</b> Does measured media tone add useful information about U.S. consumer sentiment after accounting for available economic indicators, persistence and a household-income proxy? Three explanations remain open: household pressures missing from aggregate indicators; framing and salience; and timing or measurement mismatch. A gap is not evidence of irrationality.')
p('<b>Main finding.</b> In 39 common, noncontinuous out-of-sample months between January 2023 and August 2026, adding sampled news and Twitter tone increases mean absolute error from 4.114 to 4.303 index points. A paired block interval for the change spans zero. This sample does not establish stable predictive improvement, and it cannot establish a media effect on sentiment.')
table(['Specification','MAE','RMSE'],[['Persistence','3.687','4.428'],['M1: economy + sentiment memory','4.114','4.803'],['M2: M1 + two media tones','4.303','4.835'],['M3: M2 + real income growth','4.288','4.818']],[285,98,98])
p('<b>What was actually built.</b> A vintage-aware macro panel, 82 months of fixed-window media sampling, 1,473 primary coding attempts, an AI-only audit, matched forecasting comparisons, a local interactive dashboard and an offline analysis reproduction package.')
p('<b>Financial use.</b> Treat the dashboard as a research and monitoring aid. The best observed benchmark remains persistence. Sparse content supply and miscalibrated intervals do not justify a trading signal or automatic portfolio allocation.')
p('<b>Scope decisions.</b> Human annotation was replaced at the user\'s request by independent AI calls and an additional AI review. AI agreement is not accuracy. No experiment or causal estimate is presented. The report preserves null and unfavorable results.',True)

page(2,'Economic data, definitions and information timing')
table(['Variable','Operational definition','Availability rule'],[
 ['Sentiment','Michigan UMCSENT headline level','Forecast-origin vintage for training; 2026-10-16 vintage only for scoring'],
 ['Unemployment','BLS U-3, seasonally adjusted; UNRATE','Latest observation present at preceding month-end'],
 ['Inflation','Headline PCEPI: 100*(index / exact 12-month lag - 1)','Same vintage in numerator and denominator'],
 ['Real GDP','GDPC1: 100*((Q / prior Q)^4 - 1)','Latest released quarter; no monthly interpolation'],
 ['Household proxy','Real disposable personal income DSPIC96, YoY','Same forecast-origin vintage; national aggregate'],
 ['Survey subindices','Current Conditions and Expectations monthly CSV','Descriptive latest snapshot only; never forecasting inputs']
 ],[95,205,181])
p('The macro feature panel contains 200 target months from January 2010 to August 2026. Five required series across 201 snapshot dates produce 1,005 cached files with hashes and a manifest. Month-end ALFRED snapshots establish availability by that cutoff; they do not identify the exact first publication time. FRED updates may lag the originating agency. [S1-S3]')
h('The supplied workbook is audited, not silently accepted')
p('The workbook\'s PCE YoY column matches core PCE within 0.0001 percentage point in all 200 audited months; it is not the requested headline series. The analysis instead derives headline inflation from PCEPI. The workbook\'s 2026 Q3 GDP entry is quarantined because its scheduled first release is after the project cutoff. Original workbook contents remain unchanged. [S2; local audit]')
p('For a target month t, macro features come from the preceding month-end vintage. Each training row retains its own historical feature vintage, while its sentiment label must be present in the current forecast-origin vintage. The October evaluation vintage never supplies labels to earlier training fits. Quarterly GDP enters only after it appears in that origin\'s snapshot.')
p('The latest scored target is August 2026. No September or October forecast outcome is invented, and the media sample ends in July. This is a historical exercise; it does not cover the final weeks before the 2026 election.',True)

page(3,'Media sampling, provenance and selection')
table(['Stage','News','Twitter/X'],[
 ['Presampled windows','8 archive slots per month; 656 total','2 one-hour windows per month; 164 total'],
 ['Retrieved candidates','540 timestamp-eligible headlines','3,160 posts'],
 ['Frozen primary corpus','489 headlines','984 posts'],
 ['US-economic, timing-eligible','247 headlines','733 posts'],
 ['Scorable tone','243 headlines','731 posts']
 ],[211,135,135])
p('Sampling covers October 2019 through July 2026, using seed 20261017. Two dates are presampled each month. News uses 13:00, 16:00, 19:00 and 22:00 UTC GDELT GKG slots; Twitter uses one randomly selected hour on each date. Fourteen of 656 news slots were unavailable. A capped latest-results page can truncate a busy Twitter hour. These are fixed-window samples, not random samples of all economic content. [S4-S5; configs/core_study.json]')
p('A curated source list includes 18 national and 33 local/regional domains. Of the 540 raw eligible headlines, 382 are national and 158 local/regional. The coding corpus caps platform contributions per month, removes exact/normalized duplicates, and excludes prior prompt-development material. Semantic story repetition can remain. Only headlines are analyzed; full articles were not retrieved.')
h('Inclusion and aggregation')
p('Both publication and archive-discovery timestamps must precede the next month. Publication comes from archive metadata and has not been independently verified on publisher pages. Primary analysis requires explicit AI US relevance and at least one economic topic. This can itself select the analyzed population. Negative, neutral/mixed and positive tone map to -1, 0 and +1; uncertain tone is excluded and counted.')
p('News tone averages within each observed outlet and then weights observed outlets equally. Twitter tone is the mean of eligible sampled posts. The primary common panel requires at least one scored headline and three scored posts per media month, leaving 72 eligible months. No missing month is imputed as neutral.')
p('Retweets are excluded by the query and duplicates removed where identifiable. Ads and suspected automation are not comprehensively resolved. Audience demographics, views, feed ranking and true exposure are unavailable. Supply, engagement and exposure must remain distinct; no population or causal interpretation follows from content frequencies.',True)

page(4,'AI coding, audit and measurement uncertainty')
p('Frozen prompt v2 and the coding guide operationalize tone, topic salience, factual versus emotional language, price levels versus changes, household versus national scope, current versus future emphasis, numeric-claim checkability and political credit/blame. Models must quote evidence from the supplied text, allow uncertainty and avoid assuming negative coverage is biased. Numeric claims without supplied verification evidence remain not_checkable.')
table(['Audit layer','Calls','Valid / paired','Meaning'],[
 ['Primary A, DeepSeek Flash','1,473','1,470 valid','Main features; 3 failed labels remain missing'],
 ['A/B, balanced audit','300','293 valid pairs','150 news + 150 posts; 100 development / 200 held-out'],
 ['Held-out A/B','200','196 valid pairs','Tone agreement 75.5%; kappa 0.672'],
 ['Additional C review, Pro','251','239 valid','245 disputed items + 6 agreement checks'],
 ['ID-blinding perturbation','20','20 valid pairs','Tone stability 95%; batch context can also vary']
 ],[137,58,112,174])
h('Held-out agreement across dimensions')
dims=val['held_out_200']['agreement']['dimensions']
table(['Dimension','Agreement / kappa','Dimension','Agreement / kappa'],[[a.replace('_',' '),f'{dims[a]["agreement"]:.1%} / {dims[a]["kappa"]:.3f}',b.replace('_',' '),f'{dims[b]["agreement"]:.1%} / {dims[b]["kappa"]:.3f}'] for a,b in [('language_style','price_frame'),('scope_frame','time_frame'),('factual_calibration','political_attribution'),('us_relevance','topics_exact_set')]],[140,100,141,100])
p('Separate A, B and C calls share the DeepSeek model family, so errors may be correlated. Two-vote review resolves 2,604 of 2,700 audit dimensions and leaves 96 unresolved; it is not a gold standard. Primary forecasting features consistently use A labels rather than selectively replacing disputed labels. Failed/schema-invalid calls remain visible in denominators.')
p('The user replaced the course\'s human double-coding requirement with AI-only verification. This is an explicit methodological deviation. Provider aliases and returned model identifiers, prompt hashes, request settings, usage and input hashes are cached. Historical texts were classified retrospectively with 2026 models; live historical implementability is unproven.',True)

page(5,'What the sampled narratives contain')
fig('final_frames.png',163,'Figure 1. Pooled eligible item shares. News n=247; Twitter n=733. Denominators include uncertain labels. These are sample composition estimates, not population shares.')
p('Twitter texts in this selected sample more often use emotional/mixed language and political blame/both than sampled news headlines. That difference can reflect platform format, keyword filters, source composition and coding errors. It does not establish persuasion, manipulation or irrationality.')
table(['Topic (multi-label)','News share','Twitter share'],[[topic.replace('_',' '),f'{desc["news"]["topics_multilabel"].get(topic,0)/247:.1%}',f'{desc["twitter"]["topics_multilabel"].get(topic,0)/733:.1%}'] for topic in ['prices','employment','growth','housing','household_finances','wages']],[285,98,98])
p('Prices and household finances are plausible channels through which aggregate growth can coexist with weak lived experience. But the sample contains no respondent-linked media consumption or household balance sheets. National sentiment cannot be decomposed into these mechanisms from these content counts.')
h('A transparent dictionary diagnostic')
p('An intentionally small, disclosed word list yields only 51.9% agreement with A tone on scored news and 28.2% on scored Twitter, after pooling mixed with neutral. This is a sensitivity diagnostic, not a validated finance dictionary or a truth test. The list ignores negation and context: rising prices and rising wages can imply different welfare effects. Full word lists and cross-counts are in dictionary_diagnostic.json.')
p('Monthly topic, framing, scope and political-attribution counts are available in the dashboard. Multi-label topic shares need not sum to 100%. The ID-blinding check is narrow: it does not establish robustness to source-name substitutions, broad paraphrases or model-family changes.',True)

page(6,'Household pressures and survey comparability')
fig('final_household_context.png',270,'Figure 2. Top: official monthly subindices through August 2026, descriptive current snapshot. Shading marks April-July 2024 survey transition. Bottom: vintage-available prices; the cumulative baseline is fixed to December 2018. [S1-S3, S6]')
p('Slower price growth does not mean a return to earlier price levels. The supplementary price proxy compares the latest available PCE index with December 2018 in the same origin vintage. It captures an aggregate accumulated price change, not a household-specific consumption basket or an affordability index. Real disposable income growth is likewise national, not a distributional measure.')
p('Adding income and cumulative prices before media gives MAE 3.985 on the same 39 months; adding media then gives 4.070. The change is +0.085, with an exploratory interval [-0.268, 0.483]. These post-hoc results do not isolate a household mechanism or show stable media improvement.')
p('Michigan transitioned from phone interviews to web collection during April-July 2024. The official documentation reports strong parallel-series correlations but advises care with transition-period changes. A phase-in control and seasonal harmonics are therefore tested as a supplementary specification, not as a correction proven to remove method effects. [S6]')
p('Income/age/geography/party respondent splits, debt-service burdens, housing tenure, wealth and detailed spending baskets are not modeled. The dashboard explicitly marks these unavailable. A pooled aggregate residual cannot substitute for subgroup evidence.',True)

page(7,'Forecast design and identification boundary')
table(['Model','Inputs available before target month'],[
 ['Persistence','Latest sentiment value available at forecast origin'],
 ['M1','Unemployment + headline PCE YoY + latest quarterly GDP growth + available sentiment'],
 ['M2','M1 + preceding-month news tone + preceding-month Twitter tone'],
 ['M3','M2 + real disposable income YoY']
 ],[100,381])
p('Primary M1 includes sentiment memory to impose a demanding forecasting baseline. A pure macroeconomic-only specification is also disclosed on page 9 so that media is not credited simply for repairing a weak baseline. All main models use the same 39 scored target months and the same complete-case eligibility rule, including M3 income availability.')
p('Each forecast expands the historical training window, requires at least 24 available labeled observations and begins no earlier than January 2023. Features are standardized using training data only. Ridge penalty is fixed at 1, with an unpenalized intercept; no test-month hyperparameter search is performed. The corpus and prompt are fixed before the new core audit.')
h('Uncertainty and missingness')
p('For an empirical interval, each forecast uses the 95th percentile of absolute prior out-of-sample errors whose target values are available in that forecast-origin vintage. At least 12 errors are required. These are symmetric historical error bands, not guaranteed 95% confidence intervals or formally calibrated conformal intervals.')
p('Paired MAE changes use 2,000 circular moving-block bootstrap draws, seed 20261017 and nominal three-month blocks. Draws preserve six observed calendar runs of lengths 1, 5, 3, 6, 11 and 13; they never bridge missing months. Intervals are exploratory and conditional on the observed selected months. Small samples and persistent errors limit their precision.')
h('What the residual means')
p('The displayed perception gap is observed sentiment minus M1 prediction. It is an unexplained forecast error, not an estimated media effect. Omitted household pressures, model misspecification, revisions, method changes and selection can all enter the gap. Lagging media helps temporal ordering but does not remove reverse causality or common shocks.')
p('No causal coefficients, individual exposure elasticities or pre-election attribution are identified. An observational forecast comparison and a future causal design answer different questions.',True)

page(8,'Primary results and interval performance')
fig('final_forecasts.png',188,'Figure 3. No lines are drawn across absent evaluation months. Only 27 months have enough historical errors for the M2 empirical band.')
table(['Model, n=39','MAE','RMSE','Mean error'],[[name,f'{core["metrics"][key]["MAE"]:.3f}',f'{core["metrics"][key]["RMSE"]:.3f}',f'{core["metrics"][key]["mean_error"]:+.3f}'] for key,name in [('persistence','Persistence'),('M1_economic','M1'),('M2_add_media','M2'),('M3_add_household','M3')]],[187,98,98,98])
p('<b>Media increment.</b> M2 minus M1 MAE is +0.189 index points, or about 4.6% higher error. The exploratory 95% block interval is [-0.078, 0.459]. It includes both a small improvement and a deterioration; the evidence is insufficient for stable predictive value in this sample.')
p('<b>Income increment.</b> M3 minus M2 MAE is -0.015, interval [-0.029, 0.0002]. The small change does not demonstrate a robust household-income mechanism. M3 still performs worse than persistence on the common sample.')
p('<b>Intervals need improvement.</b> All three empirical bands cover 23 of 27 scored outcomes, or 85.2%, below their nominal 95% label. Positive mean forecast errors of about two points for the regression models indicate average overprediction. The dashboard carries both calibration counts and the undercoverage warning.')
p('This is a limited null result: it does not show that media never matters. Weak measurement, sparse coverage, missing exposure, limited power and specification choices can hide a real signal. Equally, descriptive negativity alone does not justify adding an unvalidated signal to a financial model.')

page(9,'Robustness, dependence and specification stability')
table(['Specification','OOS n','M1 / comparator MAE','M2 / +media MAE'],[
 ['Primary: >=1 news, >=3 posts','39','4.114','4.303'],
 ['>=2 news, >=5 posts','25','4.411','4.287'],
 ['>=3 news, >=5 posts','17','4.417','4.287'],
 ['Negative share instead of tone','39','4.114','4.375'],
 ['Pure economy, no sentiment memory*','39','11.913','11.441'],
 ['Income + cumulative prices first*','39','3.985','4.070'],
 ['Seasonality + survey phase-in*','39','3.963','3.866']
 ],[226,45,105,105])
p('* Post-hoc specifications. Rows with different n change the evaluation population as well as the threshold; they are not evidence of a coverage dose-response. All figures are preserved rather than selecting the best-looking result. M3 in the pure-economic row has MAE 11.430, still well above persistence (3.687).')
p('In the seasonal/method specification, the media increment is -0.097 with interval [-0.380, 0.182]. Its sign differs from the primary comparison and the interval spans zero. Household controls produce +0.085 with interval [-0.268, 0.483]. These sensitivities reinforce specification uncertainty rather than establishing a winning model.')
h('Residual dependence and coefficient ranges')
res=sup['residual_diagnostics'];st=sup['coefficient_stability']
p(f'Calendar-adjacent residual correlations use 33 pairs: M1 {res["M1_economic"]["lag1_correlation"]:.3f}, M2 {res["M2_add_media"]["lag1_correlation"]:.3f}, M3 {res["M3_add_household"]["lag1_correlation"]:.3f}. Months separated by gaps are not treated as adjacent. This supports dependence-aware uncertainty but does not validate the bootstrap in a small selected panel.')
table(['M2 standardized coefficient','Minimum','Maximum','Share positive'],[[k.replace('_',' '),f'{st[k]["min"]:.3f}',f'{st[k]["max"]:.3f}',f'{st[k]["positive_share"]:.1%}'] for k in ['news_tone','twitter_tone']],[220,87,87,87])
p('Coefficients describe prediction conditional on correlated inputs; their units are sentiment points per training-sample feature standard deviation. They are neither persuasion effects nor portable elasticities. Dependence, alternate thresholds and multiple exploratory specifications preclude confirmatory significance claims.',True)

page(10,'Factual calibration and competing explanations')
p('A supplementary purposive check compares five numeric claims from four headlines with contemporaneous BEA releases. The period, statistic, rate convention, release vintage and timing are matched before comparing numbers. The checked values all match their historical releases; these cases illustrate the process, not a platform accuracy rate. [S7-S10]')
table(['Metadata date / source','Claim and release convention','Reported = official'],[
 ['29 Jul 2021 / ABC News','2021 Q2 real GDP, advance, QoQ annualized','6.5%'],
 ['26 Aug 2022 / ABC News','2022 July headline PCE, YoY','6.3%'],
 ['22 Dec 2022 / Star Tribune','2022 Q3 real GDP, third, QoQ annualized','3.2%'],
 ['30 Jan 2025 / MPR News','2024 Q4 real GDP, advance, QoQ annualized','2.3%'],
 ['30 Jan 2025 / MPR News','2024 annual real GDP, annual over annual','2.8%']
 ],[137,246,98])
p('Official releases precede each archive publication timestamp. The timing conclusion remains conditional on GDELT metadata; publisher timestamps were not independently authenticated. Only these numeric claims were checked, not every word, causal assertion or article. Later revised statistics must not be used to call an accurate historical headline false.')
p('The primary AI labels flag 64 news and 328 Twitter texts as numeric claims not externally checkable from the provided inputs. They remain unchecked, not false. The five-claim illustration is reported separately and does not retroactively upgrade the main coding labels. Twitter numeric claims and fact-check representativeness remain unresolved.')
table(['Explanation','Evidence and unresolved test'],[
 ['Household pressures','Income and cumulative prices improve one comparator; no microdata or distributional attribution. Need debt, rent and real purchasing-power data.'],
 ['Framing / salience','Platform composition differs; tone forecast gains are unstable. Need exogenous exposure or randomized framing.'],
 ['Timing / measurement','Vintage controls, definition audit and survey transition matter. More exact release and publication timestamps remain needed.']
 ],[126,355])
p('No respondent-level cognitive-bias test was conducted. Negativity, political blame and disagreement with a model are not themselves evidence of a bias or misinformation.',True)

page(11,'Proposed causal study and financial application')
h('Future study: randomized framing with identical facts')
p('<b>Estimand.</b> Average effect of assigned framing on a short-run economic outlook score and a stated spending plan among recruited U.S. adults. This would test a local framing effect; it would not directly identify an effect on the national Michigan index. No participant study has been conducted.')
p('<b>Design.</b> Recruit 600 consenting adults through a future survey budget. Randomize a 2 x 2 factorial: neutral versus negative language, and price-level versus inflation-change emphasis. All four arms receive identical, dated, verifiable economic numbers and comparable length. AI generates drafts and checks factual equivalence; a comprehension question verifies receipt. Outcome questions come before treatment-manipulation questions to limit demand effects.')
p('<b>Analysis.</b> Preregister the two outcomes and intent-to-treat factorial main effects, baseline outlook adjustment, subgroup interactions and exclusions before seeing outcomes. Report every arm and the interaction as exploratory unless powered separately. Use randomization inference and heteroskedasticity-robust intervals; adjust the two primary outcome tests, for example Bonferroni alpha 0.025. With 300 subjects per factor level, a simple normal approximation gives a standardized main-effect MDE near 0.25 at 80% power; attrition or clustering requires more participants.')
p('<b>Assumptions and diagnostics.</b> Randomization balance, consistent treatment delivery, no cross-arm spillover, limited differential attrition and a defined follow-up horizon. Preserve assignment logs, pre/post timing and missing outcomes. Include a neutral placebo passage and delayed follow-up. Self-reported intent may differ from actual spending; a convenience online sample may not transport to U.S. households.')
h('Risk monitoring workflow supported by current evidence')
p('A research analyst can compare observed sentiment with a frozen economic benchmark, inspect missing sources and release lags, and review unusual framing alongside household pressure indicators. A large residual triggers source and assumption review, not an automatic trade. Broader data collection, genuinely prospective coding and held-out calibration should precede production use.')
p('Before using a media signal in forecasting or risk allocation, require sustained common-month improvement over persistence, satisfactory interval coverage, source-level robustness, a stable cost envelope and monitoring for model/provider changes. Economic direction and market returns are separate targets; this study contains no return backtest or portfolio performance claim.')
p('This causal proposal satisfies the design component as a proposal. It is not a completed causal finding, a deployed trading system or a claim that media caused pre-election pessimism.',True)

page(12,'Reproduction, sources and submission boundaries')
p('<b>Offline reproduction.</b> The submission archive includes source code, configuration, prompts, coding guide, source manifests, aggregate feature panels, UMCSENT origin-vintage targets and frozen result JSON/CSV files. Run python scripts/reproduce_submission.py to recompute main forecasts and sensitivities, compare them with frozen numbers, and verify the SHA256 manifest. No API key or paid request is needed.')
p('<b>Data restrictions.</b> Private raw posts, full model responses, secrets and gigabytes of news archives are excluded from the shareable archive. Their provenance hashes and local regeneration instructions are retained. Offline reproduction starts from aggregated features; it does not independently re-extract or re-code private raw texts. Recollection/reclassification requires keys and may differ as services change.')
p('<b>Updateable dashboard.</b> output/dashboard.html embeds the analysis snapshot for offline use. Date/model filters, uncertainty bands, residuals, framing, source coverage and numeric evidence are interactive. scripts/build_dashboard.py refreshes the dashboard from processed outputs; it does not fetch data automatically. Regenerate analysis first when adding a new cutoff. Unavailable subgroups remain clearly labeled.')
p('<b>Cost record.</b> Estimated cumulative DeepSeek cost is $1.5849 using configured peak uncached rates; Twitter is $0.5829. These are usage estimates, not an account invoice. This finalization adds no paid model or Twitter calls.')
h('Primary sources and local evidence')
sources=[
 ('S1','ALFRED vintage concepts','https://fred.stlouisfed.org/docs/api/fred/alfred.html'),
 ('S2','BEA PCE price index and GDP release schedule','https://www.bea.gov/data/personal-consumption-expenditures-price-index'),
 ('S3','Michigan monthly headline and components','https://www.sca.isr.umich.edu/tables.html'),
 ('S4','GDELT GKG data and codebook','https://www.gdeltproject.org/data.html'),
 ('S5','TwitterAPI.io documentation','https://docs.twitterapi.io/'),
 ('S6','Michigan April 2024 methodological announcement','https://www.sca.isr.umich.edu/files/methodtransitionannouncement2024.pdf'),
 ('S7','BEA: 2021 Q2 advance GDP','https://www.bea.gov/news/2021/gross-domestic-product-second-quarter-2021-advance-estimate-and-annual-update'),
 ('S8','BEA: July 2022 income and outlays','https://www.bea.gov/news/2022/personal-income-and-outlays-july-2022'),
 ('S9','BEA: 2022 Q3 third GDP estimate','https://www.bea.gov/sites/default/files/2022-12/gdp3q22_3rd_0.pdf'),
 ('S10','BEA: 2024 Q4 and year advance GDP','https://www.bea.gov/news/2025/gross-domestic-product-4th-quarter-and-year-2024-advance-estimate')]
for num,title,url in sources:p(f'{num}. <link href="{url}" color="#254C45">{title}</link>',True)
p('Local evidence: reports/core_analysis.json; core_ai_validation.json; supplemental_analysis.json; final_fact_checks.json; data_audit.json; prompts/economic_coding_v2.txt; labels/CODEBOOK.md. Source metadata, request settings and hash manifests support the operational definitions above.',True)
p('<b>Remaining research limits, not completed findings:</b> representative/full-article coverage; comprehensive bot/ad filtering; independent-family or human accuracy assessment; broad numeric fact checking; respondent-level household/political controls; audience exposure; causal execution; prospective live and market-return validation.',True)

def footer(c,doc):
 c.setStrokeColor(G);c.setLineWidth(.7);c.line(57,50,538,50)
 c.setFillColor(GRAY);c.setFont('Arial',8);c.drawString(57,36,'AI Applications in Finance | Cutoff 16 October 2026');c.drawRightString(538,36,f'{doc.page} / 12')
doc=SimpleDocTemplate(str(OUT/'Economic_Reality_Media_and_Sentiment.pdf'),pagesize=A4,rightMargin=57,leftMargin=57,topMargin=48,bottomMargin=62,title='Economic Reality, Media Narratives and Consumer Sentiment',author='Project research team')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(ROOT/'reports/FINAL_REPORT.md').write_text('\n\n'.join(md)+'\n',encoding='utf-8')
from pypdf import PdfReader
n=len(PdfReader(OUT/'Economic_Reality_Media_and_Sentiment.pdf').pages)
if n!=12:raise ValueError(f'Report must be 12 pages, got {n}; inspect page overflow')
print('Built 12-page final report')
