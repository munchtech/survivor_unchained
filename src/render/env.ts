import * as THREE from 'three';
import { sharedLoader } from './gltfShared';
import { markShared } from './dispose';
import { occludable } from './assets';

/* The world's kits (Quaternius, CC0; gathered by tools/assets/env.py):
 *
 *   village  the Medieval Village MegaKit: walls, corners, floors, roofs,
 *            doors, windows, stairs and balconies on a 2 m grid, from which
 *            houses are put together (world/zones/houses.ts)
 *   nature   the Stylized Nature MegaKit: trees, rocks, ferns, grass
 *   props    the Fantasy Props MegaKit: barrels, stalls, anvils, lanterns
 *   custom   the game's own models (tools/models/, built in Blender), in the
 *            village kit's materials and textures
 *
 * Only what the game uses is loaded (the kits hold hundreds of pieces, and
 * every texture decoded is memory); pieces share their textures by file.
 * Copies share geometry and materials, and outlive a zone's teardown. Every
 * piece casts and takes shadows, and dithers away where it stands between
 * the camera and the survivor, as the old props did. */

export type EnvKit = 'village' | 'nature' | 'props' | 'custom';

const BASE = `${import.meta.env.BASE_URL}assets/env/`;
const loader = sharedLoader();
const templates = new Map<string, THREE.Object3D>();
let manifest: Record<EnvKit, Record<string, { min: [number, number, number]; max: [number, number, number] }>> | null = null;

const key = (kit: EnvKit, name: string) => `${kit}/${name}`;

/** Load these pieces (once each), ready for envModel(). */
export async function preloadEnv(list: Array<[EnvKit, string]>) {
  if (!manifest) manifest = await (await fetch(`${BASE}manifest.json`)).json();
  await Promise.all(list.map(async ([kit, name]) => {
    const k = key(kit, name);
    if (templates.has(k)) return;
    const gltf = await loader.loadAsync(`${BASE}${kit}/${name}.gltf`);
    const root = gltf.scene;
    prepare(root, kit);
    markShared(root, true);
    templates.set(k, root);
  }));
}

export const envLoaded = (kit: EnvKit, name: string) => templates.has(key(kit, name));

/** A copy of a piece (geometry and materials shared with every other). */
export function envModel(kit: EnvKit, name: string): THREE.Object3D {
  const t = templates.get(key(kit, name));
  if (!t) throw new Error(`env piece not preloaded: ${kit}/${name}`);
  const c = t.clone(true);
  // Which piece this is (tools/godot/export_zone.mjs reads it).
  c.userData.env = key(kit, name);
  return c;
}

/** A piece's bounds as authored (metres). */
export function envBounds(kit: EnvKit, name: string) {
  const b = manifest?.[kit]?.[name];
  return b ? new THREE.Box3(new THREE.Vector3(...b.min), new THREE.Vector3(...b.max)) : null;
}

/** The meshes of a piece, for merging (world/zones/houses.ts). */
export function envTemplate(kit: EnvKit, name: string) {
  const t = templates.get(key(kit, name));
  if (!t) throw new Error(`env piece not preloaded: ${kit}/${name}`);
  return t;
}

function prepare(root: THREE.Object3D, kit: EnvKit) {
  bakeSkins(root);
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.castShadow = true;
    m.receiveShadow = true;
    for (const mat of Array.isArray(m.material) ? m.material : [m.material]) {
      const s = mat as THREE.MeshStandardMaterial;
      if (!s.isMeshStandardMaterial) continue;
      if (s.map) s.map.anisotropy = 8;
      // Leaves and grass are cut out by alpha: hard edges, both sides,
      // shadows the shape of the leaf.
      if (kit === 'nature' && (s.transparent || s.alphaTest > 0 || /Leaf|Leaves|Grass|Flower|Petal|Clover|Fern|Plant/i.test(s.name))) {
        s.transparent = false;
        s.alphaTest = Math.max(s.alphaTest, 0.5);
        s.side = THREE.DoubleSide;
      }
      occludable(s);
      weather(s, kit);
    }
  });
}

/* A few props come rigged (the chest, for its lid). Nothing here animates
 * them, and a copy made by clone() stays bound to the template's bones, so it
 * draws where the template is (the world's origin) whatever its position.
 * Skinned meshes are baked, in the pose they were loaded in, to plain ones. */
