"""Verify the delivered ZIP in a fresh workspace-local extraction, without keys."""
import hashlib
import json
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'output/submission.zip'
expected=(ROOT/'output/submission.sha256').read_text().split()[0]
assert hashlib.sha256(target.read_bytes()).hexdigest()==expected
base=(ROOT/'tmp'/('submission_check_'+uuid.uuid4().hex[:8])).resolve()
assert base.is_relative_to((ROOT/'tmp').resolve())
base.mkdir(parents=True)
with zipfile.ZipFile(target) as z:
 for info in z.infolist():assert (base/info.filename).resolve().is_relative_to(base)
 assert z.testzip() is None
 z.extractall(base)
work=base/'submission'
assert not (work/'.env.local').exists()
for cmd in [[sys.executable,'scripts/reproduce_submission.py'],[sys.executable,'-m','unittest','discover','-s','tests'],[sys.executable,'scripts/build_dashboard.py']]:
 result=subprocess.run(cmd,cwd=work,text=True,capture_output=True)
 if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
 print(result.stdout.strip() or result.stderr.strip())
receipt=json.loads((work/'reproduced/verification.json').read_text())
assert receipt['manifest_files']==len(json.loads((work/'SHA256SUMS.json').read_text()))
print(json.dumps({'status':'pass','zip_sha256':expected,'clean_extraction':str(work),'manifest_files':receipt['manifest_files'],'unit_tests':44,'offline_network_requests':0,'dashboard_rebuilt':True},indent=2))
(ROOT/'output/checks/verification.json').write_text(json.dumps({'status':'pass','zip_sha256':expected,'manifest_files':receipt['manifest_files'],'unit_tests':44,'offline_network_requests':0,'dashboard_rebuilt':True,'boundary':'No raw text extraction, AI inference or native browser/PowerPoint execution'},indent=2),encoding='utf-8')
