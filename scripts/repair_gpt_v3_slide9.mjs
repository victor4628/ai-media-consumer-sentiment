import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const RUNTIME='C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES=RUNTIME+'/node/node_modules';
const SKILL='C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const {PresentationFile,FileBlob}=await import(pathToFileURL(RUNTIME+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'));
const {finalizePresentation}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs'));
const source=path.join(ROOT,'output/presentation/Consumer_Sentiment_Findings_GPT_v3_Reviewed.pptx');
const TMP=path.join(ROOT,'tmp/gpt_v3_slide9_fix');await fs.mkdir(TMP,{recursive:true});
const presentation=await PresentationFile.importPptx(await FileBlob.load(source));
const slide=presentation.slides.items[8];
await fs.writeFile(path.join(TMP,'before.json'),JSON.stringify(await presentation.inspect({kind:'slide,textbox,chart,layout',search:'RQ6|coverage|residual',maxChars:15000}),null,2));
for(let i=0;i<10;i++){const b=await presentation.export({slide:presentation.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(TMP,`before-${i+1}.png`),new Uint8Array(await b.arrayBuffer()));}
console.log(JSON.stringify(slide.shapes.items.map(s=>({name:s.name,position:s.position})),null,2));
const title=slide.shapes.items.find(s=>s.name.startsWith('RQ6.'));
const takeaway=slide.shapes.items.find(s=>s.name.startsWith('Price levels shrink'));
const footer=slide.shapes.items.find(s=>s.name.startsWith('Seasonality/survey-mode comparison'));
if(!title||!takeaway||!footer||slide.charts.items.length!==1)throw new Error('Expected slide-9 edit targets not found');
title.position={left:56,top:36,width:1165,height:108};title.text.style={fontSize:36};
const chart=slide.charts.items[0];chart.position={left:60,top:232,width:1130,height:315};
chart.categories=['3 news / 5 X (13 months)','2 news / 5 X (25 months)','1 news / 3 X (40 months)'];
// Diverging bars must not let category labels follow the axis crossing at zero.
chart.xAxis={tickLabelPosition:'low',textStyle:{fontSize:23}};
chart.yAxis={tickLabelPosition:'low',textStyle:{fontSize:22}};
takeaway.text='Price levels shrink the residual gap.\nStricter coverage reverses the media gain.';
takeaway.position={left:60,top:575,width:1135,height:68};takeaway.text.style={fontSize:27,bold:true};
footer.text='Minimum items per month. Seasonality/survey-mode controls. Filters change training and test months.';
footer.position={left:60,top:655,width:1095,height:30};footer.text.style={fontSize:17};
const candidate=path.join(TMP,'candidate.pptx');await(await PresentationFile.exportPptx(presentation)).save(candidate);
execFileSync(RUNTIME+'/python/python.exe',[path.join(ROOT,'scripts/preserve_slide9_package.py'),source,candidate],{stdio:'inherit'});
const final=path.join(ROOT,'output/presentation/Consumer_Sentiment_Findings_GPT_v3_Page9_Fixed.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:final,
 pythonExecutable:RUNTIME+'/python/python.exe',integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[3,4,5,6,7,8,9],
 materializeLiteralChartWorkbooks:false,fontPolicy:{basis:'reference',families:['Arial'],referencePath:source,referenceSha256:createHash('sha256').update(await fs.readFile(source)).digest('hex')},verifyArtifactToolImport:true,
 receiptPath:path.join(TMP,'Consumer_Sentiment_Findings_GPT_v3_Page9_Fixed.validation.json')});
const verified=await PresentationFile.importPptx(await FileBlob.load(final));
for(let i=0;i<10;i++){const b=await verified.export({slide:verified.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(TMP,`after-${i+1}.png`),new Uint8Array(await b.arrayBuffer()));}
console.log('Saved '+final);
