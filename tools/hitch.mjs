/* Frame hitches when places come alive: walks the survivor into each of a
 * zone's places in turn and times the frame that happens in, with what was
 * built on it (creature bakes, new shader programs).
 *
 *   node tools/hitch.mjs [zone] [quality]
 *
 * Times are wall-clock in headless Chromium on a software GPU (SwiftShader,
 * which also compiles code per draw state, and draws a big crowd slowly):
 * read them against each other. New shader programs and creature bakes are
 * what a real machine stalls on too; there should be none after arrival.
 * Expects the dev server on :5173. */
import { chromium } from 'playwright';

const [zone = 'verge', quality = 'low'] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 960, height: 540 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
await pg.goto(`http://localhost:5173/?quick=warden&zone=${zone}&manual&quality=${quality}`, { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 180000 });
await pg.evaluate(() => window.__advance(2, 30));
// Every interactable, one stop per 20 m (what brings a place alive is near
// what you can do there).
const stops = await pg.evaluate(() => {
  const out = {};
  for (const i of window.__game.game.zone?.interactables ?? []) {
    if (Object.values(out).some(([x, z]) => Math.hypot(x - i.x, z - i.z) < 20)) continue;
    out[i.id] = [i.x, i.z];
  }
  return out;
});
const frame = () => pg.evaluate(() => {
  const g = window.__game.game, r = window.__game.renderer;
  const before = r.gl.info.programs?.length ?? 0;
  const known = new Set(r.gl.info.programs);
  const bakes = { ...(g.scene.crowd?.bakeMs ?? {}) };
  const t0 = performance.now();
  window.__advance(1 / 60, 60);
  const ms = performance.now() - t0;
  const after = r.gl.info.programs?.length ?? 0;
  const baked = Object.entries(g.scene.crowd?.bakeMs ?? {}).filter(([k]) => !(k in bakes));
  // What the new programs were for (a material's name, or what made it).
  const fresh = r.gl.info.programs.filter((p) => !known.has(p)).map((p) => {
    const bits = p.cacheKey.split(',');
    return `${p.name}${p.type ? '/' + p.type : ''} [${bits.slice(-3).join(',').slice(0, 60)}]`;
  });
  return { ms: Math.round(ms), programs: after - before, baked, fresh };
});
// A baseline: ordinary frames.
const base = [];
for (let i = 0; i < 6; i++) base.push((await frame()).ms);
console.log(`ordinary frames: ${base.join(' ')} ms`);
for (const [name, [x, z]] of Object.entries(stops)) {
  await pg.evaluate(([x, z]) => { const p = window.__game.game.scene.battle.player; p.x = x; p.z = z; }, [x, z]);
  const f = [];
  for (let i = 0; i < 4; i++) f.push(await frame());
  const worst = f.reduce((a, b) => (b.ms > a.ms ? b : a));
  console.log(`${name.padEnd(10)} worst ${String(worst.ms).padStart(5)} ms  new programs ${f.reduce((a, b) => a + b.programs, 0)}  baked ${f.flatMap((x) => x.baked).map(([k, v]) => `${k} ${v}ms`).join(', ') || '-'}`);
  for (const p of f.flatMap((x) => x.fresh)) console.log(`             + ${p}`);
}
await browser.close();
