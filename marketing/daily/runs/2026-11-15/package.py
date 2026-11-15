"""Deliver manual Meta packages and keep the fixed free publishing allocation."""
from pathlib import Path
from datetime import datetime
import csv,hashlib,io,json,shutil,subprocess,zipfile

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';DAILY=ROOT.parents[1]
PROOF=json.loads((OUT/'PROOF.json').read_text())
RENDER=json.loads((OUT/'RENDER-PROOF.json').read_text())
CAL=json.loads((ROOT/'CALENDAR-VERIFIED.json').read_text())
rows=CAL['calendar'];bydate={(x['date']['dateTime'][:10],x['type']):x for x in rows}
checks=json.loads((ROOT/'ASSET-CHECKSUMS.json').read_text())
for name,expected in checks.items():
    b=(OUT/name).read_bytes()
    assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==expected,name

def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def text(path,value):path.write_text(value,encoding='utf-8')
def receipt(row):
    result=dict(row)
    result['planner_url']='https://app.metricool.com/planner/calendar?blogId=8064733&openWithPostUuid='+row['uuid']
    return result
def photo_note():
    return 'Hyundai IONIQ 5 er vist som eksempel. Udstyr, farve og fælge kan afvige. Ikke alle varianter har foto. Foto: TTTNIS / CC0. Kilde: https://commons.wikimedia.org/wiki/File:Hyundai_Ioniq_5.jpg'

captions={}
for date in ['2026-11-16','2026-11-17']:
    links=PROOF['days'][date]['links']
    if date.endswith('16'):
        body=('Hvad koster dine 100 km i strøm? ⚡\n\n'
              'I dette regneeksempel giver 16 kWh/100 km og en samlet elpris på 2,00 kr./kWh en strømudgift på 32 kr. pr. 100 km.\n\n'
              'Vælg din egen elbil – eller en model, du overvejer at købe – og ret forbrug og elpris, så tallene passer til dig.\n\n'
              'Prøv gratis på hjemmesiden, uden login:\n{link}\n\n'
              'Det viste er et regneeksempel, ikke en aktuel elpris eller bilens samlede ejeromkostning. Brug dit eget forbrug og din egen samlede elpris.\n\n')
    else:
        body=('Hvad koster din næste køretur i strøm? ⚡\n\n'
              'Et regneeksempel: 75 km med et forventet forbrug på 18 kWh/100 km kræver 13,5 kWh. Ved en valgt elpris på 2,50 kr./kWh bliver strømudgiften 33,75 kr.\n\n'
              'Find din egen elbil – eller den, du overvejer at købe. Indtast turens samlede kilometer, og brug dit eget forventede forbrug og din samlede elpris.\n\n'
              'Prøv gratis på EV Beregners hjemmeside, uden login:\n{link}\n\n'
              'Beregningen viser strømudgiften. Fx værditab, forsikring, parkering og andre biludgifter er ikke med. Priser og forbrug her er valgte eksempelværdier.\n\n')
    for kind in ['POST','REEL']:
        if date=='2026-11-16' and kind=='POST':
            captions[(date,kind)]=bydate[(date,kind)]['text']
        else:
            value=body.format(link=links[kind.lower()])
            if kind=='REEL':value+=photo_note()+'\n\n'
            captions[(date,kind)]=value+'#elbil #elbiløkonomi #EVBeregner\n'
    captions[(date,'STORY')]=''

