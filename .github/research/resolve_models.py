"""Apply the reviewed model identities without changing CSS or any calculator."""
import csv,hashlib,html,io,json,re,sys,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).parents[2];ORIGIN='https://www.evberegn.dk';esc=lambda s:html.escape(str(s),quote=True)
WITHDRAWN={
'kia-ev1-standard-range':('Kia EV1','Den registrerede variant og dens danske pris og specifikationer kunne ikke bekræftes. EV1 omtales som en mulig kommende model; de tidligere tal er derfor taget ud af bilvalget.','https://www.kia.com/dk/modeller/modeloversigt/',['kia-ev2-standard-range-access','kia-ev3-standard-range-access','kia-ev4-standard-range-access']),
'kia-sportage-ev-standard':('Kia Sportage EV','Kia beskriver Sportage med hybrid-, plug-in-hybrid- og benzinmotorer. Vi har ikke kunnet bekræfte den registrerede fuldt elektriske Sportage-variant. Den er derfor taget ud af bilvalget.','https://www.kia.com/uk/new-cars/sportage/',['kia-ev5-standard-range-access','kia-ev3-standard-range-access','kia-ev6-standard-range-rwd']),
'volvo-ex50-single-motor-rwd':('Volvo EX50','EX50 omtales som en kommende model i bilmedierne. Den konkrete variant med dansk pris og fabriksdata kunne ikke bekræftes hos Volvo. De tidligere tal er derfor taget ud af bilvalget.','https://www.volvocars.com/dk/',['volvo-ex40-single-motor-core','volvo-ex60-p6-plus-rwd','volvo-ex30-standard-range-core']),
'volvo-ex70-single-motor':('Volvo EX70','Den registrerede EX70-variant med dansk pris og fabriksdata kunne ikke bekræftes hos Volvo. Den er derfor taget ud af bilvalget og sammenligningerne. Den må ikke forveksles med andre Volvo-modeller.','https://www.volvocars.com/dk/',['volvo-ex60-p6-plus-rwd','volvo-ex90-twin-motor-awd','volvo-ex40-single-motor-core'])}
ALIAS='hyundai-ioniq-7-standard';TARGET='hyundai-ioniq-9-rwd-advanced';ELVEON='elveon-motors-min-e-sedan-base';L03='xpeng-l03-standard-range-rwd'
removed=set(WITHDRAWN)|{ALIAS}
home_path=ROOT/'index.html';home=home_path.read_text();original_home=home
cars_match=re.search(r'const cars=(\[.*?\]); let selectedCar=',home,re.S);cars=json.loads(cars_match[1])
slug_match=re.search(r'const modelSlugs=(\{.*?\});',home,re.S);slugs=json.loads(slug_match[1])
by_slug={slugs[c[0]+'|||'+c[1]]:c for c in cars}
archive={slug:list(by_slug[slug]) for slug in removed|{ELVEON}}
(ROOT/'.github/research/previous-model-records.json').write_text(json.dumps({'note':'Historiske, ikke verificerede værdier. Må ikke bruges som fabriksdata.','records':archive},ensure_ascii=False,indent=2)+'\n')
cars=[c for c in cars if slugs[c[0]+'|||'+c[1]] not in removed]
for c in cars:
 slug=slugs[c[0]+'|||'+c[1]]
 if slug==L03:c[3]=58.3
 if slug==ELVEON:c[1]='Min-E Sedan';c[2:]=[None]*5
