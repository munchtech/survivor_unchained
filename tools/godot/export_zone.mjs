/* Export a zone of the three.js game for the Godot slice: the ground, where
 * every tree, rock and kit piece stands, and the lights, read from the zone
 * as the game builds it (so the two are the same place).
 *
 *   node tools/godot/export_zone.mjs [zone]        (default: verge)
 *
 * Writes godot/data/<zone>/:
 *   terrain.json   size, resolution, splat resolution, forest-floor share
 *   heights.bin    float32 heights, row by row from -z, -x
 *   splat.png      the paint: r dirt, g stone, b blight, a mud
 *   flora.json     per kit piece: kind, scale baked into it, wind, leaf
 *                  recolour and moss (the kind's look), instance count
 *   flora.bin      float32 transforms, 12 per instance (basis x, y, z, origin),
 *                  in flora.json's order
 *   props.json     kit pieces placed one by one: kit, name, transform
 *   lights.json    the lights (lamps, fires): position, colour, strength, reach
 * Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const zone = process.argv[2] ?? 'verge';
const out = `godot/data/${zone}`;
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 640, height: 400 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
await pg.goto(`http://localhost:5173/?quick=warden&zone=${zone}&manual&quality=low`, { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 180000 });

const data = await pg.evaluate(async () => {
  const THREE = await import('/node_modules/.vite/deps/three.js');
  const r = window.__game.renderer;
  const tr = window.__game.game.scene.zone.terrain;
  const zoneRoot = window.__game.game.scene.zone.root;
  const bytes = new Uint8Array(new Float32Array(tr.heights).buffer);
  let bin = '';
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  const heights = btoa(bin);
  // Splat as a PNG, through a canvas.
  const c = document.createElement('canvas');
  c.width = c.height = tr.splatRes;
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(tr.splatRes, tr.splatRes);
  img.data.set(tr.splatData);
  ctx.putImageData(img, 0, 0);
  const splat = c.toDataURL('image/png').split(',')[1];

  const flora = new Map();
  const props = [];
  const m = new THREE.Matrix4(), s = new THREE.Matrix4();
  const tf = (mm) => { const e = mm.elements; return [e[0], e[1], e[2], e[4], e[5], e[6], e[8], e[9], e[10], e[12], e[13], e[14]]; };
  zoneRoot.updateMatrixWorld(true);
  zoneRoot.traverse((o) => {
    const fl = o.geometry?.userData?.flora;
    if (o.isInstancedMesh && fl) {
      // A piece has a mesh per part, all at the same places: take one.
      const k = `${o.id}`.length && `${o.name}|${fl.piece}|${o.count}|${o.instanceMatrix.array[12]}`;
      if (flora.has(k)) return;
      s.makeScale(fl.sx, fl.sy, fl.sx);
      const list = [];
      for (let i = 0; i < o.count; i++) { o.getMatrixAt(i, m); m.premultiply(o.matrixWorld).multiply(s); list.push(...tf(m)); }
      flora.set(k, { mesh: o.name, kind: fl.kind, piece: fl.piece, sx: fl.sx, sy: fl.sy, wind: fl.wind, leaves: fl.leaves ?? null, moss: fl.moss ?? 0, count: o.count, t: list });
      return;
    }
    if (o.userData?.env) props.push({ id: o.userData.env, t: tf(o.matrixWorld) });
  });
  const lights = [];
  zoneRoot.traverse((o) => {
    for (const l of o.userData?.sources ?? []) lights.push({ x: l.x, y: l.y, z: l.z, color: '#' + l.color.getHexString(), intensity: l.intensity, distance: l.distance, flicker: l.flicker, on: l.on });
  });
  return {
    terrain: { size: tr.size, res: tr.res, splatRes: tr.splatRes, leaves: tr.leaves },
    heights, splat, flora: [...flora.values()], props, lights,
  };
});

fs.writeFileSync(`${out}/terrain.json`, JSON.stringify(data.terrain, null, 1) + '\n');
fs.writeFileSync(`${out}/heights.bin`, Buffer.from(data.heights, 'base64'));
fs.writeFileSync(`${out}/splat.png`, Buffer.from(data.splat, 'base64'));
const floraMeta = data.flora.map(({ kind, piece, sx, sy, wind, leaves, moss, count }) => ({ kind, piece, sx, sy, wind, leaves, moss, count }));
const all = new Float32Array(data.flora.reduce((n, f) => n + f.t.length, 0));
let at = 0;
for (const f of data.flora) { all.set(f.t, at); at += f.t.length; }
fs.writeFileSync(`${out}/flora.json`, JSON.stringify(floraMeta, null, 1) + '\n');
fs.writeFileSync(`${out}/flora.bin`, Buffer.from(all.buffer));
fs.writeFileSync(`${out}/props.json`, JSON.stringify(data.props) + '\n');
fs.writeFileSync(`${out}/lights.json`, JSON.stringify(data.lights, null, 1) + '\n');
console.log(`${zone}: terrain ${data.terrain.res}² over ${data.terrain.size} m; ${floraMeta.length} flora pieces, ${floraMeta.reduce((n, f) => n + f.count, 0)} placed; ${data.props.length} props; ${data.lights.length} lights`);
await browser.close();
