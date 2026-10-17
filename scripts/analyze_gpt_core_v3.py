"""Offline research from sealed, directly assigned GPT labels; legacy outputs untouched."""
import functools
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from sentiment_project.ai_validation import ENUMS, validate_label
from sentiment_project.common import digest, read_json, read_jsonl, write_json, write_jsonl
from sentiment_project.media_models import TONE, monthly_media, paired_block_interval, rolling_comparison
from sentiment_project.vintages import parse_snapshot
from core_validation import compare_group

OUT = ROOT/'reports/gpt_core_v3'
DATA = ROOT/'data/processed/gpt_core_v3'
CFG = read_json(ROOT/'configs/gpt_core_v3_analysis.json')
BASE = CFG['baseline_features']
TONES = CFG['tone_features']

@functools.lru_cache(maxsize=None)
def snapshot(series, vintage):
    return parse_snapshot((ROOT/f'data/raw/alfred_vintages/{vintage}/{series}.csv').read_bytes(), series, vintage)

def eligibility(item, label):
    stamp = pd.Timestamp(item['published_at'])
    available = max(stamp, pd.Timestamp(item.get('discovered_at',item['published_at'])))
    cutoff = pd.Timestamp(stamp.strftime('%Y-%m')+'-01',tz='UTC')+pd.offsets.MonthBegin(1)
    return bool(label['topics']) and label['us_relevance']=='yes' and available<cutoff

def feature_values(label):
    return {
        'price_levels_share': label['price_frame'] in ['levels','both'],
        'political_blame_share': label['political_attribution'] in ['blame','both'],
        'emotional_share': label['language_style'] in ['emotional','mixed'],
        'household_share': label['scope_frame'] in ['household','both'],
        'prices_topic_share': 'prices' in label['topics'],
        'employment_topic_share': 'employment' in label['topics'],
    }

def enrich(items, records):
    frame = monthly_media(items,records,CFG['media_start'],CFG['media_end'])
    groups = defaultdict(list)
    labels = {r['id']:r['label'] for r in records}
    for item in items:
        label=labels[item['id']]
        if eligibility(item,label):
            groups[(item['published_at'][:7],item['platform'])].append((item,label))
    for platform in ['news','twitter']:
        for feature in CFG['frame_features']:
            values=[]
            for month in frame.media_month:
                sources=defaultdict(list)
                for item,label in groups[(month,platform)]:
                    sources[item['source'] if platform=='news' else 'all'].append(float(feature_values(label)[feature]))
                values.append(float(np.mean([np.mean(v) for v in sources.values()])) if sources else np.nan)
            frame[platform+'_'+feature]=values
    return frame

def build_panel(media):
    macro=pd.read_csv(ROOT/'data/processed/vintage_feature_panel.csv')
    panel=macro.merge(media,on='target_month',validate='one_to_one')
    panel['cumulative_prices']=[100*(snapshot('PCEPI',r.information_cutoff)[r.pce_yoy_period]/snapshot('PCEPI',r.information_cutoff)['2018-12-01']-1) for r in panel.itertuples()]
    month=pd.to_datetime(panel.target_month).dt.month
    panel['season_sin']=np.sin(month*2*np.pi/12)
    panel['season_cos']=np.cos(month*2*np.pi/12)
    panel['web_phase']=np.clip((pd.to_datetime(panel.target_month).dt.year*12+month-(2024*12+3))/4,0,1)
    return macro,panel

def forecast(panel, models, min_news=1, min_twitter=3):
    return rolling_comparison(panel,lambda v:snapshot('UMCSENT',v),snapshot('UMCSENT',CFG['evaluation_vintage']),
        CFG['minimum_training_months'],CFG['evaluation_start'],min_news,min_twitter,models_override=models)

def metrics(f,names):
    return {name:{'n':len(f),'MAE':float((f[name]-f.actual).abs().mean()),
        'RMSE':float(np.sqrt(((f[name]-f.actual)**2).mean())),
        'mean_error':float((f[name]-f.actual).mean())} for name in names}

