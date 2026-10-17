"""Minimize private media to metadata and categorical labels for local submission."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from sentiment_project.common import digest,read_json,read_jsonl,write_json,write_jsonl
from sentiment_project.ai_validation import ENUMS
folder=ROOT/'data/private/core_v1';out=ROOT/'data/shareable';out.mkdir(parents=True,exist_ok=True)
corpus=read_jsonl(folder/'corpus.jsonl')
fields=['id','platform','source','source_level','published_at','discovered_at']
items=[{k:i[k] for k in fields if k in i} for i in corpus];byid={i['id']:i for i in items}
write_jsonl(out/'corpus_metadata.jsonl',items)
for role,name in [('A','corpus.jsonl'),('B','audit_all_300.jsonl'),('C','review_C.jsonl')]:
 full=read_jsonl(folder/name);records=read_jsonl(ROOT/f'labels/runs/core_v1/{digest(full)[:12]}_{role}.jsonl')
 safe=[]
 for r in records:
  label=None if r['label'] is None else {k:r['label'][k] for k in [*ENUMS,'topics']}
  safe.append({'id':r['id'],'input_sha256':digest(byid[r['id']]),'original_input_sha256':r['input_sha256'],'role':role,'model':r.get('model'),'label':label,'label_status':r.get('label_status'),'source':byid[r['id']]['source'],'platform':byid[r['id']]['platform']})
 write_jsonl(out/f'labels_{role}.jsonl',safe)
write_json(out/'audit_splits.json',{name:[i['id'] for i in read_jsonl(folder/file)] for name,file in [('all_300','audit_all_300.jsonl'),('held_out_200','audit_200.jsonl'),('development_100','development_100.jsonl')]})
write_json(out/'provenance.json',{'scope':'Metadata and categorical labels only. New input_sha256 hashes minimized metadata; original_input_sha256 refers to private full inputs. Original text, evidence quotes, rationale, author handles and raw model responses excluded.', 'corpus_manifest':read_json(folder/'corpus_manifest.json'),'prompt_freeze':read_json(ROOT/'labels/runs/core_v1/prompt_frozen.json'),'counts':{'corpus':len(corpus),'A':1473,'B':300,'C':251}})
print('Prepared metadata and categorical labels without private text')
