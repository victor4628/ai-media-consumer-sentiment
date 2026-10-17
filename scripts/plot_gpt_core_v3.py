"""Research figures from versioned outputs; no new data or model fitting."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'reports/gpt_core_v3'
FIG=FOLDER/'figures';FIG.mkdir(parents=True,exist_ok=True)
R=json.loads((FOLDER/'analysis.json').read_text(encoding='utf-8'))
D=json.loads((FOLDER/'descriptive.json').read_text(encoding='utf-8'))
G='#254C45';A='#A37D46';GREY='#79847E';RED='#A9574D'
plt.rcParams.update({'font.family':'Arial','font.size':12,'axes.spines.top':False,'axes.spines.right':False,
    'axes.titleweight':'bold','axes.titlecolor':G,'axes.labelcolor':'#303A35',
    'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})

def save(fig,name,foot,top=.98):
    fig.text(.02,.015,foot,fontsize=9,color='#526159',va='bottom')
    fig.tight_layout(rect=[0,.065,1,top])
    fig.savefig(FIG/(name+'.png'),dpi=180)
    fig.savefig(FIG/(name+'.svg'))
    plt.close(fig)

# Difference in rhetoric versus direction, with explicit pooled denominators.
fig,ax=plt.subplots(figsize=(11,5.3))
names=['Negative economic tone','Emotional or mixed language','Political blame or both']
for y,(label,key) in enumerate(zip(names,['negative_share','emotional_share','political_blame_share'])):
    vals=[100*(D[p][key] if key=='negative_share' else D[p]['pooled_item_shares'][key]) for p in ['news','twitter']]
    ax.plot(vals,[y,y],color='#CED8D2',lw=5,zorder=1)
    for value,color,offset in zip(vals,[G,A],[-.13,.16]):
        ax.scatter(value,y,s=140,color=color,zorder=2)
        ax.text(value,y+offset,f'{value:.1f}%',ha='center',va='center',weight='bold',color=color)
ax.set_yticks(range(3),names);ax.invert_yaxis();ax.set_ylim(2.5,-.55)
ax.set_xlim(0,100);ax.set_xlabel('Share of sampled eligible items (%)')
ax.set_title('The largest platform difference is emotional language',loc='left',pad=18)
ax.scatter([],[],color=G,label='News (230)');ax.scatter([],[],color=A,label='X (829)')
ax.legend(frameon=False,loc='lower right');ax.grid(axis='x',alpha=.15)
save(fig,'01_content_features','Source: sealed GPT coding. Pooled item shares; headline/post formats, sampling and topics differ. These are content differences, not population bias estimates.')

fig,axes=plt.subplots(1,2,figsize=(11,4.8))
labels=['No economic substance','Foreign economic subject','US subject uncertain','Eligible US-related economics']
colors=['#CCD2CE','#AAB5AF','#D8C7A8',G]
for ax,p,title in zip(axes,['news','twitter'],['News headlines','X posts']):
    c=D[p]['counts'];vals=[c.get(k,0) for k in ['no_economic_substance','economic_but_US_no','economic_but_US_uncertain','eligible']]
    left=0
    for n,label,color in zip(vals,labels,colors):
        ax.barh(0,n,left=left,color=color,height=.38,label=label)
        if n>=20:ax.text(left+n/2,0,str(n),ha='center',va='center',color='white' if color==G else '#263A30',weight='bold')
        left+=n
    ax.set_xlim(0,c['candidate']);ax.set_ylim(-.75,.75);ax.set_yticks([]);ax.set_xlabel('Items');ax.set_title(f'{title}: {c["eligible"]} / {c["candidate"]} retained',loc='left')
handles,legend=axes[0].get_legend_handles_labels();fig.legend(handles,legend,loc='upper center',bbox_to_anchor=(.5,.73),ncol=2,frameon=False,fontsize=10)
save(fig,'02_sample_filtering','Source: 1,473 fixed corpus items. Explicit US-subject rule is strict; country-uncertain headlines are not treated as false or necessarily non-US.')

panel=pd.read_csv(ROOT/'data/processed/gpt_core_v3/model_panel.csv')
dates=pd.to_datetime(panel.target_month)
fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True)
axes[0].plot(dates,100+panel.cumulative_prices,color=G,lw=2.5)
axes[0].axhline(100,color=GREY,lw=1,ls='--');axes[0].set_ylabel('Price index\nDec 2018 = 100')
axes[0].set_title('Slower inflation leaves the accumulated price increase in place',loc='left')
axes[0].annotate(f'{100+panel.cumulative_prices.iloc[-1]:.1f}',(dates.iloc[-1],100+panel.cumulative_prices.iloc[-1]),xytext=(-40,-20),textcoords='offset points',color=G,weight='bold')
axes[1].plot(dates,panel.pce_yoy,color=A,lw=2.3);axes[1].axhline(0,color=GREY,lw=.7)
axes[1].set_ylabel('PCE inflation\nYear over year (%)')
axes[1].annotate(f'{panel.pce_yoy.iloc[-1]:.1f}%',(dates.iloc[-1],panel.pce_yoy.iloc[-1]),xytext=(-35,13),textcoords='offset points',color=A,weight='bold')
macro=pd.read_csv(ROOT/'data/processed/gpt_core_v3/macro_accounting.csv')
actual=dict(zip(macro.target_month,macro.actual))
axes[2].plot(dates,panel.target_month.map(actual),color=G,lw=2.3);axes[2].set_ylabel('Michigan sentiment\nIndex points')
axes[2].annotate(f'{R["actual_sentiment_latest"]:.1f}',(dates.iloc[-1],R['actual_sentiment_latest']),xytext=(-35,10),textcoords='offset points',color=G,weight='bold')
for ax in axes:ax.grid(axis='y',alpha=.15)
axes[-1].xaxis.set_major_locator(mdates.YearLocator());axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
save(fig,'03_prices_and_sentiment','Source: cached ALFRED. Price features use the latest release available before each target month; sentiment uses the 16 Oct 2026 scoring vintage. Co-movement is descriptive.')

fig,ax=plt.subplots(figsize=(11,5.5))
x=pd.to_datetime(macro.target_month)
ax.plot(x,macro.actual,color=G,lw=2.3,label='Observed Michigan sentiment')
ax.plot(x,macro.three_macro_fitted,color=GREY,lw=1.7,label='Unemployment + inflation + GDP')
ax.plot(x,macro.plus_price_level_fitted,color=A,lw=1.7,label='Same indicators + accumulated price level')
ax.set_title('The apparent sentiment gap depends on the economic benchmark',loc='left')
ax.set_ylabel('Sentiment index points');ax.grid(axis='y',alpha=.15);ax.legend(frameon=False,fontsize=10,loc='lower left')
save(fig,'04_macro_fit','Source: 200 monthly observations, Jan 2010–Aug 2026. Full-sample descriptive OLS; fitted lines are not out-of-sample forecasts. Price control can absorb trends and omitted changes.')

fig,ax=plt.subplots(figsize=(10,4.7))
ref=R['macro_accounting'];keys=['three_macro','plus_price_level','plus_linear_time']
for y,k in enumerate(keys):
    r=ref[k]['references']['2017_2019'];fit=-r['model_associated_change'];resid=-r['residual_change']
    ax.barh(y,fit,color=G,height=.5)
    ax.barh(y,resid,left=fit,color=A,height=.5)
    ax.text(fit/2,y,f'{fit:.1f}',ha='center',va='center',color='white',weight='bold')
    ax.text(fit+resid/2,y,f'{resid:.1f}',ha='center',va='center',color='white',weight='bold')
ax.set_yticks(range(3),['Three macro indicators','Add accumulated prices','Add a linear time trend'])
ax.invert_yaxis();ax.set_xlabel('44.9-point decline: 2017–2019 mean to June–August 2026 mean')
ax.set_title('Adding price levels reduces the residual gap from 28.3 to 7.1 points',loc='left',pad=20)
ax.legend(handles=[Patch(facecolor=G,label='Model-associated change'),Patch(facecolor=A,label='Residual change')],frameon=False,loc='lower center',bbox_to_anchor=(.5,-.35),ncol=2)
save(fig,'05_benchmark_accounting','Source: alternative descriptive OLS specifications on the same 200 months. Accounting depends on model and reference period; residual is not attributed to media.')

fig,axes=plt.subplots(1,2,figsize=(12,5.3),gridspec_kw={'width_ratios':[1,1.6]})
for ax,rows,limit,title in [(axes[0],[('economy','economy_tone','Economy only')],14,'Weak economic baseline'),
    (axes[1],[('memory','memory_tone','Economy + prior sentiment'),('household','household_tone','Memory + income + price levels'),('method_controls','method_controls_tone','Memory + seasonality + survey mode')],5.4,'Stronger baselines')]:
    for y,(base,media,label) in enumerate(rows):
        vals=[R['metrics'][m]['MAE'] for m in [base,media]]
        ax.plot(vals,[y,y],color='#CCD8D0',lw=5)
        for val,color,offset in zip(vals,[GREY,G],[-.13,.15]):
            ax.scatter(val,y,color=color,s=100,zorder=3)
            ax.text(val,y+offset,f'{val:.3f}',ha='center',va='center',color=color,weight='bold',fontsize=10)
    ax.set_yticks(range(len(rows)),[r[2] for r in rows],fontsize=10);ax.invert_yaxis();ax.set_ylim(len(rows)-.5,-.6)
    ax.set_xlim(0,limit);ax.set_xlabel('Mean absolute error (lower is better)');ax.set_title(title,loc='left');ax.grid(axis='x',alpha=.15)
    ax.axvline(R['metrics']['persistence']['MAE'],color=A,ls='--',lw=1.3,label='Last sentiment carried forward')
axes[0].scatter([],[],color=GREY,label='Without media tone');axes[0].scatter([],[],color=G,label='With media tone')
fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.99),ncol=3,frameon=False,fontsize=10)
save(fig,'06_forecast_comparison','Source: identical 40 target months, Jan 2023–Aug 2026 (4 missing months). Expanding ridge, origin-available data. Panels use different x-axis ranges. Seasonality/mode result is exploratory.',top=.91)

fig,ax=plt.subplots(figsize=(11,6.4))
keys=['economy_tone_vs_economy','memory_tone_vs_memory','household_tone_vs_household','method_controls_tone_vs_method_controls',
      'method_controls_tone_vs_persistence','memory_all_content_vs_memory']
names=['Tone added to economy','Tone added to economy + prior sentiment','Tone added to income + price controls','Tone added to seasonality + mode controls',
       'Tone + mode model vs last sentiment','All content features vs economy + prior sentiment']
for y,k in enumerate(keys):
    r=R['increments'][k];lo,hi=r['interval'];v=r['difference']
    ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=G if hi<0 else GREY,capsize=4,markersize=8)
    ax.text(1.75,y,f'{v:+.3f}',va='center',ha='right',fontsize=10)
ax.axvline(0,color=A,ls='--');ax.set_yticks(range(len(keys)),names,fontsize=10);ax.invert_yaxis()
ax.set_xlim(-1.35,1.85);ax.set_xlabel('Change in mean absolute error (negative = improvement)')
ax.set_title('Media improvement depends on specification',loc='left',pad=15)
save(fig,'07_media_increment_intervals','Source: paired segment-preserving bootstrap intervals on 40 sparse months. Exploratory, conditional on coded sample; intervals omit coding uncertainty and multiple-comparison adjustment.')

fig,ax=plt.subplots(figsize=(11,5))
rows=[('Primary: 1 news / 3 X',R['increments']['method_controls_tone_vs_method_controls']),
      ('At least 2 news / 5 X',R['sensitivity']['minimum_2_news_5_tweets']['increments']['method_controls_tone_vs_method_controls']),
      ('At least 3 news / 5 X',R['sensitivity']['minimum_3_news_5_tweets']['increments']['method_controls_tone_vs_method_controls'])]
for y,(label,r) in enumerate(rows):
    v=r['difference'];lo,hi=r['interval']
    ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=G,capsize=4,markersize=8)
    ax.text(.85,y,f'n = {r["n"]}',va='center')
ax.set_yticks(range(3),[x[0] for x in rows]);ax.invert_yaxis();ax.axvline(0,color=A,ls='--')
ax.set_xlim(-.7,1.1);ax.set_xlabel('Media change in mean absolute error (negative = improvement)')
ax.set_title('The promising media result reverses in the strictest coverage check',loc='left',pad=15)
save(fig,'08_coverage_sensitivity','Source: seasonality/survey-mode baseline with versus without tone. Higher thresholds also change training and test months, so this does not isolate measurement precision alone.')

print(json.dumps({'figures':8,'png_and_svg':True,'folder':str(FIG)}))
