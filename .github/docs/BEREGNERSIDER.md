# De fem beregnersider

Forsidens 20 værktøjer er bevaret. Fem har desuden en selvstændig adresse under `/beregnere/`: ladepris, elbil-vs-benzin, opladningstid, leasing-vs-koeb og samlet-biloekonomi.

`assets/calculators.js` indeholder de fælles feltdefinitioner, validering og formler for disse fem værktøjer på både forsiden og de nye sider. De øvrige 15 bruger fortsat forsidens kode.

Tekst, kilder, forklaringer og eksempelværdier vedligeholdes i `data/calculator-pages.json`. Kør `python tools/build_calculator_pages.py` efter ændringer. Bygningen bruger Node til at beregne de statiske eksempler med samme formler som browseren. Den opdaterer også bilvalgets JSON fra forsidens aktive biloversigt og tilføjer de fem adresser til sitemap. CSS, formularstyring og kildetekster vedligeholdes separat; hele hjemmesiden skal ikke bygges om.

Bilvalg overføres med fragmentet `#bil=modelslug`. Canonical og sitemap bruger altid beregnerens rene adresse. Ukendte specifikationer erstattes med tydeligt beskrevne, redigerbare eksempler. Maksimal DC-effekt bruges ikke som gennemsnitlig ladeeffekt. Restværdier er brugerens skøn.

Kør `python tests/seo_checks.py`, `python tests/model_photo_checks.py`, `python tests/calculator_page_checks.py`, `node tests/calculators.test.cjs` og `node tests/calculator_math.test.cjs`. GitHub Actions afprøver desuden alle 20 eksisterende værktøjer og de nye sider i Chrome på mobil og desktop. De nye sider testes også uden JavaScript. Eksterne prisopslag er kontrollerede testdata. Med `CALCULATOR_PUBLIC=1` henter de to beregner-browsertests HTML og egne assets fra den udgivne hjemmeside, mens prisdata stadig styres af testen.

Der er ikke tilføjet analyseværktøjer eller nye annoncenetværk. Den eksisterende annonceenhed anvendes under formularen. Indeksering, placeringer og annonceindtægt skal følges i Search Console og annonceplatformen efter udgivelsen; de kan ikke udledes af funktionstests.
