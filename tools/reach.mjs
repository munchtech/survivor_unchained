/* Can the survivor get there? Every place a zone asks you to go, checked.
 *
 *   node tools/reach.mjs [waystation|verge|lowford] [day|night]
 *
 * Floods the ground from where the survivor stands, half a metre at a time,
 * with the survivor's own circle against the zone's real colliders (what
 * burns or opens later, the brambles and the Low Ford's gate, counts as
 * open). Then every interactable (doors, people, clues, exits) must have
 * reached ground within its reach, and so must every way into the zone.
 * Prints what cannot be reached, and saves .shots/reach_<zone>.png: pale
 * where you can walk, dark where it is solid, red where it is open ground
 * you cannot get to. Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const [zone = 'waystation', time = 'day'] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 320, height: 180 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
const q = zone === 'lowford' ? `quick=warden&time=${time}` : `quick=warden&zone=${zone}&time=${time}`;
await pg.goto(`http://localhost:5173/?${q}&manual&quality=low`, { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 180000 });
await pg.evaluate(() => window.__advance(1, 10));

const out = await pg.evaluate(() => {
  const g = window.__game.game, b = g.scene.battle, col = b.collision, z = g.zone;
  const R = 0.42, STEP = 0.5, bound = col.bound;
  const open = (c) => c.tag && /^(bramble:|gate$)/.test(c.tag);
  const walk = (x, y) => {
    if (Math.abs(x) > bound || Math.abs(y) > bound) return false;
    for (const c of col.near(x, y, R + 0.5, [])) if (!open(c) && col.overlaps(c, x, y, R)) return false;
    return true;
  };
  const n = Math.floor((bound * 2) / STEP) + 1;
  const at = (i) => -bound + i * STEP;
  const cell = (v) => Math.round((v + bound) / STEP);
  const state = new Uint8Array(n * n); // 0 unknown, 1 solid, 2 reached, 3 open but unreached
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) state[j * n + i] = walk(at(i), at(j)) ? 3 : 1;
  const flood = (x, y) => {
    let i0 = cell(x), j0 = cell(y);
    // From a spot that is itself inside something, step out to open ground.
    if (state[j0 * n + i0] === 1) {
      let best = null;
      for (let dj = -6; dj <= 6; dj++) for (let di = -6; di <= 6; di++) {
        const k = (j0 + dj) * n + i0 + di;
        if (state[k] >= 2 && (!best || di * di + dj * dj < best[0])) best = [di * di + dj * dj, i0 + di, j0 + dj];
      }
      if (!best) return;
      [, i0, j0] = best;
    }
    const stack = [j0 * n + i0];
    while (stack.length) {
      const k = stack.pop();
      if (state[k] !== 3) continue;
      state[k] = 2;
      const i = k % n, j = (k - i) / n;
      if (i > 0) stack.push(k - 1);
      if (i < n - 1) stack.push(k + 1);
      if (j > 0) stack.push(k - n);
      if (j < n - 1) stack.push(k + n);
    }
  };
  flood(b.player.x, b.player.z);
  const reachedNear = (x, y, r) => {
    const i0 = cell(x), j0 = cell(y), m = Math.ceil(r / STEP);
    for (let dj = -m; dj <= m; dj++) for (let di = -m; di <= m; di++) {
      const i = i0 + di, j = j0 + dj;
      if (i < 0 || j < 0 || i >= n || j >= n || state[j * n + i] !== 2) continue;
      if (Math.hypot(at(i) - x, at(j) - y) < r - 0.05) return true;
    }
    return false;
  };
  const bad = [];
  for (const it of z.interactables) if (!reachedNear(it.x, it.z, it.r)) bad.push(`${it.id} "${it.name}" at ${it.x.toFixed(1)},${it.z.toFixed(1)} (reach ${it.r})`);
  for (const from of ['waystation', 'verge', 'lowford', 'death', undefined]) {
    const a = z.arrival?.(from);
    if (a && !reachedNear(a.x, a.z, 1.2)) bad.push(`arrival from ${from ?? 'anywhere'} at ${a.x.toFixed(1)},${a.z.toFixed(1)}`);
  }
  // The picture.
  const cv = document.createElement('canvas');
  cv.width = cv.height = n;
  const ctx = cv.getContext('2d'), img = ctx.createImageData(n, n);
  const pal = { 1: [40, 36, 34], 2: [214, 206, 180], 3: [220, 60, 50] };
  let pockets = 0;
  for (let k = 0; k < n * n; k++) { const c = pal[state[k]]; img.data.set([...c, 255], k * 4); if (state[k] === 3) pockets++; }
  ctx.putImageData(img, 0, 0);
  for (const it of z.interactables) { ctx.fillStyle = bad.some((s) => s.startsWith(`${it.id} `)) ? '#ff00ff' : '#2a70ff'; ctx.fillRect(cell(it.x) - 2, cell(it.z) - 2, 5, 5); }
  return { bad, total: z.interactables.length, pockets: pockets * STEP * STEP, png: cv.toDataURL('image/png') };
});
fs.mkdirSync('.shots', { recursive: true });
fs.writeFileSync(`.shots/reach_${zone}.png`, Buffer.from(out.png.split(',')[1], 'base64'));
console.log(`${zone} (${time}): ${out.total} interactables; ${out.bad.length} unreachable; ${Math.round(out.pockets)} m² of open ground nobody can walk to`);
for (const s of out.bad) console.log('  UNREACHABLE', s);
console.log(`saved .shots/reach_${zone}.png`);
await browser.close();
