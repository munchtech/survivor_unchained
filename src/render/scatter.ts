import * as THREE from 'three';
import {
  pineGeometry, broadleafGeometry, deadTreeGeometry, bushGeometry, rockGeometry, floraMaterial, floraShading, type FloraKitLook,
} from './flora';
import { envBounds, envLoaded, envTemplate, weatherOf } from './env';

/* A field of vegetation and stone, placed by the zone builder.
 *
 * Each kind is drawn from the Stylized Nature kit (Quaternius, CC0): its
 * pines, common, dead and twisted trees, bushes and rocks, each set scaled so
 * the kind stands as tall (or, for stone, as wide) as the zones were laid
 * out for, the foliage recoloured for autumn, blight or bramble and the
 * stone mossed on top. Kinds whose pieces are not loaded fall back to the
 * generated ones (render/flora.ts).
 *
 * Copies are drawn instanced, bucketed by where they stand: a forest is
 * thousands of trees of a few thousand triangles each, and a bucket off
 * screen (or out of the sun's shadow frustum) is skipped whole. */

export type FloraKind =
  | 'pine' | 'broadleaf' | 'autumn' | 'sick' | 'dead' | 'bush' | 'bramble' | 'berry'
  | 'rock' | 'boulder' | 'pebble' | 'cliff';

interface KitSet {
  pieces: string[];
  /** The set's mean height at scale 1 (trees), or its mean width (stone). */
  height?: number;
  width?: number;
  /** Flattened by this much (stone lies lower than the kit's). */
  squash?: number;
  /** The foliage recoloured: two colours, one chosen per copy. */
  leaves?: { a: string; b: string; amount: number };
  /** Moss on what faces up. */
  moss?: number;
}

interface KindSpec {
  variants: number;
  make: (seed: number) => THREE.BufferGeometry;
  wind: number;
  rim: number;
  flat?: boolean;
  shadow: boolean;
  occlude: boolean;
  kit?: KitSet;
}

const n = (base: string, ...ids: number[]) => ids.map((i) => `${base}_${i}`);

const KINDS: Record<FloraKind, KindSpec> = {
  pine: { variants: 5, make: (s) => pineGeometry(s, 9.5), wind: 0.25, rim: 0.35, shadow: true, occlude: true, kit: { pieces: n('Pine', 1, 2, 3, 4, 5), height: 9 } },
  broadleaf: { variants: 4, make: (s) => broadleafGeometry(s, 7.5, 'summer'), wind: 0.35, rim: 0.4, shadow: true, occlude: true, kit: { pieces: n('CommonTree', 1, 2, 3, 4, 5), height: 7.5 } },
  autumn: {
    variants: 3, make: (s) => broadleafGeometry(s + 50, 7, 'autumn'), wind: 0.35, rim: 0.4, shadow: true, occlude: true,
    kit: { pieces: n('CommonTree', 1, 2, 3, 4, 5), height: 7, leaves: { a: '#b4521c', b: '#c89a2c', amount: 0.85 } },
  },
  sick: {
    variants: 3, make: (s) => broadleafGeometry(s + 90, 6.5, 'sick'), wind: 0.2, rim: 0.3, shadow: true, occlude: true,
    kit: { pieces: n('TwistedTree', 1, 2, 3, 4, 5), height: 6.5, leaves: { a: '#8a8646', b: '#6a6a3a', amount: 0.75 } },
  },
  dead: { variants: 4, make: (s) => deadTreeGeometry(s, 7), wind: 0.08, rim: 0.2, shadow: true, occlude: true, kit: { pieces: n('DeadTree', 1, 2, 3, 4, 5), height: 8 } },
  bush: { variants: 4, make: (s) => bushGeometry(s, 1.3, 'green'), wind: 0.6, rim: 0.3, shadow: true, occlude: false, kit: { pieces: ['Bush_Common'], height: 1.4, leaves: { a: '#3c5a2a', b: '#52682e', amount: 0.9 } } },
  bramble: {
    variants: 3, make: (s) => bushGeometry(s + 30, 1.4, 'bramble'), wind: 0.3, rim: 0.2, shadow: true, occlude: false,
    kit: { pieces: ['Bush_Common'], height: 1.3, leaves: { a: '#4a4626', b: '#5a3c2a', amount: 0.65 } },
  },
  berry: { variants: 2, make: (s) => bushGeometry(s + 60, 1.1, 'berry'), wind: 0.5, rim: 0.3, shadow: true, occlude: false, kit: { pieces: ['Bush_Common_Flowers'], height: 1.2 } },
  rock: { variants: 6, make: (s) => rockGeometry(s, 1.0), wind: 0, rim: 0.15, flat: true, shadow: true, occlude: false, kit: { pieces: n('Rock_Medium', 1, 2, 3), width: 2, squash: 0.6, moss: 0.5 } },
  boulder: { variants: 4, make: (s) => rockGeometry(s + 100, 2.6, { flat: 0.7 }), wind: 0, rim: 0.15, flat: true, shadow: true, occlude: true, kit: { pieces: n('Rock_Medium', 1, 2, 3), width: 5.2, squash: 0.6, moss: 0.6 } },
  pebble: { variants: 4, make: (s) => rockGeometry(s + 200, 0.35, { moss: 0.3 }), wind: 0, rim: 0.1, flat: true, shadow: false, occlude: false, kit: { pieces: [...n('Pebble_Round', 1, 2, 3, 4, 5), ...n('Pebble_Square', 1, 2, 3)], width: 0.7, moss: 0.25 } },
  cliff: { variants: 4, make: (s) => rockGeometry(s + 300, 6, { flat: 1.1, moss: 0.9 }), wind: 0, rim: 0.12, flat: true, shadow: true, occlude: true, kit: { pieces: n('Rock_Medium', 1, 2, 3), width: 12, squash: 0.8, moss: 0.8 } },
};

