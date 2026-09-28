import { chromium } from 'playwright';
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 1280, height: 720 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
const adv = (s) => pg.evaluate((s) => window.__advance(s, 30), s);
await pg.goto('http://localhost:5173/?screen=create&manual&quality=low', { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1', null, { timeout: 120000 });
await adv(1);
const name = process.argv[2] ?? 'cmp';
for (const c of ['Warden', 'Reaver', 'Arcanist', 'Stalker']) {
  await pg.locator(`.choice:has-text("${c}")`).first().click();
  await adv(3.5);
  await pg.screenshot({ path: `.shots/_c_${name}_${c}.png`, clip: { x: 540, y: 170, width: 380, height: 440 } });
}
await browser.close();
