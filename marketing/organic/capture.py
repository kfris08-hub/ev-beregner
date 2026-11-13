"""Capture genuine website states; block third-party ads and analytics."""
from pathlib import Path
import json
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / 'output'
OUT.mkdir(exist_ok=True)
BASE = 'https://www.evberegn.dk'
SLUG = 'hyundai-ioniq-5-standard-range-rwd-essential'
NAME = 'Hyundai IONIQ 5 Standard Range RWD Essential'
proof = {'site': BASE, 'model': SLUG, 'viewport': [420, 748], 'screens': [], 'third_party_requests': 'aborted'}

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 420, 'height': 748}, device_scale_factor=2, is_mobile=True, has_touch=True)
    page.route('**/*', lambda route: route.continue_() if urlparse(route.request.url).hostname in ('www.evberegn.dk', 'evberegn.dk') else route.abort())
    def visit(path):
        response = page.goto(BASE + path, wait_until='networkidle')
        assert response.status == 200, (path, response.status)
    def shot(name, selector=None):
        if selector:
            page.locator(selector).evaluate('(e) => window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 148)')
        page.screenshot(path=str(OUT / (name + '.png')))
        proof['screens'].append({'file': name + '.png', 'url': page.url, 'title': page.title()})

    visit('/elbil/' + SLUG + '/')
    page.locator('#carPhoto').wait_for(state='visible')
    assert page.locator('#carPhoto').evaluate('(e) => e.complete && e.naturalWidth > 0')
    assert 'CC0' in page.locator('#photoCredit').inner_text()
    shot('model', 'h1')
    proof['model_image_credit'] = page.locator('#photoCredit').inner_text()

    visit('/')
    page.locator('#search').fill('IONIQ 5')
    page.locator('#carList .car-card').first.wait_for()
    shot('search', '#search')
    card = page.locator('#carList .car-card').filter(has_text='Standard Range RWD Essential').first
    assert card.count() == 1
    card.click()
    assert SLUG in page.locator('#selectedModelLink').get_attribute('href')
    proof['selected_model_link'] = page.locator('#selectedModelLink').get_attribute('href')
    shot('selected', '#selectedCar')

    visit('/beregnere/pris-pr-km/#bil=' + SLUG)
    page.wait_for_function('!document.querySelector("#carSelect").disabled')
    assert page.locator('#carSelect').input_value() == SLUG
    assert float(page.locator('#calc_consumption').input_value()) == 16
    page.locator('#calc_electricPrice').fill('2')
    page.locator('#calculateButton').click()
    assert '0,32' in page.locator('#answer').inner_text()
    shot('kilometer', '#carSelect')
    proof['km_result'] = page.locator('#answer').inner_text()
    shot('kilometer-result', '#calc_electricPrice')

    visit('/beregnere/ladepris/#bil=' + SLUG)
    page.wait_for_function('!document.querySelector("#carSelect").disabled')
    assert page.locator('#carSelect').input_value() == SLUG
    for name, value in {'from': '20', 'to': '80', 'electricPrice': '2', 'overhead': '10'}.items():
        page.locator('#calc_' + name).fill(value)
    page.locator('#calculateButton').click()
    proof['charge_fields'] = page.locator('.calc-field input').evaluate_all('(es) => es.map(e => ({id:e.id,value:e.value}))')
    proof['charge_result'] = page.locator('#answer').inner_text()
    shot('charge', '#carSelect')
    shot('charge-result', '#calc_electricPrice')
    browser.close()
(OUT / 'capture-proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2))
print(json.dumps(proof, ensure_ascii=False))
