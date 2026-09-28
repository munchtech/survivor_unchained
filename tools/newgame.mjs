/* A new player's first hour, clicked through the way a person would.
 *
 *   node tools/newgame.mjs [calling]        (stalker by default)
 *
 * From an empty save: the title, New Journey, every step of creation by
 * clicking (a calling, the second weapon and ability, a blessing, an origin,
 * a name, colours), Begin; then the autopilot plays the prologue to the
 * Waystation. Checks that what was chosen is what arrived (calling, weapon,
 * ability, blessing, colours), that the journey saved, that a reload offers
 * it on the title and Continue brings it back, and that the first expedition
 * out of town carries the chosen blessing and weapon. Screenshots land in
 * .shots/new_*.png. Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const calling = process.argv.slice(2).find((a) => !a.startsWith('--')) ?? 'stalker';
fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
// A page torn down mid-load (a reload) aborts its fetches; that is the
// tool's doing, not the game's.
let leaving = false;
pg.on('pageerror', (e) => { if (leaving) return; errors.push(e.message); console.log('[pageerror]', e.message); });
pg.on('console', (m) => { if (m.type() === 'error' && !leaving) { errors.push(m.text()); console.log('[error]', m.text().slice(0, 300)); } });

let ok = true;
const check = (label, pass, detail = '') => { console.log(`${pass ? 'PASS' : 'FAIL'}  ${label}${detail ? `  (${detail})` : ''}`); ok &&= !!pass; };
const adv = (s = 0.4) => pg.evaluate((s) => window.__advance(s, 30), s);
const shot = (n) => pg.screenshot({ path: `.shots/new_${n}.png`, timeout: 180000 });
const click = async (sel, label) => {
  const el = pg.locator(sel).first();
  if (!(await el.count())) { check(`found ${label}`, false, sel); return false; }
  await el.click();
  await adv(0.2);
  return true;
};
const boot = async (q) => {
  leaving = true;
  await pg.goto(`http://localhost:5173/?${q}&manual&quality=low`, { waitUntil: 'load' });
  leaving = false;
  await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
  await adv(1);
};
/** Advance until the page says so (transitions run on real timers too). */
const until = async (fn, secs = 30) => {
  for (let i = 0; i < secs * 2; i++) {
    if (await pg.evaluate(fn)) return true;
    await pg.waitForTimeout(250);
    await adv(0.25);
  }
  return false;
};

// --continue: skip creation and the prologue, from the save the last full run left.
const SAVE = '.shots/newgame_save.json';
const resume = process.argv.includes('--continue') && fs.existsSync(SAVE);

// An empty save: nobody has played here before.
await pg.goto('http://localhost:5173/?manual', { waitUntil: 'load' });
await pg.evaluate((dump) => { localStorage.clear(); if (dump) for (const [k, v] of Object.entries(JSON.parse(dump))) localStorage.setItem(k, v); }, resume ? fs.readFileSync(SAVE, 'utf8') : null);
await boot('auto');
if (!resume) {
await shot('title');
check('the title offers no Continue', !(await pg.locator('.tm-item', { hasText: 'Continue' }).count()));
await click('.tm-item:has-text("New Journey")', 'New Journey');
await adv(0.6);

// Creation, step by step.
const cap = calling[0].toUpperCase() + calling.slice(1);
await click(`.choice:has-text("${cap}")`, `the ${cap}`);
await shot('create_calling');
await click('.btn.primary:has-text("Next")', 'Next: Arms');
const weapons = pg.locator('.choice:not(.tall)');
const pickWeapon = (await weapons.count()) > 1 ? 1 : 0;
await weapons.nth(pickWeapon).click(); await adv(0.2);
const abilities = pg.locator('.choice.tall');
if ((await abilities.count()) > 1) { await abilities.nth(1).click(); await adv(0.2); }
const blessings = pg.locator('.boon-pick');
check('six starting blessings to choose from', (await blessings.count()) === 6, `${await blessings.count()}`);
await blessings.nth(3).click(); await adv(0.2);
await shot('create_arms');
const chosen = await pg.evaluate(() => {
  const d = window.__ui.creation?.value ?? null;
  return d && { archetype: d.archetype, weaponItem: d.weaponItem, ability: d.ability, startBoon: d.startBoon };
});
check('the draft remembers the arms', chosen && chosen.archetype === calling, JSON.stringify(chosen));
await click('.btn.primary:has-text("Next")', 'Next: Origin');
const origins = pg.locator('.choice');
await origins.nth(Math.min(2, (await origins.count()) - 1)).click(); await adv(0.2);
await click('.btn.primary:has-text("Next")', 'Next: Name');
const name = pg.locator('input').first();
await name.fill('Wren Tallow');
await adv(0.2);
const swatches = pg.locator('.swatch');
if ((await swatches.count()) > 2) { await swatches.nth(2).click(); await adv(0.2); }
const dyes = pg.locator('.dye:not(.skin)');
if ((await dyes.count()) > 3) { await dyes.nth(3).click(); await adv(0.2); }
await adv(0.6);
await shot('create_name');
const draft = await pg.evaluate(() => { const d = window.__ui.creation?.value; return d && { ...d }; });
await click('.btn.primary.begin', 'Begin the journey');
for (let i = 0; i < 6; i++) await adv(0.5);
await shot('begin');

const who = await pg.evaluate(() => {
  const g = window.__game.game, ch = g.ch, b = g.scene.battle;
  return {
    zone: g.zone?.id, name: ch?.name, archetype: ch?.archetype, ability: ch?.ability, startBoon: ch?.startBoon, palette: ch?.palette, cloak: ch?.cloak,
    weapon: ch?.equipment?.weapon?.def, battle: !!b, boons: b ? Object.keys(b.boons).filter((k) => b.boons[k] > 0) : [],
  };
});
check('the prologue begins', who.zone === 'lowford' && who.battle, JSON.stringify({ zone: who.zone }));
check('named as typed', who.name === 'Wren Tallow', who.name);
check('the calling chosen', who.archetype === calling, who.archetype);
check('the ability chosen', draft && who.ability === draft.ability, `${who.ability} vs ${draft?.ability}`);
check('the weapon chosen, in hand', draft && who.weapon === draft.weaponItem, `${who.weapon} vs ${draft?.weaponItem}`);
check('the blessing chosen, kept', draft && who.startBoon === draft.startBoon, `${who.startBoon}`);
check('the blessing chosen, in the fight', who.boons.includes(who.startBoon), who.boons.join(','));
check('the colours chosen', draft && who.palette === draft.palette && who.cloak === draft.cloak, `${who.palette}/${who.cloak}`);

// The autopilot plays the prologue.
let t = 0, stage = '', drafts = 0;
while (t < 420) {
  for (let s = 0; s < 10; s += 5) { await pg.evaluate(() => window.__advance(5, 30)); await pg.waitForTimeout(20); }
  t += 10;
  const st = await pg.evaluate(() => { const g = window.__game.game; return { zone: g.zone?.id, stage: g.zone?.debug?.().stage, lvl: g.scene.battle?.ember.level, hp: Math.round(g.scene.battle?.player.hp ?? 0), deaths: g.ch.stats.deaths }; });
  if (st.stage !== stage) { stage = st.stage; console.log(`  t=${t}s`, JSON.stringify(st)); }
  if (t === 100 || t === 200) await shot(`prologue_${t}`);
  if (st.zone === 'waystation') break;
}
const town = await pg.evaluate(() => { const g = window.__game.game; return { zone: g.zone?.id, done: !!g.world.facts['prologue.done'], level: g.ch.level, gold: g.ch.gold, overlay: window.__ui.overlay?.value ?? null }; });
for (let i = 0; i < 6; i++) await adv(0.5);
await shot('town');
check('reached the Waystation', town.zone === 'waystation', JSON.stringify(town));
check('the prologue counts as done', town.done);
fs.writeFileSync(SAVE, await pg.evaluate(() => JSON.stringify({ ...localStorage })));
}

