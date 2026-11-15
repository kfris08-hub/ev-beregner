"""Fresh, analytics-excluded source captures for the 16–17 November buffer."""
from pathlib import Path
import json,shutil,urllib.request
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
BASE='https://www.evberegn.dk'
SLUG='hyundai-ioniq-5-standard-range-rwd-essential'
MANIFEST=json.loads((Path.cwd()/'data/model-photos.json').read_text())['models'][SLUG]
assert MANIFEST['status']=='verified' and MANIFEST['reviewed'] and MANIFEST['license']=='CC0'
PROOF={'checked_utc':'2026-11-15','source':BASE,'model':SLUG,'rights':{k:MANIFEST[k] for k in ['author','license','license_url','source']},'captures':[],'days':{},'blocked_requests':0,'new_heygen_jobs':0,'paid_services':0,'website_changed':False}

def utm(url,date,kind):
    s=urlsplit(url);query=dict(parse_qsl(s.query))
    query.update(utm_source='facebook',utm_medium='organic_social',utm_campaign='daglig_202611',utm_content=date.replace('-','')+'_'+kind.lower())
    return urlunsplit((s.scheme,s.netloc,s.path,urlencode(query),s.fragment))

with sync_playwright() as p:
    executable=shutil.which('google-chrome') or shutil.which('chromium')
    browser=p.chromium.launch(executable_path=executable,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':420,'height':748},device_scale_factor=2,is_mobile=True,has_touch=True)
    # DNT and explicit tracker blocking are capture-only. No consent or tracking
    # action is sent; these visits are not claimed as organic audience activity.
    page.add_init_script("Object.defineProperty(navigator,'doNotTrack',{get:()=> '1'});")
    def route(req):
        parsed=urlsplit(req.request.url)
        if parsed.hostname not in ('www.evberegn.dk','evberegn.dk') or parsed.path.endswith('/website-stats.js'):
            PROOF['blocked_requests']+=1;req.abort()
        else:req.continue_()
    page.route('**/*',route)
    def visit(url):
        r=page.goto(url,wait_until='networkidle',timeout=30000)
        assert r and r.status==200,(url,r.status if r else None)
        assert page.evaluate('navigator.webdriver') is True
        return r.status
    def shot(name,selector):
        page.locator(selector).evaluate('(e)=>window.scrollTo(0,e.getBoundingClientRect().top+window.scrollY-145)')
        page.screenshot(path=str(OUT/(name+'.png')),style='iframe { visibility: hidden !important; }')
        PROOF['captures'].append({'file':name+'.png','url':page.url,'title':page.title(),'http':200})

    visit(BASE+'/elbil/'+SLUG+'/')
    page.locator('#carPhoto').wait_for(state='visible')
    assert page.locator('#carPhoto').evaluate('(i)=>i.complete&&i.naturalWidth>0')
    credit=page.locator('#photoCredit').inner_text()
    assert 'TTTNIS' in credit and 'CC0' in credit
    assert 'Nedskaleret' not in credit and 'konverteret' not in credit
    PROOF['photo_credit']=credit
    hero=page.locator('.hero').bounding_box();end=page.locator('#photoCredit').bounding_box()
    page.locator('.hero').screenshot(path=str(OUT/'model-hero.png'))
    # Keep the actual heading, photo and complete credit. Exclude catalogue price.
    from PIL import Image
    image=Image.open(OUT/'model-hero.png').convert('RGB')
    bottom=round((end['y']+end['height']-hero['y']+8)*2)
    image.crop((0,0,image.width,min(bottom,image.height))).save(OUT/'model.png')
    PROOF['captures'].append({'file':'model.png','url':page.url,'http':200,'crop':'Ends after full source credit, before catalogue price'})

    specs=[('2026-11-16','pris-pr-km',2,{'consumption':16,'electricPrice':2},'32 kr.'),
           ('2026-11-17','koeretur',6,{'km':75,'consumption':18,'electricPrice':2.5},'33,75 kr.')]
    for date,path,identifier,inputs,expected in specs:
        canonical=BASE+'/beregnere/'+path+'/'
        visit(canonical+'#bil='+SLUG)
        page.wait_for_function('!document.querySelector("#carSelect").disabled')
        assert page.locator('#carSelect').input_value()==SLUG
        for key,value in inputs.items():page.locator('#calc_'+key).fill(str(value))
        page.locator('#calculateButton').click()
        answer=page.locator('#answer').inner_text()
        assert expected in answer,(date,answer)
        actual=page.evaluate('(p)=>EVCalculators.compute(p.id,p.inputs)',{'id':identifier,'inputs':inputs})
        if identifier==2:assert abs(actual['perKm']-.32)<1e-9 and actual['per100']==32
        else:assert abs(actual['energy']-13.5)<1e-9 and abs(actual['total']-33.75)<1e-9
        shot(date+'-inputs','#carSelect');shot(date+'-result','#answer')
        share=page.evaluate('(p)=>EVCalculationShare.encode(document.querySelector("link[rel=canonical]").href,p.id,Object.keys(p.inputs),p.inputs,p.slug,"DK1")',{'id':identifier,'inputs':inputs,'slug':SLUG})
        destination=utm(share,date,'reel')
        visit(destination)
        page.wait_for_function('!document.querySelector("#carSelect").disabled')
        assert page.locator('#carSelect').input_value()==SLUG
        for key,value in inputs.items():assert abs(float(page.locator('#calc_'+key).input_value())-value)<1e-9
        assert expected in page.locator('#answer').inner_text()
        PROOF['days'][date]={'calculator':path,'calculator_id':identifier,'inputs':inputs,'computed':actual,'answer':answer,'share_url':share,'links':{kind:utm(share,date,kind) for kind in ['post','reel','story']},'shared_link_reload':'PASS','model_selection_retained':True}
    browser.close()

# Existing, already-scheduled POST is supplied for reference, never re-uploaded.
with urllib.request.urlopen('https://static.metricool.com/planner/202611/8064733-file-1436563993951226378.png',timeout=20) as r:
    (OUT/'2026-11-16-post-ALLEREDE-PLANLAGT.png').write_bytes(r.read())
with urllib.request.urlopen('https://static.metricool.com/planner/202611/8064733-file-1906549249988751242.mp4',timeout=20) as r:
    (OUT/'2026-11-15-original-QUEUED.mp4').write_bytes(r.read())
PROOF['real_analytics_or_ad_events']=0
(OUT/'PROOF.json').write_text(json.dumps(PROOF,ensure_ascii=False,indent=2))
print(json.dumps({'captures':len(PROOF['captures']),'days':list(PROOF['days']),'links':'PASS','live_results':'PASS','third_party_blocking':True}))
