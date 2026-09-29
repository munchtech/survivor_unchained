/* Run the game headless with the autopilot for a stretch of game time,
 * printing progress and saving screenshots along the way.
 *
 *   node tools/play.mjs "<query>" <name> <seconds> [shotEvery]
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const [query = 'quick=warden&auto', name = 'play', secs = '300', every = '60'] = process.argv.slice(2);
fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
page.on('console', (m) => { if (m.type() === 'error' || /mid-play/.test(m.text())) console.log(`[${m.type()}]`, m.text().slice(0, 300)); });
page.on('pageerror', (e) => console.log('[pageerror]', e.message, e.stack?.split('\n').slice(0, 3).join(' | ')));
await page.goto(`http://localhost:5173/?${query}&manual`, { waitUntil: 'load' });
await page.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
const total = Number(secs), step = Number(every);
let t = 0, i = 0;
while (t < total) {
  const chunk = Math.min(step, total - t);
  // Advance in 5 s slices so timers (setTimeout-driven respawns) get a turn.
  for (let s = 0; s < chunk; s += 10) {
    await page.evaluate((d) => window.__advance(d, 30), Math.min(10, chunk - s));
    await page.waitForTimeout(30);
  }
  t += chunk;
  const info = await page.evaluate(() => {
    const g = window.__game?.game;
    const b = g?.scene.battle;
    const d = g?.zone?.debug?.() ?? {};
    return { zone: g?.zone?.id, stage: d.stage, lvl: b?.ember.level, hp: b ? Math.round(b.player.hp) : null, x: b ? Math.round(b.player.x) : null, z: b ? Math.round(b.player.z) : null, kills: b?.killCount, deaths: g?.ch?.stats.deaths, warden: d.wardenHp ? Math.round(d.wardenHp) : null, lit: d.lit, foes: b?.enemies.count };
  });
  console.log(`t=${t}s`, JSON.stringify(info));
  await page.screenshot({ path: `.shots/${name}_${String(i++).padStart(2, '0')}.png`, timeout: 180000 });
}
console.log((await page.evaluate(() => window.__auto?.report ?? [])).join('\n'));
await browser.close();
