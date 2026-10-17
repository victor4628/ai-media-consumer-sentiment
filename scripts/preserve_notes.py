"""Apply only authored speaker-note paragraphs to a saved user's PPTX package."""
import copy,io,json,posixpath,re,sys,zipfile
from lxml import etree as E
from openpyxl import load_workbook
from pathlib import Path
source,candidate,plan=map(Path,sys.argv[1:4]);P='http://schemas.openxmlformats.org/presentationml/2006/main';A='http://schemas.openxmlformats.org/drawingml/2006/main'
NS={'p':P,'a':A}
def note_name(z,i):
 rel=E.fromstring(z.read(f'ppt/slides/_rels/slide{i}.xml.rels'));target=next(r.attrib['Target'] for r in rel if r.attrib['Type'].endswith('/notesSlide'))
 return target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('ppt/slides',target))
def body(root):
 for s in root.findall('.//p:sp',NS):
  ph=s.find('p:nvSpPr/p:nvPr/p:ph',NS)
  if ph is not None and ph.attrib.get('type')=='body':return s.find('p:txBody',NS)
 raise ValueError('No speaker-notes body placeholder')
def plain(b):return '\n'.join(''.join(t.text or '' for t in p.findall('.//a:t',NS)) for p in b.findall('a:p',NS))
cfg=json.loads(plan.read_text(encoding='utf-8'))
with zipfile.ZipFile(source) as original,zipfile.ZipFile(candidate) as authored:
 blobs={n:original.read(n) for n in original.namelist()};changed=[]
 for s in cfg['slides']:
  i=s['slide'];oldname=note_name(original,i);newname=note_name(authored,i);old=E.fromstring(blobs[oldname]);new=E.fromstring(authored.read(newname));oldbody=body(old);newbody=body(new)
  expected=s['en']+'\n\nSources\n'+s['source_notes'];normalize=lambda v:' '.join(v.split());assert normalize(plain(newbody))==normalize(expected),i
  # Preserve the user's notes-page geometry, placeholders and paragraph defaults.
  for child in list(oldbody):
   if child.tag=='{'+A+'}p':oldbody.remove(child)
  for child in newbody.findall('a:p',NS):oldbody.append(copy.deepcopy(child))
  blobs[oldname]=E.tostring(old,encoding='utf-8',xml_declaration=True);changed.append(oldname)
 # Office saves some chart cache numbers with 17-digit spelling while its own
 # embedded cells keep the same IEEE-754 value in a shorter decimal spelling.
 # Refresh those spellings from the unchanged source workbooks. No value changes.
 cache_spellings=0;chart_ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
 for name in list(blobs):
  if not re.fullmatch(r'ppt/(?:slides/)?charts/chart\d+\.xml',name):continue
  chart=E.fromstring(blobs[name]);external=chart.find('c:externalData',chart_ns)
  if external is None:continue
  relpath=posixpath.join(posixpath.dirname(name),'_rels',posixpath.basename(name)+'.rels');rels=E.fromstring(blobs[relpath]);rid=external.attrib['{'+chart_ns['r']+'}id'];target=next(r.attrib['Target'] for r in rels if r.attrib['Id']==rid);bookname=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(name),target));wb=load_workbook(io.BytesIO(blobs[bookname]),data_only=True);edits=0
  for ref in chart.findall('.//c:numRef',chart_ns):
   formula=ref.find('c:f',chart_ns).text;sheet,area=formula.rsplit('!',1);values=[cell.value for row in wb[sheet.strip("'")][area.replace('$','')] for cell in row]
   for point in ref.findall('c:numCache/c:pt',chart_ns):
    element=point.find('c:v',chart_ns);value=values[int(point.attrib['idx'])];assert isinstance(value,(int,float)) and float(element.text)==float(value),(name,formula,element.text,value)
    if element.text!=str(value):element.text=str(value);edits+=1
  if edits:blobs[name]=E.tostring(chart,encoding='utf-8',xml_declaration=True);cache_spellings+=edits
 temporary=candidate.with_name('notes-preserved.pptx')
 with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for n,b in blobs.items():z.writestr(n,b)
temporary.replace(candidate)
print(json.dumps({'speaker_note_parts_replaced':len(changed),'identical_numeric_chart_values':True,'chart_cache_decimal_spellings_refreshed':cache_spellings,'embedded_workbooks_and_slide_parts_preserved':True}))
