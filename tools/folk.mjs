/* The Waystation's townsfolk, left to themselves for three minutes.
 *
 *   node tools/folk.mjs [day|night|dusk|dawn]
 *
 * Checks every lane of the walk graph against the colliders, then runs the
 * town and reports anyone who spent eight seconds walking without getting
 * anywhere (with what is solid around them and the trail that led there),
 * how many are out and what they are doing at the end, and where people
 * went. Expects the dev server on :5173. */
import { chromium } from 'playwright';
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 320, height: 180 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message, e.stack?.split('\n').slice(0,3).join(' | ')));
const time = process.argv[2] || 'day';
await pg.goto(`http://localhost:5173/?quick=warden&bg=hunter&zone=waystation&manual&quality=low&time=${time}`, { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
const lanes = await pg.evaluate(() => window.__game.game.zone.debug().lanes);
console.log(lanes.length ? `lanes through something solid: ${lanes.join('; ')}` : 'lanes: all clear');
const hist = [];
for (let t = 0; t < 180; t += 2) {
  const s = await pg.evaluate(() => { window.__advance(2, 30); return window.__game.game.zone.debug().walkers; });
  hist.push(s);
}
// Stuck: walking, not inside, and moved < 0.6 m over 8 s.
const stuck = new Map();
for (let i = 4; i < hist.length; i++) {
  const now = hist[i], then = hist[i - 4];
  now.forEach((w) => {
    const k = w.id, p = then.find((q) => q.id === k);
    if (!p || w.state !== 'walk' || w.lead) return;
    if (!hist.slice(i - 4, i + 1).every((sn) => sn.find((q) => q.id === k)?.state === 'walk')) return;
    if (Math.hypot(w.x - p.x, w.z - p.z) < 0.6 && !stuck.has(`${k}`)) stuck.set(`${k}`, { trail: hist.slice(Math.max(0, i - 6), i + 1).map((sn) => sn.find((q) => q.id === k)).filter(Boolean).map((q) => `${q.x},${q.z} ${q.state} v${q.v} ${q.path.split('>')[0]}`).join(' | '), txt: `${w.role} at ${w.x},${w.z} -> ${w.dest} (from ${w.at}) t=${i * 2} v=${w.v} path=${w.path}`, x: w.x, z: w.z });
  });
}
const states = {};
for (const w of hist.at(-1)) states[`${w.role}:${w.state}`] = (states[`${w.role}:${w.state}`] ?? 0) + 1;
console.log(time, 'final', JSON.stringify(states), 'count', hist.at(-1).length);
for (const v of stuck.values()) {
  const near = await pg.evaluate(([x, z]) => window.__game.game.scene.zone.collision.within(x, z, 1.6).map((c) => `${c.kind}@${c.x.toFixed(1)},${c.z.toFixed(1)}${c.r ? ' r' + c.r.toFixed(2) : ' ' + (c.hw ?? 0).toFixed(1) + 'x' + (c.hd ?? 0).toFixed(1)}${c.soft ? ' soft' : ''}${c.tag ? ' ' + c.tag : ''}`).join('; '), [v.x, v.z]);
  console.log('  stuck', v.txt, '|', near);
  console.log('     trail:', v.trail);
}
// Where people went.
const visits = {};
for (const snap of hist) for (const w of snap) if (w.state === 'busy' || w.state === 'inside') visits[w.at] = (visits[w.at] ?? 0) + 1;
console.log('  visits', JSON.stringify(visits));
await browser.close();
