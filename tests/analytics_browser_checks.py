"""Verify optional traffic measurement without ever sending a real page view."""
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import asyncio, base64, json, mimetypes
from playwright.async_api import async_playwright

ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';KEY='evberegn_stats_choice_v1'
HASH='b88f7c584949360baea27864aa2e317e'
async def main():
    checks=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-dev-shm-usage'])
        async def session(init='', blocked=False, webdriver=False):
            context=await browser.new_context(viewport={'width':390,'height':844})
            if not webdriver:await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false})")
            if init:await context.add_init_script(init)
            events=[]
            async def route_request(route):
                u=urlparse(route.request.url)
                if u.netloc=='tracker.metricool.com':
                    events.append({'url':route.request.url,'headers':route.request.headers})
                    if blocked:await route.abort()
                    else:await route.fulfill(status=200,content_type='image/gif',body=base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'))
                elif u.netloc=='www.evberegn.dk':
                    name=unquote(u.path).lstrip('/')
                    if not name or name.endswith('/'):name+='index.html'
                    file=ROOT/name
                    await route.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'text/plain')
                else:await route.abort()
            await context.route('**/*',route_request)
            page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            return context,page,events,errors

        context,page,events,errors=await session()
        await page.goto(BASE+'/',wait_until='networkidle')
        assert await page.locator('#evStatsNotice').is_visible() and not events
        assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
        await page.locator('#evStatsDeny').click()
        await page.goto(BASE+'/elbil/jaecoo-j5-ev-comfort/',wait_until='networkidle')
        assert not events and not await page.locator('#evStatsNotice').count()
        assert await page.locator('#evStatsSettings').is_visible() and not errors
        checks.append('No tracking before consent; rejection persists across pages; mobile has no overflow')
        await context.close()

        context,page,events,errors=await session()
        original=BASE+'/beregnere/pris-pr-km/?utm_source=facebook&utm_campaign=bilvalg&email=private@example.test#private-calculation=123456'
        await page.goto(original,referer='https://www.facebook.com/private-profile?secret=123',wait_until='networkidle')
        await page.locator('#evStatsAllow').click();await page.wait_for_timeout(100)
        assert len(events)==1,events
        q=parse_qs(urlparse(events[0]['url']).query)
        assert q['hash']==[HASH] and q['ref']==['https://www.facebook.com/'],q
        assert q['u']==[BASE+'/beregnere/pris-pr-km/?utm_source=facebook&utm_campaign=bilvalg'],q
        assert not any(k in events[0]['headers'] for k in ['cookie','referer']),events
        assert 'private@example.test' in page.url and '#private-calculation=123456' in page.url
        script=(ROOT/'assets/website-stats.js').read_text();await page.evaluate(script)
        await page.locator('#evStatsSettings').click();await page.locator('#evStatsAllow').click()
        assert len(events)==1,'Repeated script/acceptance must not count twice'
        await page.goto(BASE+'/elbil/jaecoo-j5-ev-comfort/',wait_until='networkidle')
        assert len(events)==2 and not await page.locator('#evStatsNotice').count()
        await page.locator('#evStatsSettings').click();await page.locator('#evStatsDeny').click()
        await page.reload(wait_until='networkidle');assert len(events)==2 and not errors
        checks.append('Consent records once per page; Facebook source/UTM retained; private URL values and request credentials excluded; revocation stops future events')
        await context.close()

        for flag,init in [('DNT',"Object.defineProperty(navigator,'doNotTrack',{get:()=> '1'})"),('GPC',"Object.defineProperty(navigator,'globalPrivacyControl',{get:()=>true})")]:
            context,page,events,errors=await session(init)
            await page.goto(BASE+'/',wait_until='networkidle')
            assert not events and not await page.locator('#evStatsNotice').count() and not errors
            checks.append(flag+' privacy preference respected');await context.close()
        context,page,events,errors=await session(webdriver=True)
        await page.goto(BASE+'/',wait_until='networkidle')
        assert not events and not await page.locator('#evStatsNotice').count()
        checks.append('Automated browser tests excluded from statistics');await context.close()

        denied="Object.defineProperty(window,'localStorage',{get:()=>{throw new Error('blocked')}})"
        context,page,events,errors=await session(denied,blocked=True)
        await page.goto(BASE+'/beregnere/pris-pr-km/',wait_until='networkidle')
        await page.locator('#evStatsAllow').click()
        await page.locator('#calc_consumption').fill('16');await page.locator('#calc_electricPrice').fill('2')
        await page.locator('#calculateButton').click()
        assert '0,32' in await page.locator('#answer').inner_text() and not errors,errors
        checks.append('Blocked storage and tracker do not break calculations')
        await context.close();await browser.close()
    (ROOT/'test-results').mkdir(exist_ok=True)
    (ROOT/'test-results/website-stats.json').write_text(json.dumps({'checks':checks,'real_tracking_events':0},ensure_ascii=False,indent=2))
    print('WEBSITE_STATS_RESULT '+json.dumps({'checks_passed':len(checks),'real_tracking_events':0},ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
