"""Twelve-page revision centered on the six assigned research questions."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
G=colors.HexColor('#254C45');INK=colors.HexColor('#252b29');GRAY=colors.HexColor('#626c68')
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('Arial-Bold','C:/Windows/Fonts/arialbd.ttf'));pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
S={k:ParagraphStyle(k,fontName='Arial-Bold' if k in ['title','h1','h2','head'] else 'Arial',fontSize=size,leading=leading,textColor=col,spaceAfter=gap) for k,size,leading,col,gap in [('title',25,29,G,13),('h1',18,22,G,12),('h2',11.5,15,G,6),('body',10,14,INK,8),('small',8.3,11.2,GRAY,6),('cell',9,12,INK,0),('head',9,12,colors.white,0)]}
story=[];md=[];pages=0
def p(t,small=False):story.append(Paragraph(t,S['small' if small else 'body']));md.append(t.replace('<b>','**').replace('</b>','**'))
def h(t):story.extend([Spacer(1,5),Paragraph(t,S['h2'])]);md.extend(['','### '+t,''])
def page(n,t):
 global pages
 if pages:story.append(PageBreak())
 pages+=1;story.append(Paragraph(f'{n:02d} / {t}',S['h1']));md.extend(['','## '+t,''])
def table(head,rows,widths):
 vals=[[Paragraph(escape(str(x)),S['head']) for x in head]]+[[Paragraph(escape(str(x)),S['cell']) for x in row] for row in rows]
 t=Table(vals,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),G),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,1),(-1,-1),.4,colors.HexColor('#d9e0dc')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f5')])]))
 story.extend([t,Spacer(1,10)]);md.extend(['| '+' | '.join(head)+' |','|'+'---|'*len(head)]+['| '+' | '.join(map(str,r))+' |' for r in rows])
def fig(n,height,caption):story.append(Image(str(ROOT/'reports/figures'/n),width=481,height=height));p(caption,True)
def load(n):return json.loads((ROOT/'reports'/n).read_text(encoding='utf-8'))
core=load('core_analysis.json');audit=load('cross_family_validation.json');rq=load('research_questions_analysis.json');sup=load('supplemental_analysis.json');d=load('core_media_descriptive.json');r=rq['reference_comparisons']['2017_2019']

page(1,'Six research questions: findings and limits')
story.append(Paragraph('Media bias and the<br/>U.S. consumer sentiment gap',S['title']))
p('AI Applications in Finance | Revised research report | Cutoff: 16 October 2026',True)
p('This report addresses six questions about media measurement, pre-midterm sentiment, macroeconomic explanations, perceptual mechanisms, forecasting and evidence against a media-bias account. It reports what the data support and leaves unsupported causal or psychological claims unidentified.')
table(['Research question','Direct answer from this study'],[
 ['RQ1. Measure media bias?','Measure tone, salience, framing and numeric calibration separately. Observed negativity alone is not evidence of bias.'],
 ['RQ2. Depress sentiment before the midterms?','No causal effect or number of index points is identified. Exposure and exogenous variation are missing.'],
 ['RQ3. How much can three macro indicators explain?','Descriptive R-squared 50.2%; selected-reference accounting share 37.1%, with 43.3% under another reference. Neither is causal.'],
 ['RQ4. Which perceptual mechanisms are measurable?','Content-side proxies are measurable. Negativity, availability, confirmation and anchoring effects in people are not directly identified.'],
 ['RQ5. Improve predictions beyond economics?','A small gain over pure economics disappears against an economic model with sentiment memory. Neither comparison establishes stable media value.'],
 ['RQ6. What would contradict media bias?','Specify testable versions of the claim. Current results weaken predictive claims; causal persuasion still needs an exposure-based design.']
 ],[153,328])
p('<b>Main forecasting result.</b> On 39 common months, MAE is 11.913 for pure economics and 11.441 after media. With sentiment memory, MAE changes from 4.114 to 4.303 after media; persistence scores 3.687. Both paired media-change intervals span zero. Predictive gains are baseline-dependent, not robust evidence of a media mechanism.')
p('<b>Practical implication.</b> Use the results to review assumptions and data coverage. The project supplies no validated trading rule, causal media effect or estimate of irrational consumer pessimism. The revised 300-item measurement review is described transparently on page 9.',True)

page(2,'What the Michigan sentiment index measures')
p('The Index of Consumer Sentiment (ICS) is built from consumer survey answers, not by combining GDP, inflation and unemployment. Michigan\'s survey samples U.S. households; its FAQ reports that final monthly readings typically reflect about 1,000 interviews. The five index components are summarized below. [S1-S2]')
table(['Component','Question concept, paraphrased','Subindex'],[
 ['x1','Family finances now compared with one year ago','Current conditions'],
 ['x2','Expected family finances one year ahead','Expectations'],
 ['x3','Expected national business conditions over one year','Expectations'],
 ['x4','Expected national conditions over five years','Expectations'],
 ['x5','Whether now is a good time to buy major household items','Current conditions']
 ],[77,286,118])
p('Each relative score is 100 + favorable percentage - unfavorable percentage, rounded to an integer. The headline formula is <b>ICS = (x1 + x2 + x3 + x4 + x5) / 6.7558 + 2</b>. The divisor reflects the 1966 base; the constant adjusts an early sample-design change. ICS is an index, not a favorable-response percentage or an objective GDP score. [S1]')
p('A family can acknowledge output growth but report expensive durable goods, weak purchasing power or a poor future outlook. The question design therefore makes household affordability and expectations relevant; disagreement with headline economic indicators is not automatically a perceptual error.')
h('Study information sets')
p('The macro panel has 200 target months, January 2010-August 2026. The fixed-window media corpus covers October 2019-July 2026. Forecast evaluation uses 39 common, noncontinuous target months during January 2023-August 2026. The latest three released target months used in RQ3 accounting are June-August 2026.')
p('Current Conditions and Expectations monthly series are included descriptively; no historical vintages of those subindices enter the forecasts. The official chart XLS files contain three-month means, so monthly CSVs are used instead. Michigan phased from phone to web interviews in April-July 2024; that change is documented and tested as a supplemental control. [S3-S4]')
p('The study does not cover the final weeks before the 2026 midterms. No unreleased target or newly revised value is treated as historically available.',True)

page(3,'RQ1 / How can we measure media bias?')
p('<b>Answer.</b> Represent coverage with separate, auditable measures, then compare it with a defensible factual and coverage benchmark. We measure selected text characteristics. We do not have a calibrated scalar measure of overall media bias.')
fig('final_frames.png',162,'Figure 1. Shares of eligible sampled headlines (n=247) and posts (n=733). These are pooled item shares, not exposure or population estimates. Primary descriptive labels remain the frozen corpus coding.')
table(['Dimension','Measured here','Needed to call it bias'],[
 ['Tone','Negative/neutral/positive/mixed/uncertain','A matched-event or factual benchmark; adverse events can justify adverse tone'],
 ['Salience','Multi-label topic shares, such as prices or jobs','A relevant event universe and comparable outlet/time coverage'],
 ['Framing','Price levels/changes, household/national, present/future, emotional language, attribution','Comparable facts presented differently; not simply disagreement with a model'],
 ['Calibration','Numeric-claim flags plus 5 release-vintage checks','Representative checks of measures, periods, units and available releases']
 ],[77,184,220])
p('Emotional/mixed language appears in 6.9% of sampled eligible news and 70.3% of posts; political blame/both appears in 10.5% and 47.2%. These differences describe selected formats and sources. Keyword filtering, headline length and author selection can generate them without biased reporting.')
p('A stronger bias study would match outlets covering the same release or event and condition on information available then. It would distinguish omissions, framing and factual inaccuracies, while auditing reposts, bots and sample coverage. Our sparse headline sample cannot implement that full benchmark.')
p('Content supply is observed; engagement and actual audience exposure are not. Negative facts, criticism and political attribution are not automatically bias.',True)

page(4,'RQ2 / Did bias depress pre-midterm sentiment?')
p('<b>Answer.</b> The data do not identify how many sentiment points, if any, media bias caused before the midterms. The project can compare predictions and describe candidate channels, but cannot turn an unexplained residual into a causal effect.')
fig('final_forecasts.png',187,'Figure 2. Observed sentiment and origin-available economic/media forecasts on common months. Model errors are not identified persuasion effects; missing months remain missing.')
table(['Identification issue','Why it matters here'],[
 ['Shared shocks','Inflation, policy changes and economic disruption can jointly move news and sentiment.'],
 ['Reverse causality','Media can respond to consumer anxiety and political demand rather than cause it.'],
 ['Exposure mismatch','A sampled headline/post is not evidence that a survey respondent saw, trusted or remembered it.'],
 ['Timing and horizon','Archive publication dates are metadata; scored sentiment ends in August and media in July, not the final pre-election weeks.']
 ],[120,361])
p('Lagging media to the preceding month gives temporal ordering for forecasting, but does not remove common causes or endogenous exposure. Even a favorable media coefficient would remain an association; a coefficient on a text proxy is not a persuasion elasticity.')
p('<b>How to determine an effect.</b> A future study could randomize otherwise identical, verified economic information across language and price-framing treatments, measure prior outlook and subsequent sentiment/spending intention, and report intent-to-treat effects. The detailed proposal appears on page 11. No experiment has been executed.')
p('Transport from an experimental or regional effect to the national Michigan index requires assumptions about population, treatment intensity, actual exposure and time persistence. An election date alone supplies none of those assumptions.',True)

page(5,'RQ3 / How much can macro indicators explain?')
p('<b>Answer.</b> The three-indicator model accounts for meaningful variation, but leaves a large model-dependent discrepancy. We distinguish descriptive fit, reference-period accounting and genuinely chronological forecasts; they are different quantities.')
p(f'<b>Descriptive association.</b> OLS on all {rq["fitting_sample"]["n"]} cutoff-available monthly targets, with unemployment, headline PCE YoY and real GDP growth plus an intercept, gives R-squared <b>{rq["in_sample_R2"]:.3f}</b>. This is 50.2% of within-sample variation around the sample mean, not 50.2% of a causal perception gap. No sentiment lag or media is included.')
table(['June-August 2026 vs 2017-2019','Index-point change'],[
 ['Observed sentiment: 97.039 to 52.133',f'{r["observed_change"]:+.3f}'],
 ['Unemployment-associated component',f'{r["components_points"]["unemployment"]:+.3f}'],
 ['Inflation-associated component',f'{r["components_points"]["pce_yoy"]:+.3f}'],
 ['GDP-growth-associated component',f'{r["components_points"]["gdp_growth"]:+.3f}'],
 ['Sum associated with the three macro indicators',f'{r["model_associated_change"]:+.3f}'],
 ['Change left in the model residual',f'{r["residual_change"]:+.3f}']
 ],[350,131])
p('<b>Accounting calculation.</b> Each component is its fitted coefficient times the change in the average origin-available indicator. The associated -16.656 points are <b>37.1%</b> of the observed -44.906-point decline. Using 2015-2019 instead gives 43.3%. Both references and the latest-three-month window are post-hoc choices; this is a descriptive accounting exercise, not a structural counterfactual.')
p('The remaining 62.9% under the first reference is <b>not a media share</b>. It can contain purchasing-power pressures, omitted variables, changing relationships, survey measurement and model error. The small GDP component concerns these chosen windows and this model; it does not show GDP never matters.')
p('<b>Forecast check.</b> On the 39 common future targets, pure-economic RMSE is 13.759 versus 12.615 for the origin-available training mean and 4.428 for persistence. Its squared-error skill versus that training mean is -0.190. A model can fit historical variation while forecasting poorly, so the 37.1% accounting fraction should not be treated as a reliable causal explanation.')
p('Source: research_questions_analysis.json. All macro inputs retain their historical origin vintages; evaluation-vintage sentiment is used for this explicitly retrospective fit. The main expanding-window forecasting exercise remains separate.',True)

page(6,'RQ4 / Which perceptual mechanisms can we test?')
p('<b>Answer.</b> We can quantify content-side proxies and test their predictive associations. We cannot directly estimate the four psychological mechanisms in consumers from these aggregate texts and survey totals.')
table(['Mechanism','What these data measure','What remains unmeasured'],[
 ['Negativity bias','Frequency/tone of adverse content; emotional language','A stronger consumer response to an equally informative negative message than to a positive one'],
 ['Availability bias','Topic salience in sampled content, for example price or job mentions','What respondents encounter, recall most easily, or use when answering the survey'],
 ['Confirmation bias','Political credit/blame in content; disagreement across texts','Prior individual beliefs, selective exposure, and asymmetric belief updating'],
 ['Anchoring to past prices','Price-level framing and cumulative PCE increase since December 2018','An individual reference price and its causal effect after controlling real affordability']
 ],[97,184,200])
p('Price-level/both framing occurs in 11.3% of eligible headlines and 14.7% of posts. That shows whether a text emphasizes cost levels, not whether a reader is anchored. Lower inflation can coexist with persistently high prices and genuine household pressure; neither is intrinsically irrational.')
p('Adding national real income and cumulative prices before media improves one common-sample comparator to MAE 3.985; adding media then gives 4.070. This preserves household pressure as a plausible competing explanation. It does not isolate purchasing power from anchoring or establish a household causal effect.')
p('Political blame/both in 47.2% of sampled posts does not prove confirmation bias. Party identification, prior beliefs and respondent-linked feeds are absent. Similarly, the predominance of negative posts does not measure a larger psychological weight on bad news.')
h('What a mechanism-specific follow-up would need')
p('For negativity: balanced positive/negative messages with equivalent information. For availability: measured exposure and delayed recall. For confirmation: baseline beliefs and randomized congruent/incongruent information. For anchoring: randomized reference prices alongside income, debt, housing and spending-basket measures. Those studies are proposals, not completed results.')
p('The mechanism table is the boundary between observed content, a proxy and a psychological effect. No bias prevalence or respondent-level mechanism coefficient is reported.',True)

page(7,'RQ5 / Does media improve sentiment forecasts?')
p('<b>Answer.</b> It modestly improves a weak pure-economic baseline, but fails against an economic baseline with sentiment memory. Both exploratory paired intervals include zero, and all regression versions lose to persistence on the common sample.')
table(['Common-sample specification, n=39','MAE','RMSE'],[
 ['Economics only','11.913','13.759'],
 ['Economics only + news/Twitter tone','11.441','13.073'],
 ['Economics + sentiment memory (M1)','4.114','4.803'],
 ['M1 + news/Twitter tone (M2)','4.303','4.835'],
 ['M2 + real income growth (M3)','4.288','4.818'],
 ['Persistence: latest available sentiment','3.687','4.428']
 ],[295,93,93])
table(['Media increment: change in MAE','Estimate','Exploratory 95% block interval'],[
 ['Against economics only','-0.471','[-1.093, 0.164]'],
 ['Against economics + memory','+0.189','[-0.078, 0.459]']
 ],[225,71,185])
p('Negative changes mean improvement. The small pure-economic gain cannot be generalized into stable forecasting value: the baseline itself loses to a historical training mean, the interval spans zero and the gain reverses when a strong sentiment-memory control is included. It would also be wrong to say that no specification ever improves.')
p('All main comparisons use identical test months and complete-case rules, expanding training with at least 24 available targets, training-only standardization and fixed ridge penalty 1. Media uses the preceding calendar month. Neither feature standardization nor target training sees a future evaluation vintage.')
p('The nominal 95% empirical bands cover only 23 of 27 scoreable outcomes (85.2%). They use prior released forecast errors, but are not calibrated coverage guarantees. Sparse months, measurement disagreement and correlated errors limit confidence in small gains.')
p('The economic-only specification is a disclosed post-hoc supplement; the original economic-plus-memory primary remains frozen. Additional coverage, negative-share, price-level, seasonal and survey-mode sensitivities are retained on page 10. No best-looking specification replaces the original result.',True)

page(8,'RQ6 / What evidence would contradict media bias?')
p('<b>Answer.</b> Separate testable versions of the media explanation. Evidence against false numeric reporting, incremental prediction, a psychological mechanism and causal persuasion need not be the same.')
table(['Testable claim','Evidence that would challenge it','What we actually observe'],[
 ['False economic numbers drive pessimism','Representative contemporaneous checks find the relevant numeric claims accurate','5 claims in 4 purposively selected headlines match BEA releases. This challenges falsity for those claims only.'],
 ['Media adds a stable forecasting signal','No repeatable gain against strong baselines across samples/specifications','Small economics-only gain reverses with sentiment memory; both paired intervals span zero.'],
 ['The gap mostly reflects distorted perception','Affordability, income or measurement explain the gap under credible comparisons','Income/price controls and survey-mode sensitivity matter, but their causal shares are not identified.'],
 ['Media exposure causes lower sentiment','A well-powered randomized exposure study tightly excludes a meaningful negative effect','Not tested. No respondent exposure or exogenous assignment is available here.'],
 ['Negative coverage leads sentiment','Timing/placebo tests instead show sentiment or common shocks leading coverage','Not established. Lagging sampled content alone is not a valid causal test.']
 ],[105,178,198])
p('Accurate numbers can still be framed selectively, and inaccurate numbers are not required for persuasion. The small fact-check exercise therefore does not validate overall neutrality. Likewise, no incremental predictive value does not logically prove no causal influence: weak exposure proxies and noise can conceal an effect.')
p('For a future causal test, define a meaningful effect size and report intervals capable of excluding it. A nonsignificant result with a wide interval is inconclusive. Specify timing, negative controls and alternative household explanations before collecting outcomes, rather than deciding what counts as a refutation after seeing the result.')
p('Our current position is narrower than either extreme: a causal media-bias explanation is not demonstrated, but not decisively falsified. The evidence particularly weakens a claim of stable predictive value for these measured tones.',True)

page(9,'Measurement, independent review and provenance')
p('Primary coding remains the frozen 1,473-item corpus, with 1,470 valid Flash-coded records. We do not selectively replace main features with audit labels. The revised independent review pairs cached DeepSeek V4 Pro judgments with 300 direct GPT judgments made by the assistant in this Codex conversation. <b>No human annotation was performed.</b>')
table(['Revised review layer','Attempts / valid','Interpretation'],[
 ['DeepSeek V4 Pro','300 / 293','Original independent role-B cache, same full item inputs'],
 ['Direct GPT reviewer','300 / 300','Assistant read each text and assigned categories and literal evidence; no heuristic classifier'],
 ['All paired records','293','Tone agreement 65.2%; kappa 0.539'],
 ['Held-out portion','200 / 196 pairs','Tone agreement 63.8%; kappa 0.522'],
 ['Development portion','100 / 97 pairs','Retained separately; no retuning to agreement']
 ],[136,99,246])
v=audit['held_out_200']['agreement']['dimensions']
table(['Held-out dimension','Agreement / kappa','Held-out dimension','Agreement / kappa'],[[a.replace('_',' '),f'{v[a]["agreement"]:.1%} / {v[a]["kappa"]:.3f}',b.replace('_',' '),f'{v[b]["agreement"]:.1%} / {v[b]["kappa"]:.3f}'] for a,b in [('language_style','price_frame'),('scope_frame','time_frame'),('factual_calibration','political_attribution'),('us_relevance','topics_exact_set')]],[137,103,138,103])
p('The same 150 headlines and 150 posts are retained, with 50 development and 100 held-out records per platform. GPT categories were sealed before item-level V4 comparison; scripts expand explicitly authored shorthand and validate the nine dimensions, IDs, hashes and verbatim evidence. The script does not make semantic judgments. All seven invalid V4 records remain in attempt denominators.')
p('Independence is limited: this conversation had already seen project-level aggregate findings and a few illustrative headlines. It is not a prospectively isolated blind experiment. The exact immutable GPT model identifier is not exposed. V4 aliases also need not identify frozen weights. Disagreements remain disagreements; the earlier same-family third-call consensus is historical, not the new pair\'s truth label.')
p('Changing reviewers lowered held-out tone agreement from the earlier same-family 75.5% to 63.8%; the reviewer pair changed, so this is measurement sensitivity, not a controlled model-performance experiment or an accuracy comparison. No new paid API call was needed. Prompt/input hashes and private literal evidence are retained; shareable labels omit raw text and rationale.',True)

page(10,'Sampling, definitions and robustness')
p('Sampling uses fixed windows in 82 months: 8 news archive slots and 2 one-hour Twitter windows per month. Fourteen of 656 news slots were unavailable. The source list includes 18 national and 33 local/regional domains. Capped latest-results pages and keyword filters make the corpus sparse and nonrepresentative. News is headlines, not full articles. [S5-S6]')
table(['Corpus stage','News','Twitter/X'],[['Timestamp-eligible raw candidates','540','3,160'],['Frozen coding corpus','489','984'],['US-economic and timing-eligible','247','733'],['Scorable tone','243','731']],[259,111,111])
p('Main month eligibility is at least 1 scored headline and 3 posts, giving 72 eligible months. News averages equally across observed outlets after within-outlet means; Twitter averages sampled eligible posts. Exact/normalized duplicates are removed; semantic duplication, bots and ads are incompletely resolved. Neither publication metadata nor audience exposure is independently authenticated.')
table(['Specification','OOS n','Comparator MAE','+ media MAE'],[['Primary: >=1 news / >=3 posts','39','4.114','4.303'],['>=2 news / >=5 posts','25','4.411','4.287'],['>=3 news / >=5 posts','17','4.417','4.287'],['Negative share replaces tone','39','4.114','4.375'],['Income + cumulative prices first*','39','3.985','4.070'],['Seasonality + survey phase-in*','39','3.963','3.866']],[221,48,106,106])
p('* Post-hoc diagnostics. Stricter coverage changes the test population; it is not a dose-response. Household-first and seasonality/method media-change intervals both span zero. M2 calendar-adjacent errors correlate 0.433 over 33 pairs; gaps are not treated as adjacent. The six-run block bootstrap preserves the observed calendar gaps.')
p('Unemployment is BLS U-3 seasonally adjusted. Inflation is headline PCEPI YoY in the same origin vintage; GDP growth is latest released GDPC1 quarterly growth annualized, never interpolated monthly. The supplied workbook\'s PCE column matches core PCE in all 200 comparable months and is replaced analytically, not overwritten. Its unreleased 2026 Q3 GDP entry is quarantined. [S7-S8; local audit]')
p('The 1,005 required ALFRED files cover five series at 201 vintages. Snapshots prove availability by month-end, not first-release times, and can lag Michigan/BEA/BLS releases. Training labels come from each forecast origin; the 16 October evaluation vintage is never fed to earlier fits.',True)

page(11,'Causal follow-up and financial use')
h('Future design: equal facts, randomized framing')
p('Recruit 600 consenting U.S. adults under a future study budget. Randomize a 2 x 2 factorial: neutral versus negative language and price-level versus inflation-change emphasis. Give every arm the same dated, verified economic numbers and comparable message length. A separate comprehension check verifies receipt; outcome questions precede manipulation questions to reduce demand effects.')
p('Preregister economic outlook and stated spending as two primary outcomes, assignment, baseline adjustment, attrition, exclusions and factorial main effects. Treat the interaction and subgroup interactions as exploratory unless powered. Use intent-to-treat estimation, randomization inference and heteroskedasticity-robust intervals. Adjust the two primary outcome tests, for example Bonferroni alpha 0.025. With 300 respondents per factor level, a simple normal approximation gives main-effect MDE about 0.25 standard deviation at 80% power before attrition.')
p('Check randomization balance, consistency of treatment delivery, spillovers, differential attrition and delayed persistence. Include a neutral placebo passage and delayed recall. Linking exposure and baseline belief would enable more specific tests of availability and confirmation; randomized reference prices could probe anchoring while measuring affordability.')
p('The estimand is a short-run framing effect among recruited adults. It does not automatically transport to national ICS or actual consumption. Self-reported intentions can differ from behavior; convenience samples, real-world repetition and heterogeneous trust remain problems. No experiment, recruitment or causal effect is reported as completed.')
h('Application supported by the present results')
p('A research analyst can use the dashboard to inspect observed-versus-model sentiment, household price/income pressure, framing composition, official release evidence and missing sources. A large gap is a prompt to inspect data and assumptions. The best measured common-sample benchmark is persistence; there is no basis for automatic portfolio allocation from these media scores.')
p('Before production use, require genuinely prospective coding, wider sources, stable gains against persistence on common held-out dates, interval calibration, independent measurement checks and a cost-monitoring plan. Predicting consumer sentiment and predicting asset returns are different tasks. No return backtest or trading performance is claimed.')
p('The proposal is designed to make future contradictions informative: sufficiently precise null exposure effects would challenge a meaningful persuasion claim, while actual evidence of differential responses could support one. It does not prejudge the answer.',True)

page(12,'Sources, reproduction and delivery boundary')
p('<b>Reproduction.</b> The revised local submission contains code, configs, coding guide, frozen prompts, minimized categorical votes, public vintage snapshots, aggregate features and final results. The offline verifier rebuilds macro features, media aggregates, both the historical and revised review arithmetic, forecasts, sensitivities and RQ3 accounting. The SHA256 manifest protects delivered files. No key or paid call is required for statistical reproduction.')
p('Private texts, evidence quotes, rationales, complete model responses and large archives stay outside the shareable package. Statistical reproduction does not independently regenerate the original text extraction or model judgments. Current dashboard data are embedded locally; regeneration is explicit rather than an unattended paid collector. Estimated cumulative paid usage remains DeepSeek $1.5849 and Twitter $0.5829, not a provider invoice.')
sources=[('S1','Michigan index calculation','https://data.sca.isr.umich.edu/fetchdoc.php?docid=75432'),('S2','Michigan survey FAQ','https://data.sca.isr.umich.edu/faq.php'),('S3','Michigan monthly tables','https://www.sca.isr.umich.edu/tables.html'),('S4','Michigan April 2024 survey transition','https://www.sca.isr.umich.edu/files/methodtransitionannouncement2024.pdf'),('S5','GDELT archive documentation','https://www.gdeltproject.org/data.html'),('S6','TwitterAPI.io documentation','https://docs.twitterapi.io/'),('S7','ALFRED vintage documentation','https://fred.stlouisfed.org/docs/api/fred/alfred.html'),('S8','BEA headline PCE definition','https://www.bea.gov/data/personal-consumption-expenditures-price-index'),('S9','BEA 2021 Q2 advance GDP','https://www.bea.gov/news/2021/gross-domestic-product-second-quarter-2021-advance-estimate-and-annual-update'),('S10','BEA July 2022 income and outlays','https://www.bea.gov/news/2022/personal-income-and-outlays-july-2022'),('S11','BEA 2022 Q3 third GDP','https://www.bea.gov/sites/default/files/2022-12/gdp3q22_3rd_0.pdf'),('S12','BEA 2024 Q4/year advance GDP','https://www.bea.gov/news/2025/gross-domestic-product-4th-quarter-and-year-2024-advance-estimate')]
for n,title,url in sources:p(f'{n}. <link href="{url}" color="#254C45">{title}</link>',True)
p('Numeric illustration [S9-S12]: 2021 Q2 GDP 6.5%; July 2022 headline PCE YoY 6.3%; 2022 Q3 third GDP 3.2%; 2024 Q4 GDP 2.3% and annual GDP 2.8%. Five claims in four purposive headlines match the contemporaneous releases, conditional on archive publication metadata. Other numeric claims remain unchecked, not false.',True)
p('Local authoritative outputs: research_questions_analysis.json; cross_family_validation.json; core_analysis.json; supplemental_analysis.json; final_fact_checks.json; data_audit.json. Earlier report/deck versions remain historical and are superseded by this six-question revision.',True)
p('<b>Limits retained:</b> no representative exposure, human accuracy standard, comprehensive fact-checking, household/party microdata, identified psychological effect, causal execution, prospective trading test or final-weeks election coverage. These are research limits, not results silently filled by assumptions.',True)

def footer(c,doc):
 c.setStrokeColor(G);c.line(57,50,538,50);c.setFillColor(GRAY);c.setFont('Arial',8);c.drawString(57,36,'Six research questions | Cutoff 16 October 2026');c.drawRightString(538,36,f'{doc.page} / 12')
target=OUT/'Six_Research_Questions_Report.pdf'
doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=57,rightMargin=57,topMargin=48,bottomMargin=62,title='Media Bias and Consumer Sentiment: Six Research Questions',author='Project research team');doc.build(story,onFirstPage=footer,onLaterPages=footer)
(ROOT/'reports/SIX_RESEARCH_QUESTIONS_REPORT.md').write_text('\n\n'.join(md)+'\n',encoding='utf-8')
assert len(PdfReader(target).pages)==12,'Repair report page overflow before delivery'
print('Built revised 12-page six-question report')
