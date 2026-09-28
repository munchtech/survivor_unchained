import * as THREE from 'three';

/* Letting go of a zone.
 *
 * A zone build makes its own geometry, materials and canvas textures
 * (terrain, grass, water, awnings, straw, particles), and none of it is
 * garbage the GPU knows about: it stays uploaded until disposed. When a zone
 * is left, everything under its root is disposed, except what the asset
 * store shares between every copy of a model (marked `userData.shared`),
 * which the next zone will want again. Anything disposed that turns out to
 * be used again is simply uploaded again. */

export function markShared(root: THREE.Object3D, materialsToo: boolean) {
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.geometry.userData.shared = true;
    for (const mat of Array.isArray(m.material) ? m.material : [m.material]) {
      if (materialsToo) mat.userData.shared = true;
      for (const t of texturesOf(mat)) t.userData.shared = true;
    }
  });
}

function texturesOf(mat: THREE.Material): THREE.Texture[] {
  const out: THREE.Texture[] = [];
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
    if (m.geometry && !m.geometry.userData.shared) geos.add(m.geometry);
    const list = !m.material ? [] : Array.isArray(m.material) ? m.material : [m.material];
    for (const mat of list) {
      for (const t of texturesOf(mat)) if (!t.userData.shared) texs.add(t);
      if (!mat.userData.shared) mats.add(mat);
    }
  });
  for (const g of geos) g.dispose();
  for (const m of mats) m.dispose();
  for (const t of texs) t.dispose();
}
