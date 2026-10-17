"""Publication figures from frozen results and explicitly labeled supplements."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/figures';OUT.mkdir(exist_ok=True)
G='#254C45';A='#a37d46'
plt.rcParams.update({'font.family':'Arial','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.dpi':170,'axes.labelcolor':'#333333','text.color':'#333333'})
f=pd.read_csv(ROOT/'data/processed/core_predictions.csv',parse_dates=['target_month'])
t=f.set_index('target_month').reindex(pd.date_range(f.target_month.min(),f.target_month.max(),freq='MS'))
fig,ax=plt.subplots(figsize=(9.2,3.6),layout='constrained')
ax.fill_between(t.index,t.M2_add_media_empirical_low,t.M2_add_media_empirical_high,color=G,alpha=.12,label='M2 empirical 95% band (27 scored months)')
for c,n,col in [('actual','Observed','#242424'),('M1_economic','M1: economy + memory','#94a49f'),('M2_add_media','M2: add media',G)]:ax.plot(t.index,t[c],label=n,color=col,linewidth=1.5,marker='.',markersize=3)
ax.set_ylabel('Michigan sentiment index');ax.legend(fontsize=8,ncol=2,loc='lower left');ax.set_title('Chronological forecasts on 39 common months',loc='left',color=G)
fig.savefig(OUT/'final_forecasts.png');plt.close(fig)

s=pd.read_csv(ROOT/'data/processed/sentiment_subindices_descriptive.csv',parse_dates=['month'])
p=pd.read_csv(ROOT/'data/processed/supplemental_model_panel.csv',parse_dates=['target_month'])
fig,axes=plt.subplots(2,1,figsize=(9.2,5.1),layout='constrained')
for c,n,col in [('sentiment','Headline','#222222'),('current_conditions','Current conditions',G),('expectations','Expectations',A)]:axes[0].plot(s.month,s[c],label=n,color=col,linewidth=1.2)
axes[0].axvspan(pd.Timestamp('2024-04-01'),pd.Timestamp('2024-07-01'),color=G,alpha=.12)
axes[0].set_ylabel('Index level');axes[0].legend(fontsize=8,ncol=3);axes[0].set_title('Monthly survey subindices | descriptive latest snapshot',loc='left',color=G)
axes[1].plot(p.target_month,p.cumulative_prices,color=G,label='Cumulative PCE increase since Dec 2018')
axes[1].plot(p.target_month,p.pce_yoy,color=A,label='Latest available headline PCE YoY')
axes[1].set_ylabel('Percent');axes[1].legend(fontsize=8);axes[1].set_title('Falling inflation does not restore past price levels',loc='left',color=G)
fig.savefig(OUT/'final_household_context.png');plt.close(fig)

d=json.loads((ROOT/'reports/core_media_descriptive.json').read_text())
fig,ax=plt.subplots(figsize=(9.2,3.1),layout='constrained')
categories=['Emotional / mixed language','Price level / both','Future / both','Political blame / both']
for p,delta,col,label in [('news',-.18,G,'News (n=247)'),('twitter',.18,A,'Twitter (n=733)')]:
 dim=d[p]['dimensions'];n=d[p]['n']
 vals=[sum(dim[k].get(x,0) for x in keys)/n*100 for k,keys in [('language_style',['emotional','mixed']),('price_frame',['levels','both']),('time_frame',['future','both']),('political_attribution',['blame','both'])]]
 bars=ax.barh([i+delta for i in range(4)],vals,height=.32,color=col,label=label)
 ax.bar_label(bars,fmt='%.1f%%',padding=3,fontsize=8)
ax.set_yticks(range(4),categories);ax.set_xlim(0,86);ax.set_xlabel('Percent of sampled eligible items');ax.legend(fontsize=8);ax.set_title('Descriptive composition, not exposure or causal effects',loc='left',color=G)
fig.savefig(OUT/'final_frames.png');plt.close(fig)
print('Saved three final figures')
