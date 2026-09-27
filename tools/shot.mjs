/* Screenshot harness: open the game in headless Chromium (software WebGL),
 * wait for it to settle, and save a PNG.
 *
 *   node tools/shot.mjs "<query string>" <name> [waitMs] [width] [height]
 *
 * Expects the dev server on :5173 (npm run dev). Console errors are printed,
 * and a page error fails the run. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const [query = '', name = 'shot', wait = '2500', w = '1600', h = '900'] = process.argv.slice(2);
fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM || undefined,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'],
});
const page = await browser.newPage({ viewport: { width: Number(w), height: Number(h) }, deviceScaleFactor: 1 });
const errors = [];
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning' || process.env.VERBOSE) console.log(`[${m.type()}]`, m.text().slice(0, 400)); });
page.on('pageerror', (e) => { errors.push(e); console.log('[pageerror]', e.message); });
const manual = !process.env.LIVE;
await page.goto(`http://localhost:5173/?${query}${manual ? '&manual' : ''}`, { waitUntil: 'load' });
try {
  await page.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
} catch (e) { console.log('timeout waiting for ready'); }
const err = await page.evaluate(() => document.body.dataset.error);
if (err) console.log('[boot error]', err);
if (manual) {
  const ms = await page.evaluate((w) => window.__advance(w / 1000), Number(wait));
  console.log(`frame rendered in ${ms.toFixed(0)} ms`);
} else {
  await page.waitForTimeout(Number(wait));
}
if (process.env.EVAL) console.log(await page.evaluate(process.env.EVAL));
await page.screenshot({ path: `.shots/${name}.png`, timeout: 180000 });
console.log(`saved .shots/${name}.png`);
// SEQ="count,step": further frames, each after advancing `step` seconds.
if (process.env.SEQ && manual) {
  const [count, step] = process.env.SEQ.split(',').map(Number);
  for (let i = 1; i <= count; i++) {
    await page.evaluate((s) => window.__advance(s, 60), step);
    await page.screenshot({ path: `.shots/${name}_${i}.png`, timeout: 180000 });
    console.log(`saved .shots/${name}_${i}.png`);
  }
}
await browser.close();
if (errors.length || err) process.exit(1);
