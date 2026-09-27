/* Every screen of the interface, in one pass, at a given size.
 *
 *   node tools/ui.mjs [width height] [only...]
 *
 * Quick-starts a hunter Warden in the Waystation with a few things in the
 * pack, then opens each overlay in turn (the shops, the stash, the pack, the
 * self, the journal, the map, rest, pause) and saves .shots/ui_<w>_<name>.png.
 * Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const nums = process.argv.slice(2).filter((a) => /^\d+$/.test(a)).map(Number);
const only = process.argv.slice(2).filter((a) => !/^\d+$/.test(a));
const [W = 1280, H = 720] = nums;
fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: W, height: H } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
pg.on('console', (m) => { if (m.type() === 'error') console.log('[error]', m.text().slice(0, 300)); });
await pg.goto('http://localhost:5173/?quick=warden&bg=hunter&zone=waystation&manual&quality=low', { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
await pg.evaluate(() => {
  const g = window.__game.game;
  for (const [id, n] of [['draught', 2], ['wolf_pelt', 3], ['ember_shard', 1]]) { try { g.giveItem(id, n); } catch { /* not an item */ } }
  g.ch.gold = 120;
  window.__advance(2);
});
const SCREENS = {
  shop_brannoc: (g) => g.openShop('brannoc'),
  shop_harlan: (g) => g.openShop('harlan'),
  shop_vonnra: (g) => g.openShop('vonnra'),
  stash: (g) => g.openOverlay('stash'),
  inventory: (g) => g.openOverlay('inventory'),
  character: (g) => g.openOverlay('character'),
  journal: (g) => g.openOverlay('journal'),
  map: (g) => g.openMap(),
  rest: (g) => g.openRest(),
  pause: (g) => g.openOverlay('pause'),
  talk_holloway: (g) => g.talk('holloway'),
  talk_tam: (g) => g.talk('tam'),
};
for (const [name, open] of Object.entries(SCREENS)) {
  if (only.length && !only.includes(name)) continue;
  const err = await pg.evaluate(`(() => { try { const g = window.__game.game; (${open.toString()})(g); window.__advance(0.6); return null; } catch (e) { return String(e); } })()`);
  if (err) { console.log(`${name}: ${err}`); continue; }
  await pg.waitForTimeout(150);
  await pg.evaluate(() => window.__advance(0.3));
  await pg.screenshot({ path: `.shots/ui_${W}_${name}.png` });
  console.log(`saved .shots/ui_${W}_${name}.png`);
  await pg.evaluate(() => { const g = window.__game.game; if (g.dialogue) g.endDialogue?.(); g.closeOverlay(); window.__advance(0.3); });
}
await browser.close();
