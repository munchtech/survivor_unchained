import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';
import { markShared } from './dispose';

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

/** Every part in one folder, gathered from the packs by
 *  tools/assets/people.py (textures shared by name, WebP at full size). */
const DIR = '/assets/people';
const BASE = DIR, OUTFITS = DIR, HAIR = DIR;
const ANIMS = [`${DIR}/UAL1.glb`, `${DIR}/UAL2.glb`];

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
/* Parts share their textures by file (an outfit's arms, body, legs and feet
 * all paint from the same 4K sheets): each image is fetched and decoded
 * once, and every part's texture is a copy over the one source, so the GPU
 * holds one too. */
const images = new Map<string, Promise<THREE.Texture>>();
loader.register((parser) => {
  const own = parser.loadImageSource.bind(parser);
  parser.loadImageSource = (index: number, imageLoader: THREE.Loader) => {
    const uri = (parser.json.images?.[index] as { uri?: string } | undefined)?.uri;
    if (!uri || uri.startsWith('data:')) return own(index, imageLoader);
    const key = new URL(uri, new URL(parser.options.path, location.href)).href;
    let p = images.get(key);
    if (!p) { p = own(index, imageLoader); images.set(key, p); }
    return p.then((t) => t.clone());
  };
  return { name: 'shared_images' };
});
const cache = new Map<string, Promise<GLTF>>();
const loaded = new Map<string, GLTF>();
const load = (url: string) => {
  let p = cache.get(url);
  if (!p) {
    // Every person made from a part shares its geometry and textures, which
    // outlive any zone (dispose.ts); their materials are their own.
    p = loader.loadAsync(encodeURI(url)).then((g) => { markShared(g.scene, false); loaded.set(url, g); return g; });
    cache.set(url, p);
  }
  return p;
};
/** A part already loaded (preloadPeople), for building people on the spot. */
const got = (url: string) => {
  const g = loaded.get(url);
  if (!g) throw new Error(`person part not preloaded: ${url}`);
  return g;
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
  /** Skin tone (a CSS colour), as it would look on fair skin; none leaves
   *  the skin as painted. */
  skin?: string;
  /** The outfit dyed (CSS colours): `cloth` the main cloth (the ranger's
   *  greens, the peasant's shirt), `under` the trousers. */
  dye?: { cloth?: string; under?: string };
}

/* Dyes. Each outfit's texture keeps its cloth in a colour of its own (the
 * ranger's greens, the peasant's cream shirt and dark brown trousers), so a
 * dye picks those pixels by hue, saturation and value and recolours them,
 * keeping their shading: a pixel as bright as the cloth's middle tone
 * becomes the dye colour itself. Leather, metal and skin are left alone. */
