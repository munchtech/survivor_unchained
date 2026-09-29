/* Export the web game's zones as level data for the Godot game: each zone as
 * the game builds it (so the two are the same place), written once here and
 * from then on a Godot asset, improved piece by piece.
 *
 *   node tools/godot/export_zone.mjs [zone...]     (default: lowford waystation verge)
 *
 * Writes godot/data/zones/<zone>/:
 *   zone.json      the rest, as data: the terrain's size and resolution, the
 *                  playable bound, where the survivor starts, the air (the
 *                  zone's atmosphere), every light (lamps, fires, windows;
 *                  on or off; which glowing bits go dark with it), the fires
 *                  (flames and smoke), chimneys, lamps with moths, every
 *                  collider in order (the runtime refers to some by id), the
 *                  pieces the runtime moves or hides (named nodes in the
 *                  glTF), the named places and paths the runtime reads, and
 *                  what the map is drawn from
 *   heights.bin    float32 heights, row by row from -z, -x
 *   splat.png      the paint: r dirt, g stone, b blight, a mud (written
 *                  here, not by a canvas, which would premultiply the alpha)
 *   flora.json/bin per kit piece: kind, scale baked into it, wind, leaf
 *                  recolour and moss; float32 transforms, 12 per copy
 *   props.json     the world kits' pieces, placed one by one (the houses
 *                  and walls too, which the web game merges)
 *   landmarks.glb  everything else the zone stands up (the camps, the
 *                  Blind, ruins, the KayKit props), world placed; the pieces
 *                  the runtime reaches for (glowing bits, night-only ones,
 *                  a gate, a wheel) as nodes of their own, which zone.json
 *                  names
 *   water.json/bin every body of water: float32 positions, flow (across,
 *                  along), depth over the bed; uint32 indices; its colours
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

/** Where each zone is, and the module that names its places. */
const ZONES = {
  lowford: { query: 'quick=warden', module: '/src/world/zones/lowford.ts' },
  waystation: { query: 'quick=warden&zone=waystation', module: '/src/world/zones/waystation.ts' },
  verge: { query: 'quick=warden&zone=verge', module: '/src/world/zones/verge.ts' },
};

/* Which kit file holds each kit material, for the Godot game to take it
 * from (godot/data/zones/kit_materials.json). */
{
  const index = {};
  for (const kit of ['village', 'custom', 'props', 'nature']) {
    const dir = `public/assets/env/${kit}`;
    for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.gltf')).sort()) {
      const j = JSON.parse(fs.readFileSync(`${dir}/${f}`, 'utf8'));
      for (const m of j.materials ?? []) if (m.name && !index[m.name]) index[m.name] = `${kit}/${f.replace(/\.gltf$/, '')}`;
    }
  }
  fs.mkdirSync('godot/data/zones', { recursive: true });
  fs.writeFileSync('godot/data/zones/kit_materials.json', JSON.stringify(index, null, 1) + '\n');
}

const wanted = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(ZONES);
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });

