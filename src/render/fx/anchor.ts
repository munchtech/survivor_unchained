import * as THREE from 'three';
import { keep } from '../dispose';

/* Effects that make a material per use (a slash, a nova, a scorch) and let
 * it go when they fade share one shader program between them, and three
 * frees a program the moment the last material using it is disposed: the
 * next slash compiles it all over again, a stall in the middle of a fight.
 * An anchor is a hidden mesh with a material of the same shader that is
 * never disposed: it keeps the program alive for the session, and being in
 * the scene it is compiled with the zone, behind the fade
 * (WorldScene.warm). */

/** The attributes the effect's own meshes have matter: a shader is compiled
 *  per variant, and whether the geometry has normals (a plane does, a
 *  ribbon does not) is one. */
export const ANCHOR_BARE = keep(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 0, 0, 0, 0, 0, 0], 3)));
export const ANCHOR_PLANE = keep(new THREE.PlaneGeometry(0.001, 0.001));

/** A hidden mesh holding `make()`'s shader, made once per `key`, on the kind
 *  of geometry the effect draws with. */
const materials = new Map<string, THREE.Material>();
export function anchor(parent: THREE.Object3D, key: string, make: () => THREE.Material, geometry: THREE.BufferGeometry = ANCHOR_BARE) {
  let mat = materials.get(key);
  if (!mat) materials.set(key, mat = keep(make()));
  const m = new THREE.Mesh(geometry, mat);
  m.name = `anchor:${key}`;
  m.visible = false;
  m.frustumCulled = false;
  parent.add(m);
}
