"""Download real PDFs with print unavailable; inspect them with an independent parser."""
import asyncio,json,mimetypes,os,re
from pathlib import Path
from urllib.parse import urlsplit,unquote,parse_qs
import fitz
from playwright.async_api import async_playwright,expect

ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk'
PUBLIC=os.environ.get('PDF_PUBLIC')=='1'
OUT=ROOT/'test-results'/'pdf';OUT.mkdir(exist_ok=True,parents=True)

def compact(value):
 return re.sub(r'\s+','',value).replace('\u00a0','')

def inspect_pdf(path,expected):
 with fitz.open(path) as doc:
  assert doc.page_count>=1 and not doc.is_repaired, 'PDF must parse without repair'
  text='\n'.join(page.get_text() for page in doc)
  assert 'EV BEREGNER' in text and 'Vejledende beregning' in text
  for item in expected['text']:
   assert compact(item) in compact(text),(path.name,item,text)
  for page in doc:
   assert round(page.rect.width)==595 and round(page.rect.height)==842
   assert all(word[4] in ['EV','BEREGNER'] for word in page.get_text('words') if word[1]<55),'Body text must not overlap the page header'
   for word in page.get_text('words'):
    assert word[0]>=35 and word[2]<=563 and word[1]>=15 and word[3]<=821,(path.name,word)
  links=[link.get('uri','') for page in doc for link in page.get_links()]
  shared=next(link for link in links if '#s=1' in link)
  saved=parse_qs(urlsplit(shared).fragment)
  for key,value in expected['values'].items():
   assert float(saved[key][0])==float(value),(key,saved,expected)
  if expected.get('car'):assert saved['bil']==[expected['car']]
  if expected.get('area'):assert saved['area']==[expected['area']]
  return {'pages':doc.page_count,'bytes':path.stat().st_size,'shared_values':True,'text_and_notes':True}

async def snapshot(page):
 return await page.evaluate('''() => {
 const form=document.getElementById('calculatorForm');
 const def=EVCalculators.definitions[Number(form.dataset.calculator)];
 const values=Object.fromEntries(def.fields.map(([key])=>[key,form.elements.namedItem(key).value]));
 const select=document.getElementById('carSelect');
 return {values, car:select.value, area:document.getElementById('priceArea')?.value,
  text:[document.querySelector('h1').textContent,
   ...def.fields.flatMap(([key,label])=>[label,form.elements.namedItem(key).value.replace('.',',')]),
   ...Array.from(document.querySelectorAll('#answer th,#answer td,#answer strong,#answer .result-note'),el=>el.textContent.trim()),
   document.getElementById('modelNote').textContent,
   document.getElementById('priceStatus')?.textContent||''].filter(Boolean)};
}''')

async def download(page,name):
 expected=await snapshot(page)
 async with page.expect_download() as info:await page.locator('#downloadCalculation').click()
 item=await info.value
 assert item.suggested_filename.startswith('evberegner-') and item.suggested_filename.endswith('.pdf')
 target=OUT/(name+'.pdf');await item.save_as(target)
 result=inspect_pdf(target,expected)
 await expect(page.locator('#pdfDownload')).to_be_visible()
 return result

