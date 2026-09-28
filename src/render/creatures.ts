import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { Rng } from '@/core/rng';

/* Beasts, modelled and animated in code.
 *
 * The character packs have people and the dead, but no wolves, no boars and
 * no lamplings, and those are what the Thornhollow quests are about. So they
 * are built here, in the same chunky faceted style as the KayKit models:
 *
 *   - bodies are LOFTED: a handful of polygonal cross-sections along the
 *     spine, skinned between two spine bones so the back flexes in a gallop;
 *   - heads, jaws, legs, tails and ears are their own segments on their own
 *     bones; fur is a ruff of little pyramids, because fur in low poly is a
 *     silhouette, not a texture;
 *   - colour is per face (flat, like painted palette blocks), graded from a
 *     dark back to a pale belly;
 *   - animation is keyframed from pose functions sampled over a cycle - a
 *     gallop is a phase offset per leg, not a mocap file.
 *
 * The result is a real SkinnedMesh with real clips, which the VAT baker then
 * turns into a crowd exactly as it does the skeletons. */

type Pose = Record<string, { r?: [number, number, number]; p?: [number, number, number] }>;

interface BoneSpec { name: string; parent: string | null; pos: [number, number, number] }

class Builder {
  bones: THREE.Bone[] = [];
  byName = new Map<string, THREE.Bone>();
  parts: THREE.BufferGeometry[] = [];
  glowParts: THREE.BufferGeometry[] = [];
  rest = new Map<string, THREE.Vector3>();

  bone(spec: BoneSpec) {
    const b = new THREE.Bone();
    b.name = spec.name;
    b.position.set(...spec.pos);
    if (spec.parent) this.byName.get(spec.parent)!.add(b);
    this.bones.push(b);
    this.byName.set(spec.name, b);
    this.rest.set(spec.name, b.position.clone());
    return b;
  }

  /** World position of a bone at rest. */
  boneWorld(name: string) {
    const b = this.byName.get(name)!;
    this.bones[0].updateMatrixWorld(true);
    return new THREE.Vector3().setFromMatrixPosition(b.matrixWorld);
  }

  /** Add geometry (in model space), skinned to one bone or blended between
   *  two along an axis. Non-indexed, flat shaded, coloured per face. */
  add(geo: THREE.BufferGeometry, bone: string | { a: string; b: string; axis: 'x' | 'y' | 'z'; from: number; to: number },
    color: (centroid: THREE.Vector3, normal: THREE.Vector3) => THREE.Color, glow = false) {
    let g = geo.index ? geo.toNonIndexed() : geo;
    for (const k of Object.keys(g.attributes)) if (k !== 'position') g.deleteAttribute(k);
    g.computeVertexNormals();
    const pos = g.getAttribute('position');
    const nor = g.getAttribute('normal');
    const n = pos.count;
    const skinIndex = new Uint16Array(n * 4);
    const skinWeight = new Float32Array(n * 4);
    const col = new Float32Array(n * 3);
    const v = new THREE.Vector3(), c = new THREE.Vector3(), nn = new THREE.Vector3();
    for (let i = 0; i < n; i++) {
      v.fromBufferAttribute(pos, i);
      if (typeof bone === 'string') {
        skinIndex[i * 4] = this.bones.indexOf(this.byName.get(bone)!);
        skinWeight[i * 4] = 1;
      } else {
        const t = THREE.MathUtils.clamp((v[bone.axis] - bone.from) / (bone.to - bone.from), 0, 1);
        const s = t * t * (3 - 2 * t);
        skinIndex[i * 4] = this.bones.indexOf(this.byName.get(bone.a)!);
        skinIndex[i * 4 + 1] = this.bones.indexOf(this.byName.get(bone.b)!);
        skinWeight[i * 4] = 1 - s;
        skinWeight[i * 4 + 1] = s;
      }
    }
    for (let f = 0; f < n; f += 3) {
      c.set(0, 0, 0);
      for (let k = 0; k < 3; k++) c.add(v.fromBufferAttribute(pos, f + k));
      c.multiplyScalar(1 / 3);
      nn.fromBufferAttribute(nor, f);
      const cc = color(c, nn);
      for (let k = 0; k < 3; k++) { col[(f + k) * 3] = cc.r; col[(f + k) * 3 + 1] = cc.g; col[(f + k) * 3 + 2] = cc.b; }
    }
    g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(skinIndex, 4));
    g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(skinWeight, 4));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    (glow ? this.glowParts : this.parts).push(g);
  }

  build(glowColor: THREE.Color): THREE.Group {
    const root = new THREE.Group();
    const skeleton = new THREE.Skeleton(this.bones);
    root.add(this.bones[0]);
    root.updateMatrixWorld(true);
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85, flatShading: true });
    const body = new THREE.SkinnedMesh(mergeGeometries(this.parts)!, mat);
    body.bind(skeleton);
    root.add(body);
    if (this.glowParts.length) {
      const gm = new THREE.MeshStandardMaterial({ vertexColors: true, emissive: glowColor, color: glowColor, name: 'Glow' });
      const glow = new THREE.SkinnedMesh(mergeGeometries(this.glowParts)!, gm);
      glow.bind(skeleton);
      root.add(glow);
    }
    return root;
  }

  /** Sample a pose function into a clip. Rotations are offsets from rest
   *  (Euler XYZ, radians); positions are offsets from the rest position. */
  clip(name: string, duration: number, pose: (t: number) => Pose, samples = 16): THREE.AnimationClip {
    const times: number[] = [];
    for (let i = 0; i <= samples; i++) times.push((i / samples) * duration);
    const tracks: THREE.KeyframeTrack[] = [];
    const quats = new Map<string, number[]>();
    const poss = new Map<string, number[]>();
    for (const t of times) {
      const p = pose(t / duration);
      for (const b of this.bones) {
        const e = p[b.name];
        const r = e?.r ?? [0, 0, 0];
        const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(r[0], r[1], r[2]));
        (quats.get(b.name) ?? quats.set(b.name, []).get(b.name)!).push(q.x, q.y, q.z, q.w);
        const rest = this.rest.get(b.name)!;
        const off = e?.p ?? [0, 0, 0];
        (poss.get(b.name) ?? poss.set(b.name, []).get(b.name)!).push(rest.x + off[0], rest.y + off[1], rest.z + off[2]);
      }
    }
    for (const b of this.bones) {
      tracks.push(new THREE.QuaternionKeyframeTrack(`${b.name}.quaternion`, times, quats.get(b.name)!));
      tracks.push(new THREE.VectorKeyframeTrack(`${b.name}.position`, times, poss.get(b.name)!));
    }
    return new THREE.AnimationClip(name, duration, tracks);
  }
}

