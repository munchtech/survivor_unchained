import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { envTemplate, type EnvKit } from '@/render/env';
import { Rng } from '@/core/rng';

/* Houses, put together from the Medieval Village kit (render/env.ts).
 *
 * The kit is modular on a 2 m grid: wall panels 2 m wide and a storey high
 * (timber-framed plaster, over a stone base on the ground floor, or rough
 * stone), each in
 * plain, door and window versions; corner posts; gabled round-tile roofs
 * sized to a footprint (4x4 m up to 8x14 m) with brick gable ends; doors,
 * windows and shutters to fill the openings; chimneys. A house is a
 * footprint (w across its front, d deep; both even, and a size the roofs
 * come in), a number of storeys, what each storey is made of, where its
 * door is, and a seed for where the windows fall.
 *
 * In a house's own frame its front faces +Z, centred on the origin. Pieces
 * are merged by material, so a house costs a handful of draw calls however
 * many panels it has. */

export type WallKind = 'plaster' | 'stone';
export type Side = 'front' | 'back' | 'left' | 'right';

export interface HouseSpec {
  /** Width along the front and depth, metres (even; see ROOFS). */
  w: number;
  d: number;
  /** What each storey is, ground first. */
  storeys: WallKind[];
  door?: { side: Side; at?: number; flat?: boolean };
  /** Chance a panel above the door's is a window (0..1). */
  windows?: number;
  shutters?: boolean;
  chimney?: boolean;
  /** A gabled roof (the default), or a tower's spire (4x4 only). */
  roof?: 'gable' | 'spire';
  seed?: number;
}

/** A house, and where its door is in its own frame. */
export interface House { root: THREE.Group; door: THREE.Vector3; w: number; d: number; height: number }

/** Storey height: panels stack at 3 m (their top trim overlaps the next). */
export const STOREY = 3;
export const ROOFS = ['4x4', '4x6', '4x8', '6x4', '6x6', '6x8', '6x10', '6x12', '6x14', '8x8', '8x10', '8x12', '8x14'];

/** Every piece a house can use (for preloading). */
export function housePieces(): Array<[EnvKit, string]> {
  const v = (n: string) => ['village', n] as [EnvKit, string];
  const out = [
    'Wall_Plaster_Straight', 'Wall_Plaster_Straight_Base', 'Wall_Plaster_Door_Round', 'Wall_Plaster_Door_Flat', 'Wall_Plaster_Window_Wide_Round', 'Wall_Plaster_Window_Thin_Round', 'Wall_Plaster_Window_Wide_Flat',
    'Wall_UnevenBrick_Straight', 'Wall_UnevenBrick_Door_Round', 'Wall_UnevenBrick_Door_Flat', 'Wall_UnevenBrick_Window_Wide_Round', 'Wall_UnevenBrick_Window_Thin_Round', 'Wall_UnevenBrick_Window_Wide_Flat',
    'Corner_Exterior_Wood', 'Corner_Exterior_Brick',
    'Door_1_Round', 'Door_1_Flat', 'DoorFrame_Round_WoodDark', 'DoorFrame_Flat_WoodDark',
    'Window_Wide_Round1', 'Window_Thin_Round1', 'Window_Wide_Flat1', 'WindowShutters_Wide_Round_Open', 'WindowShutters_Thin_Round_Open', 'WindowShutters_Wide_Flat_Open',
    'Roof_Front_Brick4', 'Roof_Front_Brick6', 'Roof_Front_Brick8', 'Prop_Chimney', 'Roof_Tower_RoundTiles',
    ...ROOFS.map((r) => `Roof_RoundTiles_${r}`),
  ];
  return out.map(v);
}

interface Placed { name: string; m: THREE.Matrix4 }

const UP = new THREE.Vector3(0, 1, 0);

