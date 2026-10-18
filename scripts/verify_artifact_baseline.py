"""Verify frozen study inputs and the separately authorized presentation revision."""
import hashlib,json

def verify_baseline(root):
 baseline=json.loads((root/'reports/rubric_extension/baseline_receipt.json').read_text(encoding='utf-8'))
 receipt_path=root/'reports/final_gpt_v3/presentation_rubric_revision.json'
 revision=json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.is_file() else None
 allowed={'output/slides.pptx','output/speaker_notes.md'};frozen=0;revised=0
 for name,expected in baseline['files'].items():
  actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
  if actual==expected:frozen+=1;continue
  assert name in allowed and revision is not None,f'Frozen input changed: {name}'
  assert revision['revision']=='presentation_rubric_revision_v1'
  assert revision['scope']=='Presentation wording update; analytical inputs and results unchanged.'
  pair=revision['files'][name]
  assert pair['before_sha256']==expected and pair['after_sha256']==actual,f'Unrecorded presentation change: {name}'
  revised+=1
 return {'frozen_hashes_verified':frozen,'approved_presentation_artifacts_verified':revised}
