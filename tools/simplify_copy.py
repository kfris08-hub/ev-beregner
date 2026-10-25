"""Apply concise presentation copy without removing calculations, sources or image credits."""
from pathlib import Path
import re,xml.etree.ElementTree as ET
ROOT=Path(__file__).parents[1]
home=ROOT/'index.html';text=home.read_text()
replacements={
 'Find en elbil efter pris og rækkevidde, vælg bilen og brug dens data direkte i alle beregninger.':'Vælg en bil, eller beregn med dine egne tal.',
 'Du behøver ikke vælge en bil. Alle beregnere kan bruges med dine egne tal. Hvis du vælger en bil senere, bliver relevante bildata automatisk brugt.':'Brug beregnerne med dine egne tal.',
 'Vælg elområde. El-, benzin- og dieselpriser sættes automatisk ind i relevante beregnere, men kan altid ændres manuelt.':'Vælg elområde. Priserne kan ændres i beregnerne.',
 'Skriv mærke eller model. Du slipper for at bladre gennem en liste med 181 biler.':'Søg efter mærke eller model.',
 'Pris pr. 100 km bruger automatisk den valgte DK1/DK2-elpris ovenfor.':'Strømudgiften bruger den valgte elpris.',
 'Data er vejledende og skal verificeres hos producent eller forhandler.<br><br>Bilens registrerede data bruges automatisk i relevante beregnere.':'Bilens tal indsættes i beregnerne.',
 'Producentdata er ikke bekræftet. Beregnerne starter med redigerbare eksempelværdier, som du skal tilpasse.':'Producentdata er ikke bekræftet. Tilpas eksempelværdierne.',
 '${auto?\'<div class="auto-info">✓ Indsat automatisk – kan ændres manuelt</div>\':\'\'}':'',
}
for before,after in replacements.items():text=text.replace(before,after)
text=re.sub(r'<div class="disclaimer"><strong>Vigtigt:</strong>.*?</div>','<div class="disclaimer">Priser og bildata er vejledende. <a href="#metode">Se forudsætninger og kilder</a>.</div>',text,count=1,flags=re.S)
text=re.sub(r'<div class="calc-disclaimer">.*?</div>','<div class="calc-disclaimer">Vejledende resultat baseret på dine tal.</div>',text,count=1,flags=re.S)
if '<details class="trust-panel info-details" id="metode">' not in text:
    pattern=r'<section class="trust-panel" id="metode">(.*?)</section>\s*(<section class="seo-content".*?</section>)'
    match=re.search(pattern,text,re.S);assert match,'Expected method/source and overview sections'
    method=re.sub(r'<div class="section-label">METODE & KILDER</div>\s*<h2>Sådan beregner EV Beregner</h2>','',match[1],count=1)
    data_note='<p class="muted">Biloversigten omfatter 181 modeller/prisvarianter. Priser og specifikationer kan ændre sig og variere med udstyr og kørselsforhold. Kontrollér den præcise variant hos producent eller forhandler. Særskilt kontrollerede oplysninger har kilde og dato på modelsiden.</p>'
    block='<details class="trust-panel info-details" id="metode"><summary>Metode, kilder og forudsætninger</summary><div class="details-content">'+data_note+method+match[2]+'</div></details>'
    text=text[:match.start()]+block+text[match.end():]
text=re.sub(r'<footer class="footer">.*?</footer>','<footer class="footer"><a href="#metode">Metode og kilder</a> · <a href="/elbil/">Biloversigt</a></footer>',text,count=1,flags=re.S)
text=re.sub(r'/assets/site\.css\?v=[^"\s]+','/assets/site.css?v=20261025-copy1',text)
home.write_text(text)
updated=[]
for page in (ROOT/'elbil').glob('*/index.html'):
    text=page.read_text()
    if 'noindex, follow' in text or 'http-equiv="refresh"' in text:continue
    text=re.sub(r'(<p\b[^>]*\bid="liveNote"[^>]*>).*?(</p>)',r'\1Eksempelpriser – tilpas tallene til din aftale.\2',text,count=1,flags=re.S)
    text=re.sub(r'(<b id="rkwh">.*?</b>)kWh pr\. år',r'\1Årligt forbrug',text,count=1,flags=re.S)
    text=text.replace('Andre elbiler du bør sammenligne med','Andre elbiler').replace('Ladeboks, forsikring og finansiering','Flere beregnere')
    text=re.sub(r'/assets/model-calculator\.js\?v=[^"\s]+','/assets/model-calculator.js?v=20261025-copy1',text)
    page.write_text(text);updated.append(page.parent.name)
ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns);ET.register_namespace('image','http://www.google.com/schemas/sitemap-image/1.1')
sitemap=ET.parse(ROOT/'sitemap.xml')
for node in sitemap.getroot():
    loc=node.find('{'+ns+'}loc').text
    if loc=='https://www.evberegn.dk/' or any(loc=='https://www.evberegn.dk/elbil/'+s+'/' for s in updated):
        modified=node.find('{'+ns+'}lastmod')
        if modified is None:modified=ET.SubElement(node,'{'+ns+'}lastmod')
        if not modified.text or modified.text<'2026-10-25':modified.text='2026-10-25'
ET.indent(sitemap,space='  ');sitemap.write(ROOT/'sitemap.xml',encoding='unicode',xml_declaration=True)
print(f'Simplified homepage and {len(updated)} active model pages; calculations, image credits and model metadata preserved.')
