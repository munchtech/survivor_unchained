/* The four callings by the creation fire, side by side: one picture to
 * judge a change to the figures (proportions, models, dyes).
 *
 *   node tools/callings.mjs [name]      -> .shots/callings_<name>.png
 *
 * Expects the dev server on :5173. */
import { chromium } from 'playwright';
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 1280, height: 720 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
const adv = (s) => pg.evaluate((s) => window.__advance(s, 30), s);
await pg.goto('http://localhost:5173/?screen=create&manual&quality=low', { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1', null, { timeout: 120000 });
await adv(1);
const name = process.argv[2] ?? 'now';
const shots = [];
for (const c of ['Warden', 'Reaver', 'Arcanist', 'Stalker']) {
  await pg.locator(`.choice:has-text("${c}")`).first().click();
  await adv(3.5);
  shots.push(await pg.screenshot({ clip: { x: 540, y: 170, width: 380, height: 440 } }));
}
// Side by side, in the page itself (no image library needed).
const sheet = await browser.newPage({ viewport: { width: 1520, height: 440 } });
await sheet.setContent(`<body style="margin:0;display:flex;background:#000">${shots.map((b) => `<img src="data:image/png;base64,${b.toString('base64')}">`).join('')}</body>`);
await sheet.screenshot({ path: `.shots/callings_${name}.png` });
console.log(`saved .shots/callings_${name}.png`);
await browser.close();
