import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';

/* People: Quaternius's Universal Base Characters, dressed in the Modular
 * Character Outfits and moved by the Universal Animation Library (all CC0,
 * all on one humanoid skeleton).
 *
 * A person is put together from parts that each come with their own copy
 * of the skeleton: a body (which brings the head, eyes and brows), outfit
 * pieces (arms, torso, legs, feet, a hood...), a hairstyle. Every part's
 * skinned meshes are rebound to the body's bones by name, so one mixer
 * moves them all. Outfit pieces bring the skin they show (bare forearms,
 * hands), so under clothes only the body's head is kept: the rest of it is
 * masked away by its bone weights, which keeps a broad-chested body from
 * pushing through a shirt cut for a slighter one. */

export type Sex = 'male' | 'female';

/** Where the unpacked assets are served from (see tools/assets). */
const ROOT = '/_q';
const BASE = `${ROOT}/Universal Base Characters/Universal Base Characters[Standard]/Base Characters/Godot - UE`;
const OUTFITS = `${ROOT}/Modular Character Outfits - Fantasy/Modular Character Outfits - Fantasy[Standard]/Exports/glTF (Godot-Unreal)/Modular Parts`;
const HAIR = `${ROOT}/Universal Base Characters/Universal Base Characters[Standard]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)`;
const ANIMS = [
  `${ROOT}/Universal Animation Library/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb`,
  `${ROOT}/Universal Animation Library 2/Universal Animation Library 2[Standard]/Unreal-Godot/UAL2_Standard.glb`,
];

export const PARTS = {
  male: {
    body: 'Superhero_Male_FullBody',
    peasant: ['Male_Peasant_Arms', 'Male_Peasant_Body', 'Male_Peasant_Legs', 'Male_Peasant_Feet'],
    ranger: ['Male_Ranger_Arms', 'Male_Ranger_Body', 'Male_Ranger_Legs', 'Male_Ranger_Feet_Boots'],
    hood: 'Male_Ranger_Head_Hood', pauldron: 'Male_Ranger_Acc_Pauldron',
  },
  female: {
    body: 'Superhero_Female_FullBody',
    peasant: ['Female_Peasant_Arms', 'Female_Peasant_Body', 'Female_Peasant_Legs', 'Female_Peasant_Feet'],
    ranger: ['Female_Ranger_Arms', 'Female_Ranger_Body', 'Female_Ranger_Legs', 'Female_Ranger_Feet'],
    hood: 'Female_Ranger_Head_Hood', pauldron: 'Female_Ranger_Acc_Pauldrons',
  },
} as const;

export const HAIRSTYLES = ['Hair_SimpleParted', 'Hair_Long', 'Hair_Buns', 'Hair_Buzzed', 'Hair_BuzzedFemale', 'Hair_Beard'] as const;

const loader = new GLTFLoader();
const cache = new Map<string, Promise<GLTF>>();
const load = (url: string) => {
  let p = cache.get(url);
  if (!p) { p = loader.loadAsync(encodeURI(url)); cache.set(url, p); }
  return p;
};

let clips: Map<string, THREE.AnimationClip> | null = null;
/** Every clip of the animation libraries, by name. */
export async function peopleClips() {
  if (clips) return clips;
  const out = new Map<string, THREE.AnimationClip>();
  for (const url of ANIMS) for (const c of (await load(url)).animations) out.set(c.name, c);
  clips = out;
  return out;
}

export interface PersonSpec {
  sex: Sex;
  /** Hair and brows are authored grey and tinted (a CSS colour). */
  hairColor?: string;
  /** Outfit pieces by name (PARTS), or none for the body as it is. */
  outfit?: readonly string[];
  hair?: string | null;
  beard?: boolean;
  /** A woman's figure, 0 (as modelled) to 1.5; see shapeFigure. */
  figure?: number;
}

/** What each outfit piece covers, as the body's bones under it: the body
 *  is hidden there (the piece brings any skin it shows, forearms, hands). */
const COVER: Array<[RegExp, RegExp]> = [
  [/_Arms/, /^(clavicle|upperarm|lowerarm|hand|index|middle|pinky|ring|thumb)_/],
  [/_Body/, /^spine_0[123]$/],
  [/_Legs/, /^(thigh|calf)/],
  [/_Feet/, /^(foot|ball)/],
];

/* Geometry variants (a masked body, a shaped figure) are copies, cached:
 * clones of a person share their source geometry. */
const variants = new Map<string, THREE.BufferGeometry>();
function variant(g: THREE.BufferGeometry, key: string, make: (g: THREE.BufferGeometry) => void) {
  const k = `${g.uuid}|${key}`;
  let v = variants.get(k);
  if (!v) { v = g.clone(); make(v); variants.set(k, v); }
  return v;
}

/** Hide the body where it is covered: a vertex goes when most of its weight
 *  is on covered bones. */
function maskCovered(mesh: THREE.SkinnedMesh, covered: RegExp[]) {
  const ids = new Set(mesh.skeleton.bones.map((b, i) => (covered.some((re) => re.test(b.name)) ? i : -1)).filter((i) => i >= 0));
  const key = `mask:${[...ids].sort((x, y) => x - y).join(',')}`;
  mesh.geometry = variant(mesh.geometry, key, (g) => {
    const si = g.getAttribute('skinIndex'), sw = g.getAttribute('skinWeight');
    const m = new Float32Array(si.count);
    for (let i = 0; i < si.count; i++) {
      let w = 0;
      for (let k = 0; k < 4; k++) if (ids.has(si.getComponent(i, k))) w += sw.getComponent(i, k);
      m[i] = 1 - w;
    }
    g.setAttribute('aKeep', new THREE.BufferAttribute(m, 1));
  });
  const mat = (mesh.material as THREE.MeshStandardMaterial).clone();
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aKeep;\nvarying float vKeep;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvKeep = aKeep;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vKeep;')
      .replace('#include <clipping_planes_fragment>', '#include <clipping_planes_fragment>\nif (vKeep < 0.5) discard;');
  };
  mat.customProgramCacheKey = () => 'person-cover-mask';
  mesh.material = mat;
}

