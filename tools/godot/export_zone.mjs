/* Export a zone of the three.js game for the Godot slice: the ground, where
 * every tree, rock and kit piece stands, and the lights, read from the zone
 * as the game builds it (so the two are the same place).
 *
 *   node tools/godot/export_zone.mjs [zone]        (default: verge)
 *
 * Writes godot/data/<zone>/:
 *   terrain.json   size, resolution, splat resolution, forest-floor share
 *   heights.bin    float32 heights, row by row from -z, -x
 *   splat.png      the paint: r dirt, g stone, b blight, a mud (written
 *                  here, not by a canvas, which would premultiply the alpha
 *                  and lose the other three wherever there is no mud)
 *   flora.json     per kit piece: kind, scale baked into it, wind, leaf
 *                  recolour and moss (the kind's look), instance count
 *   flora.bin      float32 transforms, 12 per instance (basis x, y, z, origin),
 *                  in flora.json's order
 *   props.json     kit pieces placed one by one: kit, name, transform
 *   lights.json    the lights (lamps, fires): position, colour, strength, reach
 *   landmarks.glb  everything else the zone stands up (the camps, the
 *                  Hunters' Blind, ruins, the KayKit props), world placed
 *   water.json/bin the streams: float32 positions (world), flow (across,
 *                  along) and depth over the bed per vertex, uint32 indices
 * Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';
import zlib from 'node:zlib';

/** RGBA bytes as a PNG, straight alpha. */
function png(rgba, w, h) {
  const chunk = (type, data) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const td = Buffer.concat([Buffer.from(type), data]);
    const crc = Buffer.alloc(4); crc.writeUInt32BE(zlib.crc32(td));
    return Buffer.concat([len, td, crc]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; ihdr[9] = 6; // 8 bits, RGBA
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) rgba.copy(raw, y * (w * 4 + 1) + 1, y * w * 4, (y + 1) * w * 4);
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}

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
  const b64 = (u8) => {
    let s = '';
    for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode(...u8.subarray(i, i + 0x8000));
    return btoa(s);
  };
  const splat = b64(new Uint8Array(tr.splatData.buffer, tr.splatData.byteOffset, tr.splatData.byteLength));

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
  // The rest, as one glTF: every lit mesh that is not the ground, grass,
  // water, flora or a kit piece (those have their own files), where it
  // stands. Instanced pieces are laid out one by one.
  const { GLTFExporter } = await import('/node_modules/three/examples/jsm/exporters/GLTFExporter.js');
  const { decompress } = await import('/node_modules/three/examples/jsm/utils/WebGLTextureUtils.js');
  const scene = new THREE.Scene();
  // The KayKit pieces are quantized (KHR_mesh_quantization), which Godot
  // does not import: plain floats instead.
  const plain = new Map();
  const floats = (g) => {
    if (plain.has(g)) return plain.get(g);
    const out = new THREE.BufferGeometry();
    for (const [k, a] of Object.entries(g.attributes)) {
      const f = new Float32Array(a.count * a.itemSize);
      for (let i = 0; i < a.count; i++) for (let c = 0; c < a.itemSize; c++) f[i * a.itemSize + c] = a.getComponent(i, c);
      out.setAttribute(k, new THREE.BufferAttribute(f, a.itemSize));
    }
    if (g.index) out.setIndex(new THREE.BufferAttribute(Uint32Array.from(g.index.array), 1));
    for (const gr of g.groups) out.addGroup(gr.start, gr.count, gr.materialIndex);
    plain.set(g, out);
    return out;
  };
  const place = (mesh, mw) => { mesh.geometry = floats(mesh.geometry); mesh.matrixAutoUpdate = false; mesh.matrix.copy(mw); scene.add(mesh); };
  const lit = (m) => (Array.isArray(m) ? m : [m]).every((x) => x?.isMeshStandardMaterial);
  const walk = (o) => {
    if (!o.visible || o.isLight || o.isPoints || o.isLine || o.isSprite || o.isSkinnedMesh) return;
    if (o !== zoneRoot && (o.userData?.env || ['terrain', 'grass', 'water'].includes(o.name))) return;
    if (o.isInstancedMesh) {
      if (!o.geometry.userData?.flora && lit(o.material))
        for (let i = 0; i < o.count; i++) { o.getMatrixAt(i, m); place(new THREE.Mesh(o.geometry, o.material), m.clone().premultiply(o.matrixWorld)); }
    } else if (o.isMesh && lit(o.material)) place(new THREE.Mesh(o.geometry, o.material), o.matrixWorld.clone());
    for (const c of o.children) walk(c);
  };
  walk(zoneRoot);
  // The water, raw: its shader needs the stream's own coordinates.
  const water = [];
  zoneRoot.traverse((o) => {
    if (o.name !== 'water' || !o.isMesh) return;
    const g = o.geometry, p = g.attributes.position, v = new THREE.Vector3();
    const pos = [], flow = [], depth = [];
    for (let i = 0; i < p.count; i++) {
      v.fromBufferAttribute(p, i).applyMatrix4(o.matrixWorld);
      pos.push(v.x, v.y, v.z);
      flow.push(g.attributes.aFlow ? g.attributes.aFlow.getX(i) : v.x, g.attributes.aFlow ? g.attributes.aFlow.getY(i) : v.z);
      depth.push(g.attributes.aDepth ? g.attributes.aDepth.getX(i) : 1);
    }
    water.push({ pos, flow, depth, index: g.index ? [...g.index.array] : [...Array(p.count).keys()], stream: !!g.attributes.aFlow });
  });
  const exporter = new GLTFExporter().setTextureUtils({ decompress: (t, max) => decompress(t, max, r.gl) });
  const glb = await exporter.parseAsync(scene, { binary: true, maxTextureSize: 2048 });
  const landmarks = b64(new Uint8Array(glb));
  const landmarkMeshes = scene.children.length;

  const lights = [];
  zoneRoot.traverse((o) => {
    for (const l of o.userData?.sources ?? []) lights.push({ x: l.x, y: l.y, z: l.z, color: '#' + l.color.getHexString(), intensity: l.intensity, distance: l.distance, flicker: l.flicker, on: l.on });
  });
  return {
    terrain: { size: tr.size, res: tr.res, splatRes: tr.splatRes, leaves: tr.leaves },
    heights, splat, flora: [...flora.values()], props, lights, landmarks, landmarkMeshes, water,
  };
});