// Saved? A reload offers the journey, and Continue brings it back.
const saved = await pg.evaluate(() => Object.keys(localStorage).filter((k) => /save|slot|journey/i.test(k)).length);
check('the journey is saved', saved > 0, `${saved} keys`);
await boot('');
await shot('title_again');
const cont = pg.locator('.tm-item:has-text("Continue")');
check('the title offers Continue', (await cont.count()) === 1, await cont.first().innerText().catch(() => ''));
check('Continue names the survivor', /Wren Tallow/.test(await cont.first().innerText().catch(() => '')));
await cont.first().click();
await until(() => window.__game.game.zone?.id === 'waystation' && !window.__game.game.scene.showcase);
for (let i = 0; i < 4; i++) await adv(0.5);
const back = await pg.evaluate(() => { const g = window.__game.game; return { zone: g.zone?.id, name: g.ch?.name, showcase: !!g.scene.showcase, screen: window.__ui.screen?.value }; });
check('Continue returns to the Waystation', back.zone === 'waystation' && back.name === 'Wren Tallow', JSON.stringify(back));
check('the camera is the game\'s again', !back.showcase);
await shot('continued');

// The first expedition: through the east gate into the Verge.
const gate = await pg.evaluate(() => {
  const g = window.__game.game, it = g.zone.interactables.find((i) => i.id === 'gate:east');
  if (!it) return 'missing';
  const l = it.locked?.(); if (l) return `locked: ${l}`;
  const p = g.scene.battle.player; p.x = it.x; p.z = it.z; window.__advance(0.2, 30);
  it.act(); return 'ok';
});
for (let i = 0; i < 12; i++) {
  await pg.waitForTimeout(400);
  await adv(0.5);
  if ((await pg.evaluate(() => window.__game.game.zone?.id)) === 'verge') break;
}
const out = await pg.evaluate(() => { const g = window.__game.game, b = g.scene.battle; return { zone: g.zone?.id, boons: b ? Object.keys(b.boons).filter((k) => b.boons[k] > 0) : [], weapons: b?.weapons.map((w) => w.id) ?? [], blessing: g.ch.startBoon }; });
check('out through the gate', out.zone === 'verge', `${gate} -> ${out.zone}`);
check('the expedition carries the blessing', out.boons.includes(out.blessing), out.boons.join(','));
check('and a weapon', out.weapons.length > 0, out.weapons.join(','));
await adv(1);
await shot('verge');
check('no page errors', errors.length === 0, errors.slice(0, 3).join(' | '));
console.log(ok ? '\nALL PASS' : '\nSOME FAILED');
await browser.close();
process.exit(ok ? 0 : 1);
