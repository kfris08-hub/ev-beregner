# Billedmetadata: creator og copyrightNotice

Search Console meldte 25. oktober 2026 om de to manglende anbefalede felter i ImageObject. Fotograf, billedkilde og licens var allerede registreret i data/model-photos.json og vist ved hvert billede. Google angiver felterne som anbefalede, når andre understøttede rettighedsfelter allerede er udfyldt. Advarslerne er derfor ikke i sig selv en blokering af indeksering.

Alle 181 aktive modelsider har nu creator med type og navn samt copyrightNotice. Den korte kildeangivne attribution bruges som navn, hvor den findes, ellers bruges fotografnavnet fra manifestet. Det fjerner eksempelvis kontakt- og licenstekst fra selve navnet for Oleg Yunakov. Ophavsretssymbolet fjernes fra creator.name, mens kildens eksisterende copyright-angivelse bevares i copyrightNotice. De registrerede publiceringskanaler og Mercedes-Benz' officielle pressefoto angives som Organization.

For CC-billeder uden en særskilt copyright-angivelse kombinerer copyrightNotice kildens navn og den registrerede licens. Der opfindes hverken en ny rettighedshaver, et årstal eller ophavsret til EV Beregner. De 17 CC0-billeder beskrives særskilt som CC0 1.0 Universal med public domain-dedikation, uden et nyt copyright-symbol.

Fælles generering ligger i tools/photo_rights.py og bruges både af den almindelige billedskabelon og tools/update_image_metadata.py. Sidstnævnte opdaterer kun de to felter i eksisterende JSON-LD og lastmod for de 181 berørte sitemapadresser. Den ændrer ikke den synlige HTML, billedfiler, billedadresser, krediteringer, licenser, beregnere eller de fire udtagne varianter og IONIQ-omdirigeringen.

Kør python tools/update_image_metadata.py efter ændringer i de gennemgåede kildekrediteringer. Med --check kontrolleres det, at de genererede felter er ajour. Kør python tests/image_metadata_checks.py for at kontrollere kildehenvisninger, creator, copyrightNotice, CC0-angivelser og udeladte modeller. GitHub Actions kontrollerer desuden billederne, SEO og alle beregnere. Billedtesten i Chrome kontrollerer felterne direkte i HTML, også uden JavaScript. PHOTO_PUBLIC=1 bruger den udgivne hjemmeside.

Efter udgivelsen kan ejeren starte Valider rettelse under hver af de to advarsler i Search Console. Google skal genbesøge siderne, før rapporten kan opdateres; en bestået lokal test er ikke en gennemført Google-validering.

Kilde: https://developers.google.com/search/docs/appearance/structured-data/image-license-metadata
