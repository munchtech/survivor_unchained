import * as THREE from 'three';
import { PRESETS } from '@/render/atmosphere';
import { Terrain, type TerrainPaint } from '@/render/terrain';
import { Grass } from '@/render/grass';
import { createWater, waterUniforms } from '@/render/water';
import { CollisionWorld } from '@/sim/collision';
import { Noise2D, distToSegment, smoothstep, hash2, hash1 } from '@/core/math';
import type { ZoneBuild } from '@/game/scene';
import { ZoneKit } from './kit';
import { Assembly, buildHouse, STOREY, type HouseSpec, type WallKind } from './houses';

/* The Waystation: where the last three roads meet under Vonnra's toll.
 *
 * A walled market town. The south gate lets in the Low Ford road (where
 * the survivor arrives), the east gate lets out onto the Old Road and the
 * Thornhollow Verge, and the north gate is shut by a young knight who says
 * you are not ready. Inside, streets of worn cobble meet at a square with a
 * well. Every building someone lives or works in has a door the survivor
 * can use; everyone who matters stands near theirs.
 *
 * One place is not on anyone's map: behind the broken shrine, a gap in the
 * hedge opens onto the Quiet Garden. */

export const WAY = {
  square: { x: 0, z: 0 },
  south: { x: 0, z: 38 },
  east: { x: 40, z: 0 },
  north: { x: 0, z: -38 },
  inn: { x: -17, z: 11, rot: Math.PI / 2 },
  tavern: { x: -17, z: -11, rot: Math.PI / 2 },
  smithy: { x: 17, z: 12, rot: -Math.PI / 2 },
  trading: { x: 16, z: -12, rot: -Math.PI / 2 },
  warehouse: { x: 27, z: 25, rot: -Math.PI / 2 },
  shrine: { x: -26, z: -25, rot: Math.PI * 0.25 },
  wenna: { x: -28, z: 24, rot: Math.PI * 0.5 },
  barracks: { x: -9, z: -28, rot: 0 },
  toll: { x: 33, z: -8, rot: -Math.PI / 2 },
  garden: { x: -38, z: -36 },
  board: { x: 6, z: -5 },
};

export interface WaystationBuild {
  zone: ZoneBuild;
  kit: ZoneKit;
  /** Door positions, for interactions. */
  doors: Record<string, { x: number; z: number }>;
  /** After dark: braziers lit, doorways spilling light. */
  setNight: (on: boolean) => void;
  /** The market stalls: where they stand, which way the counter faces, what they sell. */
  stalls: Array<{ x: number; z: number; rot: number; kind: string }>;
}

