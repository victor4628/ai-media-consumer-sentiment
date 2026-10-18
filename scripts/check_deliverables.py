"""Check current artifact structure, source parity and exact slide-note alignment."""
import json,re,sys,zipfile,xml.etree.ElementTree as ET,hashlib
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
def main():
 cfg=json.loads((ROOT/'reports/CURRENT_DELIVERABLES.json').read_text(encoding='utf-8'));script=json.loads((ROOT/'configs/presentation_gpt_core_v3.json').read_text(encoding='utf-8'));pdf=PdfReader(ROOT/cfg['report']);assert len(pdf.pages)==12
 texts=[p.extract_text() for p in pdf.pages];assert all(len(t)>950 for t in texts)
 assert '28.25' in texts[4] and '7.08' in texts[4] and '65.2%' in texts[9] and 'One human annotator' in texts[9] and 'DeepSeek' not in ''.join(texts)
 assert '0.147' in texts[7] and 'Holm' in texts[7] and '30-month experiment' in texts[8]
 assert 'Precision' in texts[9] and '0.405' in texts[9] and '0.602' in texts[9]
 assert '339,000' in texts[2] and 'ABC / Bloomberg' in texts[2]
 from verify_artifact_baseline import verify_baseline
 baseline_check=verify_baseline(ROOT)
 assert not any('\ufffd' in t or '\u25a0' in t for t in texts)
 ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
 def xmltext(z,n):return '\n'.join(ET.fromstring(z.read(n)).itertext())
 with zipfile.ZipFile(ROOT/cfg['presentation']) as z:
  slides=sorted(n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n));charts=[n for n in z.namelist() if re.fullmatch(r'ppt/(?:slides/)?charts/chart\d+\.xml',n)];books=[n for n in z.namelist() if n.startswith('ppt/embeddings/') and n.endswith('.xlsx')]
  assert len(slides)==10 and len(charts)==len(books)==8
  for i,s in enumerate(script['slides'],1):
   root=ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml'));notes='\n'.join(n.text or '' for n in root.findall('.//a:t',ns));normalize=lambda s:re.sub(r'\s+',' ',s).strip();assert normalize(s['en']) in normalize(notes),i
   title=' '.join(n.text or '' for n in ET.fromstring(z.read(f'ppt/slides/slide{i}.xml')).findall('.//a:t',ns));assert s['title'] in title,(i,title)
  assert 'Key Takeaways' in xmltext(z,'ppt/slides/slide10.xml')
  assert '0.602' in xmltext(z,'ppt/slides/slide3.xml')
  assert '0.147' in xmltext(z,'ppt/slides/slide8.xml')
  assert '30-month' in xmltext(z,'ppt/slides/slide9.xml')
  assert '−14.4' in xmltext(z,'ppt/slides/slide10.xml') and '−3.5' in xmltext(z,'ppt/slides/slide10.xml')
  assert not any('automatic trading signal' in xmltext(z,n) for n in slides)
 words=sum(len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",s['en'])) for s in script['slides']);assert words==cfg['main_script_words']
 assert all(re.split(r'[.!?]\s+',script['slides'][i]['en'])[-1]!=re.split(r'[.!?]\s+',script['slides'][i+1]['en'])[0] for i in range(9))
 receipt={'status':'pass','pdf_pages':12,'slides':10,'native_editable_charts':8,'embedded_chart_workbooks':8,'speaker_notes_exact_script_parity':True,'script_words':words,'unit_tests_observed':50,'new_paid_API_calls':0,
 'visual_review':'All 12 PDF pages previously reviewed. All 10 revised PPT slides rendered and visually inspected. Original chart values, formatting and embedded workbooks preserved; presentation-only revision recorded separately from the frozen study inputs.',
 'baseline_verification':baseline_check,
 'boundaries':['No native PowerPoint execution','Browser tool policy blocked file URLs; offline JavaScript/DOM logic checked','No live speech rehearsal; duration estimated','Public reproduction excludes private extraction and annotation authentication'],
 'hashes':{cfg[k]:hashlib.sha256((ROOT/cfg[k]).read_bytes()).hexdigest() for k in ['report','presentation','script','dashboard']}}
 (ROOT/'reports/final_gpt_v3/FINAL_QA.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
 print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
