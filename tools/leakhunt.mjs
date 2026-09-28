/* What leaks, when tools/leaks.mjs says something does.
 *
 *   node tools/leakhunt.mjs [geo|tex] [rounds]
 *
 * Hooks the app's own BufferGeometry (or Texture) class: the renderer adds
 * a 'dispose' listener to everything it uploads, so every GPU object is
 * seen from its upload to its dispose(). Then it travels the zones as
 * leaks.mjs does (Waystation -> Verge -> Waystation -> Low Ford ->
 * Waystation) and after each round counts what is alive by kind (vertex
 * counts, image sizes). A kind whose count climbs round after round is the
 * leak, and its size says what made it. Bone textures are checked against
 * the skeletons in the scene. Expects the dev server on :5173. */
import { chromium } from 'playwright';

const [what = 'geo', rounds = '4'] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl', '--js-flags=--expose-gc'] });
const pg = await browser.newPage({ viewport: { width: 480, height: 270 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
await pg.goto('http://localhost:5173/?quick=warden&bg=hunter&zone=waystation&manual&quality=low', { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });

await pg.evaluate((what) => {
  // The class the app uses (not a second copy of three): from the scene.
  let proto = null;
  window.__game.renderer.scene.traverse((o) => {
    if (proto) return;
    if (what === 'geo' && o.geometry) proto = Object.getPrototypeOf(o.geometry);
    if (what === 'tex' && o.material?.map) proto = Object.getPrototypeOf(o.material.map);
  });
  while (proto && !Object.prototype.hasOwnProperty.call(proto, 'dispose')) proto = Object.getPrototypeOf(proto);
  const live = window.__live = new Set();
  const add = proto.addEventListener, disp = proto.dispose;
  proto.addEventListener = function (type, fn) { if (type === 'dispose') live.add(this); return add.call(this, type, fn); };
  proto.dispose = function () { live.delete(this); return disp.call(this); };
  window.__kind = (g) => {
    if (g.isTexture) { const im = g.image || {}; return `${g.constructor.name} ${im.width}x${im.height}${g.name ? ` "${g.name}"` : ''}`; }
    return `geometry ${Object.keys(g.attributes).map((k) => `${k}:${g.attributes[k].count}`).join(',')} index:${g.index ? g.index.count : 0}${g.name ? ` "${g.name}"` : ''}`;
  };
}, what);

const go = async (zone, from) => {
  await pg.evaluate(([z, f]) => { const g = window.__game.game; g.world.facts['toll.paid'] = true; g.enterZone(z, f); }, [zone, from]);
  await pg.waitForTimeout(300);
  await pg.evaluate(() => window.__advance(4, 20));
  await pg.waitForTimeout(200);
};
const census = () => pg.evaluate(() => {
  window.gc?.();
  const c = {};
  for (const g of window.__live) { const k = window.__kind(g); c[k] = (c[k] || 0) + 1; }
  const bones = new Set();
  window.__game.renderer.scene.traverse((o) => { if (o.isSkinnedMesh && o.skeleton.boneTexture) bones.add(o.skeleton.boneTexture); });
  return { c, total: window.__live.size, bones: bones.size };
});

const rows = [];
for (let i = 0; i < Number(rounds); i++) {
  await go('verge', 'waystation');
  await go('waystation', 'verge');
  await go('lowford', 'waystation');
  await go('waystation', 'lowford');
  rows.push(await census());
}
let climbing = 0;
for (const k of new Set(rows.flatMap((r) => Object.keys(r.c)))) {
  const v = rows.map((r) => r.c[k] || 0);
  if (v.every((x) => x === v[0])) continue;
  const up = v.every((x, i) => i === 0 || x > v[i - 1]);
  if (up) climbing++;
  console.log(`${up ? 'CLIMBS' : 'varies'}  ${v.join(' -> ').padEnd(28)} ${k}`);
}
if (what === 'tex') console.log(`        ${rows.map((r) => r.bones).join(' -> ').padEnd(28)} (bone textures of skeletons in the scene)`);
console.log(`total   ${rows.map((r) => r.total).join(' -> ')}`);
console.log(climbing ? `${climbing} kind(s) climb every round` : 'nothing climbs every round');
await browser.close();