const sstep = (a: number, b: number, x: number) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

/** A woman's figure, in the rig's bind space (metres, Y up, +Z forward): a
 *  fuller chest, a narrower waist, rounder hips. Applied alike to the body
 *  and to the clothes over it, so a shirt follows what it covers. The
 *  normals are tilted by the shape's slope so light falls on it rightly. */
function shapeFigure(g: THREE.BufferGeometry, bust: number) {
  const pos = g.getAttribute('position') as THREE.BufferAttribute;
  const nor = g.getAttribute('normal') as THREE.BufferAttribute | undefined;
  const n = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
    let gx = 0, gy = 0;
    // The chest: a soft rise over each breast, a little out and down.
    for (const side of [-1, 1]) {
      const ax = 0.105, ay = 0.095;
      const ex = (x - side * 0.088) / ax, ey = (y - 1.335) / ay;
      const r2 = ex * ex + ey * ey;
      if (r2 >= 1 || z < -0.02) continue;
      const front = sstep(-0.02, 0.07, z);
      const f = (1 - r2) * (1 - r2) * front;
      const h = bust * 0.06;
      z += h * f; y -= bust * 0.012 * f; x += side * bust * 0.008 * f;
      const k = h * front * 2 * (1 - r2);
      gx += k * (-2 * ex / ax); gy += k * (-2 * ey / ay);
    }
    // Waist in, hips out (the torso only, not arms held out).
    if (Math.abs(x) < 0.3) {
      const waist = Math.exp(-(((y - 1.12) / 0.07) ** 2)), hips = Math.exp(-(((y - 0.93) / 0.08) ** 2));
      const t = Math.min(1, bust);
      x *= 1 - 0.08 * t * waist + 0.07 * t * hips;
      z *= 1 - 0.05 * t * waist + 0.04 * t * hips;
    }
    pos.setXYZ(i, x, y, z);
    if (nor && (gx || gy)) {
      n.fromBufferAttribute(nor, i);
      if (n.z > 0) { n.x -= gx; n.y -= gy; n.normalize(); nor.setXYZ(i, n.x, n.y, n.z); }
    }
  }
  pos.needsUpdate = true;
  if (nor) nor.needsUpdate = true;
  g.computeBoundingSphere();
}

export async function assemble(spec: PersonSpec): Promise<{ root: THREE.Group; bones: Map<string, THREE.Bone> }> {
  const P = PARTS[spec.sex];
  const body = SkeletonUtils.clone((await load(`${BASE}/${P.body}.gltf`)).scene) as THREE.Group;
  const bones = new Map<string, THREE.Bone>();
  body.traverse((o) => { if ((o as THREE.Bone).isBone) bones.set(o.name, o as THREE.Bone); });
  const figure = spec.sex === 'female' ? spec.figure ?? 0.9 : 0;
  const shape = (m: THREE.SkinnedMesh) => {
    if (figure > 0) m.geometry = variant(m.geometry, `figure:${figure}`, (g) => shapeFigure(g, figure));
  };
  const covered = COVER.filter(([part]) => (spec.outfit ?? []).some((p) => part.test(p))).map(([, bonesRe]) => bonesRe);
  body.traverse((o) => {
    const m = o as THREE.SkinnedMesh;
    if (!m.isSkinnedMesh) return;
    m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false;
    if (/superhero|retopology/i.test(m.name)) {
      shape(m);
      if (covered.length) maskCovered(m, covered);
    }
  });
  const attach = async (url: string) => {
    const part = SkeletonUtils.clone((await load(url)).scene);
    const meshes: THREE.SkinnedMesh[] = [];
    part.traverse((o) => { if ((o as THREE.SkinnedMesh).isSkinnedMesh) meshes.push(o as THREE.SkinnedMesh); });
    for (const m of meshes) {
      const bs = m.skeleton.bones.map((b) => bones.get(b.name) ?? b);
      m.bind(new THREE.Skeleton(bs, m.skeleton.boneInverses), m.bindMatrix);
      m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false;
      // Clothes on the torso and hips take the same figure as the body.
      if (/_(Body|Legs)/.test(url)) shape(m);
      body.add(m);
    }
  };
  for (const p of spec.outfit ?? []) await attach(`${OUTFITS}/${p}.gltf`);
  if (spec.hair) await attach(`${HAIR}/${spec.hair}.gltf`);
  if (spec.beard) await attach(`${HAIR}/Hair_Beard.gltf`);
  // Hair, beard and brows take the chosen colour (their texture is grey).
  const tint = new THREE.Color(spec.hairColor ?? '#3a2a1e');
  body.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const mat = m.material as THREE.MeshStandardMaterial;
    if (/Hair/i.test(mat.name)) { m.material = mat.clone(); (m.material as THREE.MeshStandardMaterial).color.copy(tint); }
  });
  const root = new THREE.Group();
  root.add(body);
  return { root, bones };
}