slugs={c[0]+'|||'+c[1]:(ELVEON if c[0]=='Elveon Motors' else slugs[c[0]+'|||'+c[1]]) for c in cars}
by_slug={slugs[c[0]+'|||'+c[1]]:c for c in cars}
home=home[:cars_match.start(1)]+json.dumps(cars,ensure_ascii=False,separators=(',',':'))+home[cars_match.end(1):]
home=re.sub(r'const modelSlugs=\{.*?\};','const modelSlugs='+json.dumps(slugs,ensure_ascii=False,separators=(',',':'))+';',home,count=1,flags=re.S)
# Known missing data must remain unknown, including in comparisons and filters.
home=home.replace('const money=v=>Number(v).toLocaleString("da-DK")+" kr.";', 'const money=v=>Number.isFinite(v)?Number(v).toLocaleString("da-DK")+" kr.":"Ikke oplyst";')
home=home.replace('function setMode(mode){','function carMetric(v,unit=""){return Number.isFinite(v)?number(v)+(unit?" "+unit:""):"Ikke oplyst";} function setMode(mode){',1)
home=home.replace('&&c[2]<=max&&','&&(c[2]==null?max===Infinity:c[2]<=max)&&')
home=home.replace('results.sort((a,b)=>b[2]-a[2])','results.sort((a,b)=>(b[2]??-1)-(a[2]??-1))').replace('results.sort((a,b)=>a[2]-b[2])','results.sort((a,b)=>(a[2]??Infinity)-(b[2]??Infinity))')
home=home.replace('Dansk listepris · batteri, WLTP, forbrug og DC-ladning registreret for alle biler','${c.slice(2).every(v=>v==null)?"Producentdata afventer bekræftelse. Brug egne forudsætninger i beregnerne.":"Vejledende pris og registrerede tekniske data"}')
home=home.replace('Data er vejledende og skal verificeres hos producent eller forhandler.<br><br>Bilens registrerede data bruges automatisk i relevante beregnere.','${c.slice(2).every(v=>v==null)?"Producentdata er ikke bekræftet. Beregnerne starter med redigerbare eksempelværdier, som du skal tilpasse.":"Data er vejledende og skal verificeres hos producent eller forhandler.<br><br>Bilens registrerede data bruges automatisk i relevante beregnere."}')
home=home.replace('badge.innerText="🚗 "+selectedCar[0]+" "+selectedCar[1]+" – bildata indlæst automatisk"','badge.innerText="🚗 "+selectedCar[0]+" "+selectedCar[1]+(selectedCar.slice(2).every(v=>v==null)?" – generelle eksempelværdier; indtast dine egne tal":" – bildata indlæst automatisk")')
home=home.replace('${c[4]} km · ${c[5]} kWh/100 km','${carMetric(c[4],"km")} · ${carMetric(c[5],"kWh/100 km")}')
home=home.replace('const best={price:Math.min(...chosen.map(c=>c[2])),range:Math.max(...chosen.map(c=>c[4])),cons:Math.min(...chosen.map(c=>c[5])),charge:Math.max(...chosen.map(c=>c[6]))};','const known=(i)=>chosen.map(c=>c[i]).filter(Number.isFinite); const best={price:Math.min(...known(2)),range:Math.max(...known(4)),cons:Math.min(...known(5)),charge:Math.max(...known(6))};')
home=home.replace('const cost=c=>c[5]*energyPrices.electric;','const cost=c=>Number.isFinite(c[5])?c[5]*energyPrices.electric:NaN;')
for index,unit in [(3,'kWh'),(4,'km'),(5,'kWh/100 km'),(6,'kW')]:home=home.replace("c=>c["+str(index)+"]+' "+unit+"'",'c=>carMetric(c['+str(index)+'],"'+unit+'")')
home=home.replace('Math.min(...chosen.map(cost))','Math.min(...chosen.map(cost).filter(Number.isFinite))')
# Old car-query links resolve to the current model as well.
home=home.replace("new URLSearchParams(location.search).get('car')","(new URLSearchParams(location.search).get('car') === '"+ALIAS+"' ? '"+TARGET+"' : new URLSearchParams(location.search).get('car'))")
# Remove old model links from the public catalogues.
for slug in removed:home=re.sub(r'<a\b[^>]*href="/elbil/'+re.escape(slug)+r'/"[^>]*>.*?</a>','',home,flags=re.S)
home=home.replace('Elveon Motors Min-E Sedan BASE','Elveon Motors Min-E Sedan')
for a,b in [('186 elbiler','181 elbiler'),('186 biler','181 biler'),('186 aktuelle','181 aktuelle'),('186 registrerede','181 registrerede')]:home=home.replace(a,b)
home_path.write_text(home)
# Keep the exported dataset consistent; blank fields are unknown rather than zero.
csv_path=ROOT/'bil-data-komplet.csv';rows=list(csv.reader(csv_path.open(encoding='utf-8-sig'),delimiter=';'));out=[rows[0]]
old_keys={(v[0],v[1]):s for s,v in archive.items()};old_el=archive[ELVEON]
for row in rows[1:]:
 slug=old_keys.get(tuple(row[:2]))
 if slug in removed:continue
 if row[:2]==old_el[:2]:row=[row[0],'Min-E Sedan','','','','','']
 if row[:2]==['XPENG','L03 Standard Range RWD']:row[3]='58.3'
 out.append(row)
