"""Daily Facebook production plan; targets are not publication receipts."""
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import csv, json

P=Path(__file__).parent
BASE='https://www.evberegn.dk'
START=date(2026,11,15)
END=date(2026,12,31)
# Each theme has a useful question, a verified existing destination and a caveat.
THEMES=[
 ('Bilvalg','Din elbil – eller din næste?','/', 'Find din egen elbil eller en model, du overvejer at købe. Åbn modelsiden, se oplysningerne, og regn videre med dine egne tal.','Modelbilleder findes ikke til alle varianter; udstyr og farve kan afvige.'),
 ('Kilometerpris','Hvad koster strømmen til 100 km?','/beregnere/pris-pr-km/','Med 16 kWh/100 km og en valgt elpris på 2 kr./kWh er strømudgiften 32 kr. pr. 100 km. Prøv med dit eget forbrug og din samlede elpris.','Et regneeksempel på strømudgiften; bilens øvrige udgifter kommer oveni.'),
 ('Køretur','Hvad koster weekendens eller hverdagens tur?','/beregnere/koeretur/','Indtast turens kilometer, bilens forbrug og din elpris. Du kan vælge bilmodellen som udgangspunkt og rette tallene.','Resultatet viser strømudgiften, ikke alle bilens omkostninger.'),
 ('Ladepris','Hvad koster 20 til 80 procent?','/beregnere/ladepris/','Vælg en bil, og tilpas batteri, startprocent, slutprocent, elpris og ekstra strømforbrug. Se prisen på netop dit regneeksempel.','Elprisen er din valgte pris, og batteridata skal passe til den mængde energi, du regner med.'),
 ('El mod benzin','El eller benzin med dine egne tal?','/beregnere/elbil-vs-benzin/','Sammenlign energiudgiften ved samme årlige kørsel. Indtast eget elforbrug, km/l, elpris og benzinpris.','Energiforskellen er ikke en beregning af alle ejeromkostninger.'),
 ('Vinterforbrug','Hvad gør højere forbrug ved rækkevidden?','/beregnere/raekkevidde/','Prøv to selvvalgte forbrugstal med samme batteri, og se forskellen i det matematiske overslag.','Det er et regneeksempel, ikke en garanti for faktisk vinterrækkevidde.'),
 ('Bil før køb','Regn på bilen, før du beslutter dig','/','Find den model, du overvejer, og brug dens data som udgangspunkt. Ret især købspris, elpris og forbrug til dine forhold.','Katalogpriser er vejledende og er ikke nødvendigvis et aktuelt forhandlertilbud.'),
 ('Opladningstid','Hvor lang tid skal bilen lade?','/beregnere/opladningstid/','Tilpas batteri, start- og slutprocent og den gennemsnitlige ladeeffekt. Se et overslag over tiden.','Bilens maksimale ladeeffekt er ikke en konstant effekt gennem hele opladningen.'),
 ('Rækkevidde','Batteri og forbrug: hvor langt rækker det?','/beregnere/raekkevidde/','Indtast den batterikapacitet og det forbrug, du vil regne med. Sammenlign flere scenarier.','Beregnet rækkevidde er et matematisk overslag; kørselsforhold påvirker den faktiske rækkevidde.'),
 ('Årligt strømforbrug','Hvor mange kWh bruger din elbil om året?','/beregnere/stroemforbrug-elbil/','Gang dine årlige kilometer med dit forventede forbrug. Beregneren viser dit årlige energibehov.','Et årsoverslag fortæller ikke præcist, hvornår bilen bliver ladet.'),
 ('Din elaftale','Hvad betyder din ladepris for økonomien?','/beregnere/pris-pr-km/','Prøv to selvvalgte elpriser med samme bilforbrug. Se, hvordan strømudgiften pr. kilometer ændrer sig.','De valgte elpriser er regneeksempler, ikke live tilbud fra ladeudbydere.'),
 ('Din bils opladning','Din bil – din ladepris','/beregnere/ladepris/','Vælg bilmodellen og regn videre på en delvis opladning. Ret elpris og ekstra strømforbrug til dit eksempel.','Batteriets brutto-/nettobasis kan være ukendt; kontrollér bilens konkrete kapacitet.'),
 ('Månedsbudget','Hvad fylder bilen i dit månedsbudget?','/#beregner-13','Saml de udgifter, du faktisk har til finansiering, forsikring, strøm og andet, i et månedsbudget.','Brug konkrete udgifter fra dine egne aftaler, og undgå at tælle samme udgift to gange.'),
 ('Egne tal','Din bil. Din elpris. Dine tal.','/beregnere/pris-pr-km/','Bilvalget er et udgangspunkt. Ret forbruget og elprisen, så beregningen passer til dig.','Eksempelværdier er ikke et løfte om din faktiske strømudgift.'),
 ('Leasing eller køb','Leasing eller køb over samme periode?','/beregnere/leasing-vs-koeb/','Medregn førstegangsydelse, den månedlige leasingydelse og dit eget skøn over bilens salgspris ved køb.','Salgsprisen er et skøn, og relevante gebyrer og øvrige udgifter skal også med.'),
 ('Samlet biløkonomi','Hvad koster bilen samlet over fem år?','/beregnere/samlet-biloekonomi/','Tag købspris, dit skøn over salgspris og de løbende udgifter med i regnestykket.','Værditab og fremtidige udgifter er skøn, ikke en konkret markedsvurdering.'),
 ('Hjemmeladning','Hvad bruger du på strøm derhjemme?','/#beregner-10','Indtast dit årlige kørselsbehov, forbrug og en samlet elpris, som passer til din aftale.','Hjemmeladningens strømudgift omfatter ikke automatisk alle udgifter til installation og abonnement.'),
 ('El mod diesel','El eller diesel: sammenlign energien','/beregnere/elbil-vs-diesel/','Sammenlign samme antal kilometer med dit elforbrug, km/l og dine energi- og brændstofpriser.','Forskellen gælder energien; købspris, finansiering og værditab skal vurderes særskilt.'),
 ('Tilgængeligt batteri','Hvilken batterikapacitet regner du med?','/beregnere/raekkevidde/','Prøv med den kapacitet, bilen faktisk kan bruge, når den er dokumenteret. Ret katalogtallet, hvis det ikke passer til dit formål.','Brutto og netto er forskellige oplysninger; ukendte data må ikke kaldes bekræftede.'),
 ('Solceller','Kan solceller dække en del af bilens strøm?','/#beregner-11','Sammenhold bilens årlige energibehov med den solenergi, du vil regne med.','Et årsoverslag sikrer ikke, at produktion og opladning falder på samme tidspunkt.'),
 ('Vedligeholdelse','Hvad koster vedligeholdelse pr. kilometer?','/#beregner-15','Fordel dit eget årlige vedligeholdelsesbudget på dine kilometer.','Dit budget skal passe til din bil; det er ikke en garanti for fremtidige reparationer.'),
 ('Årlig energiforskel','Hvad betyder energien for dit årsbudget?','/#beregner-17','Sammenhold de årlige energiudgifter i dine egne scenarier.','En energiforskel er ikke automatisk en besparelse på hele bilbudgettet.'),
 ('Besparelse pr. måned','Hvad svarer dit årsoverslag til pr. måned?','/#beregner-20','Fordel en selvvalgt årlig besparelse på 12 måneder, og brug beløbet i dit budget.','Det er en fordeling af dit input, ikke en uafhængig garanti for besparelse.'),
 ('Længere tur','Skal du køre langt? Start med dit eget forbrug','/beregnere/koeretur/','Regn på turens strømudgift med dine kilometer og dit forventede forbrug. Prøv et andet forbrug for at se forskellen.','Ladestop, kø, parkering og andre rejseudgifter indgår ikke automatisk i strømoverslaget.'),
 ('Energi til turen','Hvor mange kWh kræver køreturen?','/#beregner-19','Se energibehovet til et selvvalgt antal kilometer og et selvvalgt forbrug.','Energibehov er ikke det samme som en fuld rute- eller ladestopplan.'),
 ('Værditab','Hvad betyder dit skøn over værditab?','/#beregner-16','Prøv at ændre købsprisen og perioden, og se hvordan det generelle estimat påvirker regnestykket.','Modellen er et generelt estimat og kan ikke forudsige den konkrete salgspris.'),
 ('Historisk model','Brugt elbil? Brug din egen købspris','/','Find en relevant historisk model, fx Kia e-Soul, når den findes i bilvalget, og indtast din faktiske købspris.','Historiske oplysninger er daterede, og manglende specifikationer må ikke gøres til nul.'),
 ('Ladetab','Hvad betyder ekstra strømforbrug ved opladning?','/beregnere/ladepris/','Prøv med og uden et selvvalgt ekstra strømforbrug, og se forskellen i prisen.','Procenten er dit valg til eksemplet, ikke en påstand om alle ladere eller alle biler.'),
 ('To biler','Sammenlign to biler med samme forudsætninger','/','Brug samme kilometer og energipriser, og tilpas bilernes egne forbrugstal, før du sammenligner.','Vejledende katalogdata skal passe til den præcise variant, du vil undersøge.'),
 ('Dit værktøj','Find den beregner, du faktisk har brug for','/beregnere/','Vælg mellem de 20 beregnere, find din bil som udgangspunkt, eller brug dine egne tal.','Vælg et værktøj, der dækker spørgsmålet; strømudgift og samlet ejerøkonomi er forskellige beregninger.'),
]

