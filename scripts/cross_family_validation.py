"""Compare sealed direct-GPT judgments with cached independent DeepSeek V4 votes."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from sentiment_project.common import digest,read_json,read_jsonl,write_json,write_jsonl
from core_validation import compare_group
folder=ROOT/'data/private/core_v1';new=ROOT/'data/private/cross_family_v2'
items=read_jsonl(folder/'audit_all_300.jsonl');sealed=read_json(new/'sealed.json');gpt_rows=read_jsonl(new/'GPT_300.jsonl')
assert sealed['sha256']==digest(gpt_rows) and sealed['file_sha256']==digest((new/'GPT_300.jsonl').read_bytes())
# First access to the V4 item labels occurs only after the direct GPT file is sealed.
v4_rows=read_jsonl(ROOT/f'labels/runs/core_v1/{digest(items)[:12]}_B.jsonl')
gpt={r['id']:r for r in gpt_rows};v4={r['id']:r for r in v4_rows}
for item in items:
 assert gpt[item['id']]['input_sha256']==digest(item)==v4[item['id']]['input_sha256']
report={'scope':'Cross-family model-based coding audit; no human annotations or accuracy gold standard. Reviewer A in agreement tables is V4; B is direct GPT.', 'protocol':read_json(new/'protocol.json'),'seal':sealed,'reviewers':{'A':'Cached independent deepseek-v4-pro, original role B','B':'GPT / current Codex conversation; exact immutable identifier not exposed'},'all_300':compare_group(items,v4,gpt),'held_out_200':compare_group(read_jsonl(folder/'audit_200.jsonl'),v4,gpt),'development_100':compare_group(read_jsonl(folder/'development_100.jsonl'),v4,gpt),'by_platform':{p:compare_group([i for i in items if i['platform']==p],v4,gpt) for p in ['news','twitter']},'disagreements':'Unresolved model disagreement, not majority truth; old same-family C results are historical only.','feature_rule':'All main forecasts retain the frozen Flash-coded corpus; new audit does not selectively substitute labels.','incremental_paid_api_calls':0}
write_json(ROOT/'reports/cross_family_validation.json',report)
safe=ROOT/'data/shareable/cross_family_v2';safe.mkdir(parents=True,exist_ok=True)
for role,rows in [('V4',v4_rows),('GPT',gpt_rows)]:
 clean=[]
 for r in rows:
  label=None if r['label'] is None else {k:v for k,v in r['label'].items() if k not in ['evidence','rationale']}
  clean.append({k:r[k] for k in ['id','input_sha256','source','platform','role','model'] if k in r}|{'label':label})
 write_jsonl(safe/f'{role}_300.jsonl',clean)
write_json(safe/'protocol.json',report['protocol']);write_json(safe/'sealed.json',sealed)
print({k:{'attempted':report[k]['attempted'],'valid_pairs':report[k]['valid_pairs'],'tone_agreement':report[k]['agreement']['dimensions']['tone']['agreement'],'tone_kappa':report[k]['agreement']['dimensions']['tone']['kappa']} for k in ['all_300','held_out_200','development_100']})
