"""Verify deployed traffic measurement; intercept every actual tracking request."""
from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse,parse_qs
import json,re,hashlib,base64
from playwright.sync_api import sync_playwright

ROOT=Path.cwd();BASE='https://www.evberegn.dk';OUT=ROOT/'test-results';OUT.mkdir(exist_ok=True)
HASH='b88f7c584949360baea27864aa2e317e'
def read(path):
    request=Request(BASE+path,headers={'User-Agent':'EVBeregn-stats-release-check/1.0','Cache-Control':'no-cache'})
    with urlopen(request,timeout=25) as r:
        assert r.status==200,(path,r.status)
        return r.read().decode('utf-8')
def check(path):
    relative=path.parent.relative_to(ROOT).as_posix()
    url='/' if relative=='.' else '/'+relative+'/'
    text=read(url+'?statscheck=20261114')
    redirect='http-equiv="refresh"' in path.read_text()
    count=text.count('/assets/website-stats.js?v=20261114-stats1')
    assert count==(0 if redirect else 1),(url,count)
    return url
paths=sorted(p for p in ROOT.rglob('index.html') if '.git' not in p.parts and 'templates' not in p.parts)
with ThreadPoolExecutor(max_workers=6) as pool:pages=list(pool.map(check,paths))
actual=read('/assets/website-stats.js?v=20261114-stats1')
assert HASH in actual and actual==(ROOT/'assets/website-stats.js').read_text()
assert 'id="statistik"' in read('/om/')
events=[];errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844})
    context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false})")
    def handle(route):
        u=urlparse(route.request.url)
        if u.netloc=='tracker.metricool.com':
            events.append(route.request.url)
            route.fulfill(status=200,body=b'')
        elif u.netloc=='www.evberegn.dk':route.continue_()
        else:route.abort()
    context.route('**/*',handle)
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/elbil/jaecoo-j5-ev-comfort/',wait_until='networkidle')
    assert page.locator('#evStatsNotice').is_visible() and not events
    assert page.locator('#carPhoto').evaluate('(i)=>i.complete && i.naturalWidth>0')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    preview=page.screenshot(type='jpeg',quality=75,style='iframe{visibility:hidden!important}')
    (OUT/'stats-mobile.jpg').write_bytes(preview)
    print('STATS_PREVIEW_MOBILE '+base64.b64encode(preview).decode())
    page.locator('#evStatsDeny').click();assert not events
    page.locator('#evStatsSettings').click();page.locator('#evStatsAllow').click()
    page.wait_for_timeout(150);assert len(events)==1
    q=parse_qs(urlparse(events[0]).query);assert q['hash']==[HASH]
    page.set_viewport_size({'width':1280,'height':900})
    page.goto(BASE+'/beregnere/pris-pr-km/?utm_source=facebook&utm_campaign=release_test&private=secret#private-value=123',wait_until='networkidle')
    assert not page.locator('#evStatsNotice').count() and len(events)==2
    q=parse_qs(urlparse(events[-1]).query)
    assert q['u']==[BASE+'/beregnere/pris-pr-km/?utm_source=facebook&utm_campaign=release_test']
    page.locator('#calc_consumption').fill('16');page.locator('#calc_electricPrice').fill('2');page.locator('#calculateButton').click()
    assert '0,32' in page.locator('#answer').inner_text() and not errors,errors
    page.screenshot(path=str(OUT/'stats-desktop.png'),full_page=False,style='iframe{visibility:hidden!important}')
    context.close();browser.close()
summary={'public_html_pages':len(pages),'single_loader_per_normal_page':True,'redirect_excluded':True,'asset_sha256':hashlib.sha256(actual.encode()).hexdigest(),'consent_and_rejection':'passed','facebook_utm':'passed','private_values_excluded':True,'mobile_and_desktop':'passed','calculator_result':'0,32 kr.','real_tracking_events':0,'intercepted_test_events':len(events)}
(OUT/'stats-release.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print('STATS_RELEASE_RESULT '+json.dumps(summary,ensure_ascii=False))
