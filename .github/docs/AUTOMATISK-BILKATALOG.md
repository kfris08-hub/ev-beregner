# Automatisk bilkatalog

`data/cars.json` er den fælles kilde til bilvalg, sammenligning, CSV, modelsider og beregnernes bildata. `tools/build_car_catalog.py` genbruger det eksisterende design og de eksisterende billeder. Alle 20 beregnere og de 181 oprindelige biladresser bevares. De fire udtagne varianter og IONIQ-omdirigeringen kan ikke genindføres af importen.

## Daglig drift uden godkendelse

GitHub Actions-workflowet `Opdater bilkatalog automatisk` kører dagligt kl. 03:43 UTC samt ved manuel start. GitHub kan forsinke planlagte kørsler. Der bruges ingen betalte tjenester, API-nøgler eller AI-tjenester.

1. Hent de tilsluttede kilder med timeout, begrænsning på filstørrelse og et ekstra forsøg ved fejl.
2. Kontrollér format, licens, dato, variantidentitet, enheder og talgrænser. En kildefejl sletter aldrig eksisterende data. Fejler alle kilder, udgives ingen ændringer.
3. Opdater dokumenterede felter og registrer deres kilde og dato. En dags kontrol af uændrede data ændrer ikke sidernes `lastmod` eller verificeringsdato kunstigt.
4. Tilføj højst 15 nye varianter pr. dag. Gentagne kørsler samme dag giver ikke flere tilføjelser. De resterende opdages ved næste dags kørsel.
5. Byg alle berørte sider og kør data-, SEO-, billed-, beregner- og browsertest. En fejl stopper før commit og udgivelse.
6. Gem beståede ændringer og anmod udtrykkeligt GitHub Pages om et build. Det er nødvendigt, fordi commits med `GITHUB_TOKEN` ikke selv starter Pages eller et nyt CI-workflow.

Kilde- og resultatrapport findes i `data/car-update-status.json`, workflowets GitHub-oversigt og artefaktet `automatisk-bilkontrol`. Ved alle-kilder-fejl gemmes fejlrapporten som artefakt, mens den offentlige rapport bevarer sidste vellykkede kørsel. Standardfejlmeddelelser fra GitHub Actions gælder fortsat.

## Faktisk dækning og afgrænsning

- Bil-Portalen stiller danske model- og variantpriser til rådighed som CC BY 4.0. Siden krediterer datakilden og linker til dens licens samt producentens prisliste. Feedets rækkevidde kan være en modelværdi for en anden variant og importeres derfor **ikke**. Batterital i et variantnavn bruges kun til identitetskontrol.
- Producenternes offentlige danske retail-API er tilsluttet for Alfa Romeo Junior, Peugeot E-208 og Peugeot E-2008. Det giver pris, variantens forbrug i Wh/km (omregnet til kWh/100 km), rækkevidde og batterikapacitet. Batteriets brutto-/nettobasis er ikke oplyst og markeres som sådan. Feltet `batteryMaxPower` importeres aldrig som DC-ladeeffekt: det kan være motoreffekt.
- Eksisterende varianter får kun en ny pris ved en udtrykkelig variantkobling eller et entydigt match af alle navnets identitetsord med batterikontrol, hvor batteriet fremgår. RWD/GT/Plus, batteristørrelse og trim må ikke forveksles. Prisændringer over 40 % tilbageholdes automatisk i rapporten; andre varianter opdateres fortsat.
- Nye modelnavne opdages fra det åbne danske feed uden godkendelse. Nye varianter med kun en dokumenteret pris kan bruges med egne tal i beregnerne, men har `noindex, follow` og er udeladt af sitemap. De bliver automatisk indexable, hvis den samme variant senere får dokumenteret pris, rækkevidde og forbrug fra en tilsluttet variantkilde.
- Manglende fotos får en tydelig pladsholder. Automatikken kopierer ikke pressebilleder eller ophavsretligt uafklarede billeder. Eksisterende 181 lokale billeder, krediteringer og billedmetadata bevares.
- Automatik betyder ikke, at alle tidligere 181 varianter har fuld datadækning. Den aktuelle prisdækning og antallet af ældre varianter uden sikker kobling fremgår af statusrapporten. For disse bevares de tidligere oplysninger, og modelsidens kildeoversigt viser, at kildedatoen mangler. Ukendte felter opfindes ikke, og manglende varianter i et feed med kun den billigste variant betyder ikke automatisk, at bilen er udgået.
- Der foretages ingen automatisk sletning af gamle URL'er. For fuld dækning af samtlige historiske udstyrsvarianter og alle tekniske felter kræves flere dokumenterede variantkilder eller en dækkende licenseret dataleverandør. Systemet lover ikke det modsatte.

## Udvikling

Kør `python tools/update_car_catalog.py`, `python tools/build_car_catalog.py` og `python tools/build_calculator_pages.py`. `--fixture-dir` på importværktøjet kan bruges til kildefejl og reproducérbare prøvekørsler uden netværk. Hentede kildefiler publiceres ikke. Tests følger det fælles katalog i stedet for faste antal modeller. `tests/car_catalog.test.py` kontrollerer blandt andet hybridafvisning, enheder, navneforveksling, prisfejl, historiske URL'er og den daglige tilføjelsesgrænse.
