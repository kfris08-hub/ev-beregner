"""Render one shared catalogue into the existing design; retain historical URLs/photos."""
from pathlib import Path
import csv, html, io, json, re, xml.etree.ElementTree as ET
from car_catalog import load_catalog
ROOT=Path(__file__).parents[1];BASE='https://www.evberegn.dk';FIELDS=('price','battery','range','consumption','charging')
ESC=lambda s:html.escape(str(s),quote=True)

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf-8')!=text:path.write_text(text,encoding='utf-8')

def fmt(value,digits=0):
    if value is None:return 'Ikke oplyst'
    return format(value,','+('.'+str(digits)+'f')).replace(',','X').replace('.',',').replace('X','.')

def meta(text,name,value):
    pattern=r'<meta\b(?=[^>]*(?:name|property)="'+re.escape(name)+r'")[^>]*>'
    def replace(m):return re.sub(r'content="[^"]*"','content="'+ESC(value)+'"',m[0])
    text,n=re.subn(pattern,replace,text);assert n==1,(name,n)
    return text

def replace_id(text,tag,identifier,value):
    pattern=r'(<'+tag+r'\b[^>]*\bid="'+identifier+r'"[^>]*>).*?(</'+tag+'>)'
    text,n=re.subn(pattern,lambda m:m[1]+value+m[2],text,flags=re.S);assert n==1,identifier
    return text

def source_details(m):
    labels={'price':'Pris','battery':'Batteri','range':'WLTP','consumption':'Forbrug','charging':'DC-ladning'}
    content=''
    for f in FIELDS:
        src=m.get('provenance',{}).get(f)
        if src:
            detail='<a href="'+ESC(src['url'])+'" target="_blank" rel="noopener noreferrer">'+ESC(src['label'])+'</a> · '+ESC(src['source_date'])
            if src.get('primary_url'):detail+=' · <a href="'+ESC(src['primary_url'])+'" target="_blank" rel="noopener noreferrer">Producentens prisliste</a>'
            if src.get('license_url'):detail+=' · <a href="'+ESC(src['license_url'])+'">'+ESC(src['license'])+'</a>'
        elif f=='price' and m.get('availability')=='discontinued':detail='Indtast din egen købspris.'
        else:detail='Kildedato mangler i det tidligere katalog.' if m.get(f) is not None else 'Ikke dokumenteret.'
        content+='<dt>'+labels[f]+'</dt><dd>'+detail+'</dd>'
    note='<p>Batteriets brutto-/nettobasis er ikke oplyst.</p>' if m.get('battery') is not None and not m.get('battery_basis') else ''
    if m.get('price_note'):note+='<p>'+ESC(m['price_note'])+'</p>'
    return '<details class="note" id="modelSources"><summary>Kilder og datoer</summary><dl>'+content+'</dl>'+note+'</details>'