with csv_path.open('w',newline='',encoding='utf-8-sig') as f:csv.writer(f,delimiter=';',lineterminator='\n').writerows(out)
# Reuse the current model-page CSS verbatim for the four explanation pages.
def head(title,description,canonical,robots='noindex, follow',refresh=''):
 return '<!DOCTYPE html>\n<html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+' | EV Beregner</title><meta name="description" content="'+esc(description)+'"><meta name="robots" content="'+robots+'"><link rel="canonical" href="'+ORIGIN+'/elbil/'+canonical+'/"><link href="/favicon.ico" rel="icon">'+refresh

def alt(slug):
 c=by_slug[slug];price=f'{c[2]:,}'.replace(',','.')+' kr.' if c[2] is not None else 'Data afventer kontrol'
 return '<a class="alt" href="/elbil/'+slug+'/"><b>'+esc(c[0]+' '+c[1])+'</b><span>'+price+'</span></a>'
for slug,(name,reason,source,alternatives) in WITHDRAWN.items():
 path=ROOT/'elbil'/slug/'index.html';style=re.search(r'<style>(.*?)</style>',path.read_text(),re.S)[0]
 description=name+': den tidligere registrerede elbilvariant er ikke bekræftet. Se modelstatus og dokumenterede alternativer.'
 structured={'@context':'https://schema.org','@type':'WebPage','name':name+' – modelstatus','url':ORIGIN+'/elbil/'+slug+'/','description':description,'dateModified':'2026-10-24'}
 body='<main><div class="crumb"><a href="/">EV Beregner</a> › <a href="/elbil/">Elbiler</a> › '+esc(name)+'</div><section class="hero"><div class="label">MODELSTATUS</div><h1>'+esc(name)+'</h1><p id="modelStatus">'+esc(reason)+'</p><p class="note">Den gamle adresse er bevaret som forklaring. Der vises ingen ubekræftede priser, rækkevidder eller beregninger for denne variant.</p></section><section class="box"><h2>Kilde til kontrollen</h2><p><a href="'+source+'" target="_blank" rel="noopener noreferrer">Se producentens modeloplysninger</a></p><p class="note">Kontrolleret 24. oktober 2026. Oplysninger kan blive opdateret, når producenten offentliggør en dokumenteret variant.</p></section><section class="box"><h2>Se andre elbiler</h2><div class="alts">'+''.join(alt(s) for s in alternatives)+'</div></section><section class="box moneybox"><h2>Beregn med dine egne tal</h2><a class="calc-link" href="/#beregner-2">ÅBN ALLE 20 BEREGNERE →</a></section></main>'
 path.write_text(head(name+' – modelstatus',description,slug)+ '<script type="application/ld+json">'+json.dumps(structured,ensure_ascii=False)+'</script>'+style+'</head><body>'+body+'</body></html>\n')