export function buildWaystation(grassDensity = 1): WaystationBuild {
  const noise = new Noise2D(77);
  const W = WAY;
  // Streets: the three roads through the square, and lanes to each door.
  const streets: Array<[number, number, number, number, number]> = [
    [0, 80, 0, -80, 3.0], [0, 0, 80, 0, 2.8],
    [0, 8, -12, 11, 1.6], [0, -8, -12, -11, 1.6], [0, 9, 12, 12, 1.6], [0, -9, 11, -12, 1.6],
    [12, 12, 22, 24, 1.3], [-6, -16, -22, -22, 1.3], [-12, 11, -24, 24, 1.3], [0, -24, -9, -23, 1.3], [24, 0, 30, -7, 1.4],
    [-12, -11, -26, 0, 1.2], [12, -12, 22, -26, 1.2], [-6, 28, 6, 28, 1.1],
  ];
  const streetD = (x: number, z: number) => {
    let d = 1e9;
    for (const [x0, z0, x1, z1, w] of streets) d = Math.min(d, distToSegment(x, z, x0, z0, x1, z1) - w);
    return d;
  };
  const inside = (x: number, z: number) => Math.abs(x) < 39 && Math.abs(z) < 36;
  const stream = (x: number) => 52 + Math.sin(x * 0.05) * 4;

  const terrain = new Terrain({
    size: 180, resolution: 181,
    height: (x, z) => {
      let h = noise.fbm(x * 0.02, z * 0.02, 3) * 1.6;
      // The town sits on a levelled rise; the land falls away outside the walls.
      const out = Math.max(Math.abs(x) - 42, Math.abs(z) - 40, 0);
      h = inside(x, z) ? h * 0.25 : h + smoothstep(0, 30, out) * 3.5;
      h += smoothstep(66, 88, Math.max(Math.abs(x), Math.abs(z))) * 12;
      // A brook south of the walls, crossed by the Low Ford road.
      const sd = Math.abs(z - stream(x));
      h -= (1 - smoothstep(2, 6, sd)) * 1.6;
      return h;
    },
    paint: (x: number, z: number, o: TerrainPaint) => {
      const n = noise.noise(x * 0.35, z * 0.35);
      const sd = streetD(x, z);
      const inTown = inside(x, z);
      o.stone = inTown ? 1 - smoothstep(-0.4, 0.8, sd + n * 0.5) : 0;
      // The square.
      o.stone = Math.max(o.stone, 1 - smoothstep(10, 12, Math.hypot(x, z) + n));
      o.dirt = inTown ? (1 - smoothstep(0.6, 3, sd + n)) * 0.7 : 1 - smoothstep(1.5, 3.5, Math.min(Math.abs(x) - 0.5, Math.abs(z) - 0.5) + n);
      if (!inTown) o.dirt = Math.max(o.dirt, (1 - smoothstep(2.6, 4.2, Math.abs(x) + n)) * (z > 36 ? 1 : 0), (1 - smoothstep(2.6, 4.2, Math.abs(z) + n)) * (x > 39 ? 1 : 0));
      // Trodden earth in yards and around the buildings.
      o.dirt = Math.max(o.dirt, inTown ? (0.35 + n * 0.25) * (1 - smoothstep(4, 9, sd)) : 0);
      const sdist = Math.abs(z - stream(x));
      o.mud = 1 - smoothstep(1.5, 4.5, sdist + n);
      // The shrine's scorched yard.
      o.blight = (1 - smoothstep(3, 8, Math.hypot(x - W.shrine.x, z - W.shrine.z) + n * 2)) * 0.25;
    },
  });

  const col = new CollisionWorld(180);
  col.bound = 86;
  // A town at night is many small lights: a bigger pool than the wood.
  const kit = new ZoneKit(terrain, col, 9);
  const root = kit.root;
  root.add(terrain.mesh);
  const grass = new Grass(terrain, { density: grassDensity * 0.8 });
  root.add(grass.mesh);
  const water = createWater({ width: 180, depth: 12, color: '#3a5a60', murk: '#1a2a2c', flow: [0.4, 0], opacity: 0.8, sky: '#5a7080' });
  water.position.set(0, -0.95, 52);
  root.add(water);

  /** Footprints for the map. */
  const footprints: Array<{ x: number; z: number; r: number; rot: number }> = [];

  /* ------------------------------------------------------------- walls -- */
  // Rough stone two storeys high (the village kit's panels, houses.ts),
  // faced toward the town (the side the camera sees), with a dressed-stone
  // buttress every few panels. Gates are gaps on the roads between towers;
  // towers stand at the corners too.
  const X = 42, Z = 39;
  const GATE = 3, TOWER = 5; // half the opening; a gate tower's centre, from the gate
  const tower = (x: number, z: number, rot: number, seed: number) => {
    const t = buildHouse({ w: 4, d: 4, storeys: ['stone', 'stone', 'stone'], seed, roof: 'spire', windows: 0.35, chimney: false, door: { side: 'front' } });
    t.root.position.set(x, kit.y(x, z) - 0.3, z);
    t.root.rotation.y = rot;
    kit.root.add(t.root);
    col.addBox(x, z, 2.2, 2.2, -rot);
    footprints.push({ x, z, r: 2.6, rot });
  };
  const wallRun = (x0: number, z0: number, x1: number, z1: number, gate?: number) => {
    const len = Math.hypot(x1 - x0, z1 - z0);
    const ux = (x1 - x0) / len, uz = (z1 - z0) / len;
    const mx = (x0 + x1) / 2, mz = (z0 + z1) / 2;
    // Face the town (the origin): the normal on whichever side it lies.
    const side = uz * mx - ux * mz > 0 ? 1 : -1;
    const fx = -uz * side, fz = ux * side;
    const rot = Math.atan2(fx, fz);
    const baseY = kit.y(mx, mz) - 0.3;
    const asm = new Assembly();
    const n = Math.round(len / 2);
    let runStart = -1;
    const closeRun = (to: number) => {
      if (runStart < 0) return;
      // One collider per unbroken stretch of wall.
      const a = runStart * 2, b = to * 2, c = (a + b) / 2 - len / 2;
      col.addBox(mx + ux * c - fx * 0.2, mz + uz * c - fz * 0.2, (b - a) / 2, 0.45, -Math.atan2(-uz, ux));
      runStart = -1;
    };
    for (let i = 0; i < n; i++) {
      const s = (i + 0.5) * 2 - len / 2; // along the run, from its middle
      if (gate !== undefined && Math.abs(s - gate) < TOWER + 2) { closeRun(i); continue; }
      if (runStart < 0) runStart = i;
      const x = mx + ux * s, z = mz + uz * s;
      const y = kit.y(x, z) - 0.3 - baseY;
      // A panel is dressed on one face only: a second, back to back and
      // overlapping it, faces the country (the plaster of both inside).
      for (let f = 0; f < 2; f++) {
        asm.put('Wall_UnevenBrick_Straight', x - mx, y + f * STOREY, z - mz, rot);
        asm.put('Wall_UnevenBrick_Straight', x - mx - fx * 0.45, y + f * STOREY, z - mz - fz * 0.45, rot + Math.PI);
      }
      // A buttress at every fourth joint, on the town side.
      if (i % 4 === 0) for (let f = 0; f < 2; f++) asm.put('Corner_Exterior_Brick', x - mx - ux, y + f * STOREY, z - mz - uz, rot);
    }
    closeRun(n);
    const g = asm.build();
    g.position.set(mx, baseY, mz);
    kit.root.add(g);
    if (gate !== undefined) {
      for (const k of [-1, 1]) tower(mx + ux * (gate + k * TOWER), mz + uz * (gate + k * TOWER), rot, 40 + k + Math.round(mx + mz));
      // A torch on each tower's town-facing wall, on the side nearer the
      // opening (its bracket reaches half a metre out from the stone).
      for (const k of [-1, 1]) {
        const a = gate + k * (GATE + 1);
        const tx = mx + ux * a + fx * 2.05, tz = mz + uz * a + fz * 2.05;
        const ty = kit.y(tx, tz) + 3.3;
        kit.env('props', 'Torch_Metal', tx, tz, { rot, y: ty, scale: 1.4 });
        const glow = kit.flameGlow(tx + fx * 0.5, ty + 0.55, tz + fz * 0.5, 0.14);
        kit.source(tx + fx * 0.8, ty + 1.0, tz + fz * 0.8, 0xffa050, 10, 14, 0.2, [glow]);
      }
    }
  };
  // Gates sit on the roads: south and north at x = 0, east at z = 0.
  wallRun(-X, Z, X, Z, 0); // south: the Low Ford road
  wallRun(X, -Z, -X, -Z, 0); // north, shut
  wallRun(-X, -Z, -X, Z); // west
  wallRun(X, Z, X, -Z, 0); // east: the Old Road
  for (const [x, z] of [[-X, -Z], [X, -Z], [-X, Z], [X, Z]] as const) tower(x, z, Math.atan2(-x, -z), Math.round(x * 3 + z));

  /* --------------------------------------------------------- buildings -- */
  const doors: Record<string, { x: number; z: number }> = {};
  /** A house of the village kit (houses.ts), its front facing local +z. */
  const building = (key: string, spec: HouseSpec, p: { x: number; z: number; rot: number }) => {
    const h = buildHouse(spec);
    // Stand it on the lowest ground under its corners (the stone base hides
    // the rest), so no corner floats.
    const c = Math.cos(p.rot), sn = Math.sin(p.rot);
    let y = Infinity;
    for (const [lx, lz] of [[-1, -1], [1, -1], [1, 1], [-1, 1], [0, 0]]) {
      const ox = (lx * h.w) / 2, oz = (lz * h.d) / 2;
      y = Math.min(y, kit.y(p.x + ox * c + oz * sn, p.z - ox * sn + oz * c));
    }
    h.root.position.set(p.x, y - 0.05, p.z);
    h.root.rotation.y = p.rot;
    kit.root.add(h.root);
    col.addBox(p.x, p.z, h.w / 2 + 0.15, h.d / 2 + 0.15, -p.rot);
    footprints.push({ x: p.x, z: p.z, r: Math.max(h.w, h.d) * 0.55, rot: p.rot });
    // The door, and a step out from it.
    const door = h.door.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), p.rot);
    const dx = Math.sin(p.rot), dz = Math.cos(p.rot);
    const doorOut = 0.7;
    doors[key] = { x: p.x + door.x + dx * doorOut, z: p.z + door.z + dz * doorOut };
    // A lantern on a bracket beside every door: after dark, the town is
    // where the light is. (Its bracket reaches 1.25 m out from the wall.)
    const side = new THREE.Vector3(1.15, 0, 0).applyAxisAngle(new THREE.Vector3(0, 1, 0), p.rot);
    const wx = p.x + door.x + dx * 0.1 + side.x, wz = p.z + door.z + dz * 0.1 + side.z;
    kit.env('props', 'Lantern_Wall', wx, wz, { rot: p.rot, y: y + 1.3 });
    const lx = wx + dx * 1.05, lz = wz + dz * 1.05;
    const glow = kit.flameGlow(lx, y + 2.05, lz, 0.05, '#ffd08a');
    const lsrc = kit.source(lx, y + 2.1, lz, 0xffb468, 4.5, 8, 0.08, [glow]);
    kit.moths(lsrc);
    // After dark the doorway spills light onto the step, and the chimney smokes.
    kit.spill(p.x + door.x + dx * 0.8, p.z + door.z + dz * 0.8, 3.0, '#ffae62', 0.3);
    if (spec.chimney) {
      const ch = new THREE.Vector3(h.w / 2 - 1.2, 0, -h.d / 4).applyAxisAngle(new THREE.Vector3(0, 1, 0), p.rot);
      kit.chimney(p.x + ch.x, y + spec.storeys.length * STOREY + 3.4, p.z + ch.z);
    }
    return doors[key];
  };
  const house = (w: number, d: number, storeys: WallKind[], seed: number, o: Partial<HouseSpec> = {}): HouseSpec => ({ w, d, storeys, seed, windows: 0.55, shutters: true, chimney: true, ...o });
  building('inn', house(6, 10, ['stone', 'plaster', 'plaster'], 11, { windows: 0.75 }), W.inn);
  building('tavern', house(8, 8, ['stone', 'plaster'], 12, { windows: 0.6 }), W.tavern);
  building('smithy', house(6, 8, ['stone'], 13, { windows: 0.3, shutters: false, door: { side: 'front', flat: true } }), W.smithy);
  building('trading', house(8, 10, ['stone', 'plaster'], 14, { windows: 0.65 }), W.trading);
  building('warehouse', house(8, 12, ['stone', 'stone'], 15, { windows: 0.15, shutters: false, chimney: false, door: { side: 'front', flat: true } }), W.warehouse);
  building('shrine', house(6, 6, ['stone', 'stone'], 16, { windows: 0.45, shutters: false, chimney: false }), W.shrine);
  building('wenna', house(4, 6, ['plaster'], 17, { windows: 0.5 }), W.wenna);
  building('barracks', house(8, 12, ['stone', 'stone'], 18, { windows: 0.4, shutters: false }), W.barracks);
  building('toll', house(4, 4, ['stone', 'stone', 'plaster'], 19, { roof: 'spire', chimney: false, windows: 0.5, shutters: false }), W.toll);
  // The shrine's bell tower, beside it.
  {
    const t = buildHouse(house(4, 4, ['stone', 'stone', 'stone'], 20, { roof: 'spire', chimney: false, windows: 0.35, shutters: false, door: { side: 'back' } }));
    const off = new THREE.Vector3(-3.2, 0, -5.4).applyAxisAngle(new THREE.Vector3(0, 1, 0), W.shrine.rot);
    const tx = W.shrine.x + off.x, tz = W.shrine.z + off.z;
    t.root.position.set(tx, kit.y(tx, tz) - 0.05, tz);
    t.root.rotation.y = W.shrine.rot;
    kit.root.add(t.root);
    col.addBox(tx, tz, 2.15, 2.15, -W.shrine.rot);
    footprints.push({ x: tx, z: tz, r: 2.4, rot: W.shrine.rot });
  }
  const homes: Array<[number, number, number, number, number, number]> = [
    // x, z, facing, width, depth, storeys
    [25, -30, 0, 6, 6, 2], [16, -30, 0.2, 4, 6, 1], [-31, 5, Math.PI / 2, 6, 8, 2],
    [-32, -8, Math.PI / 2, 4, 6, 1], [9, 30, Math.PI, 6, 6, 2], [-9, 30, Math.PI, 4, 6, 1],
    [31, 10, -Math.PI / 2, 6, 8, 2], [-20, 31, Math.PI, 4, 6, 2], [19, 31, Math.PI, 6, 6, 1],
    [-31, 15, Math.PI / 2, 4, 6, 1], [32, -20, -Math.PI / 2, 6, 6, 2], [-2, -31, 0, 6, 8, 2],
  ];
  homes.forEach(([x, z, rot, w, d, n], i) => building(`home${i}`, house(w, d, n === 1 ? [i % 3 ? 'plaster' : 'stone'] : ['stone', 'plaster'], 30 + i), { x, z, rot }));
  // Yards: low fences and a little clutter behind the houses.
  homes.forEach(([x, z, rot, , d], i) => {
    const bx = x - Math.sin(rot) * (d / 2 + 1.4), bz = z - Math.cos(rot) * (d / 2 + 1.4);
    for (let k = -1; k <= 1; k++) {
      const fx = bx + Math.cos(rot) * k * 2.05, fz = bz - Math.sin(rot) * k * 2.05;
      kit.env('village', k ? 'Prop_WoodenFence_Extension1' : 'Prop_WoodenFence_Single', fx, fz, { rot, y: kit.y(fx, fz) });
    }
    const junk = ['Barrel', 'Crate_Wooden', 'Bag', 'Bucket_Wooden_1', 'Barrel_Holder', 'FarmCrate_Empty'][i % 6];
    kit.env('props', junk, bx + Math.cos(rot) * 1.5, bz - Math.sin(rot) * 1.5 + 0.8, { rot: i, scale: junk === 'Crate_Wooden' ? 0.8 : 1, r: 0.45 });
  });
  // Outside the walls: a windmill and fields, for the skyline.
  kit.prop('hex_buildings', 'building_windmill_blue', -58, 50, { rot: 0.4, scale: 8, clay: true });
  kit.prop('hex_buildings', 'building_watermill_blue', 24, 50, { rot: Math.PI, scale: 7, clay: true });
  kit.prop('hex_buildings', 'building_grain', -30, 52, { rot: 0.2, scale: 8 });
  kit.prop('hex_buildings', 'building_grain', -42, 60, { rot: -0.3, scale: 8 });
  footprints.push({ x: -58, z: 50, r: 5, rot: 0.4 }, { x: 24, z: 50, r: 4.5, rot: Math.PI }, { x: -30, z: 52, r: 3.5, rot: 0.2 }, { x: -42, z: 60, r: 3.5, rot: -0.3 });

  /* ------------------------------------------------------------ square -- */
  kit.prop('hex_buildings', 'building_well_blue', 0, 0, { scale: 5, r: 2, clay: true });
  // The notice board: posts and a plank with papers pinned to it.
  {
    const b = new THREE.Group();
    const wood = new THREE.MeshStandardMaterial({ color: '#5a4030', roughness: 0.9 });
    for (const sx of [-1.1, 1.1]) {
      const post = new THREE.Mesh(new THREE.BoxGeometry(0.16, 2.4, 0.16), wood);
      post.position.set(sx, 1.2, 0);
      b.add(post);
    }
    const board = new THREE.Mesh(new THREE.BoxGeometry(2.6, 1.4, 0.1), new THREE.MeshStandardMaterial({ color: '#6a4c34', roughness: 0.95 }));
    board.position.set(0, 1.55, 0);
    b.add(board);
    const roof = new THREE.Mesh(new THREE.BoxGeometry(2.9, 0.1, 0.5), wood);
    roof.position.set(0, 2.35, 0.1);
    roof.rotation.x = 0.25;
    b.add(roof);
    const paperMat = [new THREE.MeshStandardMaterial({ color: '#e8dcc0', roughness: 1 }), new THREE.MeshStandardMaterial({ color: '#d8c8a0', roughness: 1 })];
    for (let i = 0; i < 6; i++) {
      const p = new THREE.Mesh(new THREE.PlaneGeometry(0.42 + hash1(i, 1) * 0.2, 0.5 + hash1(i, 2) * 0.2), paperMat[i % 2]);
      p.position.set(-0.95 + (i % 4) * 0.62 + hash1(i, 3) * 0.1, 1.3 + Math.floor(i / 4) * 0.55 + hash1(i, 4) * 0.08, 0.06);
      p.rotation.z = (hash1(i, 5) - 0.5) * 0.2;
      b.add(p);
    }
    b.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = o.receiveShadow = true; });
    b.position.set(W.board.x, kit.y(W.board.x, W.board.z), W.board.z);
    b.rotation.y = -0.6;
    root.add(b);
    col.addBox(W.board.x, W.board.z, 1.3, 0.3, 0.6);
  }
  // Market stalls round the square: four posts, a striped awning, a
  // counter with whatever is for sale today.
  const stalls: Array<[number, number, number, string, string]> = [[-8, 7, 0.4, '#8a2a24', 'produce'], [8, 8, -0.3, '#2a4a6a', 'cloth'], [-9, -7, 2.6, '#3a5a2a', 'herbs'], [10, -6, 3.5, '#8a6a2a', 'pots']];
  const postM = new THREE.MeshStandardMaterial({ color: '#4a3424', roughness: 0.9 });
  const counterM = new THREE.MeshStandardMaterial({ color: '#6a4a32', roughness: 0.85 });
  const awningTex = (stripe: string) => {
    const c = document.createElement('canvas');
    c.width = 64; c.height = 8;
    const g2 = c.getContext('2d')!;
    for (let i = 0; i < 8; i++) { g2.fillStyle = i % 2 ? '#d8ccb0' : stripe; g2.fillRect(i * 8, 0, 8, 8); }
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.magFilter = THREE.NearestFilter;
    return t;
  };
  for (const [x, z, rot, stripe, kind] of stalls) {
    const st = new THREE.Group();
    for (const [px, pz] of [[-1.3, -0.8], [1.3, -0.8], [-1.3, 0.9], [1.3, 0.9]]) {
      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, pz < 0 ? 2.5 : 2.1, 6), postM);
      post.position.set(px, (pz < 0 ? 2.5 : 2.1) / 2, pz);
      st.add(post);
    }
    const aw = new THREE.Mesh(new THREE.PlaneGeometry(3.1, 2.1, 6, 1), new THREE.MeshStandardMaterial({ map: awningTex(stripe), roughness: 0.95, side: THREE.DoubleSide }));
    // Sagging a little between the posts.
    const pa = aw.geometry.attributes.position;
    for (let i = 0; i < pa.count; i++) pa.setZ(i, -Math.sin((pa.getX(i) / 3.1 + 0.5) * Math.PI) * 0.12);
    aw.geometry.computeVertexNormals();
    aw.rotation.x = -Math.PI / 2 + 0.2;
    aw.position.set(0, 2.32, 0.05);
    st.add(aw);
    // A scalloped valance along the front.
    for (let i = 0; i < 7; i++) {
      const v = new THREE.Mesh(new THREE.CircleGeometry(0.22, 8, 0, Math.PI), new THREE.MeshStandardMaterial({ color: i % 2 ? '#d8ccb0' : stripe, roughness: 0.95, side: THREE.DoubleSide }));
      v.rotation.z = Math.PI;
      v.position.set(-1.32 + i * 0.44, 2.1, 1.07);
      st.add(v);
    }
    const counter = new THREE.Mesh(new THREE.BoxGeometry(2.7, 0.9, 0.7), counterM);
    counter.position.set(0, 0.45, 0.75);
    st.add(counter);
    // What is for sale, in crates and pots along the counter.
    const wares: Record<string, string[]> = {
      produce: ['FarmCrate_Apple', 'FarmCrate_Carrot', 'FarmCrate_Apple'], cloth: ['Bag', 'Rope_1', 'Bag'],
      herbs: ['Pot_1', 'Vase_2', 'Pot_1'], pots: ['Vase_4', 'Pot_1', 'Vase_2'],
    };
    st.traverse((o) => { if ((o as THREE.Mesh).isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    st.position.set(x, kit.y(x, z), z);
    st.rotation.y = rot;
    root.add(st);
    const c = Math.cos(rot), sn = Math.sin(rot);
    wares[kind].forEach((w, i) => {
      const lx = -0.85 + i * 0.85, lz = 0.75;
      kit.env('props', w, x + lx * c + lz * sn, z - lx * sn + lz * c, { rot: rot + (i - 1) * 0.2, y: kit.y(x, z) + 0.9, scale: w === 'Bag' ? 0.6 : 1 });
    });
    col.addBox(x, z, 1.5, 1.2, -rot);
    // Stock behind the counter, either side of the keeper (inside the
    // stall's own footprint: the square's lanes run close by).
    const back = (lx: number, lz: number): [number, number] => [x + lx * c + lz * sn, z - lx * sn + lz * c];
    kit.env('props', 'Crate_Wooden', ...back(0.9, -0.45), { rot: rot + 0.15, scale: 0.6 });
    kit.env('props', hash1(x, 3) > 0.5 ? 'Barrel_Apples' : 'Bag', ...back(-0.9, -0.45), { rot });
  }
  // Benches, barrels and life.
  kit.env('props', 'Bench', W.tavern.x + 5.5, W.tavern.z + 3.2, { rot: Math.PI / 2, scale: 0.8, box: [1.1, 0.3] });
  kit.env('props', 'Bench', -4, 6, { rot: 0.3, scale: 0.8, box: [1.1, 0.3] });
  kit.env('props', 'Barrel', W.inn.x + 4, W.inn.z - 4.5, { rot: 0.4, r: 0.4 });
  kit.env('props', 'Barrel', W.inn.x + 4.6, W.inn.z - 5.2, { rot: 1.4, r: 0.4 });
  kit.env('props', 'Barrel_Holder', W.tavern.x + 3.5, W.tavern.z - 4.5, { rot: 0.2, box: [0.7, 0.4] });
  kit.env('props', 'Crate_Wooden', W.warehouse.x - 6, W.warehouse.z - 2, { rot: 0.3, r: 0.8 });
  kit.env('props', 'Crate_Wooden', W.warehouse.x - 6, W.warehouse.z - 2, { rot: 0.9, scale: 0.8, y: kit.y(W.warehouse.x - 6, W.warehouse.z - 2) + 1.1 });
  kit.env('props', 'Crate_Wooden', W.warehouse.x - 7.2, W.warehouse.z - 1.1, { rot: -0.2, scale: 0.85, r: 0.6 });
  kit.env('props', 'Crate_Wooden', W.warehouse.x + 5, W.warehouse.z - 4, { rot: -0.5, scale: 0.9, r: 0.7 });
  // The trader's wagon, unhitched along the post's south wall.
  kit.env('village', 'Prop_Wagon', W.trading.x + 0.5, W.trading.z - 5.6, { rot: Math.PI / 2 + 0.08, box: [1.0, 2.0] });
  kit.env('props', 'Crate_Wooden', W.trading.x - 5.6, W.trading.z - 3, { rot: 0.2, scale: 0.85, r: 0.7 });
  kit.env('props', 'WeaponStand', W.barracks.x + 5, W.barracks.z + 4, { rot: 0.5, box: [0.7, 0.5] });
  kit.env('props', 'Dummy', W.barracks.x - 5, W.barracks.z + 5, { rot: -0.3, r: 0.45 });
  kit.env('props', 'Dummy', W.barracks.x - 6.6, W.barracks.z + 4.4, { rot: 0.4, r: 0.45 });
  kit.env('props', 'Barrel', W.barracks.x + 6.4, W.barracks.z + 3, { r: 0.4 });

  // The smithy's forge, anvil and bench.
  const smithFire = kit.campfire(W.smithy.x - 4.2, W.smithy.z - 3.2, 0.7);
  void smithFire;
  kit.env('props', 'Anvil_Log', W.smithy.x - 5.2, W.smithy.z + 1.2, { rot: Math.PI / 2, r: 0.5 });
  kit.env('props', 'Workbench', W.smithy.x - 4.4, W.smithy.z + 4.2, { rot: -Math.PI / 2, box: [1.0, 0.5] });
  kit.env('props', 'Bucket_Metal', W.smithy.x - 5.9, W.smithy.z + 2.2, {});
  kit.env('props', 'Chain_Coil', W.smithy.x - 3.6, W.smithy.z + 2.4, { rot: 0.7 });

  // The broken shrine: a cracked altar and cold candles.
  kit.prop('halloween', 'shrine', W.shrine.x + 4.4, W.shrine.z + 4.6, { rot: -Math.PI * 0.75, scale: 0.9, r: 0.6 });
  kit.env('props', 'Candle_1', W.shrine.x + 5.2, W.shrine.z + 3.8, {});
  kit.env('props', 'Candle_2', W.shrine.x + 3.6, W.shrine.z + 5.4, {});
  kit.env('props', 'Vase_Rubble_Medium', W.shrine.x - 4, W.shrine.z + 4, { rot: 2 });
  kit.env('village', 'Prop_Brick2', W.shrine.x - 3.2, W.shrine.z + 4.6, { rot: 0.6 });
  kit.env('village', 'Prop_Brick3', W.shrine.x - 4.6, W.shrine.z + 3.2, { rot: 1.9 });

  // Wenna's garden.
  for (let i = 0; i < 14; i++) {
    const x = W.wenna.x + 4 + (i % 4) * 1.3, z = W.wenna.z - 4 + Math.floor(i / 4) * 1.4;
    kit.flora.add(i % 3 ? 'bush' : 'berry', x, kit.y(x, z), z, i, 0.45);
  }
  kit.env('props', 'Bucket_Wooden_1', W.wenna.x + 3, W.wenna.z + 3, {});

  /* ------------------------------------------------------ Quiet Garden -- */
  // Hedges close the corner behind the shrine; one gap, hard to see.
  const G = W.garden;
  for (let i = 0; i < 12; i++) {
    const t = i / 11;
    const x = G.x + 11 * t, z = G.z + 9 - 1.5 * t;
    if (i === 7) continue; // the gap
    kit.flora.add('bush', x, kit.y(x, z), z, i * 1.7, 1.3);
    col.addCircle(x, z, 0.9, { soft: true });
  }
  for (let i = 0; i < 5; i++) {
    const x = G.x + 11, z = G.z + 7.5 - i * 1.8;
    kit.flora.add('bush', x, kit.y(x, z), z, i * 2.3, 1.3);
    col.addCircle(x, z, 0.9, { soft: true });
  }
  kit.prop('halloween', 'grave_B', G.x + 4, G.z + 2, { rot: Math.PI / 4, scale: 0.7, r: 0.5 });
  kit.prop('halloween', 'lantern_standing', G.x + 6, G.z + 3.5, { scale: 0.7 });
  const gGlow = kit.flameGlow(G.x + 6, kit.y(G.x + 6, G.z + 3.5) + 0.45, G.z + 3.5, 0.06, '#ffe8b0');
  kit.source(G.x + 6, kit.y(G.x, G.z) + 1, G.z + 3.5, 0xffe0a0, 5, 8, 0.1, [gGlow]);
  kit.env('props', 'Chest_Wood', G.x + 2.5, G.z + 4.5, { rot: 0.7, r: 0.6, tag: 'garden_chest' });
  for (let i = 0; i < 9; i++) kit.flora.add('berry', G.x + 1 + hash1(i, 1) * 8, kit.y(G.x, G.z), G.z + 1 + hash1(i, 2) * 5, i, 0.4);

  /* ------------------------------------------------------ lamps, trees -- */
  const lamps: Array<[number, number, number]> = [[-4, 12, 0], [5, -12, Math.PI], [12, 4, -Math.PI / 2], [-12, -3, Math.PI / 2], [-4, 24, 0], [24, 3.8, 0], [-4, -20, Math.PI], [4, 33, Math.PI]];
  for (const [x, z, r] of lamps) {
    const { src } = kit.lamp(x, z, r, true, 0.85);
    kit.moths(src);
    kit.spill(src.x, src.z, 2.8, '#ffb070', 0.22);
  }
  // Braziers in the square, lit at dusk by the Watch.
  const braziers = [kit.brazier(5.4, 1.4, false), kit.brazier(-5.4, -1.8, false), kit.brazier(-2.2, 30.5, false), kit.brazier(2.2, 30.5, false)];
  for (const b of braziers) kit.spill(b.x, b.z, 3.6, '#ff9a50', 0.26);
  for (let i = 0; i < 160; i++) {
    const a = hash1(i, 11) * Math.PI * 2, d = 52 + hash1(i, 12) * 34;
    const x = Math.cos(a) * d * 1.05, z = Math.sin(a) * d;
    if (Math.abs(x) < 7 && z > 32) continue; // keep the roads clear
    if (Math.abs(z) < 7 && x > 36) continue;
    if (Math.abs(x) < 7 && z < -32) continue;
    if (Math.abs(z - stream(x)) < 5) continue;
    const h = hash1(i, 13);
    flora(kit, h < 0.6 ? 'pine' : h < 0.8 ? 'broadleaf' : 'autumn', x, z, h * 7, 0.9 + hash1(i, 14) * 0.5);
  }
  // A few trees inside the walls.
  for (const [x, z] of [[-24, 10], [24, -20], [-14, 22], [34, 30], [-36, -20], [-6, -12], [30, -30]] as const) flora(kit, 'broadleaf', x, z, x, 0.7);
  for (const [x, z] of [[-34, 30], [36, 26], [-36, -2], [14, -24]] as const) flora(kit, 'autumn', x, z, x, 0.6);
  kit.flora.finalize();
  root.add(kit.flora.group);

  const zone: ZoneBuild = {
    id: 'waystation', terrain, grass, collision: col, root, atmosphere: PRESETS.day,
    map: { flora: kit.flora.marks, extent: 120, buildings: footprints },
    start: { x: W.south.x, z: W.south.z - 15, facing: Math.PI },
    tick: (dt, t, fx, fz) => {
      waterUniforms.uTime.value = t;
      kit.tick(dt, fx, fz);
    },
  };
  const setNight = (on: boolean) => {
    kit.setNight(on);
    for (const b of braziers) kit.setLit(b, on);
  };
  return { zone, kit, doors, setNight, stalls: stalls.map(([x, z, rot, , kind]) => ({ x, z, rot, kind })) };
}

function flora(kit: ZoneKit, kind: 'pine' | 'broadleaf' | 'autumn', x: number, z: number, rot: number, s: number) {
  kit.flora.add(kind, x, kit.y(x, z) - 0.1, z, rot, s);
  kit.col.addCircle(x, z, 0.5 * s);
  void hash2;
}
