"""Supplement frozen primary results; public downloads are explicitly opt-in."""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tmp/final_deps')]
from sentiment_project.common import digest, read_json, read_jsonl, write_json
from sentiment_project.media_models import TONE, rolling_comparison, paired_block_interval
from sentiment_project.vintages import parse_snapshot

PUBLIC = {
 'tbmics.csv':'https://www.sca.isr.umich.edu/files/tbmics.csv',
 'tbmiccice.csv':'https://www.sca.isr.umich.edu/files/tbmiccice.csv',
 'chicsh.xls':'https://www.sca.isr.umich.edu/files/chicsh.xls',
 'chicch.xls':'https://www.sca.isr.umich.edu/files/chicch.xls',
 'chiceh.xls':'https://www.sca.isr.umich.edu/files/chiceh.xls',
 'gdp2021q2.html':'https://www.bea.gov/news/2021/gross-domestic-product-second-quarter-2021-advance-estimate-and-annual-update',
 'pce202207.html':'https://www.bea.gov/news/2022/personal-income-and-outlays-july-2022',
 'gdp2022q3.pdf':'https://www.bea.gov/sites/default/files/2022-12/gdp3q22_3rd_0.pdf',
 'gdp2024q4.html':'https://www.bea.gov/news/2025/gross-domestic-product-4th-quarter-and-year-2024-advance-estimate',
 'survey_transition.pdf':'https://www.sca.isr.umich.edu/files/methodtransitionannouncement2024.pdf',
}

def snapshot(series, vintage):
 return parse_snapshot((ROOT / f'data/raw/alfred_vintages/{vintage}/{series}.csv').read_bytes(), series, vintage)

