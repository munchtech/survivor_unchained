import * as THREE from 'three';
import { loadKtx2 } from './gltfShared';
import { keep } from './dispose';

/* The ground's materials: photoscanned sets from Poly Haven (CC0), gathered
 * by tools/assets/ground.py into three texture arrays, one layer each:
 *
 *   albedo  colour
 *   normal  OpenGL normals (green toward the image's top, which on the
 *           terrain, uv = world xz over the tile's size, is -z)
 *   arh     ambient occlusion, roughness, height (0..1 in every layer, so
 *           heights compare across layers when they blend)
 *
 * Loaded once, before any zone is built, and shared by every terrain and
 * the grass that grows from it. */

export const GROUND_LAYERS = ['grass', 'leaves', 'dirt', 'mud', 'stone', 'rock', 'blight'] as const;
export type GroundLayer = typeof GROUND_LAYERS[number];

export interface Ground {
  albedo: THREE.Texture;
  normal: THREE.Texture;
  arh: THREE.Texture;
  /** Each layer's tile, in metres, in GROUND_LAYERS order. */
  metres: number[];
}

const BASE = `${import.meta.env.BASE_URL}assets/ground/`;
let ground: Ground | null = null;

export async function preloadGround() {
  if (ground) return ground;
  const [albedo, normal, arh, meta] = await Promise.all([
    loadKtx2(`${BASE}albedo.ktx2`), loadKtx2(`${BASE}normal.ktx2`), loadKtx2(`${BASE}arh.ktx2`),
    fetch(`${BASE}ground.json`).then((r) => r.json() as Promise<{ layers: Array<{ name: string; metres: number }> }>),
  ]);
  const names = meta.layers.map((l) => l.name);
  if (names.join() !== GROUND_LAYERS.join()) throw new Error(`ground layers ${names} are not ${GROUND_LAYERS}`);
  for (const t of [albedo, normal, arh]) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.anisotropy = 8;
    keep(t);
  }
  ground = { albedo, normal, arh, metres: meta.layers.map((l) => l.metres) };
  return ground;
}

/** The ground (preloadGround first). */
export function groundTextures(): Ground {
  if (!ground) throw new Error('ground not preloaded');
  return ground;
}
