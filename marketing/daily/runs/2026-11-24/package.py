from pathlib import Path
import json,shutil,hashlib,zipfile,datetime,subprocess
from PIL import Image
R=Path(__file__).parent;M=R.parents[2];P=M/'private/daily-20261124';NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
plan=json.loads((M/'daily/DAILY-PLAN.json').read_text());before=json.loads(json.dumps(plan));(P/'DAILY-PLAN-before.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
cal=json.loads((P/'CALENDAR-INITIAL.json').read_text())['data'];by_uuid={str(p['uuid']):p for p in cal}
assert len(cal)==16;assert not any(p['publicationDate']['dateTime'].startswith('2026-11-25') for p in cal)
brand=json.loads(json.loads((P/'BRAND.json').read_text())['content'][0]['text'])['data'][0]
assert str(brand['id'])=='8064733' and brand['networksData']['facebookData']=='1430242190176506' and brand['timezone']=='Europe/Copenhagen'
manifest=[];preserved=[];days=[]
for day in plan['days']:
 if day['date'] not in ['2026-11-24','2026-11-25','2026-11-26']:continue
 D=R/day['date'];D.mkdir(exist_ok=True);lines=[f"# {day['date']} – {day['theme']}",'','Alle tider er dansk tid. Filer er ikke en udgivelseskvittering. Bevar eksisterende aftaler og brug hver plads én gang.','', '| Tid | Format | Hvem udgiver? | Faktisk status |','|---|---|---|---|']
 for item in day['items']:
  kind=item['type'];old_path=item.get('local_workspace_path');route=item['publication_route'];manual=route=='MANUAL_META_BUSINESS_SUITE';folder=D/('MANUELT-I-META' if manual else 'METRICOOL-MA-IKKE-DUPLIKERES');folder.mkdir(exist_ok=True)
  if day['date']=='2026-11-26' and kind in ['POST','STORY']:
   src=R/'output'/f"{day['date']}-{kind.lower()}.jpg"
   item['status']='MATERIALER_KLAR_UDGIVELSE_AFVENTER';item['production']='original_typographic_still';item['visual_brief']='Original dark/turquoise still diagram. Selected 20–80 percent example, no invented UI or model imagery.'
   if kind=='POST':
    item['caption']='''Lader du kun en del af batteriet op? Regn på den del. ⚡

Prøv på hjemmesiden:
'''+item['destination']+'''

Vælg din egen elbil eller en model, du overvejer. Kontrollér batterikapaciteten, og indtast startprocent, slutprocent, din samlede elpris og et eventuelt skøn over ekstra strømforbrug.

Billedets 20 % → 80 % er valgte procenter, ikke en anbefaling til alle biler. Brutto- og brugbar batterikapacitet kan være forskellige. Ladetab skal ikke tælles to gange, hvis de allerede indgår i dine tal.

Resultatet er et regneoverslag over strømudgiften, ikke hele bilbudgettet eller et aktuelt tilbud. EV Beregner er gratis direkte i browseren uden login.

Like og følg Facebook-siden for flere enkle forklaringer om elbil og økonomi.
#elbil #opladning #EVBeregner
'''
   item['production_receipt']='marketing/daily/runs/2026-11-24/STILL-RENDER-PROOF.json'
  else:src=Path(old_path);assert src.is_file(),src
  # Preserve each original asset and copy it into a new, clearly dated delivery.
  src_hash=hashlib.sha256(src.read_bytes()).hexdigest();dest=folder/f"{item['time'].replace(':','.')}-{kind}{src.suffix}"
  shutil.copy2(src,dest);assert hashlib.sha256(dest.read_bytes()).hexdigest()==src_hash
  preserved.append({'source':str(src),'copy':str(dest),'sha256':src_hash,'source_preserved':True})
  if kind in ['POST','STORY']:
   with Image.open(dest) as im:assert im.size==((1080,1350) if kind=='POST' else (1080,1920))
  else:
   f=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]));v=next(s for s in f['streams'] if s['codec_type']=='video');a=next(s for s in f['streams'] if s['codec_type']=='audio');assert (v['codec_name'],v['width'],v['height'],a['codec_name'])==('h264',1080,1920,'aac')
  if manual:
   actual_status='UKENDT_I_MANUEL_META_KALENDER';action='Ejeren lægger filen i Meta, hvis pladsen ikke allerede er brugt.'
   if kind=='REEL':action='UDSKIFT_MEDIET_I_META_HVIS_ALLEREDE_PLANLAGT. Ny dialogversion; opret ikke en ekstra Reel.'
   item['owner_action']=action;item['manual_publication_status']='UNKNOWN_NATIVE_META_NOT_CONNECTED'
  else:
   p=by_uuid.get(str(item.get('existing_uuid')));assert p and p['facebookData']['type']==kind and p['publicationDate']['dateTime'][:10]==day['date']
   assert p['publicationDate']['dateTime'][11:16]==item['time'];actual_status=p['providers'][0]['status'];item.update({'status':actual_status,'existing_id':str(p['id']),'existing_media':p['media'],'plannerUrl':p.get('plannerUrl'),'last_calendar_check':NOW});action='MÅ_IKKE_DUPLIKERES_I_META. Metricool håndterer denne eksisterende aftale.'
   receipt={'id':str(p['id']),'uuid':str(p['uuid']),'date':p['publicationDate'],'type':kind,'media':p['media'],'providers':p['providers'],'source':'Metricool calendar read 2026-11-24','plannerUrl':p.get('plannerUrl')};(folder/f"{kind}-KVITTERING.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
  item.update({'local_workspace_path':str(dest),'artifact_storage':'WORKSPACE_DAILY_ZIP; binary not uploaded to GitHub','last_material_check':NOW})
  (folder/f"{item['time'].replace(':','.')}-{kind}-TEKST.txt").write_text(item['caption'] or 'Story: upload dette ene stillbillede som en Facebook-historie, ikke som Reel.\n')
  (folder/f"{kind}-HVEM-UDGIVER.txt").write_text(f"{day['date']} kl. {item['time']} Europe/Copenhagen\n{action}\nStatus i faktisk kalender: {actual_status}\nDestination til valgfri linkfunktion: {item['destination']}\n")
  manifest.append({'date':day['date'],'time':item['time'],'type':kind,'publication_route':route,'file':str(dest),'caption':item['caption'],'sha256':src_hash,'material_status':'READY','actual_publication_status':actual_status,'id':item.get('existing_id'),'uuid':item.get('existing_uuid'),'owner_action':action})
  lines.append(f"| {item['time']} | {kind} | {'Ejeren i Meta' if manual else 'Metricool – må ikke dubleres'} | {actual_status} |")
 lines+=['','POST og STORY til den 24.–25. genbruger de tidligere leverede filer uændret. Reel-versionerne er de nye dialogfilm fra 23. november. Gamle leverancer og allerede udgivne film er bevaret.','', 'STORY er ét 1080×1920-stillbillede i historiefeltet. Opfordring til like/følg samt hjemmesidehenvisning findes i Reel/POST. En manuel Story kan bruge linkfunktionen med destinationen i HVEM-UDGIVER.txt.','', 'Manuelle pladser må allerede være planlagt af ejeren. Kontrollér Meta før upload; udskift den eksisterende Reels medie ved revision, i stedet for at oprette en dublet.']
 (D/'START-HER.md').write_text('\n'.join(lines)+'\n');days.append(D)
# All 141 slots, routes and existing UUIDs must survive this daily run.
signature=lambda a:[(i['date'],i['type'],i['time'],i['publication_route'],i.get('existing_uuid')) for d in a['days'] for i in d['items']]
assert signature(plan)==signature(before)
plan['latest_production_run']={'date':'2026-11-24','material_dates':['2026-11-24','2026-11-25','2026-11-26'],'new_stills':2,'reused_stills':4,'reused_dialogue_reels':3,'new_Metricool_posts':0,'new_HeyGen_jobs':0,'first_incomplete_material_day':'2026-11-27','daily_target_preserved':True}
(M/'daily/DAILY-PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');(R/'READY-CONTENT.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(P/'PRESERVED-ASSETS.json').write_text(json.dumps(preserved,ensure_ascii=False,indent=2))
old_ledger=json.loads((M/'daily/QUOTA-LEDGER-202611.json').read_text());historic={str(p['uuid']):p for p in old_ledger['publications']}
for p in cal:historic[str(p['uuid'])]={'id':str(p['id']),'uuid':str(p['uuid']),'date':p['publicationDate'],'type':p['facebookData']['type'],'media':p['media'],'providers':p['providers'],'plannerUrl':p.get('plannerUrl')}
reserve=[20,22,27,30];known=len(historic);assert known+len(reserve)<=20
ledger={'month':'2026-11','verified_utc':NOW,'plan_assumption':'Metricool Free','actual_counter_exposed':False,'free_monthly_limit':20,'known_publications_and_queue':known,'known_published_with_url':sum(any(q.get('status')=='PUBLISHED' and q.get('publicUrl') for q in x['providers']) for x in historic.values()),'known_pending_or_publishing':sum(any(q.get('status') in ['PENDING','PUBLISHING'] for q in x['providers']) for x in historic.values()),'reserved_reel_days':reserve,'reserved_count':len(reserve),'known_total_including_reservations':known+len(reserve),'new_posts_created_this_run':0,'note':'Keep expired Story receipts. 20/22 remain conservative allocations after unacknowledged earlier attempts; no retries. Manual Meta rows never auto-scheduled.','publications':list(historic.values())}
(M/'daily/QUOTA-LEDGER-202611.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(P/'QUOTA-CHECK.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2))
# Source and licence bundle contains no account metrics or private calendar snapshots.
S=R/'KILDER-OG-KONTROL';S.mkdir(exist_ok=True)
for f in ['render_stills.py','verify_math.cjs','MATH-AND-LINK-PROOF.json','NEWS-FACT-CHECK.json','STILL-RENDER-PROOF.json']:shutil.copy2(R/f,S/f)
for f in ['calculators.js','calculation-share.js']:shutil.copy2(R/'reference'/f,S/f)
shutil.copy2(M/'reels/samtale-serie-20261123/FONT-LICENSE.txt',S/'FONT-LICENSE.txt');shutil.copy2(M/'reels/samtale-serie-20261123/LICENSES-AND-SOURCES.md',S/'REEL-KILDER.md')
(S/'BILLEDKILDE.txt').write_text('Genbrugte Story-billeder viser en Hyundai IONIQ 5 som illustration. Foto: TTTNIS / CC0. Udstyr, farve og fælge kan afvige, og visse varianter mangler foto. Original billedkilde: https://commons.wikimedia.org/wiki/File:Hyundai_Ioniq_5.jpg . Licens: https://creativecommons.org/publicdomain/zero/1.0/ . Billedkrediteringen i de oprindelige filer er bevaret. Nye 26-Nov-billeder er original typografi og et abstrakt diagram uden foto.\n')
(S/'KONTROL-OG-BEGRAENSNINGER.md').write_text('# Kontrol\n\nTal og delte input er kontrolleret mod GitHubs aktuelle main-beregningskode. Sider og Skats gældende 2026–2027-regel er læst via det tilsluttede webværktøj. Direkte HTTP fra kommandosandboxen gav Operation not permitted. Det ene netværksforsøg med ekstra adgang mistede sin kørsel ved runtimeudskiftning; ingen kvittering eller ny HTTP-kontrol foreligger derfra. Der er ikke foretaget lange genforsøg eller sendt beacons.\n\nIngen nye skærmoptagelser er nødvendige: POST/STORY 24.–25. genbruges uændret, og 26-Nov er original typografi. Ingen påstand om ny fotooptagelse. Nye stillbilleder er visuelt gennemgået, tekstgrænser og filstørrelser er kontrolleret. Videoerne er de uændrede dialogeksporter fra 23-Nov, med bevaret hash og H.264/AAC/1080×1920 verificeret. Ingen ny stemmegenerering. Menneskelig gennemlytning og officiel Meta-forhåndsvisning er ikke udført.\n')
start=['# Dagspakker 24.–26. november 2026','','Tre formater pr. dag er klar. Der er produceret to nye stillbilleder til den 26.; resten genbruges fra tidligere kontrollerede leverancer.','', '**24. november:** POST10 manuel, REEL14 faktisk planlagt i Metricool, STORY19 manuel.','', '**25. november:** POST10, REEL14 og STORY19 er manuelle. Reel er den nye dialogfilm om elafgift; udskift mediet i Meta, hvis du allerede har lagt den gamle ind.','', '**26. november:** REEL10 faktisk planlagt i Metricool, POST13 og STORY19 manuelle.','', 'Åbn den enkelte dags START-HER.md. Brug MANUELT-I-META til dine manuelle pladser. METRICOOL-MA-IKKE-DUPLIKERES indeholder kopier af allerede planlagte Reels; læg dem ikke også i Meta. Materialer er ikke det samme som udgivelse. Faktisk status for manuelle Meta-pladser kan ikke læses her.','', 'Gratisplanen giver højst 20 faktiske Metricool-publiceringer pr. måned, mens tre formater dagligt kræver 90–93. Ejeren udgiver resten i Meta Business Suite. Ingen køb, opgraderinger eller nye HeyGen-job. Den næste dag med manglende materiale er den 27. november.','', 'Se KILDER-OG-KONTROL for fakta, regneeksempler og licenser. Alle oprindelige leverancer er bevaret.']
(R/'START-HER.md').write_text('\n'.join(start)+'\n')
for D in days:
 z=R/f'DAGSPAKKE-{D.name}.zip'
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:
  for p in D.rglob('*'):
   if p.is_file():f.write(p,str(p.relative_to(R)))
 assert zipfile.ZipFile(z).testzip() is None
z=R/'DAGSPAKKER-24-26-NOVEMBER.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:
 for D in days+[S]:
  for p in D.rglob('*'):
   if p.is_file():f.write(p,str(p.relative_to(R)))
 f.write(R/'START-HER.md','START-HER.md')
assert zipfile.ZipFile(z).testzip() is None
proof={'date':'2026-11-24','ready_formats':9,'new_stills':2,'reused_stills':4,'reused_dialogue_reels':3,'new_HeyGen_jobs':0,'new_Metricool_posts':0,'today_Reel_status':'PENDING','manual_Meta_actual_status':'unknown','all_141_slots_routes_UUIDs_preserved':signature(plan)==signature(before),'first_incomplete_day':'2026-11-27','bundle':str(z),'bundle_megabytes':round(z.stat().st_size/1024**2,2),'purchases':0}
(R/'PRODUCTION-PROOF.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));print(json.dumps(proof,ensure_ascii=False))