ready=[]
for date in ['2026-11-16','2026-11-17']:
    folder=ROOT/date;manual=folder/'MANUELT-I-META';manual.mkdir(parents=True,exist_ok=True)
    files=[]
    for kind,time in [('POST','10.00'),('REEL','14.00'),('STORY','19.00')]:
        if date=='2026-11-16' and kind=='POST':
            reference=folder/'ALLEREDE-PLANLAGT-MAA-IKKE-DUPLIKERES';reference.mkdir(exist_ok=True)
            shutil.copyfile(OUT/'2026-11-16-post-ALLEREDE-PLANLAGT.png',reference/'10.00-POST.png')
            text(reference/'10.00-TEKST.txt',captions[(date,kind)])
            dump(reference/'KVITTERING.json',receipt(bydate[(date,kind)]))
            continue
        ext='mp4' if kind=='REEL' else 'jpg'
        source=OUT/(date+'-'+kind.lower()+'.'+ext)
        target=manual/(time+'-'+kind+'.'+ext)
        shutil.copyfile(source,target)
        if kind!='STORY':text(manual/(time+'-TEKST.txt'),captions[(date,kind)])
        else:text(manual/(time+'-LINK.txt'),'Billedets synlige tekst er færdig. Opret som Story, ikke som Reel.\n\nHvis Meta-editoren tilbyder et linkmærkat, kan dette link bruges:\n'+PROOF['days'][date]['links']['story']+'\n\nEt trykt domæne i et billede er ikke automatisk klikbart.\n')
        ready.append({'date':date,'time':time.replace('.',':'),'timezone':'Europe/Copenhagen','type':kind,'status':'MATERIALER_KLAR_UDGIVELSE_AFVENTER','publication_route':'MANUAL_META_BUSINESS_SUITE','media_path':'marketing/daily/runs/2026-11-15/output/'+source.name,'caption':captions[(date,kind)],'destination':PROOF['days'][date]['links'][kind.lower()],'scheduled':False,'public_url':None})
        files.append(time+' '+kind)
    instructions=('# Start her – '+date+'\n\nHvem udgiver?\n\n'
        'Filerne i MANUELT-I-META skal du selv uploade og planlægge på EV Beregners egen Facebook-side i Meta Business Suite. De er ikke planlagt eller udgivet af denne opgave.\n\n'
        'Kontrollér først din Meta-kalender for samme dato og format, så du ikke lægger noget op to gange. Vi har ikke adgang til at læse den native Meta-kalender her.\n\n'
        'Planlæg disse pladser i dansk tid:\n\n'+''.join('- '+x+'\n' for x in files)+'\n'
        'Brug MP4-filen som Reel. Story er ét lodret JPG-stillbillede i historiefeltet og skal ikke genudgives som Reel. POST bruger billedet og den tilhørende tekst. Ingen annoncer eller boost er nødvendige.\n\n'
        'Alle viste priser er regneeksempler. Kun strømudgiften beregnes, ikke alle bilens omkostninger. Begge delte beregninger og bilvalget er kontrolleret ved genåbning på den aktuelle hjemmeside.\n\n')
    if date=='2026-11-16':instructions+='Opslaget kl. 10 er allerede PENDING i Metricool (UUID -6589191064007917297). MÅ IKKE DUPLIKERES I META. Billede, tekst og kvittering findes i referencefolderen.\n'
    text(folder/'START-HER.md',instructions)
    dump(folder/'STATUS.json',{'date':date,'timezone':'Europe/Copenhagen','manual_materials':[x for x in ready if x['date']==date],'metricool_post':receipt(bydate[(date,'POST')]) if date=='2026-11-16' else None,'native_meta_calendar_access':False})

dump(ROOT/'READY-CONTENT.json',{'produced_utc':CAL['verified_utc'],'source_run':'https://github.com/kfris08-hub/ev-beregner/actions/runs/43698677739','items':ready,'new_metricool_posts':0,'native_meta_calendar_access':False})

# Persist the receipt history, including Stories even after they disappear.
ledger_path=DAILY/'QUOTA-LEDGER-202611.json'
baseline=json.loads((DAILY/'CALENDAR-BASELINE.json').read_text())
old=json.loads(ledger_path.read_text()).get('publications',[]) if ledger_path.exists() else []
history={}
for row in baseline+old+rows:
    if not isinstance(row,dict) or not row.get('uuid'):continue
    date=row.get('date') or row.get('publicationDate') or {}
    if isinstance(date,str):date={'dateTime':date,'timezone':'Europe/Copenhagen'}
    if not date.get('dateTime','').startswith('2026-11'):continue
    history[row['uuid']]=row
published=[x for x in history.values() if any(p.get('status')=='PUBLISHED' and p.get('publicUrl') for p in x.get('providers',[]))]
pending=[x for x in history.values() if any(p.get('status') in ['PENDING','PUBLISHING'] for p in x.get('providers',[]))]
ledger={'month':'2026-11','verified_utc':CAL['verified_utc'],'plan_assumption':'Metricool Free','actual_counter_exposed':False,'free_monthly_limit':20,'known_publications_and_queue':len(history),'known_published_with_url':len(published),'known_pending_or_publishing':len(pending),'reserved_reel_days':[20,22,24,27,30],'reserved_count':5,'known_total_including_reservations':len(history)+5,'new_posts_created_this_run':0,'publications':list(history.values()),'rule':'Reservations are not scheduled posts. Manual Meta slots must never be automatically created in Metricool. Expired Story receipts remain in this history.'}
assert ledger['known_total_including_reservations']<=20
dump(ledger_path,ledger)