/* ------------------------------------------------------------- shapes -- */

/** A loft: polygonal rings along +z, each with centre (y), half width and
 *  half height, and optional ring rotation. Capped both ends. */
function loft(rings: Array<{ z: number; y: number; w: number; h: number; x?: number }>, sides = 7, jitter = 0, rng?: Rng) {
  const pos: number[] = [];
  const ring = rings.map((r) => {
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i < sides; i++) {
      const a = (i / sides) * Math.PI * 2 + Math.PI / sides;
      const j = jitter && rng ? 1 + (rng.next() - 0.5) * jitter : 1;
      pts.push(new THREE.Vector3((r.x ?? 0) + Math.cos(a) * r.w * j, r.y + Math.sin(a) * r.h * j, r.z));
    }
    return pts;
  });
  const tri = (a: THREE.Vector3, b: THREE.Vector3, c: THREE.Vector3) => pos.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
  for (let k = 0; k < ring.length - 1; k++) {
    const A = ring[k], B = ring[k + 1];
    for (let i = 0; i < sides; i++) {
      const i2 = (i + 1) % sides;
      tri(A[i], A[i2], B[i]);
      tri(A[i2], B[i2], B[i]);
    }
  }
  const cap = (R: THREE.Vector3[], flip: boolean) => {
    const c = R.reduce((s, p) => s.add(p), new THREE.Vector3()).multiplyScalar(1 / R.length);
    for (let i = 0; i < sides; i++) {
      const i2 = (i + 1) % sides;
      if (flip) tri(c, R[i2], R[i]); else tri(c, R[i], R[i2]);
    }
  };
  cap(ring[0], true);
  cap(ring[ring.length - 1], false);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  return g;
}

/** A tapered limb from a to b. */
function limb(a: THREE.Vector3, b: THREE.Vector3, r0: number, r1: number, sides = 5) {
  const len = a.distanceTo(b);
  const g = new THREE.CylinderGeometry(r1, r0, len, sides, 1, false);
  g.translate(0, len / 2, 0);
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
  g.applyQuaternion(q);
  g.translate(a.x, a.y, a.z);
  return g;
}

function cone(at: THREE.Vector3, dir: THREE.Vector3, r: number, h: number, sides = 4) {
  const g = new THREE.ConeGeometry(r, h, sides, 1);
  g.translate(0, h / 2, 0);
  g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize()));
  g.translate(at.x, at.y, at.z);
  return g;
}

function blob(at: THREE.Vector3, r: number, sx = 1, sy = 1, sz = 1, detail = 0) {
  const g = new THREE.IcosahedronGeometry(r, detail);
  g.scale(sx, sy, sz);
  g.translate(at.x, at.y, at.z);
  return g;
}

/* --------------------------------------------------------------- wolves -- */

export interface WolfLook {
  back: string; belly: string; muzzle: string; nose: string; eye: string; glowEyes?: boolean; ruff?: number; seed?: number;
  sick?: boolean;
}