def campaign_url(path,day,kind):
    u=urlsplit(BASE+path);q=dict(parse_qsl(u.query))
    q.update(utm_source='facebook',utm_medium='organic_social',utm_campaign='daglig_'+day.strftime('%Y%m'),utm_content=day.strftime('%Y%m%d')+'_'+kind.lower())
    return urlunsplit((u.scheme,u.netloc,u.path,urlencode(q),u.fragment))

existing=json.loads((P/'CALENDAR-BASELINE.json').read_text())
by_slot={(x['date'][:10],x['type']):x for x in existing if x['providers'] and x['providers'][0]['status'] in ('PENDING','PUBLISHED')}
entries=[];days=[]
for offset in range((END-START).days+1):
    day=START+timedelta(days=offset)
    theme,title,path,explain,caveat=THEMES[offset%len(THEMES)]
    posts=[]
    for kind,hour in [('POST','10:00'),('REEL','14:00'),('STORY','19:00')]:
        old=by_slot.get((str(day),kind))
        at=old['date'][11:16] if old else hour
        # Keep an already scheduled 10:00 Reel and place the new feed post later.
        if kind=='POST' and not old and (str(day),'REEL') in by_slot and by_slot[(str(day),'REEL')]['date'][11:16]=='10:00':at='13:00'
        url=campaign_url(path,day,kind)
        caption=title+'\n\n'+explain+'\n\nPrøv gratis på hjemmesiden: '+url+'\n\nDirekte i browseren – uden login.\n\n'+caveat+'\n\n#elbil #EVBeregner'
        item={'date':str(day),'time':at,'timezone':'Europe/Copenhagen','type':kind,'theme':theme,'title':title,'destination':url,'caption':caption if kind!='STORY' else '',
              'status':'already_scheduled' if old and old['providers'][0]['status']=='PENDING' else 'already_published' if old else 'production_plan_only',
              'existing_id':old['id'] if old else None,'existing_uuid':old['uuid'] if old else None,
              'production':'reuse_existing' if old else 'original_non_heygen','heygen_generation_allowed':False,
              'format':'1080x1350 image or useful feed text' if kind=='POST' else '9:16, 12–25 sec, H.264/AAC, real website visible by second 2' if kind=='REEL' else 'one static 1080x1920 image, facebookData.type=STORY, visible 24 hours',
              'visual_brief':('Vis én konkret side og et kort forklarende budskab.' if kind=='POST' else 'Vis den ægte side fra start; vælg bil eller ret ét relevant input; vis det korrekte resultat; slut med evberegn.dk.' if kind=='REEL' else 'Ét lodret stillbillede med dagens spørgsmål, en rigtig model-/beregnervisning og evberegn.dk. Ingen Reel-publicering.'),
              'quality_note':caveat,'existing_media':old['media'] if old else []}
        posts.append(item);entries.append(item)
    days.append({'date':str(day),'theme':theme,'items':posts})

