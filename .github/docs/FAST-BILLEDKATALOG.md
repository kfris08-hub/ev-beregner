# Faste modelbilleder

`data/model-photos.json` kobler en modelsides URL til et lokalt WebP-billede i `assets/cars/`. Filnavnet indeholder billedets SHA-256-præfiks. Hjemmesiden søger ikke efter billeder hos Wikimedia eller Wikipedia, og browserens gamle billedcache anvendes ikke længere.

Billedet, dets dimensioner, alternativtekst og kreditering står direkte i HTML. Det samme billede bruges i Open Graph, WebPage/ImageObject-data og billedsitemap. `assets/car-images.js` håndterer kun en eventuel fejl ved indlæsning af den lokale billedfil.

Billederne er udvalgt efter model/karrosseri, visuel gennemgang og kildeoplysninger. Fotograf, kilde, licens, kontroltidspunkt, filhash og formatændring er registreret. Billedteksten oplyser, at udstyr, farve og fælge kan afvige; billeder af samme bil under et andet markedsnavn forklares særskilt. Der bruges CC BY, CC BY-SA, CC0 eller public domain, bortset fra det officielle GLA-pressefoto, som bruges redaktionelt efter Mercedes-Benz Medias vilkår og krediteres særskilt. CC BY-SA gælder billedet; en fil i et nyt format beholder sin oprindelige licens. Den tyske udgave af CC BY-SA 3.0 er bevaret, hvor kilden bruger den.

Ved udskiftning: kontrollér det præcise motiv og brugsretten, gem den nye billedfil, opdatér manifestets kilde/kreditering/licens/hash/dimensioner, og kør `python tools/render_model_photos.py`. Et billede må kun have status `verified`, når det er gennemgået; en side uden et egnet billede har status `missing` med en begrundelse. Status `withdrawn` bruges til de fire noindex-forklaringssider, og `redirect` bruges til IONIQ 7-henvisningen. De tilføjes ikke til billedsitemap. Der må ikke indsættes et vilkårligt billede for at opnå fuld dækning.

Kontrol før publicering:

- `python tests/seo_checks.py`
- `python tests/model_photo_checks.py`
- `node tests/calculators.test.cjs`
- `python tests/browser_checks.py`
- `python tests/photo_browser_checks.py`

Den sidste kontrol gennemgår alle 186 modelsider med JavaScript slået fra, indlæser de faktiske billedfiler og kontrollerer også håndteringen af en manglende fil. Med `PHOTO_PUBLIC=1` kontrollerer den den offentlige hjemmeside. Browserkontrollerne kræver Playwright og Chrome. Listen over modeller, der endnu mangler et egnet billede, findes i `BILLEDDÆKNING.md`.