def comparison(f,left,right):
    return paired_block_interval(f,left,right)

def descriptions(items,records):
    labels={r['id']:r['label'] for r in records}
    desc={}
    for platform in ['news','twitter']:
        subset=[i for i in items if i['platform']==platform]
        counts=Counter(); selected=[]
        for i in subset:
            lab=labels[i['id']]
            counts['candidate']+=1
            if not lab['topics']:
                counts['no_economic_substance']+=1;continue
            counts['economic']+=1
            if lab['us_relevance']!='yes':
                counts['economic_but_US_'+lab['us_relevance']]+=1;continue
            if not eligibility(i,lab):
                counts['late_availability']+=1;continue
            counts['eligible']+=1;selected.append(lab)
            if lab['tone'] in TONE:counts['tone_scored']+=1
        assert counts['candidate']==counts['no_economic_substance']+counts['economic_but_US_no']+counts['economic_but_US_uncertain']+counts['late_availability']+counts['eligible']
        dimensions={field:dict(Counter(l[field] for l in selected)) for field in ENUMS if field!='us_relevance'}
        shares={key:float(np.mean([feature_values(l)[key] for l in selected])) for key in CFG['frame_features']}
        desc[platform]={'counts':dict(counts),'dimensions':dimensions,'pooled_item_shares':shares,
            'topics_multilabel':dict(Counter(t for l in selected for t in l['topics'])),
            'negative_share':sum(l['tone']=='negative' for l in selected)/len(selected),
            'numeric_claims':sum(l['factual_calibration']=='not_checkable' for l in selected)}
    return desc

def macro_accounting(macro):
    frame=macro.copy();frame['actual']=frame.target_month.map(snapshot('UMCSENT',CFG['evaluation_vintage']))
    frame=frame.dropna(subset=BASE+['actual'])
    out={}
    price=[]
    for r in frame.itertuples():
        vals=snapshot('PCEPI',r.information_cutoff)
        # December 2008 is already released at every origin, including Dec 2009.
        price.append(100*(vals[r.pce_yoy_period]/vals['2008-12-01']-1))
    frame['cumulative_prices_2008']=price
    frame['linear_time']=np.arange(len(frame))/12
    for name,features in [('three_macro',BASE),('plus_price_level',BASE+['cumulative_prices_2008']),('plus_linear_time',BASE+['linear_time']),('plus_income_and_price',BASE+['income_yoy','cumulative_prices_2008'])]:
        x=np.column_stack([np.ones(len(frame)),frame[features].to_numpy(float)])
        y=frame.actual.to_numpy(float)
        beta=np.linalg.lstsq(x,y,rcond=None)[0];prediction=x@beta
        frame[name+'_fitted']=prediction
        latest=frame.tail(3);references={}
        for period,start in [('2017_2019','2017-01-01'),('2015_2019','2015-01-01')]:
            ref=frame[frame.target_month.between(start,'2019-12-01')]
            components=dict(zip(features,map(float,(latest[features].mean()-ref[features].mean()).to_numpy()*beta[1:])))
            decline=float(latest.actual.mean()-ref.actual.mean());associated=sum(components.values())
            references[period]={'reference_sentiment':float(ref.actual.mean()),'latest_sentiment':float(latest.actual.mean()),
                'observed_change':decline,'model_associated_change':associated,'residual_change':decline-associated,
                'accounting_share':associated/decline,'components_points':components}
        out[name]={'n':len(frame),'features':features,'in_sample_R2':float(1-np.sum((y-prediction)**2)/np.sum((y-y.mean())**2)),
            'coefficients':dict(zip(['intercept']+features,map(float,beta))), 'references':references}
    frame.to_csv(DATA/'macro_accounting.csv',index=False)
    out['scope']='Descriptive full-sample OLS, not a forecast or causal decomposition. Price-level cumulative trend depends on reference/window; no media attribution of residual.'
    return out

