"""Check the release inventory for language, disclosure and publication hygiene."""
import json,re,sys,zipfile
from pathlib import Path
from release_files import release_paths

ROOT=Path(__file__).resolve().parents[1]
HAN=re.compile('[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]')
TEXT={'.md','.txt','.json','.jsonl','.csv','.py','.mjs','.html','.svg','.xml','.rels','.toml','.yml','.yaml'}
INTERNAL_NAMES=('NEXT_MODEL_HANDOFF','STAGES_1_2_FINDINGS','STAGE_COMPLETION','PROJECT_PLAN','speaker_notes_revision','cover_identity_revision','filename_changes','slide9_revision')
INTERNAL_TEXT=re.compile(r'(?:current chat|send_message_to_thread|removed_user_material|user deletions|user-saved|rewrite pending|next model handoff)',re.I)

def inspect_bytes(name,body,findings):
 if HAN.search(name):findings.append({'file':name,'issue':'non-English filename'})
 if any(v in name for v in INTERNAL_NAMES):findings.append({'file':name,'issue':'internal working document'})
 suffix=Path(name).suffix.lower()
 if suffix in TEXT or name in {'.gitignore','.gitattributes','.env.example'}:
  text=body.decode('utf-8-sig')
  decoded=text
  if suffix=='.json':decoded=json.dumps(json.loads(text),ensure_ascii=False)
  elif suffix=='.jsonl':decoded='\n'.join(json.dumps(json.loads(line),ensure_ascii=False) for line in text.split('\n') if line.strip())
  if HAN.search(decoded):findings.append({'file':name,'issue':'Chinese text'})
  if suffix in {'.md','.json','.html'} and INTERNAL_TEXT.search(decoded):findings.append({'file':name,'issue':'internal editorial wording'})
  if re.search(rb'\bsk-[A-Za-z0-9_-]{24,}',body):findings.append({'file':name,'issue':'credential-like value'})
 elif suffix in {'.pptx','.xlsx','.docx'}:
  import io
  with zipfile.ZipFile(io.BytesIO(body)) as z:
   for part in z.namelist():
    if part.endswith(('.xml','.rels')):
     if HAN.search(z.read(part).decode('utf-8')):findings.append({'file':name,'part':part,'issue':'Chinese OOXML text'})
 elif suffix=='.pdf':
  import io
  from pypdf import PdfReader
  for n,page in enumerate(PdfReader(io.BytesIO(body)).pages,1):
   if HAN.search(page.extract_text()):findings.append({'file':name,'page':n,'issue':'Chinese PDF text'})

def check(root=ROOT,archive=None):
 findings=[]
 if archive:
  with zipfile.ZipFile(archive) as z:
   pairs=[(n.removeprefix('submission/'),z.read(n)) for n in z.namelist() if not n.endswith('/')]
 else:
  declared=release_paths(root)
  pairs=[(p.relative_to(root).as_posix(),p.read_bytes()) for p in declared]
  allowed={p.resolve() for p in declared}
  for p in root.rglob('*'):
   if not p.is_file():continue
   relative=p.relative_to(root);parts=relative.parts
   if parts[0] in {'.git','tmp','reproduced'} or '__pycache__' in parts or p.suffix in {'.pyc','.pyo'}:continue
   if relative.as_posix() in {'output/submission.zip','output/submission.sha256','SHA256SUMS.json'} or relative.as_posix().startswith('output/checks/'):continue
   if p.resolve() not in allowed:findings.append({'file':relative.as_posix(),'issue':'file outside publication inventory'})
 for name,body in pairs:inspect_bytes(name,body,findings)
 result={'status':'pass' if not findings else 'fail','files_scanned':len(pairs),'chinese_findings':sum('Chinese' in f['issue'] or 'non-English' in f['issue'] for f in findings),'findings':findings,
  'scope':'Current release file names and text, decoded JSON, PDF extraction, and OOXML; original Git history and private inputs are outside the release.'}
 print(json.dumps(result,indent=2));assert not findings,'Release hygiene check failed'
 return result

if __name__=='__main__':check(archive=Path(sys.argv[1]) if len(sys.argv)>1 else None)