def public_files(download):
 folder = ROOT / 'data/raw/final_public'
 folder.mkdir(parents=True, exist_ok=True)
 records = []
 for name, url in PUBLIC.items():
  p = folder / name
  if download and not p.exists():
   p.write_bytes(urlopen(url, timeout=40).read())
  if p.exists():
   records.append({'file':name,'url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
 write_json(folder / 'manifest.json', {'retrieval_recorded_at':datetime.now(timezone.utc).isoformat(), 'records':records, 'note':'Latest public chart files, not historical vintages; all descriptive rows restricted to August 2026 or earlier.'})

def subindices():
 frames=[]
 for name in ['tbmics.csv','tbmiccice.csv']:
  f=pd.read_csv(ROOT/'data/raw/final_public'/name)
  f['month']=pd.to_datetime(f.Month+' '+f.YYYY.astype(str),format='%B %Y').dt.strftime('%Y-%m-%d')
  frames.append(f.drop(columns=['Month','YYYY']))
 frame=frames[0].merge(frames[1],on='month',validate='one_to_one').rename(columns={'ICS_ALL':'sentiment','ICC':'current_conditions','ICE':'expectations'})
 frame=frame.loc[frame.month.between('2010-01-01','2026-08-01')].sort_values('month')
 assert len(frame)==200 and not frame.isna().any().any()
 evaluation=snapshot('UMCSENT','2026-10-16')
 assert max(abs(row.sentiment-evaluation[row.month]) for row in frame.itertuples()) < 0.11, 'Latest public headline differs materially from fixed evaluation vintage'
 frame.to_csv(ROOT/'data/processed/sentiment_subindices_descriptive.csv',index=False)
 return {'n':len(frame),'start':frame.month.min(),'end':frame.month.max(),'latest':frame.iloc[-1].to_dict(),'scope':'Current official monthly CSV snapshot; descriptive only, not used in forecasting or vintage targets. Chart XLS files contain three-month moving averages and are deliberately not used.'}

def fact_checks(corpus):
 from pypdf import PdfReader
 folder=ROOT/'data/raw/final_public'
 texts={}
 for name in PUBLIC:
  if not name.startswith(('gdp','pce')):continue
  p=folder/name
  texts[name]=' '.join(page.extract_text() or '' for page in PdfReader(p).pages) if p.suffix=='.pdf' else re.sub('<[^>]+>',' ',p.read_text(encoding='utf-8'))
 byid={i['id']:i for i in corpus}
 specs=[('gdelt:ec1eb677a5ce5709c34f43e0','2021 Q2 real GDP, advance, QoQ annualized',6.5,'2021-07-29T12:30:00Z','gdp2021q2.html'),
 ('gdelt:872db267dc34350b7eefb7b4','2022 July headline PCE, YoY',6.3,'2022-08-26T12:30:00Z','pce202207.html'),
 ('gdelt:9b18bbecf80ac2356bf562c2','2022 Q3 real GDP, third, QoQ annualized',3.2,'2022-12-22T13:30:00Z','gdp2022q3.pdf'),
 ('gdelt:49fe044086a7bf5a8b66f120','2024 Q4 real GDP, advance, QoQ annualized',2.3,'2025-01-30T13:30:00Z','gdp2024q4.html'),
 ('gdelt:49fe044086a7bf5a8b66f120','2024 real GDP, annual over annual',2.8,'2025-01-30T13:30:00Z','gdp2024q4.html')]
 rows=[]
 for id, claim, value, release, name in specs:
  item=byid[id]
  assert str(value) in item['text'], (id,value)
  assert re.search(r'\b'+re.escape(str(value))+r'\s*percent',texts[name],re.I), (name,value)
  assert pd.Timestamp(item['published_at']) >= pd.Timestamp(release)
  rows.append({'item_id':id,'source':item['source'],'article_url':item.get('url',''),'claim':claim,'reported_percent':value,'official_percent':value,'official_release_utc':release,'metadata_publication_utc':item['published_at'],'official_url':PUBLIC[name],'verdict':'matches contemporaneous official release','availability_caveat':'Conditional on GDELT publication metadata; publisher timestamp not independently verified.'})
 report={'scope':'Purposive illustration, 5 numeric claims in 4 headlines; not a random audit, no platform accuracy rate; primary AI labels unchanged.', 'method':'Match period, metric, rate convention and release vintage, then compare numbers at displayed 0.1 percentage-point precision. Publication metadata must follow the official release.', 'claims':rows,'other_numeric_texts':'Unchecked, not false. Twitter claims are not covered.'}
 write_json(ROOT/'reports/final_fact_checks.json',report)
 return report

def content_diagnostics(corpus):
 labels=read_jsonl(ROOT/f'labels/runs/core_v1/{digest(corpus)[:12]}_A.jsonl')
 labels={x['id']:x['label'] for x in labels}
 positive={'growth','growing','gain','gains','strong','stronger','boom','booming','improve','improving','recovery','recover','optimistic','surge','rising'}
 negative={'recession','crisis','collapse','crash','layoffs','unemployment','weak','weaker','struggling','decline','declining','poverty','pessimistic','fear','suffer','costly'}
 counters={p:Counter() for p in ['news','twitter']}; monthly={}
 for item in corpus:
  lab=labels[item['id']]
  stamp=pd.Timestamp(item['published_at']); cutoff=pd.Timestamp(stamp.strftime('%Y-%m')+'-01',tz='UTC')+pd.offsets.MonthBegin(1)
  if lab is None or lab['us_relevance']!='yes' or not lab['topics'] or max(stamp,pd.Timestamp(item.get('discovered_at',item['published_at'])))>=cutoff:continue
  p=item['platform']; month=stamp.strftime('%Y-%m'); key=(month,p)
  if key not in monthly:monthly[key]=Counter()
  c=monthly[key];c['eligible_n']+=1
  for field in ['tone','language_style','price_frame','scope_frame','time_frame','political_attribution','factual_calibration']:
   c[field+':'+lab[field]]+=1
  for topic in lab['topics']:c['topic:'+topic]+=1
  if lab['tone'] not in TONE:continue
  words=re.findall(r'[a-z]+',item['text'].lower()); score=sum(w in positive for w in words)-sum(w in negative for w in words)
  lexical='positive' if score>0 else 'negative' if score<0 else 'neutral'
  ai='neutral' if lab['tone']=='mixed' else lab['tone']
  counters[p]['n']+=1;counters[p]['agree']+=int(ai==lexical);counters[p]['lex_'+lexical]+=1
  counters[p]['AI_'+ai]+=1
  counters[p]['pair_'+ai+'_'+lexical]+=1
 output=[]
 for (month,p),c in sorted(monthly.items()):output.append({'media_month':month,'platform':p,**dict(c)})
 write_json(ROOT/'reports/monthly_content_dimensions.json',{'scope':'Sample composition, pooled item counts; multi-label topics need not sum to 100%; no audience exposure weights.','rows':output})
 result={'scope':'Unvalidated transparent toy lexicon, not a calibrated finance dictionary or accuracy benchmark. Single-word counts ignore negation, syntax and sarcasm; rising/growth can be adverse in a price context.', 'positive_words':sorted(positive),'negative_words':sorted(negative),'comparison':{p:{**dict(c),'agreement':c['agree']/c['n']} for p,c in counters.items()}}
 write_json(ROOT/'reports/dictionary_diagnostic.json',result)
 return result

def supplemental_models():
 panel=pd.read_csv(ROOT/'data/processed/core_model_panel.csv')
 prices=[]
 for _,row in panel.iterrows():
  values=snapshot('PCEPI',row.information_cutoff)
  prices.append(100*(values[row.pce_yoy_period]/values['2018-12-01']-1))
 panel['cumulative_prices']=prices
 month=pd.to_datetime(panel.target_month).dt.month
 panel['season_sin']=np.sin(month*2*np.pi/12);panel['season_cos']=np.cos(month*2*np.pi/12)
 panel['web_phase']=np.clip((pd.to_datetime(panel.target_month).dt.year*12+month-(2024*12+3))/4,0,1)
 panel.to_csv(ROOT/'data/processed/supplemental_model_panel.csv',index=False)
 base=['unemployment','pce_yoy','gdp_growth','sentiment_available']
 controls=['income_yoy','cumulative_prices']; media=['news_tone','twitter_tone']
 specs={'household_price_level_posthoc':{'M1H_household':base+controls,'M3H_add_media':base+controls+media},
        'seasonality_method_posthoc':{'M1S_controls':base+['season_sin','season_cos','web_phase'],'M2S_add_media':base+['season_sin','season_cos','web_phase']+media}}
 out={}
 for name,models in specs.items():
  f,_,eligible=rolling_comparison(panel,lambda v:snapshot('UMCSENT',v),snapshot('UMCSENT','2026-10-16'),models_override=models)
  f.to_csv(ROOT/f'data/processed/{name}_predictions.csv',index=False)
  names=list(models)
  out[name]={'n':len(f),'features':models,'MAE':{m:float((f[m]-f.actual).abs().mean()) for m in models},'media_increment':paired_block_interval(f,names[1],names[0])}
 f=pd.read_csv(ROOT/'data/processed/core_predictions.csv');coef=pd.read_csv(ROOT/'data/processed/core_rolling_coefficients.csv')
 residual={}
 for m in ['M1_economic','M2_add_media','M3_add_household']:
  errors=f.set_index(pd.PeriodIndex(pd.to_datetime(f.target_month),freq='M'))[m]-f.set_index(pd.PeriodIndex(pd.to_datetime(f.target_month),freq='M')).actual
  pairs=[(errors.loc[t-1],v) for t,v in errors.items() if t-1 in errors.index]
  residual[m]={'calendar_adjacent_pairs':len(pairs),'lag1_correlation':float(np.corrcoef(np.array(pairs).T)[0,1])}
 stability={}
 for feat in media:
  v=coef.loc[coef.model=='M2_add_media',feat].dropna()
  stability[feat]={'min':float(v.min()),'max':float(v.max()),'positive_share':float((v>0).mean()),'unit':'sentiment points per training-sample SD of feature; predictive, not causal'}
 report={'scope':'Post-hoc diagnostics, no selection of a winning model or new confirmatory p-values; primary results frozen.', 'price_level_definition':'100*(latest available PCE index / December 2018 index - 1), both taken from the same forecast-origin vintage. Dec 2018 reference fixed for core sample only.', 'specifications':out,'residual_diagnostics':residual,'coefficient_stability':stability,'latest_household_proxies':panel.iloc[-1][['target_month','income_yoy','cumulative_prices','pce_yoy']].to_dict()}
 write_json(ROOT/'reports/supplemental_analysis.json',report)
 return report

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--download',action='store_true');a=parser.parse_args()
 public_files(a.download)
 corpus=read_jsonl(ROOT/'data/private/core_v1/corpus.jsonl')
 summary={'subindices':subindices(),'fact_checks':fact_checks(corpus),'dictionary':content_diagnostics(corpus),'supplemental_models':supplemental_models()}
 write_json(ROOT/'reports/final_research.json',summary)
 print(json.dumps({'subindices':summary['subindices'],'fact_claims':len(summary['fact_checks']['claims']),'dictionary_agreement':{p:c['agreement'] for p,c in summary['dictionary']['comparison'].items()},'posthoc_models':summary['supplemental_models']['specifications']},indent=2))

if __name__=='__main__':main()
