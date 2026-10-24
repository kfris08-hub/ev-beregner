"""Load real Wikimedia/Wikipedia responses and actual image bytes in Chrome."""
import asyncio,json,mimetypes,os
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.async_api import async_playwright

ROOT=Path(__file__).parents[1]
BASE='https://www.evberegn.dk'
SLUGS=['tesla-model-y-standard-rwd','kia-ev3-standard-range-access','skoda-elroq-60','volkswagen-id-4-pure','hyundai-ioniq-5-standard-range-rwd-essential','bmw-ix3-2025-50-xdrive']
async def main():
 results=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for slug in SLUGS:
   context=await browser.new_context(viewport={'width':390,'height':844})
   page=await context.new_page();errors=[];responses=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('response',lambda r:responses.append({'status':r.status,'url':r.url}) if 'wikimedia.org' in r.url or 'wikipedia.org' in r.url else None)
   async def handle(route):
    url=urlsplit(route.request.url)
    if url.netloc=='www.evberegn.dk':
     name=unquote(url.path).lstrip('/')
     if not name or name.endswith('/'):name+='index.html'
     file=ROOT/name
     await route.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'text/plain')
    elif url.netloc=='elpriser.org':await route.fulfill(status=200,json={'price':2.5})
    elif url.netloc.endswith(('wikimedia.org','wikipedia.org')):await route.continue_()
    else:await route.abort()
   await context.route('**/*',handle)
   await page.goto(BASE+'/elbil/'+slug+'/',wait_until='domcontentloaded')
   passed=True
   try:
    await page.wait_for_function('(()=>{const image=document.getElementById("carPhoto");return (image.complete && image.naturalWidth>0 && getComputedStyle(image).display!=="none") || document.getElementById("photoLoading").textContent.includes("ikke tilgængeligt")})()',timeout=65000)
    passed=await page.locator('#carPhoto').evaluate('(image)=>image.complete && image.naturalWidth>0 && getComputedStyle(image).display!=="none"')
   except Exception:passed=False
   details=await page.locator('#carPhoto').evaluate('(image)=>({src:image.currentSrc,width:image.naturalWidth,height:image.naturalHeight,display:getComputedStyle(image).display,alt:image.alt})')
   result={'slug':slug,'visibleLoadedImage':passed,'image':details,'credit':await page.locator('#photoCredit').inner_text(),'status':await page.locator('#photoLoading').inner_text(),'errors':errors,'responses':responses}
   results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
   await page.screenshot(path=str(ROOT/'test-results'/('photo-'+slug+'.png')),full_page=True)
   await context.close()
  await browser.close()
 (ROOT/'test-results/photo-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 assert all(x['visibleLoadedImage'] and not x['errors'] for x in results),'One or more model images failed; see photo-results.json'

if __name__=='__main__':
 (ROOT/'test-results').mkdir(exist_ok=True)
 asyncio.run(main())
