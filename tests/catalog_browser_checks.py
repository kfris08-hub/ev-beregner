"""Smoke-test automatically created cars, including absent photos/specs, with and without JS."""
import asyncio,json,mimetypes,os,re
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.async_api import async_playwright
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk'
MODELS=json.loads((ROOT/'data/cars.json').read_text())['models'];PUBLIC=os.environ.get('CATALOG_PUBLIC')=='1'
async def main():
 results=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for width in [390,1280]:
   for javascript in [False,True]:
    context=await browser.new_context(viewport={'width':width,'height':844},java_script_enabled=javascript)
    async def route(r):
     u=urlsplit(r.request.url)
     if u.netloc=='www.evberegn.dk':
      if PUBLIC:await r.continue_();return
      name=unquote(u.path).lstrip('/');name=name+'index.html' if not name or name.endswith('/') else name;file=ROOT/name
      await r.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
     elif u.netloc=='elpriser.org':await r.fulfill(status=200,json={'price':2.5})
     else:await r.abort()
    await context.route('**/*',route);page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    samples=[m for m in MODELS if m['origin']=='automatic']
    for m in samples:
     response=await page.goto(BASE+'/elbil/'+m['slug']+'/',wait_until='load');assert response.status==200
     assert await page.locator('h1').inner_text()==m['brand']+' '+m['model']
     assert ('noindex' in await page.locator('meta[name=robots]').get_attribute('content'))==(not m['indexable'])
     assert await page.locator('#photoLoading').is_visible()
     assert not await page.locator('#carPhoto').get_attribute('src')
     await page.locator('#modelSources summary').click();assert await page.locator('#modelSources dd').first.is_visible();await page.locator('#modelSources summary').click()
     if javascript:
      if m['consumption'] is None:await page.locator('#modelConsumption').fill('18')
      await page.locator('#km').fill('12000');await page.locator('#ep').fill('2');await page.get_by_role('button',name='BEREGN',exact=True).click()
      assert not re.search(r'NaN|Infinity|undefined',await page.locator('.results').inner_text())
      expected=(m['consumption'] if m['consumption'] is not None else 18)*240
      actual=await page.locator('#ryear').inner_text();assert str(round(expected))==actual.replace('.','').replace(' kr.',''),(m['slug'],actual,expected)
     assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),m['slug']
     results.append({'slug':m['slug'],'width':width,'javascript':javascript,'result':'passed'})
    assert not errors,errors
    await context.close()
  await browser.close()
 out=ROOT/'test-results';out.mkdir(exist_ok=True);(out/'catalog-browser.json').write_text(json.dumps(results,indent=2));print('CATALOG_BROWSER_RESULT '+json.dumps({'cases':len(results),'passed':len(results)}))
if __name__=='__main__':asyncio.run(main())
