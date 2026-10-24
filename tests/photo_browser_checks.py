"""Load all local photo bytes without JavaScript, then test actual failure handling.
Set PHOTO_PUBLIC=1 to use the public website instead of checked-out HTML/assets.
"""
import asyncio,json,mimetypes,os
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.async_api import async_playwright
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk'
CATALOG=json.loads((ROOT/'data/model-photos.json').read_text())['models']
PUBLIC=os.environ.get('PHOTO_PUBLIC')=='1'
SAMPLES=['tesla-model-y-standard-rwd','kia-ev3-standard-range-access','skoda-elroq-60','volkswagen-id-4-pure','hyundai-ioniq-5-standard-range-rwd-essential','bmw-ix3-2025-50-xdrive']
async def main():
 results=[];external=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  context=await browser.new_context(viewport={'width':390,'height':844},java_script_enabled=False)
  async def handle(route):
   url=urlsplit(route.request.url)
   if url.netloc=='www.evberegn.dk':
    if PUBLIC:await route.continue_();return
    name=unquote(url.path).lstrip('/')
    if not name or name.endswith('/'):name+='index.html'
    file=ROOT/name
    await route.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
   elif url.netloc=='elpriser.org':await route.fulfill(status=200,json={'price':2.5})
   else:
    external.append(route.request.url);await route.abort()
  await context.route('**/*',handle)
  page=await context.new_page()
  for slug,photo in CATALOG.items():
   response=await page.goto(BASE+'/elbil/'+slug+'/?billedtjek=20261024-static1',wait_until='load',timeout=30000)
   assert response.status==200,(slug,response.status)
   if photo['status']=='verified':
    image=page.locator('#carPhoto')
    state=await image.evaluate('(i)=>({complete:i.complete,width:i.naturalWidth,height:i.naturalHeight,display:getComputedStyle(i).display,src:new URL(i.currentSrc).pathname})')
    assert state['complete'] and state['width']>=700 and state['display']!='none' and state['src']==photo['src'],(slug,state)
    assert photo['author'] in await page.locator('#photoCredit').inner_text(),slug
    kind='loadedWithoutJavaScript'
   else:
    assert await page.locator('#photoLoading').is_visible(),slug
    assert 'kontrolleret modelbillede' in await page.locator('#photoLoading').inner_text(),slug
    kind='explicitMissingState'
   assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth+1'),slug
   results.append({'slug':slug,'result':kind})
   if slug in SAMPLES:await page.screenshot(path=str(ROOT/'test-results'/('fixed-photo-'+slug+'.png')),full_page=True)
  await context.close()
  # A broken asset produces a useful message and never initiates another image search.
  context=await browser.new_context(viewport={'width':390,'height':844})
  await context.route('**/*',handle)
  slug=next(s for s,p in CATALOG.items() if p['status']=='verified')
  await context.route('**'+CATALOG[slug]['src'],lambda route:route.fulfill(status=404,body='missing'))
  page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE+'/elbil/'+slug+'/',wait_until='load')
  await page.wait_for_function('getComputedStyle(document.getElementById("carPhoto")).display === "none"')
  assert 'genindlæse' in await page.locator('#photoLoading').inner_text()
  assert not errors,errors
  await context.close();await browser.close()
 assert not any('wikimedia.org' in url or 'wikipedia.org' in url for url in external),external
 (ROOT/'test-results/photo-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 print(json.dumps({'origin':'public' if PUBLIC else 'checked-out source','models':len(results),'loaded_without_javascript':sum(x['result']=='loadedWithoutJavaScript' for x in results),'explicit_missing':sum(x['result']=='explicitMissingState' for x in results),'broken_asset_message':'passed','external_image_api_requests':0,'horizontal_overflow':False},ensure_ascii=False),flush=True)
if __name__=='__main__':
 (ROOT/'test-results').mkdir(exist_ok=True)
 asyncio.run(main())
