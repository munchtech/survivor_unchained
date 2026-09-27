/* Save and reload, end to end, in a real browser.
 *
 *   node tools/saveload.mjs
 *
 * Starts a journey in the Verge, changes the world (facts, gold, an item,
 * a quest entry, a relationship, the ember build), walks somewhere, saves,
 * reloads the page, continues the journey from the title, and checks that
 * every one of those things came back. Expects the dev server on :5173. */
import { chromium } from 'playwright';

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM || undefined,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'],
});
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on('pageerror', (e) => { errors.push(e.message); console.log('[pageerror]', e.message); });
const ready = () => page.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });

await page.goto('http://localhost:5173/?quick=warden&bg=scholar&name=Tessaly&zone=verge&at=-40,14&manual', { waitUntil: 'load' });
await ready();
await page.evaluate(() => window.__advance(1.5));

const before = await page.evaluate(() => {
  const g = window.__game.game;
  g.apply([
    { set: { 'dig.pump': 'moved', 'test.marker': 'kept' } },
    { gold: 77 },
    { give: 'stream_sample' },
    { quest: { id: 'beasts', status: 'active', entry: 'clue.green_stream' } },
    { rel: { npc: 'maeca', trust: 33 } },
    { history: { id: 'test_deed', text: 'tested the save', tags: [], spread: 0 }, witnesses: ['maeca'] },
  ]);
  // Walk a little, so the saved position is not the arrival point.
  const p = g.scene.battle.player;
  p.x += 6; p.z -= 3;
  window.__advance(0.5);
  g.save('test');
  return {
    zone: g.zone.id, x: p.x, z: p.z, gold: g.ch.gold, day: g.world.day,
    pack: g.ch.pack.filter(Boolean).map((i) => i.def).sort(),
    ember: g.expedition ? { level: g.expedition.level, weapons: g.expedition.weapons.length } : null,
    trust: g.world.npcs.maeca.trust, memories: g.world.npcs.maeca.memories.slice(),
    entries: g.world.quests.beasts.entries.slice(),
  };
});
console.log('saved   ', JSON.stringify(before));

await page.goto('http://localhost:5173/?manual', { waitUntil: 'load' });
await ready();
const slots = await page.evaluate(() => JSON.parse(localStorage.getItem('survivor-unchained.meta') || '{}'));
await page.evaluate((slot) => window.__game.game.continueJourney(slot), slots.last ?? 0);
await page.waitForTimeout(900);
await page.evaluate(() => window.__advance(1.0));

const after = await page.evaluate(() => {
  const g = window.__game.game;
  const p = g.scene.battle?.player;
  return {
    zone: g.zone?.id, x: p?.x, z: p?.z, gold: g.ch.gold, day: g.world.day,
    pack: g.ch.pack.filter(Boolean).map((i) => i.def).sort(),
    ember: g.expedition ? { level: g.expedition.level, weapons: g.expedition.weapons.length } : null,
    trust: g.world.npcs.maeca.trust, memories: g.world.npcs.maeca.memories.slice(),
    entries: g.world.quests.beasts.entries.slice(),
    marker: g.world.facts['test.marker'], pump: g.world.facts['dig.pump'], mode: g.mode,
  };
});
console.log('reloaded', JSON.stringify(after));
await page.screenshot({ path: '.shots/saveload.png' });

const checks = [
  ['zone', after.zone === before.zone],
  ['position', Math.hypot(after.x - before.x, after.z - before.z) < 0.6],
  ['gold', after.gold === before.gold],
  ['day', after.day === before.day],
  ['pack', JSON.stringify(after.pack) === JSON.stringify(before.pack)],
  ['ember build', JSON.stringify(after.ember) === JSON.stringify(before.ember)],
  ['relationship', after.trust === before.trust],
  ['memories', JSON.stringify(after.memories) === JSON.stringify(before.memories)],
  ['journal', JSON.stringify(after.entries) === JSON.stringify(before.entries)],
  ['facts', after.marker === 'kept' && after.pump === 'moved'],
  ['playing', after.mode === 'play'],
  ['no page errors', errors.length === 0],
];
let ok = true;
for (const [name, pass] of checks) { console.log(`${pass ? 'PASS' : 'FAIL'}  ${name}`); ok &&= pass; }
await browser.close();
process.exit(ok ? 0 : 1);