/** The kit pieces the flora is drawn from (loaded at boot: world/zones/envUse.ts). */
export function floraPieces(): string[] {
  return [...new Set(Object.values(KINDS).flatMap((k) => k.kit?.pieces ?? []))];
}

interface Part { geo: THREE.BufferGeometry; mat: THREE.Material }

const geometryCache = new Map<string, THREE.BufferGeometry>();
const kitParts = new Map<string, Part[]>();
const kitMats = new Map<string, THREE.MeshStandardMaterial>();

// ?flora=gen: the generated kinds everywhere (for comparison).
const generatedOnly = typeof location !== 'undefined' && new URLSearchParams(location.search).get('flora') === 'gen';
const usesKit = (spec: KindSpec) => !generatedOnly && !!spec.kit && spec.kit.pieces.every((p) => envLoaded('nature', p));
const variantsOf = (spec: KindSpec) => (usesKit(spec) ? spec.kit!.pieces.length : spec.variants);

/** A kit piece as the kind draws it: its meshes baked to the kind's size,
 *  their materials shaded as flora. Shared by every field and zone. */
function kitPartsOf(kind: FloraKind, v: number): Part[] {
  const key = `${kind}:${v}`;
  let parts = kitParts.get(key);
  if (parts) return parts;
  const spec = KINDS[kind], set = spec.kit!;
  // One scale for the whole set, so its pieces keep their differences.
  const sizes = set.pieces.map((p) => {
    const b = envBounds('nature', p)!;
    return set.width ? Math.max(b.max.x - b.min.x, b.max.z - b.min.z) : b.max.y;
  });
  const mean = sizes.reduce((a, b) => a + b, 0) / sizes.length;
  const k = (set.width ?? set.height ?? mean) / mean;
  const t = envTemplate('nature', set.pieces[v]);
  t.updateMatrixWorld(true);
  parts = [];
  t.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const geo = m.geometry.clone();
    for (const a of Object.keys(geo.attributes)) if (a !== 'position' && a !== 'normal' && a !== 'uv' && a !== 'color') geo.deleteAttribute(a);
    geo.applyMatrix4(m.matrixWorld);
    geo.scale(k, k * (set.squash ?? 1), k);
    if (set.squash) geo.computeVertexNormals();
    geo.computeBoundingBox();
    geo.computeBoundingSphere();
    geo.userData.shared = true;
    parts!.push({ geo, mat: kitMaterial(kind, m.material as THREE.MeshStandardMaterial) });
  });
  kitParts.set(key, parts);
  return parts;
}

