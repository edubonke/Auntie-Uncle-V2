"""Real-page UI regression tests; do not contact Supabase production."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import asyncio
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / '_screenshots'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


async def run():
    SCREENSHOTS.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/'
    try:
        async with async_playwright() as p:
            launch = {'headless': True, 'args': ['--no-sandbox', '--disable-dev-shm-usage']}
            if Path('/usr/bin/chromium').exists():
                launch['executable_path'] = '/usr/bin/chromium'
            browser = await p.chromium.launch(**launch)
            context = await browser.new_context(viewport={'width':1440,'height':900}, reduced_motion='reduce')
            async def route(request):
                # Never query the production directory or use real accounts during tests.
                if request.request.url.endswith('/backend.js'):
                    await request.fulfill(content_type='text/javascript', body='')
                elif request.request.url.startswith(url):
                    await request.continue_()
                else:
                    await request.abort()
            await context.route('**/*', route)
            page = await context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            await page.goto(url)
            await page.locator('.hero-photo img').evaluate('(img) => img.decode()')
            assert await page.locator('.hero-photo img').evaluate('(img) => img.naturalWidth > 0')
            await page.locator('#services').scroll_into_view_if_needed()
            assert await page.locator('.service-art img').count() == 6
            for icon in await page.locator('.service-art img').all():
                assert await icon.evaluate('(img) => img.decode().then(() => img.naturalWidth > 0)')
            await page.locator('#hero-service').select_option('Cleaning')
            await page.locator('#hero-location').fill('Randburg')
            await page.locator('#hero-search button[type=submit]').click()
            assert await page.locator('.helper-card').count() == 1
            assert 'Thandi M.' in await page.locator('#helper-grid').inner_text()
            await page.locator('#hero-service').select_option('all')
            await page.locator('[data-suburb="Soweto"]').click()
            assert await page.locator('.helper-card').count() == 1
            assert 'Nomusa K.' in await page.locator('#helper-grid').inner_text()
            await page.locator('#reset-search').click()
            assert await page.locator('.helper-card').count() == 8
            await page.locator('[data-filter="family"]').click()
            assert await page.locator('.service-card:visible').count() == 2
            await page.locator('[data-filter="all"]').click()
            await page.locator('.profile-button').first.click()
            assert await page.locator('#helper-dialog').is_visible()
            await page.get_by_role('button',name='Request this helper').click()
            assert await page.locator('#selected-provider').is_visible()
            await page.locator('#details').fill('Please help with an illustrative household cleaning request.')
            await page.locator('#booking-hours').fill('3')
            await page.locator('#enquiry-form .form-submit').click()
            assert await page.locator('#request-result').is_visible()
            assert 'DEMO ONLY' in await page.locator('#request-preview').inner_text()
            await page.locator('#edit-request').click()
            await page.locator('#clear-provider').click()
            await page.locator('#rate-slider').fill('200')
            await page.locator('#hours-slider').fill('20')
            def number(s): return int(''.join(ch for ch in s if ch.isdigit()))
            assert number(await page.locator('#weekly-total').inner_text()) == 4000
            assert number(await page.locator('#monthly-total').inner_text()) == 17333
            assert number(await page.locator('#annual-total').inner_text()) == 208000
            await page.locator('#palette-open').click()
            assert await page.locator('#palette-dialog').is_visible()
            for theme in ['highveld','jacaranda','tablemountain','obsidian','protea']:
                await page.locator(f'[data-theme="{theme}"]').click()
                assert await page.locator('html').get_attribute('data-palette') == theme
                assert await page.locator(f'[data-theme="{theme}"]').get_attribute('aria-pressed') == 'true'
            await page.locator('[data-theme="obsidian"]').click()
            await page.keyboard.press('Escape')
            assert not await page.locator('#palette-dialog').is_visible()
            await page.reload()
            assert await page.locator('html').get_attribute('data-palette') == 'obsidian'
            await page.locator('#palette-open').click()
            await page.locator('[data-theme="protea"]').click()
            await page.locator('#palette-close').click()
            for width in [320,390,650,768,1024,1280,1440,1920]:
                await page.set_viewport_size({'width':width,'height':900})
                await page.evaluate('scrollTo(0,0)')
                scroll_width = await page.evaluate('document.documentElement.scrollWidth')
                assert scroll_width <= width, f'Horizontal overflow: {width} -> {scroll_width}'
                if width == 390:
                    await page.locator('#menu-toggle').click()
                    assert await page.locator('#primary-nav').is_visible()
                    await page.locator('#palette-open').click()
                    assert await page.locator('#palette-dialog').is_visible()
                    await page.locator('#palette-close').click()
                    assert await page.locator('#menu-toggle').get_attribute('aria-expanded') == 'false'
                if width in (390, 1440):
                    await page.screenshot(path=str(SCREENSHOTS / f'auntie-v2-{width}.png'))
                    await page.locator('#browse').scroll_into_view_if_needed()
                    await page.screenshot(path=str(SCREENSHOTS / f'auntie-v2-directory-{width}.png'))
            assert not errors, errors
            await browser.close()
            print('PASS: hero search, suburb shortcuts, 6 SVG assets, hero photo, calculator, five themes, persistence, keyboard close, mobile nav, 8 viewport widths, no JS errors')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    asyncio.run(run())
