"""Keep the current public deliverable paths in one place."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def write(name,value):
 (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cfg=json.loads((ROOT/'reports/CURRENT_DELIVERABLES.json').read_text(encoding='utf-8'))
cfg.update({'report':'output/report.pdf','report_source':'reports/report.md','presentation':'output/slides.pptx','script':'output/speaker_notes.md','dashboard':'output/dashboard.html','submission':'output/submission.zip','cover_identity':json.loads((ROOT/'configs/submission_identity.json').read_text(encoding='utf-8')),'identity_placement':'First page only','older_outputs':'Superseded local artifacts are archived; use the short names under output/.'})
write('reports/CURRENT_DELIVERABLES.json',cfg)
write('reports/ACTIVE_RESEARCH.json',{'status':'Stages 1–5 complete','version':'gpt_core_v3_final','current_deliverables':'reports/CURRENT_DELIVERABLES.json','analysis':cfg['analysis'],'validation':cfg['measurement_review'],'verification':'reports/final_gpt_v3/FINAL_QA.json','primary_labels':'data/private/gpt_core_v3/GPT_primary.jsonl','new_paid_API_calls':0})
write('reports/final_gpt_v3/STAGE_COMPLETION.json',{'completed':[1,2,3,4,5],'deliverables':cfg,'research_limitations_preserved':True,'data_collection_or_spending_this_revision':False})
print('Updated current deliverable paths.')
