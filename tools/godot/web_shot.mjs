/* The web game at a place and hour, 1080p, for comparing with the Godot
 * game (tools/godot/compare.py):
 *
 *   node tools/godot/web_shot.mjs NAME [--zone verge] [--time night] [--at X,Z]
 *                                      [--secs 12] [--still]
 *
 * By default the autopilot fights (the slice's shot: the Verge at night by
 * the Hunters' Blind); --still stands the survivor there and takes one
 * picture of the place, the interface hidden. Needs the dev server (npx vite
 * --port 5173). Saves .shots/NAME_NN.png (NAME.png with --still).
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const argv = process.argv.slice(2);
const name = argv[0] && !argv[0].startsWith('--') ? argv.shift() : 'cmp_web';
const opt = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? (argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : true) : d; };
const zone = opt('zone', 'verge'), time = opt('time', 'night'), at = opt('at', '-22,-33'), secs = Number(opt('secs', 12)), still = !!opt('still', false);

fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => console.log('[pageerror]', e.message));
const q = `quick=warden${zone === 'lowford' ? '' : `&zone=${zone}`}&at=${at}&time=${time}${still ? '' : '&auto'}&quality=high&manual`;
await page.goto(`http://localhost:5173/?${q}`, { waitUntil: 'load' });
await page.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 180000 });
if (still) {
  await page.evaluate(() => window.__advance(2, 30));
  await page.addStyleTag({ content: '#ui, #hud, .hud, #stage > :not(canvas) { display: none !important; }' });
  await page.screenshot({ path: `.shots/${name}.png`, timeout: 180000 });
  console.log(`saved .shots/${name}.png`);
} else {
  let i = 0;
  for (let t = 0; t < secs; t += 2) {
    await page.evaluate(() => window.__advance(2, 30));
    await page.waitForTimeout(30);
    if (t + 2 >= secs - 4) {
      await page.screenshot({ path: `.shots/${name}_${String(i++).padStart(2, '0')}.png`, timeout: 180000 });
      console.log(`saved .shots/${name}_${String(i - 1).padStart(2, '0')}.png at ${t + 2}s`);
    }
  }
}
await browser.close();
