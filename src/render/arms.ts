import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { markShared } from './dispose';

/* Weapons worth holding: third-party models (Sketchfab, CC-BY and CC0; see
 * public/assets/CREDITS.md), each turned and scaled on load to one
 * convention so any hand can take any of them:
 *
 *   +Y  the shaft, from the grip out to the business end (a blade's tip, an
 *       axe's head, a staff's crown); the grip is at the origin;
 *   +X  the blade's width (its edge in line with the knuckles);
 *   +Z  its thickness.
 *
 * The model's own spread gives the axes (longest, middle, shortest); what
 * that cannot know (which end is the grip, where along the shaft the hand
 * goes, how long the thing is in life) is written below per weapon. */

export interface ArmSpec {
  file: string;
  /** Length in life, metres (tip to pommel, or the whole staff). */
  length: number;
  /** Where the hand closes, as a fraction of the length from the grip end. */
  grip: number;
  /** The model's long axis runs tip-first: turn it round. */
  flip?: boolean;
  /** Turn about the shaft after (radians), when the width axis lies. */
  roll?: number;
  /** Only this node (and what hangs from it) of a model holding several. */
  node?: string;
  /** The second-longest spread is the shaft (a crossbow's bow is wider
   * than its stock is long). */
  swap?: boolean;
  /** How a hand takes it: 'fist' (the default) closes round the shaft, which
   *  leaves on the thumb side; 'pistol' holds a stock pointing where the
   *  fingers do, its top (+Z) on the thumb side. */
  hold?: 'fist' | 'pistol';
}

export const ARMS: Record<string, ArmSpec> = {
  chevalier_sword: { file: 'chevalier_sword', length: 1.0, grip: 0.1 },
  viking_sword: { file: 'viking_sword', length: 0.92, grip: 0.13 },
  longsword: { file: 'longsword', length: 1.05, grip: 0.22, flip: true },
  zweihander: { file: 'zweihander', length: 1.6, grip: 0.2 },
  mace: { file: 'mace', length: 0.75, grip: 0.12 },
  viking_axe: { file: 'viking_axe', length: 0.8, grip: 0.15, roll: Math.PI },
  snake_axe: { file: 'snake_axe', length: 1.3, grip: 0.22 },
  mage_staff: { file: 'mage_staff', length: 1.75, grip: 0.45 },
  short_staff: { file: 'mage_staff', length: 1.1, grip: 0.3 },
  crossbow: { file: 'crossbow', length: 0.85, grip: 0.3, swap: true, hold: 'pistol' },
  shield_round: { file: 'shield_round', length: 0.66, grip: 0.5 },
  daggers: { file: 'daggers', length: 0.4, grip: 0.2, node: 'Cube004' },
  dagger_b: { file: 'daggers', length: 0.4, grip: 0.2, node: 'Cube00401' },
};

const loader = new GLTFLoader();
const templates = new Map<string, THREE.Object3D>();

/** Load every weapon model and normalise it (once, at boot). */
export async function preloadArms() {
  const files = new Map<string, Promise<THREE.Group>>();
  await Promise.all(Object.entries(ARMS).map(async ([id, spec]) => {
    let f = files.get(spec.file);
    if (!f) { f = loader.loadAsync(`/assets/weapons/${spec.file}.glb`).then((g) => g.scene); files.set(spec.file, f); }
    // Each weapon normalises its own copy (a file can hold several).
    templates.set(id, normalise((await f).clone(true), spec));
  }));
}

export const armReady = (id: string) => templates.has(id);

/** A copy of a weapon, ready for a socket (geometry and materials shared). */
export function arm(id: string): THREE.Object3D | null {
  const t = templates.get(id);
  return t ? t.clone(true) : null;
}

/** A weapon's own axes: the principal axes of its vertices (a box would be
 * fooled by a model tilted in its file), longest spread first, each signed
 * to agree with the file's axis it lies closest to. Positions are in the
 * frame the model will sit in (its parent's), and come back projected. */
