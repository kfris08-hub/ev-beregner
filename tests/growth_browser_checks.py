"""Real UI tests for shareable results, discovery, diesel prices and a clear first screen."""
import asyncio,json,mimetypes,os
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,unquote,parse_qs
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';PUBLIC=os.environ.get('GROWTH_PUBLIC')=='1'
async def main():
 results=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for width in [320,390,1280]:
   context=await browser.new_context(viewport={'width':width,'height':900})
   async def route(r):
    u=urlsplit(r.request.url)
    if u.netloc=='www.evberegn.dk' and u.path=='/data/fuel-prices.json':
     now=datetime.now(timezone.utc).isoformat();await r.fulfill(status=200,json={'price_type':'pump_average','currency':'DKK','unit':'DKK/l','source_chain':'OK','checked_at':now,'updated':now,'petrol95':14.11,'diesel':19.77,'coverage':{'petrol95':689,'diesel':690}});return
    if u.netloc=='www.evberegn.dk':
     if PUBLIC:await r.continue_();return
     name=unquote(u.path).lstrip('/');name+='index.html' if not name or name.endswith('/') else '';f=ROOT/name
     await r.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
    elif u.netloc=='elpriser.org':await r.fulfill(status=200,json={'price':2.5})
    else:await r.abort()
   await context.route('**/*',route)
   await context.add_init_script("Object.defineProperty(navigator,'share',{value:undefined,configurable:true});Object.defineProperty(navigator,'clipboard',{value:{writeText:async value=>{window.__copied=value;}},configurable:true});window.print=()=>{window.__printed=true;};")
   page=await context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto(BASE+'/',wait_until='load')
   assert await page.locator('#calculatorCards .calc-card').count()==20
   assert await page.locator('#quickTools a').count()==4
   positions=await page.evaluate('({hero:document.querySelector(".hero").getBoundingClientRect().bottom,ad:document.getElementById("homeAd").getBoundingClientRect().top})');assert positions['ad']>positions['hero']
   await page.goto(BASE+'/beregnere/#bil=tesla-model-y-standard-rwd',wait_until='load')
   assert await page.locator('[data-tool]').count()==20
   await page.locator('#toolSearch').fill('diesel');assert await page.locator('[data-tool]:visible').count()>0
   await page.locator('#toolSearch').fill('ingen-beregner-med-dette-navn');await expect(page.locator('#noTools')).to_be_visible()
   await page.locator('#toolSearch').fill('')
   root_link=page.locator('a[data-tool][href*="#beregner-5"]')
   assert parse_qs(urlsplit(await root_link.get_attribute('href')).query)['car']==['tesla-model-y-standard-rwd']
   await root_link.click();await page.wait_for_function('currentCalculator===5 && selectedCar!==null')
   await page.goto(BASE+'/beregnere/pris-pr-km/#bil=tesla-model-y-standard-rwd',wait_until='load');await page.wait_for_function('!document.getElementById("carSelect").disabled')
   await page.locator('#calc_consumption').fill('22.5');await page.locator('#calc_electricPrice').fill('3.1');await page.locator('#priceArea').select_option('DK2')
   expected=await page.locator('#answer').inner_text();await page.locator('#shareCalculation').click()
   await page.wait_for_function('typeof window.__copied==="string"');shared=await page.evaluate('window.__copied')
   assert not urlsplit(shared).query and '#s=1' in shared
   await page.goto(shared,wait_until='load');await page.wait_for_function('!document.getElementById("carSelect").disabled')
   assert await page.locator('#answer').inner_text()==expected
   assert await page.locator('#calc_consumption').input_value()=='22.5' and await page.locator('#calc_electricPrice').input_value()=='3.1'
   assert await page.locator('#carSelect').input_value()=='tesla-model-y-standard-rwd'
   await page.locator('#printCalculation').click();assert await page.evaluate('window.__printed===true')
   await page.goto(BASE+'/beregnere/pris-pr-km/#s=1&k=2&consumption=%3Csvg%3E&electricPrice=2',wait_until='load')
   await expect(page.locator('#shareStatus')).to_contain_text('kunne ikke')
   await page.goto(BASE+'/beregnere/elbil-vs-diesel/',wait_until='load');await page.locator('#loadPrices').click();await page.wait_for_function('!document.getElementById("loadPrices").disabled')
   assert await page.locator('#calc_fuelPrice').input_value()=='19.77';assert 'Diesel' in await page.locator('#priceStatus').inner_text()
   await page.goto(BASE+'/beregnere/samlet-biloekonomi/#bil=opel-rocks-electric-rocks-electric',wait_until='load');await page.wait_for_function('!document.getElementById("carSelect").disabled')
   assert 'katalogpris' in (await page.locator('#modelNote').inner_text()).lower()
   assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
   assert not errors,errors
   results.append({'width':width,'overview_and_old_20_calculators':'passed','same_shared_values_after_car_load':'passed','malformed_link':'passed','diesel_not_petrol':'passed','catalogue_price_label':'passed','print_action':'passed'})
   await context.close()
  # Tool overview and methods stay usable when JavaScript is off.
  context=await browser.new_context(java_script_enabled=False);await context.route('**/*',route);page=await context.new_page();await page.goto(BASE+'/beregnere/')
  assert await page.locator('[data-tool]').count()==20 and not await page.locator('#toolSearch').is_visible()
  await context.close();await browser.close()
 out=ROOT/'test-results';out.mkdir(exist_ok=True);(out/'growth-browser.json').write_text(json.dumps(results,indent=2))
 print('GROWTH_BROWSER_RESULT '+json.dumps({'origin':'public' if PUBLIC else 'source','cases':results,'no_javascript_overview':'passed','errors':[]}))
if __name__=='__main__':asyncio.run(main())

