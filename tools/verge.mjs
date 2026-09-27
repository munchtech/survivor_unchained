/* The Verge's questline beats, driven in a real browser.
 *
 *   node tools/verge.mjs [scenario...]     (hollow, roost, dig, death)
 *
 * Each scenario starts a fresh survivor with the background that opens its
 * route, walks (teleports) into the place, uses the same interactables and
 * dialogue choices a player would, lets the world run, and checks what the
 * world did about it. Screenshots land in .shots/verge_<scenario>_*.png.
 * Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM || undefined,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'],
});

const HELPERS = () => {
  const g = () => window.__game.game;
  window.T = {
    adv: (s) => window.__advance(s, 30),
    tp(x, z) { const p = g().scene.battle.player; p.x = x; p.z = z; p.vx = 0; p.vz = 0; window.__advance(0.3, 30); },
    act(id) {
      const it = g().zone.interactables.find((i) => i.id === id);
      if (!it) return 'missing';
      if (it.when && !it.when()) return 'unavailable';
      const l = it.locked?.();
      if (l) return `locked: ${l}`;
      it.act();
      return 'ok';
    },
    /** Pick a dialogue choice by a fragment of its text (continuing through
     *  choice-less nodes first). */
    say(frag) {
      const game = g();
      for (let i = 0; i < 12 && game.runner; i++) {
        const p = game.runner.present();
        if (!p) return 'ended';
        if (!p.choices.length) { game.advanceDialogue(); continue; }
        const c = p.choices.find((x) => x.text.toLowerCase().includes(frag.toLowerCase()));
        if (!c) return `no "${frag}" in [${p.choices.map((x) => x.text).join(' | ')}]`;
        if (!c.enabled) return `locked: ${c.locked}`;
        game.chooseDialogue(c.index);
        return 'ok';
      }
      return 'not talking';
    },
    fact: (k) => g().world.facts[k],
    hp: () => { const b = g().scene.battle; return { hp: Math.round(b.player.hp), max: b.maxHp, alive: b.player.alive }; },
    near(r = 14) {
      const b = g().scene.battle, p = b.player, out = {};
      b.enemies.forEach((e) => {
        if (!e.alive || Math.hypot(e.x - p.x, e.z - p.z) >= r) return;
        out[e.disposition] = (out[e.disposition] ?? 0) + 1;
        if (e.disposition === 'hostile') (out.who ??= {})[`${e.def.id}/${e.faction ?? '-'}/${e.tag ?? '-'}`] = ((out.who ?? {})[`${e.def.id}/${e.faction ?? '-'}/${e.tag ?? '-'}`] ?? 0) + 1;
      });
      return out;
    },
    has: (def) => g().ch.pack.some((i) => i && i.def === def),
    overlay: () => document.querySelector('.dialogue, .death, .chapter-overlay') ? 'open' : 'none',
  };
};

async function run(name, query, steps) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', (e) => { errors.push(e.message); console.log(`  [pageerror] ${e.message}`); });
  await page.goto(`http://localhost:5173/?${query}&manual`, { waitUntil: 'load' });
  await page.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
  await page.evaluate(HELPERS);
  await page.evaluate(() => window.__advance(1, 30));
  console.log(`\n== ${name}`);
  let ok = true, shot = 0;
  const T = async (expr) => page.evaluate(`(${expr})`);
  const check = (label, pass, detail = '') => { console.log(`  ${pass ? 'PASS' : 'FAIL'}  ${label}${detail ? `  (${detail})` : ''}`); ok &&= !!pass; };
  const snap = async () => page.screenshot({ path: `.shots/verge_${name}_${++shot}.png`, timeout: 180000 });
  await steps({ T, check, snap, page });
  check('no page errors', errors.length === 0, errors[0]);
  await page.close();
  return ok;
}

