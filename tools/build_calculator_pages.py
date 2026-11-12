"""Build useful calculator pages, a complete tool overview and source information."""
from pathlib import Path
from datetime import date
import html,json,re,subprocess,xml.etree.ElementTree as ET
from build_car_catalog import catalog_price
ROOT=Path(__file__).parents[1];ORIGIN='https://www.evberegn.dk';VERSION='20261111-growth1'
PDF_VERSION='20261112-pdf1'
ESC=lambda value:html.escape(str(value),quote=True)
MONTHS=['januar','februar','marts','april','maj','juni','juli','august','september','oktober','november','december']
NAV='<nav class="page-nav" aria-label="Hovednavigation"><a href="/">Forside</a><a href="/beregnere/" data-carry-car>Alle 20 beregnere</a><a href="/elbil/">Bilmodeller</a></nav>'
def write(path,text):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.read_text()==text:return False
 path.write_text(text);return True
def reviewed(stamp):
 d=date.fromisoformat(stamp);return str(d.day)+'. '+MONTHS[d.month-1]+' '+str(d.year)
def previous_stamp(text,fallback):
 match=re.search(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"',text)
 return match[1] if match else fallback
def head(title,description,url,graph,image,script=''):
 return '<!DOCTYPE html>\n<html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+ESC(title)+' | EV Beregner</title><meta name="description" content="'+ESC(description)+'"><meta name="robots" content="index, follow, max-image-preview:large"><link rel="canonical" href="'+url+'"><meta property="og:type" content="website"><meta property="og:locale" content="da_DK"><meta property="og:title" content="'+ESC(title)+'"><meta property="og:description" content="'+ESC(description)+'"><meta property="og:url" content="'+url+'"><meta property="og:image" content="'+ORIGIN+image+'"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="'+ESC(title)+'"><meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#070c17"><link href="/favicon.ico" rel="icon" sizes="any"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="stylesheet" href="/assets/site.css?v='+VERSION+'"><link rel="stylesheet" href="/assets/calculator-page.css?v='+VERSION+'"><script type="application/ld+json">'+json.dumps(graph,ensure_ascii=False)+'</script>'+script+'</head>'
def header():
 return '<body class="calculator-page"><div class="page"><header class="header"><div class="logo"><a href="/">EV <span>BEREGNER</span></a></div><div class="tagline">GRATIS · ENKELT · UDEN LOGIN</div>'+NAV+'</header>'
def footer():
 return '<footer class="page-footer">EV Beregner · <a class="model-link" href="/">Forside</a> · <a class="model-link" href="/elbil/">Biloversigt</a> · <a class="model-link" href="/om/">Om og kilder</a><br><a class="model-link" href="/#beregnere">Åbn de 20 beregnere på forsiden →</a></footer></div></body></html>\n'
def breadcrumb(url,label):
 return {'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'EV Beregner','item':ORIGIN+'/'},{'@type':'ListItem','position':2,'name':'Alle beregnere','item':ORIGIN+'/beregnere/'},{'@type':'ListItem','position':3,'name':label,'item':url}]}
def settle(path,content,stamp,today):
 old=path.read_text() if path.exists() else ''
 if old!=content:
  content=content.replace('"dateModified": "'+stamp+'"','"dateModified": "'+today+'"',1)
  write(path,content);return today
 return stamp
def build(root=ROOT,today=None):
 root=Path(root);today=(today or date.today()).isoformat()
 pages=json.loads((root/'data/calculator-pages.json').read_text());by_slug={p['slug']:p for p in pages}
 examples=json.loads(subprocess.check_output(['node',str(root/'tools/calculator_examples.cjs')],text=True))
 home=(root/'index.html').read_text();original_home=home
 catalog=json.loads((root/'data/cars.json').read_text())['models']
 models=[{'slug':m['slug'],'label':m['brand']+' '+m['model'],**{k:m[k] for k in ('price','battery','range','consumption','charging')},**({'price_status':'catalogue'} if catalog_price(m) else {}),**({'battery_basis':m['battery_basis']} if m.get('battery_basis') else {}),**({k:m[k] for k in ('availability','model_year')} if m.get('availability')=='discontinued' else {})} for m in catalog if m['status']=='active']
 write(root/'assets/calculator-cars.json',json.dumps({'models':models},ensure_ascii=False,separators=(',',':'))+'\n')
 match=re.search(r'<!-- BEGIN AADS AD UNIT.*?<!-- END AADS AD UNIT.*?-->',home,re.S);assert match,'Existing ad unit missing'
 ad=match[0].replace('z-index: 99998','z-index: 0')
 ad=re.sub(r'<iframe(?![^>]*loading=)', '<iframe loading="lazy" title="Annonce"',ad,count=1)
 stamps={}
 for page in pages:
  slug=page['slug'];identifier=page['calculator'];example=examples[slug];url=ORIGIN+'/beregnere/'+slug+'/'
  path=root/'beregnere'/slug/'index.html';old=path.read_text() if path.exists() else '';stamp=previous_stamp(old,page['reviewed'])
  graph={'@context':'https://schema.org','@graph':[
   {'@type':'WebPage','@id':url+'#page','url':url,'name':page['title'],'description':page['description'],'inLanguage':'da-DK','dateModified':stamp,'isPartOf':{'@id':ORIGIN+'/#website'},'mainEntity':{'@id':url+'#calculator'},'publisher':{'@type':'Organization','name':'EV Beregner','url':ORIGIN+'/'}},
   {'@type':'WebApplication','@id':url+'#calculator','name':page['h1'],'url':url,'applicationCategory':'UtilitiesApplication' if identifier in (7,8,9) else 'FinanceApplication','operatingSystem':'Web','inLanguage':'da-DK','isAccessibleForFree':True,'description':page['description']},breadcrumb(url,page['h1'])]}
  scripts='<script src="/assets/ev-core.js?v=20261105-fuel1" defer></script><script src="/assets/calculators.js?v='+VERSION+'" defer></script><script src="/assets/calculation-share.js?v='+VERSION+'" defer></script><script src="/assets/calculation-pdf.js?v='+PDF_VERSION+'" defer></script><script src="/assets/calculator-page.js?v='+PDF_VERSION+'" defer></script>'
  text=head(page['title'],page['description'],url,graph,'/assets/social/'+slug+'.png',scripts)+header()
  text+='<div class="crumb"><a href="/">Forside</a> › <a href="/beregnere/" data-carry-car>Beregnere</a> › '+ESC(page['h1'])+'</div><main><section class="hero"><div class="section-label">GRATIS BEREGNER</div><h1>'+ESC(page['h1'])+'</h1><p>'+ESC(page['intro'])+'</p></section>'
  text+='<section class="calculator-panel" aria-labelledby="formTitle"><h2 id="formTitle">Indtast dine tal</h2><div class="car-chooser" data-js-only hidden><label for="carSelect">Bil (valgfrit)</label><select id="carSelect" disabled><option value="">Brug egne tal</option></select><p class="muted" id="modelNote"></p></div><noscript><p class="muted">Slå JavaScript til for at beregne. Eksempler og metode kan åbnes nedenfor uden JavaScript.</p></noscript><form id="calculatorForm" data-calculator="'+str(identifier)+'" novalidate><div class="calc-fields">'
  for key,label,_,kind in example['fields']:
   attrs=' step="any"'+(' min="0"' if key!='electricPrice' else '')
   if key in ('from','to','overhead'):attrs+=' max="100"'
   if key in ('power','fuelEconomy') or (identifier==7 and key=='consumption'):attrs=attrs.replace('min="0"','min="0.01"')
   if key=='months':attrs=' min="1" step="1"'
   text+='<div class="calc-field"><label for="calc_'+key+'">'+ESC(label)+'</label><input id="calc_'+key+'" name="'+key+'" type="number" value="'+ESC(example['values'][key])+'"'+attrs+' required aria-describedby="help_'+key+' error_'+key+'"><p class="field-error" id="error_'+key+'"></p></div>'
  text+='</div><details class="field-explanations"><summary>Hjælp til felterne</summary><dl>'+''.join('<dt>'+ESC(label)+'</dt><dd id="help_'+key+'">'+ESC(page['help'][key])+'</dd>' for key,label,_,kind in example['fields'])+'</dl></details>'
  if any(kind=='liveElectric' for key,label,_,kind in example['fields']):
   text+='<div class="price-tools" data-js-only hidden><div class="price-controls"><label for="priceArea">Elområde<select id="priceArea"><option value="DK1">DK1 · Vest</option><option value="DK2">DK2 · Øst</option></select></label><button id="loadPrices" type="button">Hent vejledende priser</button></div><p class="muted" id="priceStatus">Eksempelpriser – brug dine egne priser.</p></div>'
  text+='<button class="calculate" id="calculateButton" type="submit" disabled>BEREGN</button><p id="calcMessage" role="alert"></p></form><div id="answer" class="answer" aria-live="polite" aria-atomic="true">'+example['html']+'</div><p class="muted">Vejledende resultat baseret på dine tal.</p><div class="result-actions" data-js-only hidden><button id="shareCalculation" type="button">Del beregningen</button><button id="downloadCalculation" type="button">Gem PDF</button><button id="printCalculation" type="button">Print</button><a id="pdfDownload" class="model-link" target="_blank" rel="noopener" hidden>Åbn PDF</a></div><p id="shareStatus" class="muted" role="status"></p><input id="shareURL" aria-label="Link til beregningen" readonly hidden></section>'
  text+='<aside class="site-ad" aria-label="Annonce"><p class="ad-label">Annonce</p>'+ad+'</aside>'
  text+='<details class="guide calculator-explanation"><summary>Eksempler, metode og kilder</summary><div class="explanation-content">'
  for section in page['sections']:
   text+='<section class="guide"><h2>'+ESC(section['heading'])+'</h2>'+''.join('<p>'+ESC(p)+'</p>' for p in section.get('paragraphs',[]))
   if section.get('formula'):text+='<p class="formula">'+ESC(section['formula'])+'</p>'
   if section.get('table'):
    table=section['table'];text+='<table><thead><tr>'+''.join('<th scope="col">'+ESC(v)+'</th>' for v in table['headers'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+ESC(v)+'</td>' for v in row)+'</tr>' for row in table['rows'])+'</tbody></table>'
   if section.get('bullets'):text+='<ul>'+''.join('<li>'+ESC(v)+'</li>' for v in section['bullets'])+'</ul>'
   text+='</section>'
  text+='<section class="guide"><h2>Spørgsmål om beregningen</h2>'+''.join('<h3>'+ESC(f['question'])+'</h3><p>'+ESC(f['answer'])+'</p>' for f in page['faq'])+'</section>'
  text+='<section class="guide"><h2>Metode og baggrund</h2><p>Beregningsmetode og regneeksempler: EV Beregner. Gennemgået '+reviewed(page['reviewed'])+'. Formlerne er vist ovenfor, så du kan kontrollere resultatet.</p><p>Baggrund og praktiske forhold:</p><ul>'+''.join('<li><a href="'+ESC(v['url'])+'" target="_blank" rel="noopener noreferrer">'+ESC(v['label'])+'</a></li>' for v in page['sources'])+'</ul><p><a href="/om/">Om værktøjet og datakilderne →</a></p></section></div></details>'
  text+='<section class="related-tools"><h2>Regn videre</h2><div class="related-list">'+''.join('<a data-carry-car href="/beregnere/'+related+'/">'+ESC(by_slug[related]['h1'])+' →</a>' for related in page['related'])+'</div><p class="muted"><a class="model-link" href="/beregnere/" data-carry-car>Se alle 20 beregnere →</a></p></section></main>'+footer()
  stamps[url]=settle(path,text,stamp,today)
 # A complete overview includes the ten stand-alone pages and all remaining home tools.
 raw=re.search(r'const calculatorList=(\[.*?\]); const calculators=',home,re.S);assert raw
 labels={i:(name.replace('\n',' '),description) for i,(name,description) in enumerate(json.loads(raw[1]),1)}
 by_id={p['calculator']:p for p in pages}
 for info in json.loads((root/'data/site-pages.json').read_text()):
  slug=info['slug'];url=ORIGIN+'/'+slug+'/';path=root/slug/'index.html';old=path.read_text() if path.exists() else '';stamp=previous_stamp(old,'2026-11-11')
  node={'@type':'CollectionPage' if slug=='beregnere' else 'WebPage','name':info['title'],'url':url,'description':info['description'],'dateModified':stamp,'inLanguage':'da-DK'}
  graph={'@context':'https://schema.org','@graph':[node]}
  if slug=='beregnere':
   graph['@graph'].append({'@type':'ItemList','numberOfItems':20,'itemListElement':[{'@type':'ListItem','position':i,'name':labels[i][0],'url':ORIGIN+('/beregnere/'+by_id[i]['slug']+'/' if i in by_id else '/#beregner-'+str(i))} for i in range(1,21)]})
  text=head(info['title'],info['description'],url,graph,'/assets/social/ev-beregner.png','<script src="/assets/tool-navigation.js?v='+VERSION+'" defer></script>')+header()+'<main><section class="hero"><h1>'+ESC(info['h1'])+'</h1>'
  if slug=='beregnere':
   text+='<p>Find beregningen til dit spørgsmål. Vælg en bil, eller brug dine egne tal.</p><div data-nav-js hidden><label for="toolSearch">Find en beregner</label><input id="toolSearch" type="search" maxlength="100" placeholder="Fx ladepris eller benzin"></div></section>'
   groups=[('Opladning og strøm',[1,7,8,9,10,11,19]),('Pris og køreture',[2,6,18]),('El, benzin og diesel',[3,4,5,17,20]),('Køb og budget',[12,13,14,15,16])]
   for label,ids in groups:
    text+='<section class="guide tool-group"><h2>'+label+'</h2><div class="related-list">'
    for identifier in ids:
     target='/beregnere/'+by_id[identifier]['slug']+'/' if identifier in by_id else '/#beregner-'+str(identifier)
     text+='<a data-tool="'+ESC(labels[identifier][0]+' '+labels[identifier][1]+' '+target)+'" data-carry-car href="'+target+'"><b>'+ESC(labels[identifier][0])+'</b><span>'+ESC(labels[identifier][1])+'</span></a>'
    text+='</div></section>'
   text+='<p id="noTools" class="muted" role="status" hidden>Ingen beregnere matcher din søgning.</p>'
  else:
   text+='<p>Gratis værktøjer til at regne på elbilens energi og økonomi.</p></section>'
   text+='<section class="guide"><h2>Hvad kan du bruge siden til?</h2><p>EV Beregner samler 20 beregnere og en biloversigt. Du kan bruge dine egne tal og vælge en registreret bilvariant som udgangspunkt. Siden er uafhængig af bilmærker og ladeudbydere.</p><p>Beregningerne viser konsekvensen af dine forudsætninger. En lav strømudgift er ikke det samme som lave samlede ejeromkostninger. Købspris, forsikring, finansiering og værditab kræver egne oplysninger.</p></section>'
   text+='<section class="guide"><h2>Priser og bildata</h2><ul><li>Elprisen hentes fra elpriser.org for DK1 eller DK2. Din samlede aftale og lokale nettarif kan afvige.</li><li>Benzin og diesel bruger gennemsnit af OK-stationers standard-pumpepriser. Det er ikke et landsgennemsnit eller prisen på din lokale station.</li><li>Bilvariantens kilder og datoer står på modelsiden. Beløb uden sikker automatisk priskobling er mærket katalogpris.</li><li>Historiske modeller bruger daterede oplysninger og din egen købspris. Ukendte specifikationer står som ikke oplyst.</li></ul><p>Automatiske opdateringer kan blive forsinket. Kontrollér din konkrete aftale og variant, når du skal træffe en beslutning.</p></section>'
   text+='<section class="guide"><h2>Sådan kontrolleres beregningerne</h2><p>Metoder og gennemregnede eksempler findes ved hver selvstændig beregner. Regn gerne med flere scenarier. Værditabsmodellen på forsiden er en generel matematisk model og forudsiger ikke en konkret handelspris.</p><p>Delte beregninger gemmer tal i linket. De kan være baseret på ældre priser. Du vælger selv, om du deler et link eller gemmer en PDF.</p><details><summary>Se kode og test</summary><p><a href="https://github.com/kfris08-hub/ev-beregner" target="_blank" rel="noopener noreferrer">Projektets kode og kontrolforløb på GitHub</a></p></details></section>'
   text+='<section class="guide"><h2>Finansiering og feedback</h2><p>Siden er gratis at bruge og kan vise annoncer, som er mærket Annonce. Et beregningsresultat er ikke en anbefaling af en bestemt annoncør.</p><p><a href="https://github.com/kfris08-hub/ev-beregner/issues" target="_blank" rel="noopener noreferrer">Rapportér en fejl eller kom med et forslag</a>. Medtag gerne sidens adresse og et regneeksempel.</p><p><a href="/beregnere/">Find en beregner →</a></p></section>'
  text+='</main>'+footer();stamps[url]=settle(path,text,stamp,today)
 # Put useful content before the existing ad, keeping its network and unit.
 home=re.sub(r'<!-- BEGIN AADS AD UNIT.*?<!-- END AADS AD UNIT.*?-->', '',home,count=1,flags=re.S)
 home=re.sub(r'<aside class="site-ad" id="homeAd"[^>]*>.*?</aside>\s*','',home,count=1,flags=re.S)
 home=home.replace('<section class="compare-panel"','<aside class="site-ad" id="homeAd" aria-label="Annonce"><p class="ad-label">Annonce</p>'+ad+'</aside>\n<section class="compare-panel"',1)
 home=re.sub(r'<title>.*?</title>','<title>EV Beregner – ladepris, kilometerpris og biløkonomi</title>',home,count=1)
 home=re.sub(r'(<meta name="description" content=")[^"]*(")',r'\g<1>Gratis elbil beregner med 20 værktøjer. Beregn ladepris, pris pr. km og forskellen på elbil, benzin og diesel. Vælg en bil eller brug egne tal.\2',home,count=1)
 home=home.replace('href="/#beregnere">Alle 20 beregnere','href="/beregnere/">Alle 20 beregnere')
 home=re.sub(r'/assets/site\.css\?[^"]+','/assets/site.css?v='+VERSION,home)
 home=re.sub(r'/assets/calculators\.js\?[^"]+','/assets/calculators.js?v='+VERSION,home)
 if 'id="quickTools"' not in home:
  shortcuts='<nav class="quick-tools" id="quickTools" aria-label="Populære beregninger">'+''.join('<a href="/beregnere/'+s+'/">'+label+'</a>' for s,label in [('ladepris','Ladepris'),('elbil-vs-benzin','Elbil vs. benzin'),('pris-pr-km','Pris pr. km'),('beregnere','Alle beregnere')])+'</nav>'
  shortcuts=shortcuts.replace('/beregnere/beregnere/','/beregnere/')
  home=home.replace('<div class="disclaimer"',shortcuts+'<div class="disclaimer"',1)
 section='<section class="all-cars-seo" id="guideOverview" style="margin:26px 16px;padding:20px;border:1px solid #29374d;border-radius:18px;background:#0e1727"><div class="section-label">BEREGNERE MED EKSEMPLER</div><h2>Find beregningen til dit spørgsmål</h2><div class="related-list">'+''.join('<a class="model-link" href="/beregnere/'+p['slug']+'/">'+ESC(p['h1'])+' →</a>' for p in pages)+'</div><p><a class="model-link" href="/beregnere/">Alle 20 beregnere →</a></p></section>'
 home,n=re.subn(r'<section class="all-cars-seo"[^>]*><div class="section-label">BEREGNERE MED EKSEMPLER</div>.*?</section>',lambda _:section,home,count=1,flags=re.S);assert n==1
 if 'href="/om/"' not in home:home=home.replace('<footer class="footer">','<footer class="footer"><a href="/om/">Om og kilder</a> · ',1)
 home=re.sub(r'<meta[^>]*property="og:image(?::(?:width|height|alt))?"[^>]*>','',home)
 home=re.sub(r'<meta[^>]*name="twitter:card"[^>]*>','',home)
 home=home.replace('</head>','<meta property="og:image" content="'+ORIGIN+'/assets/social/ev-beregner.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="EV Beregner – 20 gratis beregnere"><meta name="twitter:card" content="summary_large_image"></head>',1)
 home_changed=write(root/'index.html',home)
 NS='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',NS);ET.register_namespace('image','http://www.google.com/schemas/sitemap-image/1.1')
 tree=ET.parse(root/'sitemap.xml');sitemap=tree.getroot()
 for node in list(sitemap):
  url=node.findtext('{'+NS+'}loc')
  if url in stamps:sitemap.remove(node)
  elif url==ORIGIN+'/' and home_changed:node.find('{'+NS+'}lastmod').text=today
 for url,stamp in stamps.items():
  node=ET.SubElement(sitemap,'{'+NS+'}url');ET.SubElement(node,'{'+NS+'}loc').text=url;ET.SubElement(node,'{'+NS+'}lastmod').text=stamp
 ET.indent(tree,space='  ');text=ET.tostring(sitemap,encoding='unicode',xml_declaration=True);write(root/'sitemap.xml',text)
 print('GROWTH_BUILD_RESULT '+json.dumps({'calculator_pages':len(pages),'home_calculators':20,'models':len(models),'auxiliary_pages':2,'homepage_changed':home_changed}))
if __name__=='__main__':build()

