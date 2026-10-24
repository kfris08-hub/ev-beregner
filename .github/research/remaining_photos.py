"""Read-only research of the remaining photo identities; no production pages change."""
import base64,html,io,json,re,time,unicodedata,urllib.parse,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).parents[2];OUT=ROOT/'.github/research/remaining';OUT.mkdir(parents=True,exist_ok=True)
UA='EVBeregn-model-photo-review/1.0 (https://www.evberegn.dk/; credited image research)'
def get(url,binary=False):
 for n in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=30) as r:raw=r.read()
   return raw if binary else json.loads(raw)
  except Exception:
   if n==2:raise
   time.sleep(1+n)
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',str(s or '')))).strip()
def norm(s):return unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
queries={
'xpeng-l03-standard-range-rwd':(['XPeng L03'],r'xpeng.*l03',r'interior|cockpit|dashboard|logo|detail'),
'elveon-motors-min-e-sedan-base':(['Wuling Hongguang Mini EV 2025','Wuling Hongguang Mini EV 4 door'],r'wuling.*mini.*(ii|5dr|4.?door|2025|2026)',r'interior|cockpit|dashboard|logo|detail|cabrio|macaron|2020|2021|2022|2023'),
'mercedes-benz-gla-with-eq-technology-200':(['Mercedes-Benz GLA 2026','Mercedes-Benz GLA electric','Mercedes-Benz H248'],r'(gla.*(2026|electric|eq)|h248)',r'interior|cockpit|dashboard|logo|detail|h247|h246|\b250[ _-]+e\b|camoufl|erlkonig'),
'volkswagen-id-cross-life':(['Volkswagen ID. Cross 2026','Volkswagen ID. Cross'],r'volkswagen.*id[ ._-]*cross',r'interior|cockpit|dashboard|logo|detail|camoufl|crozz')}
all_candidates={};pictures=[];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
for slug,(searches,required,bad) in queries.items():
 files={}
 for query in searches:
  url='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','generator':'search','gsrnamespace':6,'gsrsearch':query,'gsrlimit':50,'prop':'imageinfo','iiprop':'url|extmetadata|size|mime','iiurlwidth':1200})
  try:
   data=get(url)
   for p in data.get('query',{}).get('pages',{}).values():
    title=p['title'];name=norm(title);ii=(p.get('imageinfo') or [{}])[0];m=ii.get('extmetadata',{})
    if not re.search(required,name,re.I) or re.search(bad,name,re.I):continue
    if ii.get('mime') not in ('image/jpeg','image/png','image/webp') or ii.get('width',0)<800 or ii.get('width',0)/max(1,ii.get('height',0))<1.08:continue
    lic=clean(m.get('LicenseShortName',{}).get('value'));license_url=html.unescape(m.get('LicenseUrl',{}).get('value',''))
    if not (re.match(r'https?://creativecommons.org/licenses/by(?:-sa)?/',license_url) or lic in ('CC0','CC0 1.0','Public domain')):continue
    if lic.startswith('CC0'):license_url='https://creativecommons.org/publicdomain/zero/1.0/'
    elif lic=='Public domain':license_url=license_url or 'https://creativecommons.org/publicdomain/mark/1.0/'
    else:license_url=license_url.replace('http://','https://').split('/deed.')[0].rstrip('/')+'/'
    author=clean(m.get('Artist',{}).get('value'))
    if not author:continue
    files[title]={'file':title,'url':ii.get('thumburl') or ii['url'],'original_url':ii['url'],'source':ii.get('descriptionurl') or 'https://commons.wikimedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_')),'author':author,'license':lic,'license_url':license_url,'credit':clean(m.get('Credit',{}).get('value')),'attribution':clean(m.get('Attribution',{}).get('value')),'description':clean(m.get('ImageDescription',{}).get('value'))[:1800],'width_original':ii['width'],'height_original':ii['height'],'checked_at':'2026-10-24','modifications':'Nedskaleret og konverteret til WebP; ingen beskæring.'}
  except Exception as e:print('QUERY_ERROR',slug,query,str(e),flush=True)
 candidates=list(files.values());candidates.sort(key=lambda p:(bool(re.search(r'concept|2025',p['file'],re.I)),not bool(re.search(r'front|001|img01',p['file'],re.I))))
 all_candidates[slug]=candidates
 print('MODEL_CANDIDATES '+json.dumps({'slug':slug,'candidates':[{'n':n,'file':p['file'],'description':p['description'],'license':p['license']} for n,p in enumerate(candidates,1)]},ensure_ascii=False),flush=True)
 for n,p in enumerate(candidates[:8],1):
  try:
   raw=get(p['url'],True);image=Image.open(io.BytesIO(raw));image.load();image=image.convert('RGB');image.thumbnail((310,165))
   pictures.append((slug,n,p,image))
  except Exception as e:print('IMAGE_ERROR',slug,n,str(e),flush=True)
(OUT/'candidates.json').write_text(json.dumps(all_candidates,ensure_ascii=False,indent=2)+'\n')
for start in range(0,len(pictures),16):
 sheet=Image.new('RGB',(1280,920),'#eeeeee');draw=ImageDraw.Draw(sheet)
 for j,(slug,n,p,image) in enumerate(pictures[start:start+16]):
  x=j%4*320;y=j//4*230;sheet.paste(image,(x+(312-image.width)//2,y))
  title=slug+' ['+str(n)+']';draw.text((x+2,y+168),title[:44],font=font,fill='blue');draw.text((x+2,y+181),title[44:88],font=font,fill='blue')
  title=p['file'][5:];draw.text((x+2,y+196),title[:44],font=font,fill='black');draw.text((x+2,y+210),title[44:88],font=font,fill='black')
 out=io.BytesIO();sheet.save(out,format='JPEG',quality=66)
 print('PHOTO_SHEET '+str(start//16+1)+' '+base64.b64encode(out.getvalue()).decode(),flush=True)
# Inspect the importer's outbound source URL exposed in the page/app assets.
for url in ['https://minnyeelbil.dk/maerker/elveon-motors','https://elbilguide.dk/biler/elveon-motors/min-e-sedan']:
 try:
  raw=get(url,True).decode('utf-8','replace')
  for link in re.findall(r'https?[^\s<>"\\]+',raw):
   if 'elveon' in link.lower() and not any(host in link for host in ['minnyeelbil.dk','elbilguide.dk']):print('IMPORTER_LINK',html.unescape(link[:500]),flush=True)
 except Exception as e:print('IMPORTER_LOOKUP_ERROR',str(e),flush=True)
print('DONE',json.dumps({s:len(v) for s,v in all_candidates.items()}),flush=True)