function kitMaterial(kind: FloraKind, src: THREE.MeshStandardMaterial) {
  const key = `${kind}|${src.uuid}`;
  let mat = kitMats.get(key);
  if (mat) return mat;
  const spec = KINDS[kind], set = spec.kit!;
  mat = src.clone();
  mat.userData = { shared: true };
  const [sat, tint] = weatherOf(src.name);
  const foliage = /Leaf|Leaves|Flower/i.test(src.name);
  const look: FloraKitLook = {
    sat, tint,
    recolor: foliage && set.leaves ? set.leaves : undefined,
    moss: set.moss,
    jitter: foliage ? 0.14 : 0.08,
  };
  floraShading(mat, { wind: spec.wind, rim: spec.rim, occlude: spec.occlude, kit: look });
  kitMats.set(key, mat);
  return mat;
}

/** Kinds that show on a map, as an ink mark. */
const MAPPED = new Set(['pine', 'broadleaf', 'autumn', 'sick', 'dead', 'boulder', 'cliff']);

/** Metres to a bucket's side. */
const CELL = 48;

export class FloraField {
  readonly group = new THREE.Group();
  /** Where the trees and big rocks stand: [kind, x, z, scale], for the map. */
  readonly marks: Array<[string, number, number, number]> = [];
  private buckets = new Map<string, { kind: FloraKind; v: number; at: THREE.Matrix4[] }>();
  private counts = new Map<string, number>();
  private materials = new Map<string, THREE.Material>();
  private q = new THREE.Quaternion();
  private s = new THREE.Vector3();
  private p = new THREE.Vector3();
  private up = new THREE.Vector3(0, 1, 0);

  /** capacity: most copies of any one kind and variant. */
  constructor(private capacity = 600) {
    this.group.name = 'flora';
  }

  add(kind: FloraKind, x: number, y: number, z: number, rotY = 0, scale = 1, variant?: number, tilt = 0) {
    const spec = KINDS[kind];
    const count = variantsOf(spec);
    const v = (variant ?? Math.floor(Math.abs(Math.sin(x * 12.9898 + z * 78.233) * 43758.5453) % 1 * count)) % count;
    const vk = `${kind}:${v}`;
    const had = this.counts.get(vk) ?? 0;
    if (had >= this.capacity) return;
    this.counts.set(vk, had + 1);
    if (MAPPED.has(kind)) this.marks.push([kind, x, z, scale]);
    this.q.setFromAxisAngle(this.up, rotY);
    if (tilt) this.q.multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(tilt, 0, tilt * 0.6)));
    this.p.set(x, y, z);
    this.s.setScalar(scale);
    const key = `${vk}|${Math.floor(x / CELL)},${Math.floor(z / CELL)}`;
    let b = this.buckets.get(key);
    if (!b) this.buckets.set(key, b = { kind, v, at: [] });
    b.at.push(new THREE.Matrix4().compose(this.p, this.q, this.s));
  }

  /** Build the meshes: once, after the last add(). */
  finalize() {
    for (const b of this.buckets.values()) {
      const spec = KINDS[b.kind];
      for (const part of this.partsOf(b.kind, b.v)) {
        const im = new THREE.InstancedMesh(part.geo, part.mat, b.at.length);
        b.at.forEach((m, i) => im.setMatrixAt(i, m));
        im.castShadow = spec.shadow;
        im.receiveShadow = true;
        im.name = `${b.kind}:${b.v}`;
        im.computeBoundingBox();
        im.computeBoundingSphere();
        this.group.add(im);
      }
    }
    this.buckets.clear();
  }

  private partsOf(kind: FloraKind, v: number): Part[] {
    const spec = KINDS[kind];
    if (usesKit(spec)) return kitPartsOf(kind, v);
    // Generated: one geometry per variant (kept between zones), one material
    // per kind and variant in this field (let go with the zone).
    const key = `${kind}:${v}`;
    let geo = geometryCache.get(key);
    if (!geo) geometryCache.set(key, geo = spec.make(v + 1));
    let mat = this.materials.get(key);
    if (!mat) this.materials.set(key, mat = floraMaterial({ wind: spec.wind, rim: spec.rim, occlude: spec.occlude, flatShading: spec.flat }));
    return [{ geo, mat }];
  }
}