path=ROOT/'elbil'/ALIAS/'index.html';style=re.search(r'<style>(.*?)</style>',path.read_text(),re.S)[0]
description='IONIQ 7 var et navn i Hyundais tidlige elbilplaner. Se den aktuelle store elektriske SUV, Hyundai IONIQ 9.'
path.write_text(head('Hyundai IONIQ 7 – se IONIQ 9',description,TARGET,'index, follow','<meta http-equiv="refresh" content="0;url=/elbil/'+TARGET+'/">')+style+'</head><body><main><section class="hero"><div class="label">OPDATERET MODELHENVISNING</div><h1>Hyundai IONIQ 7: se IONIQ 9</h1><p>'+description+'</p><a class="calc-link" href="/elbil/'+TARGET+'/">SE HYUNDAI IONIQ 9 →</a><p class="note"><a href="https://www.hyundai.dk/modeller/ioniq-9">Hyundai Danmarks aktuelle model</a></p></section></main></body></html>\n')
# Refresh remaining links and remove unsupported recommendations from every active model page.
for path in (ROOT/'elbil').glob('*/index.html'):
 slug=path.parent.name
 if slug in removed:continue
 text=path.read_text().replace('/assets/model-calculator.js?v=20261024', '/assets/model-calculator.js?v=20261024-models3')
 for bad in removed:
  pattern=r'<a class="alt" href="/elbil/'+re.escape(bad)+r'/">.*?</a>'
  if re.search(pattern,text,re.S):
   current=set(re.findall(r'class="alt" href="/elbil/([^/]+)/',text))
   candidates=[(s,c) for s,c in by_slug.items() if s!=slug and s not in current and c[2] is not None]
   reference=by_slug[slug][2] or 250000
   choice=min(candidates,key=lambda pair:abs(pair[1][2]-reference))[0]
   text=re.sub(pattern,alt(choice),text,flags=re.S)
 text=re.sub(r'<a class="alt" href="/elbil/'+ELVEON+r'/">.*?</a>',alt(ELVEON),text,flags=re.S)
 text=text.replace('Se alle 186 elbiler','Se alle 181 elbiler')
 if slug==L03:text=re.sub(r'(<small>Batteri</small><strong>)[^<]*',r'\g<1>58,3 kWh',text,count=1)
 if slug==ELVEON:
  text=text.replace('Elveon Motors Min-E Sedan BASE','Elveon Min-E Sedan')
  text=re.sub(r'(<small>(?:Pris|Batteri|WLTP|Forbrug \(kWh/100 km\)|DC-ladning)</small><strong>)[^<]*',r'\g<1>Ikke bekræftet',text)
  text=re.sub(r'<title>.*?</title>','<title>Elveon Min-E Sedan – modeloplysninger og beregner | EV Beregner</title>',text,count=1)
  desc='Elveon Min-E Sedan: se modelbillede og beregn strømudgift med dit eget forbrugsskøn. Pris, WLTP og tekniske fabriksdata afventer bekræftelse.'
  text=re.sub(r'<meta content="[^"]*" name="description">','<meta content="'+desc+'" name="description">',text,count=1)
  text=re.sub(r'<meta content="[^"]*" property="og:description">','<meta content="'+desc+'" property="og:description">',text,count=1)
  text=text.replace('<div class="controls">','<p class="note" id="modelDataNotice">Producentens aktuelle variantdata har ikke kunnet bekræftes. Derfor vises ukendte felter uden tal. Beregningen nedenfor bruger dit eget forbrugsskøn og er ikke en oplysning om bilens officielle forbrug. <a href="https://blog.bilbasen.dk/ukendt-bilmaerke-saelger-elbil-for-under-105-000-kr-i-danmark">Læs om modelnavnet hos Bilbasen</a>.</p><div class="controls"><label>Dit forbrugsskøn (kWh/100 km)<input id="modelConsumption" min="0.1" step="0.1" type="number" value="9.0"></label>',1)
  text=text.replace('data-consumption="9.0"','data-consumption=""')
  text=text.replace('Eksempel: 20.000 km/år og 2,00 kr./kWh.','Eksempel: dit skøn på 9,0 kWh/100 km, 20.000 km/år og 2,00 kr./kWh.')
  match=re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S);data=json.loads(match[1])
  for node in data.get('@graph',[]):
   if node.get('@type')=='WebPage':node['name']='Elveon Min-E Sedan – modeloplysninger og beregner';node['description']=desc
  text=text[:match.start(1)]+json.dumps(data,ensure_ascii=False)+text[match.end(1):]
 path.write_text(text)