/** Pieces put in place, merged by material when built: a house, a wall. */
export class Assembly {
  private placed: Placed[] = [];
  put(name: string, x: number, y: number, z: number, rot = 0) {
    this.placed.push({ name, m: new THREE.Matrix4().compose(new THREE.Vector3(x, y, z), new THREE.Quaternion().setFromAxisAngle(UP, rot), new THREE.Vector3(1, 1, 1)) });
  }
  build() { return merge(this.placed); }
}

/** A doorway panel, its frame, and the door hung from its left edge,
 *  closed across the opening (the panel's front facing `rot`). */
export function putDoor(asm: Assembly, wall: 'Plaster' | 'UnevenBrick', shape: 'Round' | 'Flat', x: number, y: number, z: number, rot: number) {
  asm.put(`Wall_${wall}_Door_${shape}`, x, y, z, rot);
  asm.put(`DoorFrame_${shape}_WoodDark`, x, y, z, rot);
  const hinge = new THREE.Vector3(-0.53, 0, 0).applyAxisAngle(UP, rot);
  asm.put(`Door_1_${shape}`, x + hinge.x, y, z + hinge.z, rot);
}

export function buildHouse(spec: HouseSpec): House {
  const rng = new Rng(spec.seed ?? 1);
  const { w, d } = spec;
  const roof = `${w}x${d}`;
  const spire = spec.roof === 'spire';
  if (!spire && !ROOFS.includes(roof)) throw new Error(`no roof for a ${roof} house`);
  const asm = new Assembly();
  const put = asm.put.bind(asm);
  // The four sides: where each panel stands and which way it faces.
  const sides: Record<Side, { n: number; at: (i: number) => [number, number]; rot: number }> = {
    front: { n: w / 2, at: (i) => [-w / 2 + 1 + i * 2, d / 2], rot: 0 },
    back: { n: w / 2, at: (i) => [w / 2 - 1 - i * 2, -d / 2], rot: Math.PI },
    right: { n: d / 2, at: (i) => [w / 2, d / 2 - 1 - i * 2], rot: Math.PI / 2 },
    left: { n: d / 2, at: (i) => [-w / 2, -d / 2 + 1 + i * 2], rot: -Math.PI / 2 },
  };
  const door = spec.door ?? { side: 'front' as Side };
  const doorAt = door.at ?? Math.floor((sides[door.side].n - 1) / 2);
  spec.storeys.forEach((kind, f) => {
    const y = f * STOREY;
    const mat = kind === 'stone' ? 'UnevenBrick' : 'Plaster';
    for (const [side, s] of Object.entries(sides) as Array<[Side, typeof sides.front]>) {
      for (let i = 0; i < s.n; i++) {
        const [x, z] = s.at(i);
        const isDoor = f === 0 && side === door.side && i === doorAt;
        // Windows: more on the front, fewer on the ground floor's sides.
        const chance = (spec.windows ?? 0.5) * (side === 'front' ? 1.2 : side === 'back' ? 0.6 : 0.8) * (f === 0 ? 0.7 : 1);
        const isWindow = !isDoor && rng.next() < chance;
        if (isDoor) {
          putDoor(asm, mat, door.flat ? 'Flat' : 'Round', x, y, z, s.rot);
          continue;
        }
        if (isWindow) {
          const shape = (['Wide_Round', 'Thin_Round', 'Wide_Flat'] as const)[Math.floor(rng.next() * 3)];
          put(`Wall_${mat}_Window_${shape}`, x, y, z, s.rot);
          put(`Window_${shape}1`, x, y, z, s.rot);
          // (Open shutters reach past the panel: not beside a corner.)
          if (spec.shutters && i > 0 && i < s.n - 1 && rng.next() < 0.6) put(`WindowShutters_${shape}_Open`, x, y, z, s.rot);
          continue;
        }
        put(kind === 'stone' ? 'Wall_UnevenBrick_Straight' : f === 0 ? 'Wall_Plaster_Straight_Base' : 'Wall_Plaster_Straight', x, y, z, s.rot);
      }
    }
    // Corner posts: timber on plaster, dressed stone on stone.
    const corner = kind === 'stone' ? 'Corner_Exterior_Brick' : 'Corner_Exterior_Wood';
    ([[w / 2, d / 2, 0], [-w / 2, d / 2, -Math.PI / 2], [-w / 2, -d / 2, Math.PI], [w / 2, -d / 2, Math.PI / 2]] as const).forEach(([x, z, r]) => put(corner, x, y, z, r));
  });
  // The roof, its ridge running front to back, gabled at both ends; or a
  // tower's spire.
  const top = spec.storeys.length * STOREY;
  if (spire) put('Roof_Tower_RoundTiles', 0, top, 0, 0);
  else {
    put(`Roof_RoundTiles_${roof}`, 0, top, 0, 0);
    if (w === 4 || w === 6 || w === 8) {
      put(`Roof_Front_Brick${w}`, 0, top, d / 2, 0);
      put(`Roof_Front_Brick${w}`, 0, top, -d / 2, Math.PI);
    }
  }
  if (spec.chimney && !spire) put('Prop_Chimney', w / 2 - 1.2, top + 0.4, -d / 4, 0);
  const s = sides[door.side];
  const [dx, dz] = s.at(doorAt);
  return { root: asm.build(), door: new THREE.Vector3(dx, 0, dz), w, d, height: top + (spire ? 6.8 : w * 0.6 + 1) };
}

