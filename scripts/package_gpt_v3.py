"""Allowlisted shareable archive for the final GPT-core revision, with no credentials."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from sentiment_project.common import read_json
def main():
 cfg=read_json(ROOT/'reports/CURRENT_DELIVERABLES.json');paths=set()
 for folder,pattern in [('src','*.py'),('scripts','*.py'),('scripts','*.mjs'),('tests','*.py'),('configs','*.json'),('prompts','*.txt'),('data/shareable/gpt_core_v3','*'),('data/processed/gpt_core_v3','*.csv'),('reports/gpt_core_v3','*'),('reports/final_gpt_v3','*')]:
  paths.update(p for p in (ROOT/folder).rglob(pattern) if p.is_file() and '__pycache__' not in p.parts and 'history' not in p.parts)
 names=['README.md','SUBMISSION_GUIDE.zh-CN.md','requirements.txt','requirements-artifacts.txt','.env.example','labels/CODEBOOK.md',cfg['report'],cfg['presentation'],
 'reports/CURRENT_DELIVERABLES.json','reports/ACTIVE_RESEARCH.json','reports/PROJECT_STATUS.zh-CN.md','reports/FINAL_QA.zh-CN.md','reports/PRESENTATION_STYLE.zh-CN.md','reports/SLIDE_SCRIPT_ALIGNMENT.zh-CN.md','reports/dashboard.html','reports/dashboard_gpt_v3.template.html','reports/final_fact_checks.json',
 'data/processed/vintage_feature_panel.csv','data/processed/sentiment_subindices_descriptive.csv','data/shareable/audit_splits.json','data/shareable/cross_family_v2/V4_300.jsonl','data/raw/alfred_vintages/manifest.json']
 source=read_json(ROOT/'data/raw/alfred_vintages/manifest.json');names += [f'data/raw/alfred_vintages/{r["vintage"]}/{r["series"]}.csv' for r in source['records']]
 paths.update(ROOT/n for n in names);blobs={}
 for p in sorted(paths):
  assert p.resolve().is_relative_to(ROOT) and not any(s in p.parts for s in ['private','cache','node_modules']);name=p.relative_to(ROOT).as_posix();assert p.name!='.env.local' and (not p.name.startswith('.env') or p.name=='.env.example');body=p.read_bytes()
  if p.suffix in ['.py','.mjs','.json','.jsonl','.md','.html','.txt']:
   assert not re.search(rb'\bsk-[A-Za-z0-9_-]{24,}',body),'Potential credential; package aborted'
  if name.startswith('data/shareable/') and p.suffix=='.jsonl':
   for line in body.decode('utf-8').split('\n'):
    if line.strip():
     row=json.loads(line);assert not any(k in row for k in ['text','author','evidence','rationale']);assert not any(k in (row.get('label') or {}) for k in ['text','evidence','rationale'])
  blobs[name]=body
 hashes={n:hashlib.sha256(b).hexdigest() for n,b in blobs.items()};blobs['SHA256SUMS.json']=json.dumps(hashes,indent=2,sort_keys=True).encode();target=ROOT/cfg['submission'];target.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  for n,b in sorted(blobs.items()):z.writestr('Consumer_Sentiment_GPT_v3_Submission/'+n,b)
 checksum=hashlib.sha256(target.read_bytes()).hexdigest();target.with_suffix('.sha256').write_text(checksum+'  '+target.name+'\n',encoding='utf-8');receipt={'files':len(blobs),'bytes':target.stat().st_size,'sha256':checksum,'private_text_included':False,'environment_files_included':False,'credential_pattern_scan':'pass','source_snapshots':len(source['records']),'scope':'Local allowlisted archive; not uploaded or published'};(target.parent/'package_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
