/* A tour of a zone's places, one screenshot each, in one browser.
 *
 *   node tools/tour.mjs verge [day|night] [w h]
 *
 * Uses the empty dev view of the zone (no people, no fighting) so what you
 * see is the place itself. Saves .shots/tour_<zone>_<place>.png and a
 * contact sheet .shots/tour_<zone>.png. Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const [zone = 'verge', time = 'day', W = '960', H = '540'] = process.argv.slice(2);
const PLACES = {
  verge: {
    entry: [-128, 8], wreck: [-70, 28], post: [-10, 40], blind: [-26, -40], hollow: [-64, -86], carcass: [-8, -34], sample: [20, -46],
    pipe: [82, -86], dig: [100, -100], roost: [52, 80], vault: [-106, -54], sinkhole: [106, 54], grove: [-114, 80], brambles: [-100, 72],
  },
  lowford: { camp: [0, 80], post: [14, 38], barrow: [-8, 8], ford: [0, -30], exit: [0, -100] },
  waystation: { south: [0, 30], square: [0, 2], inn: [-12, 11], smithy: [12, 12], shrine: [-20, -20], east: [34, 0], garden: [-36, -33], north: [0, -32] },
}[zone];
fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const names = [];
for (const [name, [x, z]] of Object.entries(PLACES)) {
  const pg = await browser.newPage({ viewport: { width: Number(W), height: Number(H) } });
  pg.on('pageerror', (e) => console.log(`[${name}] pageerror`, e.message));
  const t = time === 'night' ? '&time=night' : '';
  await pg.goto(`http://localhost:5173/?dev=zone&zone=${zone}&x=${x}&z=${z}&camdist=24&pitch=55&yaw=0${t}&manual`, { waitUntil: 'load' });
  await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
  await pg.evaluate(() => window.__advance(2.5));
  await pg.screenshot({ path: `.shots/tour_${zone}_${name}.png` });
  names.push(name);
  console.log(`saved .shots/tour_${zone}_${name}.png`);
  await pg.close();
}
await browser.close();