async def main():
 results=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path=os.environ.get('CHROME_BIN','/usr/bin/google-chrome'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for width in [390,1280]:
   context=await browser.new_context(viewport={'width':width,'height':900},is_mobile=width<600,has_touch=width<600,accept_downloads=True)
   async def route(r):
    u=urlsplit(r.request.url)
    if u.scheme=='blob':await r.continue_();return
    if u.netloc=='www.evberegn.dk':
     if PUBLIC:await r.continue_();return
     name=unquote(u.path).lstrip('/');name+='index.html' if not name or name.endswith('/') else '';path=ROOT/name
     await r.fulfill(status=200 if path.is_file() else 404,body=path.read_bytes() if path.is_file() else b'missing',content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
    else:await r.abort()
   await context.route('**/*',route)
   await context.add_init_script('window.print=undefined;' if width<600 else 'window.print=()=>{throw new Error("print is unavailable");};')
   page=await context.new_page();page.set_default_timeout(12000)
   errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
   for info in json.loads((ROOT/'data/calculator-pages.json').read_text()):
    slug=info['slug'];await page.goto(BASE+'/beregnere/'+slug+'/',wait_until='load')
    await page.wait_for_function('!document.getElementById("carSelect").disabled')
    for key,value in [('consumption','22.5'),('electricPrice','3.1'),('battery','61.5')]:
     if await page.locator('#calc_'+key).count():await page.locator('#calc_'+key).fill(value)
    result=await download(page,str(width)+'-'+slug)
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    results.append({'width':width,'calculator':slug,**result})
    if slug=='pris-pr-km':
     await page.locator('#calc_electricPrice').fill('4')
     await expect(page.locator('#pdfDownload')).to_be_hidden()
     await download(page,str(width)+'-changed-values')
     text=''.join(p.get_text() for p in fitz.open(OUT/(str(width)+'-changed-values.pdf')))
     assert '90 kr.' in text,'PDF must use the edited values, not the previous result'
   await page.goto(BASE+'/beregnere/pris-pr-km/',wait_until='load')
   await page.wait_for_function('!document.getElementById("carSelect").disabled')
   await page.locator('#printCalculation').click()
   await expect(page.locator('#shareStatus')).to_contain_text('Gem PDF')
   await download(page,str(width)+'-print-unavailable')
   await page.evaluate('() => {window.__printed=0;window.print=()=>{window.__printed++;};}')
   await page.locator('#printCalculation').click()
   try:await page.wait_for_function('window.__printed===1')
   except Exception:
    print('PRINT_DIAGNOSTIC '+json.dumps(await page.evaluate('({calls:window.__printed,url:location.href,status:document.getElementById("shareStatus").textContent,message:document.getElementById("calcMessage").textContent})')))
    raise
   await expect(page.locator('#shareStatus')).to_contain_text('Gem PDF')
   await download(page,str(width)+'-print-ignored')
   await page.locator('#calc_consumption').fill('')
   await page.locator('#downloadCalculation').click()
   await expect(page.locator('#shareStatus')).to_contain_text('Ret tallene')
   await expect(page.locator('#pdfDownload')).to_be_hidden()
   # Preserve historical-model and catalogue-price reservations in saved reports.
   for car,note in [('kia-e-soul-64-kwh-2019','Tidligere model'),('opel-rocks-electric-rocks-electric','Katalogpris')]:
    await page.goto(BASE+'/beregnere/samlet-biloekonomi/#bil='+car,wait_until='load')
    await page.wait_for_function('!document.getElementById("carSelect").disabled')
    await expect(page.locator('#modelNote')).to_contain_text(note)
    await page.locator('#calc_price').fill('135000')
    await download(page,str(width)+'-'+car)
   # Values and model must survive a PDF link, just like the ordinary share button.
   url=BASE+'/beregnere/pris-pr-km/#s=1&k=2&bil=tesla-model-y-standard-rwd&area=DK2&consumption=22.5&electricPrice=3.1'
   await page.goto(url,wait_until='load');await page.wait_for_function('!document.getElementById("carSelect").disabled')
   await download(page,str(width)+'-shared-model')
   await page.emulate_media(media='print')
   await expect(page.locator('.result-actions')).to_be_hidden()
   await expect(page.locator('#answer')).to_be_visible()
   assert not errors,errors
   await page.emulate_media(media='screen')
   if width<600:await page.screenshot(path=str(OUT/'mobile-pdf-actions.png'),full_page=True)
   await context.close()
  # Danish characters, PDF control characters and multi-page output stay valid.
  context=await browser.new_context(accept_downloads=True);await context.route('**/*',route);page=await context.new_page()
  await page.goto(BASE+'/beregnere/pris-pr-km/',wait_until='load')
  async with page.expect_download() as event:
   await page.evaluate('''() => {
    const bytes=EVCalculationPDF.build({title:'ÆØÅ æøå (test) \\ korrekt',savedAt:'12. november 2026',car:'Kia e-Soul',
     fields:[{label:'Årligt strømforbrug',value:'22,5'}],result:Array.from({length:150},(_,i)=>'Række '+i+': rækkevidde og strøm'),notes:['Katalogpris – brug egen købspris.'],
     source:'https://www.evberegn.dk/beregnere/pris-pr-km/',shareURL:'https://www.evberegn.dk/beregnere/pris-pr-km/#s=1&k=2&consumption=22.5&electricPrice=3.1'});
    const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([bytes],{type:'application/pdf'}));a.download='multipage.pdf';document.body.append(a);a.click();
   }''')
  pdf=await event.value;target=OUT/'multipage-danish.pdf';await pdf.save_as(target)
  inspect_pdf(target,{'text':['ÆØÅ æøå (test)','Årligt strømforbrug','Katalogpris','egen købspris.','Række 0:','Række 149:'],'values':{'consumption':'22.5','electricPrice':'3.1'}})
  with fitz.open(target) as doc:assert doc.page_count>2
  await context.close();await browser.close()
 (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 print('PDF_BROWSER_RESULT '+json.dumps({'origin':'public' if PUBLIC else 'source','calculator_exports':len(results),'native_print_unavailable_and_ignored':'passed','invalid_values':'passed','new_values_invalidate_old_pdf':'passed','shared_model_and_area':'passed','data_quality_notes':'passed','danish_and_multipage':'passed','errors':[]}))

if __name__=='__main__':asyncio.run(main())
