"""Validate static SEO, navigation and data with the Python standard library."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser
import json,xml.etree.ElementTree as ET,csv,re
ROOT=Path(__file__).parents[1]
ORIGIN='https://www.evberegn.dk'
class Page(HTMLParser):
 def __init__(self,text):
  super().__init__();self.canonicals=[];self.descriptions=[];self.robots=[];self.titles=[];self.h1=0;self.links=[];self.scripts=[];self.current=None;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='link' and a.get('rel')=='canonical':self.canonicals.append(a.get('href'))
  if tag=='meta':
   if a.get('name')=='description':self.descriptions.append(a.get('content',''))
   if a.get('name')=='robots':self.robots.append(a.get('content',''))
  if tag=='h1':self.h1+=1
  if tag=='title':self.current='title';self.titles.append('')
  if tag=='a':self.links.append(a)
  if tag=='script':self.current='script';self.scripts.append({'attrs':a,'text':''})
 def handle_data(self,data):
  if self.current=='title':self.titles[-1]+=data
  if self.current=='script':self.scripts[-1]['text']+=data
 def handle_endtag(self,tag):
  if tag in ('title','script'):self.current=None
models=sorted((ROOT/'elbil').glob('*/index.html'))
assert len(models)==186
WITHDRAWN={'kia-ev1-standard-range','kia-sportage-ev-standard','volvo-ex50-single-motor-rwd','volvo-ex70-single-motor'}
ALIAS={'hyundai-ioniq-7-standard':'hyundai-ioniq-9-rwd-advanced'}
EXCLUDED=WITHDRAWN|set(ALIAS)
pages={}
for path in [ROOT/'index.html',ROOT/'elbil/index.html',*models]:
 relative=path.relative_to(ROOT).as_posix()
 url=ORIGIN+('/' if relative=='index.html' else '/'+relative.removesuffix('index.html'))
 pages[url]=Page(path.read_text())
sitemap=ET.parse(ROOT/'sitemap.xml')
locations=[x.text for x in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(locations)==len(set(locations))==183
assert set(locations)=={u for u in pages if u.rstrip('/').split('/')[-1] not in EXCLUDED},'Sitemap must contain exactly the indexable canonical pages'
robot=RobotFileParser();robot.parse((ROOT/'robots.txt').read_text().splitlines())
for url,page in pages.items():
 slug=url.rstrip('/').split('/')[-1]
 assert page.canonicals==[ORIGIN+'/elbil/'+ALIAS[slug]+'/' if slug in ALIAS else url],f'Wrong canonical: {url}'
 assert len(page.titles)==1 and page.titles[0],f'Missing title: {url}'
 assert len(page.descriptions)==1 and page.descriptions[0],f'Missing description: {url}'
 assert page.h1==1,f'Expected one H1: {url}'
 assert any('noindex' in x.lower() for x in page.robots)==(slug in WITHDRAWN),f'Wrong indexing state: {url}'
 assert robot.can_fetch('Googlebot',url),f'Blocked by robots.txt: {url}'
 for script in page.scripts:
  src=script['attrs'].get('src')
  if src and src.startswith('/'):assert (ROOT/urlsplit(src).path.lstrip('/')).is_file(),f'Missing script {src}'
  if script['attrs'].get('type')=='application/ld+json':json.loads(script['text'])
 for link in page.links:
  target=urlsplit(urljoin(url,link.get('href','')))
  if target.netloc=='www.evberegn.dk' and target.path.startswith('/elbil/') and target.path.endswith('/'):
   assert ORIGIN+target.path in pages,f'Broken model link {url}: {target.path}'
 if url.count('/')>4 and slug not in EXCLUDED:assert any(x.get('href','').startswith('/?car=') for x in page.links),f'Missing car link {url}'
for field in ('titles','descriptions'):
 values=[getattr(p,field)[0] for p in pages.values()]
 assert len(values)==len(set(values)),f'Duplicate {field}'
cards=[a for a in pages[ORIGIN+'/'].links if 'calc-card' in a.get('class','').split()]
assert {a.get('href') for a in cards}=={f'#beregner-{i}' for i in range(1,21)}
data=list(csv.reader((ROOT/'bil-data-komplet.csv').open(encoding='utf-8-sig'),delimiter=';'))
records={(r[0],r[1]):r for r in data[1:] if len(r)==7}
assert len(records)==181
assert records['XPENG','G6 Standard Range RWD'][4:6]==['470','16.9']
assert records['XPENG','L03 Standard Range RWD'][5]=='15.3'
assert records['BYD','Atto 3 EVO Design'][5]=='16.4'
home_text=(ROOT/'index.html').read_text()
cars=json.loads(re.search(r'const cars=(\[.*?\]); let selectedCar=',home_text,re.S)[1])
cars_by_name={(row[0],row[1]):row for row in cars}
assert len(cars_by_name)==181
sources=json.loads((ROOT/'data/model-data-sources.json').read_text())
overview=(ROOT/'elbil/index.html').read_text()
for slug,source in sources.items():
 expected=source['consumption_kwh_100km']
 assert cars_by_name[source['brand'],source['model']][5]==expected
 page=pages[ORIGIN+'/elbil/'+slug+'/']
 calculators=[s for s in page.scripts if '/model-calculator.js' in s['attrs'].get('src','')]
 assert len(calculators)==1 and float(calculators[0]['attrs']['data-consumption'])==expected
 display=str(expected).replace('.',',')+' kWh/100 km'
 assert display in page.descriptions[0]
 card=re.search(r'<a\b[^>]*href="/elbil/'+re.escape(slug)+r'/"[^>]*>(.*?)</a>',overview,re.S)[1]
 assert display in card
 if 'range_km' in source:
  assert cars_by_name[source['brand'],source['model']][4]==source['range_km']
  assert str(source['range_km'])+' km' in page.descriptions[0]
assert cars_by_name['Elveon Motors','Min-E Sedan'][2:]==[None]*5
assert records['Elveon Motors','Min-E Sedan'][2:]==['']*5
assert cars_by_name['XPENG','L03 Standard Range RWD'][3]==58.3
for forbidden in EXCLUDED:
 assert not re.search(r'href="/elbil/'+re.escape(forbidden)+r'/"',overview)
 assert not re.search(r'href="/elbil/'+re.escape(forbidden)+r'/"',home_text)
assert 'unzip -o' not in (ROOT/'.github/workflows/installer.yml').read_text()
print('PASS: 188 preserved URLs, 183 sitemap entries, 181 selectable models, four noindex explanations, one IONIQ alias, unknown Elveon data and all 20 calculators.')
