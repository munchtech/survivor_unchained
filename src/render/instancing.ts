import * as THREE from 'three';

/* Many copies of one prop in one draw per part.
 *
 * A prop template is a small tree of meshes. Each mesh becomes an
 * InstancedMesh; the transform of the part relative to the prop root is baked
 * in, so placing instance i is one matrix for the whole prop. Optional wind:
 * vertices sway by their height above the prop's base, which is enough to
 * make a forest breathe without skinning a single branch. */

export interface InstanceOpts {
  wind?: number; // sway amplitude in metres at 1m of height
  castShadow?: boolean;
  receiveShadow?: boolean;
  tint?: THREE.Color;
}

const windUniforms = { uWindTime: { value: 0 } };
export function tickWind(t: number) { windUniforms.uWindTime.value = t; }

export class PropInstances {
  readonly group = new THREE.Group();
  private parts: Array<{ mesh: THREE.InstancedMesh; local: THREE.Matrix4 }> = [];
  private tmp = new THREE.Matrix4();
  count = 0;

  constructor(template: THREE.Object3D, readonly capacity: number, opts: InstanceOpts = {}) {
    template.updateMatrixWorld(true);
    const rootInv = template.matrixWorld.clone().invert();
    template.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      let material = m.material as THREE.Material;
      if (opts.wind || opts.tint) {
        material = material.clone();
        if (opts.tint) (material as THREE.MeshStandardMaterial).color?.multiply(opts.tint);
        if (opts.wind) addWind(material as THREE.MeshStandardMaterial, opts.wind);
      }
      const im = new THREE.InstancedMesh(m.geometry, material, capacity);
      im.castShadow = opts.castShadow ?? true;
      im.receiveShadow = opts.receiveShadow ?? true;
      im.count = 0;
      const local = rootInv.clone().multiply(m.matrixWorld);
      this.parts.push({ mesh: im, local });
      this.group.add(im);
    });
  }

  add(matrix: THREE.Matrix4) {
    if (this.count >= this.capacity) return -1;
    const i = this.count++;
    this.setMatrix(i, matrix);
    for (const p of this.parts) p.mesh.count = this.count;
    return i;
  }

  setMatrix(i: number, matrix: THREE.Matrix4) {
    for (const p of this.parts) {
      this.tmp.multiplyMatrices(matrix, p.local);
      p.mesh.setMatrixAt(i, this.tmp);
      p.mesh.instanceMatrix.needsUpdate = true;
    }
  }

  /** Recompute bounds after placement so frustum culling works per part. */
  finalize() {
    for (const p of this.parts) {
      p.mesh.computeBoundingSphere();
      p.mesh.computeBoundingBox();
    }
  }

  dispose() {
    for (const p of this.parts) p.mesh.dispose();
  }
}

function addWind(mat: THREE.MeshStandardMaterial, amount: number) {
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uWindTime = windUniforms.uWindTime;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uWindTime;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
#ifdef USE_INSTANCING
{
  vec3 ip = vec3(instanceMatrix[3][0], instanceMatrix[3][1], instanceMatrix[3][2]);
  float h = max(position.y, 0.0);
  float ph = uWindTime * 1.3 + ip.x * 0.21 + ip.z * 0.17;
  float sway = (sin(ph) * 0.6 + sin(ph * 2.7 + 1.3) * 0.25) * ${amount.toFixed(4)} * h * h * 0.12;
  transformed.x += sway;
  transformed.z += sway * 0.45;
}
#endif`);
  };
  mat.customProgramCacheKey = () => `wind-${amount}`;
}