/** One mesh per material: every piece's geometry, moved into place. */
function merge(placed: Placed[]) {
  const byMat = new Map<THREE.Material, THREE.BufferGeometry[]>();
  for (const p of placed) {
    const t = envTemplate('village', p.name);
    t.updateMatrixWorld(true);
    t.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      const g = mesh.geometry.clone();
      g.applyMatrix4(new THREE.Matrix4().multiplyMatrices(p.m, mesh.matrixWorld));
      // (Merging needs one attribute set: position, normal, uv, and colour
      // where any piece of this material has it.)
      const mat = mesh.material as THREE.Material;
      let list = byMat.get(mat);
      if (!list) { list = []; byMat.set(mat, list); }
      list.push(g);
    });
  }
  const group = new THREE.Group();
  // The pieces as placed (tools/godot/export_zone.mjs places them one by one).
  group.userData.pieces = placed.map((p) => ({ name: p.name, m: p.m.elements.slice() }));
  for (const [mat, geos] of byMat) {
    const keys = ['position', 'normal', 'uv'];
    const colored = geos.some((g) => g.getAttribute('color'));
    for (const g of geos) {
      for (const k of Object.keys(g.attributes)) if (!keys.includes(k) && !(colored && k === 'color')) g.deleteAttribute(k);
      if (colored && !g.getAttribute('color')) g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(g.getAttribute('position').count * 3).fill(1), 3));
      if (colored && g.getAttribute('color').itemSize === 4) {
        const c = g.getAttribute('color');
        const c3 = new Float32Array(c.count * 3);
        for (let i = 0; i < c.count; i++) { c3[i * 3] = c.getX(i); c3[i * 3 + 1] = c.getY(i); c3[i * 3 + 2] = c.getZ(i); }
        g.setAttribute('color', new THREE.BufferAttribute(c3, 3));
      }
      if (!g.index) g.setIndex([...Array(g.getAttribute('position').count).keys()]);
    }
    const merged = mergeGeometries(geos, false);
    if (!merged) continue;
    merged.computeBoundingSphere();
    const mesh = new THREE.Mesh(merged, mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.merged = true;
    group.add(mesh);
  }
  return group;
}

/** Pieces a stone town wall uses (for preloading). */
export const WALL_PIECES: Array<[EnvKit, string]> = [['village', 'Wall_UnevenBrick_Straight'], ['village', 'Corner_Exterior_Brick']];
