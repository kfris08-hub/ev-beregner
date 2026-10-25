# Funktionskontrol af hele hjemmesiden

Den samlede kontrol den 25. oktober 2026 undersøger den udgivne hjemmeside og den tilsvarende kildekode. Google-indeksering og betaling hos annoncenetværket kræver desuden oplysninger fra ejerens konti.

## Rettede brugerfejl

- Generel beregning fjerner nu en tidligere valgt bil og dens car-parameter. Beregneren bruger dermed de generelle forudsætninger, når brugeren vælger denne tilstand.
- Bilvalg og fjernelse holdes sammen med adressen, så genindlæsning gendanner den aktuelle tilstand. Beregnerens hash og historik bevares.
- Beregnervinduet ligger over det eksisterende annoncefelt, også når et direkte beregnerlink åbnes ved toppen af siden. Annoncekoden og det øvrige design er bevaret.

Den eksisterende browsertest ventede tidligere kun på selectedCar != null efter navigation. Inden forsidens script var færdigt, kunne navnet pege på HTML-elementet med samme id. Testen venter nu på en faktisk bil-array med det forventede modelnavn. Det var en timingfejl i testen, ikke en dokumenteret fejl i modeloverførslen.

## Gentagelig kontrol

Workflowet Gennemgå hele den udgivne hjemmeside kan startes manuelt i GitHub Actions. Det kontrollerer kildekode og metadata, alle 193 offentlige HTML-adresser, 188 sitemapadresser, lokale filer, interne links, alle 181 aktive modelbilleder og de fem særskilte beregnersider. De fire udtagne varianter og den gamle IONIQ-adresse kontrolleres med deres tilsigtede noindex/omdirigering.

tests/full_public_flows.py kontrollerer fysisk betjening på 320, 390, 768 og 1440 pixels: søgning, danske tal i filtre, sortering, bilvalg, sammenligning af tre biler med manglende data, fjernelse, generel tilstand, tilbageknapper, direkte links, navigation og vandret overløb. Standardtilstanden bruger de udcheckede filer. FLOW_PUBLIC=1 bruger den udgivne hjemmeside. Prisopslag observeres i en separat browserkontekst mod de rigtige tjenester. Kontrolleret elpris bruges i UI- og regnetests, så de forventede beløb er stabile. Der klikkes ikke på annoncer.

tests/full_public_crawl.py kontrollerer den rigtige hjemmesides HTTP-svar, canonical, titel, metabeskrivelse, H1, JSON-LD, billedmetadata, robots.txt, sitemap, lokale assets, interne links og ankre, 404-svar samt alternative domæne-/protokoladresser. Hostingadvarsler rapporteres separat. De eksterne kilde- og licenslinks opgøres; samtlige eksterne hjemmesider gennemgås ikke.

## Afgrænsning

Et bestået teknisk tjek er ikke en garanti for Google-indeksering, annonceindtægt eller korrekte dagsaktuelle priser og specifikationer hos hver bilproducent. Brændstofdata og elprisformat kontrolleres teknisk; kundens konkrete nettariffer, leverandørtillæg og aftaler kan afvige. Browserkontrollen er Chrome på simulerede skærmstørrelser, ikke en selvstændig kontrol i alle telefoner, Safari eller Firefox. Search Console-valideringen af billedmetadata og A-Ads' levering af betalte annoncer følges i deres respektive konti.

Hostingkontrollen viste gyldigt HTTPS-certifikat for begge domænevarianter, men https_enforced=false. Ejeren skal slå Enforce HTTPS til under GitHub-repositoriets Settings → Pages; den tilsluttede adgang har ikke administrationsrettigheden til at ændre denne indstilling. Canonical, interne links og sitemap bruger allerede https://www.evberegn.dk/.
