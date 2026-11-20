# Optimering af EV Beregner, 20. november 2026

Ændringen bevarer sidens mørke/turkise udtryk, de 20 oprindelige beregnere, eksisterende adresser, historiske modeller, kildeforbehold og alle godkendte billeder/licenser.

- Efter bilvalg vises strømudgift pr. km, 100 km, måned og år samlet. Besøgende kan ændre kilometer, forbrug og samlet elpris samt kombinere egne hjemme- og udepriser efter andel af ladet energi. En timepris er ikke et årsgennemsnit. Resultatet dækker kun strøm og henviser videre til det samlede budget og leasing/køb.
- De relevante indtastninger følger med til de eksisterende beregnersider i deres validerede URL-fragmenter. Egne priser overskrives ikke af forsinkede prisopslag eller skift af elområde. Manglende forbrug må ikke blive til nul eller præsenteres som dokumenterede bildata.
- Bilens eksisterende godkendte billede hentes først efter bilvalg. Fotograf, licens, originalkilde og variantforbehold genbruges fra modelsiden. Der er ingen ny billedleverandør, billedbeskæring eller licensændring.
- Mobilfiltrene fylder mindre, og tom plads over forsiden er fjernet. Logo, farver, hero og beregnerkort bevares. Domænet evberegn.dk står tydeligt ved navnet.
- Bilvælgeren på de ti selvstændige beregnersider får søgning. Filtrering bevarer den valgte bil og de indtastede tal. Ingen match må ikke slette et resultat.
- Bilkort er tastaturbetjente knapper. Beregnerdialogen understøtter fokus, Tab, Enter og Escape. Der tilføjes genvej til hovedindhold og danske decimalkommaer i forsideresultaterne. Meget store tal må ikke give Infinity som resultat.
- Sammenligningens modellinks bygges som DOM-links. Den tidligere bogstavelige `${modelSlugs[...]}`-adresse fjernes fra kilden; en ukendt adresse skal fortsat svare 404. En 404-side i det eksisterende design giver brugbare veje tilbage uden at blive til en falsk HTTP 200-side.
- Generatoren bevarer søgefelt, scripts og metadata ved næste automatiske opdatering. Sitemap omfatter fortsat 214 kanoniske adresser; ufuldstændige modeller beholder noindex.
- Den daglige kontrol den 20. november, kørsel 44752347175, stoppede på HTTP 503 for et MG-billede. Læseforespørgsler får nu højst tre korte forsøg ved midlertidige fejl. Permanente 404/403 og vedvarende 503 bliver ikke godkendt som succes. Lange Retry-After-blokeringer medfører ingen blinde genforsøg.

## Validering før udgivelse

De eksisterende kilde-, matematik-, metadata-, sitemap-, billed- og genopbygningskontroller er kørt. De lokale browserkontroller omfatter alle 20 beregnere, de ti selvstændige sider, 400 katalogcases, historiske biler, centrale brugerforløb, deling/PDF og statistikvalg. De nye brugerforløb kontrolleres ved 320, 390, 768 og 1440 pixels, herunder blandede ladepriser, nul og negative elpriser, ugyldige tal, manglende bildata, billedkreditering, bevarede indtastninger og tastaturbetjening. Syv isolerede HTTP-tests beskytter genforsøg og reelle fejltilstande.

PR-kontrollen og en kontrol af den faktisk offentliggjorte version skal være bestået, før ændringen beskrives som udgivet. PDF-test i en automatiseret browser dokumenterer ikke løsningen på ejerens tidligere konkrete telefonproblem.

Der er ingen nye eksterne analysekald, køb eller sociale udgivelser. Tekniske browserkontroller blokerer statistik og annoncer. IndexNow-kvitteringer betyder modtagelse, ikke indeksering. Ingen effekt på klik, placeringer eller indtjening påstås.