function principal(src: THREE.Object3D) {
  const rel = src.parent ? src.parent.matrixWorld.clone().invert() : new THREE.Matrix4();
  const pts: number[] = [];
  const v = new THREE.Vector3(), m = new THREE.Matrix4();
  src.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    const pos = mesh.geometry.getAttribute('position');
    m.multiplyMatrices(rel, mesh.matrixWorld);
    for (let i = 0; i < pos.count; i++) {
      v.fromBufferAttribute(pos, i).applyMatrix4(m);
      pts.push(v.x, v.y, v.z);
    }
  });
  const n = pts.length / 3;
  const mean = [0, 0, 0];
  for (let i = 0; i < n; i++) for (let a = 0; a < 3; a++) mean[a] += pts[i * 3 + a] / n;
  const c = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (let i = 0; i < n; i++) {
    const d = [pts[i * 3] - mean[0], pts[i * 3 + 1] - mean[1], pts[i * 3 + 2] - mean[2]];
    for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) c[a][b] += d[a] * d[b] / n;
  }
  const { values, vectors } = jacobi(c);
  const order = [0, 1, 2].sort((a, b) => values[b] - values[a]);
  const axes = order.map((k) => {
    const e = new THREE.Vector3(vectors[0][k], vectors[1][k], vectors[2][k]).normalize();
    const big = [Math.abs(e.x), Math.abs(e.y), Math.abs(e.z)];
    const at = big.indexOf(Math.max(...big));
    if (e.getComponent(at) < 0) e.negate();
    return e;
  });
  return { axes, pts };
}

/** Eigen-decomposition of a symmetric 3x3 (cyclic Jacobi). Columns of
 * `vectors` are the eigenvectors. */
function jacobi(a0: number[][]) {
  const a = a0.map((r) => r.slice());
  const vec = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  for (let sweep = 0; sweep < 32; sweep++) {
    const off = a[0][1] ** 2 + a[0][2] ** 2 + a[1][2] ** 2;
    if (off < 1e-18) break;
    for (const [p, q] of [[0, 1], [0, 2], [1, 2]]) {
      if (Math.abs(a[p][q]) < 1e-14) continue;
      const theta = (a[q][q] - a[p][p]) / (2 * a[p][q]);
      const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1));
      const cs = 1 / Math.sqrt(t * t + 1), sn = t * cs;
      for (let k = 0; k < 3; k++) {
        const akp = a[k][p], akq = a[k][q];
        a[k][p] = cs * akp - sn * akq;
        a[k][q] = sn * akp + cs * akq;
      }
      for (let k = 0; k < 3; k++) {
        const apk = a[p][k], aqk = a[q][k];
        a[p][k] = cs * apk - sn * aqk;
        a[q][k] = sn * apk + cs * aqk;
      }
      for (let k = 0; k < 3; k++) {
        const vkp = vec[k][p], vkq = vec[k][q];
        vec[k][p] = cs * vkp - sn * vkq;
        vec[k][q] = sn * vkp + cs * vkq;
      }
    }
  }
  return { values: [a[0][0], a[1][1], a[2][2]], vectors: vec };
}

function normalise(scene: THREE.Object3D, spec: ArmSpec) {
  const src = spec.node ? scene.getObjectByName(spec.node) ?? scene : scene;
  scene.updateMatrixWorld(true);
  const { axes, pts } = principal(src);
  let [long, mid] = axes;
  if (spec.swap) [long, mid] = [mid, long];
  if (spec.flip) long = long.clone().negate();
  const short = new THREE.Vector3().crossVectors(mid, long);
  // The model's extent along each new axis, and the middle of it.
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  const basis = [mid, long, short], p = new THREE.Vector3();
  for (let i = 0; i < pts.length; i += 3) {
    p.set(pts[i], pts[i + 1], pts[i + 2]);
    for (let a = 0; a < 3; a++) {
      const d = p.dot(basis[a]);
      if (d < lo[a]) lo[a] = d;
      if (d > hi[a]) hi[a] = d;
    }
  }
  const centre = new THREE.Vector3();
  for (let a = 0; a < 3; a++) centre.addScaledVector(basis[a], (lo[a] + hi[a]) / 2);
  // Rows of the turn: model axes -> (X = mid, Y = long, Z = short).
  const turn = new THREE.Matrix4().makeBasis(mid, long, short).transpose();
  const inner = new THREE.Group();
  const holder = new THREE.Group();
  const model = src === scene ? scene : src.clone(true);
  // Centre the model, turn it, scale it to life, put the grip at the origin.
  model.position.sub(centre);
  inner.add(model);
  inner.quaternion.setFromRotationMatrix(turn);
  if (spec.roll) inner.quaternion.premultiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), spec.roll));
  const k = spec.length / (hi[1] - lo[1]);
  inner.scale.setScalar(k);
  inner.position.y = spec.length * (0.5 - spec.grip);
  holder.add(inner);
  holder.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.castShadow = true;
    m.receiveShadow = true;
  });
  holder.name = `arm:${spec.file}`;
  // Copies share all of it, past any zone (dispose.ts).
  markShared(holder, true);
  return holder;
}
