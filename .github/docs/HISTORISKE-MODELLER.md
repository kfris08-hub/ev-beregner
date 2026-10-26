# Tidligere elbilmodeller

`data/historical-cars.json` indeholder producentdokumenterede, tidligere modeller. De indgår sammen med nye biler i `data/cars.json`, bilvalg, sammenligning, beregnere og sitemap. At en bil ikke længere står i en nybilprisliste, sletter ikke dens side eller tekniske data.

De første to poster er Kia e-Soul 39,2 kWh og 64 kWh fra lanceringen i 2019. Kia Import Danmarks pressemeddelelse fra 3. maj 2019 dokumenterer batteri, WLTP-rækkevidde og blandet forbrug for begge drivlinjer: 39,2 kWh / 276 km / 156 Wh/km og 64 kWh / 452 km / 157 Wh/km. Forbruget omregnes til 15,6 og 15,7 kWh/100 km. Udstyr og senere modelår er ikke sammenblandet. Kilden er kontrolleret 26. oktober 2026; offentliggørelsesdatoen bevares som 3. maj 2019.

Kilde: https://www.mynewsdesk.com/dk/kia-motors-denmark/pressreleases/kia-praesenterer-modelprogrammet-paa-den-nye-e-soul-2865057

## Priser og ladning

Den historiske nypris må ikke bruges som aktuel købspris eller som brugtpris. Derfor er `price` tom, og prisafhængige beregnere kræver brugerens egen købspris. Alle 20 beregnere og deres formler er bevaret. Generelle eksempelværdier for øvrige økonomiposter kan fortsat redigeres.

Kilden nævner opladning ved en 100 kW ladestander. Det dokumenterer ikke bilens maksimale DC-effekt; `charging` er derfor tom. Oplysninger om batteriets brutto-/nettobasis er ikke opfundet. Der anvendes en tydelig pladsholder, indtil et billede er verificeret.

## Automatisk bevaring

Den fælles indlæser `tools/car_catalog.py` sammenlægger det aktuelle katalog med arkivet før import og sideopbygning. Historiske poster har `availability: discontinued`, men er stadig aktive i beregnernes bilvalg. Nye prisfeeds må ikke overskrive deres tekniske data eller sætte en aktuel pris på dem. En relancering må oprettes som en anden variant.

Tilføjelse af yderligere ældre modeller kræver en dokumenteret variant og kilde første gang. Derefter bevares den dagligt uden ejerens godkendelse. Arkivet er ikke en automatisk, komplet registrering af alle tidligere elbiler. NEDC-tal accepteres ikke i WLTP-feltet.

Modelsiderne har en kort markering af årgang og tidligere model. Kildeoplysningerne ligger under »Kilder og datoer«. Designet er bevaret, og introduktioner er ikke gjort længere.

Testene omfatter genindlæsning, uændrede arkivposter efter prisimport, NEDC-afvisning, tomme købsprisfelter, begge varianter i alle 20 beregnere og mobil/desktop med og uden JavaScript. Søgning efter både »Kia e-Soul« og »Kia e soul« finder modellerne.
