# Besøgsstatistik i Metricool

Opsat efter ejerens sporingskode 14. november 2026. Brand: 8064733.
Målingen gælder nye besøg efter aktivering og besøgendes tilladelse.
Historiske besøg kan ikke genskabes, og visninger på Facebook er ikke webbesøg.

Den leverede be.js blev læst fra tracker.metricool.com uden at sende et
sporingskald. Den 379-byte version bruger c3po.jpg med hash, u, bw, bh og ref.
Kontrolleret SHA-256:
b4e62a8daa779d16b2c25d343db85f6501e334632b0eeafd7d9f5bc5b8f96367.

assets/website-stats.js bruger samme pixelprotokol lokalt, men sender først
efter aktiv tilladelse. Requesten sendes uden cookies/credentials eller
automatisk Referer-header. Statistikken modtager kun sidens origin/sti,
fire tilladte UTM-parametre, vinduets mål og henviserens origin. Delte
beregningsværdier, e-mailparametre, øvrige queries og fragmenter sendes ikke.
Sidens aktuelle URL og delingsfunktioner ændres ikke.

Valget gemmes lokalt under evberegn_stats_choice_v1 og kan ændres via
Statistik nederst på siden. Afvisning påvirker ingen beregnere. DNT, GPC
og automatiserede webdriver-browsere sender ingen statistik. Blokeret
lager eller tracker må ikke give fejl i de eksisterende brugerforløb.
Annoncenetværkets eksisterende kode er ikke ændret af denne integration.

Der indsættes ét defer-script i normale HTML-dokumenter og modelskabelonen.
Redirect- og Google-verifikationsfiler må ikke måle en ekstra sidevisning.
Beregnersidegeneratoren bevarer scriptet og statistikafsnittet i Om og kilder.

Kontrollér i Metricool under Analyse → Web/Blog: besøg, sidevisninger og
trafikkilder. Trafikkilden kan mangle, når en browser ikke sender en henviser.
Brug fremover UTM-mærkede links fra Facebook med utm_source=facebook og
utm_medium=organic_social; bevar eksisterende query- og beregningsfragmenter.
UTM-parametre hjælper tilskrivning, men garanterer ikke at en besøgende kan
måles. Opdateringstider og samtykke skal med i vurderingen af tal.

tests/analytics_browser_checks.py blokerer alle rigtige Metricool-kald og
kontrollerer samtykke, afvisning, tilbagetrækning, private URL-værdier,
trafikkilde, dubletter, DNT/GPC og fejl i lager/netværk. Ingen test må
opfinde besøg eller blive fremstillet som organisk trafik.
