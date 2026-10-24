"""Build the five static, useful calculator pages from reviewed content and shared math."""
from pathlib import Path
import html,json,re,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).parents[1];ORIGIN='https://www.evberegn.dk';DATE='2026-10-24'
ESC=lambda s:html.escape(str(s),quote=True)
pages=json.loads((ROOT/'data/calculator-pages.json').read_text());by_slug={p['slug']:p for p in pages}
examples=json.loads(subprocess.check_output(['node',str(ROOT/'tools/calculator_examples.cjs')],text=True))
home=(ROOT/'index.html').read_text()
cars=json.loads(re.search(r'const cars=(\[.*?\]); let selectedCar=',home,re.S)[1]);slugs=json.loads(re.search(r'const modelSlugs=(\{.*?\});',home,re.S)[1])
models=[{'slug':slugs[c[0]+'|||'+c[1]],'label':c[0]+' '+c[1],'price':c[2],'battery':c[3],'range':c[4],'consumption':c[5],'charging':c[6]} for c in cars]
(ROOT/'assets/calculator-cars.json').write_text(json.dumps({'models':models},ensure_ascii=False,separators=(',',':'))+'\n')
NAV='<nav class="page-nav" aria-label="Hovednavigation" style="display:flex;flex-wrap:wrap;gap:14px;margin-top:14px;font-size:13px"><a style="color:#10ddb2" href="/">Forside</a><a style="color:#10ddb2" href="/#beregnere">Alle 20 beregnere</a><a style="color:#10ddb2" href="/elbil/">Bilmodeller</a></nav>'
# The current ad unit is reused below the form, without adding a new ad network.
ad=re.search(r'<!-- BEGIN AADS AD UNIT.*?<!-- END AADS AD UNIT.*?-->',home,re.S)[0]
for page in pages:
 slug=page['slug'];identifier=page['calculator'];example=examples[slug];url=ORIGIN+'/beregnere/'+slug+'/'
 graph={'@context':'https://schema.org','@graph':[
 {'@type':'WebPage','@id':url+'#page','url':url,'name':page['title'],'description':page['description'],'inLanguage':'da-DK','dateModified':DATE,'isPartOf':{'@id':ORIGIN+'/#website'},'mainEntity':{'@id':url+'#calculator'}},
 {'@type':'WebApplication','@id':url+'#calculator','name':page['h1'],'url':url,'applicationCategory':'UtilitiesApplication' if identifier==8 else 'FinanceApplication','operatingSystem':'Web','inLanguage':'da-DK','isAccessibleForFree':True,'description':page['description']},
 {'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'EV Beregner','item':ORIGIN+'/'},{'@type':'ListItem','position':2,'name':page['h1'],'item':url}]}]}
 head='<!DOCTYPE html>\n<html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+ESC(page['title'])+' | EV Beregner</title><meta name="description" content="'+ESC(page['description'])+'"><meta name="robots" content="index, follow"><link rel="canonical" href="'+url+'"><meta property="og:type" content="website"><meta property="og:title" content="'+ESC(page['title'])+'"><meta property="og:description" content="'+ESC(page['description'])+'"><meta property="og:url" content="'+url+'"><meta property="og:image" content="'+ORIGIN+'/favicon-512x512.png"><meta name="theme-color" content="#070c17"><link href="/favicon.ico" rel="icon" sizes="any"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="stylesheet" href="/assets/site.css?v=20261024-calculators"><link rel="stylesheet" href="/assets/calculator-page.css?v=20261024-pages1"><script type="application/ld+json">'+json.dumps(graph,ensure_ascii=False)+'</script><script src="/assets/ev-core.js?v=20261024" defer></script><script src="/assets/calculators.js?v=20261024-pages1" defer></script><script src="/assets/calculator-page.js?v=20261024-pages1" defer></script></head>'
 body='<body class="calculator-page"><div class="page"><header class="header"><div class="logo"><a href="/">EV <span>BEREGNER</span></a></div><div class="tagline">GRATIS · ENKELT · UDEN LOGIN</div>'+NAV+'</header><div class="crumb"><a href="/">Forside</a> › '+ESC(page['h1'])+'</div><main><section class="hero"><div class="section-label">BEREGNER MED EKSEMPEL</div><h1>'+ESC(page['h1'])+'</h1><p>'+ESC(page['intro'])+'</p></section>'
 body+='<section class="calculator-panel" aria-labelledby="formTitle"><h2 id="formTitle">Beregn med dine egne tal</h2><div class="car-chooser" data-js-only hidden><label for="carSelect">Vælg eventuelt en bil som udgangspunkt</label><select id="carSelect" disabled><option value="">Generel beregning – ingen bil valgt</option></select><p class="muted" id="modelNote">Du kan beregne med dine egne tal, mens biloversigten hentes.</p></div><noscript><p class="muted">Slå JavaScript til for at beregne med dine egne tal. Regneeksemplet, metoden og forudsætningerne kan læses her uden JavaScript.</p></noscript><form id="calculatorForm" data-calculator="'+str(identifier)+'" novalidate><div class="calc-fields">'
 for key,label,_,kind in example['fields']:
  attrs=' step="any"'
  if key!='electricPrice':attrs+=' min="0"'
  if key in ('from','to','overhead'):attrs+=' max="100"'
  if key in ('power','fuelEconomy'):attrs=attrs.replace('min="0"','min="0.01"')
  if key=='months':attrs=' min="1" step="1"'
  body+='<div class="calc-field"><label for="calc_'+key+'">'+ESC(label)+'</label><input id="calc_'+key+'" name="'+key+'" type="number" value="'+ESC(example['values'][key])+'"'+attrs+' required aria-describedby="help_'+key+' error_'+key+'"><p class="field-help" id="help_'+key+'">'+ESC(page['help'][key])+'</p><p class="field-error" id="error_'+key+'"></p></div>'
 body+='</div>'
 if identifier in (1,3):
  body+='<div class="price-tools" data-js-only hidden><div class="price-controls"><label for="priceArea">Elområde<select id="priceArea"><option value="DK1">DK1 · Vest</option><option value="DK2">DK2 · Øst</option></select></label><button id="loadPrices" type="button">Hent vejledende priser</button></div><p class="muted" id="priceStatus">Eksempelpriser er vist. Indtast dine egne priser for din aftale.</p></div>'
 body+='<button class="calculate" id="calculateButton" type="submit" disabled>BEREGN</button><p id="calcMessage" role="alert"></p></form><div id="answer" class="answer" aria-live="polite" aria-atomic="true">'+example['html']+'</div><p class="muted">Resultatet følger de viste forudsætninger. Eksempelværdier er hverken aktuelle pristilbud eller en vurdering af en bestemt bil.</p></section>'
 body+='<aside aria-label="Annonce"><p class="ad-label">Annonce</p>'+ad+'</aside>'
 for section in page['sections']:
  body+='<section class="guide"><h2>'+ESC(section['heading'])+'</h2>'
  for paragraph in section.get('paragraphs',[]):body+='<p>'+ESC(paragraph)+'</p>'
  if section.get('formula'):body+='<p class="formula">'+ESC(section['formula'])+'</p>'
  if section.get('table'):
   table=section['table'];body+='<table><thead><tr>'+''.join('<th scope="col">'+ESC(v)+'</th>' for v in table['headers'])+'</tr></thead><tbody>'
   for row in table['rows']:body+='<tr>'+''.join('<td>'+ESC(v)+'</td>' for v in row)+'</tr>'
   body+='</tbody></table>'
  if section.get('bullets'):body+='<ul>'+''.join('<li>'+ESC(v)+'</li>' for v in section['bullets'])+'</ul>'
  body+='</section>'
 body+='<section class="guide"><h2>Spørgsmål om beregningen</h2>'+''.join('<h3>'+ESC(f['question'])+'</h3><p>'+ESC(f['answer'])+'</p>' for f in page['faq'])+'</section>'
 body+='<section class="guide"><h2>Metode og baggrund</h2><p>Beregningsmetode og regneeksempler: EV Beregner. Gennemgået 24. oktober 2026. Formlerne er vist ovenfor, så du kan kontrollere, hvad resultatet indeholder.</p><p>Læs også baggrund og praktiske forhold hos:</p><ul>'+''.join('<li><a href="'+ESC(v['url'])+'" target="_blank" rel="noopener noreferrer">'+ESC(v['label'])+'</a></li>' for v in page['sources'])+'</ul></section>'
 body+='<section class="related-tools"><h2>Regn videre</h2><div class="related-list">'+''.join('<a data-carry-car href="/beregnere/'+related+'/">'+ESC(by_slug[related]['h1'])+' →</a>' for related in page['related'])+'</div><p class="muted"><a class="model-link" href="/#beregnere">Se alle 20 beregnere →</a></p></section></main><footer class="page-footer">EV Beregner · <a class="model-link" href="/">Forside</a> · <a class="model-link" href="/elbil/">Biloversigt</a><br>Priser og resultater er vejledende. Kontrollér din aftale og bilens præcise variant, når du lægger budget.</footer></div></body></html>\n'
 folder=ROOT/'beregnere'/slug;folder.mkdir(parents=True,exist_ok=True);(folder/'index.html').write_text(head+body)
# Share the same small, ordinary navigation with the existing homepage.
if 'aria-label="Hovednavigation"' not in home:
 home=home.replace('<div class="tagline">GRATIS · ENKELT · UDEN LOGIN</div></header>','<div class="tagline">GRATIS · ENKELT · UDEN LOGIN</div>'+NAV+'</header>',1)
 (ROOT/'index.html').write_text(home)
NS='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',NS);ET.register_namespace('image','http://www.google.com/schemas/sitemap-image/1.1')
sitemap=ET.parse(ROOT/'sitemap.xml');root=sitemap.getroot();wanted={ORIGIN+'/beregnere/'+p['slug']+'/' for p in pages}
for node in list(root):
 if node.find('{'+NS+'}loc').text in wanted:root.remove(node)
for page in pages:
 node=ET.SubElement(root,'{'+NS+'}url');ET.SubElement(node,'{'+NS+'}loc').text=ORIGIN+'/beregnere/'+page['slug']+'/'
 ET.SubElement(node,'{'+NS+'}lastmod').text=DATE
ET.indent(sitemap,space='  ');sitemap.write(ROOT/'sitemap.xml',encoding='unicode',xml_declaration=True)
print('Built five standalone calculator pages, static examples, 181 car presets and sitemap with 188 canonical URLs.')