const scenarios = {
  // A hunter walks into the Hollow and speaks with Greymuzzle.
  hollow: () => run('hollow', 'quick=warden&bg=hunter&zone=verge&at=-40,-50', async ({ T, check, snap }) => {
    await T('T.tp(-50, -66)'); await T('T.adv(3)');
    await T('T.tp(-60, -79)'); await T('T.adv(1.5)');
    const a = await T('T.act("greymuzzle")');
    check('Greymuzzle can be approached', a === 'ok', a);
    await snap();
    check('kneel', (await T('T.say("kneel")')) === 'ok');
    check('promise', (await T('T.say("I will stop")')) === 'ok');
    check('the Hollow is at peace', (await T('T.fact("hollow.peace")')) === true);
    const hp0 = await T('T.hp()');
    await T('T.adv(12)');
    const hp1 = await T('T.hp()'), near = await T('T.near(18)');
    const packHostile = Object.keys(near.who ?? {}).filter((k) => k.includes('/pack/'));
    check('the Pack leaves you be', packHostile.length === 0, `${JSON.stringify(near)} hp ${hp0.hp}->${hp1.hp}`);
    await snap();
  }),

  // An outcast bluffs the Kerchiefs out of the Roost and frees the teamsters.
  roost: () => run('roost', 'quick=warden&bg=outcast&zone=verge&at=20,60', async ({ T, check, snap }) => {
    await T('T.tp(36, 72)'); await T('T.adv(2)');
    await T('T.tp(52, 87)'); await T('T.adv(1)');
    const a = await T('T.act("redcowl")');
    check('Redcowl will talk', a === 'ok', a);
    await snap();
    const s1 = await T('T.say("watch is on its way")');
    check('the bluff', s1 === 'ok', s1);
    check('they run', (await T('T.say("watch them run")')) === 'ok');
    check('Redcowl tricked', (await T('T.fact("redcowl")')) === 'tricked');
    await T('T.adv(8)');
    for (let i = 0; i < 3; i++) {
      await T(`T.tp(${62 + i * 3.2}, ${84 - i * 0.8 - 1.6})`);
      const r = await T(`T.act("cage${i}")`);
      check(`cage ${i} opens`, r === 'ok', r);
      await T('T.adv(0.5)');
    }
    check('survivors rescued', (await T('T.fact("caravan.survivors")')) === 'rescued');
    await T('T.tp(46.2, 84.6)');
    const sb = await T('T.act("strongbox")');
    check('strongbox taken', sb === 'ok' && (await T('T.has("coyle_strongbox")')), sb);
    await T('T.adv(2)');
    await snap();
  }),

  // A scholar talks Snib into moving the outflow.
  dig: () => run('dig', 'quick=warden&bg=scholar&zone=verge&at=70,-70', async ({ T, check, snap }) => {
    await T('T.tp(86, -80)'); await T('T.adv(2)');
    await T('T.tp(97, -89)'); await T('T.adv(1)');
    const a = await T('T.act("snib")');
    check('Snib will talk', a === 'ok', a);
    await snap();
    const s = await T('T.say("sinkhole")');
    check('the arcana argument', s === 'ok', s);
    await T('T.say("good idea")');
    check('pump moved', (await T('T.fact("dig.pump")')) === 'moved');
    await T('T.adv(8)');
    const near = await T('T.near(16)');
    check('the diggers stay peaceable', !Object.keys(near.who ?? {}).some((k) => k.includes('/lampling/')), JSON.stringify(near));
    await snap();
  }),

  // Falling in the Verge: the corpse, the nemesis, waking at the shrine.
  death: () => run('death', 'quick=warden&bg=devout&zone=verge&at=-40,14', async ({ T, check, snap, page }) => {
    await page.evaluate(() => { const g = window.__game.game; g.ch.gold = 120; });
    await T('T.tp(-50, -66)'); await T('T.adv(4)');
    await page.evaluate(() => { const b = window.__game.game.scene.battle; b.player.hp = 1; });
    await T('T.adv(6)');
    const dead = await T('T.hp()');
    check('the survivor fell', !dead.alive, JSON.stringify(dead));
    await page.waitForTimeout(2600);
    const res = await page.evaluate(() => {
      const g = window.__game.game;
      return { caption: document.querySelector('.fader-caption')?.textContent ?? '', corpse: g.world.corpse, nemesis: g.world.nemesis?.title };
    });
    check('the fall', /fell/i.test(res.caption), res.caption);
    check('a corpse with gold on it', !!res.corpse && res.corpse.gold > 0, JSON.stringify(res.corpse && { gold: res.corpse.gold, zone: res.corpse.zone }));
    check('a nemesis', !!res.nemesis, res.nemesis);
    await page.waitForTimeout(5200);
    await T('T.adv(1.5)');
    check('Chid is there when you wake', await page.evaluate(() => window.__game.game.talkNpc === 'chid'));
    await snap();
    const after = await page.evaluate(() => { const g = window.__game.game; return { zone: g.zone?.id, gold: g.ch.gold, traits: g.ch.traits, wounded: g.ch.conditions.some((c) => c.id === 'wounded') }; });
    check('wakes somewhere safe', after.zone === 'waystation', after.zone);
    check('lighter purse', after.gold < 120, String(after.gold));
    check('risen once', after.traits.includes('risen_once'));
    check('wounded', after.wounded);
    await snap();
  }),
};

const want = process.argv.slice(2);
let all = true;
for (const [k, fn] of Object.entries(scenarios)) if (!want.length || want.includes(k)) all = (await fn()) && all;
await browser.close();
console.log(all ? '\nALL PASS' : '\nSOME FAILED');
process.exit(all ? 0 : 1);
