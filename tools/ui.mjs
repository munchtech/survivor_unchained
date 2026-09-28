/* Every screen of the interface, in one pass, at a given size.
 *
 *   node tools/ui.mjs [width height] [only...]
 *
 * Quick-starts a hunter Warden in the Waystation with a few things in the
 * pack, then opens each overlay in turn (the shops, the stash, the pack, the
 * self, the journal, the map, rest, pause) and saves .shots/ui_<w>_<name>.png.
 * With --rich the survivor has been busy first: both questlines under way,
 * people met, deeds done, gear worn, so the journal and sheet have pages.
 * Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const nums = process.argv.slice(2).filter((a) => /^\d+$/.test(a)).map(Number);
const rich = process.argv.includes('--rich');
const only = process.argv.slice(2).filter((a) => !/^\d+$/.test(a) && !a.startsWith('--'));
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
if (rich) {
  await pg.evaluate(() => {
    const g = window.__game.game;
    const q = (id, entry) => ({ quest: { id, entry, status: 'active' } });
    g.apply([
      q('beasts', 'rumour'), q('beasts', 'holloway_bounty'), q('beasts', 'maeca_theory'), q('beasts', 'tam_plea'), q('beasts', 'clue.sick_wolf'), q('beasts', 'clue.green_stream'),
      q('caravan', 'harlan_plea'), q('caravan', 'wreck'), q('caravan', 'ruts'), q('caravan', 'toll_ledger'),
      { quest: { id: 'vault', entry: 'seen', status: 'active' } },
      { learn: ['lore.warden', 'hint.stream'] },
      { rel: { npc: 'holloway', trust: 12, respect: 8 } }, { rel: { npc: 'maeca', affection: 15, respect: 10 } }, { rel: { npc: 'pell', trust: -20, fear: 5 } }, { rel: { npc: 'tam', affection: 25 } },
      { history: { id: 'ui_test_deed', text: 'drove the dead back from the Low Ford', tags: ['combat'], spread: 2 } },
      { give: 'old_hunters_cloak' }, { give: 'wolf_fang_necklace' },
    ]);
    for (const id of ['holloway', 'maeca', 'pell', 'tam', 'rook', 'brannoc', 'harlan', 'wenna', 'chid']) { const n = g.world.npcs[id]; if (n) n.flags.met = true; }
    window.__advance(0.5);
  });
}
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
  journal_people: (g) => g.openOverlay('journal'),
  journal_deeds: (g) => g.openOverlay('journal'),
  journal_codex: (g) => g.openOverlay('journal'),
  chapter: (g) => {
    g.apply([{ set: { 'beasts.outcome': 'cured', 'caravan.survivors': 'rescued', 'caravan.cargo': 'returned' } }, { quest: { id: 'beasts', status: 'resolved', outcome: 'cured' } }, { quest: { id: 'caravan', status: 'resolved', outcome: 'returned' } }]);
    g.openOverlay('chapter');
  },
  rest_report: (g) => { g.openRest(); document.querySelector('.rest button.primary, .rest .btn')?.click(); },
  shop_pick: (g) => g.openShop('brannoc'),
  pack_pick: (g) => g.openOverlay('inventory'),
};
// A second step, once the overlay has drawn (a tab to click).
const THEN = {
  journal_people: () => document.querySelectorAll('.jr-tab')[1]?.click(),
  journal_deeds: () => document.querySelectorAll('.jr-tab')[2]?.click(),
  journal_codex: () => document.querySelectorAll('.jr-tab')[3]?.click(),
  shop_pick: () => document.querySelectorAll('.shop-body .pslot.filled')[1]?.click(),
  pack_pick: () => document.querySelectorAll('.inv .pslot.filled')[1]?.click(),
};
for (const [name, open] of Object.entries(SCREENS)) {
  if (only.length && !only.includes(name)) continue;
  const err = await pg.evaluate(`(() => { try { const g = window.__game.game; (${open.toString()})(g); window.__advance(0.6); return null; } catch (e) { return String(e); } })()`);
  if (err) { console.log(`${name}: ${err}`); continue; }
  await pg.waitForTimeout(150);
  if (THEN[name]) { await pg.evaluate(THEN[name]); await pg.waitForTimeout(100); }
  await pg.evaluate(() => window.__advance(0.3));
  const file = `.shots/ui_${W}${rich ? 'r' : ''}_${name}.png`;
  await pg.screenshot({ path: file, timeout: 180000 });
  console.log(`saved ${file}`);
  await pg.evaluate(() => { const g = window.__game.game; if (g.dialogue) g.endDialogue?.(); g.closeOverlay(); window.__advance(0.3); });
}
await browser.close();
