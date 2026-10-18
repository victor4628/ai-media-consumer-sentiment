"""Network-free public reproduction of GPT-core v3, without private text."""
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import analyze_gpt_core_v3 as a
from sentiment_project.common import read_json,read_jsonl,write_json
from sentiment_project.vintages import annual_change,latest_value,quarterly_annualized
from sentiment_project.reference_validation import reference_validation
def close(x,y):
 if isinstance(x,dict):
  assert set(x)==set(y),set(x)^set(y)
  for k in x:close(x[k],y[k])
 elif isinstance(x,list):
  assert len(x)==len(y)
  for l,r in zip(x,y):close(l,r)
 elif isinstance(x,(float,int)) and not isinstance(x,bool):assert np.isclose(x,y,atol=1e-9,rtol=1e-9),(x,y)
 else:assert x==y,(x,y)
def frame(f,name):pd.testing.assert_frame_equal(f,pd.read_csv(ROOT/('data/processed/'+name)),check_dtype=False,atol=1e-9,rtol=1e-9)
def main():
 out=ROOT/'reproduced';out.mkdir(exist_ok=True);checks={}
 if (ROOT/'SHA256SUMS.json').exists():
  hashes=read_json(ROOT/'SHA256SUMS.json')
  for n,h in hashes.items():
   p=(ROOT/n).resolve();assert p.is_relative_to(ROOT) and hashlib.sha256(p.read_bytes()).hexdigest()==h,n
  checks['manifest_files']=len(hashes)
 meta=ROOT/'data/shareable/gpt_core_v3';items=read_jsonl(meta/'corpus_metadata.jsonl');original=read_jsonl(meta/'GPT_primary_labels.jsonl');mapping={r['id']:r for r in original}
 assert len(items)==len(original)==1473 and {i['id'] for i in items}==set(mapping)
 for i in items:assert mapping[i['id']]['input_sha256']==i['original_input_sha256']
 # Metadata hashes only compare stored identifiers. Full original inputs are unavailable.
 labels=copy.deepcopy(original)
 for r in labels:r['input_sha256']=None
 media=a.enrich(items,labels);frame(media,'gpt_core_v3/monthly_media.csv');media.to_csv(out/'monthly_media.csv',index=False)
 source=read_json(ROOT/'data/raw/alfred_vintages/manifest.json')
 for r in source['records']:
  p=ROOT/f'data/raw/alfred_vintages/{r["vintage"]}/{r["series"]}.csv';assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
 rows=[];series={'unemployment':'UNRATE','pce_yoy':'PCEPI','gdp_growth':'GDPC1','sentiment_available':'UMCSENT','income_yoy':'DSPIC96'}
 for vintage in sorted({r['vintage'] for r in source['records']}-{a.CFG['evaluation_vintage']}):
  target=(pd.Timestamp(vintage)+pd.offsets.MonthBegin(1)).strftime('%Y-%m-%d');row={'target_month':target,'information_cutoff':vintage}
  for name,s in series.items():
   fn=annual_change if name in ['pce_yoy','income_yoy'] else quarterly_annualized if name=='gdp_growth' else latest_value
   period,value=fn(a.snapshot(s,vintage),target);row.update({name:value,name+'_period':period,name+'_age_months':(pd.Timestamp(target).year-pd.Timestamp(period).year)*12+pd.Timestamp(target).month-pd.Timestamp(period).month})
  rows.append(row)
 macro=pd.DataFrame(rows);frame(macro,'vintage_feature_panel.csv');macro.to_csv(out/'vintage_feature_panel.csv',index=False)
 _,panel=a.build_panel(media);frame(panel,'gpt_core_v3/model_panel.csv');models=a.model_specs();f,coef,valid=a.forecast(panel,models);f['training_mean']=a.training_mean(valid,f)
 frame(f,'gpt_core_v3/predictions.csv');frame(coef,'gpt_core_v3/coefficients.csv');f.to_csv(out/'predictions.csv',index=False)
 expected=read_json(ROOT/'reports/gpt_core_v3/analysis.json');close(a.metrics(f,['persistence']+list(models)+['training_mean']),expected['metrics'])
 for key,value in expected['increments'].items():
  l,r=key.split('_vs_');close(a.comparison(f,l,r),value)
 compact={k:models[k] for k in ['economy','economy_tone','memory','memory_tone','household','household_tone','method_controls','method_controls_tone']};pairs=[('economy_tone','economy'),('memory_tone','memory'),('household_tone','household'),('method_controls_tone','method_controls')]
 def alt_check(af,key,mk='metrics',ik='increments'):
  exp=expected['sensitivity'][key];close(a.metrics(af,['persistence']+list(compact)),exp[mk]);close({l+'_vs_'+r:a.comparison(af,l,r) for l,r in pairs},exp[ik])
 for key,nn,nt in [('minimum_2_news_5_tweets',2,5),('minimum_3_news_5_tweets',3,5)]:
  af,_,v=a.forecast(panel,compact,nn,nt);close(len(v),expected['sensitivity'][key]['eligible_n']);close(len(af),expected['sensitivity'][key]['test_n']);alt_check(af,key)
 excluded=set(read_json(meta/'dedup_excluded_ids.json')['ids']);unique=[i for i in items if i['id'] not in excluded];_,p=a.build_panel(a.enrich(unique,[r for r in labels if r['id'] not in excluded]));af,_,_=a.forecast(p,compact);alt_check(f[['target_month']].merge(af,on='target_month'),'url_normalized_duplicates')
 relaxed=copy.deepcopy(labels)
 for r in relaxed:
  if r['label']['topics']:r['label']['us_relevance']='yes'
 _,p=a.build_panel(a.enrich(items,relaxed));af,_,_=a.forecast(p,compact);alt_check(f[['target_month']].merge(af,on='target_month'),'all_geographies_economic_texts','metrics_on_primary_months','increments_on_primary_months')
 from sentiment_project import media_models
 original_ridge=media_models.ridge_prediction
 for penalty in [.1,10.]:
  def change(train,current,features,penalty_unused=1.,value=penalty):return original_ridge(train,current,features,penalty=value)
  media_models.ridge_prediction=change
  try:af,_,_=a.forecast(panel,compact)
  finally:media_models.ridge_prediction=original_ridge
  alt_check(af,'ridge_penalty_'+str(penalty))
 olddata=a.DATA;a.DATA=out
 try:accounting=a.macro_accounting(macro)
 finally:a.DATA=olddata
 close(accounting,expected['macro_accounting']);frame(pd.read_csv(out/'macro_accounting.csv'),'gpt_core_v3/macro_accounting.csv')
 full=macro.copy();full['news_scored_n']=99;full['twitter_scored_n']=99;full['cumulative_prices_2008']=[100*(a.snapshot('PCEPI',r.information_cutoff)[r.pce_yoy_period]/a.snapshot('PCEPI',r.information_cutoff)['2008-12-01']-1) for r in full.itertuples()];full['linear_time']=np.arange(len(full))/12
 mm={k:models[k] for k in ['economy','memory']};mm.update({'economy_price_level':a.BASE+['cumulative_prices_2008'],'economy_linear_time':a.BASE+['linear_time'],'memory_price_level':a.BASE+['sentiment_available','cumulative_prices_2008']});af,_,_=a.forecast(full,mm);af['training_mean']=a.training_mean(full,af);frame(af,'gpt_core_v3/all_macro_predictions.csv');close(a.metrics(af,['persistence','training_mean']+list(mm)),expected['all_macro_forecasts']['metrics'])
 for key,value in expected['all_macro_forecasts']['increments'].items():l,r=key.split('_vs_');close(a.comparison(af,l,r),value)
 close(a.descriptions(items,labels),read_json(ROOT/'reports/gpt_core_v3/descriptive.json'))
 splits=read_json(ROOT/'data/shareable/audit_splits.json');reference={r['id']:r for r in read_jsonl(ROOT/'data/shareable/human_reference/labels_300.jsonl')};audit=read_json(ROOT/'reports/gpt_core_v3/validation.json')
 reference_protocol=read_json(ROOT/'data/shareable/human_reference/protocol.json')
 assert reference_protocol['human_annotators']==1 and all(r['annotator_id']=='human_01' and 'model' not in r for r in reference.values())
 assert hashlib.sha256((ROOT/'data/shareable/human_reference/labels_300.jsonl').read_bytes()).hexdigest()==reference_protocol['current_labels_sha256']
 close(reference_validation(items,splits,reference,mapping),audit)
 dictionary=read_jsonl(meta/'dictionary_scores.jsonl');diag=read_json(ROOT/'reports/final_gpt_v3/dictionary_comparison.json')
 for p in ['news','twitter']:
  rows=[r for r in dictionary if r['platform']==p];close(sum(r['dictionary_tone']==r['GPT_tone_mixed_as_neutral'] for r in rows)/len(rows),diag['by_platform'][p]['agreement'])
 checks.update({'status':'pass','primary_items':1473,'eligible_news':230,'eligible_X':829,'media_months':len(media),'macro_months':len(macro),'matched_forecast_months':len(f),'model_specifications':len(models),'sensitivity_specifications':6,'macro_forecast_months':len(af),'source_snapshots':len(source['records']),'valid_review_pairs':audit['all_300']['valid_pairs'],'network_requests':0,'private_text_required':False,'boundary':'Replays public labels and fixed duplicate exclusion. Does not rerun semantic coding, private-input hashes, text extraction or an independent review.'})
 import subprocess
 extension=subprocess.run([sys.executable,str(ROOT/'scripts/run_rubric_extension.py'),'--verify'],cwd=ROOT,text=True,capture_output=True)
 if extension.returncode:raise RuntimeError(extension.stdout+'\n'+extension.stderr)
 checks['rubric_extension']=read_json(ROOT/'reports/rubric_extension/verification.json')
 write_json(out/'verification.json',checks);print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
