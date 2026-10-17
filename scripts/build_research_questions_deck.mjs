import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const RUNTIME='C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies';process.env.RUNTIME_NODE_MODULES=RUNTIME+'/node/node_modules';
const SKILL='C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const {Presentation,PresentationFile,FileBlob}=await import(pathToFileURL(RUNTIME+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'));
const {applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs'));
const TMP=path.join(ROOT,'tmp/six_questions_deck_english'),OUT=path.join(ROOT,'output/presentation');await fs.mkdir(TMP,{recursive:true});await fs.mkdir(OUT,{recursive:true});
const read=async n=>JSON.parse(await fs.readFile(path.join(ROOT,'reports',n),'utf8'));
const rq=await read('research_questions_analysis.json'),core=await read('core_analysis.json'),audit=await read('cross_family_validation.json');
const G='#254C45',A='#a37d46',K='#252b29',M='#63726a';const deck=Presentation.create({slideSize:{width:1280,height:720}});deck.theme.defaultFont='Arial';const notes=[];const script=JSON.parse(await fs.readFile(path.join(ROOT,'configs/presentation_script.json'),'utf8'));if(script.slides.length!==10)throw new Error('Expected ten script entries');
function t(s,text,x,y,w,h,size=28,bold=false,color=K){let sh=s.shapes.add({geometry:'textbox',name:text.slice(0,55),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});sh.text=text;sh.text.style={typeface:'Arial',fontSize:size,bold,color};return sh}
function slide(title,answer){let s=deck.slides.add();s.background.fill='#ffffff';t(s,title,64,44,1150,90,44,true,G);t(s,answer,68,143,1135,69,29,true,K);t(s,'Cutoff: 16 October 2026',68,673,1010,25,18,false,M);t(s,String(deck.slides.items.length).padStart(2,'0'),1160,673,50,25,18,true,G);return s}
function tbl(s,values,widths,y=230,h=315,size=25){let q=s.tables.add({rows:values.length,columns:values[0].length,left:67,top:y,width:1146,height:h,columnWidths:widths,values});for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){let cell=q.getCell(r,c);cell.fill=r===0?G:r%2?'#f1f5f2':'#ffffff';cell.text.style={typeface:'Arial',fontSize:size,color:r===0?'#ffffff':K,bold:r===0}}return q}
function chart(s,options){let q=s.charts.add('bar',options);applyPresentationChartFont(q,{fontFamily:'Arial'});return q}
function note(s,sources){const n=script.slides[deck.slides.items.length-1];if(n.slide!==deck.slides.items.length)throw new Error('Script order mismatch');const {en,seconds}=n;s.speakerNotes.text='SPOKEN ENGLISH\n\n'+en+'\n\nREFERENCE ONLY — DO NOT READ ALOUD\n\nSources:\n'+sources.join('\n');notes.push({slide:n.slide,seconds,en,sources})}

let s=deck.slides.add();s.background.fill='#ffffff';t(s,'AI APPLICATIONS IN FINANCE',69,62,1120,32,22,true,G);t(s,'Media bias and the\nconsumer sentiment gap',64,170,1148,175,60,true,G);t(s,'Six research questions. Findings, explanations and limits.',69,416,1120,90,32,false,K);t(s,'U.S. evidence through 16 October 2026',69,611,1120,35,24,false,M);
note(s,['Six-question report, page 1']);

s=slide('First, what does the Michigan index measure?','It measures survey answers, not a formula made from GDP and inflation.');
tbl(s,[['Current conditions','Expectations'],['Family finances compared with a year ago','Family finances one year ahead'],['Whether now is a good time to buy major goods','National conditions over one year and five years']],[573,573],255,214,28);
t(s,'Five relative scores → divide their sum by 6.7558 → add 2',69,513,1135,58,30,true,G);t(s,'An index reading of 60 does not mean 60% of people are confident.',69,596,1135,56,27,false,M);
note(s,['https://data.sca.isr.umich.edu/fetchdoc.php?docid=75432','https://data.sca.isr.umich.edu/faq.php','Report page 2']);

