/* How hard is the Verge? Measured with a character who earned their way there.
 *
 *   node tools/field.mjs [--fresh] [scenario...]
 *
 * First (or with --fresh) the autopilot plays the whole prologue and the save
 * it arrives in town with is kept in .shots/after_prologue.json. Then each
 * scenario loads that survivor, lets the night's ember go out (as a rest
 * would), walks them into the Verge and plays for a while: the autopilot's
 * field mode (kiting, dodging, drinking) or standing still. Prints health,
 * kills, ember level and the hostile count as it goes, and a summary.
 * Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const args = process.argv.slice(2);
const fresh = args.includes('--fresh');
// --shots: a full-size screenshot every 30 s of each scenario, to look at the fighting.
const shots = args.includes('--shots');
const want = args.filter((a) => !a.startsWith('--'));
const SNAP = '.shots/after_prologue.json';
fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });

async function page() {
  const pg = await browser.newPage({ viewport: shots ? { width: 1280, height: 720 } : { width: 320, height: 180 } });
  pg.on('pageerror', (e) => console.log('  [pageerror]', e.message));
  return pg;
}
const ready = (pg) => pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });

if (fresh || !fs.existsSync(SNAP)) {
  console.log('playing the prologue for a survivor...');
  const pg = await page();
  await pg.goto('http://localhost:5173/?quick=warden&bg=hunter&name=Tester&auto&manual&quality=low', { waitUntil: 'load' });
  await ready(pg);
  for (let t = 0; t < 900; t += 10) {
    await pg.evaluate(() => window.__advance(10, 30));
    await pg.waitForTimeout(20);
    const z = await pg.evaluate(() => window.__game.game.zone?.id);
    if (z === 'waystation') break;
  }
  await pg.waitForTimeout(3500);
  const snap = await pg.evaluate(() => {
    const g = window.__game.game;
    g.save('snapshot');
    const out = {};
    for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k.startsWith('survivor-unchained')) out[k] = localStorage.getItem(k); }
    return { storage: out, level: g.ch.level, kills: g.ch.stats.kills, gold: g.ch.gold, pack: g.ch.pack.filter(Boolean).map((i) => `${i.def}${i.qty > 1 ? `x${i.qty}` : ''}`) };
  });
  fs.writeFileSync(SNAP, JSON.stringify(snap));
  console.log(`  arrived: character level ${snap.level}, ${snap.kills} kills, ${snap.gold} gold, pack ${snap.pack.join(', ')}`);
  await pg.close();
}
const snap = JSON.parse(fs.readFileSync(SNAP, 'utf8'));

const SCENARIOS = {
  day_play: { time: 'day', at: [-60, 8], secs: 240, auto: true },
  night_play: { time: 'night', at: [-60, 8], secs: 240, auto: true },
  day_idle: { time: 'day', at: [-60, 8], secs: 180, auto: false },
  roost_play: { time: 'day', at: [30, 60], secs: 150, auto: true },
  day_long: { time: 'day', at: [-60, 8], secs: 480, auto: true },
};

for (const [name, sc] of Object.entries(SCENARIOS)) {
  if (want.length && !want.includes(name)) continue;
  const pg = await page();
  await pg.addInitScript((s) => { for (const [k, v] of Object.entries(s)) localStorage.setItem(k, v); }, snap.storage);
  await pg.goto(`http://localhost:5173/?manual&quality=${shots ? 'high' : 'low'}&auto${sc.auto ? '' : '=idle'}`, { waitUntil: 'load' });
  await ready(pg);
  await pg.evaluate(() => { const g = window.__game.game; const m = JSON.parse(localStorage.getItem('survivor-unchained.meta') || '{}'); g.continueJourney(m.last ?? 0); });
  await pg.waitForTimeout(1500);
  await pg.evaluate(([time, at]) => {
    const g = window.__game.game;
    g.expedition = null; // a night's rest: the ember went out
    g.world.time = time;
    g.world.day = Math.max(2, g.world.day);
    g.world.facts['toll.paid'] = true;
    g.enterZone('verge', 'waystation', { x: at[0], z: at[1] });
  }, [sc.time, sc.at]);
  console.log(`\n== ${name} (${sc.time}, ${sc.auto ? 'playing' : 'standing still'}, character level ${snap.level})`);
  let died = null;
  for (let t = 0; t < sc.secs; t += 10) {
    await pg.evaluate(() => window.__advance(10, 30));
    await pg.waitForTimeout(20);
    const s = await pg.evaluate(() => {
      const g = window.__game.game, b = g.scene.battle, p = b.player;
      let h = 0; b.enemies.forEach((e) => { if (e.alive && e.disposition === 'hostile' && Math.hypot(e.x - p.x, e.z - p.z) < 25) h++; });
      return { t: Math.round(b.time), hp: Math.round(p.hp), max: b.maxHp, alive: p.alive, ember: b.ember.level, kills: b.killCount, hostile: h, zone: g.zone?.id };
    });
    console.log(`  t=${String(s.t).padStart(3)} hp ${String(s.hp).padStart(3)}/${s.max} ember ${String(s.ember).padStart(2)} kills ${String(s.kills).padStart(4)} hostile ${s.hostile}${s.alive ? '' : '  DEAD'}`);
    if (shots && (t + 10) % 30 === 0) await pg.screenshot({ path: `.shots/field_${name}_${String(t + 10).padStart(3, '0')}.png` });
    if (!s.alive || s.zone !== 'verge') { died = s.t; break; }
  }
  const sum = await pg.evaluate(() => { const a = window.__game.game.autopilot; return a ? a.stats : null; });
  if (sum) console.log(`  summary: min hp ${Math.round(sum.minHp * 100)}%, damage taken ${Math.round(sum.hurt)}, draughts ${sum.draughts}, dashes ${sum.dashes}, bashes ${sum.bashes}${died !== null ? `, died at ${died}s` : ''}`);
  else if (died !== null) console.log(`  died at ${died}s`);
  await pg.close();
}
await browser.close();
