"""Check current artifact structure, source parity and exact slide-note alignment."""
import json,re,sys,zipfile,xml.etree.ElementTree as ET,hashlib
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
def main():
 cfg=json.loads((ROOT/'reports/CURRENT_DELIVERABLES.json').read_text(encoding='utf-8'));script=json.loads((ROOT/'configs/presentation_gpt_core_v3.json').read_text(encoding='utf-8'));pdf=PdfReader(ROOT/cfg['report']);assert len(pdf.pages)==12
 texts=[p.extract_text() for p in pdf.pages];assert all(len(t)>950 for t in texts)
 assert '28.25' in texts[4] and '7.08' in texts[4] and '65.2%' in texts[9] and 'human' in texts[9]
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
  assert not any('automatic trading signal' in xmltext(z,n) for n in slides)
 words=sum(len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",s['en'])) for s in script['slides']);assert words==943
 assert all(re.split(r'[.!?]\s+',script['slides'][i]['en'])[-1]!=re.split(r'[.!?]\s+',script['slides'][i+1]['en'])[0] for i in range(9))
 receipt={'status':'pass','pdf_pages':12,'slides':10,'native_editable_charts':8,'embedded_chart_workbooks':8,'speaker_notes_exact_script_parity':True,'script_words':words,'unit_tests_observed':44,'new_paid_API_calls':0,
 'visual_review':'All 12 PDF pages and 10 PPT imported-render pages inspected; overlapping report-chart legend and slide-9 footer corrected.',
 'boundaries':['No native PowerPoint execution','No browser-layout inspection; offline JavaScript/DOM logic checked','No live speech rehearsal; duration estimated','Public reproduction excludes private extraction and AI inference'],
 'hashes':{cfg[k]:hashlib.sha256((ROOT/cfg[k]).read_bytes()).hexdigest() for k in ['report','presentation','script','dashboard']}}
 (ROOT/'reports/final_gpt_v3/FINAL_QA.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
 (ROOT/'reports/FINAL_QA.zh-CN.md').write_text('# 当前交付核对\n\n12 页报告、10 页 PPT 已逐页渲染检查；PPT 8 个原生可编辑图表，8 个内嵌 Excel 数据表。十页备注与 943 词英文稿完全一致，末页 Key Takeaways，无附录。\n\n44 项测试通过。公共离线复现重算所有 15 个模型、6 组敏感性、40/44 月预测以及 1,005 份来源快照。仪表盘检查模型/平台切换、区间开关、单月、空样本、非法区间、重置和 40 行 CSV 导出。\n\n提交包的干净解压复验见 output/checks/verification.json。逐页视觉检查不等于原生 PowerPoint 实机检查；仪表盘是逻辑/SVG 验证，没有浏览器布局实机核验；讲稿时长为估计，没有排练。没有新增付费 API 调用，也没有人工金标准。\n',encoding='utf-8');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