function bakeSkins(root: THREE.Object3D) {
  const skinned: THREE.SkinnedMesh[] = [];
  root.traverse((o) => { if ((o as THREE.SkinnedMesh).isSkinnedMesh) skinned.push(o as THREE.SkinnedMesh); });
  if (!skinned.length) return;
  root.updateMatrixWorld(true);
  const skin = new THREE.Matrix4(), part = new THREE.Matrix4(), normal = new THREE.Matrix3();
  const v = new THREE.Vector3();
  for (const sm of skinned) {
    sm.skeleton.update();
    const geo = sm.geometry.clone();
    const pos = geo.attributes.position, nrm = geo.attributes.normal;
    const idx = geo.attributes.skinIndex, wt = geo.attributes.skinWeight;
    const bones = sm.skeleton.boneMatrices!;
    for (let i = 0; i < pos.count; i++) {
      skin.elements.fill(0);
      for (let k = 0; k < 4; k++) {
        const w = wt.getComponent(i, k);
        if (!w) continue;
        part.fromArray(bones, idx.getComponent(i, k) * 16).multiplyScalar(w);
        for (let e = 0; e < 16; e++) skin.elements[e] += part.elements[e];
      }
      skin.premultiply(sm.bindMatrixInverse).multiply(sm.bindMatrix);
      pos.setXYZ(i, ...v.fromBufferAttribute(pos, i).applyMatrix4(skin).toArray());
      if (nrm) nrm.setXYZ(i, ...v.fromBufferAttribute(nrm, i).applyMatrix3(normal.getNormalMatrix(skin)).normalize().toArray());
    }
    geo.deleteAttribute('skinIndex');
    geo.deleteAttribute('skinWeight');
    geo.computeBoundingBox();
    geo.computeBoundingSphere();
    const m = new THREE.Mesh(geo, sm.material);
    m.name = sm.name;
    m.matrix.copy(sm.matrix);
    m.matrix.decompose(m.position, m.quaternion, m.scale);
    sm.parent!.add(m);
    sm.removeFromParent();
    sm.geometry.dispose();
    sm.skeleton.dispose();
  }
}

/* The kits are painted bright and clean, for a sunnier world than this one.
 * Each material is weathered in its shader: its colour pulled toward grey
 * and darkened (clay roofs dulled, plaster grimed, timber darkened), and on
 * the village's walls the foot of every wall darker still, where mud and rain
 * splash. Local height is height above the ground: houses and walls are
 * merged in their own frame, 0 at the foot (world/zones/houses.ts). */
const WEATHER: Array<[RegExp, number, [number, number, number]]> = [
  // material, saturation kept, colour multiply
  [/RoundTiles/, 0.42, [0.74, 0.7, 0.68]],
  [/Plaster/, 0.6, [0.84, 0.82, 0.78]],
  [/WoodTrim|Wood/, 0.7, [0.72, 0.7, 0.68]],
  [/Brick|Rock|Stone/, 0.7, [0.84, 0.83, 0.8]],
  [/Leaf|Leaves|Grass|Clover|Fern|Plant|Bush/, 0.7, [0.8, 0.84, 0.76]],
  [/Bark/, 0.75, [0.8, 0.78, 0.76]],
  [/./, 0.82, [0.88, 0.87, 0.85]],
];

/** How a kit material is weathered: saturation kept, colour multiply. */
export function weatherOf(name: string): [number, [number, number, number]] {
  const [, sat, tint] = WEATHER.find(([re]) => re.test(name))!;
  return [sat, tint];
}

function weather(mat: THREE.MeshStandardMaterial, kit: EnvKit) {
  // A material is shared by the meshes of a piece: weather it once.
  if (mat.userData.weathered) return;
  mat.userData.weathered = true;
  const [sat, tint] = weatherOf(mat.name);
  const foot = kit === 'village' || kit === 'custom';
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh, r) => {
    prev.call(mat, sh, r);
    sh.uniforms.uWeatherSat = { value: sat };
    sh.uniforms.uWeatherTint = { value: new THREE.Vector3(...tint) };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying float vWeatherY;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvWeatherY = position.y;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uWeatherSat;\nuniform vec3 uWeatherTint;\nvarying float vWeatherY;')
      .replace('#include <map_fragment>', `#include <map_fragment>
        {
          float l = dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722));
          diffuseColor.rgb = mix(vec3(l), diffuseColor.rgb, uWeatherSat) * uWeatherTint;
          ${foot ? 'diffuseColor.rgb *= mix(0.6, 1.0, smoothstep(0.0, 1.3, vWeatherY));' : ''}
        }`);
  };
  const key = mat.customProgramCacheKey();
  mat.customProgramCacheKey = () => `${key}|weather${foot ? 'foot' : ''}`;
}