interface DyeMask { h: [number, number]; s: [number, number]; v: [number, number]; lum: number }
const DYES: Record<string, { cloth?: DyeMask; under?: DyeMask }> = {
  MI_Ranger: { cloth: { h: [0.17, 0.45], s: [0.25, 1], v: [0.03, 1], lum: 0.037 } },
  MI_Peasant: {
    cloth: { h: [0.04, 0.2], s: [0, 0.35], v: [0.5, 1], lum: 0.25 },
    under: { h: [0, 0.14], s: [0.3, 1], v: [0, 0.3], lum: 0.008 },
  },
};
const DYE_GLSL = `
uniform vec3 uDye;
uniform vec3 uDyeH, uDyeS, uDyeV; // (lo, hi, soft)
uniform float uDyeLum;
float dyeBand(float x, vec3 r) { return smoothstep(r.x - r.z, r.x, x) * (1.0 - smoothstep(r.y, r.y + r.z, x)); }
vec3 dyeHsv(vec3 c) {
  vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
  vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
  vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
  float d = q.x - min(q.w, q.y);
  return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + 1e-10)), d / (q.x + 1e-10), q.x);
}`;
function dyeMaterial(mat: THREE.MeshStandardMaterial, mask: DyeMask, color: THREE.Color) {
  const prev = mat.onBeforeCompile;
  const band = (r: [number, number]) => new THREE.Vector3(r[0], r[1], 0.05);
  mat.onBeforeCompile = (sh, gl) => {
    prev.call(mat, sh, gl);
    Object.assign(sh.uniforms, {
      uDye: { value: color }, uDyeH: { value: band(mask.h) }, uDyeS: { value: band(mask.s) }, uDyeV: { value: band(mask.v) }, uDyeLum: { value: mask.lum },
    });
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>\n${DYE_GLSL}`)
      .replace('#include <map_fragment>', `#include <map_fragment>
      {
        vec3 c = diffuseColor.rgb;
        vec3 hsv = dyeHsv(pow(max(c, vec3(0.0)), vec3(1.0 / 2.2)));
        float m = dyeBand(hsv.x, uDyeH) * dyeBand(hsv.y, uDyeS) * dyeBand(hsv.z, uDyeV);
        float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
        diffuseColor.rgb = mix(c, min(uDye * (lum / uDyeLum), vec3(1.0)), m);
      }`);
  };
  const key = mat.customProgramCacheKey();
  mat.customProgramCacheKey = () => `${key}|dye`;
}


/** The fair tone the skin choices are measured from (render/recolor.ts's
 *  palette): a choice becomes a multiply over the painted skin. */
const FAIR = new THREE.Color('#f2c4a8');
const SKIN_MAT = /^MI_(Superhero|Regular)_/;

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
 *  and to the clothes over it, so a shirt follows what it covers.
 *
 *  Each breast follows the proportion people find most attractive (the
 *  Mallucci study): about 45:55 above and below the nipple line, the upper
 *  slope straight (a linear rise), the lower pole full and convex (a
 *  sphere-cap curve), eased into the chest at its base, set a little
 *  apart, projecting forward with the nipple tilted slightly up. Normals
 *  follow the new surface (from the shape's own slope) so light rounds it. */
const BUST = { cx: 0.086, cy: 1.305, ax: 0.098, up: 0.085, down: 0.098, lift: 0.052 };

function domeAt(x: number, y: number, side: number) {
  const ex = (x - side * BUST.cx) / BUST.ax;
  const dy = y - BUST.cy;
  const upper = dy > 0;
  const ey = dy / (upper ? BUST.up : BUST.down);
  const r = Math.sqrt(ex * ex + ey * ey);
  if (r >= 1) return 0;
  // Straight above, full and round below; eased in at the base.
  const profile = upper ? 1 - r : Math.sqrt(1 - r * r);
  return profile * sstep(1.0, 0.6, r);
}

function shapeFigure(g: THREE.BufferGeometry, bust: number) {
  const pos = g.getAttribute('position') as THREE.BufferAttribute;
  const nor = g.getAttribute('normal') as THREE.BufferAttribute | undefined;
  const n = new THREE.Vector3();
  const H = BUST.lift * bust, d = 0.003;
  const height = (x: number, y: number) => domeAt(x, y, -1) + domeAt(x, y, 1);
  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
    // Only the front of the chest (not the back, not arms held out).
    const front = sstep(-0.01, 0.075, z) * (Math.abs(x) < 0.22 ? 1 : 0);
    const k = height(x, y) * front;
    let gx = 0, gy = 0;
    if (k > 0) {
      const side = x < 0 ? -1 : 1;
      z += H * k;
      x += side * H * 0.22 * k;
      y += H * 0.1 * k * (y < BUST.cy + 0.02 ? 1 : 0.4);
      gx = H * front * (height(x + d, y) - height(x - d, y)) / (2 * d);
      gy = H * front * (height(x, y + d) - height(x, y - d)) / (2 * d);
    }
    // Waist in, hips out (the torso only).
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

/** Put a person together: a Group holding the rig and every part, bones
 *  shared. Height is left as authored (metres). */
function build(spec: PersonSpec, get: (url: string) => GLTF): { root: THREE.Group; bones: Map<string, THREE.Bone> } {
  const P = PARTS[spec.sex];
  const body = SkeletonUtils.clone(get(`${BASE}/${P.body}.gltf`).scene) as THREE.Group;
  const bones = new Map<string, THREE.Bone>();
  body.traverse((o) => { if ((o as THREE.Bone).isBone) bones.set(o.name, o as THREE.Bone); });
  const figure = spec.sex === 'female' ? spec.figure ?? 0.9 : 0;
  const shape = (m: THREE.SkinnedMesh) => {
    if (figure > 0) m.geometry = variant(m.geometry, `figure:${figure}`, (g) => shapeFigure(g, figure));
  };
  const covered = COVER.filter(([part]) => (spec.outfit ?? []).some((p) => part.test(p))).map(([, bonesRe]) => bonesRe);
  // Top and trousers together cover the hips too (trousers alone sit lower,
  // and a bare-chested figure keeps its hips).
  const has = (re: RegExp) => (spec.outfit ?? []).some((p) => re.test(p));
  if (has(/_Body/) && has(/_Legs/)) covered.push(/^pelvis$/);
  body.traverse((o) => {
    const m = o as THREE.SkinnedMesh;
    if (!m.isSkinnedMesh) return;
    m.castShadow = true; m.receiveShadow = true; m.frustumCulled = false;
    if (/superhero|retopology/i.test(m.name)) {
      shape(m);
      if (covered.length) maskCovered(m, covered);
    }
  });
  const attach = (url: string) => {
    const part = SkeletonUtils.clone(get(url).scene);
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
  for (const p of spec.outfit ?? []) attach(`${OUTFITS}/${p}.gltf`);
  if (spec.hair) attach(`${HAIR}/${spec.hair}.gltf`);
  if (spec.beard) attach(`${HAIR}/Hair_Beard.gltf`);
  // Each person has materials of their own (a hit flashes one person, not
  // everyone in the same shirt; textures stay shared). Hair, beard and brows
  // take the chosen colour (their texture is grey), skin the chosen tone.
  const hair = new THREE.Color(spec.hairColor ?? '#3a2a1e');
  const skin = spec.skin ? new THREE.Color(spec.skin) : null;
  if (skin) { skin.r /= FAIR.r; skin.g /= FAIR.g; skin.b /= FAIR.b; }
  const own = new Map<string, THREE.MeshStandardMaterial>();
  const cloth = spec.dye?.cloth ? new THREE.Color(spec.dye.cloth) : null;
  const under = spec.dye?.under ? new THREE.Color(spec.dye.under) : null;
  body.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const src = m.material as THREE.MeshStandardMaterial;
    const legs = /_Legs/.test(m.name);
    const k = `${src.uuid}|${legs}`;
    let mat = own.get(k);
    if (!mat) {
      mat = src.clone();
      // (A clone leaves shader changes behind: the body's cover mask.)
      mat.onBeforeCompile = src.onBeforeCompile;
      mat.customProgramCacheKey = src.customProgramCacheKey;
      if (/Hair/i.test(mat.name)) mat.color.copy(hair);
      else if (skin && SKIN_MAT.test(mat.name)) mat.color.copy(skin);
      const d = DYES[mat.name];
      // (One dye per material: trousers with a colour of their own take it.)
      if (d?.under && under && legs) dyeMaterial(mat, d.under, under);
      else if (d?.cloth && cloth) dyeMaterial(mat, d.cloth, cloth);
      own.set(k, mat);
    }
    m.material = mat;
  });
  const root = new THREE.Group();
  root.add(body);
  return { root, bones };
}

/** Put a person together, loading what it needs. */
export async function assemble(spec: PersonSpec) {
  const P = PARTS[spec.sex];
  const urls = [`${BASE}/${P.body}.gltf`, ...(spec.outfit ?? []).map((n) => `${OUTFITS}/${n}.gltf`), ...(spec.hair ? [`${HAIR}/${spec.hair}.gltf`] : []), ...(spec.beard ? [`${HAIR}/Hair_Beard.gltf`] : [])];
  await Promise.all(urls.map(load));
  return build(spec, got);
}

/** Put a person together from preloaded parts (preloadPeople). */
export const assembleSync = (spec: PersonSpec) => build(spec, got);

const partUrls = () => [
  ...(['male', 'female'] as const).flatMap((sx) => {
    const P = PARTS[sx];
    return [`${BASE}/${P.body}.gltf`, ...[...P.peasant, ...P.ranger, P.hood, P.pauldron].map((n) => `${OUTFITS}/${n}.gltf`)];
  }),
  ...HAIRSTYLES.map((h) => `${HAIR}/${h}.gltf`),
];

/** Load every body, outfit piece, hairstyle and clip, so people can be put
 *  together synchronously (the game builds its figures on the spot). */
export async function preloadPeople(onProgress?: (done: number, total: number) => void) {
  const urls = [...partUrls(), ...ANIMS];
  let done = 0;
  await Promise.all(urls.map((u) => load(u).then(() => onProgress?.(++done, urls.length))));
  await peopleClips();
}

/** A clip, once preloaded. */
export const clipSync = (name: string) => clips?.get(name);
export const peopleReady = () => !!clips;
