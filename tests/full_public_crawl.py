"""Read-only crawl of every published HTML page, internal target and local asset."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,urljoin,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,re,time,xml.etree.ElementTree as ET

ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';OUT=ROOT/'test-results';OUT.mkdir(exist_ok=True)
catalog=json.loads((ROOT/'data/model-photos.json').read_text())['models']
errors=[];warnings=[]
def fetch(url,method='GET'):
    started=time.monotonic()
    try:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 EVBeregnerTechnicalAudit/1.0'},method=method),timeout=25) as r:
            return {'url':url,'status':r.status,'final':r.geturl(),'headers':{k.lower():v for k,v in r.headers.items()},'body':r.read() if method=='GET' else b'','seconds':round(time.monotonic()-started,3)}
    except HTTPError as e:return {'url':url,'status':e.code,'final':e.geturl(),'headers':{k.lower():v for k,v in e.headers.items()},'body':e.read(),'seconds':round(time.monotonic()-started,3)}
    except Exception as e:return {'url':url,'status':0,'error':str(e),'headers':{},'body':b''}
class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.title='';self.h1=0;self.canonical=[];self.descriptions=[];self.robots=[];self.ids=set();self.links=[];self.assets=[];self.metas={};self.ld=[];self.images=[];self.refresh=False;self.current=None;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.add(a['id'])
        if tag=='title':self.current='title'
        if tag=='h1':self.h1+=1
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag=='meta':
            self.metas[a.get('property',a.get('name',''))]=a.get('content','')
            if a.get('name')=='description':self.descriptions.append(a.get('content',''))
            if a.get('name')=='robots':self.robots.append(a.get('content',''))
            if a.get('http-equiv','').lower()=='refresh':self.refresh=True
        if tag=='link':
            if a.get('rel')=='canonical':self.canonical.append(a.get('href'))
            elif a.get('href') and a.get('rel') in ('stylesheet','icon','apple-touch-icon','manifest'):self.assets.append(a['href'])
        if tag=='script':
            if a.get('src'):self.assets.append(a['src'])
            if a.get('type')=='application/ld+json':self.current='ld';self.ld.append('')
        if tag=='img':
            self.images.append(a)
            if a.get('src'):self.assets.append(a['src'])
    def handle_endtag(self,tag):
        if tag in ('title','script'):self.current=None
    def handle_data(self,data):
        if self.current=='title':self.title+=data
        if self.current=='ld':self.ld[-1]+=data
def problem(message,url):errors.append({'message':message,'url':url})
files=[ROOT/'index.html',ROOT/'elbil/index.html',*sorted((ROOT/'elbil').glob('*/index.html')),*sorted((ROOT/'beregnere').glob('*/index.html'))]
paths=['/' if p==ROOT/'index.html' else '/'+p.relative_to(ROOT).as_posix().removesuffix('index.html') for p in files]
with ThreadPoolExecutor(max_workers=4) as pool:responses=list(pool.map(fetch,[BASE+p for p in paths]))
pages={};assets=set();external=set();titles={};descriptions={}
for path,response in zip(paths,responses):
    url=BASE+path
    if response['status']!=200:problem('HTML response '+str(response['status']),url);continue
    if 'text/html' not in response['headers'].get('content-type',''):problem('Wrong HTML content type',url)
    if 'noindex' in response['headers'].get('x-robots-tag','').lower():problem('Unexpected HTTP noindex',url)
    page=Page(response['body'].decode('utf-8'));pages[path]=page
    slug=path.rstrip('/').split('/')[-1];photo=catalog.get(slug);excluded=photo and photo['status'] in ('withdrawn','redirect')
    canonical=BASE+'/elbil/'+photo['redirect_to']+'/' if photo and photo['status']=='redirect' else url
    if page.canonical!=[canonical]:problem('Wrong canonical '+str(page.canonical),url)
    if not page.title or page.h1!=1 or len(page.descriptions)!=1 or not page.descriptions[0]:problem('Missing or repeated title/H1/description',url)
    if page.title in titles:problem('Duplicate title',url)
    titles[page.title]=url
    description=page.descriptions[0] if page.descriptions else ''
    if description in descriptions:problem('Duplicate description',url)
    descriptions[description]=url
    noindex=any('noindex' in value.lower() for value in page.robots)
    if noindex!=bool((photo and photo['status']=='withdrawn') or any(m['slug']==slug and not m['indexable'] for m in json.loads((ROOT/'data/cars.json').read_text())['models'])):problem('Wrong index/noindex state',url)
    try:
        graph=[json.loads(x) for x in page.ld]
        if photo and photo['status']=='verified':
            webpage=next(n for g in graph for n in g.get('@graph',[]) if n.get('@type')=='WebPage')
            image=webpage['primaryImageOfPage'];creator=image['creator']
            assert image['contentUrl']==BASE+photo['src'] and image['license']==photo['license_url']
            assert creator['@type'] in ('Person','Organization') and creator['name'] in image['copyrightNotice']
            assert image['creditText']==photo['author'] and image['acquireLicensePage']==photo['source']
            if photo['license']=='CC0':assert 'CC0' in image['copyrightNotice'] and '©' not in image['copyrightNotice']
            rendered=next(i for i in page.images if i.get('id')=='carPhoto')
            assert rendered.get('src')==photo['src'] and rendered.get('alt') and int(rendered.get('width',0))>0
    except Exception as e:problem('Structured data/image mismatch: '+str(e),url)
    for target in page.assets+[page.metas.get('og:image','')]:
        if not target:continue
        parsed=urlsplit(urljoin(url,target))
        if parsed.netloc=='www.evberegn.dk':assets.add(BASE+parsed.path)
    for target in page.links:
        parsed=urlsplit(urljoin(url,target))
        if parsed.scheme in ('http','https') and parsed.netloc not in ('www.evberegn.dk','evberegn.dk'):external.add(parsed.geturl())
for path,page in pages.items():
    for target in page.links:
        parsed=urlsplit(urljoin(BASE+path,target))
        if parsed.netloc not in ('www.evberegn.dk','evberegn.dk') or parsed.scheme not in ('http','https'):continue
        dest=parsed.path or '/'
        if dest.endswith('index.html'):dest=dest.removesuffix('index.html')
        if dest not in pages:
            if dest.startswith(('/assets/','/data/')):assets.add(BASE+dest)
            else:problem('Internal link target not found: '+target,BASE+path)
        elif parsed.fragment and parsed.fragment not in pages[dest].ids:
            special=(dest=='/' and re.fullmatch(r'beregner-(?:[1-9]|1[0-9]|20)',parsed.fragment)) or (dest.startswith('/beregnere/') and parsed.fragment.startswith('bil='))
            if not special:problem('Missing anchor: '+target,BASE+path)
with ThreadPoolExecutor(max_workers=4) as pool:asset_responses=list(pool.map(lambda u:fetch(u,'HEAD'),sorted(assets)))
for r in asset_responses:
    if r['status']!=200:problem('Asset response '+str(r['status']),r['url'])
    if r['headers'].get('content-length')=='0':problem('Empty asset',r['url'])
sitemap_response=fetch(BASE+'/sitemap.xml');robot_response=fetch(BASE+'/robots.txt');site_entries=[]
try:
    assert sitemap_response['status']==robot_response['status']==200
    root=ET.fromstring(sitemap_response['body']);site_entries=[n.find('{*}loc').text for n in root]
    incomplete={m['slug'] for m in json.loads((ROOT/'data/cars.json').read_text())['models'] if not m['indexable']}
    expected={BASE+p for p in pages if p.rstrip('/').split('/')[-1] not in incomplete and not (catalog.get(p.rstrip('/').split('/')[-1],{}).get('status') in ('withdrawn','redirect'))}
    assert len(site_entries)==len(set(site_entries))==len(expected) and set(site_entries)==expected
    image_nodes=root.findall('.//{http://www.google.com/schemas/sitemap-image/1.1}loc')
    assert len(image_nodes)==sum(p['status']=='verified' for p in catalog.values()) and {i.text for i in image_nodes}=={BASE+p['src'] for p in catalog.values() if p['status']=='verified'}
    robot_text=robot_response['body'].decode('utf-8');robot=RobotFileParser();robot.parse(robot_text.splitlines())
    assert BASE+'/sitemap.xml' in robot_text
    assert all(robot.can_fetch('Googlebot',u) for u in expected|assets)
except Exception as e:problem('Sitemap/robots mismatch: '+str(e),BASE+'/sitemap.xml')
variants=[fetch(u) for u in ['http://evberegn.dk/','http://www.evberegn.dk/','https://evberegn.dk/']]
for r in variants:
    if r['status']!=200 or r.get('final')!=BASE+'/':warnings.append({'message':'Domain/protocol redirect needs review','url':r['url'],'status':r['status'],'final':r.get('final')})
missing=fetch(BASE+'/teknisk-kontrol-side-der-ikke-findes-20261025/')
if missing['status']!=404:problem('Unknown URL should return 404, got '+str(missing['status']),missing['url'])
fuel_response=fetch(BASE+'/data/fuel-prices.json');fuel={}
try:
    assert fuel_response['status']==200
    fuel=json.loads(fuel_response['body']);assert 0<float(fuel['petrol95'])<100 and 0<float(fuel['diesel'])<100
    date=datetime.fromisoformat(fuel['updated']);age=(datetime.now(timezone.utc)-date).total_seconds()/3600
    if age>30:warnings.append({'message':'Fuel file older than 30 hours','age_hours':round(age,1)})
except Exception as e:problem('Fuel JSON unavailable/invalid: '+str(e),fuel_response['url'])
record={'checked_at':datetime.now(timezone.utc).isoformat(),'html_pages':len(pages),'expected_html_pages':len(paths),'sitemap_urls':len(site_entries),'local_assets':len(assets),'link_occurrences':sum(len(p.links) for p in pages.values()),'internal_links':sum(urlsplit(urljoin(BASE+path,target)).netloc in ('www.evberegn.dk','evberegn.dk') and urlsplit(urljoin(BASE+path,target)).scheme in ('http','https') for path,page in pages.items() for target in page.links),'unique_external_links':len(external),'image_metadata_objects':sum(p['status']=='verified' for p in catalog.values()),'fuel':fuel,'missing_url_status':missing['status'],'errors':errors,'warnings':warnings,'responses':[{k:v for k,v in r.items() if k!='body'} for r in responses+asset_responses],'external_links':sorted(external)}
(OUT/'full-public-crawl.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
print('FULL_PUBLIC_CRAWL_RESULT '+json.dumps({k:v for k,v in record.items() if k not in ('responses','external_links')},ensure_ascii=False),flush=True)
assert not errors,errors[:10]
