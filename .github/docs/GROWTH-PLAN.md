# Drift og vækst for EV Beregner

Ejerens mandat 11. november 2026: Arbejd selvstændigt med IT og marketing for at skabe flere relevante besøgende og bedre brug af siden. Almindelige testede forbedringer på det eksisterende domæne kan udgives. Design, de 20 oprindelige beregnere, eksisterende adresser og historiske modeller bevares.

## Første vækstrunde

- Fem nye selvstændige beregnere: pris pr. km, elbil mod diesel, turens energi/pris, rækkevidde og årligt strømforbrug. De supplerer fem eksisterende sider. Hver har egen beregning, gennemregnede eksempler og tydelig afgrænsning.
- /beregnere/ samler alle 20 værktøjer i almindelige links, også uden JavaScript. Forsiden får korte genveje; bilvalget følger med til relevante værktøjer.
- Besøgende kan selv dele en beregning med de samme tal eller udskrive den. Tal i et delt link ligger i URL-fragmentet. Ukendte nøgler, ugyldige tal og dobbelte parametre afvises. Senere modelopslag må ikke overskrive delte eller egne værdier.
- Nye billeder til linkvisning følger sidens eget design. Der bruges ingen lånte annoncer eller opdigtede vurderinger.
- Den eksisterende annonce flyttes væk fra forsiden før overskrift og værktøjer. Der tilføjes ingen ny annonceudbyder, klikopfordring eller skjult reklame.
- /om/ beskriver metoder, data og begrænsninger uden opdigtede personnavne, ekspertuddannelser eller virksomhedskontakt.
- En reel fejl rettes: build_calculator_pages.py må ikke fjerne price_status fra fælles bilpresets. Ubekræftede prisbeløb skal også mærkes katalogpris i beregnersiderne.
- En daglig kontrol gennemgår offentlig tilgængelighed, links, metadata og kildernes alder.
- IndexNow underretter deltagende søgemaskiner om ændrede kanoniske adresser efter kontrol af ejerskabsfil og offentliggjort sitemap. Kvittering er ikke indeksering. Det er ikke Googles generelle indekserings-API.

## Drift og måling

Benzin/diesel og bilkatalog har eksisterende automatiske opdateringer. GitHub kan forsinke planlagte job. En godkendt opdatering må først beskrives som offentliggjort efter en kontrol på www.evberegn.dk.

Den tilgængelige GitHub-forbindelse giver ikke adgang til aktuelle Search Console-, Analytics- eller annoncekontotal. Offentlige site:-søgninger er ikke dækkende indekseringsdata og kan ikke bruges som klik-, impressions- eller indtægtstal. Vækst skal vurderes på faktiske data, hvis adgang senere bliver tilgængelig. Indtil da rapporteres konkrete ændringer og observerede tekniske forhold; der opfindes ingen effektmålinger.

Ingen køb af trafik, annoncer eller tjenester uden særskilt budget. Ingen automatiske opslag, e-mails eller beskeder på fremmede konti. Ingen kunstige besøgende, annonceklik, linkspam eller masseproduktion af tynde sider.

## Løbende arbejde

Prioriter nyttige eksisterende sider, hurtig adgang til en beregning, korrekte eksempler, kildekvalitet og intern navigation. Tilføj kun nye sider, når de løser et selvstændigt brugerbehov. Fjern ikke noindex fra ufuldstændige modeldata alene for at øge antallet af sider.

Brug PR og relevante kilde-/browsertests. Udgiv inden for mandatet, og bekræft den offentlige side. Bevar kanoniske adresser og links, og undgå nye ændringsdatoer ved uændrede genbygninger.

Officiel baggrund:
- https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- https://www.indexnow.org/documentation

