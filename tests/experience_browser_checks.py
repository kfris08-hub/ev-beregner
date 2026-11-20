"""Exercise user-visible improvements with controlled prices and no test beacons."""
import asyncio, json, mimetypes, os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).parents[1]
BASE = 'https://www.evberegn.dk'
PUBLIC = os.environ.get('EXPERIENCE_PUBLIC') == '1'
OUT = ROOT / 'test-results'

async def main():
    OUT.mkdir(exist_ok=True)
    results = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=os.environ.get('CHROME_PATH', '/usr/bin/google-chrome'), headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        for width in [320, 390, 768, 1440]:
            context = await browser.new_context(viewport={'width': width, 'height': 900})
            async def route(r):
                u = urlsplit(r.request.url)
                if 'metricool.com' in u.netloc or 'a-ads.com' in u.netloc or 'aads.com' in u.netloc:
                    await r.abort(); return
                if u.netloc == 'elpriser.org':
                    await asyncio.sleep(.15)
                    await r.fulfill(status=200, json={'price': 2.5 if 'DK1' in u.query else 3.7}); return
                if u.netloc == 'www.evberegn.dk':
                    if PUBLIC:
                        await r.continue_(); return
                    path = unquote(u.path).lstrip('/')
                    if not path or path.endswith('/'): path += 'index.html'
                    file = ROOT / path
                    await r.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'missing', content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream'); return
                await r.abort()
            await context.route('**/*', route)
            page = await context.new_page()
            page.set_default_timeout(10000)
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            await page.goto(BASE + '/', wait_until='load')
            assert await page.locator('a.calc-card').count() == 20
            assert await page.locator('#carOverview').is_hidden()
            await page.locator('#search').fill('Kia EV3')
            card = page.get_by_role('button', name='Kia EV3 Standard Range Access', exact=False)
            await card.focus(); await page.keyboard.press('Enter')
            await expect(page.locator('#carOverview')).to_be_visible()
            await expect(page.locator('#overviewPhoto img')).to_be_visible()
            await expect(page.locator('#overviewPhoto figcaption')).to_contain_text('Foto:')
            assert await page.locator('#overviewPhoto figcaption a[href*="creativecommons.org"]').count() > 0
            for selector, value in [('#overviewConsumption', '16'), ('#overviewPrice', '2'), ('#overviewKm', '20000')]:
                await page.locator(selector).fill(value)
            await expect(page.locator('#overviewPerKm')).to_have_text('0,32 kr.')
            await expect(page.locator('#overviewPer100')).to_have_text('32,00 kr.')
            await expect(page.locator('#overviewYear')).to_have_text('6.400 kr.')
            await page.locator('#overviewMix').check()
            await page.locator('#overviewHomeShare').fill('80')
            await page.locator('#overviewPublicPrice').fill('4')
            await expect(page.locator('#overviewPer100')).to_have_text('38,40 kr.')
            await expect(page.locator('#overviewYear')).to_have_text('7.680 kr.')
            await page.locator('#overviewKm').fill('0')
            await expect(page.locator('#overviewYear')).to_have_text('0 kr.')
            await page.locator('#overviewKm').fill('20000')
            await page.locator('#overviewHomeShare').fill('101')
            await expect(page.locator('#overviewResults')).to_be_hidden()
            await expect(page.locator('#overviewError')).to_contain_text('gyldige tal')
            await page.locator('#overviewHomeShare').fill('80')
            assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
            await page.locator('#carOverview').screenshot(path=str(OUT / f'overview-{width}.png'))
            await page.locator('#overviewCostLink').click()
            await page.wait_for_function('!document.getElementById("carSelect").disabled')
            await expect(page.locator('#carSelect')).to_have_value('kia-ev3-standard-range-access')
            assert abs(float(await page.locator('#calc_electricPrice').input_value()) - 2.4) < 1e-10
            await expect(page.locator('#answer')).to_contain_text('38,4 kr.')
            await page.locator('#carSearch').fill('KIA E SOUL')
            assert await page.locator('#carSelect option').count() == 4  # own values, two matches, current car
            await expect(page.locator('#carSelect')).to_have_value('kia-ev3-standard-range-access')
            await page.locator('#carSearch').fill('zz-ingen-bil')
            await expect(page.locator('#carSearchStatus')).to_contain_text('0 bilvarianter')
            await expect(page.locator('#answer')).to_contain_text('38,4 kr.')
            await page.locator('#carSearch').fill('')
            assert await page.locator('#carSelect option').count() == 284
            await page.goto(BASE + '/?car=tesla-model-y-standard-rwd', wait_until='load')
            await page.locator('#overviewPrice').fill('0')
            await page.locator('#regionDK2').click()
            await page.wait_for_function('energyState.electric === "ready"')
            await expect(page.locator('#overviewPrice')).to_have_value('0')
            await expect(page.locator('#overviewYear')).to_have_text('0 kr.')
            await page.locator('a.calc-card[href="#beregner-2"]').click()
            await expect(page.locator('#calc_consumption')).to_be_focused()
            await page.locator('#calc_electricPrice').fill('0')
            await page.keyboard.press('Enter')
            await expect(page.locator('#answer')).to_contain_text('0,00 kr.')
            await page.keyboard.press('Escape')
            await expect(page.locator('#calculator')).to_be_hidden()
            await expect(page.locator('a.calc-card[href="#beregner-2"]')).to_be_focused()
            await page.goto(BASE + '/?car=elveon-motors-min-e-sedan-base', wait_until='load')
            await expect(page.locator('#overviewConsumption')).to_have_value('')
            await expect(page.locator('#overviewResults')).to_be_hidden()
            await page.locator('#overviewConsumption').fill('20')
            await page.locator('#overviewPrice').fill('-1')
            await expect(page.locator('#overviewPer100')).to_have_text('-20,00 kr.')
            await page.locator('#generalModeBtn').click()
            await expect(page.locator('#generalModeBtn')).to_have_attribute('aria-pressed', 'true')
            await expect(page.locator('#overviewTitle')).to_have_text('Din strømøkonomi')
            assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
            assert not errors, errors
            results.append({'width': width, 'keyboard_car_choice': 'passed', 'photo_and_licence': 'passed', 'same_values_in_detail': 'passed', 'home_public_mix': 'passed', 'zero_and_negative_prices': 'passed', 'invalid_and_unknown_data': 'passed', 'manual_price_preserved': 'passed', 'search_keeps_selection_and_result': 'passed', 'modal_enter_escape_focus': 'passed', 'overflow': False})
            await context.close()
        await browser.close()
    (OUT / 'experience-browser.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print('EXPERIENCE_BROWSER_RESULT ' + json.dumps(results, ensure_ascii=False))

if __name__ == '__main__': asyncio.run(main())