def training_mean(panel, predictions):
    out=[]
    for r in predictions.itertuples():
        targets=snapshot('UMCSENT',r.information_cutoff)
        history=panel.loc[panel.target_month<r.target_month,'target_month'].map(targets).dropna()
        assert len(history)==r.training_n
        out.append(float(history.mean()))
    return out

def model_specs():
    memory=BASE+['sentiment_available']
    household=memory+['income_yoy','cumulative_prices']
    models={'economy':BASE,'economy_tone':BASE+TONES,
        'memory':memory,'memory_tone':memory+TONES,
        'household':household,'household_tone':household+TONES,
        'method_controls':memory+['season_sin','season_cos','web_phase'],
        'method_controls_tone':memory+['season_sin','season_cos','web_phase']+TONES}
    for feature in CFG['frame_features']:
        models['memory_'+feature]=memory+[p+'_'+feature for p in ['news','twitter']]
    models['memory_all_content']=memory+TONES+[p+'_'+f for p in ['news','twitter'] for f in CFG['frame_features']]
    return models

def run():
    OUT.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)
    corpus=read_jsonl(ROOT/'data/private/core_v1/corpus.jsonl')
    records=read_jsonl(ROOT/CFG['primary_labels'])
    seal=read_json(ROOT/'data/private/gpt_core_v3/sealed.json')
    assert seal['sha256']==digest(records)
    assert {r['id'] for r in records}=={i['id'] for i in corpus} and len(records)==len(corpus)==1473
    byid={r['id']:r for r in records}
    for item in corpus:
        r=byid[item['id']];assert r['input_sha256']==digest(item);validate_label(r['label'],item)
    # All comparisons are only loaded now that the primary file is sealed.
    audit_items=read_jsonl(ROOT/'data/private/core_v1/audit_all_300.jsonl')
    review=read_jsonl(ROOT/f'labels/runs/core_v1/{digest(audit_items)[:12]}_B.jsonl')
    v4={r['id']:r for r in review}
    for i in audit_items:assert v4[i['id']]['input_sha256']==digest(i)
    validation={'role':'GPT primary, cached DeepSeek V4 sample review only; no human accuracy gold standard.',
        'all_300':compare_group(audit_items,v4,byid),
        'original_development_100':compare_group(read_jsonl(ROOT/'data/private/core_v1/development_100.jsonl'),v4,byid),
        'original_held_out_200':compare_group(read_jsonl(ROOT/'data/private/core_v1/audit_200.jsonl'),v4,byid),
        'by_platform':{p:compare_group([i for i in audit_items if i['platform']==p],v4,byid) for p in ['news','twitter']},
        'independence':'Reuses original GPT 300 judgments and original V4 calls; no new agreement replication. Sample was not drawn after seeing new core results. Multiple direct-coding sessions, model versions not recoverable.'}
    write_json(OUT/'validation.json',validation)
    share=ROOT/'data/shareable/gpt_core_v3';share.mkdir(parents=True,exist_ok=True)
    write_jsonl(share/'GPT_primary_labels.jsonl',[{k:r[k] for k in ['id','input_sha256','source','platform','role','model'] if k in r}|{'label':{k:v for k,v in r['label'].items() if k not in ['evidence','rationale']}} for r in records])
    for name in ['protocol.json','sealed.json','provenance_addendum.json']:
        write_json(share/name,read_json(ROOT/'data/private/gpt_core_v3'/name))
    write_json(share/'export_manifest.json',{'private_annotation_payload_sha256':seal['sha256'],
        'shareable_file_sha256':digest((share/'GPT_primary_labels.jsonl').read_bytes()),
        'note':'Private seal covers full annotation records including evidence/rationales. Shareable rows intentionally remove text excerpts and rationales; their file hash is separate. input_sha256 refers to original full input, not a minimized replacement.'})
    write_json(OUT/'stage1_quality.json',{'corpus_items':len(corpus),'valid_primary_labels':len(records),'input_hashes_verified':len(corpus),
        'literal_evidence_verified':len(corpus),'new_direct_GPT':1173,'reused_direct_GPT':300,'correction_records':5,
        'sealed_sha256':seal['sha256'],'new_paid_API_calls':0,
        'accuracy_limit':'Schema/evidence checks verify traceability, not semantic accuracy. Model agreement is not a gold standard.'})
    media=enrich(corpus,records);macro,panel=build_panel(media)
    media.to_csv(DATA/'monthly_media.csv',index=False);panel.to_csv(DATA/'model_panel.csv',index=False)
    desc=descriptions(corpus,records);write_json(OUT/'descriptive.json',desc)
    models=model_specs();f,coef,valid=forecast(panel,models)
    assert not f.empty
    f.to_csv(DATA/'predictions.csv',index=False);coef.to_csv(DATA/'coefficients.csv',index=False)
    pairs=[('economy_tone','economy'),('memory_tone','memory'),('household_tone','household'),('method_controls_tone','method_controls')]
    pairs += [('memory_'+feature,'memory') for feature in CFG['frame_features']]
    pairs += [('memory_all_content','memory')]
    pairs += [('method_controls_tone','persistence'),('memory','persistence'),('household','memory')]
    report={'version':'gpt_core_v3','config_sha256':digest(CFG),'labels_sha256':digest(records),
        'media_months':len(media),'common_eligible_months':len(valid),'test_n':len(f),'test_start':f.target_month.min(),'test_end':f.target_month.max(),
        'models':models,'metrics':metrics(f,['persistence']+list(models)),
        'increments':{a+'_vs_'+b:comparison(f,a,b) for a,b in pairs},
        'year_metrics':{str(year):metrics(part,['persistence','economy','economy_tone','memory','memory_tone','household','household_tone','method_controls','method_controls_tone','memory_all_content']) for year,part in f.groupby(f.target_month.str[:4])},
        'period_metrics':{name:metrics(f.loc[mask],['persistence','economy','economy_tone','memory','memory_tone','method_controls','method_controls_tone','memory_all_content']) for name,mask in [('before_2025',f.target_month<'2025-01-01'),('from_2025',f.target_month>='2025-01-01')]},
        'coverage':{p:{'candidate':int(media[p+'_candidate_n'].sum()),'eligible':int(media[p+'_eligible_n'].sum()),'scored':int(media[p+'_scored_n'].sum()),'median_scored_per_month':float(media[p+'_scored_n'].median()),'months_zero_scored':int((media[p+'_scored_n']==0).sum())} for p in ['news','twitter']},
        'scope':'All extensions exploratory and fixed before reading new analysis outputs; no winner selection. Retrospective coding, sparse keyword/time windows, headline-only news. No causal or consumer psychology effects identified.'}
    sensitivity={}
    compact={k:models[k] for k in ['economy','economy_tone','memory','memory_tone','household','household_tone','method_controls','method_controls_tone']}
    sensitivity_pairs=pairs[:4]
    for name,nn,nt in [('minimum_2_news_5_tweets',2,5),('minimum_3_news_5_tweets',3,5)]:
        alt,_,eligible=forecast(panel,compact,nn,nt)
        sensitivity[name]={'eligible_n':len(eligible),'test_n':len(alt),'metrics':metrics(alt,['persistence']+list(compact)) if not alt.empty else {},
            'increments':{a+'_vs_'+b:comparison(alt,a,b) for a,b in sensitivity_pairs} if not alt.empty else {}}
    # Remove URL-only differences but do not claim semantic duplicate removal.
    unique=[];seen=set()
    for item in sorted(corpus,key=lambda i:(max(i['published_at'],i.get('discovered_at',i['published_at'])),i['id'])):
        normalized=re.sub(r'\s+',' ',re.sub(r'https?://\S+','',item['text']).lower()).strip()
        key=(item['platform'],item['published_at'][:7],normalized)
        if key not in seen:seen.add(key);unique.append(item)
    ids={i['id'] for i in unique};_,dedup_panel=build_panel(enrich(unique,[r for r in records if r['id'] in ids]))
    alt,_,_=forecast(dedup_panel,compact)
    common=f[['target_month']].merge(alt,on='target_month')
    sensitivity['url_normalized_duplicates']={'removed':len(corpus)-len(unique),'test_n':len(alt),'same_primary_test_months':len(common),
        'metrics':metrics(common,['persistence']+list(compact)),'increments':{a+'_vs_'+b:comparison(common,a,b) for a,b in sensitivity_pairs}}
    relaxed=[]
    for r in records:
        r=dict(r);r['label']=dict(r['label'])
        if r['label']['topics']:r['label']['us_relevance']='yes'
        relaxed.append(r)
    _,relaxed_panel=build_panel(enrich(corpus,relaxed))
    alt,_,_=forecast(relaxed_panel,compact);common=f[['target_month']].merge(alt,on='target_month')
    sensitivity['all_geographies_economic_texts']={'scope':'Geography sensitivity only, includes known foreign economies; cannot be substituted for US consumer exposure.',
        'test_n':len(alt),'same_primary_test_months':len(common),'metrics_on_primary_months':metrics(common,['persistence']+list(compact)),
        'increments_on_primary_months':{a+'_vs_'+b:comparison(common,a,b) for a,b in sensitivity_pairs}}
    # Penalty changes run explicitly without changing the primary function's defaults.
    from sentiment_project import media_models
    original=media_models.ridge_prediction
    for penalty in [.1,10.]:
        def changed(train,current,features,penalty_unused=1., value=penalty):
            return original(train,current,features,penalty=value)
        media_models.ridge_prediction=changed
        try:alt,_,_=forecast(panel,compact)
        finally:media_models.ridge_prediction=original
        assert list(alt.target_month)==list(f.target_month)
        sensitivity['ridge_penalty_'+str(penalty)]={'metrics':metrics(alt,['persistence']+list(compact)),
            'increments':{a+'_vs_'+b:comparison(alt,a,b) for a,b in sensitivity_pairs}}
    report['sensitivity']=sensitivity
    # An economic baseline on the entire macro history does not need media coverage.
    full=macro.copy();full['news_scored_n']=99;full['twitter_scored_n']=99
    full['cumulative_prices_2008']=[100*(snapshot('PCEPI',r.information_cutoff)[r.pce_yoy_period]/snapshot('PCEPI',r.information_cutoff)['2008-12-01']-1) for r in full.itertuples()]
    full['linear_time']=np.arange(len(full))/12
    macro_models={k:models[k] for k in ['economy','memory']}
    macro_models.update({'economy_price_level':BASE+['cumulative_prices_2008'],
        'economy_linear_time':BASE+['linear_time'],
        'memory_price_level':BASE+['sentiment_available','cumulative_prices_2008']})
    all_f,_,_=forecast(full,macro_models)
    all_f['training_mean']=training_mean(full,all_f)
    all_f.to_csv(DATA/'all_macro_predictions.csv',index=False)
    report['all_macro_forecasts']={'n':len(all_f),'start':all_f.target_month.min(),'end':all_f.target_month.max(),
        'metrics':metrics(all_f,['persistence','training_mean']+list(macro_models)),'interpretation':'Same test months within this comparison, full expanding macro history. Different training sample from media-restricted models; do not compare levels directly across the two experiments.'}
    f['training_mean']=training_mean(valid,f)
    f.to_csv(DATA/'predictions.csv',index=False)
    report['metrics']['training_mean']=metrics(f,['training_mean'])['training_mean']
    report['macro_accounting']=macro_accounting(macro)
    report['all_macro_forecasts']['increments']={a+'_vs_'+b:comparison(all_f,a,b) for a,b in [
        ('economy_price_level','economy'),('economy_linear_time','economy'),
        ('memory_price_level','memory'),('memory_price_level','persistence')]}
    # Cross-tabulations describe rhetoric separately from direction of economic tone.
    conditional={}
    for platform in ['news','twitter']:
        selected=[byid[i['id']]['label'] for i in corpus if i['platform']==platform and eligibility(i,byid[i['id']]['label'])]
        conditional[platform]={}
        for tone in ['negative','positive','neutral','mixed']:
            part=[l for l in selected if l['tone']==tone]
            conditional[platform][tone]={'n':len(part),
                'emotional_or_mixed_share':float(np.mean([l['language_style'] in ['emotional','mixed'] for l in part])),
                'political_blame_or_both_share':float(np.mean([l['political_attribution'] in ['blame','both'] for l in part]))}
    write_json(OUT/'tone_rhetoric_cross_tabs.json',conditional)
    latest=panel.iloc[-1]
    report['latest_proxies']={k:latest[k] for k in ['target_month','pce_yoy','cumulative_prices','income_yoy','sentiment_available']}
    report['actual_sentiment_latest']=snapshot('UMCSENT',CFG['evaluation_vintage'])[latest.target_month]
    write_json(OUT/'analysis.json',report)
    # Sanitized annotation-session composition, not evidence of annotation accuracy.
    sessions=defaultdict(Counter)
    pending=read_jsonl(ROOT/'data/private/core_v1/corpus.jsonl')
    reused={r['id'] for r in read_jsonl(ROOT/'data/private/cross_family_v2/GPT_300.jsonl')}
    new=[i for i in pending if i['id'] not in reused]
    session={i['id']:('new_first_540' if n<540 else 'new_last_633') for n,i in enumerate(new)}
    for i in corpus:
        s=session.get(i['id'],'original_300');sessions[s][i['platform']]+=1
        sessions[s]['eligible']+=int(eligibility(i,byid[i['id']]['label']))
    cohort_features={}
    for s in sessions:
        cohort_features[s]={}
        for p in ['news','twitter']:
            part=[i for i in corpus if session.get(i['id'],'original_300')==s and i['platform']==p]
            labs=[byid[i['id']]['label'] for i in part if eligibility(i,byid[i['id']]['label'])]
            cohort_features[s][p]={'candidate_n':len(part),'eligible_n':len(labs),
                'first_publication':min(i['published_at'] for i in part),'last_publication':max(i['published_at'] for i in part),
                'negative_share':float(np.mean([l['tone']=='negative' for l in labs])),
                'emotional_or_mixed_share':float(np.mean([l['language_style'] in ['emotional','mixed'] for l in labs]))}
    write_json(OUT/'session_composition.json',{'counts':dict(sessions),'descriptive_by_session_and_platform':cohort_features,
        'limitation':'Session cohorts differ in dates and platforms; differences cannot isolate model effects. No prospective randomly assigned identical-model comparison.'})
    manifest={'status':'Stages 1 and 2 complete; presentation/report rewrite pending',
        'primary_labels':CFG['primary_labels'],'config':'configs/gpt_core_v3_analysis.json',
        'analysis':'reports/gpt_core_v3/analysis.json','validation':'reports/gpt_core_v3/validation.json',
        'findings':'reports/gpt_core_v3/STAGES_1_2_FINDINGS.zh-CN.md',
        'handoff':'reports/gpt_core_v3/NEXT_MODEL_HANDOFF.md',
        'verification':'reports/gpt_core_v3/verification.json',
        'old_deliverables':'Historical Flash-based artifacts remain unchanged and are not the new research deliverables.',
        'incremental_paid_API_calls':0}
    write_json(ROOT/'reports/ACTIVE_RESEARCH.json',manifest)
    print(json.dumps({'stage1':1473,'test_n':len(f),'metrics':report['metrics'],'increments':report['increments'],'coverage':report['coverage']},ensure_ascii=False,indent=2))

if __name__=='__main__':run()