export const WOLF_LOOKS: Record<string, WolfLook> = {
  wolf: { back: '#6b6a70', belly: '#b9b3a4', muzzle: '#d4cdbb', nose: '#141416', eye: '#e8c060', ruff: 1 },
  wolf_alpha: { back: '#2e2d31', belly: '#8d8a84', muzzle: '#d9d4c8', nose: '#0e0e10', eye: '#ffd070', glowEyes: true, ruff: 1.5 },
  wolf_blighted: { back: '#3a3b33', belly: '#6d6e58', muzzle: '#8a8b70', nose: '#161612', eye: '#9dff6a', glowEyes: true, ruff: 1.1, sick: true },
  wolf_spirit: { back: '#a8c8ff', belly: '#e8f4ff', muzzle: '#ffffff', nose: '#6a8ccc', eye: '#ffffff', glowEyes: true, ruff: 1.2 },
};

export function buildWolf(look: WolfLook): { root: THREE.Group; clips: Record<string, THREE.AnimationClip> } {
  const rng = new Rng(look.seed ?? 5);
  const B = new Builder();
  B.bone({ name: 'root', parent: null, pos: [0, 0, 0] });
  B.bone({ name: 'hips', parent: 'root', pos: [0, 0.62, -0.32] });
  B.bone({ name: 'chest', parent: 'hips', pos: [0, 0.04, 0.5] });
  B.bone({ name: 'neck', parent: 'chest', pos: [0, 0.12, 0.2] });
  B.bone({ name: 'head', parent: 'neck', pos: [0, 0.14, 0.14] });
  B.bone({ name: 'jaw', parent: 'head', pos: [0, -0.08, 0.1] });
  B.bone({ name: 'tail', parent: 'hips', pos: [0, 0.06, -0.2] });
  B.bone({ name: 'tail2', parent: 'tail', pos: [0, -0.05, -0.24] });
  for (const [side, sx] of [['L', 1], ['R', -1]] as const) {
    B.bone({ name: `fu${side}`, parent: 'chest', pos: [0.15 * sx, -0.05, 0.08] });
    B.bone({ name: `fl${side}`, parent: `fu${side}`, pos: [0, -0.28, 0.02] });
    B.bone({ name: `bu${side}`, parent: 'hips', pos: [0.15 * sx, -0.02, -0.08] });
    B.bone({ name: `bl${side}`, parent: `bu${side}`, pos: [0, -0.3, -0.04] });
  }

  const back = new THREE.Color(look.back), belly = new THREE.Color(look.belly), muzzle = new THREE.Color(look.muzzle), nose = new THREE.Color(look.nose);
  const shade = (c: THREE.Vector3, n: THREE.Vector3) => {
    // Dark along the back, pale underneath, with a little per-facet noise.
    const up = n.y * 0.5 + 0.5;
    const k = THREE.MathUtils.smoothstep(c.y, 0.45, 0.75) * 0.6 + up * 0.4;
    const col = belly.clone().lerp(back, k);
    col.offsetHSL(0, 0, (Math.sin(c.x * 41 + c.z * 23 + c.y * 17) * 0.5) * 0.04);
    if (look.sick && Math.sin(c.x * 30 + c.z * 12) > 0.75) col.lerp(new THREE.Color('#7a8a3a'), 0.6);
    return col;
  };

  // Torso: rump to chest, deep chest, tucked waist.
  B.add(loft([
    { z: -0.62, y: 0.64, w: 0.1, h: 0.1 },
    { z: -0.5, y: 0.66, w: 0.2, h: 0.18 },
    { z: -0.22, y: 0.64, w: 0.21, h: 0.17 },
    { z: 0.02, y: 0.64, w: 0.2, h: 0.17 },
    { z: 0.2, y: 0.63, w: 0.24, h: 0.24 },
    { z: 0.36, y: 0.66, w: 0.22, h: 0.23 },
    { z: 0.46, y: 0.72, w: 0.14, h: 0.14 },
  ], 7, 0.1, rng), { a: 'hips', b: 'chest', axis: 'z', from: -0.2, to: 0.2 }, shade);

  // Neck ruff: fur in low poly is a silhouette.
  const ruffN = Math.round(9 * (look.ruff ?? 1));
  for (let i = 0; i < ruffN; i++) {
    const a = (i / ruffN) * Math.PI * 2;
    const at = new THREE.Vector3(Math.cos(a) * 0.17, 0.78 + Math.sin(a) * 0.15, 0.42);
    const dir = new THREE.Vector3(Math.cos(a), Math.sin(a) + 0.2, -0.9);
    B.add(cone(at, dir, 0.07, 0.2 + rng.next() * 0.08, 3), 'neck', (c, n) => shade(c, n).multiplyScalar(0.92));
  }

  // Neck and head.
  B.add(loft([
    { z: 0.4, y: 0.76, w: 0.13, h: 0.14 },
    { z: 0.56, y: 0.86, w: 0.11, h: 0.12 },
  ], 6), 'neck', shade);
  const headShade = (c: THREE.Vector3, n: THREE.Vector3) => {
    if (c.z > 0.88) return muzzle.clone().lerp(belly, 0.2);
    return shade(c, n).lerp(muzzle, c.y < 0.88 ? 0.35 : 0);
  };
  B.add(loft([
    { z: 0.56, y: 0.92, w: 0.14, h: 0.13 },
    { z: 0.7, y: 0.93, w: 0.15, h: 0.12 },
    { z: 0.82, y: 0.9, w: 0.1, h: 0.08 },
    { z: 1.0, y: 0.88, w: 0.06, h: 0.05 },
  ], 6), 'head', headShade);
  B.add(blob(new THREE.Vector3(0, 0.9, 1.02), 0.035, 1.2, 0.8, 1), 'head', () => nose);
  // Jaw.
  B.add(loft([
    { z: 0.7, y: 0.82, w: 0.09, h: 0.04 },
    { z: 0.97, y: 0.83, w: 0.05, h: 0.03 },
  ], 5), 'jaw', () => muzzle.clone().multiplyScalar(0.85));
  // Ears.
  for (const sx of [1, -1]) {
    B.add(cone(new THREE.Vector3(0.08 * sx, 1.02, 0.66), new THREE.Vector3(0.25 * sx, 1, -0.2), 0.055, 0.16, 3), 'head', (c, n) => shade(c, n).multiplyScalar(0.8));
  }
  // Eyes.
  for (const sx of [1, -1]) {
    B.add(blob(new THREE.Vector3(0.1 * sx, 0.97, 0.8), 0.028, 1, 0.7, 1), 'head', () => new THREE.Color(look.eye), !!look.glowEyes);
  }

  // Legs.
  for (const [side, sx] of [['L', 1], ['R', -1]] as const) {
    const fu = B.boneWorld(`fu${side}`), fl = B.boneWorld(`fl${side}`);
    B.add(limb(fu.clone().add(new THREE.Vector3(0, 0.05, 0)), fl, 0.075, 0.055, 5), `fu${side}`, shade);
    B.add(limb(fl, new THREE.Vector3(fl.x, 0.04, fl.z + 0.02), 0.05, 0.04, 5), `fl${side}`, shade);
    B.add(blob(new THREE.Vector3(fl.x, 0.04, fl.z + 0.06), 0.05, 1, 0.6, 1.4), `fl${side}`, () => belly.clone().multiplyScalar(0.55));
    const bu = B.boneWorld(`bu${side}`), bl = B.boneWorld(`bl${side}`);
    B.add(blob(bu.clone().add(new THREE.Vector3(0.02 * sx, -0.04, 0.02)), 0.11, 0.8, 1.2, 1.1), `bu${side}`, shade);
    B.add(limb(bu, bl, 0.08, 0.05, 5), `bu${side}`, shade);
    B.add(limb(bl, new THREE.Vector3(bl.x, 0.04, bl.z + 0.05), 0.05, 0.04, 5), `bl${side}`, shade);
    B.add(blob(new THREE.Vector3(bl.x, 0.04, bl.z + 0.09), 0.05, 1, 0.6, 1.4), `bl${side}`, () => belly.clone().multiplyScalar(0.55));
  }

  // Tail: bushy in the middle.
  B.add(loft([
    { z: -0.52, y: 0.68, w: 0.06, h: 0.06 },
    { z: -0.66, y: 0.62, w: 0.1, h: 0.1 },
  ], 6), 'tail', shade);
  B.add(loft([
    { z: -0.66, y: 0.62, w: 0.1, h: 0.1 },
    { z: -0.86, y: 0.5, w: 0.09, h: 0.09 },
    { z: -1.0, y: 0.42, w: 0.03, h: 0.03 },
  ], 6), 'tail2', (c, n) => (c.z < -0.93 ? belly : shade(c, n)));

  const root = B.build(new THREE.Color(look.eye));

  const run = B.clip('run', 0.56, (t) => {
    const a = t * Math.PI * 2;
    const leg = (ph: number, amp: number) => Math.sin(a + ph) * amp;
    return {
      hips: { r: [Math.sin(a) * 0.08, 0, 0], p: [0, Math.abs(Math.sin(a)) * 0.07, 0] },
      chest: { r: [-Math.sin(a) * 0.12, 0, 0] },
      neck: { r: [Math.sin(a + 0.6) * 0.1, 0, 0] },
      head: { r: [-Math.sin(a + 0.6) * 0.08, 0, 0] },
      tail: { r: [0.25 + Math.sin(a * 2) * 0.12, Math.sin(a) * 0.2, 0] },
      tail2: { r: [0.1, Math.sin(a + 1) * 0.25, 0] },
      fuL: { r: [leg(0, 0.75), 0, 0] }, flL: { r: [Math.max(0, leg(0.9, 0.9)), 0, 0] },
      fuR: { r: [leg(0.4, 0.75), 0, 0] }, flR: { r: [Math.max(0, leg(1.3, 0.9)), 0, 0] },
      buL: { r: [leg(Math.PI, 0.7), 0, 0] }, blL: { r: [-Math.max(0, leg(Math.PI + 0.9, 0.8)), 0, 0] },
      buR: { r: [leg(Math.PI + 0.4, 0.7), 0, 0] }, blR: { r: [-Math.max(0, leg(Math.PI + 1.3, 0.8)), 0, 0] },
      jaw: { r: [0.15 + Math.sin(a) * 0.05, 0, 0] },
    };
  });
  const idle = B.clip('idle', 2.4, (t) => {
    const a = t * Math.PI * 2;
    return {
      chest: { p: [0, Math.sin(a * 2) * 0.008, 0] },
      neck: { r: [Math.sin(a) * 0.05, Math.sin(a * 0.5) * 0.25, 0] },
      head: { r: [0.05, Math.sin(a) * 0.15, 0] },
      tail: { r: [0.35, Math.sin(a * 3) * 0.35, 0] },
      tail2: { r: [0.2, Math.sin(a * 3 + 1) * 0.3, 0] },
      jaw: { r: [0.05 + Math.max(0, Math.sin(a * 4)) * 0.12, 0, 0] },
    };
  });
  const attack = B.clip('attack', 0.5, (t) => {
    const k = Math.sin(Math.min(1, t * 1.6) * Math.PI);
    return {
      hips: { p: [0, -0.04 * k, 0.12 * k], r: [-0.15 * k, 0, 0] },
      chest: { r: [0.2 * k, 0, 0] },
      neck: { r: [-0.35 * k, 0, 0] },
      head: { r: [0.25 * k, 0, 0] },
      jaw: { r: [0.6 * k, 0, 0] },
      fuL: { r: [-0.8 * k, 0, 0] }, fuR: { r: [-0.7 * k, 0, 0] },
      tail: { r: [0.1, 0, 0] },
    };
  });
  const windup = B.clip('windup', 0.8, (t) => {
    const a = t * Math.PI * 2;
    return {
      hips: { p: [0, -0.12, -0.05], r: [0.15, 0, 0] },
      chest: { r: [0.1, 0, 0] },
      neck: { r: [0.35, 0, 0] },
      head: { r: [-0.25, 0, 0] },
      jaw: { r: [0.3 + Math.sin(a * 6) * 0.08, 0, 0] },
      tail: { r: [-0.2, Math.sin(a * 4) * 0.08, 0] },
      buL: { r: [0.4, 0, 0] }, buR: { r: [0.4, 0, 0] }, blL: { r: [-0.6, 0, 0] }, blR: { r: [-0.6, 0, 0] },
    };
  });
  const die = B.clip('die', 0.9, (t) => {
    const k = Math.min(1, t * 1.5);
    const e = 1 - (1 - k) * (1 - k);
    return {
      root: { r: [0, 0, e * 1.45], p: [0, -0.05 * e, 0] },
      hips: { p: [0, -0.35 * e, 0] },
      neck: { r: [0.3 * e, 0, 0] },
      head: { r: [0.2 * e, 0, 0] },
      jaw: { r: [0.35 * e, 0, 0] },
      fuL: { r: [-0.5 * e, 0, 0] }, fuR: { r: [0.3 * e, 0, 0] }, buL: { r: [0.4 * e, 0, 0] }, buR: { r: [-0.3 * e, 0, 0] },
      tail: { r: [0.5 * e, 0, 0] },
    };
  });
  const hit = B.clip('hit', 0.3, (t) => {
    const k = Math.sin(t * Math.PI);
    return { chest: { r: [0, 0, 0.15 * k], p: [0, 0, -0.06 * k] }, head: { r: [-0.25 * k, 0.2 * k, 0] }, neck: { r: [-0.2 * k, 0, 0] } };
  });
  return { root, clips: { run, idle, attack, windup, die, hit } };
}

