import * as THREE from 'three';
import { MeshoptSimplifier } from 'meshoptimizer';
import { assembleSync, type DyeMask, type PersonSpec } from './people';
import { HUMAN_SOCKETS, heldArm, type Socket } from './characterView';

/* A person made light enough for a crowd (render/vat.ts bakes the crowd's
 * figures into textures, a few thousand vertices and one texture each).
 *
 * From a person as the game dresses them: the triangles clothes hide are
 * dropped, the figure's shapes applied, every part simplified (meshoptimizer,
 * keeping seams and silhouettes), and every texture it wears (skin, outfit,
 * hair, eyes, the weapons in hand) drawn into one atlas with its colour and
 * dye already in it, since a crowd figure has neither per-part materials nor
 * the dye shader. Weapons ride their hand bones as the survivor's do. */

export const bakeReady = () => MeshoptSimplifier.ready;

export interface BakeArms { right?: string; left?: string; forearm?: string }

const ATLAS = 2048;
/** Vertices a crowd figure may have in all (one row of a VAT texture). */
const BUDGET = 4000;

export function bakeablePerson(spec: PersonSpec, arms: BakeArms = {}): THREE.Group {
  const { root, bones } = assembleSync(spec);
  // Weapons on their mounts, named for the baker (it keeps what hangs from
  // an "attach:" group).
  for (const [socket, id] of [['handslot.r', arms.right], ['handslot.l', arms.left], ['forearm.l', arms.forearm]] as Array<[Socket, string | undefined]>) {
    const hs = HUMAN_SOCKETS[socket];
    const bone = id && hs && bones.get(hs.bone);
    const w = id ? heldArm(id) : null;
    if (!bone || !w) continue;
    const mount = new THREE.Group();
    mount.name = `attach:${id}`;
    mount.quaternion.copy(hs.turn);
    mount.position.set(...hs.pos);
    mount.add(w);
    bone.add(mount);
  }
  root.updateMatrixWorld(true);

  const meshes: THREE.Mesh[] = [];
  root.traverse((o) => { if ((o as THREE.Mesh).isMesh) meshes.push(o as THREE.Mesh); });
  const parts = meshes.map((m) => prepare(m));
  const total = parts.reduce((n, p) => n + p.tris, 0);

  // Simplify toward the budget, harder if it comes out over.
  let ratio = Math.min(1, (BUDGET * 1.3) / Math.max(1, total));
  let out: Simplified[] = [];
  for (let tries = 0; tries < 6; tries++) {
    out = parts.map((p) => simplify(p, ratio));
    const verts = out.reduce((n, s) => n + s.count, 0);
    if (verts <= BUDGET) break;
    ratio *= (BUDGET / verts) * 0.92;
  }

  // One atlas: a cell per material, its colour and dye painted in.
  const mats = [...new Set(meshes.map((m) => m.material as THREE.MeshStandardMaterial))];
  const atlas = paintAtlas(mats);
  const shared = new THREE.MeshStandardMaterial({ map: atlas.texture, roughness: 0.8, metalness: 0 });
  meshes.forEach((m, i) => {
    const s = out[i];
    const cell = atlas.cells.get(m.material as THREE.MeshStandardMaterial)!;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(s.position, 3));
    const uv = s.uv;
    for (let k = 0; k < uv.length; k += 2) {
      uv[k] = cell.x + Math.min(1, Math.max(0, uv[k])) * cell.w;
      uv[k + 1] = cell.y + Math.min(1, Math.max(0, uv[k + 1])) * cell.h;
    }
    g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    if (s.skinIndex) g.setAttribute('skinIndex', new THREE.BufferAttribute(s.skinIndex, 4));
    if (s.skinWeight) g.setAttribute('skinWeight', new THREE.BufferAttribute(s.skinWeight, 4));
    g.setIndex(new THREE.BufferAttribute(s.index, 1));
    m.geometry = g;
    m.material = shared;
    m.morphTargetInfluences = undefined;
    m.morphTargetDictionary = undefined;
  });
  return root;
}

