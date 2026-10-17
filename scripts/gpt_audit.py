"""Record interactive GPT judgments; this script never assigns semantic labels."""
import argparse
import json
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from sentiment_project.common import digest,read_json,read_jsonl,write_json,write_jsonl,now_utc
from sentiment_project.ai_validation import validate_label
FOLDER=ROOT/'data/private/cross_family_v2'
MAPS={
 'tone':{'-':'negative','0':'neutral','+':'positive','m':'mixed','?':'uncertain'},
 'language_style':{'f':'factual','e':'emotional','m':'mixed','?':'uncertain'},
 'price_frame':{'l':'levels','c':'changes','b':'both','n':'neither','?':'uncertain'},
 'scope_frame':{'h':'household','n':'national','b':'both','x':'neither','?':'uncertain'},
 'time_frame':{'c':'current','f':'future','b':'both','n':'neither','?':'uncertain'},
 'factual_calibration':{'k':'not_checkable','n':'no_numeric_claim'},
 'political_attribution':{'c':'credit','b':'blame','d':'both','n':'none','?':'uncertain'},
 'us_relevance':{'y':'yes','n':'no','?':'uncertain'},
}
TOPIC={'P':'prices','E':'employment','W':'wages','G':'growth','H':'housing','F':'household_finances','O':'other'}
FIELDS=['tone','language_style','topics','price_frame','scope_frame','time_frame','factual_calibration','political_attribution','us_relevance']

def items():return read_jsonl(ROOT/'data/private/core_v1/audit_all_300.jsonl')
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','show','record','seal']);p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=50);p.add_argument('--input',type=Path);a=p.parse_args();corpus=items()
 FOLDER.mkdir(parents=True,exist_ok=True)
 if a.action=='prepare':
  target=FOLDER/'protocol.json'
  if target.exists():raise ValueError('Protocol already frozen')
  write_json(target,{'study_id':'cross_family_v2','created_at':now_utc(),'items':300,'corpus_sha256':digest(corpus),'prompt_sha256':digest((ROOT/'prompts/economic_coding_v2.txt').read_bytes()),'GPT_reviewer':'GPT, current Codex conversation; exact immutable model identifier not exposed','method':'Interactive assistant reads supplied item text, assigns every categorical judgment and selects literal evidence. Script expands explicit shorthand and validates; no lexicon, rule classifier or copied V4 predictions.','V4_reviewer':'Previously cached independent deepseek-v4-pro role B on identical 300 inputs; failed records remain null. Not loaded for comparison until GPT labels are sealed.','independence_limit':'Assistant already saw project-level aggregate findings and a few illustrative headlines in earlier conversation. Item-level V4 judgments are withheld during this annotation. Not a prospectively isolated blind experiment.','split':'Original 100 development and 200 held-out item identities retained. Prompt is unchanged; no tuning to GPT/V4 agreement.','analysis_rule':'Primary 1473-item Flash-coded feature panel stays frozen. Cross-family audit is measurement validation only; no selective label substitution or claim of human accuracy.','adjudication':'No automatic third-call majority for the new pair; disagreements remain reported, not converted to ground truth.','incremental_paid_API_requests':0})
  print('Prepared frozen cross-family audit protocol; no labels loaded.')
 elif a.action=='show':
  for index in range(a.start,min(a.start+a.count,len(corpus))):
   i=corpus[index];print(json.dumps({'n':index,'id':i['id'],'published_at':i['published_at'],'text':i['text'],'official_evidence':i.get('official_evidence',[])},ensure_ascii=False))
 elif a.action=='record':
  if (FOLDER/'sealed.json').exists():raise ValueError('Sealed audit cannot be edited')
  rows=json.loads(a.input.read_text(encoding='utf-8'))
  for raw in rows:
   index,code,quotes,rationale=raw;item=corpus[index];codes=code.split();assert len(codes)==9,(index,codes)
   label={'id':item['id'],'evidence':quotes,'rationale':rationale}
   for field,c in zip(FIELDS,codes):
    label[field]=[TOPIC[k] for k in c] if field=='topics' and c!='_' else [] if field=='topics' else MAPS[field][c]
   validate_label(label,item)
   record={'id':item['id'],'label':label,'input_sha256':digest(item),'source':item['source'],'platform':item['platform'],'role':'GPT','model':'GPT / Codex interactive reviewer (immutable identifier unavailable)','annotation_method':'Direct assistant judgment; explicit shorthand expanded, no semantic decisions made by script','recorded_at':now_utc(),'protocol_sha256':digest(read_json(FOLDER/'protocol.json'))}
   dest=FOLDER/'judgments'/f'{index:03d}.json';dest.parent.mkdir(exist_ok=True)
   if dest.exists() and read_json(dest)['label']!=label:raise ValueError('Refuse changing an existing judgment: '+str(index))
   write_json(dest,record)
  print('Validated and recorded',len(rows),'GPT judgments; total',len(list((FOLDER/'judgments').glob('*.json'))))
 else:
  rows=[]
  for n,item in enumerate(corpus):
   r=read_json(FOLDER/'judgments'/f'{n:03d}.json');assert r['input_sha256']==digest(item);validate_label(r['label'],item);rows.append(r)
  target=FOLDER/'GPT_300.jsonl';write_jsonl(target,rows)
  write_json(FOLDER/'sealed.json',{'sealed_at':now_utc(),'items':len(rows),'sha256':digest(rows),'file_sha256':digest(target.read_bytes()),'V4_item_labels_seen_during_GPT_annotation':False,'context_limit':'Project-level aggregates and a few example headlines were visible earlier; see protocol.'})
  print('Sealed',len(rows),'GPT judgments before cross-family comparison.')
if __name__=='__main__':main()
