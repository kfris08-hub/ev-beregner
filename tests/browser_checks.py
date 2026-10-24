"""Browser regression checks with controlled local responses, not live market data."""
import asyncio,json,mimetypes,os
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.async_api import async_playwright

ROOT=Path(__file__).parents[1]
BASE='https://www.evberegn.dk'
async def main():
 results=[]
 async with async_playwright() as pw:
  executable=os.environ.get('CHROME_PATH','/usr/bin/google-chrome')
  browser=await pw.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for label,width,height in [('mobile',390,844),('desktop',1280,900)]:
   context=await browser.new_context(viewport={'width':width,'height':height})
   page=await context.new_page();errors=[];state={'price':0}
   page.on('pageerror',lambda e:errors.append(str(e)))
   async def route_request(route):
    url=urlsplit(route.request.url)
    if url.netloc=='www.evberegn.dk':
     name=unquote(url.path).lstrip('/')
     if not name or name.endswith('/'):name+='index.html'
     file=ROOT/name
     await route.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'text/plain')
    elif url.netloc=='elpriser.org':await route.fulfill(status=200,json={'price':state['price']})
    elif 'wikimedia.org' in url.netloc:await route.fulfill(status=200,json={'query':{'pages':{}}})
    else:await route.abort()
   await context.route('**/*',route_request)
   await page.goto(BASE+'/elbil/tesla-model-y-standard-rwd/')
   await page.wait_for_function('document.getElementById("ep").value === "0.00"')
   assert await page.locator('#r100').inner_text()=='0,00 kr.'
   await page.locator('#ep').fill('0')
   assert await page.locator('#r100').inner_text()=='0,00 kr.'
   await page.screenshot(path=str(ROOT/'test-results'/f'model-{label}.png'),full_page=True)
   await page.get_by_role('link',name='ÅBN ALLE BEREGNERE').click()
   await page.wait_for_function('selectedCar !== null')
   assert await page.evaluate('selectedCar[1]')=='Model Y Standard RWD'
   assert await page.locator('a.calc-card').count()==20
   for number in range(1,21):
    await page.evaluate('(n)=>{openCalculator(n);calculate()}',number)
    answer=await page.locator('#answer').inner_text()
    assert answer and not any(x in answer for x in ['NaN','Infinity','∞']),(number,answer)
   await page.evaluate('openCalculator(8)')
   await page.locator('#calc_power').fill('0');await page.evaluate('calculate()')
   assert 'større end 0' in await page.locator('#answer').inner_text()
   await page.goto(BASE+'/?car=tesla-model-y-standard-rwd#beregner-2')
   await page.wait_for_function('currentCalculator === 2')
   await page.locator('#calc_electricPrice').fill('0');await page.evaluate('calculate()')
   assert '0.00 kr.' in await page.locator('#answer').inner_text()
   await page.screenshot(path=str(ROOT/'test-results'/f'calculator-{label}.png'),full_page=True)
   await page.goto(BASE+'/')
   await page.wait_for_function('typeof calculators !== "undefined"')
   await page.screenshot(path=str(ROOT/'test-results'/f'home-{label}.png'),full_page=True)
   overflow=await page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
   assert not overflow, f'{label}: horizontal overflow'
   assert not errors, errors
   results.append({'viewport':label,'calculators':20,'zeroPrice':'pass','carTransfer':'pass','deepLink':'pass','zeroDivisor':'pass','horizontalOverflow':False,'pageErrors':errors})
   await context.close()
  await browser.close()
 (ROOT/'test-results/browser-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':
 (ROOT/'test-results').mkdir(exist_ok=True)
 asyncio.run(main())
