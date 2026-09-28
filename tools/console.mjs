/* Listen to the console everywhere: each zone, by day and night, with the
 * autopilot fighting where there is fighting, the menus opened and closed,
 * a rest taken. Prints every warning and error once with where it happened.
 *
 *   node tools/console.mjs
 *
 * Expects the dev server on :5173. */
import { chromium } from 'playwright';

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const seen = new Map();
const RUNS = [
  ['title', '?quality=low'],
  ['create', '?screen=create&quality=low'],
  ['lowford', '?quick=arcanist&bg=scholar&auto&quality=low'],
  ['waystation day', '?quick=warden&bg=hunter&zone=waystation&quality=low'],
  ['waystation night', '?quick=warden&bg=hunter&zone=waystation&time=night&quality=low'],
  ['verge day', '?quick=reaver&bg=outcast&zone=verge&at=-40,14&auto&quality=low'],
  ['verge night', '?quick=stalker&bg=devout&zone=verge&at=40,60&auto&time=night&quality=low'],
];
for (const [where, q] of RUNS) {
  const pg = await browser.newPage({ viewport: { width: 800, height: 450 } });
  const note = (kind, text) => { const k = `${kind}: ${text.slice(0, 220)}`; if (!seen.has(k)) seen.set(k, where); };
  pg.on('pageerror', (e) => note('pageerror', e.message));
  pg.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') note(m.type(), m.text()); });
  pg.on('requestfailed', (r) => note('request failed', r.url()));
  await pg.goto(`http://localhost:5173/${q}&manual`, { waitUntil: 'load' });
  await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
  for (let t = 0; t < 40; t += 5) { await pg.evaluate(() => window.__advance(5, 20)); await pg.waitForTimeout(30); }
  // The menus, if there is a game.
  await pg.evaluate(async () => {
    const g = window.__game?.game;
    if (!g?.ch || g.mode !== 'play') return;
    for (const o of ['inventory', 'character', 'journal', 'pause']) { g.openOverlay(o); window.__advance(0.3); g.closeOverlay(); }
    g.openMap(); window.__advance(0.3); g.closeOverlay();
  });
  await pg.waitForTimeout(200);
  console.log(`${where}: done`);
  await pg.close();
}
await browser.close();
console.log(seen.size ? '\n' + [...seen].map(([k, w]) => `[${w}] ${k}`).join('\n') : '\nclean');