for (const zone of wanted) {
  const spec = ZONES[zone];
  if (!spec) throw new Error(`no zone ${zone}`);
  const out = `godot/data/zones/${zone}`;
  fs.mkdirSync(out, { recursive: true });
  const pg = await browser.newPage({ viewport: { width: 640, height: 400 } });
  pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
  await pg.goto(`http://localhost:5173/?${spec.query}&time=day&manual&quality=low`, { waitUntil: 'load' });
  await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 180000 });

  const data = await pg.evaluate(async ({ zone, module }) => {
    const THREE = await import('/node_modules/.vite/deps/three.js');
    const game = window.__game.game;
    const zb = game.scene.zone;
    const build = zb.root.userData.build;
    if (!build) throw new Error(`zone ${zone} does not expose its build`);
    const kit = build.kit;
    const tr = zb.terrain;
    const root = zb.root;
    root.updateMatrixWorld(true);
    const b64 = (u8) => {
      let s = '';
      for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode(...u8.subarray(i, i + 0x8000));
      return btoa(s);
    };
    const tf = (mm) => { const e = mm.elements; return [e[0], e[1], e[2], e[4], e[5], e[6], e[8], e[9], e[10], e[12], e[13], e[14]]; };

    /* ------------------------------------ what the runtime reaches into -- */
    // Pieces the runtime moves, hides, lights or burns go into the glTF as
    // nodes of their own, named, at their own place (a wheel turns about its
    // axle), what is in them relative to them. Names use '-' (Godot keeps
    // it; ':' it does not). A piece keeps the first name it is given.
    const tagged = new Map();
    const tag = (o, n) => { if (o && !tagged.has(o)) tagged.set(o, n); };
    const sources = kit.sources;
    const srcIndex = (s) => sources.indexOf(s);
    const refs = {};
    if (zone === 'verge') {
      build.brambles.forEach((b, i) => tag(b.mesh, `bramble-${i}`));
      refs.brambles = build.brambles.map((b, i) => ({ x: b.x, z: b.z, collider: b.collider, node: `bramble-${i}` }));
      tag(build.pumpWheel, 'pump_wheel');
      tag(build.thing, 'thing');
      build.cageBars.forEach((c, i) => tag(c, `cage-${i}`));
      refs.cages = build.cageBars.map((_, i) => `cage-${i}`);
      tag(build.vaultGlow, 'vault_glow');
      refs.postFire = srcIndex(build.postFire);
      refs.blindFire = srcIndex(build.blindFire);
    }
    if (zone === 'lowford') {
      build.pylons.forEach((p, i) => tag(p.flame, `pylon_flame-${i}`));
      refs.pylons = build.pylons.map((p, i) => ({ x: p.x, z: p.z, light: srcIndex(p.src), collider: p.collider, top: p.top, flame: `pylon_flame-${i}` }));
      refs.campfire = srcIndex(build.campfire);
      build.gate.forEach((g, i) => tag(g, `gate-${i}`));
      refs.gate = build.gate.map((_, i) => `gate-${i}`);
    }
    // The bits that glow with a light (shown while it is on), and what only
    // shows after dark.
    sources.forEach((s, i) => s.glow.forEach((g, k) => tag(g, `glow-${i}-${k}`)));
    kit.nightOnly.forEach((o, i) => tag(o, `night-${i}`));

    /* -------------------------------------------------- lights and fire -- */
    const hex = (c) => '#' + c.getHexString();
    const lights = sources.map((s) => ({ x: s.x, y: s.y, z: s.z, color: hex(s.color), intensity: s.intensity, distance: s.distance, flicker: s.flicker, on: s.on, glow: s.glow.map((g) => tagged.get(g)) }));
    const nightNodes = kit.nightOnly.map((o) => tagged.get(o));
    const fires = kit.fires.map((f) => ({ x: f.x, y: f.y, z: f.z, size: f.size, light: srcIndex(f.src) }));
    const chimneys = kit.chimneys.map((c) => ({ x: c.x, y: c.y, z: c.z }));
    const moths = kit.mothLamps.map(srcIndex);
    if (zone === 'waystation') {
      refs.doors = build.doors;
      refs.stalls = build.stalls;
    }

    /* --------------------------------------------------------- terrain -- */
    const heights = b64(new Uint8Array(new Float32Array(tr.heights).buffer));
    const splat = b64(new Uint8Array(tr.splatData.buffer, tr.splatData.byteOffset, tr.splatData.byteLength));

    /* ----------------------------------------------- flora and kit props -- */
    const flora = new Map();
    const props = [];
    const m = new THREE.Matrix4(), s = new THREE.Matrix4();
    root.traverse((o) => {
      const fl = o.geometry?.userData?.flora;
      if (o.isInstancedMesh && fl) {
        // A piece has a mesh per part, all at the same places: take one.
        const k = `${o.name}|${fl.piece}|${o.count}|${o.instanceMatrix.array[12]}`;
        if (flora.has(k)) return;
        s.makeScale(fl.sx, fl.sy, fl.sx);
        const list = [];
        for (let i = 0; i < o.count; i++) { o.getMatrixAt(i, m); m.premultiply(o.matrixWorld).multiply(s); list.push(...tf(m)); }
        flora.set(k, { mesh: o.name, kind: fl.kind, piece: fl.piece, sx: fl.sx, sy: fl.sy, wind: fl.wind, leaves: fl.leaves ?? null, moss: fl.moss ?? 0, count: o.count, t: list });
        return;
      }
      if (o.userData?.env) props.push({ id: o.userData.env, t: tf(o.matrixWorld) });
      // A house or a wall: the village kit's pieces, merged here; placed one
      // by one there.
      if (o.userData?.pieces && o.visible) for (const p of o.userData.pieces) props.push({ id: `village/${p.name}`, t: tf(m.fromArray(p.m).premultiply(o.matrixWorld)) });
    });

    /* -------------------------------------------------------- landmarks -- */
    // Everything else, as one glTF. Quantized geometry (the KayKit packs) as
    // plain floats, which Godot reads.
    const { GLTFExporter } = await import('/node_modules/three/examples/jsm/exporters/GLTFExporter.js');
    const { decompress } = await import('/node_modules/three/examples/jsm/utils/WebGLTextureUtils.js');
    const scene = new THREE.Scene();
    const plain = new Map();
    const floats = (g, flat) => {
      const key = flat ? `${g.uuid}|flat` : g.uuid;
      if (plain.has(key)) return plain.get(key);
      if (flat) {
        // Faceted, as three.js draws a flat-shaded material: a normal per face.
        const o = floats(g, false).toNonIndexed();
        o.computeVertexNormals();
        plain.set(key, o);
        return o;
      }
      const o = new THREE.BufferGeometry();
      for (const [k, a] of Object.entries(g.attributes)) {
        const f = new Float32Array(a.count * a.itemSize);
        for (let i = 0; i < a.count; i++) for (let c = 0; c < a.itemSize; c++) f[i * a.itemSize + c] = a.getComponent(i, c);
        o.setAttribute(k, new THREE.BufferAttribute(f, a.itemSize));
      }
      if (g.index) o.setIndex(new THREE.BufferAttribute(Uint32Array.from(g.index.array), 1));
      for (const gr of g.groups) o.addGroup(gr.start, gr.count, gr.materialIndex);
      plain.set(key, o);
      return o;
    };
    const drawn = (mat) => (Array.isArray(mat) ? mat : [mat]).every((x) => x?.isMeshStandardMaterial || x?.isMeshBasicMaterial);
    // The world kits' materials (their textures are the kits' KTX2 sheets)
    // go by name only: the Godot game takes them from the kits themselves,
    // weathered as here, and a sheet is not copied into every zone.
    const SLOTS = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'emissiveMap', 'alphaMap', 'bumpMap'];
    //
    // What glTF cannot say goes in the material's name, as 'key=value|...'
    // (the Godot game reads it, World/Landmarks.cs):
    //   kit=NAME     a kit material, taken from the kit (textures left out)
    //   hdr=R,G,B    an unlit colour brighter than 1 (a flame, embers), linear
    //   add          drawn additively (light spilled on the ground)
    //   name=NAME    the material's own name
    const exported = new Map();
    const look = (mat) => {
      if (Array.isArray(mat)) return mat.map(look);
      if (exported.has(mat)) return exported.get(mat);
      const tags = [];
      let c = mat;
      if (SLOTS.some((k) => mat[k]?.isCompressedTexture)) {
        c = mat.clone();
        for (const k of SLOTS) c[k] = null;
        tags.push(`kit=${mat.name}`);
      }
      if (mat.isMeshBasicMaterial && Math.max(mat.color.r, mat.color.g, mat.color.b) > 1) tags.push(`hdr=${[mat.color.r, mat.color.g, mat.color.b].map((v) => +v.toFixed(4)).join(',')}`);
      if (mat.blending === THREE.AdditiveBlending) tags.push('add');
      if (tags.length) {
        if (c === mat) c = mat.clone();
        if (mat.name) tags.push(`name=${mat.name}`);
        c.name = tags.join('|');
      }
      exported.set(mat, c);
      return c;
    };
    const flatOf = (mat) => (Array.isArray(mat) ? mat : [mat]).some((x) => x.flatShading);
    let meshes = 0;
    const place = (mesh, local, parent) => {
      mesh.geometry = floats(mesh.geometry, flatOf(mesh.material));
      mesh.material = look(mesh.material);
      mesh.matrixAutoUpdate = false;
      mesh.matrix.copy(local);
      mesh.castShadow = true;
      parent.add(mesh);
      meshes++;
    };
    const inv = new THREE.Matrix4();
    const hidden = [];
    const walk = (o, parent, frame) => {
      // People and creatures are actors, not the place (a hat or a lantern
      // held in a hand hangs from a bone).
      if (o.isLight || o.isPoints || o.isLine || o.isSprite || o.isSkinnedMesh || o.isBone) return;
      if (o !== root && (o.userData?.env || o.userData?.merged || ['terrain', 'grass', 'water', 'flora'].includes(o.name))) return;
      if (!o.visible && !tagged.has(o)) return;
      let into = parent, f = frame;
      if (tagged.has(o)) {
        const g = new THREE.Group();
        g.name = tagged.get(o);
        g.matrixAutoUpdate = false;
        g.matrix.copy(frame ? inv.copy(frame).invert().multiply(o.matrixWorld) : o.matrixWorld);
        if (!o.visible) hidden.push(g.name);
        parent.add(g);
        into = g; f = o.matrixWorld.clone();
      }
      const local = (mw) => (f ? new THREE.Matrix4().copy(f).invert().multiply(mw) : mw.clone());
      if (o.isInstancedMesh) {
        if (!o.geometry.userData?.flora && drawn(o.material))
          for (let i = 0; i < o.count; i++) { o.getMatrixAt(i, m); place(new THREE.Mesh(o.geometry, o.material), local(m.clone().premultiply(o.matrixWorld)), into); }
      } else if (o.isMesh && drawn(o.material)) {
        place(new THREE.Mesh(o.geometry, o.material), local(o.matrixWorld), into);
      }
      for (const c of o.children) walk(c, into, f);
    };
    walk(root, scene, null);
    const exporter = new GLTFExporter().setTextureUtils({ decompress: (t, max) => decompress(t, max, window.__game.renderer.gl) });
    const glb = await exporter.parseAsync(scene, { binary: true, maxTextureSize: 2048, onlyVisible: false });
    // Too big for one string on a big zone: left on the page, read in pieces.
    window.__landmarks = new Uint8Array(glb);
    const landmarks = glb.byteLength;

    /* ----------------------------------------------------------- water -- */
    const water = [];
    root.traverse((o) => {
      if (o.name !== 'water' || !o.isMesh) return;
      const g = o.geometry, p = g.attributes.position, v = new THREE.Vector3();
      const pos = [], flow = [], depth = [];
      for (let i = 0; i < p.count; i++) {
        v.fromBufferAttribute(p, i).applyMatrix4(o.matrixWorld);
        pos.push(v.x, v.y, v.z);
        flow.push(g.attributes.aFlow ? g.attributes.aFlow.getX(i) : v.x, g.attributes.aFlow ? g.attributes.aFlow.getY(i) : v.z);
        depth.push(g.attributes.aDepth ? g.attributes.aDepth.getX(i) : 1);
      }
      water.push({ pos, flow, depth, index: g.index ? [...g.index.array] : [...Array(p.count).keys()], stream: !!g.attributes.aFlow, look: o.userData.water ?? {} });
    });

    /* ---------------------------------------------------- the rest, as data -- */
    const col = zb.collision;
    const colliders = col.all().map((c) => ({ id: c.id, kind: c.kind, x: c.x, z: c.z, r: c.r, hw: c.hw, hd: c.hd, rot: c.rot, tag: c.tag ?? null, soft: !!c.soft, playerOnly: !!c.playerOnly }));
    const mod = await import(module);
    const places = {}, paths = {};
    for (const [k, v] of Object.entries(mod)) {
      if (typeof v === 'function') continue;
      if (Array.isArray(v) && Array.isArray(v[0])) paths[k] = v;
      else if (v && typeof v === 'object') places[k] = v;
      else if (typeof v === 'number') places[k] = v;
    }
    const map = zb.map ? { flora: zb.map.flora ?? [], extent: zb.map.extent ?? null, buildings: zb.map.buildings ?? [] } : null;
    // The water on the map, as a mask over the zone (a pixel a metre and a half).
    let waterMask = null;
    if (zb.map?.water) {
      const n = Math.ceil(tr.size / 1.5), bytes = new Uint8Array(n * n);
      for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) bytes[j * n + i] = zb.map.water(-tr.half + (i + 0.5) * tr.size / n, -tr.half + (j + 0.5) * tr.size / n) ? 1 : 0;
      waterMask = { n, bits: b64(bytes) };
    }
    return {
      meta: {
        id: zone, size: tr.size, res: tr.res, splatRes: tr.splatRes, leaves: tr.leaves, blightGlow: hex(tr.uniforms.uBlightGlow.value), bound: col.bound, start: zb.start,
        atmosphere: zb.atmosphere, lights, fires, chimneys, moths, nightNodes, hiddenNodes: hidden, colliders, refs, places, paths, map, waterMask,
        landmarkMeshes: meshes,
      },
      heights, splat, flora: [...flora.values()], props, landmarks, water,
    };
  }, { zone, module: spec.module });

  const meta = data.meta;
  const glbParts = [];
  for (let at = 0; at < data.landmarks; at += 32 << 20)
    glbParts.push(Buffer.from(await pg.evaluate(([a, n]) => {
      const u8 = window.__landmarks.subarray(a, a + n);
      let s = '';
      for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode(...u8.subarray(i, i + 0x8000));
      return btoa(s);
    }, [at, 32 << 20]), 'base64'));
  fs.writeFileSync(`${out}/zone.json`, JSON.stringify(meta) + '\n');
  fs.writeFileSync(`${out}/heights.bin`, Buffer.from(data.heights, 'base64'));
  fs.writeFileSync(`${out}/splat.png`, png(Buffer.from(data.splat, 'base64'), meta.splatRes, meta.splatRes));
  const floraMeta = data.flora.map(({ kind, piece, sx, sy, wind, leaves, moss, count }) => ({ kind, piece, sx, sy, wind, leaves, moss, count }));
  const all = new Float32Array(data.flora.reduce((n, f) => n + f.t.length, 0));
  let at = 0;
  for (const f of data.flora) { all.set(f.t, at); at += f.t.length; }
  fs.writeFileSync(`${out}/flora.json`, JSON.stringify(floraMeta, null, 1) + '\n');
  fs.writeFileSync(`${out}/flora.bin`, Buffer.from(all.buffer));
  fs.writeFileSync(`${out}/props.json`, JSON.stringify(data.props) + '\n');
  fs.writeFileSync(`${out}/landmarks.glb`, Buffer.concat(glbParts));
  const wmeta = [], wbufs = [];
  for (const w of data.water) {
    wmeta.push({ vertices: w.pos.length / 3, indices: w.index.length, stream: w.stream, look: w.look });
    wbufs.push(Buffer.from(new Float32Array(w.pos).buffer), Buffer.from(new Float32Array(w.flow).buffer), Buffer.from(new Float32Array(w.depth).buffer), Buffer.from(new Uint32Array(w.index).buffer));
  }
  fs.writeFileSync(`${out}/water.json`, JSON.stringify(wmeta) + '\n');
  fs.writeFileSync(`${out}/water.bin`, Buffer.concat(wbufs));
  console.log(`${zone}: terrain ${meta.res}² over ${meta.size} m; ${floraMeta.length} flora pieces, ${floraMeta.reduce((n, f) => n + f.count, 0)} placed; ${data.props.length} props; ${meta.landmarkMeshes} landmark meshes; ${data.water.length} waters; ${meta.lights.length} lights, ${meta.fires.length} fires; ${meta.colliders.length} colliders`);
  await pg.close();
}
await browser.close();
