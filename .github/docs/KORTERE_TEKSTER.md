# Kortere tekster og forklaringer efter behov

Forsiden bruger korte beskrivelser og én indgang til metode, kilder og forudsætninger. Gentagne generelle forbehold er samlet dér, og de gentagne automatisk-indsat-tekster under hvert beregnerfelt er fjernet. Beregnernavne, feltbetegnelser, værdier, fejlbeskeder og de nødvendige markeringer af ubekræftede data er bevaret.

På de fem selvstændige beregnersider er introduktionerne forkortet. Felthjælp er samlet under Hjælp til felterne. De eksisterende, unikke regneeksempler, formler, forklaringer og kildehenvisninger er bevaret under Eksempler, metode og kilder. Det er almindelige HTML details/summary-elementer; hele indholdet findes i serverens HTML og kan åbnes uden JavaScript. Valideringsfejl vises fortsat direkte ved det relevante input. Hjælpeteksterne beholder deres id og forbindelsen via aria-describedby.

På modelsiderne er prisstatus og generelle overskrifter kortere. Forbrugsenheden gentages ikke længere både i tallet og i overskriften. Fotograf, licens, kilde, billedændringer, særskilte modelbemærkninger, producentkilder og ImageObject-metadata er ikke fjernet.

tools/simplify_copy.py opdaterer forside og aktive modelsider idempotent. tools/build_calculator_pages.py bygger de fem beregnersider fra data/calculator-pages.json. Kør dem i den rækkefølge efter en genopbygning. De fælles beregningsformler og bilernes tal ændres ikke af tekstoprydningen.

De eksisterende kontroller af SEO, billedkilder, metadata og alle beregnere køres fortsat. Browserkontrollen af de fem beregnersider afprøver desuden de nye fold-ud-felter med og uden JavaScript.

Baggrund for almindelige fold-ud-felter som brugergrænseflade: https://developers.google.com/search/docs/essentials/spam-policies#hidden-text-and-link-abuse . Google skelner mellem nyttige accordions til brugere og indhold, som skjules for at manipulere søgninger. Der vises samme HTML til brugere og søgemaskiner. Dette er ikke en garanti for placering eller indeksering.