def render_model(m,models,photo):
    path=ROOT/'elbil'/m['slug']/'index.html';is_new=not path.exists()
    text=path.read_text() if not is_new else (ROOT/'templates/model.html').read_text()
    old_graph=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)[1]);old_page=next(n for n in old_graph['@graph'] if n['@type']=='WebPage')
    old_label=html.unescape(re.search(r'<h1>(.*?)</h1>',text)[1]);label=m['brand']+' '+m['model']
    # Keep the carefully reviewed special name and explanation for Elveon.
    if m['slug']=='elveon-motors-min-e-sedan-base':label=old_label
    if is_new:
        text=text.replace('tesla-model-3-standard-rwd',m['slug']).replace(ESC(old_label),ESC(label))
        text=re.sub(r'<meta[^>]*property="og:image(?::(?:width|height|alt))?"[^>]*>','',text)
        placeholder='<div class="visual photo-wrap"><img alt="'+ESC(label)+' – modelbillede" decoding="async" id="carPhoto" style="display:none"><div class="photo-loading" id="photoLoading">Vi mangler et kontrolleret modelbillede.</div></div><div class="photo-credit" id="photoCredit"></div>'
        text=re.sub(r'<div class="visual photo-wrap">.*?<div class="photo-credit" id="photoCredit">.*?</div>',lambda _:placeholder,text,count=1,flags=re.S)
    historical=m.get('availability')=='discontinued'
    text=re.sub(r'<p class="note" id="historicalModelNotice">.*?</p>','',text,flags=re.S)
    if historical:
        notice='<p class="note" id="historicalModelNotice">Tidligere model · '+str(m['model_year'])+'. Indtast egen købspris i beregnerne.</p>'
        text=text.replace('</h1>','</h1>'+notice,1)
    title=label+' – pris, rækkevidde og økonomi | EV Beregner'
    description=label+': pris '+(fmt(m['price'])+' kr.' if m['price'] is not None else 'egen købspris' if historical else 'ikke oplyst')
    description+=', WLTP '+(fmt(m['range'])+' km' if m['range'] is not None else 'ikke oplyst')
    description+=' og forbrug '+(fmt(m['consumption'],1)+' kWh/100 km' if m['consumption'] is not None else 'ikke oplyst')+'. Beregn strømudgift og sammenlign med benzin og diesel.'
    if historical:description=label+': WLTP '+fmt(m['range'])+' km og forbrug '+fmt(m['consumption'],1)+' kWh/100 km. Beregn økonomien med din egen købspris.'
    text=re.sub(r'<title>.*?</title>',lambda _:'<title>'+ESC(title)+'</title>',text,count=1,flags=re.S)
    for key,value in [('description',description),('og:description',description),('og:title',label+' – pris og økonomi'),('og:url',BASE+'/elbil/'+m['slug']+'/'),('robots','index, follow' if m['indexable'] else 'noindex, follow')]:text=meta(text,key,value)
    stats=[('Pris',fmt(m['price'])+' kr.' if m['price'] is not None else 'Egen købspris' if historical else 'Ikke oplyst'),('Batteri (brutto)' if m.get('battery_basis')=='gross' else 'Batteri',fmt(m['battery'],1)+' kWh' if m['battery'] is not None else 'Ikke oplyst'),('WLTP',fmt(m['range'])+' km' if m['range'] is not None else 'Ikke oplyst'),('Forbrug (kWh/100 km)',fmt(m['consumption'],1)),('DC-ladning',fmt(m['charging'])+' kW' if m['charging'] is not None else 'Ikke oplyst')]
    grid='<div class="grid">'+''.join('<div class="stat"><small>'+ESC(a)+'</small><strong>'+ESC(b)+'</strong></div>' for a,b in stats)+'</div>'
    text,n=re.subn(r'<div class="grid">(?:<div class="stat">.*?</div>){5}</div>',lambda _:grid,text,count=1,flags=re.S);assert n==1,m['slug']
    text=re.sub(r'<p class="photo-credit">Kilde.*?</p>','',text,flags=re.S)
    text=re.sub(r'<details class="note" id="modelSources">.*?</details>','',text,flags=re.S)
    text=text.replace('</section>',source_details(m)+'</section>',1)
    text=re.sub(r'(data-consumption=")[^"]*(")',lambda x:x[1]+('' if m['consumption'] is None else str(m['consumption']))+x[2],text,count=1)
    if m['consumption'] is None:
        if 'id="modelConsumption"' not in text:
            text=text.replace('<div class="controls">','<p class="note" id="modelDataNotice">Forbruget er ikke dokumenteret. Beregningen bruger dit eget skøn.</p><div class="controls"><label>Dit forbrugsskøn (kWh/100 km)<input id="modelConsumption" min="0.1" step="0.1" type="number" value="16"></label>',1)
        consumption=9 if m['slug']=='elveon-motors-min-e-sedan-base' else 16
    else:
        consumption=m['consumption']
        text=re.sub(r'<label>Dit forbrugsskøn.*?</label>','',text,count=1,flags=re.S)
        text=re.sub(r'<p class="note" id="modelDataNotice">.*?</p>','',text,count=1,flags=re.S)
    for identifier,value in {'r100':fmt(consumption*2,2)+' kr.','rkm':fmt(consumption*2/100,2)+' kr.','ryear':fmt(consumption*400)+' kr.','rkwh':fmt(consumption*200)+' kWh','evAnnual':fmt(consumption*400)+' kr.'}.items():text=replace_id(text,'b',identifier,ESC(value))
    other=sorted([x for x in models if x['slug']!=m['slug']],key=lambda x:abs(x['price']-m['price']) if x['price'] is not None and m['price'] is not None else float('inf'))[:3]
    alts=''.join('<a class="alt" href="/elbil/'+x['slug']+'/"><b>'+ESC(x['brand']+' '+x['model'])+'</b><span>'+fmt(x['price'])+(' kr.' if x['price'] is not None else '')+' · '+fmt(x['range'])+(' km WLTP' if x['range'] is not None else '')+'</span></a>' for x in other)
    text=re.sub(r'(<h2>Andre elbiler</h2><div class="alts">).*?(</div>)',lambda x:x[1]+alts+x[2],text,count=1,flags=re.S)
    text=text.replace('<button onclick="calculate()">','<button aria-label="BEREGN" onclick="calculate()">')
    text=re.sub(r'Se alle \d+ elbiler',f'Se alle {len(models)} elbiler',text)
    url=BASE+'/elbil/'+m['slug']+'/'
    page={'@type':'WebPage','name':label+' – pris og økonomi','url':url,'description':description,'dateModified':m['modified']}
    if not is_new and old_page.get('primaryImageOfPage'):page['primaryImageOfPage']=old_page['primaryImageOfPage']
    graph={'@context':'https://schema.org','@graph':[page,{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'EV Beregner','item':BASE+'/'},{'@type':'ListItem','position':2,'name':'Elbiler','item':BASE+'/elbil/'},{'@type':'ListItem','position':3,'name':label,'item':url}]}]}
    text=re.sub(r'(<script type="application/ld\+json">).*?(</script>)',lambda x:x[1]+json.dumps(graph,ensure_ascii=False)+x[2],text,count=1,flags=re.S)
    write(path,text)

