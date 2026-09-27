import * as THREE from 'three';
import {
  pineGeometry, broadleafGeometry, deadTreeGeometry, bushGeometry, rockGeometry, floraMaterial,
} from './flora';

/* A field of generated vegetation and stone: a few variants of each kind,
 * each drawn as one InstancedMesh, placed by the zone builder. */

export type FloraKind =
  | 'pine' | 'broadleaf' | 'autumn' | 'sick' | 'dead' | 'bush' | 'bramble' | 'berry'
  | 'rock' | 'boulder' | 'pebble' | 'cliff';

interface KindSpec {
  variants: number;
  make: (seed: number) => THREE.BufferGeometry;
  wind: number;
  rim: number;
  flat?: boolean;
  shadow: boolean;
  occlude: boolean;
}

const KINDS: Record<FloraKind, KindSpec> = {
  pine: { variants: 5, make: (s) => pineGeometry(s, 9.5), wind: 0.25, rim: 0.35, shadow: true, occlude: true },
  broadleaf: { variants: 4, make: (s) => broadleafGeometry(s, 7.5, 'summer'), wind: 0.35, rim: 0.4, shadow: true, occlude: true },
  autumn: { variants: 3, make: (s) => broadleafGeometry(s + 50, 7, 'autumn'), wind: 0.35, rim: 0.4, shadow: true, occlude: true },
  sick: { variants: 3, make: (s) => broadleafGeometry(s + 90, 6.5, 'sick'), wind: 0.2, rim: 0.3, shadow: true, occlude: true },
  dead: { variants: 4, make: (s) => deadTreeGeometry(s, 7), wind: 0.08, rim: 0.2, shadow: true, occlude: true },
  bush: { variants: 4, make: (s) => bushGeometry(s, 1.3, 'green'), wind: 0.6, rim: 0.3, shadow: true, occlude: false },
  bramble: { variants: 3, make: (s) => bushGeometry(s + 30, 1.4, 'bramble'), wind: 0.3, rim: 0.2, shadow: true, occlude: false },
  berry: { variants: 2, make: (s) => bushGeometry(s + 60, 1.1, 'berry'), wind: 0.5, rim: 0.3, shadow: true, occlude: false },
  rock: { variants: 6, make: (s) => rockGeometry(s, 1.0), wind: 0, rim: 0.15, flat: true, shadow: true, occlude: false },
  boulder: { variants: 4, make: (s) => rockGeometry(s + 100, 2.6, { flat: 0.7 }), wind: 0, rim: 0.15, flat: true, shadow: true, occlude: true },
  pebble: { variants: 4, make: (s) => rockGeometry(s + 200, 0.35, { moss: 0.3 }), wind: 0, rim: 0.1, flat: true, shadow: false, occlude: false },
  cliff: { variants: 4, make: (s) => rockGeometry(s + 300, 6, { flat: 1.1, moss: 0.9 }), wind: 0, rim: 0.12, flat: true, shadow: true, occlude: true },
};

const geometryCache = new Map<string, THREE.BufferGeometry>();

export class FloraField {
  readonly group = new THREE.Group();
  private meshes = new Map<string, THREE.InstancedMesh>();
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private s = new THREE.Vector3();
  private p = new THREE.Vector3();
  private up = new THREE.Vector3(0, 1, 0);

  constructor(private capacity = 600) {
    this.group.name = 'flora';
  }

  private mesh(kind: FloraKind, variant: number) {
    const key = `${kind}:${variant}`;
    let im = this.meshes.get(key);
    if (!im) {
      const spec = KINDS[kind];
      let geo = geometryCache.get(key);
      if (!geo) {
        geo = spec.make(variant + 1);
        geometryCache.set(key, geo);
      }
      im = new THREE.InstancedMesh(geo, floraMaterial({ wind: spec.wind, rim: spec.rim, occlude: spec.occlude, flatShading: spec.flat }), this.capacity);
      im.count = 0;
      im.castShadow = spec.shadow;
      im.receiveShadow = true;
      im.name = key;
      this.meshes.set(key, im);
      this.group.add(im);
    }
    return im;
  }

  add(kind: FloraKind, x: number, y: number, z: number, rotY = 0, scale = 1, variant?: number, tilt = 0) {
    const spec = KINDS[kind];
    const v = variant ?? Math.floor(Math.abs(Math.sin(x * 12.9898 + z * 78.233) * 43758.5453) % 1 * spec.variants);
    const im = this.mesh(kind, v % spec.variants);
    if (im.count >= this.capacity) return;
    this.q.setFromAxisAngle(this.up, rotY);
    if (tilt) this.q.multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(tilt, 0, tilt * 0.6)));
    this.p.set(x, y, z);
    this.s.setScalar(scale);
    this.m.compose(this.p, this.q, this.s);
    im.setMatrixAt(im.count++, this.m);
    im.instanceMatrix.needsUpdate = true;
  }

  finalize() {
    for (const im of this.meshes.values()) {
      im.computeBoundingBox();
      im.computeBoundingSphere();
    }
  }
}
