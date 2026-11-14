"""One release check of public copy, image credits and the reported model page."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
import json, re, time
from playwright.sync_api import sync_playwright

ROOT=Path.cwd();BASE='https://www.evberegn.dk';OUT=ROOT/'test-results'
OUT.mkdir(exist_ok=True)
PHOTOS=json.loads((ROOT/'data/model-photos.json').read_text())['models']
FORBIDDEN=re.compile(r'nedskaleret|konverteret til WebP|ingen beskæring|kontrolleret modelbillede',re.I)
class Page(HTMLParser):
    def __init__(self,html):
        super().__init__();self.skip=0;self.text=[];self.links=[];self.feed(html)
    def handle_starttag(self,tag,attrs):
        if tag in ('head','script','style'):self.skip+=1
        if tag=='a':self.links.append(dict(attrs).get('href',''))
    def handle_endtag(self,tag):
        if tag in ('head','script','style') and self.skip:self.skip-=1
    def handle_data(self,text):
        if not self.skip:self.text.append(text)

def check(path):
    relative=path.parent.relative_to(ROOT).as_posix()
    url=BASE+('/' if relative=='.' else '/'+relative+'/')
    request=Request(url+'?copycheck=20261114',headers={'User-Agent':'EVBeregn-copy-release-check/1.0','Cache-Control':'no-cache'})
    with urlopen(request,timeout=25) as response:
        assert response.status==200,(url,response.status)
        html=response.read().decode('utf-8')
    page=Page(html);visible=' '.join(page.text)
    assert not FORBIDDEN.search(visible),url
    match=re.fullmatch(r'elbil/([^/]+)',relative)
    if match:
        photo=PHOTOS[match[1]]
        if photo['status']=='verified':
            assert photo['author'] in visible and photo['license'] in visible,url
            assert photo['source'] in page.links and photo['license_url'] in page.links,url
            assert photo['src'] in html,url
        elif photo['status']=='missing':
            assert 'Der er endnu ikke et billede af denne model.' in visible,url
    return {'url':url,'status':200}

paths=sorted(p for p in ROOT.rglob('index.html') if '.git' not in p.parts and 'templates' not in p.parts)
with ThreadPoolExecutor(max_workers=6) as pool:
    results=list(pool.map(check,paths))

screens=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for width,height in [(390,844),(1280,900)]:
        page=browser.new_page(viewport={'width':width,'height':height})
        page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(BASE+'/') else route.abort())
        page.goto(BASE+'/elbil/jaecoo-j5-ev-comfort/?copycheck=20261114',wait_until='networkidle')
        assert page.locator('#carPhoto').evaluate('(i)=>i.complete && i.naturalWidth>0')
        credit=page.locator('#photoCredit').inner_text()
        assert not FORBIDDEN.search(credit)
        assert 'iMoD Official' in credit and 'CC BY 3.0' in credit
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
        filename=f'jaecoo-copy-{width}.png'
        page.screenshot(path=str(OUT/filename),full_page=True,style='iframe {visibility:hidden!important}')
        screens.append(filename);page.close()
    browser.close()
summary={'html_pages_checked':len(results),'technical_photo_notes':0,'reviewed_photos':sum(p['status']=='verified' for p in PHOTOS.values()),'missing_photo_messages':sum(p['status']=='missing' for p in PHOTOS.values()),'image_rights_links':'preserved','jaecoo_mobile_and_desktop':'passed','screenshots':screens}
(OUT/'copy-release.json').write_text(json.dumps({'summary':summary,'pages':results},ensure_ascii=False,indent=2))
print('COPY_RELEASE_RESULT '+json.dumps(summary,ensure_ascii=False))
