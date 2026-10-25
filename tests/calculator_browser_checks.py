"""Exercise the real five calculator pages on mobile/desktop, also without JS.
CALCULATOR_PUBLIC=1 uses public HTML/assets instead of source interception.
"""
import asyncio,base64,io,json,mimetypes,os
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.async_api import async_playwright
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';PUBLIC=os.environ.get('CALCULATOR_PUBLIC')=='1'
PAGES=json.loads((ROOT/'data/calculator-pages.json').read_text());RESULTS=ROOT/'test-results';RESULTS.mkdir(exist_ok=True)
EXPECTED={'ladepris':'132 kr.','elbil-vs-benzin':'13.800','opladningstid':'3,27','leasing-vs-koeb':'158.964','samlet-biloekonomi':'225.000'}
async def main():
 report=[];panels=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for label,width,height in [('mobile',390,844),('desktop',1280,900)]:
   for javascript in [False,True]:
    context=await browser.new_context(viewport={'width':width,'height':height},java_script_enabled=javascript)
    api_requests=[]
    async def handle(route):
     url=urlsplit(route.request.url)
     if url.netloc=='www.evberegn.dk':
      if PUBLIC:await route.continue_();return
      name=unquote(url.path).lstrip('/')
      if not name or name.endswith('/'):name+='index.html'
      file=ROOT/name
      await route.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
     elif url.netloc=='elpriser.org':api_requests.append(route.request.url);await route.fulfill(status=200,json={'price':2.5})
     else:await route.abort()
    await context.route('**/*',handle)
    page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for config in PAGES:
     slug=config['slug'];response=await page.goto(BASE+'/beregnere/'+slug+'/?kontrol=calc-pages-20261024',wait_until='load')
     assert response.status==200,(slug,response.status)
     assert await page.locator('h1').count()==1
     assert EXPECTED[slug] in await page.locator('#answer').inner_text(),(slug,await page.locator('#answer').inner_text())
     assert await page.locator('#answer').is_visible()
     assert await page.locator('link[rel=canonical]').get_attribute('href')==BASE+'/beregnere/'+slug+'/'
     assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),(slug,label)
     # Additional explanations are available on demand, including without JavaScript.
     helpbox=page.locator('details.field-explanations')
     assert await helpbox.get_attribute('open') is None
     await helpbox.locator('summary').click()
     assert await helpbox.locator('dd').first.is_visible()
     await helpbox.locator('summary').click()
     explanation=page.locator('details.calculator-explanation')
     assert await explanation.get_attribute('open') is None
     await explanation.locator('summary').click()
     assert await explanation.locator('.guide h2').first.is_visible()
     await explanation.locator('summary').click()
     if not javascript:
      assert await page.locator('#calculateButton').is_disabled()
      assert await page.locator('noscript').inner_text()
     else:
      await page.wait_for_function('!document.getElementById("carSelect").disabled')
      assert await page.locator('#carSelect option').count()==182
      assert not api_requests,'Initial example must not silently become a live price'
      if slug=='ladepris':
       await page.locator('#calc_from').fill('20');await page.locator('#calc_to').fill('80');await page.locator('#calc_electricPrice').fill('2.5')
       assert '99 kr.' in await page.locator('#answer').inner_text()
       await page.locator('#calc_electricPrice').fill('0');assert '0 kr.' in await page.locator('#answer').inner_text()
       await page.locator('#calc_electricPrice').fill('-0.25');assert '-9,9 kr.' in await page.locator('#answer').inner_text()
       await page.locator('#calc_to').fill('10');assert await page.locator('#calc_to').get_attribute('aria-invalid')=='true'
      elif slug=='elbil-vs-benzin':
       await page.locator('#calc_electricPrice').fill('8');assert '-4.800' in await page.locator('#answer').inner_text()
       await page.locator('#calc_fuelEconomy').fill('0');assert await page.locator('#calc_fuelEconomy').get_attribute('aria-invalid')=='true'
      elif slug=='opladningstid':
       await page.locator('#carSelect').select_option('tesla-model-y-standard-rwd')
       assert await page.locator('#calc_power').input_value()=='11','Do not use maximum DC power as average'
       await page.locator('#calc_power').fill('50');assert '0,72 timer' in await page.locator('#answer').inner_text()
       await page.locator('#calc_power').fill('0');assert await page.locator('#calc_power').get_attribute('aria-invalid')=='true'
      elif slug=='leasing-vs-koeb':
       await page.locator('#calc_resaleValue').fill('100000');assert '8.964' in await page.locator('#answer').inner_text()
       await page.locator('#calc_months').fill('0');assert await page.locator('#calc_months').get_attribute('aria-invalid')=='true'
      else:
       await page.locator('#carSelect').select_option('tesla-model-y-standard-rwd')
       assert await page.locator('#calc_price').input_value()=='304990'
       await page.locator('#carSelect').select_option('elveon-motors-min-e-sedan-base')
       assert await page.locator('#calc_price').input_value()=='250000'
       assert 'ikke bekræftet' in await page.locator('#modelNote').inner_text()
       await page.locator('#calc_price').fill('250000');await page.locator('#calc_futureValue').fill('75000')
       assert '250.000' in await page.locator('#answer').inner_text()
      # Capture a valid initial form for visual review, preserving the real mobile layout.
      await page.goto(BASE+'/beregnere/'+slug+'/',wait_until='load')
      shot=RESULTS/(slug+'-'+label+'.png');await page.locator('.calculator-panel').screenshot(path=str(shot));panels.append((label,slug,shot))
      await page.locator('#calculateButton').click()
      answer=await page.locator('#answer').inner_text()
      assert not any(word in answer for word in ['NaN','Infinity','undefined'])
     report.append({'slug':slug,'viewport':label,'javascript':javascript,'result':'passed'})
    assert not errors,errors
    await context.close()
  # Model links lead to a real page and carry car selection only as UI state.
  context=await browser.new_context(viewport={'width':390,'height':844});await context.route('**/*',handle)
  page=await context.new_page();await page.goto(BASE+'/elbil/tesla-model-y-standard-rwd/',wait_until='load')
  await page.locator('a[href="/beregnere/ladepris/#bil=tesla-model-y-standard-rwd"]').click()
  await page.wait_for_function('document.getElementById("carSelect").value==="tesla-model-y-standard-rwd"')
  assert await page.locator('#calc_battery').input_value()=='60'
  await context.close()
  # A late price lookup cannot overwrite a price entered while it was in flight.
  context=await browser.new_context();await context.route('**/*',handle)
  gate=asyncio.Event()
  async def delayed_price(route):
   await gate.wait();await route.fulfill(status=200,json={'price':3.5})
  await context.route('https://elpriser.org/**',delayed_price)
  page=await context.new_page();await page.goto(BASE+'/beregnere/ladepris/')
  await page.locator('#loadPrices').click();await page.locator('#calc_electricPrice').fill('0');gate.set()
  await page.wait_for_function('!document.getElementById("loadPrices").disabled')
  assert await page.locator('#calc_electricPrice').input_value()=='0'
  assert 'egen indtastning' in await page.locator('#priceStatus').inner_text()
  await context.close()
  # Failed price providers preserve editable examples and complete the loading state.
  context=await browser.new_context();await context.route('**/*',handle)
  await context.route('https://elpriser.org/**',lambda route:route.fulfill(status=503,body='offline'))
  await context.route('**/data/fuel-prices.json',lambda route:route.fulfill(status=503,body='offline'))
  page=await context.new_page();await page.goto(BASE+'/beregnere/elbil-vs-benzin/')
  await page.locator('#loadPrices').click();await page.wait_for_function('!document.getElementById("loadPrices").disabled')
  assert await page.locator('#calc_electricPrice').input_value()=='2'
  assert 'kunne ikke' in await page.locator('#priceStatus').inner_text()
  assert '13.800' in await page.locator('#answer').inner_text()
  await context.close();await browser.close()
 (RESULTS/'calculator-page-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 # Contact sheets are review output only, not site assets.
 try:
  from PIL import Image,ImageDraw
  for label in ['mobile','desktop']:
   rows=[p for p in panels if p[0]==label];sheet=Image.new('RGB',(1050,1500),'#eeeeee');draw=ImageDraw.Draw(sheet)
   for n,(_,slug,file) in enumerate(rows):
    im=Image.open(file).convert('RGB');im.thumbnail((340,710));x=n%3*350;y=n//3*750;sheet.paste(im,(x,y+22));draw.text((x+3,y+3),slug,fill='black')
   raw=io.BytesIO();sheet.save(raw,format='JPEG',quality=66)
   print('CALCULATOR_SHEET '+label+' '+base64.b64encode(raw.getvalue()).decode(),flush=True)
 except ImportError:pass
 print('CALCULATOR_BROWSER_RESULT '+json.dumps({'origin':'public' if PUBLIC else 'checked-out source','page_viewport_js_cases':len(report),'model_transfer':'passed','late_manual_price':'passed','price_api_failure':'passed','all_checks':'passed'}),flush=True)
if __name__=='__main__':asyncio.run(main())
