import asyncio,json,urllib.request
from urllib.parse import urlsplit
from playwright.async_api import async_playwright

ORIGINS=['https://www.evberegn.dk','https://evberegn.dk']
PATH='/beregnere/pris-pr-km/'
for origin in ORIGINS:
 with urllib.request.urlopen(origin+PATH,timeout=25) as response:
  body=response.read().decode()
  print('PDF_ORIGIN '+json.dumps({'requested':origin+PATH,'url':response.url,'status':response.status,'cache':response.headers.get('Cache-Control'),'etag':response.headers.get('ETag'),'newPdfButton':'id="downloadCalculation"' in body,'oldCombinedLabel':'Print / gem PDF' in body,'pdfScript':'calculation-pdf.js?v=20261112-pdf1' in body},ensure_ascii=False),flush=True)

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for origin in ORIGINS:
   for blocked in [False,True]:
    context=await browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,accept_downloads=True)
    async def route(r):
     if urlsplit(r.request.url).netloc in ['www.evberegn.dk','evberegn.dk'] or r.request.url.startswith('blob:'):await r.continue_()
     else:await r.abort()
    await context.route('**/*',route)
    await context.add_init_script('window.print=undefined;')
    page=await context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)));page.set_default_timeout(15000)
    if blocked:
     cdp=await context.new_cdp_session(page);await cdp.send('Browser.setDownloadBehavior',{'behavior':'deny'})
    await page.goto(origin+PATH,wait_until='load')
    await page.wait_for_function('!document.getElementById("carSelect").disabled')
    async with page.expect_download() as event:await page.locator('#downloadCalculation').click()
    download=await event.value
    failure=await download.failure()
    print('PDF_CLIENT '+json.dumps({'requested':origin,'url':page.url,'downloadDenied':blocked,'filename':download.suggested_filename,'downloadFailure':failure,'status':await page.locator('#shareStatus').inner_text(),'openPdfVisible':await page.locator('#pdfDownload').is_visible(),'pageErrors':errors},ensure_ascii=False),flush=True)
    await context.close()
  await browser.close()
asyncio.run(main())
