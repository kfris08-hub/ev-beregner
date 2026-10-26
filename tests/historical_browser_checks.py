"""Older cars: search, dated technical data and explicit personal purchase prices."""
import asyncio,json,mimetypes,os,re
from pathlib import Path
from urllib.parse import unquote,urlsplit
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';PUBLIC=os.environ.get('HISTORICAL_PUBLIC')=='1'
MODELS=json.loads((ROOT/'data/historical-cars.json').read_text())['models']
async def main():
 results=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for width in [390,1280]:
   for js in [False,True]:
    context=await browser.new_context(viewport={'width':width,'height':844},java_script_enabled=js)
    async def route(r):
     u=urlsplit(r.request.url)
     if u.netloc=='www.evberegn.dk':
      if PUBLIC:await r.continue_();return
      name=unquote(u.path).lstrip('/');name=name+'index.html' if not name or name.endswith('/') else name;f=ROOT/name
      await r.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
     elif u.netloc=='elpriser.org':await r.fulfill(status=200,json={'price':2.5})
     else:await r.abort()
    await context.route('**/*',route);page=await context.new_page();page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for m in MODELS:
     response=await page.goto(BASE+'/elbil/'+m['slug']+'/',wait_until='load');assert response.status==200
     assert '2019' in await page.locator('#historicalModelNotice').inner_text()
     assert 'Egen købspris' in await page.locator('.stat').first.inner_text()
     assert await page.locator('#photoLoading').is_visible()
     assert not re.search(r'269\.999|324\.999|339\.999',await page.locator('body').inner_text())
     assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
     if js:
      await page.locator('#km').fill('10000');await page.locator('#ep').fill('2');await page.get_by_role('button',name='BEREGN',exact=True).click()
      assert re.sub(r'\D','',await page.locator('#ryear').inner_text())==str(round(m['consumption']*200))
      await page.goto(BASE+'/?car='+m['slug']+'#beregner-14',wait_until='load')
      await page.wait_for_function('currentCalculator===14 && selectedCar!==null')
      assert await page.locator('#calc_price').input_value()==''
      await page.locator('#calc_price').fill('120000')
      for input in await page.locator('#calcFields input').all():
       if await input.input_value()=='':await input.fill('60000')
      await page.locator('#calculator button.calculate').click()
      assert not re.search(r'NaN|Infinity|undefined',await page.locator('#answer').inner_text())
      await page.goto(BASE+'/beregnere/samlet-biloekonomi/#bil='+m['slug'],wait_until='load')
      await page.wait_for_function('document.getElementById("carSelect").value==='+json.dumps(m['slug']))
      assert await page.locator('#calc_price').input_value()==''
      assert 'Indtast egen købspris' in await page.locator('#modelNote').inner_text()
      await page.locator('#calc_price').fill('120000');await page.locator('#calculateButton').click()
      assert not await page.locator('#calcMessage').inner_text()
      assert not re.search(r'NaN|Infinity|undefined',await page.locator('#answer').inner_text())
     results.append({'slug':m['slug'],'width':width,'javascript':js,'result':'passed'})
    if js:
     await page.goto(BASE+'/',wait_until='load');await page.locator('#search').fill('KIA E SOUL')
     await expect(page.locator('#carList .car-card')).to_have_count(2)
     await page.locator('#cmpSearch0').fill('kia e soul');await expect(page.locator('#cmpResults0 .compare-option')).to_have_count(2)
    assert not errors,errors
    await context.close()
  await browser.close()
 out=ROOT/'test-results';out.mkdir(exist_ok=True);(out/'historical-browser.json').write_text(json.dumps(results,indent=2));print('HISTORICAL_BROWSER_RESULT '+json.dumps({'origin':'public' if PUBLIC else 'source','cases':len(results),'passed':len(results)}))
if __name__=='__main__':asyncio.run(main())
