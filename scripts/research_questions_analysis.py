"""Post-hoc, explicitly noncausal macro accounting for the six-question report."""
import itertools
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from sentiment_project.common import write_json
from sentiment_project.vintages import parse_snapshot
from sentiment_project.media_models import rolling_comparison,paired_block_interval
def snapshot(series,vintage):return parse_snapshot((ROOT/f'data/raw/alfred_vintages/{vintage}/{series}.csv').read_bytes(),series,vintage)
def compute():
 macro=pd.read_csv(ROOT/'data/processed/vintage_feature_panel.csv');evaluation=snapshot('UMCSENT','2026-10-16')
 macro['sentiment']=macro.target_month.map(evaluation);f=['unemployment','pce_yoy','gdp_growth'];d=macro.dropna(subset=f+['sentiment']).copy()
 x=np.column_stack([np.ones(len(d)),d[f].to_numpy(float)]);y=d.sentiment.to_numpy(float);beta=np.linalg.lstsq(x,y,rcond=None)[0];pred=x@beta;sse=float(((y-pred)**2).sum());sst=float(((y-y.mean())**2).sum())
 d['fitted_macro']=pred;d['residual']=d.sentiment-d.fitted_macro
 latest=d.tail(3);comparisons={}
 for name,start,end in [('2017_2019','2017-01-01','2019-12-01'),('2015_2019','2015-01-01','2019-12-01')]:
  ref=d.loc[d.target_month.between(start,end)];dx=latest[f].mean()-ref[f].mean();components={feature:float(beta[i+1]*dx[feature]) for i,feature in enumerate(f)}
  observed=float(latest.sentiment.mean()-ref.sentiment.mean());explained=sum(components.values());remainder=observed-explained
  assert np.isclose(observed,explained+remainder)
  comparisons[name]={'reference_start':start,'reference_end':end,'reference_n':len(ref),'latest_start':latest.target_month.min(),'latest_end':latest.target_month.max(),'latest_n':len(latest),'reference_sentiment':float(ref.sentiment.mean()),'latest_sentiment':float(latest.sentiment.mean()),'observed_change':observed,'model_associated_change':explained,'residual_change':remainder,'accounting_share':explained/observed,'components_points':components}
 panel=pd.read_csv(ROOT/'data/processed/core_model_panel.csv');pf,_,_=rolling_comparison(panel,lambda v:snapshot('UMCSENT',v),evaluation,include_memory=False)
 primary=pd.read_csv(ROOT/'data/processed/core_predictions.csv');assert list(pf.target_month)==list(primary.target_month)
 mean_predictions=[]
 for row in pf.itertuples():
  labels=snapshot('UMCSENT',row.information_cutoff)
  # Matches the same complete-case training origins as the pure-economic model.
  valid=panel[(panel.news_scored_n>=1)&(panel.twitter_scored_n>=3)].dropna(subset=f+['news_tone','twitter_tone','income_yoy'])
  history=valid.loc[valid.target_month<row.target_month,'target_month'].map(labels).dropna()
  assert len(history)==row.training_n;mean_predictions.append(float(history.mean()))
 pf['training_mean']=mean_predictions
 forecast={}
 for name in ['persistence','training_mean','M1_economic','M2_add_media','M3_add_household']:
  e=pf[name]-pf.actual
  forecast[name]={'MAE':float(e.abs().mean()),'RMSE':float(np.sqrt((e**2).mean())),'skill_vs_training_mean':float(1-(e**2).sum()/((pf.training_mean-pf.actual)**2).sum()),'skill_vs_persistence':float(1-(e**2).sum()/((pf.persistence-pf.actual)**2).sum())}
 report={'scope':'Post-hoc descriptive macro accounting and matched pure-economic forecasting. Neither R-squared nor accounting share is a causal explanation or a media-attributable fraction.', 'fitting_sample':{'n':len(d),'start':d.target_month.min(),'end':d.target_month.max()},'features':f,'model':'OLS with intercept, three origin-available macro indicators; no sentiment memory, media or household controls. Fitted on all cutoff-available targets for descriptive accounting only.','in_sample_R2':1-sse/sst,'coefficients':{'intercept':float(beta[0]),**dict(zip(f,map(float,beta[1:])))},'reference_comparisons':comparisons,'reference_choice':'Post-hoc 2017-2019 pre-pandemic reference versus latest 3 released months; 2015-2019 sensitivity disclosed. A different reference/model changes the fraction; not bounded to [0,1].','oos_common_n':len(pf),'oos_pure_economic':forecast,'pure_economic_media_increment':paired_block_interval(pf,'M2_add_media','M1_economic'),'latest_common_month':pf.iloc[-1][['target_month','actual','M1_economic','M2_add_media','persistence']].to_dict(),'interpretation':'The residual includes omitted household pressures, measurement changes, misspecification and media among other candidates. No unique natural sentiment discrepancy exists before choosing a benchmark.'}
 return report,d,pf
def main():
 report,d,pf=compute()
 d.to_csv(ROOT/'data/processed/rq3_macro_accounting.csv',index=False);pf.to_csv(ROOT/'data/processed/rq3_pure_economic_predictions.csv',index=False)
 write_json(ROOT/'reports/research_questions_analysis.json',report)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
