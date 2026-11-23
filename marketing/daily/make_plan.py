"""Export the canonical plan without rebuilding or resetting routes/calendar IDs."""
from pathlib import Path
import csv,json
P=Path(__file__).resolve().parent
plan=json.loads((P/'DAILY-PLAN.json').read_text());items=[i for d in plan['days'] for i in d['items']]
keys=[(i['date'],i['type']) for i in items];assert len(keys)==len(set(keys))
assert all(i['publication_route'] in ['MANUAL_META_BUSINESS_SUITE','METRICOOL_CONFIRMED','METRICOOL_RESERVED_NOT_SCHEDULED'] for i in items)
with (P/'DAGLIG-KALENDER.csv').open('w',encoding='utf-8-sig',newline='') as f:
 fields=['date','time','type','theme','title','status','publication_route','owner_action','existing_id','existing_uuid','destination','caption'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:i.get(k,'') for k in fields} for i in items)
md=['# EV Beregner – daglig Facebook-plan','',f"Periode: {plan['start']}–{plan['end']}. Produktionsmål: én POST, én REEL og én separat billed-STORY dagligt. {len(items)} indholdspladser er ikke det samme som {len(items)} planlagte publiceringer.",'',
'## Kreativ retning fra 23. november 2026','',
'Følg [REEL-RETNING-20261123.md](../creative/REEL-RETNING-20261123.md) og [de 38 episodebriefs](../creative/FREMTIDIGE-REELS-20261123.md). Nye Reels bruger naturlig dansk dialog mellem normalt to fiktive voksne ved bilen. Et konkret spørgsmål, et hurtigt nyttigt svar og et roligt tempo styret af faktisk tale. Ingen hjemmesidevisning i nye standardfilm. evberegn.dk, gratis/uden login og like/følg står tydeligt til sidst. Kvinder har varierede centrale roller i mindst to af hver næste tre personfilm. Ingen garanti for rækkevidde eller organisk kønsfordeling.','',
'Nyheds- og politiske vinkler kræver en aktuel primær kilde, dato og korrekt status: forslag, aftale, vedtaget eller trådt i kraft. Genkontrollér før udgivelse. En ældre gældende regel er ikke en ny aftale. Ellers bruges et nyttigt hverdagsspørgsmål.','',
'## Hvem udgiver?','',
'METRICOOL_CONFIRMED kræver en rigtig aftale med ID/UUID og genlæsning. METRICOOL_RESERVED_NOT_SCHEDULED er kun en lokal reservation. MANUAL_META_BUSINESS_SUITE er ejerens manuelle vej og må aldrig auto-planlægges i Metricool. Er filen allerede i Meta, udskifter ejeren den på samme plads; opret ikke en dublet. Tjenestens aktuelle kalender går forud.','',
'Metricool Free har højst 20 faktiske publiceringer pr. kalendermåned på tværs af formater. Medregn udgivet, kommende, udløbne Stories og faste reservationer. Den faktiske kontotæller går forud, når den kan læses. Tre formater dagligt kræver 90–93 udgivelser om måneden; resten udgiver ejeren manuelt i Meta. Ingen køb eller opgraderinger.','',
'Ingen nye HeyGen-job i november. Den separate decemberopgave håndterer højst tre faktiske decemberforsøg inklusive fejlede forsøg, inden for den reelle kvote. Film erstatter eksisterende Reel-pladser. En Story er ét lodret 1080×1920-stillbillede, ikke en Reel. POST forklarer dagens pointe og linker til relevant værktøj. Eksisterende datoer og tider bevares.','',
'## Kalenderoversigt','',
'Status er senest dokumenterede kontrol. Manual betyder ikke, at ejeren endnu ikke har lagt filen ind.','',
'| Dato | Tema | POST | REEL | STORY |','|---|---|---|---|---|']
for d in plan['days']:
 cells=[]
 for k in ['POST','REEL','STORY']:
  i=next(i for i in d['items'] if i['type']==k);route='manuel Meta' if i['publication_route']=='MANUAL_META_BUSINESS_SUITE' else 'Metricool-aftale' if i['publication_route']=='METRICOOL_CONFIRMED' else 'Metricool-reservation';cells.append(f"{i['time']} · {route} · {i['status']}")
 md.append('| '+' | '.join([d['date'],d['theme']]+cells)+' |')
md+=['','## Kontrol og opfølgning','',
'Kontrollér tekst, faktiske produktfunktioner, priser/forbehold, licenser, lyd, mobilvisning og destination. Nye links bruger utm_source=facebook og utm_medium=organic_social før #fragmenter; bevar bilvalg og delte input.','',
'Følg op efter sammenlignelige 48 timer og 7 dage. Visninger er ikke unik rækkevidde eller webbesøg. Alle klik er ikke automatisk linkklik. Brug Reel-specifik kønsfordeling, når den findes; mål både absolut rækkevidde og andel. Samtykkebaserede webtal kan være forsinkede og ufuldstændige. Private kontotal gemmes privat. Ingen kunstige besøg eller testbeacons.','',
'DAILY-PLAN.json er den kanoniske produktionsplan. Markdown og CSV er oversigter, ikke publiceringskvitteringer eller garanteret Meta-import. make_plan.py opdaterer kun oversigter og nulstiller ikke datoer, ruter eller kalender-ID’er.']
(P/'DAGLIG-FACEBOOK-PLAN.md').write_text('\n'.join(md)+'\n');print(json.dumps({'exported_slots':len(items),'canonical_plan_modified':False}))
