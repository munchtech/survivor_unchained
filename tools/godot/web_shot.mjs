/* The web game at the slice's place and hour, for tools/godot/compare.py:
 * the Verge at night by the Hunters' Blind, the autopilot fighting, 1080p.
 *
 *   node tools/godot/web_shot.mjs [name] [seconds] [at]
 *
 * Needs the dev server (npx vite --port 5173). Saves .shots/NAME_NN.png.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const [name = 'cmp_web', secs = '12', at = '-22,-33'] = process.argv.slice(2);
fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => console.log('[pageerror]', e.message));
await page.goto(`http://localhost:5173/?quick=warden&zone=verge&at=${at}&time=night&auto&quality=high&manual`, { waitUntil: 'load' });
await page.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 180000 });
let i = 0;
for (let t = 0; t < Number(secs); t += 2) {
  await page.evaluate(() => window.__advance(2, 30));
  await page.waitForTimeout(30);
  if (t + 2 >= Number(secs) - 4) {
    await page.screenshot({ path: `.shots/${name}_${String(i++).padStart(2, '0')}.png`, timeout: 180000 });
    console.log(`saved .shots/${name}_${String(i - 1).padStart(2, '0')}.png at ${t + 2}s`);
  }
}
await browser.close();
