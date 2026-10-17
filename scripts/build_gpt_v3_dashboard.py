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
 html=(ROOT/'reports/dashboard_gpt_v3.template.html').read_text(encoding='utf-8').replace('__PAYLOAD__',json.dumps(payload,separators=(',',':')).replace('</','<\\/'));(ROOT/'reports/dashboard.html').write_text(html,encoding='utf-8');print(json.dumps({'bytes':len(html.encode()),'test_months':len(payload['predictions']),'network_requests':0}))
if __name__=='__main__':main()