/* ---------------------------------------------------------- simplifying -- */

interface Prepared { mesh: THREE.Mesh; position: Float32Array; index: Uint32Array; tris: number }
interface Simplified { position: Float32Array; uv: Float32Array; skinIndex?: Uint16Array; skinWeight?: Float32Array; index: Uint32Array; count: number }

/** A part's surface as it shows: the figure's shapes applied, and without
 *  the triangles its clothes hide. */
function prepare(m: THREE.Mesh): Prepared {
  const g = m.geometry;
  const pos = g.getAttribute('position') as THREE.BufferAttribute;
  const position = new Float32Array(pos.count * 3);
  for (let i = 0; i < pos.count; i++) { position[i * 3] = pos.getX(i); position[i * 3 + 1] = pos.getY(i); position[i * 3 + 2] = pos.getZ(i); }
  const morphs = g.morphAttributes.position;
  const inf = m.morphTargetInfluences;
  if (morphs && inf) {
    morphs.forEach((d, k) => {
      const w = inf[k];
      if (!w) return;
      for (let i = 0; i < d.count; i++) { position[i * 3] += d.getX(i) * w; position[i * 3 + 1] += d.getY(i) * w; position[i * 3 + 2] += d.getZ(i) * w; }
    });
  }
  const keep = g.getAttribute('aKeep') as THREE.BufferAttribute | undefined;
  const src = g.index ? (g.index.array as ArrayLike<number>) : Array.from({ length: pos.count }, (_, i) => i);
  const tris: number[] = [];
  for (let t = 0; t < src.length; t += 3) {
    const a = src[t], b = src[t + 1], c = src[t + 2];
    if (keep && (keep.getX(a) < 0.5 || keep.getX(b) < 0.5 || keep.getX(c) < 0.5)) continue;
    tris.push(a, b, c);
  }
  return { mesh: m, position, index: new Uint32Array(tris), tris: tris.length / 3 };
}

function simplify(p: Prepared, ratio: number): Simplified {
  const g = p.mesh.geometry;
  let index = p.index;
  if (ratio < 1 && index.length > 36) {
    const target = Math.max(12, Math.floor((index.length / 3) * ratio) * 3);
    // (The error is relative to the part's size: a few percent at most.)
    [index] = MeshoptSimplifier.simplify(index, p.position, 3, target, 0.025, ['Prune']);
  }
  // Keep only the vertices still used, in first-use order.
  const remap = new Map<number, number>();
  const outIndex = new Uint32Array(index.length);
  for (let i = 0; i < index.length; i++) {
    let r = remap.get(index[i]);
    if (r === undefined) { r = remap.size; remap.set(index[i], r); }
    outIndex[i] = r;
  }
  const n = remap.size;
  const uvA = g.getAttribute('uv') as THREE.BufferAttribute | undefined;
  const si = g.getAttribute('skinIndex') as THREE.BufferAttribute | undefined;
  const sw = g.getAttribute('skinWeight') as THREE.BufferAttribute | undefined;
  const position = new Float32Array(n * 3), uv = new Float32Array(n * 2);
  const skinIndex = si ? new Uint16Array(n * 4) : undefined, skinWeight = sw ? new Float32Array(n * 4) : undefined;
  for (const [src, dst] of remap) {
    position[dst * 3] = p.position[src * 3]; position[dst * 3 + 1] = p.position[src * 3 + 1]; position[dst * 3 + 2] = p.position[src * 3 + 2];
    if (uvA) { uv[dst * 2] = uvA.getX(src); uv[dst * 2 + 1] = uvA.getY(src); }
    if (si && skinIndex) for (let k = 0; k < 4; k++) skinIndex[dst * 4 + k] = si.getComponent(src, k);
    if (sw && skinWeight) for (let k = 0; k < 4; k++) skinWeight[dst * 4 + k] = sw.getComponent(src, k);
  }
  return { position, uv, skinIndex, skinWeight, index: outIndex, count: n };
}

/* --------------------------------------------------------------- atlas -- */

