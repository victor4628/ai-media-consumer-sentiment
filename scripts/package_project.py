"""Allowlisted shareable archive for the final GPT-core revision, with no credentials."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from sentiment_project.common import read_json
from release_files import release_paths
def main():
 cfg=read_json(ROOT/'reports/CURRENT_DELIVERABLES.json');paths=release_paths(ROOT)
 source=read_json(ROOT/'data/raw/alfred_vintages/manifest.json');blobs={}
 from check_release import check
 check(ROOT)
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
  for n,b in sorted(blobs.items()):z.writestr('submission/'+n,b)
 checksum=hashlib.sha256(target.read_bytes()).hexdigest();target.with_suffix('.sha256').write_text(checksum+'  '+target.name+'\n',encoding='utf-8');receipt={'files':len(blobs),'bytes':target.stat().st_size,'sha256':checksum,'private_text_included':False,'environment_files_included':False,'credential_pattern_scan':'pass','source_snapshots':len(source['records']),'scope':'Allowlisted shareable archive; contains no private raw text or credentials'};checks=target.parent/'checks';checks.mkdir(exist_ok=True);(checks/'package.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
