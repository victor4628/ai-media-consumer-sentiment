import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const RUNTIME='C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const SKILL='C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
process.env.RUNTIME_NODE_MODULES=RUNTIME+'/node/node_modules';
const {Presentation,PresentationFile,FileBlob}=await import(pathToFileURL(RUNTIME+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'));
const {applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs'));
const TMP=path.join(ROOT,'tmp/gpt_v3_deck');await fs.mkdir(TMP,{recursive:true});await fs.mkdir(path.join(ROOT,'output/presentation'),{recursive:true});
const data=JSON.parse(await fs.readFile(path.join(ROOT,'reports/final_gpt_v3/authoring_data.json'),'utf8'));
const script=JSON.parse(await fs.readFile(path.join(ROOT,'configs/presentation_gpt_core_v3.json'),'utf8'));
const G='#254C45',A='#A37D46',K='#252B29',M='#68766E',LIGHT='#DEE5E0';
const deck=Presentation.create({slideSize:{width:1280,height:720}});deck.theme.defaultFont='Arial';
const inventory=[];
function text(s,value,x,y,w,h,size=28,bold=false,color=K){const sh=s.shapes.add({geometry:'textbox',name:value.slice(0,70),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});sh.text=value;sh.text.style={typeface:'Arial',fontSize:size,bold,color};return sh;}
function slide(n,answer){const s=deck.slides.add();s.background.fill='#FFFFFF';text(s,script.slides[n-1].title,56,36,1165,108,38,true,G);if(answer)text(s,answer,60,154,1155,62,29,true);text(s,String(n).padStart(2,'0'),1170,678,50,22,17,false,M);return s;}
function foot(s,value){text(s,value,60,643,1140,48,18,false,M);}
function note(s,n,sources){s.speakerNotes.text=script.slides[n-1].en+'\n\nSources\n'+sources.join('\n');inventory.push({slide:n,title:script.slides[n-1].title,script:script.slides[n-1].en,sources});}
function chart(s,type,options){
 // Six decimals preserve more than the displayed precision and fit Excel's numeric limit.
 options.series=options.series.map(v=>({...v,values:v.values.map(x=>x===null?null:Number(x.toFixed(6)))}));
 const q=s.charts.add(type,options);applyPresentationChartFont(q,{fontFamily:'Arial'});return q;
}
const axisText={fontSize:23,fill:M};
function bar(s,categories,series,pos,max=100,format='0.0',title='Share of eligible items (%)'){
 return chart(s,'bar',{position:pos,categories,series,barOptions:{direction:'bar',grouping:'clustered',gapWidth:70},
  hasLegend:series.length>1,legend:{position:'bottom',textStyle:{fontSize:22}},
  xAxis:{textStyle:{fontSize:25,fill:K},majorGridlines:null},
  yAxis:{min:0,max,majorUnit:max===100?20:undefined,numberFormatCode:format,title,textStyle:axisText,majorGridlines:{fill:LIGHT,width:1}},
  dataLabels:{showValue:true,position:'outEnd',numberFormatCode:format,textStyle:{fontSize:25,fill:K,bold:true}}});
}
function line(s,categories,series,pos,min,max,title){return chart(s,'line',{position:pos,categories,series,hasLegend:series.length>1,
 legend:{position:'bottom',textStyle:{fontSize:19}},lineOptions:{smooth:false},
 xAxis:{textStyle:{fontSize:18,fill:M},majorGridlines:null},yAxis:{min,max,title,numberFormatCode:'0',textStyle:{fontSize:21,fill:M},majorGridlines:{fill:LIGHT,width:1}}});}

let s=deck.slides.add();s.background.fill='#FFFFFF';
text(s,'Media narratives and the\nconsumer sentiment gap',60,155,1160,184,62,true,G);
text(s,'Findings from six research questions',64,398,1130,58,33,false,K);
text(s,'AI Applications in Finance\nAnalysis cutoff: 16 October 2026',64,586,1130,66,23,false,M);
note(s,1,['Project study gpt_core_v3; reports/final_gpt_v3/RESEARCH_REPORT.md']);

s=slide(2,'Five survey answers combine current conditions and expectations');
text(s,'Current conditions',65,250,520,48,29,true,G);
text(s,'Family finances versus a year ago\nBuying major household items',65,310,535,106,28);
text(s,'Expectations',675,250,535,48,29,true,G);
text(s,'Family finances one year ahead\nNational outlook over one and five years',675,310,535,106,28);
text(s,'xᵢ = round(100 + favorable % − unfavorable %)',66,454,1140,49,31,true,G);
text(s,'ICS = (x₁ + x₂ + x₃ + x₄ + x₅) / 6.7558 + 2',66,528,1140,58,35,true,G);
foot(s,'The five relative scores describe survey responses. Source: University of Michigan, Index Calculations.');
note(s,2,['https://data.sca.isr.umich.edu/fetchdoc.php?docid=75432','https://data.sca.isr.umich.edu/faq.php','Report page 2']);

const d=data.descriptive;
s=slide(3,'Emotional language differs much more than negative economic tone');
bar(s,['Political blame','Emotional or mixed language','Negative economic tone'],[
 {name:'News',values:[100*d.news.pooled_item_shares.political_blame_share,100*d.news.pooled_item_shares.emotional_share,100*d.news.negative_share],fill:G},
 {name:'X',values:[100*d.twitter.pooled_item_shares.political_blame_share,100*d.twitter.pooled_item_shares.emotional_share,100*d.twitter.negative_share],fill:A}
],{left:58,top:239,width:1150,height:351});
foot(s,'230 eligible headlines + 829 X posts from 1,473 coded texts. October 2019–July 2026. Selected sample.');
note(s,3,['Report page 3','reports/gpt_core_v3/descriptive.json','Political blame includes texts assigning both credit and blame. Sample content differences do not establish a platform causal effect.']);

s=slide(4,'The estimated gap changes with the economic benchmark');
const latest=data.predictions.at(-1);
bar(s,['Prior sentiment carried forward','Economy + media','Economy only','Observed sentiment'],[
 {name:'August 2026',values:[latest.persistence,latest.economy_tone,latest.economy,latest.actual],fill:G}
],{left:58,top:244,width:1128,height:322},80,'0.0','Sentiment index points');
text(s,'Actual respondent exposure is missing, so a causal media effect remains unidentified.',64,582,1140,54,25,true,G);
foot(s,'July media forecasts August sentiment. The final weeks before the November election are outside this sample.');
note(s,4,['Report page 4','data/processed/gpt_core_v3/predictions.csv','Single-month illustration; whole-sample errors appear on slide 8.']);

s=slide(5,'Accumulated prices substantially reduce the model’s residual gap');
const annual=[];for(let year=2010;year<=2026;year++){const r=data.macro.filter(v=>v.target_month.startsWith(String(year)));const mean=k=>r.reduce((v,x)=>v+x[k],0)/r.length;annual.push({year:String(year)+(year===2026?'*':''),actual:mean('actual'),macro:mean('three_macro_fitted'),price:mean('plus_price_level_fitted')});}
line(s,annual.map(v=>v.year),[
 {name:'Observed sentiment',values:annual.map(v=>v.actual),line:{fill:G,width:3}},
 {name:'Three macro indicators',values:annual.map(v=>v.macro),line:{fill:M,width:2}},
 {name:'Also accumulated prices',values:annual.map(v=>v.price),line:{fill:A,width:2.5}}
],{left:55,top:240,width:805,height:350},40,110,'Index points');
text(s,'44.9-point decline',900,254,305,45,30,true,G);text(s,'2017–2019 mean: 97.0\nJune–August 2026: 52.1',900,307,310,85,25);
text(s,'Residual gap',900,425,300,35,26,true,G);text(s,'Three indicators: 28.3\nAdd price levels: 7.1',900,470,320,90,28,true);
foot(s,'Descriptive OLS on 200 months. Chart shows annual means (*2026: Jan–Aug). Residuals are not causal effects.');
note(s,5,['Report page 5','reports/gpt_core_v3/analysis.json: macro_accounting','Monthly series averaged by calendar year solely for display. Decomposition compares 2017–2019 with June–August 2026.']);

s=slide(6,'The speed of price increases differs from the accumulated bill');
const sampled=data.panel.filter((v,i)=>i%12===0||i===data.panel.length-1);const cats=sampled.map(v=>v.target_month.slice(0,4));
text(s,'Price level (December 2018 = 100)',70,236,780,32,24,true,G);
line(s,cats,[{name:'Price level',values:sampled.map(v=>100+v.cumulative_prices),line:{fill:G,width:3}}],{left:55,top:271,width:780,height:154},95,135,'');
text(s,'PCE inflation (year over year, %)',70,448,780,32,24,true,A);
line(s,cats,[{name:'PCE inflation',values:sampled.map(v=>v.pce_yoy),line:{fill:A,width:3}}],{left:55,top:483,width:780,height:135},0,8,'');
text(s,'+27.9%',905,253,290,69,51,true,G);text(s,'Accumulated price increase',905,325,300,62,26);
text(s,'3.7%',905,425,290,64,47,true,A);text(s,'Annual inflation\nReal income growth: 0.5%',905,495,300,88,25);
foot(s,'Latest origin-available releases before August 2026. Selected monthly readings shown. All 82 months enter analysis.');
note(s,6,['Report page 6','data/processed/gpt_core_v3/model_panel.csv','PCEPI reference December 2018, numerator and denominator from the same origin vintage. DSPIC96 income growth is aggregate real disposable income, not household microdata.']);

s=slide(7,'Our measurements describe content proxies for the mechanisms');
bar(s,['Anchoring to past prices\nPrice-level framing','Confirmation bias\nPolitical blame','Availability bias\nTopic salience (prices)','Negativity bias\nNegative economic tone'],[
 {name:'News',values:[100*d.news.pooled_item_shares.price_levels_share,100*d.news.pooled_item_shares.political_blame_share,100*d.news.pooled_item_shares.prices_topic_share,100*d.news.negative_share],fill:G},
 {name:'X',values:[100*d.twitter.pooled_item_shares.price_levels_share,100*d.twitter.pooled_item_shares.political_blame_share,100*d.twitter.pooled_item_shares.prices_topic_share,100*d.twitter.negative_share],fill:A}
],{left:58,top:235,width:1145,height:360},65,'0.0','Observed content proxy (%)');
foot(s,'Measuring consumer mechanisms also requires exposure, recall, prior beliefs, responses and individual reference prices.');
note(s,7,['Report page 7','reports/gpt_core_v3/descriptive.json','Mechanism names identify candidate explanations, not diagnoses. Topic salience means the share of eligible texts mentioning prices.']);

s=slide(8,'Media helps in one controlled specification, with limited stability');
const m=data.analysis.metrics;
bar(s,['Memory + seasonality + survey mode','Memory + income + price levels','Economy + prior sentiment'],[
 {name:'Without media tone',values:[m.method_controls.MAE,m.household.MAE,m.memory.MAE],fill:M},
 {name:'With media tone',values:[m.method_controls_tone.MAE,m.household_tone.MAE,m.memory_tone.MAE],fill:G}
],{left:55,top:239,width:1155,height:333},5.2,'0.000','Mean absolute error (lower is better)');
text(s,'Carry forward prior sentiment: 3.725     All content features together: 4.737',64,589,1135,45,26,true,G);
foot(s,'Same 40 test months, January 2023–August 2026. Expanding ridge regression. Method control: 2024 web transition.');
note(s,8,['Report page 8','reports/gpt_core_v3/analysis.json','https://www.sca.isr.umich.edu/files/methodtransitionannouncement2024.pdf','Method controls contain the economy and prior sentiment plus annual sine/cosine and a transition ramp. They do not also contain household controls. The nominal paired media-gain interval excludes zero, but multiplicity and coding uncertainty are not included.']);

s=slide(9,'The media gain reverses under the strictest coverage rule');
const sens=data.analysis.sensitivity;
chart(s,'bar',{position:{left:55,top:245,width:1140,height:325},categories:['At least 3 news / 5 X (13 months)','At least 2 news / 5 X (25 months)','At least 1 news / 3 X (40 months)'],
 series:[{name:'Media change in MAE',values:[sens.minimum_3_news_5_tweets.increments.method_controls_tone_vs_method_controls.difference,sens.minimum_2_news_5_tweets.increments.method_controls_tone_vs_method_controls.difference,data.analysis.increments.method_controls_tone_vs_method_controls.difference],fill:G}],
 barOptions:{direction:'bar',gapWidth:80},hasLegend:false,xAxis:{textStyle:{fontSize:24},majorGridlines:null},
 yAxis:{min:-.5,max:.5,majorUnit:.25,title:'Change in MAE (negative = improvement)',numberFormatCode:'0.00',textStyle:axisText,majorGridlines:{fill:LIGHT,width:1}},
 dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'+0.000;-0.000;0.000',textStyle:{fontSize:28,bold:true,fill:G}}});
text(s,'Price levels shrink the residual gap; stricter coverage reverses the media gain.',65,589,1140,48,27,true,G);
foot(s,'Seasonality/survey-mode comparison. Higher coverage thresholds change training and test months as well as text counts.');
note(s,9,['Report page 9','reports/gpt_core_v3/analysis.json: sensitivity','The 13-month change interval crosses zero. A coverage sensitivity is not an isolated measurement-precision experiment.']);

s=slide(10,'Prices and benchmark choice change the interpretation');
text(s,'1',65,257,48,48,34,true,G);text(s,'X shows more emotional language and political blame',131,257,1060,72,34,true);
text(s,'2',65,372,48,48,34,true,G);text(s,'Accumulated price pressure reduces the unexplained gap',131,372,1060,72,34,true);
text(s,'3',65,487,48,48,34,true,G);text(s,'Media forecasting gains depend on controls and coverage',131,487,1060,72,34,true);
foot(s,'Forecasting implication: purchasing power and recent sentiment deserve priority before adding more text features.');
note(s,10,['Report pages 1, 5–9','reports/gpt_core_v3/analysis.json','Final main slide. No methods appendix follows.']);

await fs.writeFile(path.join(TMP,'slide_inventory.json'),JSON.stringify(inventory,null,2));
const candidate=path.join(TMP,'candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);
const final=path.join(ROOT,'output/presentation',process.env.FINAL_PPTX_NAME||'Consumer_Sentiment_Findings_GPT_v3.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:final,
 pythonExecutable:RUNTIME+'/python/python.exe',integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[3,4,5,6,7,8,9],materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(TMP,path.basename(final)+'.validation.json')});
const verified=await PresentationFile.importPptx(await FileBlob.load(final));
for(let i=0;i<verified.slides.items.length;i++){const b=await verified.export({slide:verified.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(TMP,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));}
await fs.writeFile(path.join(ROOT,'reports/final_gpt_v3/deck_build.json'),JSON.stringify({file:path.relative(ROOT,final).replaceAll('\\','/'),slides:10,native_chart_slides:[3,4,5,6,7,8,9],render_folder:path.relative(ROOT,TMP).replaceAll('\\','/')},null,2));
console.log('Built and rendered ten-slide GPT-core deck.');
