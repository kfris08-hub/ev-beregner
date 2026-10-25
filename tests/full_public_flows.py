"""Physical UI interactions and real-provider observations; never click advertisements."""
import asyncio,base64,io,json,mimetypes,os,re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';OUT=ROOT/'test-results';OUT.mkdir(exist_ok=True)
PUBLIC=os.environ.get('FLOW_PUBLIC')=='1'
MODELS=json.loads((ROOT/'assets/calculator-cars.json').read_text())['models']
async def main():
    results=[];providers=[];shots=[]
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        for label,width in [('small-mobile',320),('mobile',390),('tablet',768),('desktop',1440)]:
            context=await browser.new_context(viewport={'width':width,'height':900})
            async def route(r):
                host=urlsplit(r.request.url).netloc
                if host=='www.evberegn.dk' and not PUBLIC:
                    name=urlsplit(r.request.url).path.lstrip('/')
                    if not name or name.endswith('/'):name+='index.html'
                    file=ROOT/name
                    await r.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
                elif 'a-ads.com' in host or host=='aads.com':await r.abort()
                elif host=='elpriser.org':await r.fulfill(status=200,json={'price':2.5})
                else:await r.continue_()
            await context.route('**/*',route)
            page=await context.new_page();page.set_default_timeout(6500);page_errors=[];page.on('pageerror',lambda e:page_errors.append(str(e)))
            async def case(name,fn):
                try:await fn();results.append({'viewport':label,'case':name,'result':'passed'})
                except Exception as e:
                    results.append({'viewport':label,'case':name,'result':'failed','error':str(e)[:1200]})
                    await page.screenshot(path=str(OUT/('failure-'+label+'-'+name+'.png')),full_page=True)
            async def filters():
                await page.goto(BASE+'/',wait_until='load')
                await page.locator('#search').fill('Tesla Model Y Standard RWD')
                await expect(page.locator('#carList .car-card')).to_have_count(1)
                await page.locator('#carList .car-card').click()
                await expect(page.locator('#selectedCar')).to_be_visible()
                await expect(page.locator('#selectedModelLink')).to_have_attribute('href','/elbil/tesla-model-y-standard-rwd/')
                await page.locator('#selectedCar .remove-car').click()
                await page.locator('#maxPrice').fill('300.000');await page.locator('#minRange').fill('450')
                expected=[c for c in MODELS if c['price'] is not None and c['price']<=300000 and c['range'] is not None and c['range']>=450]
                await expect(page.locator('#carList .car-card')).to_have_count(len(expected));assert expected
                await page.locator('#sortCars').select_option('rangeDesc')
                actual=await page.locator('#carList .car-name').all_text_contents()
                assert actual==[c['label'] for c in sorted(expected,key=lambda c:-c['range'])],actual
                await page.locator('#search').fill('model-der-ikke-findes-zz')
                await expect(page.locator('#noResults')).to_be_visible()
                await page.get_by_role('button',name='NULSTIL',exact=True).click()
                assert await page.locator('#search').input_value()==''
                await page.get_by_role('button',name='VIS BILER',exact=True).click()
                await expect(page.locator('#carList .car-card')).to_have_count(181)
                assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
            await case('search-filters-sort-select-reset',filters)
            async def cards():
                await page.goto(BASE+'/',wait_until='load')
                for n in (range(1,21) if width==390 else [1,12,20]):
                    await page.locator('a.calc-card[href="#beregner-'+str(n)+'"]').click()
                    await expect(page.locator('#calculator')).to_be_visible()
                    await page.locator('#calculator button.calculate').click()
                    await expect(page.locator('#answer')).to_be_visible()
                    assert not re.search(r'NaN|Infinity|undefined',await page.locator('#answer').inner_text())
                    await page.locator('#calculator button.back').click()
                    await expect(page.locator('#calculator')).not_to_be_visible()
            await case('calculator-cards-calculate-back',cards)
            async def overlay_stacking():
                await page.goto(BASE+'/?car=tesla-model-y-standard-rwd#beregner-2',wait_until='load')
                await expect(page.locator('#calculator')).to_be_visible()
                assert await page.evaluate('Boolean(document.elementFromPoint(innerWidth/2,150)?.closest("#calculator"))'),'Advertisement covers the calculator opened from a direct link'
            await case('calculator-direct-link-overlay',overlay_stacking)
            async def comparison():
                await page.goto(BASE+'/',wait_until='load')
                for slot,label2 in enumerate(['Tesla Model Y Standard RWD','Kia EV3 Standard Range Access','Elveon Motors Min-E Sedan']):
                    await page.locator('#cmpSearch'+str(slot)).fill(label2)
                    await page.locator('#cmpResults'+str(slot)+' .compare-option').first.click()
                await expect(page.locator('#compareOutput table')).to_be_visible()
                assert 'Ikke oplyst' in await page.locator('#compareOutput').inner_text()
                assert await page.locator('#compareOutput td.winner').filter(has_text='Ikke oplyst').count()==0
                assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
                await page.locator('#cmpSelected2 button').click()
                assert await page.locator('#compareOutput .compare-head').count()==2
            await case('three-car-comparison-unknown-remove',comparison)
            async def general_mode():
                await page.goto(BASE+'/?car=tesla-model-y-standard-rwd',wait_until='load')
                await page.wait_for_function('selectedCar!==null')
                await page.locator('#generalModeBtn').click()
                assert await page.evaluate('selectedCar===null'),'General calculation still has the previously selected car'
                await page.locator('a.calc-card[href="#beregner-2"]').click()
                assert 'ingen bil valgt' in await page.locator('#dataBadge').inner_text()
            await case('general-mode-clears-selected-car',general_mode)
            async def remove_url():
                await page.goto(BASE+'/?car=tesla-model-y-standard-rwd',wait_until='load')
                await page.locator('#selectedCar .remove-car').click()
                assert await page.evaluate('selectedCar===null')
                assert not await page.evaluate('new URL(location.href).searchParams.has("car")'),'Removed car is still in the URL and returns on reload'
                await page.reload();assert await page.evaluate('selectedCar===null')
            await case('remove-car-survives-reload',remove_url)
            async def navigation_layout():
                await page.goto(BASE+'/elbil/',wait_until='load')
                assert await page.locator('a[href="/elbil/tesla-model-y-standard-rwd/"]').count()==1
                await page.locator('a[href="/elbil/tesla-model-y-standard-rwd/"]').click()
                await page.locator('a[href="/beregnere/ladepris/#bil=tesla-model-y-standard-rwd"]').click()
                await page.wait_for_function('document.getElementById("carSelect").value==="tesla-model-y-standard-rwd"')
                await page.locator('a[href="/#beregnere"]').first.click()
                await expect(page.locator('#beregnere')).to_be_visible()
                assert await page.locator('a.calc-card').count()==20
                assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
                await page.goto(BASE+'/',wait_until='load');file=OUT/('audit-home-'+label+'.png');await page.screenshot(path=str(file),full_page=True);shots.append((label,file))
            await case('overview-model-calculator-navigation',navigation_layout)
            if page_errors:results.append({'viewport':label,'case':'javascript-errors','result':'failed','error':page_errors})
            await context.close()
        # Observe the real price requests separately from controlled arithmetic tests.
        context=await browser.new_context(viewport={'width':390,'height':844})
        async def live_route(r):
            host=urlsplit(r.request.url).netloc
            if 'a-ads.com' in host or host=='aads.com':await r.abort()
            else:await r.continue_()
        await context.route('**/*',live_route)
        page=await context.new_page();page.set_default_timeout(15000)
        await page.goto(BASE+'/',wait_until='load')
        for region in ['DK1','DK2']:
            await page.locator('#region'+region).click()
            await page.wait_for_function('energyState.electric!=="loading" && energyState.fuel!=="loading"')
            providers.append(await page.evaluate('({page:"homepage",region:energyPrices.region,states:{...energyState},prices:{...energyPrices},message:document.getElementById("energyStatus").textContent})'))
        await page.goto(BASE+'/beregnere/ladepris/',wait_until='load')
        await page.locator('#loadPrices').click();await page.wait_for_function('!document.getElementById("loadPrices").disabled')
        providers.append({'page':'ladepris','price':await page.locator('#calc_electricPrice').input_value(),'status':await page.locator('#priceStatus').inner_text()})
        await context.close();await browser.close()
    (OUT/'full-public-flows.json').write_text(json.dumps({'results':results,'real_price_observations':providers},ensure_ascii=False,indent=2))
    try:
        from PIL import Image,ImageDraw
        sheet=Image.new('RGB',(1200,1000),'#ddd');draw=ImageDraw.Draw(sheet)
        for n,(label,file) in enumerate(shots):
            im=Image.open(file).convert('RGB');im=im.crop((0,0,im.width,min(im.height,im.width*3)));im.thumbnail((290,940));sheet.paste(im,(n*300,35));draw.text((n*300+4,10),label,fill='black')
        raw=io.BytesIO();sheet.save(raw,format='JPEG',quality=70);print('FULL_SITE_SHEET '+base64.b64encode(raw.getvalue()).decode(),flush=True)
    except ImportError:pass
    failed=[r for r in results if r['result']=='failed']
    print('FULL_PUBLIC_FLOWS_RESULT '+json.dumps({'origin':'public' if PUBLIC else 'checked-out source','cases':len(results),'passed':len(results)-len(failed),'failed':failed,'real_price_observations':providers},ensure_ascii=False),flush=True)
    assert not failed,failed
if __name__=='__main__':asyncio.run(main())