plan={'created':'2026-11-14','timezone':'Europe/Copenhagen','start':str(START),'end':str(END),'daily_target':{'POST':1,'REEL':1,'STORY':1},'target_items':len(entries),
      'production_is_not_publication':True,'publishing_limit':{'last_known_plan':'Metricool Free','monthly_publications':20,'source':'https://help.metricool.com/main-differences-between-free-and-paid-plans-bl0v9','budget_changes_authorized':False},
      'heygen':{'november_new_generations':0,'december_maximum_attempts':3,'managed_by':'separate December automation','tentative_publication_dates':['2026-12-07','2026-12-17','2026-12-27'],'require_actual_quota_reset':True,'if_not_available':'use a non-HeyGen screen demonstration instead','never_extra_daily_slot':True},'days':days}
(P/'DAILY-PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
with (P/'DAGLIG-KALENDER.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['date','time','type','theme','title','status','existing_uuid','destination','caption']);w.writeheader();w.writerows({k:item[k] for k in w.fieldnames} for item in entries)

md=['# EV Beregner – daglig Facebook-plan','',f'Periode: {START}–{END}. Én POST, én REEL og én STORY pr. dag som produktionsmål. {len(entries)} planlagte indholdspladser; dette er ikke en kvittering for udgivelse.','',
'## Daglig rytme','','| Tid, dansk | Format | Opgave |','|---|---|---|','| 10.00 | Opslag | Ét konkret spørgsmål, en nyttig forklaring og link til hjemmesiden. |','| 14.00 | Reel | Kort demonstration af den ægte hjemmeside og ét resultat. |','| 19.00 | Story | Ét lodret stillbillede med én pointe og evberegn.dk. |','',
'Eksisterende publiceringstider bevares. 15. og 26. november ligger den eksisterende Reel kl. 10; dagens ekstra opslag foreslås kl. 13. Opladningsreelen 18. november forbliver kl. 12. Ingen dubletter.','',
'## Første uge','','| Dato | Tema | Opslag | Reel | Story |','|---|---|---|']
for day in days[:7]:
    slots={x['type']:x for x in day['items']}
    cell=lambda k:slots[k]['time']+(' – allerede planlagt' if slots[k]['status']=='already_scheduled' else ' – materiale skal produceres')
    md.append('| '+day['date']+' | '+day['theme']+' | '+cell('POST')+' | '+cell('REEL')+' | '+cell('STORY')+' |')
md+=['','## Produktion uden HeyGen','','Hele november og hovedparten af december laves med rigtige skærmbilleder, korte skærmdemonstrationer, kontrolleret typografi og original/klart licenseret lyd. Ingen AI-tegnet hjemmeside, opdigtede kundeudtalelser eller ubekræftede bilpriser.','',
'Reelen viser hjemmesiden senest efter to sekunder. En Story er et særskilt stillbillede i historiefeltet, ikke en genudgivet Reel. Brug den præcise stavning EV Beregner, gratis og evberegn.dk. Vis især bilvalg → modelside/billede → relevant beregner med bilens data og egne input.','',
'## HeyGen i december','','Højst tre nye generationer/forsøg i december, aldrig før december og aldrig flere end den faktiske ledige kvote. Den særskilte decemberopgave kontrollerer nulstillingsdatoen. Filmene erstatter tre af de almindelige daglige Reels. Foreløbige udgivelsesdatoer er 7., 17. og 27. december; hvis kvoten eller kvaliteten ikke er klar, bruges en lokal skærmdemonstration den dag. Ingen køb eller opgraderinger.','',
'## Udgivelse og den konkrete grænse','','Den hidtil anvendte Metricool Free-plan tillader 20 faktiske publiceringer pr. kalendermåned på tværs af formater. Tre daglige udgivelser kræver 90–93 om måneden. En API-forbindelse hæver ikke grænsen. Kalenderen viser 5 udgivne og 8 kommende novemberudgivelser på kontroltidspunktet; en kontovisning kan indeholde yderligere forbrug.','',
'Daglig produktion kan fortsætte gratis. Fuld automatisk udgivelse af alle tre formater afventer en udgivelsesvej med tilstrækkelig kapacitet. Den gratis mulighed er at bruge de færdige filer og tekster i Meta Business Suite; det kræver brugerens planlægning dér, fordi der ikke er en tilsluttet native Meta-udgivelsesforbindelse i denne chat. Et selvvalgt, selvbetalt Metricool-abonnement med tilstrækkelig kapacitet er en anden mulighed. Intet abonnement er ændret eller købt.','',
'Den daglige opgave må kun planlægge inden for den kendte kvote og skal regne både udgivet og allerede reserveret indhold med. Den må aldrig fremstille et udkast, en CSV-række eller en produceret fil som et planlagt/udgivet opslag. Kvittering og kalender i tjenesten er sandhedskilden.','',
'## Kontrol og opfølgning','','Kontrollér stavning, faktiske beregninger, billedrettigheder, mobilvisning og destination før planlægning. Alle priser er daterede kilder eller udtrykkelige regneeksempler. Energiudgift er ikke total ejerøkonomi. Billeder kan mangle eller vise andet udstyr.','',
'Nye links bruger utm_source=facebook og utm_medium=organic_social før eventuelle #fragmenter. Følg reelle linkklik og samtykkebaserede Metricool-webbesøg og trafikkilder. Ingen købt trafik, annonceklik eller testbeacons. Brug resultater til at forbedre emner og åbninger, ikke til at opfinde vækst.','',
'## Filer','','DAILY-PLAN.json indeholder alle dagsbriefs og eksisterende kalender-ID’er. DAGLIG-KALENDER.csv er en oversigt, ikke en garanti for import i Meta Business Suite. Færdige dagsfiler og verificerede kvitteringer opbevares særskilt.']
(P/'DAGLIG-FACEBOOK-PLAN.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'days':len(days),'content_slots':len(entries),'existing_scheduled':sum(x['status']=='already_scheduled' for x in entries),'production_plan_only':sum(x['status']=='production_plan_only' for x in entries),'heygen_calls':0},ensure_ascii=False))