/* ---------------------------------------------------------------- boars -- */

export function buildBoar(): { root: THREE.Group; clips: Record<string, THREE.AnimationClip> } {
  const rng = new Rng(17);
  const B = new Builder();
  B.bone({ name: 'root', parent: null, pos: [0, 0, 0] });
  B.bone({ name: 'hips', parent: 'root', pos: [0, 0.55, -0.3] });
  B.bone({ name: 'chest', parent: 'hips', pos: [0, 0.05, 0.5] });
  B.bone({ name: 'head', parent: 'chest', pos: [0, -0.02, 0.28] });
  B.bone({ name: 'tail', parent: 'hips', pos: [0, 0.1, -0.35] });
  for (const [side, sx] of [['L', 1], ['R', -1]] as const) {
    B.bone({ name: `fu${side}`, parent: 'chest', pos: [0.2 * sx, -0.15, 0.05] });
    B.bone({ name: `bu${side}`, parent: 'hips', pos: [0.2 * sx, -0.15, -0.1] });
  }
  const dark = new THREE.Color('#3b2a20'), mid = new THREE.Color('#6a4a33'), light = new THREE.Color('#8a6a4c'), bristle = new THREE.Color('#2a1d16');
  const shade = (c: THREE.Vector3, n: THREE.Vector3) => {
    const up = n.y * 0.5 + 0.5;
    const col = light.clone().lerp(mid, up).lerp(dark, THREE.MathUtils.smoothstep(c.y, 0.7, 0.9) * 0.6);
    col.offsetHSL(0, 0, Math.sin(c.x * 33 + c.z * 19) * 0.025);
    return col;
  };
  B.add(loft([
    { z: -0.7, y: 0.58, w: 0.14, h: 0.14 },
    { z: -0.55, y: 0.62, w: 0.3, h: 0.28 },
    { z: -0.2, y: 0.66, w: 0.34, h: 0.32 },
    { z: 0.15, y: 0.7, w: 0.36, h: 0.36 },
    { z: 0.35, y: 0.66, w: 0.3, h: 0.31 },
  ], 8, 0.12, rng), { a: 'hips', b: 'chest', axis: 'z', from: -0.3, to: 0.2 }, shade);
  // Bristle ridge along the spine.
  for (let i = 0; i < 9; i++) {
    const z = -0.5 + i * 0.1;
    B.add(cone(new THREE.Vector3(0, 0.94 + Math.sin(i * 0.6) * 0.04, z), new THREE.Vector3(0, 1, -0.35), 0.05, 0.18 + rng.next() * 0.08, 3),
      z > 0 ? 'chest' : 'hips', () => bristle);
  }
  // Head: a wedge ending in a flat snout, with tusks.
  B.add(loft([
    { z: 0.36, y: 0.68, w: 0.26, h: 0.26 },
    { z: 0.56, y: 0.6, w: 0.2, h: 0.2 },
    { z: 0.78, y: 0.5, w: 0.12, h: 0.12 },
    { z: 0.86, y: 0.48, w: 0.11, h: 0.1 },
  ], 7), 'head', (c, n) => (c.z > 0.84 ? new THREE.Color('#b08070') : shade(c, n)));
  for (const sx of [1, -1]) {
    B.add(cone(new THREE.Vector3(0.1 * sx, 0.45, 0.76), new THREE.Vector3(0.3 * sx, 1, 0.5), 0.03, 0.2, 4), 'head', () => new THREE.Color('#e8e0c8'));
    B.add(cone(new THREE.Vector3(0.13 * sx, 0.84, 0.46), new THREE.Vector3(0.6 * sx, 0.8, -0.3), 0.06, 0.14, 3), 'head', () => dark);
    B.add(blob(new THREE.Vector3(0.14 * sx, 0.72, 0.62), 0.025, 1, 1, 1), 'head', () => new THREE.Color('#1a0e0a'));
  }
  for (const side of ['L', 'R'] as const) {
    const f = B.boneWorld(`fu${side}`), b = B.boneWorld(`bu${side}`);
    B.add(limb(f, new THREE.Vector3(f.x, 0.03, f.z + 0.03), 0.09, 0.06, 5), `fu${side}`, () => dark);
    B.add(limb(b, new THREE.Vector3(b.x, 0.03, b.z - 0.02), 0.1, 0.06, 5), `bu${side}`, () => dark);
  }
  B.add(cone(new THREE.Vector3(0, 0.66, -0.68), new THREE.Vector3(0, -0.5, -1), 0.03, 0.22, 3), 'tail', () => dark);
  const root = B.build(new THREE.Color('#000000'));
  const run = B.clip('run', 0.5, (t) => {
    const a = t * Math.PI * 2;
    return {
      hips: { p: [0, Math.abs(Math.sin(a)) * 0.05, 0], r: [Math.sin(a) * 0.05, 0, 0] },
      chest: { r: [-Math.sin(a) * 0.06, 0, 0] },
      head: { r: [Math.sin(a + 0.5) * 0.08, 0, 0] },
      fuL: { r: [Math.sin(a) * 0.7, 0, 0] }, fuR: { r: [Math.sin(a + Math.PI) * 0.7, 0, 0] },
      buL: { r: [Math.sin(a + Math.PI) * 0.7, 0, 0] }, buR: { r: [Math.sin(a) * 0.7, 0, 0] },
      tail: { r: [Math.sin(a * 2) * 0.3, 0, 0] },
    };
  });
  const idle = B.clip('idle', 2, (t) => {
    const a = t * Math.PI * 2;
    return { head: { r: [0.2 + Math.max(0, Math.sin(a * 2)) * 0.25, Math.sin(a) * 0.2, 0] }, tail: { r: [0, Math.sin(a * 5) * 0.4, 0] }, chest: { p: [0, Math.sin(a * 2) * 0.01, 0] } };
  });
  const windup = B.clip('windup', 0.6, (t) => {
    const a = t * Math.PI * 2;
    // Pawing the ground.
    return {
      hips: { p: [0, -0.04, 0], r: [0.1, 0, 0] }, head: { r: [0.35, 0, 0] },
      fuL: { r: [-0.6 + Math.max(0, Math.sin(a * 2)) * 0.9, 0, 0] }, fuR: { r: [0.1, 0, 0] },
      tail: { r: [-0.4, Math.sin(a * 6) * 0.3, 0] },
    };
  });
  const attack = B.clip('attack', 0.45, (t) => {
    const k = Math.sin(t * Math.PI);
    return { head: { r: [-0.5 * k, 0, 0], p: [0, 0.05 * k, 0.1 * k] }, chest: { r: [-0.1 * k, 0, 0] }, fuL: { r: [-0.4 * k, 0, 0] }, fuR: { r: [-0.4 * k, 0, 0] } };
  });
  const die = B.clip('die', 0.8, (t) => {
    const e = 1 - (1 - Math.min(1, t * 1.4)) ** 2;
    return { root: { r: [0, 0, -1.5 * e] }, hips: { p: [0, -0.3 * e, 0] }, head: { r: [0.3 * e, 0, 0] }, fuL: { r: [0.6 * e, 0, 0] }, buR: { r: [-0.5 * e, 0, 0] } };
  });
  const hit = B.clip('hit', 0.3, (t) => ({ chest: { r: [0, 0, 0.12 * Math.sin(t * Math.PI)] }, head: { r: [-0.3 * Math.sin(t * Math.PI), 0, 0] } }));
  return { root, clips: { run, idle, windup, attack, die, hit } };
}

