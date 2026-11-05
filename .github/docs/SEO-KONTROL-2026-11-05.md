# SEO-kontrol 5. november 2026

## Hvad Search Console-billedet viser

Billedet viser 23 klik og cirka 1.430 eksponeringer over 28 dage. Det tidligere billede viste 34 klik og 861 eksponeringer. Klik er cirka 32 % lavere; eksponeringer er cirka 66 % højere. Den omtrentlige klikrate er faldet fra 3,95 % til 1,61 %. Det er to overlappende 28-dagesperioder, ikke en kontrolleret før/efter-måling. De sidste dage på den nye graf ser svagere ud, men totalerne viser ikke et fald i eksponeringer over hele vinduet.

Billedet viser hverken indekseringsårsager, søgeord, landingssider eller gennemsnitsplaceringer. Den konkrete årsag til de oplyste 149 ikke-indekserede sider er derfor endnu ikke dokumenteret. Der er bedt om Search Consoles præcise årsagskategori.

## Kontrol af den offentliggjorte side

Kontrollen før rettelsen omfattede 240 HTML-sider, 201 canonical-adresser i sitemap, 193 lokale assets, 2.671 interne linkforekomster og 181 billedmetadataobjekter. Den samlede HTTP/metadata/link-kontrol gav ingen fejl og ingen advarsler. Alle 20 beregnere, de fem beregnerlandingssider og de centrale offentlige brugerforløb bestod browserkontrollen.

En separat billedgennemgang mødte én HTTP 503 på /elbil/polestar-2-long-range-single-motor-rwd/. Den fulde crawl fik ikke denne fejl. Kontrollen gentages særskilt for at afgøre, om den kan gentages; et enkelt 503-svar dokumenterer ikke en vedvarende blokering for Google.

Det aktuelle katalog før genoptagelse indeholder 228 valgbare varianter. Af dem er 194 modeller indexable og 34 prisbaserede modeller bevidst noindex, fordi tekniske data mangler. Dertil kommer fire tidligere udtagne varianter med noindex og én gammel IONIQ-adresse med canonical/viderestilling. De bevidst udeladte sider indgår ikke i sitemap. De 34 kan ikke automatisk sidestilles med Search Consoles gruppe på 149.

## Bekræftede fejl og rettelse

1. Bilopdateringen har ikke udgivet en vellykket opdatering siden 27. oktober. Kilderne blev hentet, men en browserkontrol stoppede før commit og udgivelse. Ved 320 pixels blev bilkortene 4 pixels for brede, når nye lange modelnavne blev tilføjet. Rettelsen lader gridsporet krympe og modelnavnene bryde linjer, mens priserne forbliver læselige. Ingen testgrænser sænkes, og hele siden får ikke skjult vandret overløb.
2. Forsidens og biloversigtens lastmod blev bevaret fra et ældre sitemap, selv når kataloget og HTML-indholdet ændrede sig. Rettelsen opdaterer disse datoer, når det faktiske sideindhold ændres. Uændret genopbygning må ikke give en ny dato. Ændringsdato er et signal til Google, ikke en garanti for crawl eller indeksering.

Rettelserne genoptager vedligeholdelsen og gør sitemapdatoerne præcise. De dokumenterer ikke årsagen til klikfaldet eller alle 149 uindekserede sider.

## Prioriteret videre arbejde

- Match Search Consoles indekseringsårsager og konkrete eksempler med de tilsigtet indexable URL'er. Ved »Opdaget« undersøges opdagelse og Googles crawl; ved »Crawlet« gennemgås især sidernes selvstændige nytte, variantidentitet og kildegrundlag. Fejl på canonical, noindex eller HTTP skal løses ud fra de faktiske eksempler.
- Prioritér dokumenterede data på de modelsider, der allerede får eksponeringer. 139 af de 194 indexable modelposter har ingen registreret kilde pr. datafelt. Det er en dokumentationsmangel, ikke bevis for at alle tal er forkerte. Et større antal sider løser ikke denne mangel.
- Gennemgå klikrate pr. søgeord og side i Search Console. 143 af de 194 modeltitler er længere end 65 tegn. Google har ingen fast grænse på 65 tegn, og længden er ikke en indekseringsblokering. Lange eller gentagne variantnavne er dog konkrete kandidater til en mere præcis titel, især ved mange eksponeringer og få klik. Titler ændres målrettet efter de faktiske søgninger.
- Bevar korte introduktioner og alle 20 beregnere. Prioritér korrekte variantdata, korte nyttige regneeksempler og tydelige kilder frem for mere generisk forklarende tekst.
- Følg ikke-indekserede grupper, klikrate og eksponeringer på de samme sider over sammenlignelige perioder. Google træffer selv beslutningen om indeksering; teknisk tilgængelighed eller en sitemapindsendelse lover ikke indeksering.

Kontrol af publiceret baseline: https://github.com/kfris08-hub/ev-beregner/actions/runs/42066741352
Prøveopdatering med mobilrettelsen: https://github.com/kfris08-hub/ev-beregner/actions/runs/42067305354
