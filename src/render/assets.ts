import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';
import { floraUniforms, OCCLUDE_PARS, OCCLUDE_FRAG, OCCLUDE_VERT_PARS, OCCLUDE_VERT } from './flora';
import { grimeTexture, grimeColor, WORLD_GRIME, PEOPLE_GRIME } from './grime';
import { markShared } from './dispose';

/* Everything the game draws from a file comes through here, once.
 *
 * Characters are loaded as a template and cloned per instance with
 * SkeletonUtils so each gets its own skeleton. Animation clips live in one
 * shared library (every humanoid is on the same rig) and are bound by bone
 * name. Props arrive as packs - one file, one texture atlas, each prop a
 * named root node - and are handed out as clones that share geometry and
 * material. */

export const CHARACTER_IDS = [
  'knight', 'barbarian', 'mage', 'rogue', 'rogue_hooded',
  'skeleton_minion', 'skeleton_warrior', 'skeleton_mage', 'skeleton_rogue',
] as const;
export type CharacterModel = (typeof CHARACTER_IDS)[number];

export const PROP_PACKS = ['hex_buildings', 'hex_nature', 'dungeon', 'halloween', 'adventure_items'] as const;
export type PropPack = (typeof PROP_PACKS)[number];

const BASE = `${import.meta.env.BASE_URL}assets/`;

class AssetStore {
  private loader = new GLTFLoader();
  private characters = new Map<string, GLTF>();
  private packs = new Map<string, Map<string, THREE.Object3D>>();
  clips = new Map<string, THREE.AnimationClip>();
  private loaded = false;

  constructor() {
    this.loader.setMeshoptDecoder(MeshoptDecoder);
  }

  async loadAll(onProgress?: (done: number, total: number) => void) {
    if (this.loaded) return;
    const jobs: Array<() => Promise<void>> = [];
    for (const id of CHARACTER_IDS) {
      jobs.push(async () => { this.characters.set(id, await this.loader.loadAsync(`${BASE}characters/${id}.glb`)); });
    }
    jobs.push(async () => {
      const g = await this.loader.loadAsync(`${BASE}anim/humanoid.glb`);
      for (const clip of g.animations) this.clips.set(clip.name, clip);
    });
    for (const p of PROP_PACKS) {
      jobs.push(async () => {
        const g = await this.loader.loadAsync(`${BASE}props/${p}.glb`);
        const map = new Map<string, THREE.Object3D>();
        for (const child of g.scene.children) {
          prepareStatic(child);
          map.set(child.name, child);
        }
        this.packs.set(p, map);
      });
    }
    let done = 0;
    onProgress?.(0, jobs.length);
    await Promise.all(jobs.map((j) => j().then(() => onProgress?.(++done, jobs.length))));
    for (const g of this.characters.values()) prepareCharacter(g.scene);
    // What every copy shares survives a zone being let go (see dispose.ts):
    // props share geometry and material; characters share geometry and the
    // texture atlas, but each copy has its own materials.
    for (const g of this.characters.values()) markShared(g.scene, false);
    for (const pack of this.packs.values()) for (const t of pack.values()) markShared(t, true);
    this.loaded = true;
  }

  /** A fresh, independently animatable copy of a character model. */
  character(id: CharacterModel): THREE.Group {
    const g = this.characters.get(id);
    if (!g) throw new Error(`character ${id} not loaded`);
    const clone = SkeletonUtils.clone(g.scene) as THREE.Group;
    // Materials are shared by default; characters are tinted individually, so
    // each clone owns its own.
    clone.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) m.material = (m.material as THREE.Material).clone();
    });
    return clone;
  }

  /** The raw template, for baking. Do not add it to a scene. */
  characterTemplate(id: CharacterModel): THREE.Group {
    const g = this.characters.get(id);
    if (!g) throw new Error(`character ${id} not loaded`);
    return g.scene;
  }

  clip(name: string): THREE.AnimationClip {
    const c = this.clips.get(name);
    if (!c) throw new Error(`clip ${name} missing`);
    return c;
  }

  hasProp(pack: PropPack, name: string) {
    return !!this.packs.get(pack)?.has(name);
  }

  /** A clone of a prop. Geometry and material are shared with the template. */
  prop(pack: PropPack, name: string): THREE.Object3D {
    const t = this.packs.get(pack)?.get(name);
    if (!t) throw new Error(`prop ${pack}/${name} missing`);
    return t.clone(true);
  }

  /** The prop's template, for instancing (geometry + material pairs). */
  propTemplate(pack: PropPack, name: string): THREE.Object3D {
    const t = this.packs.get(pack)?.get(name);
    if (!t) throw new Error(`prop ${pack}/${name} missing`);
    return t;
  }

  propNames(pack: PropPack): string[] {
    return [...(this.packs.get(pack)?.keys() ?? [])];
  }
}

/** Static props: shadows on, and the KayKit atlases read as slightly glossy
 *  plastic under strong light, so roughness goes up and metalness off. */
function prepareStatic(root: THREE.Object3D) {
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.castShadow = true;
    m.receiveShadow = true;
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    for (const mat of mats) {
      const s = mat as THREE.MeshStandardMaterial;
      if (s.isMeshStandardMaterial) {
        s.roughness = Math.max(s.roughness, 0.82);
        s.metalness = Math.min(s.metalness, 0.1);
        occludable(s);
        if (s.map) {
          s.map.colorSpace = THREE.SRGBColorSpace;
          s.map.anisotropy = 8;
          s.map = grimeTexture(s.map, WORLD_GRIME);
        }
        // Flat-coloured parts (no atlas) get the same wear.
        else if (s.color && !s.userData.grimed) { grimeColor(s.color, WORLD_GRIME); s.userData.grimed = true; }
      }
    }
  });
}

/** Props dither away where they stand between the camera and the survivor
 *  (walls, houses, a stack of crates), the way the trees do. */
function occludable(mat: THREE.MeshStandardMaterial) {
  if (mat.userData.occludable) return;
  mat.userData.occludable = true;
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uOccluder = floraUniforms.uOccluder;
    shader.uniforms.uOccView = floraUniforms.uOccView;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\n${OCCLUDE_VERT_PARS}`)
      .replace('#include <project_vertex>', `#include <project_vertex>\n${OCCLUDE_VERT}`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\n${OCCLUDE_PARS}`)
      .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>\n${OCCLUDE_FRAG}`);
  };
  mat.customProgramCacheKey = () => 'occludable-prop2';
}

function prepareCharacter(root: THREE.Object3D) {
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.castShadow = true;
    m.receiveShadow = true;
    m.frustumCulled = false; // skinned bounds do not follow the pose
    const s = m.material as THREE.MeshStandardMaterial;
    if (s.isMeshStandardMaterial) {
      s.roughness = Math.max(s.roughness, 0.7);
      s.metalness = Math.min(s.metalness, 0.2);
      if (s.map) { s.map.colorSpace = THREE.SRGBColorSpace; s.map = grimeTexture(s.map, PEOPLE_GRIME); }
    }
  });
}

export const Assets = new AssetStore();
