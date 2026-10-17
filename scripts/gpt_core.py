"""Persist direct assistant coding. No automatic semantic classification."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from sentiment_project.common import digest, read_json, read_jsonl, write_json, write_jsonl, now_utc
from sentiment_project.ai_validation import validate_label
from gpt_audit import MAPS, TOPIC, FIELDS

FOLDER = ROOT / 'data/private/gpt_core_v3'

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', 'show', 'record', 'correct', 'status', 'seal'])
    p.add_argument('--start', type=int, default=0)
    p.add_argument('--count', type=int, default=30)
    p.add_argument('--input', type=Path)
    a = p.parse_args()
    corpus = read_jsonl(ROOT / 'data/private/core_v1/corpus.jsonl')
    reused = {r['id']: r for r in read_jsonl(ROOT / 'data/private/cross_family_v2/GPT_300.jsonl')}
    pending = [i for i in corpus if i['id'] not in reused]
    FOLDER.mkdir(parents=True, exist_ok=True)
    judgments = FOLDER / 'judgments'
    judgments.mkdir(exist_ok=True)
    protocol_path = FOLDER / 'protocol.json'
    if a.action == 'prepare':
        if protocol_path.exists():
            raise ValueError('Protocol already frozen')
        for item in corpus:
            if item['id'] in reused:
                r = reused[item['id']]
                assert r['input_sha256'] == digest(item)
                validate_label(r['label'], item)
        write_json(protocol_path, {
            'study_id': 'gpt_core_v3', 'created_at': now_utc(),
            'corpus_sha256': digest(corpus), 'pending_sha256': digest(pending),
            'prompt_sha256': digest((ROOT/'prompts/economic_coding_v2.txt').read_bytes()),
            'primary_coder': 'GPT / current Codex assistant; immutable model identifier unavailable',
            'method': 'Direct reading and categorical judgments by assistant. Script only expands explicit codes and validates evidence and schema.',
            'reused_GPT_items': len(reused), 'new_GPT_items': len(pending),
            'reused_source_sha256': digest(list(reused.values())),
            'reviewer': 'Cached DeepSeek V4 review of original 300-item sample only; never primary coding.',
            'independence_limit': 'Retrospective recoding after aggregate study and review results were seen. Old item-level DeepSeek labels withheld during new coding. Not prospective blind validation.',
            'adjudication': 'Disagreement is reported, not converted into truth. No human validation.',
            'analysis_rule': 'Recompute all media-dependent results after all primary judgments are sealed. Do not tune judgments to outcomes or review agreement.',
            'incremental_API_requests': 0})
    elif a.action == 'show':
        for n in range(a.start, min(a.start + a.count, len(pending))):
            i = pending[n]
            print(json.dumps({'n': n, 'platform': i['platform'], 'text': i['text'], 'official_evidence': i.get('official_evidence', [])}, ensure_ascii=False))
    elif a.action == 'record':
        if (FOLDER/'sealed.json').exists():
            raise ValueError('Primary labels are sealed')
        for n, code, quotes, rationale in json.loads(a.input.read_text(encoding='utf-8')):
            item = pending[n]
            codes = code.split()
            assert len(codes) == len(FIELDS)
            label = {'id': item['id'], 'evidence': quotes, 'rationale': rationale}
            for field, c in zip(FIELDS, codes):
                label[field] = ([TOPIC[k] for k in c] if c != '_' else []) if field == 'topics' else MAPS[field][c]
            validate_label(label, item)
            dest = judgments/f'{n:04d}.json'
            if dest.exists():
                assert read_json(dest)['label'] == label, 'Existing judgment cannot be silently changed'
            else:
                write_json(dest, {'id': item['id'], 'label': label, 'input_sha256': digest(item),
                    'source': item['source'], 'platform': item['platform'], 'role': 'GPT_primary',
                    'model': 'GPT / Codex direct assistant judgment', 'recorded_at': now_utc(),
                    'protocol_sha256': digest(read_json(protocol_path))})
    elif a.action == 'correct':
        if (FOLDER/'sealed.json').exists():
            raise ValueError('Primary labels are sealed')
        for change in json.loads(a.input.read_text(encoding='utf-8')):
            n = change['index']
            path = judgments/f'{n:04d}.json'
            record = read_json(path)
            before = dict(record['label'])
            if all(before[k] == v for k, v in change['fields'].items()):
                continue
            record['label'].update(change['fields'])
            validate_label(record['label'], pending[n])
            record.setdefault('corrections', []).append({'at': now_utc(), 'before': before,
                'fields': change['fields'], 'reason': change['reason'],
                'stage': 'Pre-seal rubric consistency review; new analysis outcomes not yet calculated'})
            write_json(path, record)
    elif a.action == 'seal':
        new = {r['id']: r for r in (read_json(f) for f in sorted(judgments.glob('*.json')))}
        assert len(new) == len(pending), 'Cannot seal incomplete coding'
        rows = []
        for item in corpus:
            record = reused[item['id']] if item['id'] in reused else new[item['id']]
            assert record['input_sha256'] == digest(item)
            validate_label(record['label'], item)
            rows.append(record)
        write_jsonl(FOLDER/'GPT_primary.jsonl', rows)
        write_json(FOLDER/'sealed.json', {'sealed_at': now_utc(), 'items': len(rows), 'sha256': digest(rows), 'protocol_sha256': digest(read_json(protocol_path))})
    done = len(list(judgments.glob('*.json')))
    progress = {'total': len(corpus), 'reused': len(reused), 'new_completed': done, 'remaining': len(pending)-done, 'sealed': (FOLDER/'sealed.json').exists()}
    write_json(FOLDER/'progress.json', progress)
    print(json.dumps(progress))

if __name__ == '__main__':
    main()
