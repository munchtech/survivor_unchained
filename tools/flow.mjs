/* The roads between places, and a night's sleep, driven for real.
 *
 *   node tools/flow.mjs
 *
 * From the Waystation: pay the toll and take the Old Road east, come back
 * through the Verge's gate, walk down to the Low Ford and back up it, then
 * sleep at the inn and read the morning. Checks where you end up, what it
 * cost and that the day turned. Expects the dev server on :5173. */
import { chromium } from 'playwright';

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM || undefined,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'],
});
const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
const errors = [];
page.on('pageerror', (e) => { errors.push(e.message); console.log('[pageerror]', e.message); });
await page.goto('http://localhost:5173/?quick=warden&bg=devout&zone=waystation&manual&quality=low', { waitUntil: 'load' });
await page.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });

let ok = true;
const check = (label, pass, detail = '') => { console.log(`${pass ? 'PASS' : 'FAIL'}  ${label}${detail ? `  (${detail})` : ''}`); ok &&= !!pass; };
const ev = (fn, arg) => page.evaluate(fn, arg);
const state = () => ev(() => { const g = window.__game.game, p = g.scene.battle?.player; return { zone: g.zone?.id, x: Math.round(p?.x ?? 0), z: Math.round(p?.z ?? 0), gold: g.ch.gold, day: g.world.day, time: g.world.time, overlay: document.querySelector('.rest, .report') ? 'rest' : null }; });
const act = (id) => ev((id) => {
  const g = window.__game.game, it = g.zone.interactables.find((i) => i.id === id);
  if (!it) return 'missing';
  if (it.when && !it.when()) return 'unavailable';
  const l = it.locked?.(); if (l) return `locked: ${l}`;
  const p = g.scene.battle.player; p.x = it.x; p.z = it.z; window.__advance(0.2, 30);
  it.act(); return 'ok';
}, id);
const settle = async (ms = 3200) => { await page.waitForTimeout(ms); await ev(() => window.__advance(0.5, 30)); };

await ev(() => window.__advance(1, 30));
const s0 = await state();
check('starts in the Waystation', s0.zone === 'waystation', JSON.stringify(s0));

check('east gate', (await act('gate:east')) === 'ok');
await settle();
const s1 = await state();
check('arrives in the Verge', s1.zone === 'verge', JSON.stringify(s1));
check('paid the toll', s1.gold === s0.gold - 5, `${s0.gold} -> ${s1.gold}`);
check('the world runs after travel', await ev(() => { const g = window.__game.game; const t0 = g.scene.battle.time; window.__advance(0.5, 30); return !g.scene.simPaused && g.scene.battle.time > t0; }));

check('Verge exit', (await act('exit')) === 'ok');
await settle();
const s2 = await state();
check('back in the Waystation', s2.zone === 'waystation', JSON.stringify(s2));
check('by the east gate', s2.x > 25, `x=${s2.x}`);

check('east gate again, no second toll', (await act('gate:east')) === 'ok');
await settle();
const s3 = await state();
check('toll paid once', s3.zone === 'verge' && s3.gold === s1.gold, `gold ${s3.gold}`);
await act('exit'); await settle();

check('south gate', (await act('gate:south')) === 'ok');
await settle();
const s4 = await state();
check('down to the Low Ford', s4.zone === 'lowford', JSON.stringify(s4));
check('at the north end of it', s4.z < -80, `z=${s4.z}`);
// Walk north past the old gate.
await ev(() => { const p = window.__game.game.scene.battle.player; p.z = -108; window.__advance(0.5, 30); });
await settle();
const s5 = await state();
check('up the road to town again', s5.zone === 'waystation', JSON.stringify(s5));

// A night at the inn: Rook's rest, then the morning.
await ev(() => { const g = window.__game.game; g.ch.gold = Math.max(g.ch.gold, 10); g.openRest(); });
await page.waitForTimeout(300);
await ev(() => window.__game.game.rest('sleep'));
await page.waitForTimeout(1600);
const s6 = await state();
check('slept', s6.day === s0.day + 1 && s6.time === 'day', JSON.stringify(s6));
const report = await ev(() => document.querySelector('.report')?.textContent?.slice(0, 200) ?? '');
check('a morning report', report.length > 10, report);
await page.screenshot({ path: '.shots/flow_report.png', timeout: 180000 });
await ev(() => window.__game.game.finishRest());
await settle(1500);
check('no page errors', errors.length === 0, errors[0]);
await browser.close();
console.log(ok ? '\nALL PASS' : '\nSOME FAILED');
process.exit(ok ? 0 : 1);
