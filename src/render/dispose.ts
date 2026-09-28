import * as THREE from 'three';

/* Letting go of a zone.
 *
 * A zone build makes its own geometry, materials and canvas textures
 * (terrain, grass, water, awnings, straw, particles), and none of it is
 * garbage the GPU knows about: it stays uploaded until disposed. When a zone
 * is left, everything under its root is disposed, except what outlives every
 * zone: a template's geometry, materials and textures, which every copy of a
 * model shares, and what the caches hold. Those are kept (keep()), in a set
 * rather than a flag on the object, because a flag would be copied by
 * clone() and a zone's own copy of a template's mesh would never be let go.
 * Anything disposed that turns out to be used again is simply uploaded
 * again. */

const kept = new WeakSet<object>();

/** Outlives every zone: a template's, or a cache's (a clone of it is not). */
export function keep<T extends object>(x: T): T {
  kept.add(x);
  return x;
}

export function markShared(root: THREE.Object3D, materialsToo: boolean) {
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    keep(m.geometry);
    for (const mat of Array.isArray(m.material) ? m.material : [m.material]) {
      if (materialsToo) keep(mat);
      for (const t of texturesOf(mat)) keep(t);
    }
  });
}

const owned = new WeakMap<THREE.Material, THREE.Texture[]>();

/** Textures a material's shader reads through uniforms of its own
 *  (onBeforeCompile), where disposeTree cannot see them: they go with it. */
export function ownTextures(mat: THREE.Material, ...textures: THREE.Texture[]) {
  owned.set(mat, [...(owned.get(mat) ?? []), ...textures]);
}

function texturesOf(mat: THREE.Material): THREE.Texture[] {
  const out: THREE.Texture[] = [...(owned.get(mat) ?? [])];
  for (const v of Object.values(mat)) if (v && (v as THREE.Texture).isTexture) out.push(v as THREE.Texture);
  const u = (mat as THREE.ShaderMaterial).uniforms;
  if (u) for (const k of Object.keys(u)) { const v = u[k]?.value; if (v && (v as THREE.Texture).isTexture) out.push(v as THREE.Texture); }
  return out;
}

export function disposeTree(root: THREE.Object3D) {
  const geos = new Set<THREE.BufferGeometry>(), mats = new Set<THREE.Material>(), texs = new Set<THREE.Texture>();
  root.traverse((o) => {
    // An instanced mesh's own buffer (where its copies stand) goes with it.
    if ((o as THREE.InstancedMesh).isInstancedMesh) (o as THREE.InstancedMesh).dispose();
    const m = o as THREE.Mesh;
    if (!m.geometry && !m.material) return;
    if (m.geometry && !kept.has(m.geometry)) geos.add(m.geometry);
    const list = !m.material ? [] : Array.isArray(m.material) ? m.material : [m.material];
    for (const mat of list) {
      for (const t of texturesOf(mat)) if (!kept.has(t)) texs.add(t);
      if (!kept.has(mat)) mats.add(mat);
    }
  });
  for (const g of geos) g.dispose();
  for (const m of mats) m.dispose();
  for (const t of texs) t.dispose();
}
