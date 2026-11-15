"""Apply the approved creative direction without changing publication routes or media."""
from pathlib import Path
import copy
import json

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'daily/DAILY-PLAN.json'
MARKER = 'SAMTALE-OG-BREDERE-PUBLIKUM-20261115'
plan = json.loads(PLAN.read_text())
before = copy.deepcopy(plan)
brief = 'marketing/creative/SAMTALE-OG-BREDERE-PUBLIKUM.md'
scripts = 'marketing/creative/NAESTE-TRE-MANUSKRIPTER.md'
plan['creative_direction'] = {
    'version': MARKER,
    'owner_instruction_date': '2026-11-15',
    'brief': brief,
    'scripts': scripts,
    'reference': 'Owner-identified Reel with three adults meeting at an electric car',
    'goal': 'Retain the conversation format and test broader reach among women',
    'next_person_films': {'people': 3, 'women_in_central_roles_minimum_of_next_three': 2},
    'real_website_visible_by_second': 2,
    'website_call_to_action_seconds': [10, 15],
    'private_analytics_in_public_plan': False,
    'organic_audience_guaranteed': False,
    'new_november_heygen_generations': 0,
    'publication_routes_or_appointments_changed': False,
    'already_finished_manual_packages_preserved': ['2026-11-16', '2026-11-17'],
    'note': 'Scripts and briefs are not finished films or scheduled publications.'
}

contexts = {
    '2026-11-18': ('Hvad koster den opladning, du faktisk har brug for?', 'En kvindelig elbilejer forklarer sin ven, hvilke egne input opladningsberegningen bruger.'),
    '2026-11-19': ('Giver el mening med mine kilometer?', 'To veninder undersøger energiudgifter med samme egne forudsætninger; ingen sikker besparelse.'),
    '2026-11-20': ('Hvad sker der, hvis mit forbrug stiger?', 'En kvindelig fører undersøger forskellen i matematisk rækkevidde med sin ven.'),
    '2026-11-21': ('Jeg overvejer den her elbil. Hvad skal jeg regne på?', 'En kvinde vælger selv bil; en kvindelig ven forklarer modelvalg og relevante beregnere.'),
    '2026-11-22': ('Hvornår kan jeg køre igen?', 'En kvindelig elbilejer forklarer, at ladetid er et overslag med valgte forudsætninger.'),
    '2026-11-23': ('Hvor langt rækker det med mit eget forbrug?', 'Venner ved en elbil sammenligner to egne forbrugstal; en kvinde viser beregneren.'),
    '2026-11-24': ('Hvad bruger mine ture på et helt år?', 'En kvindelig pendler bruger egne kilometer og forbrug, uden at hendes brugsmønster gøres typisk for et køn.'),
    '2026-11-25': ('Regner jeg med den elpris, jeg selv betaler?', 'En kvindelig bilejer forklarer forskellen mellem en valgt eksempelpris og sin egen samlede elpris.'),
    '2026-11-27': ('Hvad skal bilen fylde i mit budget?', 'En kvinde undersøger sit eget budget sammen med venner; strøm og øvrige udgifter holdes adskilt.'),
    '2026-11-28': ('Kan jeg bruge min egen bil og mine egne tal?', 'En kvindelig elbilejer viser værktøjet til en mandlig ven, der er ny i elbiler.'),
    '2026-11-29': ('Skal jeg lease eller købe min næste elbil?', 'To veninder sammenligner egne tilbud over samme periode; begge er aktive beslutningstagere.'),
    '2026-11-30': ('Har jeg fået bilens andre udgifter med?', 'En blandet vennegruppe, hvor en kvinde forklarer forskellen på strømudgift og samlet biløkonomi.')
}
changed = []
for day in plan['days']:
    for item in day['items']:
        if item.get('status') != 'production_plan_only' or item['date'] <= '2026-11-15':
            continue
        question, scenario = contexts.get(item['date'], (
            item['title'],
            'Et konkret hverdagsspørgsmål; variér kvinder som bilvælgere, førere og forklarere uden at antage interesser ud fra køn.'
        ))
        item['creative_brief'] = {
            'version': MARKER,
            'source': brief,
            'opening_question': question,
            'scenario': scenario,
            'person_scene_status': 'not_produced',
            'production_note': 'Question-answer structure using verified real UI and typography; new talking person footage only when actually available within rights and quota.',
            'no_extra_publication': True
        }
        changed.append([item['date'], item['type']])

assert len(plan['days']) == 47
assert sum(len(d['items']) for d in plan['days']) == 141
assert plan['daily_target'] == {'POST': 1, 'REEL': 1, 'STORY': 1}
for old_day, new_day in zip(before['days'], plan['days']):
    assert old_day['date'] == new_day['date']
    for old, new in zip(old_day['items'], new_day['items']):
        # Everything except the new creative brief must be byte-for-byte equivalent as data.
        stripped = {k: v for k, v in new.items() if k != 'creative_brief'}
        old_stripped = {k: v for k, v in old.items() if k != 'creative_brief'}
        assert stripped == old_stripped, (old['date'], old['type'])
        if old['status'] != 'production_plan_only':
            assert old == new
