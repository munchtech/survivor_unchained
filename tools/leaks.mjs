/* Walk back and forth between the zones and watch what is left behind.
 *
 *   node tools/leaks.mjs [rounds]
 *
 * Travels Waystation -> Verge -> Waystation -> Low Ford -> Waystation, a few
 * rounds, and after each arrival prints what the renderer is holding
 * (geometries, textures, shader programs), how many objects hang off the
 * scene, the DOM nodes of the name plates and barks, and the JS heap. A
 * number that keeps climbing round after round is a leak. Expects the dev
 * server on :5173. */
import { chromium } from 'playwright';

const rounds = Number(process.argv[2] ?? 3);
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl', '--js-flags=--expose-gc'] });
const pg = await browser.newPage({ viewport: { width: 480, height: 270 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
await pg.goto('http://localhost:5173/?quick=warden&bg=hunter&zone=waystation&manual&quality=low', { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
const measure = () => pg.evaluate(() => {
  const g = window.__game.game, r = g.r;
  let objects = 0;
  r.scene.traverse(() => { objects++; });
  if (window.gc) window.gc();
  const info = r.renderer?.info ?? r.gl?.info;
  return {
    zone: g.zone?.id,
    geo: info?.memory.geometries, tex: info?.memory.textures, prog: info?.programs?.length,
    objects, plates: document.querySelectorAll('.plate').length, barks: document.querySelectorAll('.bark').length,
    heapMB: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : null,
  };
});
const go = async (zone, from) => {
  await pg.evaluate(([z, f]) => { const g = window.__game.game; g.world.facts['toll.paid'] = true; g.enterZone(z, f); }, [zone, from]);
  await pg.waitForTimeout(300);
  await pg.evaluate(() => window.__advance(4, 20));
  await pg.waitForTimeout(200);
  return measure();
};
console.log('start   ', JSON.stringify(await measure()));
for (let i = 0; i < rounds; i++) {
  await go('verge', 'waystation');
  await go('waystation', 'verge');
  await go('lowford', 'waystation');
  const m = await go('waystation', 'lowford');
  console.log(`round ${i + 1}`, JSON.stringify(m));
}
await browser.close();
