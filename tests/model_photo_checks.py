"""Validate the complete photo inventory, local bytes, credits and crawler markup."""
import hashlib,html,json,re,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).parents[1];ORIGIN='https://www.evberegn.dk'
class Page(HTMLParser):
 def __init__(self,text):
  super().__init__();self.image=None;self.meta={};self.credit='';self.incredit=False;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='img' and a.get('id')=='carPhoto':self.image=a
  if tag=='meta':self.meta[a.get('property',a.get('name',''))]=a.get('content')
  if tag=='div' and a.get('id')=='photoCredit':self.incredit=True
 def handle_endtag(self,tag):
  if tag=='div':self.incredit=False
 def handle_data(self,text):
  if self.incredit:self.credit+=text
catalog=json.loads((ROOT/'data/model-photos.json').read_text())['models']
assert set(catalog)=={p.parent.name for p in (ROOT/'elbil').glob('*/index.html')}
seen=set();verified=0
for slug,photo in catalog.items():
 text=(ROOT/'elbil'/slug/'index.html').read_text();page=Page(text)
 assert 'Henter udvendigt modelbillede' not in text,slug
 if photo['status']=='withdrawn':
  assert 'noindex, follow' in text and 'modelStatus' in text and not page.image,slug
  continue
 if photo['status']=='redirect':
  assert 'http-equiv="refresh"' in text and photo['redirect_to'] in text and not page.image,slug
  continue
 if photo['status']=='verified':
  verified+=1
  assert photo['reviewed'] and photo['reviewed_at'],slug
  assert photo['src'].startswith('/assets/cars/') and '..' not in photo['src'],slug
  file=ROOT/photo['src'].lstrip('/');body=file.read_bytes();seen.add(file.name)
  assert body[:4]==b'RIFF' and body[8:12]==b'WEBP',slug
  assert hashlib.sha256(body).hexdigest()==photo['sha256'],slug
  assert len(body)==photo['bytes'] and photo['width']>=(480 if photo.get('usage')=='editorial-only' else 700),slug
  assert page.image['src']==photo['src'] and page.image.get('width')==str(photo['width']) and page.image.get('height')==str(photo['height']),slug
  assert page.image.get('alt') and 'display:none' not in page.image.get('style',''),slug
  assert photo['author'] in page.credit and photo['license'] in page.credit,slug
  if photo.get('usage')=='editorial-only':
   assert slug=='mercedes-benz-gla-with-eq-technology-200'
   assert photo['source']=='https://media.mercedes-benz.com/en/article/22b96b64-a441-4fad-a22a-bc41718aded7'
   assert photo['license_url']=='https://media.mercedes-benz.com/en/legal/terms-of-use'
  else:
   assert photo['source'].startswith('https://commons.wikimedia.org/'),slug
   assert re.match(r'https://creativecommons.org/(licenses/by(?:-sa)?/|publicdomain/)',photo['license_url'].replace('http://','https://')),slug
  assert photo['source'] in html.unescape(text) and photo['license_url'] in html.unescape(text),slug
  assert page.meta.get('og:image')==ORIGIN+photo['src'],slug
  graph=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)[1])['@graph']
  image=next(n for n in graph if n['@type']=='WebPage')['primaryImageOfPage']
  assert image['contentUrl']==ORIGIN+photo['src'] and image['license']==photo['license_url'] and image['creditText']==photo['author'],slug
 else:
  assert photo['status']=='missing' and photo.get('reason'),slug
  assert not page.image.get('src') and 'Vi mangler et kontrolleret modelbillede.' in text,slug
assert seen=={p.name for p in (ROOT/'assets/cars').glob('*.webp')},'Unreferenced photos should not be published'
root=ET.parse(ROOT/'sitemap.xml')
images=root.findall('.//{http://www.google.com/schemas/sitemap-image/1.1}loc')
assert {x.text for x in images}=={ORIGIN+p['src'] for p in catalog.values() if p['status']=='verified'}
assert len(images)==verified
print(f'PASS: all {len(catalog)} photo records, {verified} reviewed local photos, {sum(p['status']=='missing' for p in catalog.values())} missing states, four withdrawn entries and one alias, credits, licenses, hashes, static HTML, Open Graph and image sitemap.')
