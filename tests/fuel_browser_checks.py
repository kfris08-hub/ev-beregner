"""Fuel source, freshness and personal prices across all three page types."""
import asyncio,json,mimetypes,os,re
from pathlib import Path
from urllib.parse import unquote,urlsplit
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';PUBLIC=os.environ.get('FUEL_PUBLIC')=='1'
async def main():
 data=json.loads((ROOT/'data/fuel-prices.json').read_text());results=[]
 if PUBLIC:
  import time,urllib.request
  with urllib.request.urlopen(BASE+'/data/fuel-prices.json?kontrol='+str(time.time_ns()),timeout=15) as response:data=json.load(response)
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for width in [390,1280]:
   context=await browser.new_context(viewport={'width':width,'height':844});stale=False
   async def route(r):
    u=urlsplit(r.request.url)
    if u.netloc=='www.evberegn.dk':
     if u.path=='/data/fuel-prices.json' and stale:
      old={**data,'checked_at':'2020-01-01T00:00:00Z','updated':'2020-01-01T00:00:00Z'};await r.fulfill(status=200,json=old);return
     if PUBLIC:await r.continue_();return
     name=unquote(u.path).lstrip('/');name=name+'index.html' if not name or name.endswith('/') else name;f=ROOT/name
     await r.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
    elif u.netloc=='elpriser.org':await r.fulfill(status=200,json={'price':2.5})
    else:await r.abort()
   await context.route('**/*',route);page=await context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto(BASE+'/',wait_until='load');await page.wait_for_function('energyState.fuel==="ready"')
   assert float((await page.locator('#petrolPriceDisplay').inner_text()).split()[0].replace(',','.'))==data['petrol95']
   assert 'OK-stationer' in await page.locator('#petrolDate').inner_text()
   await page.goto(BASE+'/?car=tesla-model-y-standard-rwd#beregner-3',wait_until='load');await page.wait_for_function('energyState.fuel==="ready"');await page.evaluate('openCalculator(3,true)')
   assert float(await page.locator('#calc_fuelPrice').input_value())==data['petrol95']
   await page.locator('#calc_fuelPrice').fill('0');await page.locator('#calculator button.calculate').click()
   assert not re.search(r'NaN|Infinity|undefined',await page.locator('#answer').inner_text())
   await page.goto(BASE+'/elbil/tesla-model-y-standard-rwd/',wait_until='load');await expect(page.locator('#liveNote')).to_contain_text('OK-pumpepriser')
   assert await page.locator('#petPrice').inner_text()==f"{data['petrol95']:.2f}".replace('.',',')+' kr./l'
   assert await page.locator('#dieselPrice').inner_text()==f"{data['diesel']:.2f}".replace('.',',')+' kr./l'
   await page.goto(BASE+'/beregnere/elbil-vs-benzin/',wait_until='load');await page.locator('#loadPrices').click();await expect(page.locator('#priceStatus')).to_contain_text('OK-stationer')
   assert float(await page.locator('#calc_fuelPrice').input_value())==data['petrol95']
   await page.locator('#calc_fuelPrice').fill('14.55');await page.locator('#calculateButton').click();assert float(await page.locator('#calc_fuelPrice').input_value())==14.55
   assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
   stale=True;await page.goto(BASE+'/',wait_until='load');await page.wait_for_function('energyState.fuel==="fallback"')
   assert 'Eksempelpris' in await page.locator('#petrolDate').inner_text()
   assert '*' in await page.locator('#petrolPriceDisplay').inner_text()
   assert not errors,errors
   results.append({'width':width,'home_model_guide_same_pump_prices':'passed','manual_zero_and_custom_price':'passed','stale_snapshot_not_presented_as_current':'passed'})
   await context.close()
  await browser.close()
 out=ROOT/'test-results';out.mkdir(exist_ok=True);(out/'fuel-browser.json').write_text(json.dumps(results,indent=2));print('FUEL_BROWSER_RESULT '+json.dumps({'origin':'public' if PUBLIC else 'source','cases':results,'all_checks':'passed'}))
if __name__=='__main__':asyncio.run(main())