fs.writeFileSync(`${out}/terrain.json`, JSON.stringify(data.terrain, null, 1) + '\n');
fs.writeFileSync(`${out}/heights.bin`, Buffer.from(data.heights, 'base64'));
fs.writeFileSync(`${out}/splat.png`, png(Buffer.from(data.splat, 'base64'), data.terrain.splatRes, data.terrain.splatRes));
fs.writeFileSync(`${out}/landmarks.glb`, Buffer.from(data.landmarks, 'base64'));
const wmeta = [], wbufs = [];
for (const w of data.water) {
  wmeta.push({ vertices: w.pos.length / 3, indices: w.index.length, stream: w.stream });
  wbufs.push(Buffer.from(new Float32Array(w.pos).buffer), Buffer.from(new Float32Array(w.flow).buffer), Buffer.from(new Float32Array(w.depth).buffer), Buffer.from(new Uint32Array(w.index).buffer));
}
fs.writeFileSync(`${out}/water.json`, JSON.stringify(wmeta) + '\n');
fs.writeFileSync(`${out}/water.bin`, Buffer.concat(wbufs));
const floraMeta = data.flora.map(({ kind, piece, sx, sy, wind, leaves, moss, count }) => ({ kind, piece, sx, sy, wind, leaves, moss, count }));
const all = new Float32Array(data.flora.reduce((n, f) => n + f.t.length, 0));
let at = 0;
for (const f of data.flora) { all.set(f.t, at); at += f.t.length; }
fs.writeFileSync(`${out}/flora.json`, JSON.stringify(floraMeta, null, 1) + '\n');
fs.writeFileSync(`${out}/flora.bin`, Buffer.from(all.buffer));
fs.writeFileSync(`${out}/props.json`, JSON.stringify(data.props) + '\n');
fs.writeFileSync(`${out}/lights.json`, JSON.stringify(data.lights, null, 1) + '\n');
console.log(`${zone}: terrain ${data.terrain.res}² over ${data.terrain.size} m; ${floraMeta.length} flora pieces, ${floraMeta.reduce((n, f) => n + f.count, 0)} placed; ${data.props.length} props; ${data.landmarkMeshes} landmark meshes; ${data.water.length} waters; ${data.lights.length} lights`);
await browser.close();