s=slide('RQ1 | How can we measure media bias?','We can measure content features. Negativity alone does not prove bias.');
chart(s,{position:{left:65,top:245,width:1144,height:290},categories:['Political blame / both','Emotional / mixed language'],series:[{name:'News (n=247)',values:[10.5,6.9],fill:G},{name:'Twitter (n=733)',values:[47.2,70.3],fill:A}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:60},hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:24}},xAxis:{textStyle:{fontSize:25},majorGridlines:null},yAxis:{min:0,max:85,majorUnit:20,numberFormatCode:'0',title:'Percent of sampled eligible items',textStyle:{fontSize:24},majorGridlines:{fill:'#e0e7e2',width:1}},dataLabels:{showValue:true,numberFormatCode:'0.0',position:'outEnd',textStyle:{fontSize:25,fill:K}}});
t(s,'Tone · topic salience · framing · factual calibration',69,559,1132,42,29,true,G);t(s,'To establish bias, compare coverage of the same facts and events.',69,613,1132,40,26,false,M);
note(s,['Report page 3','reports/core_media_descriptive.json']);

s=slide('RQ2 | Did media depress pre-election sentiment?','We cannot identify a causal effect, or a number of index points.');
tbl(s,[['What we have','What is missing'],['Monthly text measures and sentiment forecasts','Which respondents saw which content'],['A gap between observed and predicted sentiment','Exogenous exposure that separates cause from response'],['Historical media through July; scored sentiment through August','Coverage of the final pre-election weeks']],[573,573],245,278,26);
t(s,'A future test: identical economic facts, randomly assigned framing.',69,568,1132,77,29,true,G);
note(s,['Report pages 4 and 11','reports/core_analysis.json']);

s=slide('RQ3 | How much can the economy explain?','Three macro indicators account for part of the decline, under a chosen model.');
t(s,'97.04 → 52.13',69,237,1128,69,51,true,G);t(s,'2017–2019 mean → June–August 2026 mean',69,316,1128,40,26,false,M);
tbl(s,[['Accounting for the 44.91-point decline','Index points'],['Unemployment + inflation + GDP growth','−16.66'],['Change left in the model residual','−28.25']],[840,306],386,167,27);
t(s,'Macro share: 37.1%  |  2015–2019 reference: 43.3%',69,573,1132,42,30,true,G);t(s,'Post-hoc descriptive accounting, not causal attribution. In-sample R²: 0.502.',69,624,1132,34,24,false,M);
note(s,['Report page 5','reports/research_questions_analysis.json']);

s=slide('RQ4 | Which perceptual mechanisms can we test?','We observe content-side proxies, not psychological effects in consumers.');
tbl(s,[['Mechanism','Observed proxy','Missing evidence'],['Negativity bias','Negative tone and emotional wording','A stronger response to equally informative bad news'],['Availability bias','Topic salience in sampled content','Actual exposure, recall and use in survey answers'],['Confirmation bias','Political credit and blame','Prior beliefs, selective exposure and belief updating'],['Past-price anchoring','Price-level framing; cumulative PCE','Individual reference prices, separated from affordability']],[217,410,519],236,326,25);
t(s,'Real affordability pressure can explain pessimism without a cognitive bias.',69,595,1132,63,28,true,G);
note(s,['Report page 6','reports/core_media_descriptive.json','reports/supplemental_analysis.json']);

s=slide('RQ5 | Does media improve sentiment forecasts?','The answer depends on the baseline; the gain is not stable.');
chart(s,{position:{left:75,top:247,width:1118,height:275},categories:['Persistence','+ media + income','+ media','Economy + memory'],series:[{name:'MAE',values:[3.687,4.288,4.303,4.114],fill:G}],hasLegend:false,barOptions:{direction:'bar',grouping:'clustered',gapWidth:65},xAxis:{textStyle:{fontSize:25},majorGridlines:null},yAxis:{min:0,max:5,majorUnit:1,numberFormatCode:'0.0',title:'Common 39 months: MAE, lower is better',textStyle:{fontSize:24},majorGridlines:{fill:'#e0e7e2',width:1}},dataLabels:{showValue:true,numberFormatCode:'0.000',position:'outEnd',textStyle:{fontSize:25,fill:G,bold:true}}});
t(s,'Pure economics: 11.913 → 11.441 with media (small improvement).',69,548,1132,42,27,true,G);t(s,'Both media-change intervals span zero. Persistence remains strongest.',69,610,1132,42,26,false,M);
note(s,['Report pages 7 and 10','reports/core_analysis.json','reports/research_questions_analysis.json']);

