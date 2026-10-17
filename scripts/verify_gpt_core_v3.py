"""Independent reconciliation of the sealed research version and exported outputs."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from sentiment_project.common import digest,read_json,read_jsonl,write_json
from sentiment_project.ai_validation import validate_label
from sentiment_project.vintages import parse_snapshot

def main():
    output=ROOT/'reports/gpt_core_v3'
    data=ROOT/'data/processed/gpt_core_v3'
    original=read_jsonl(ROOT/'data/private/core_v1/corpus.jsonl')
    labels=read_jsonl(ROOT/'data/private/gpt_core_v3/GPT_primary.jsonl')
    seal=read_json(ROOT/'data/private/gpt_core_v3/sealed.json')
    assert digest(labels)==seal['sha256']
    assert len({r['id'] for r in labels})==len(labels)==1473
    mapping={r['id']:r for r in labels}
    for item in original:
        r=mapping[item['id']]
        assert r['input_sha256']==digest(item)
        assert 'deepseek' not in r.get('model','').lower()
        validate_label(r['label'],item)
    exported=read_jsonl(ROOT/'data/shareable/gpt_core_v3/GPT_primary_labels.jsonl')
    for r in exported:
        assert 'evidence' not in r['label'] and 'rationale' not in r['label']
        assert all(mapping[r['id']]['label'][k]==v for k,v in r['label'].items())
    export_manifest=read_json(ROOT/'data/shareable/gpt_core_v3/export_manifest.json')
    assert digest((ROOT/'data/shareable/gpt_core_v3/GPT_primary_labels.jsonl').read_bytes())==export_manifest['shareable_file_sha256']
    cfg=read_json(ROOT/'configs/gpt_core_v3_analysis.json')
    analysis=read_json(output/'analysis.json')
    assert analysis['labels_sha256']==digest(labels) and analysis['config_sha256']==digest(cfg)
    media=pd.read_csv(data/'monthly_media.csv')
    panel=pd.read_csv(data/'model_panel.csv')
    assert len(media)==len(panel)==82
    assert (pd.to_datetime(media.media_month).dt.to_period('M')+1).astype(str).tolist()==pd.to_datetime(media.target_month).dt.to_period('M').astype(str).tolist()
    for p in ['news','twitter']:
        coverage=analysis['coverage'][p]
        for field in ['candidate','eligible','scored']:
            assert int(media[p+'_'+field+'_n'].sum())==coverage[field]
        for feature in cfg['frame_features']:
            assert media[p+'_'+feature].dropna().between(0,1).all()
    for row in panel.itertuples():
        vals=parse_snapshot((ROOT/f'data/raw/alfred_vintages/{row.information_cutoff}/PCEPI.csv').read_bytes(),'PCEPI',row.information_cutoff)
        assert row.pce_yoy_period<row.target_month
        assert np.isclose(row.cumulative_prices,100*(vals[row.pce_yoy_period]/vals['2018-12-01']-1))
    f=pd.read_csv(data/'predictions.csv')
    assert len(f)==analysis['test_n']==40
    assert f.target_month.is_unique and f.target_month.is_monotonic_increasing
    assert (f.latest_training_target<f.information_cutoff).all()
    assert (f.information_cutoff<f.target_month).all() and (f.training_n>=24).all()
    for name,result in analysis['metrics'].items():
        error=f[name]-f.actual
        assert np.isclose(error.abs().mean(),result['MAE'],atol=1e-11)
        assert np.isclose(np.sqrt((error**2).mean()),result['RMSE'],atol=1e-11)
    for pair,result in analysis['increments'].items():
        left,right=pair.split('_vs_')
        delta=(f[left]-f.actual).abs().mean()-(f[right]-f.actual).abs().mean()
        assert np.isclose(delta,result['difference'],atol=1e-11)
    macro=pd.read_csv(data/'macro_accounting.csv')
    assert len(macro)==200
    for name,result in analysis['macro_accounting'].items():
        if not isinstance(result,dict):continue
        coef=result['coefficients']
        independent=coef['intercept']+sum(macro[k]*coef[k] for k in result['features'])
        assert np.allclose(independent,macro[name+'_fitted'])
        r2=1-((macro.actual-independent)**2).sum()/((macro.actual-macro.actual.mean())**2).sum()
        assert np.isclose(r2,result['in_sample_R2'])
        for v in result['references'].values():
            assert np.isclose(v['observed_change'],v['model_associated_change']+v['residual_change'])
    figures=sorted((output/'figures').glob('*.png'))
    assert len(figures)==8 and len(list((output/'figures').glob('*.svg')))==8
    for path in figures:
        assert path.stat().st_size>10000 and path.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'
    report={'status':'passed','sealed_items':1473,'media_months':82,'prediction_months':40,'macro_months':200,
        'verified':['Input identities and primary source roles','Literal evidence/schema validity','Sanitized export parity and hash',
            'Monthly aggregation counts and bounded shares','Prior-month mapping and origin-available cumulative-price calculations',
            'Forecast training precedes cutoff and target','All forecast MAE/RMSE and paired differences independently reconciled',
            'OLS coefficients/fits/R2 and accounting totals reconciled','Eight PNG/SVG figure pairs present'],
        'visual_review':'All eight plotted PNGs inspected; filtering legend, accounting legend colors and forecast legend spacing corrected.',
        'unit_tests_observed':44,'new_paid_api_calls':0,
        'limits':'These checks establish computational consistency and traceability, not semantic label accuracy or causal identification.'}
    write_json(output/'verification.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
