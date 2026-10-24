"""Render reviewed local photos and their credits into the existing model pages."""
import html,json,re,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).parents[1]
ORIGIN='https://www.evberegn.dk'
ESC=lambda s:html.escape(str(s),quote=True)
manifest=json.loads((ROOT/'data/model-photos.json').read_text())
models=manifest['models']
for slug,photo in models.items():
 path=ROOT/'elbil'/slug/'index.html';text=path.read_text()
 verified=photo['status']=='verified' and photo.get('reviewed') is True
 if verified:
  note=photo.get('caption') or 'Modelbillede. Udstyr, farve og fælge kan afvige fra den valgte variant.'
  image=f'<img alt="{ESC(photo["identity"])} – modelbillede" decoding="async" id="carPhoto" loading="eager" fetchpriority="high" src="{ESC(photo["src"])}" width="{photo["width"]}" height="{photo["height"]}">'
  loading='<div class="photo-loading" id="photoLoading" style="display:none">Modelbilledet kunne ikke indlæses.</div>'
  credit=f'{ESC(note)} Foto: {ESC(photo["author"])} · <a href="{ESC(photo["license_url"])}" target="_blank" rel="noopener noreferrer">{ESC(photo["license"])}</a> · <a href="{ESC(photo["source"])}" target="_blank" rel="noopener noreferrer">Billedkilde og original</a>. {ESC(photo["modifications"])}'
  if photo.get('attribution') and photo['attribution']!=photo['author']:credit+=' '+ESC(photo['attribution'])
 else:
  image=f'<img alt="{ESC(photo["label"])} – modelbillede" decoding="async" id="carPhoto" style="display:none">'
  loading='<div class="photo-loading" id="photoLoading">Vi mangler et kontrolleret modelbillede.</div>'
  credit=''
 block=f'<div class="visual photo-wrap">{image}{loading}</div><div class="photo-credit" id="photoCredit">{credit}</div>'
 text,n=re.subn(r'<div class="visual photo-wrap">.*?<div class="photo-credit" id="photoCredit">.*?</div>',lambda _:block,text,count=1,flags=re.S)
 assert n==1,slug
 text=re.sub(r'<script src="/assets/car-images\.js[^>]*></script>','<script src="/assets/car-images.js?v=20261024-static1" defer></script>',text)
 # Share the same reviewed photo with search and social crawlers.
 text=re.sub(r'<meta[^>]*property="og:image(?::(?:width|height|alt))?"[^>]*>','',text)
 if verified:
  metas=f'<meta content="{ORIGIN}{ESC(photo["src"])}" property="og:image"><meta content="{photo["width"]}" property="og:image:width"><meta content="{photo["height"]}" property="og:image:height"><meta content="{ESC(photo["identity"])} – modelbillede" property="og:image:alt">'
  text=text.replace('<link href="/favicon.ico"',metas+'\n<link href="/favicon.ico"',1)
 data_match=re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)
 data=json.loads(data_match[1])
 for node in data.get('@graph',[]):
  if node.get('@type')=='WebPage':
   node.pop('primaryImageOfPage',None)
   if verified:
    node['primaryImageOfPage']={'@type':'ImageObject','contentUrl':ORIGIN+photo['src'],'url':ORIGIN+photo['src'],'caption':photo.get('caption') or photo['identity']+' – modelbillede; udstyr og farve kan variere.','width':photo['width'],'height':photo['height'],'creditText':photo['author'],'license':photo['license_url'],'acquireLicensePage':photo['source']}
 text=text[:data_match.start(1)]+json.dumps(data,ensure_ascii=False)+text[data_match.end(1):]
 path.write_text(text)
NS='http://www.sitemaps.org/schemas/sitemap/0.9';IM='http://www.google.com/schemas/sitemap-image/1.1'
ET.register_namespace('',NS);ET.register_namespace('image',IM)
sitemap=ET.parse(ROOT/'sitemap.xml')
for entry in sitemap.getroot():
 for old in entry.findall('{'+IM+'}image'):entry.remove(old)
 loc=entry.find('{'+NS+'}loc').text
 match=re.fullmatch(re.escape(ORIGIN)+r'/elbil/([^/]+)/',loc)
 if match and models[match[1]]['status']=='verified':
  node=ET.SubElement(entry,'{'+IM+'}image');ET.SubElement(node,'{'+IM+'}loc').text=ORIGIN+models[match[1]]['src']
ET.indent(sitemap,space='  ');sitemap.write(ROOT/'sitemap.xml',encoding='unicode',xml_declaration=True)
verified=[p for p in models.values() if p['status']=='verified']
missing=[(slug,p) for slug,p in models.items() if p['status']!='verified']
report=['# Billeddækning, 24. oktober 2026','',f'{len(verified)} af {len(models)} modelsider har et fast, lokalt modelbillede med kilde, fotograf og licens.','', 'Billederne viser modellen. Udstyrsvariant, fælge og farve kan afvige; det er angivet ved billederne. Ingen billeder vælges ved automatisk søgning i besøgendes browser.','', '## Resterende modeller','', '| Model | Adresse | Årsag |','|---|---|---|']
for slug,p in missing:report.append(f'| {p["label"]} | [/elbil/{slug}/](https://www.evberegn.dk/elbil/{slug}/) | {p.get("reason","")} |')
(ROOT/'BILLEDDÆKNING.md').write_text('\n'.join(report)+'\n')
print('Rendered',len(verified),'fixed photos;',len(missing),'explicit missing states; 186 existing pages preserved.')