def build():
    catalog=load_catalog(ROOT);write(ROOT/'data/cars.json',json.dumps(catalog,ensure_ascii=False,indent=2)+'\n');models=[m for m in catalog['models'] if m['status']=='active'];count=len(models)
    home=(ROOT/'index.html').read_text();rows=[[m['brand'],m['model'],*[m[f] for f in FIELDS]] for m in models]
    home=re.sub(r'(const cars=)\[.*?\](; let selectedCar=)',lambda m:m[1]+json.dumps(rows,ensure_ascii=False,separators=(',',':'))+m[2],home,count=1,flags=re.S)
    slugs={m['brand']+'|||'+m['model']:m['slug'] for m in models}
    home=re.sub(r'(const modelSlugs=)\{.*?\}(;)',lambda m:m[1]+json.dumps(slugs,ensure_ascii=False,separators=(',',':'))+m[2],home,count=1,flags=re.S)
    historical={m['slug']:m['model_year'] for m in models if m.get('availability')=='discontinued'}
    marker='const historicalModels='+json.dumps(historical,ensure_ascii=False,separators=(',',':'))+';'
    if 'const historicalModels=' in home:home=re.sub(r'const historicalModels=\{.*?\};',lambda _:marker,home,count=1)
    else:home=re.sub(r'(const modelSlugs=\{.*?\};)',lambda x:x[1]+'\n'+marker,home,count=1,flags=re.S)
    home=re.sub(r'\d+ aktuelle elbiler · brug søgning eller filtre',str(count)+' elbiler · brug søgning eller filtre',home)
    home=re.sub(r'\d+ elbiler · brug søgning eller filtre',str(count)+' elbiler · brug søgning eller filtre',home)
    home=re.sub(r'Biloversigten omfatter \d+ modeller/prisvarianter',f'Biloversigten omfatter {count} modeller/prisvarianter',home)
    home=re.sub(r'Se alle \d+ elbiler',f'Se alle {count} elbiler',home)
    if 'id="automaticCatalogSource"' not in home:
        home=home.replace('<div class="details-content">','<div class="details-content"><p class="muted" id="automaticCatalogSource">Bilpriser kontrolleres automatisk dagligt for de tilsluttede datakilder. Kilder og datoer står på modelsiderne; manglende dækning betyder, at ældre oplysninger kan være bevaret.</p>',1)
    write(ROOT/'index.html',home)
    buffer=io.StringIO(newline='');csv.writer(buffer,delimiter=';').writerows([['Mærke','Model/variant','Pris DKK','Batteri kWh','WLTP km','Forbrug kWh/100 km','DC kW'],*rows]);write(ROOT/'bil-data-komplet.csv','\ufeff'+buffer.getvalue())
    presets=[{'slug':m['slug'],'label':m['brand']+' '+m['model'],**{f:m[f] for f in FIELDS},**({k:m[k] for k in ('availability','model_year')} if m.get('availability')=='discontinued' else {})} for m in models]
    write(ROOT/'assets/calculator-cars.json',json.dumps({'models':presets},ensure_ascii=False,separators=(',',':'))+'\n')
    manifest=json.loads((ROOT/'data/model-photos.json').read_text())
    for m in models:
        manifest['models'].setdefault(m['slug'],{'label':m['brand']+' '+m['model'],'status':'missing','reviewed':False,'reason':'Nyt modelnavn fra dokumenteret datakilde; intet kontrolleret foto tilgængeligt.'})
        render_model(m,models,manifest['models'][m['slug']])
    write(ROOT/'data/model-photos.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    overview=(ROOT/'elbil/index.html').read_text();brands=sorted({m['brand'] for m in models},key=str.casefold)
    ident=lambda b:'brand-'+str(brands.index(b))
    nav='<nav class="brandnav" aria-label="Bilmærker">'+''.join('<a href="#'+ident(b)+'">'+ESC(b)+'</a>' for b in brands)+'</nav>'
    sections=''
    for b in brands:
        sections+='<section class="brand" id="'+ident(b)+'"><h2>'+ESC(b)+'</h2><div class="list">'
        for m in sorted([x for x in models if x['brand']==b],key=lambda m:m['model'].casefold()):
            values=[('Egen købspris' if m.get('availability')=='discontinued' and m['price'] is None else fmt(m['price'])+(' kr.' if m['price'] is not None else '')),fmt(m['range'])+(' km' if m['range'] is not None else ''),fmt(m['consumption'],1)+(' kWh/100 km' if m['consumption'] is not None else '')]
            sections+='<a class="car" href="/elbil/'+m['slug']+'/"><b>'+ESC(m['brand']+' '+m['model'])+'</b><span>'+ESC(' · '.join(values))+'</span></a>'
        sections+='</div></section>'
    overview=re.sub(r'<nav class="brandnav".*?</main>',lambda _:nav+sections+'</main>',overview,count=1,flags=re.S)
    overview=re.sub(r'<p class="intro">.*?</p>','<p class="intro">Find en elbil efter mærke, og se pris, rækkevidde og forbrug.</p>',overview,count=1,flags=re.S)
    overview=meta(overview,'description',f'Se {count} elbiler samlet efter mærke. Sammenlign pris, WLTP-rækkevidde og forbrug, og åbn beregninger for hver elbil.')
    graph={'@context':'https://schema.org','@graph':[{'@type':'CollectionPage','name':'Alle elbiler – priser, rækkevidde og forbrug','url':BASE+'/elbil/'},{'@type':'ItemList','name':'Elbiler i EV Beregner','numberOfItems':count,'itemListElement':[{'@type':'ListItem','position':i,'name':m['brand']+' '+m['model'],'url':BASE+'/elbil/'+m['slug']+'/'} for i,m in enumerate(sorted(models,key=lambda x:(x['brand'].casefold(),x['model'].casefold())),1)]}]}
    overview=re.sub(r'(<script type="application/ld\+json">).*?(</script>)',lambda x:x[1]+json.dumps(graph,ensure_ascii=False)+x[2],overview,count=1,flags=re.S);write(ROOT/'elbil/index.html',overview)
    NS='http://www.sitemaps.org/schemas/sitemap/0.9';IM='http://www.google.com/schemas/sitemap-image/1.1';ET.register_namespace('',NS);ET.register_namespace('image',IM)
    old=ET.parse(ROOT/'sitemap.xml');last={n.find('{'+NS+'}loc').text:n.findtext('{'+NS+'}lastmod') for n in old.getroot()};root=ET.Element('{'+NS+'}urlset')
    urls=[(BASE+'/',None),(BASE+'/elbil/',None)]+[(BASE+'/elbil/'+m['slug']+'/',m) for m in models if m['indexable']]+[(BASE+'/beregnere/'+p['slug']+'/',None) for p in json.loads((ROOT/'data/calculator-pages.json').read_text())]
    for url,m in urls:
        n=ET.SubElement(root,'{'+NS+'}url');ET.SubElement(n,'{'+NS+'}loc').text=url
        stamp=m['modified'] if m else last.get(url) or '2026-10-25';ET.SubElement(n,'{'+NS+'}lastmod').text=stamp
        photo=manifest['models'].get(m['slug']) if m else None
        if photo and photo['status']=='verified':image=ET.SubElement(n,'{'+IM+'}image');ET.SubElement(image,'{'+IM+'}loc').text=BASE+photo['src']
    ET.indent(root,space='  ');write(ROOT/'sitemap.xml',ET.tostring(root,encoding='unicode',xml_declaration=True))
    print(f'Built catalogue: {count} active variants; {sum(m["indexable"] for m in models)} indexable model pages; 20 calculators preserved.')
if __name__=='__main__':build()
