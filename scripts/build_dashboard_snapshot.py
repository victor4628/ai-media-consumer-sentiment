"""Create a self-contained, interactive research dashboard without API requests."""
import json,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from sentiment_project.common import read_json,read_jsonl
from analyze_gpt_core_v3 import eligibility
def main():
 def csv(n):return json.loads(pd.read_csv(ROOT/('data/processed/'+n)).to_json(orient='records'))
 labels={r['id']:r['label'] for r in read_jsonl(ROOT/'data/shareable/gpt_core_v3/GPT_primary_labels.jsonl')};items=read_jsonl(ROOT/'data/shareable/gpt_core_v3/corpus_metadata.jsonl')
 payload={'analysis':read_json(ROOT/'reports/gpt_core_v3/analysis.json'),'predictions':csv('gpt_core_v3/predictions.csv'),'media':csv('gpt_core_v3/monthly_media.csv'),'panel':csv('gpt_core_v3/model_panel.csv'),'subindices':csv('sentiment_subindices_descriptive.csv'),'items':[{k:i[k] for k in ['id','platform','source','published_at']}|{'label':labels[i['id']]} for i in items if eligibility(i,labels[i['id']])]}
 extension=ROOT/'reports/rubric_extension'
 measurement=read_json(extension/'measurement.json')
 payload['validation']={split:{'attempted':group['attempted'],'valid_pairs':group['valid_pairs'],'tone':group['dimensions']['tone'],
  'by_platform':{p:{'valid_pairs':v['valid_pairs'],'tone':v['dimensions']['tone']} for p,v in group['by_platform'].items()},
  'by_source':{s:{'valid_pairs':v['valid_pairs'],'small_sample':v['small_sample'],'tone':v['dimensions']['tone']} for s,v in group['by_source'].items()}}
  for split,group in measurement['splits'].items()}
 payload.update({'stability':read_json(extension/'statistical_stability.json'),'same_events':read_json(extension/'same_event_comparison.json'),
  'events':read_json(ROOT/'data/shareable/rubric_extension/events.json'),'factual_audit':read_json(ROOT/'reports/final_fact_checks.json')})
 for row in payload['predictions']:row['economic_gap']=row['actual']-row['economy']
 html=(ROOT/'reports/dashboard_rubric.template.html').read_text(encoding='utf-8').replace('__PAYLOAD__',json.dumps(payload,separators=(',',':')).replace('</','<\\/'));(ROOT/'output/dashboard.html').write_text(html,encoding='utf-8');print(json.dumps({'bytes':len(html.encode()),'test_months':len(payload['predictions']),'network_requests':0,'extension':'rubric_extension_v1'}))
if __name__=='__main__':main()