interface Cell { x: number; y: number; w: number; h: number }

/** Every material's texture in one image, each in a cell, with the
 *  material's colour multiplied in and its dye (people.ts) applied, as the
 *  shader would. UVs map into a cell (the texture is not flipped). */
function paintAtlas(mats: THREE.MeshStandardMaterial[]) {
  const n = mats.length;
  const grid = Math.ceil(Math.sqrt(n));
  const size = Math.floor(ATLAS / grid);
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = ATLAS;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.imageSmoothingQuality = 'high';
  const cells = new Map<THREE.MeshStandardMaterial, Cell>();
  const pad = 2;
  mats.forEach((mat, i) => {
    const cx = (i % grid) * size, cy = Math.floor(i / grid) * size;
    const img = mat.map?.image as CanvasImageSource | undefined;
    if (img) ctx.drawImage(img, cx, cy, size, size);
    else { ctx.fillStyle = '#ffffff'; ctx.fillRect(cx, cy, size, size); }
    const data = ctx.getImageData(cx, cy, size, size);
    shade(data.data, mat.color, mat.userData.dye as { mask: DyeMask; color: THREE.Color } | undefined);
    ctx.putImageData(data, cx, cy);
    cells.set(mat, { x: (cx + pad) / ATLAS, y: (cy + pad) / ATLAS, w: (size - pad * 2) / ATLAS, h: (size - pad * 2) / ATLAS });
  });
  const texture = new THREE.CanvasTexture(canvas);
  texture.flipY = false;
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  return { texture, cells };
}

const lin = (c: number) => (c < 0.04045 ? c * 0.0773993808 : Math.pow(c * 0.9478672986 + 0.0521327014, 2.4));
const srgb = (c: number) => (c < 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 0.41666) - 0.055);
const toLin = new Float32Array(256).map((_, i) => lin(i / 255));
const toSrgb = (v: number) => Math.round(Math.min(1, Math.max(0, srgb(v))) * 255);

/** A cell's pixels times the material's colour (linear), then dyed. */
function shade(px: Uint8ClampedArray, color: THREE.Color, dye?: { mask: DyeMask; color: THREE.Color }) {
  const plain = color.r === 1 && color.g === 1 && color.b === 1;
  if (plain && !dye) return;
  const band = (x: number, lo: number, hi: number) => {
    const s = (a: number, b: number, v: number) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
    return s(lo - 0.05, lo, x) * (1 - s(hi, hi + 0.05, x));
  };
  for (let i = 0; i < px.length; i += 4) {
    let r = toLin[px[i]] * color.r, g = toLin[px[i + 1]] * color.g, b = toLin[px[i + 2]] * color.b;
    if (dye) {
      // As the shader: hue, saturation and value of the (roughly) sRGB
      // colour pick the cloth; its brightness scales the dye.
      const sr = Math.pow(r, 1 / 2.2), sg = Math.pow(g, 1 / 2.2), sb = Math.pow(b, 1 / 2.2);
      const mx = Math.max(sr, sg, sb), mn = Math.min(sr, sg, sb), d = mx - mn;
      let h = 0;
      if (d > 1e-6) h = mx === sr ? ((sg - sb) / d + 6) % 6 : mx === sg ? (sb - sr) / d + 2 : (sr - sg) / d + 4;
      h /= 6;
      const sat = mx > 0 ? d / mx : 0;
      const m = band(h, dye.mask.h[0], dye.mask.h[1]) * band(sat, dye.mask.s[0], dye.mask.s[1]) * band(mx, dye.mask.v[0], dye.mask.v[1]);
      if (m > 0) {
        const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        const k = lum / dye.mask.lum;
        r += (Math.min(1, dye.color.r * k) - r) * m;
        g += (Math.min(1, dye.color.g * k) - g) * m;
        b += (Math.min(1, dye.color.b * k) - b) * m;
      }
    }
    px[i] = toSrgb(r); px[i + 1] = toSrgb(g); px[i + 2] = toSrgb(b);
  }
}