assert plan['allocation'] == before['allocation']
assert plan['publishing_limit'] == before['publishing_limit']
assert plan['heygen'] == before['heygen']
PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')

daily_path = ROOT / 'daily/DAGLIG-FACEBOOK-PLAN.md'
daily = daily_path.read_text()
section = '''## Kreativ retning fra 15. november 2026

Følg samtaleformen fra ejerens reference med tre personer ved bilen. Nye personfilm får kvinder i centrale og varierede roller i mindst to af de næste tre film. Se [den fælles brief](../creative/SAMTALE-OG-BREDERE-PUBLIKUM.md) og [de tre manuskripter](../creative/NAESTE-TRE-MANUSKRIPTER.md). Dette er en afprøvning; organisk kønsfordeling kan ikke garanteres.

Åbn med ét konkret spørgsmål. Vis den ægte hjemmeside og EV Beregner senest sekund 2, giv et nyttigt svar hurtigt og en tydelig vej til hjemmesiden omkring sekund 10–15. Brug rolig dansk tale og kontrollerede tekstlag. Indtil ny personproduktion er mulig, bruges spørgsmål–svar-formen med rigtige skærmklip og typografi; illustrativ grafik kaldes ikke nye talende mennesker.

De færdige pakker til 16.–17. november og alle eksisterende aftaler bevares. Den kreative retning er lagt på endnu ikke producerede planrækker. Der er ikke produceret eller planlagt nye film med denne opdatering. Højst tre HeyGen-forsøg i december; ingen i november. Den separate decemberopgave vælger passende allerede reserverede Reel-pladser ved produktion.

'''
if '## Kreativ retning fra 15. november 2026' not in daily:
    daily = daily.replace('## Daglig rytme\n', section + '## Daglig rytme\n', 1)
daily = daily.replace('Kort demonstration af den ægte hjemmeside og ét resultat.', 'Ét spørgsmål og et svar med ægte hjemmeside; personfilm når færdige og kvalitetssikrede.')
daily = daily.replace('| 2026-11-15 | Bilvalg | 13:00 – Metricool, planlagt | 10:00 – Metricool, planlagt | 19:00 – Metricool, planlagt |', '| 2026-11-15 | Bilvalg | 13:00 – udgivet på Facebook | 10:00 – udgivet på Facebook | 19:00 – udgivet på Facebook |')
daily = daily.replace('Kalenderen viser 5 udgivne og 10 kommende novemberudgivelser på kontroltidspunktet; en kontovisning kan indeholde yderligere forbrug.', 'Se de daterede kalender- og udgivelseskvitteringer for den aktuelle fordeling mellem udgivet og kommende indhold; en kontovisning kan indeholde yderligere forbrug.')
daily_path.write_text(daily)

december_path = ROOT / 'DECEMBER-REELS-PLAN.md'
december = december_path.read_text()
december = december.replace('Bevar den aftalte naturtro stil med to fiktive voksne personer, der taler dansk og viser værktøjet.', 'Følg den nye ejerinstruktion fra 15. november: som udgangspunkt tre fiktive voksne ved elbilen, og kvinder i centrale, varierede roller i mindst to af de næste tre personfilm. De taler naturligt dansk og viser værktøjet.')
if '## Opdateret kreativ retning 15. november' not in december:
    december += '''\n## Opdateret kreativ retning 15. november

Brug marketing/creative/SAMTALE-OG-BREDERE-PUBLIKUM.md og NAESTE-TRE-MANUSKRIPTER.md som den aktuelle kreative retning. Manuskripterne om bilvalg, køretur og leasing/køb erstatter de tidligere foreløbige idéer som udgangspunkt; de er ikke færdige film eller bekræftede udgivelser. Vælg ved produktion passende ledige, allerede reserverede Reel-pladser i DAILY-PLAN.json og koordinér dagens øvrige formater, uden at flytte en faktisk aftale eller miste variation og de 20 beregnere. De tidligere datoer er foreløbige, ikke garantier.

Læg en læsbar opfordring til hjemmesiden omkring sekund 10–15, behold rigtig hjemmesidevisning senest sekund 2, og læg tekst på efter generering. Tildel kvinder både spørgende, forklarende og besluttende roller. Mål Reel-specifik rækkevidde og kønsfordeling, når data findes; ingen garanti for en bestemt fordeling. Alle kvoter, rettigheder, forbehold og kvalitetskrav ovenfor gælder stadig. Ingen ny generering er udført med denne opdatering.
'''
december_path.write_text(december)
organic_december = ROOT / 'organic/DECEMBER-REELS-PLAN.md'
organic_december.write_text(december)

report = {
    'version': MARKER,
    'plan_days': len(plan['days']),
    'plan_slots': sum(len(d['items']) for d in plan['days']),
    'new_creative_briefs': len(changed),
    'appointments_routes_media_and_captions_preserved': True,
    'existing_finished_items_preserved': True,
    'daily_target_and_allocation_preserved': True,
    'new_video_generations': 0,
    'new_publications': 0,
    'modified_slot_briefs': changed
}
(ROOT / 'creative/PLAN-CHECK.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'modified_slot_briefs'}, ensure_ascii=False))
