"""Prepare final-authoring inputs and transparent ancillary measurement checks."""
import json,re,sys
from collections import Counter
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from sentiment_project.common import read_json,read_jsonl,write_json,write_jsonl,digest
from analyze_gpt_core_v3 import eligibility

F=ROOT/'reports/final_gpt_v3';F.mkdir(parents=True,exist_ok=True)
corpus=read_jsonl(ROOT/'data/private/core_v1/corpus.jsonl')
records=read_jsonl(ROOT/'data/private/gpt_core_v3/GPT_primary.jsonl');labels={r['id']:r['label'] for r in records}
positive=set('growth growing gain gains strong stronger boom booming improve improving recovery recover optimistic surge rising'.split())
negative=set('recession crisis collapse crash layoffs unemployment weak weaker struggling decline declining poverty pessimistic fear suffer costly'.split())
rows=[];counts={p:Counter() for p in ['news','twitter']}
for i in corpus:
 l=labels[i['id']]
 if not eligibility(i,l):continue
 words=re.findall('[a-z]+',i['text'].lower());score=sum(w in positive for w in words)-sum(w in negative for w in words)
 lexical='positive' if score>0 else 'negative' if score<0 else 'neutral'
 gpt='neutral' if l['tone']=='mixed' else l['tone'];c=counts[i['platform']]
 c['n']+=1;c['agree']+=int(gpt==lexical);c['pair_'+gpt+'_'+lexical]+=1
 rows.append({'id':i['id'],'platform':i['platform'],'word_score':score,'dictionary_tone':lexical,'GPT_tone_mixed_as_neutral':gpt})
write_jsonl(ROOT/'data/shareable/gpt_core_v3/dictionary_scores.jsonl',rows)
write_json(F/'dictionary_comparison.json',{'scope':'Unvalidated toy word-count comparator, no FinBERT/RoBERTa or accuracy gold standard. Mixed mapped to neutral solely for this three-class comparison.',
 'positive_words':sorted(positive),'negative_words':sorted(negative),
 'by_platform':{p:{**dict(c),'agreement':c['agree']/c['n']} for p,c in counts.items()}})
checks=read_json(ROOT/'configs/gpt_core_v3_constructed_checks.json')
write_json(F/'constructed_checks.json',{'pairs':len(checks['pairs']),'scope':checks['protocol'],
 'tone_unchanged':sum(p['judgments'][0][0]==p['judgments'][1][0] for p in checks['pairs']),
 'political_attribution_unchanged':sum(p['judgments'][0][1]==p['judgments'][1][1] for p in checks['pairs']),
 'inference':'Explicit paired coding by the same assistant with visible pairing. Not blinded, not representative, and not a test of repeated independent API behavior.'})
meta=[{**{k:i[k] for k in ['id','platform','source','source_level','published_at','discovered_at'] if k in i},
       'original_input_sha256':digest(i)} for i in corpus]
write_jsonl(ROOT/'data/shareable/gpt_core_v3/corpus_metadata.jsonl',meta)
seen=set();excluded=[]
for i in sorted(corpus,key=lambda i:(max(i['published_at'],i.get('discovered_at',i['published_at'])),i['id'])):
 key=(i['platform'],i['published_at'][:7],re.sub(r'\s+',' ',re.sub(r'https?://\S+','',i['text']).lower()).strip())
 if key in seen:excluded.append(i['id'])
 else:seen.add(key)
write_json(ROOT/'data/shareable/gpt_core_v3/dedup_excluded_ids.json',{'ids':excluded,'scope':'Fixed private-text normalization result; arithmetic can replay exclusions but cannot independently re-extract duplicates without private texts.'})

def csv(n):return json.loads(pd.read_csv(ROOT/'data/processed'/n).to_json(orient='records'))
analysis=read_json(ROOT/'reports/gpt_core_v3/analysis.json')
data={'analysis':analysis,'descriptive':read_json(ROOT/'reports/gpt_core_v3/descriptive.json'),
 'audit':read_json(ROOT/'reports/gpt_core_v3/validation.json'),
 'panel':csv('gpt_core_v3/model_panel.csv'),'media':csv('gpt_core_v3/monthly_media.csv'),
 'predictions':csv('gpt_core_v3/predictions.csv'),'macro':csv('gpt_core_v3/macro_accounting.csv'),
 'subindices':csv('sentiment_subindices_descriptive.csv')}
write_json(F/'authoring_data.json',data)
script=read_json(ROOT/'configs/presentation_gpt_core_v3.json')
for s in script['slides']:s['words']=len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",s['en']))
total=sum(s['words'] for s in script['slides']);seconds=sum(s['seconds'] for s in script['slides'])
write_json(F/'script_timing.json',{'words':total,'allocated_seconds':seconds,'estimated_minutes_at_125_wpm':total/125,
 'estimated_minutes_at_135_wpm':total/135,'slides':[{'slide':s['slide'],'words':s['words'],'seconds':s['seconds']} for s in script['slides']],
 'scope':'Text-based estimate; actual delivery needs rehearsal. Allocations include pointing and pauses.'})
text='# '+script['title']+'\n\nTen slides. Suggested duration: '+str(seconds//60)+' minutes '+str(seconds%60)+' seconds. English only.\n\n'
for s in script['slides']:text+=f'## Slide {s["slide"]}. {s["title"]}\n\n{s["en"]}\n\n'
(F/'SPEAKER_SCRIPT.en.md').write_text(text,encoding='utf-8')
print(json.dumps({'script_words':total,'allocated_seconds':seconds,'dictionary':{p:round(c['agree']/c['n'],3) for p,c in counts.items()},'dedup_exclusions':len(excluded)},indent=2))