plan_path=DAILY/'DAILY-PLAN.json';plan=json.loads(plan_path.read_text())
ready_map={(x['date'],x['type']):x for x in ready}
for day in plan['days']:
    for item in day['items']:
        key=(day['date'],item['type'])
        if key in ready_map:
            prepared=ready_map[key]
            assert item['publication_route']=='MANUAL_META_BUSINESS_SUITE'
            item.update(status=prepared['status'],production='finished_original_non_heygen',media_path=prepared['media_path'],caption=prepared['caption'],destination=prepared['destination'],production_receipt='marketing/daily/runs/2026-11-15/READY-CONTENT.json',owner_action='Upload this finished file in Meta Business Suite only if not already present in your native Meta calendar')
        if key in bydate and day['date'] in ['2026-11-15','2026-11-16']:
            actual=bydate[key];provider=next((p for p in actual['providers'] if p['network']=='facebook'),{})
            item.update(existing_id=actual['id'],existing_uuid=actual['uuid'],existing_media=actual['media'],calendar_verified_utc=CAL['verified_utc'],publication_status=provider.get('status'),public_url=provider.get('publicUrl'),status='PUBLISHED' if provider.get('status')=='PUBLISHED' and provider.get('publicUrl') else 'already_scheduled')
            if key==('2026-11-15','REEL'):
                item['repair_candidate']={'path':'marketing/daily/runs/2026-11-15/output/2026-11-15-reel-clean.mp4','status':'READY_NOT_APPLIED','reason':'Original 10:00 time passed before replacement was verified. Existing publication preserved; no duplicate or reschedule.'}
plan['latest_production_run']='marketing/daily/runs/2026-11-15/READY-CONTENT.json'
dump(plan_path,plan)

csv_path=DAILY/'DAGLIG-KALENDER.csv'
with csv_path.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);columns=reader.fieldnames;csv_rows=list(reader)
for row in csv_rows:
    key=(row['date'],row['type'])
    if key in ready_map:
        update=ready_map[key]
        for name in ['status','caption','destination']:
            if name in row:row[name]=update[name]
with csv_path.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(csv_rows)

summary=('# Daglig status – 15. november 2026\n\n'
         'Kalender verificeret '+CAL['verified_utc']+'. Egen Facebook-side 1430242190176506, brand 8064733, dansk tidszone.\n\n'
         'Dagens Reel er PUBLISHED med offentlig adresse: https://facebook.com/reel/1149250870815125 . POST kl. 13 og STORY kl. 19 er PENDING. Der er ikke oprettet, flyttet eller dubleret nogen kalenderaftale.\n\n'
         'En gammel teknisk billednote blev fundet i dagens Reel. Den rensede intro er produceret, men udskiftningen nåede ikke at blive verificeret før kl. 10. Den allerede udgivne film er bevaret; den rensede kopi må ikke genudgives som en ekstra Reel. Nye bufferfilm bruger den rettede, aktuelle modelside med fuld kreditering.\n\n'
         '16. november: POST kl. 10 er allerede PENDING i Metricool; REEL kl. 14 og STORY kl. 19 er færdige manuelle materialer.\n\n'
         '17. november: POST kl. 10, REEL kl. 14 og STORY kl. 19 er færdige manuelle materialer. Ingen af disse fem manuelle pladser er planlagt i Metricool eller bekræftet i Meta.\n\n'
         'Næste produktionsbehov er 18. november: POST og STORY. Den eksisterende Reel kl. 12 er allerede i Metricool og skal bevares.\n\n'
         'Kontrol: liveberegnerne gav 0,32 kr./km og 32 kr./100 km ved 16 kWh/100 km × 2,00 kr./kWh; en tur på 75 km med 18 kWh/100 km × 2,50 kr./kWh gav 13,5 kWh og 33,75 kr. Begge delte links bevarede bilvalg og alle tal ved genåbning. Nye Reels er 20 sekunder, H.264/AAC, 720 × 1280; Story er ét 1080 × 1920 JPG. Filer og kildechecksums er verificeret, og alle semantiske billeder er gennemgået. Musik og hele filmforløbet er ikke gennemlyttet/afspillet i en player.\n\n'
         'Kvote: 15 kendte novemberudgivelser/kalenderaftaler plus fem faste Reel-reservationer fylder den planlagte gratisramme på 20. Kontoens egentlige counter er ikke eksponeret. Automatisk udgivelse af 90–93 månedlige formater kan ikke leveres på den kendte gratisplan; ejeren har valgt manuel planlægning i Meta Business Suite for resten. Ingen opgradering eller prøveperiode er oprettet.\n\n'
         'Lokal netadgang var blokeret med Operation not permitted. Den offentlige Actions-kørsel 43698677739 producerede og kontrollerede materialet. Ti eksterne/trackerforespørgsler blev blokeret under optagelsen; ingen annoncer eller analyticsbegivenheder blev sendt som test. Ingen ændring af hjemmesidens design, 20 beregnere, URLer, datakvalitetsforbehold eller billedlicenser. Ingen nye HeyGen-jobs eller køb.\n')