/* ------------------------------------------------------------- lamplings -- */

export function buildLampling(sapper = false): { root: THREE.Group; clips: Record<string, THREE.AnimationClip> } {
  const B = new Builder();
  B.bone({ name: 'root', parent: null, pos: [0, 0, 0] });
  B.bone({ name: 'body', parent: 'root', pos: [0, 0.38, 0] });
  B.bone({ name: 'head', parent: 'body', pos: [0, 0.3, 0.04] });
  B.bone({ name: 'lamp', parent: 'head', pos: [0, 0.22, -0.05] });
  B.bone({ name: 'armL', parent: 'body', pos: [0.26, 0.12, 0.05] });
  B.bone({ name: 'armR', parent: 'body', pos: [-0.26, 0.12, 0.05] });
  B.bone({ name: 'legL', parent: 'body', pos: [0.13, -0.22, 0] });
  B.bone({ name: 'legR', parent: 'body', pos: [-0.13, -0.22, 0] });
  const skin = new THREE.Color(sapper ? '#8a6a4a' : '#9a7e58'), dark = new THREE.Color('#5a4230'), belly = new THREE.Color('#c8ac80');
  const shade = (_c: THREE.Vector3, n: THREE.Vector3) => skin.clone().lerp(belly, Math.max(0, n.z) * 0.4).lerp(dark, Math.max(0, -n.y) * 0.4);
  // A round body and a big round head: small, and certain everything is food.
  B.add(blob(new THREE.Vector3(0, 0.36, 0), 0.25, 1, 1.05, 0.95, 1), 'body', shade);
  B.add(blob(new THREE.Vector3(0, 0.7, 0.04), 0.22, 1.1, 0.95, 1, 1), 'head', shade);
  // Snout, eyes, ears.
  B.add(blob(new THREE.Vector3(0, 0.66, 0.25), 0.08, 1.3, 0.8, 1, 0), 'head', () => new THREE.Color('#d8a080'));
  for (const sx of [1, -1]) {
    B.add(blob(new THREE.Vector3(0.09 * sx, 0.76, 0.2), 0.055, 1, 1.2, 0.6, 1), 'head', () => new THREE.Color('#1a1410'));
    B.add(blob(new THREE.Vector3(0.1 * sx, 0.78, 0.23), 0.018, 1, 1, 1, 0), 'head', () => new THREE.Color('#ffe8a0'), true);
    B.add(cone(new THREE.Vector3(0.17 * sx, 0.84, 0), new THREE.Vector3(0.9 * sx, 0.6, -0.2), 0.06, 0.16, 3), 'head', () => skin.clone().multiplyScalar(0.8));
  }
  // The hard hat and its lamp: the lamp glows, which is what they dig toward.
  B.add(loft([
    { z: -0.02, y: 0.86, w: 0.24, h: 0.02, x: 0 },
    { z: 0.02, y: 0.9, w: 0.2, h: 0.1 },
  ], 8), 'head', () => new THREE.Color(sapper ? '#7a2a1a' : '#c8a030'));
  B.add(limb(new THREE.Vector3(0, 0.95, -0.02), new THREE.Vector3(0, 1.08, -0.04), 0.02, 0.02, 4), 'lamp', () => new THREE.Color('#3a3a3a'));
  B.add(blob(new THREE.Vector3(0, 1.12, -0.04), 0.07, 1, 1.1, 1, 1), 'lamp', () => new THREE.Color('#ffd070'), true);
  // Arms with digging claws; the sapper carries a satchel.
  for (const [side, sx] of [['L', 1], ['R', -1]] as const) {
    B.add(limb(new THREE.Vector3(0.24 * sx, 0.5, 0.05), new THREE.Vector3(0.36 * sx, 0.3, 0.12), 0.06, 0.05, 5), `arm${side}`, shade);
    for (let k = 0; k < 3; k++) B.add(cone(new THREE.Vector3((0.36 + k * 0.015) * sx, 0.28, 0.12 + k * 0.03), new THREE.Vector3(0.2 * sx, -1, 0.5), 0.02, 0.1, 3), `arm${side}`, () => new THREE.Color('#e8dcc0'));
    B.add(limb(new THREE.Vector3(0.13 * sx, 0.18, 0), new THREE.Vector3(0.14 * sx, 0.03, 0.03), 0.07, 0.06, 5), `leg${side}`, () => dark);
    B.add(blob(new THREE.Vector3(0.14 * sx, 0.03, 0.08), 0.07, 1, 0.5, 1.4, 0), `leg${side}`, () => dark);
  }
  if (sapper) {
    B.add(blob(new THREE.Vector3(0, 0.4, -0.26), 0.14, 1.1, 1, 0.7, 0), 'body', () => new THREE.Color('#5a3a22'));
    B.add(blob(new THREE.Vector3(0, 0.55, -0.3), 0.05, 1, 1, 1, 0), 'body', () => new THREE.Color('#ff7a30'), true);
  }
  const root = B.build(new THREE.Color('#ffc860'));
  const run = B.clip('run', 0.42, (t) => {
    const a = t * Math.PI * 2;
    return {
      body: { p: [0, Math.abs(Math.sin(a)) * 0.06, 0], r: [0.15, 0, Math.sin(a) * 0.12] },
      head: { r: [-0.1, 0, -Math.sin(a) * 0.1] },
      lamp: { r: [Math.sin(a + 1) * 0.3, 0, Math.sin(a) * 0.3] },
      armL: { r: [Math.sin(a) * 0.9, 0, 0] }, armR: { r: [-Math.sin(a) * 0.9, 0, 0] },
      legL: { r: [-Math.sin(a) * 0.8, 0, 0] }, legR: { r: [Math.sin(a) * 0.8, 0, 0] },
    };
  });
  const idle = B.clip('idle', 1.6, (t) => {
    const a = t * Math.PI * 2;
    return { body: { p: [0, Math.sin(a * 2) * 0.01, 0] }, head: { r: [0, Math.sin(a) * 0.4, 0] }, lamp: { r: [Math.sin(a * 2) * 0.15, 0, 0] }, armL: { r: [0.2, 0, Math.sin(a * 4) * 0.1] } };
  });
  const attack = B.clip('attack', 0.45, (t) => {
    const k = Math.sin(t * Math.PI);
    return { body: { r: [0.35 * k, 0, 0] }, armL: { r: [-1.6 * k, 0, 0] }, armR: { r: [-1.2 * k, 0, 0] }, head: { r: [0.2 * k, 0, 0] } };
  });
  const burrow = B.clip('burrow', 0.5, (t) => {
    const a = t * Math.PI * 2;
    return { body: { p: [0, -0.35, 0], r: [0.9, 0, 0] }, armL: { r: [-1.2 + Math.sin(a) * 0.8, 0, 0] }, armR: { r: [-1.2 - Math.sin(a) * 0.8, 0, 0] }, lamp: { r: [Math.sin(a * 2) * 0.4, 0, 0] } };
  });
  const rise = B.clip('rise', 0.6, (t) => {
    const e = Math.min(1, t * 1.3);
    return { root: { p: [0, -0.6 * (1 - e), 0] }, body: { r: [0.6 * (1 - e), 0, 0] }, armL: { r: [-2.2 * (1 - e), 0, 0] }, armR: { r: [-2.2 * (1 - e), 0, 0] } };
  });
  const die = B.clip('die', 0.8, (t) => {
    const e = 1 - (1 - Math.min(1, t * 1.4)) ** 2;
    return { root: { r: [-1.4 * e, 0, 0], p: [0, 0, -0.2 * e] }, head: { r: [0.3 * e, 0, 0] }, lamp: { r: [1.2 * e, 0, 0] }, armL: { r: [-1.5 * e, 0, 0.5 * e] }, armR: { r: [-1.2 * e, 0, -0.6 * e] } };
  });
  const hit = B.clip('hit', 0.3, (t) => ({ body: { r: [-0.25 * Math.sin(t * Math.PI), 0, 0] } }));
  return { root, clips: { run, idle, attack, burrow, rise, die, hit } };
}
