"""The new source labels and photo reuse preserve data, calculators and mobile layout."""
import asyncio,json,os,mimetypes
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';PUBLIC=os.environ.get('REPAIRS_PUBLIC')=='1'
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for width in [320,390,1280]:
   context=await browser.new_context(viewport={'width':width,'height':844})
   async def route(r):
    u=urlsplit(r.request.url)
    if u.netloc=='www.evberegn.dk':
     if PUBLIC:await r.continue_();return
     name=unquote(u.path).lstrip('/');name+='index.html' if not name or name.endswith('/') else '';f=ROOT/name
     await r.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
    elif u.netloc=='elpriser.org':await r.fulfill(status=200,json={'price':2.5})
    else:await r.abort()
   await context.route('**/*',route);page=await context.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto(BASE+'/?car=opel-rocks-electric-rocks-electric',wait_until='load')
   await expect(page.locator('#selectedCar')).to_contain_text('katalogpris')
   await page.evaluate('openCalculator(16,true)');await expect(page.locator('#dataBadge')).to_contain_text('katalogpris')
   await page.locator('#calc_price').fill('100000');await page.locator('#calculator button.calculate').click();assert 'NaN' not in await page.locator('#answer').inner_text()
   await page.goto(BASE+'/elbil/opel-rocks-electric-rocks-electric/',wait_until='load');await expect(page.locator('.stat').first).to_contain_text('Katalogpris')
   await page.goto(BASE+'/elbil/citroen-e-c3-you/',wait_until='load');assert 'Katalogpris' not in await page.locator('.stat').first.inner_text()
   await page.goto(BASE+'/elbil/kia-e-soul-64-kwh-2019/',wait_until='load');await page.wait_for_function('document.getElementById("carPhoto").naturalWidth>=700')
   assert 'Egen købspris' in await page.locator('.stat').first.inner_text()
   assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
   assert not errors,errors
   await context.close()
  await browser.close()
 print('REPAIRS_BROWSER_RESULT '+json.dumps({'origin':'public' if PUBLIC else 'source','widths':[320,390,1280],'catalogue_price_labels_and_own_price':'passed','verified_price_label':'passed','historical_photo_and_own_purchase_price':'passed','page_errors':[]}))
if __name__=='__main__':asyncio.run(main())
