# Brændstofpriser

Benzin og diesel bruger nu faktiske offentlige pumpepriser fra OKs officielle API: https://mobility-prices.ok.dk/api/v1/fuel-prices

Dokumentation: https://www.ok.dk/globalassets/pdfer/diverse/offentlig-api-dokumentation.pdf

## Hvad prisen betyder

Der beregnes ét uvægtet gennemsnit pr. produkt. Hver OK-station tæller én gang. Kun »Blyfri 95« og »Svovlfri Diesel« indgår; Oktan 100, premium- og alternative produkter indgår ikke. Det er et gennemsnit af OK-stationer, ikke et landsgennemsnit, den billigste pris eller brugerens lokale pumpepris. Pris og dækning vises med kilde og faktisk kontroltidspunkt. Brugeren kan fortsat angive egne priser i beregnerne.

Den tidligere kilde, Drivkraft Danmark, angiver vejledende priser fra foregående dag. Den var derfor ikke egnet til at blive vist som aktuelle pumpepriser. Den gamle import satte samtidig dagens dato på kildens pris. Begge forhold er ændret.

## Automatisk kontrol

Workflowet forsøger at hente priser hver time. GitHub kan forsinke planlagte kørsler. Data er et kontrolleret snapshot, ikke en garanti for realtid på den enkelte station. En ny indlæsning får sit faktiske kontroltidspunkt; kildens stationsopdateringer opbevares separat.

Data kræver gyldige stations-id'er og tidsstempler. Stationer med opdateringer ældre end 72 timer eller mere end ti minutter i fremtiden udelades. Priser skal ligge i intervallet 5–60 DKK/l. Der kræves mindst 200 stationer pr. standardprodukt; et fald på mere end 25 % fra sidste dækningsantal stopper udgivelsen. Dubletter tæller én gang, og modstridende dubletter stopper importen. Ved kildefejl udskiftes sidste kontrollerede fil ikke.

Browseren afviser listepriser, forkert valuta/enhed, manglende dækning og snapshots ældre end 48 timer. Fejl vises som eksempelpriser; gamle eller udokumenterede priser kaldes ikke aktuelle pumpepriser. Forside, modelsidernes statiske regneeksempler og prisopslag bruger samme datasæt. De fem beregnerlandingssiders generelle eksempler forbliver tydeligt mærkede eksempler, indtil brugeren aktivt henter priser.

Datakilde, udregning, alle beregnere, metadata og brugerforløb kontrolleres før commit og udgivelse. Designet og alle 20 beregnere er bevaret. Der er ingen betalt tjeneste eller API-nøgle.