overview_path=ROOT/'elbil/index.html';overview=overview_path.read_text()
for slug in removed:overview=re.sub(r'<a class="car" href="/elbil/'+re.escape(slug)+r'/">.*?</a>','',overview,flags=re.S)
overview=re.sub(r'(<a class="car" href="/elbil/'+ELVEON+r'/"><b>).*?(</b><span>).*?(</span></a>)',r'\g<1>Elveon Min-E Sedan\2Tekniske data afventer bekræftelse · beregn med egne tal\3',overview,flags=re.S)
for a,b in [('186 elbiler','181 elbiler'),('186 modeller','181 modeller'),('186 biler','181 biler')]:overview=overview.replace(a,b)
overview_path.write_text(overview)
# Remove the four noindex pages and the alias from sitemap; crawl remains allowed in robots.txt.
NS='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',NS);ET.register_namespace('image','http://www.google.com/schemas/sitemap-image/1.1')
st=ET.parse(ROOT/'sitemap.xml')
for node in list(st.getroot()):
 if node.find('{'+NS+'}loc').text in {ORIGIN+'/elbil/'+s+'/' for s in removed}:st.getroot().remove(node)
ET.indent(st,space='  ');st.write(ROOT/'sitemap.xml',encoding='unicode',xml_declaration=True)
# Store model identity evidence and update the reviewed photo manifest.
catalog_path=ROOT/'data/model-photos.json';catalog=json.loads(catalog_path.read_text())
for slug,(name,reason,source,_) in WITHDRAWN.items():catalog['models'][slug].update(status='withdrawn',reason=reason,identity_source=source,reviewed=True,reviewed_at='2026-10-24')
catalog['models'][ALIAS].update(status='redirect',redirect_to=TARGET,reason='Tidligere modelnavn; den aktuelle modelhenvisning er IONIQ 9.',reviewed=True,reviewed_at='2026-10-24')
catalog['models'][ELVEON]['label']='Elveon Min-E Sedan'
pins=json.loads((ROOT/'.github/research/remaining-reviewed-pins.json').read_text())
for slug,pin in ({} if '--skip-image-downloads' in sys.argv else pins).items():
 from PIL import Image
 with urllib.request.urlopen(urllib.request.Request(pin['url'],headers={'User-Agent':'EVBeregn-photo-check/1.0 (https://www.evberegn.dk/)'}),timeout=40) as response:body=response.read()
 image=Image.open(io.BytesIO(body));image.load();image=image.convert('RGB');original=(image.width,image.height);image.thumbnail((1200,900))
 assert image.width>=480,slug
 output=io.BytesIO();image.save(output,format='WEBP',quality=82,method=6);body=output.getvalue();sha=hashlib.sha256(body).hexdigest();filename=slug+'-'+sha[:12]+'.webp'
 (ROOT/'assets/cars'/filename).write_bytes(body)
 catalog['models'][slug].update(pin,status='verified',src='/assets/cars/'+filename,width=image.width,height=image.height,original_width=original[0],original_height=original[1],bytes=len(body),sha256=sha,reviewed=True,reviewed_at='2026-10-24')
 catalog['models'][slug].pop('reason',None)
catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
sources_path=ROOT/'data/model-data-sources.json';sources=json.loads(sources_path.read_text());s=sources[L03]
s.update(battery_kwh=58.3,note='Batterikapacitet, pris, rækkevidde og DC-ladning kontrolleret i XPENG Danmarks pressemeddelelse. Kilden skelner ikke mellem brutto og netto; kapaciteten gengives uden denne betegnelse.',identity_source='https://www.xpeng.com/pressroom/news/01a13b414128a12024aa8a02829e014d')
s['verified_fields']=list(dict.fromkeys(s['verified_fields']+['battery_kwh']));sources_path.write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
print('IDENTITY_CORRECTIONS',json.dumps({'catalog_models':len(cars),'withdrawn':len(WITHDRAWN),'aliases':1,'photos':sum(p['status']=='verified' for p in catalog['models'].values()),'unknown_elveon_data':True}))