s=slide('RQ6 | What would contradict media bias?','A useful explanation must have tests that could weaken or reject it.');
tbl(s,[['Claim to test','Challenging evidence','Our result'],['Stable forecasting value','No repeatable gain over strong baselines','Weakens the predictive claim'],['False numbers drive the gap','Representative historical fact checks match releases','Five claims match; sample too small for a general conclusion'],['Psychological distortion dominates','Affordability or measurement explains the gap','Plausible alternatives remain'],['Exposure causes pessimism','Precise randomized null excludes a meaningful effect','Not tested here']],[280,490,376],238,334,24);
t(s,'No predictive gain is not proof of no causal effect.',69,604,1132,44,30,true,G);
note(s,['Report page 8','reports/final_fact_checks.json']);

s=slide('What should we take from these six answers?','The measured gap has several plausible explanations. Media causation is unproven.');
t(s,'Economics matters, but three headline indicators are incomplete.',69,266,1125,79,34,true,G);t(s,'Content patterns suggest channels; they do not measure people’s biases.',69,382,1125,85,32,false,K);t(s,'Use the dashboard for research review, not an automatic trading signal.',69,513,1125,85,32,false,K);
note(s,['Report pages 1 and 11']);

s=slide('Appendix | Measurement review and study limits','Independent review of 300 stratified texts; disagreement is retained.');
tbl(s,[['Review statistic','Result'],['Sample','150 headlines + 150 posts'],['Valid pairs','293 of 300 attempted'],['Held-out portion','196 valid pairs from 200 attempted'],['Held-out tone agreement / kappa','63.8% / 0.522']],[660,486],250,265,27);
t(s,'Model-based review, not a human accuracy benchmark.\nSource coverage is sparse and actual audience exposure is unavailable.',69,567,1130,82,26,false,M);
note(s,['reports/cross_family_validation.json','data/shareable/cross_family_v2/protocol.json']);

const total=notes.reduce((x,n)=>x+n.seconds,0);await fs.writeFile(path.join(TMP,'speaker_notes.json'),JSON.stringify(notes,null,2));
await fs.writeFile(path.join(ROOT,'reports/SIX_QUESTIONS_SPEAKER_SCRIPT.en.md'),'# '+script.title+'\n\n'+script.intro+'\n\n## Delivery notes\n\n'+script.delivery_notes.map(v=>'- '+v).join('\n')+'\n\n'+notes.map(n=>'## Slide '+n.slide+(n.seconds?' · '+n.seconds+' seconds':' · Optional Q&A appendix')+'\n\n'+n.en+'\n\n### Reference sources — not spoken\n\n'+n.sources.map(v=>'- '+v).join('\n')).join('\n\n'));
const candidate=path.join(TMP,'candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);const final=path.join(OUT,process.env.FINAL_PPTX_NAME||'Six_Research_Questions_Presentation_English.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:final,pythonExecutable:RUNTIME+'/python/python.exe',integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','2','--require-native-table-slide','4','--require-native-table-slide','5','--require-native-table-slide','6','--require-native-table-slide','8','--require-native-table-slide','10'],requiredNativeTableOwnerSlides:[2,4,5,6,8,10],requiredNativeChartOwnerSlides:[3,7],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(TMP,path.basename(final)+'.validation.json')});
const verified=await PresentationFile.importPptx(await FileBlob.load(final));for(let i=0;i<verified.slides.items.length;i++){let b=await verified.export({slide:verified.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(TMP,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()))}
console.log(`Built six-question deck: ${deck.slides.items.length} slides, ${total} suggested seconds; script adapted to the supplied speaking reference.`);