text(ROOT/'STATUS.md',summary)
metrics=json.loads((ROOT/'METRICS-PRIVATE.json').read_text()) if (ROOT/'METRICS-PRIVATE.json').exists() else {}
feed_rows=metrics.get('feed_posts',{}).get('rows',[])
web_rows=metrics.get('website',{}).get('rows',[])
feed_values=', '.join(str(r[3]) for r in feed_rows if len(r)>3)
web_values=', '.join(str(v) for v in web_rows[0][:3]) if web_rows else 'intet returneret udtræk'
text(ROOT/'MAALING-PRIVAT.md','# Måling til ejeren\n\n'
     f'Det tilgængelige Facebook-feed-udtræk for {metrics.get("feed_period","ikke hentet")} returnerer {len(feed_rows)} opslag med disse linkkliktal: {feed_values}. Det er ikke et bevis på tilsvarende målte webbesøg.\n\n'
     f'Metricools samtykkebaserede webudtræk for {metrics.get("website_date","ikke hentet")} returnerer sidevisninger, besøg og besøgende: {web_values}. Dækning og forsinkelse er ukendt, så nul kan ikke bruges som bevis på, at ingen besøgte hjemmesiden. Der kan ikke udledes en trend af dette datagrundlag. Ingen Search Console- eller annonceindtægtsdata er tilgængelige.\n')

for date in ['2026-11-16','2026-11-17']:
    with zipfile.ZipFile(ROOT/('DAGSPAKKE-'+date+'.zip'),'w',zipfile.ZIP_DEFLATED) as z:
        for f in (ROOT/date).rglob('*'):
            if f.is_file():z.write(f,f.relative_to(ROOT/date))
with zipfile.ZipFile(ROOT/'DAGSPAKKER-16-17-NOVEMBER.zip','w',zipfile.ZIP_DEFLATED) as z:
    for date in ['2026-11-16','2026-11-17']:
        for f in (ROOT/date).rglob('*'):
            if f.is_file():z.write(f,f.relative_to(ROOT))
    z.write(ROOT/'STATUS.md','STATUS.md')
    z.write(ROOT/'MAALING-PRIVAT.md','MAALING-PRIVAT.md')
with zipfile.ZipFile(ROOT/'KILDER-OG-KONTROL.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in ['capture.py','render.py','package.py','workflow.yml','CALENDAR-VERIFIED.json','READY-CONTENT.json','ASSET-CHECKSUMS.json','STATUS.md']:
        z.write(ROOT/name,name)
    for f in OUT.iterdir():
        if f.is_file():z.write(f,'output/'+f.name)
for f in ROOT.glob('*.zip'):
    with zipfile.ZipFile(f) as z:assert z.testzip() is None
print(json.dumps({'manual_assets_ready':len(ready),'november_known':len(history),'published':len(published),'pending':len(pending),'reserved':5,'new_calendar_entries':0,'packages':[f.name for f in ROOT.glob('*.zip')]},ensure_ascii=False))
