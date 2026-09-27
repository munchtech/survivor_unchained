import * as THREE from 'three';
import { PRESETS } from '@/render/atmosphere';
import { Terrain, type TerrainPaint } from '@/render/terrain';
import { Grass } from '@/render/grass';
import { createWater, waterUniforms } from '@/render/water';
import { CollisionWorld } from '@/sim/collision';
import { Noise2D, distToSegment, smoothstep, hash2, hash1 } from '@/core/math';
import type { ZoneBuild } from '@/game/scene';
import { ZoneKit } from './kit';

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

  /* ------------------------------------------------------------- walls -- */
  const ws = 5.2, seg = 2 * ws;
  const wallRun = (x0: number, z0: number, x1: number, z1: number, gapAt?: number) => {
    const len = Math.hypot(x1 - x0, z1 - z0);
    const n = Math.round(len / seg);
    const rot = Math.atan2(-(z1 - z0), x1 - x0);
    for (let i = 0; i < n; i++) {
      const t = (i + 0.5) / n;
      const x = x0 + (x1 - x0) * t, z = z0 + (z1 - z0) * t;
      const isGate = gapAt !== undefined && i === gapAt;
      kit.prop('hex_buildings', isGate ? 'wall_straight_gate' : 'wall_straight', x, z, { rot, scale: ws, y: kit.y(x, z) - 0.3 });
      if (!isGate) col.addBox(x, z, ws, 2.1, -rot);
      else {
        // Gate posts either side; the opening itself is left clear.
        const dx = Math.cos(rot), dz = -Math.sin(rot);
        col.addBox(x + dx * ws * 0.78, z + dz * ws * 0.78, ws * 0.25, 2.1, -rot);
        col.addBox(x - dx * ws * 0.78, z - dz * ws * 0.78, ws * 0.25, 2.1, -rot);
      }
    }
  };
  const X = 41.6, Z = 39;
  wallRun(-X, Z, X, Z, 4); // south, gate in the middle
  wallRun(X, -Z, -X, -Z, 4); // north
  wallRun(-X, -Z, -X, Z); // west
  wallRun(X, Z, X, -Z, 3); // east
  for (const [x, z] of [[-X, -Z], [X, -Z], [-X, Z], [X, Z]] as const) {
    kit.prop('hex_buildings', 'building_tower_A_blue', x, z, { scale: 5.4, r: 3.4 });
  }
  // Gate towers and torches.
  for (const [gx, gz, rot] of [[0, Z, 0], [0, -Z, Math.PI], [X, 0, -Math.PI / 2]] as const) {
    for (const side of [-1, 1]) {
      const along = rot === 0 || rot === Math.PI;
      const tx = along ? gx + side * 7 : gx + 3.6, tz = along ? gz + (rot === 0 ? -3.6 : 3.6) : gz + side * 7;
      const glow = kit.flameGlow(tx, kit.y(tx, tz) + 4.1, tz, 0.14);
      kit.prop('dungeon', 'torch_mounted', tx, tz, { rot: rot + Math.PI, scale: 1, y: kit.y(tx, tz) + 3.3 });
      kit.source(tx, kit.y(tx, tz) + 4.4, tz, 0xffa050, 10, 14, 0.2, [glow]);
    }
  }

  /* --------------------------------------------------------- buildings -- */
  const doors: Record<string, { x: number; z: number }> = {};
  /** Footprints for the map. */
  const footprints: Array<{ x: number; z: number; r: number; rot: number }> = [];
  const building = (key: string, model: string, p: { x: number; z: number; rot: number }, scale = 6, r = 4.2, doorOut = 4.6) => {
    kit.prop('hex_buildings', model, p.x, p.z, { rot: p.rot, scale, y: kit.y(p.x, p.z) - 0.05 });
    col.addCircle(p.x, p.z, r);
    footprints.push({ x: p.x, z: p.z, r: r * 1.15, rot: p.rot });
    // Doors face local +z.
    const dx = Math.sin(p.rot), dz = Math.cos(p.rot);
    doors[key] = { x: p.x + dx * doorOut, z: p.z + dz * doorOut };
    // A lantern by every door: after dark, the town is where the light is.
    const lx = p.x + dx * (doorOut - 0.6) + dz * 1.7, lz = p.z + dz * (doorOut - 0.6) - dx * 1.7;
    kit.prop('halloween', 'lantern_standing', lx, lz, { rot: p.rot, scale: 0.9, r: 0.25 });
    const glow = kit.flameGlow(lx, kit.y(lx, lz) + 0.62, lz, 0.05, '#ffd08a');
    const lsrc = kit.source(lx, kit.y(lx, lz) + 1.1, lz, 0xffb468, 4.5, 8, 0.08, [glow]);
    kit.moths(lsrc);
    // After dark the doorway spills light onto the step, and the chimney smokes.
    kit.spill(p.x + dx * (doorOut - 0.8), p.z + dz * (doorOut - 0.8), 3.0, '#ffae62', 0.3);
    kit.chimney(p.x - dx * r * 0.3 + dz * r * 0.25, kit.y(p.x, p.z) + scale * 1.05, p.z - dz * r * 0.3 - dx * r * 0.25);
    return doors[key];
  };
  building('inn', 'building_home_B_red', W.inn, 8.6, 4.2, 5.2);
  building('tavern', 'building_tavern_blue', W.tavern, 6.8, 4.4, 5.2);
  building('smithy', 'building_blacksmith_blue', W.smithy, 7.2, 4.6, 5.2);
  building('trading', 'building_market_blue', W.trading, 6.8, 5.4, 5.6);
  building('warehouse', 'building_barracks_red', W.warehouse, 6.4, 5, 5.8);
  building('shrine', 'building_church_blue', W.shrine, 7.4, 4.2, 5);
  building('wenna', 'building_home_A_blue', W.wenna, 7, 3.2, 3.8);
  building('barracks', 'building_barracks_blue', W.barracks, 6.6, 5, 5.8);
  building('toll', 'building_tower_B_blue', W.toll, 6, 3.8, 4.2);
  const homes: Array<[string, number, number, number]> = [
    ['building_home_B_blue', 25, -30, 0], ['building_home_A_red', 16, -30, 0.2], ['building_home_B_red', -31, 5, Math.PI / 2],
    ['building_home_A_blue', -32, -8, Math.PI / 2], ['building_home_B_blue', 9, 30, Math.PI], ['building_home_A_red', -9, 30, Math.PI],
    ['building_home_B_red', 31, 10, -Math.PI / 2], ['building_home_A_blue', -20, 31, Math.PI], ['building_home_A_red', 19, 31, Math.PI],
    ['building_home_B_blue', -31, 15, Math.PI / 2], ['building_home_A_blue', 32, -20, -Math.PI / 2], ['building_home_B_red', -2, -31, 0],
  ];
  homes.forEach(([m, x, z, rot], i) => building(`home${i}`, m, { x, z, rot }, m.includes('_B_') ? 7 : 6.6, 3, 3.8));
  // Yards: low fences and a little clutter behind the houses.
  homes.forEach(([, x, z, rot], i) => {
    const bx = x - Math.sin(rot) * 4.4, bz = z - Math.cos(rot) * 4.4;
    for (let k = -1; k <= 1; k++) {
      const fx = bx + Math.cos(rot) * k * 2.2, fz = bz - Math.sin(rot) * k * 2.2;
      kit.prop('hex_buildings', 'fence_wood_straight', fx, fz, { rot: rot + Math.PI / 2, scale: 2.2, y: kit.y(fx, fz) });
    }
    const junk = ['barrel', 'crate_A_big', 'sack', 'bucket_water', 'resource_lumber', 'pallet'][i % 6];
    kit.prop('hex_nature', junk, bx + Math.cos(rot) * 1.5, bz - Math.sin(rot) * 1.5 + 0.8, { rot: i, scale: 6, r: 0.4 });
  });
  // Outside the walls: a windmill and fields, for the skyline.
  kit.prop('hex_buildings', 'building_windmill_blue', -58, 50, { rot: 0.4, scale: 8 });
  kit.prop('hex_buildings', 'building_watermill_blue', 24, 50, { rot: Math.PI, scale: 7 });
  kit.prop('hex_buildings', 'building_grain', -30, 52, { rot: 0.2, scale: 8 });
  kit.prop('hex_buildings', 'building_grain', -42, 60, { rot: -0.3, scale: 8 });
  footprints.push({ x: -58, z: 50, r: 5, rot: 0.4 }, { x: 24, z: 50, r: 4.5, rot: Math.PI }, { x: -30, z: 52, r: 3.5, rot: 0.2 }, { x: -42, z: 60, r: 3.5, rot: -0.3 });

  /* ------------------------------------------------------------ square -- */
  kit.prop('hex_buildings', 'building_well_blue', 0, 0, { scale: 5, r: 2 });
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
  const goods: Record<string, string[]> = { produce: ['#c84a2a', '#e8b030', '#6a9a3a', '#b8322a'], cloth: ['#3a5a8a', '#8a3a4a', '#d8c8a0', '#5a7a4a'], herbs: ['#5a8a3a', '#8aa84a', '#6a5a3a', '#b0c070'], pots: ['#8a5a3a', '#a86a4a', '#6a4a3a', '#c8a070'] };
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
    const cols = goods[kind];
    for (let i = 0; i < 9; i++) {
      const c = new THREE.Color(cols[i % cols.length]);
      const piece = kind === 'cloth' ? new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.08 + hash1(i, 7) * 0.1, 0.4), new THREE.MeshStandardMaterial({ color: c, roughness: 1 }))
        : kind === 'pots' ? new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.13, 0.26, 8), new THREE.MeshStandardMaterial({ color: c, roughness: 0.7 }))
          : new THREE.Mesh(new THREE.SphereGeometry(0.09 + hash1(i, 8) * 0.05, 7, 5), new THREE.MeshStandardMaterial({ color: c, roughness: 0.8 }));
      piece.position.set(-1.1 + (i % 5) * 0.55 + hash1(i, 9) * 0.1, 0.95 + (kind === 'pots' ? 0.04 : 0), 0.6 + Math.floor(i / 5) * 0.28);
      st.add(piece);
    }
    st.traverse((o) => { if ((o as THREE.Mesh).isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    st.position.set(x, kit.y(x, z), z);
    st.rotation.y = rot;
    root.add(st);
    col.addBox(x, z, 1.5, 1.2, -rot);
    kit.prop('hex_nature', 'crate_A_big', x + Math.cos(rot) * 2.1, z - Math.sin(rot) * 2.1 + 0.2, { rot, scale: 6, r: 0.6 });
    kit.prop('hex_nature', hash1(x, 3) > 0.5 ? 'barrel' : 'sack', x - Math.cos(rot) * 2.0, z + Math.sin(rot) * 2.0, { rot, scale: 6.5, r: 0.5 });
  }
  // Benches, barrels and life.
  kit.prop('halloween', 'bench', W.tavern.x + 5.5, W.tavern.z + 3.2, { rot: Math.PI / 2, scale: 0.8, box: [0.8, 0.3] });
  kit.prop('halloween', 'bench', -4, 6, { rot: 0.3, scale: 0.8, box: [0.8, 0.3] });
  kit.prop('dungeon', 'barrel_small_stack', W.inn.x + 4, W.inn.z - 4.5, { rot: 0.4, scale: 0.8, r: 0.8 });
  kit.prop('dungeon', 'keg_decorated', W.tavern.x + 3.5, W.tavern.z - 4.5, { rot: 0.2, scale: 0.6, r: 1.0 });
  kit.prop('dungeon', 'crates_stacked', W.warehouse.x - 6, W.warehouse.z - 2, { rot: 0.3, scale: 0.8, r: 1.2 });
  kit.prop('dungeon', 'box_stacked', W.warehouse.x + 5, W.warehouse.z - 4, { rot: -0.5, scale: 0.55, r: 1.1 });
  kit.prop('hex_nature', 'wheelbarrow', W.trading.x - 5, W.trading.z + 5, { rot: 1.2, scale: 6, r: 0.8 });
  kit.prop('hex_nature', 'crate_long_A', W.trading.x - 5.6, W.trading.z - 3, { rot: 0.2, scale: 6, r: 0.9 });
  kit.prop('hex_nature', 'weaponrack', W.barracks.x + 5, W.barracks.z + 4, { rot: 0.5, scale: 7, r: 0.6 });
  kit.prop('hex_nature', 'target', W.barracks.x - 5, W.barracks.z + 5, { rot: -0.3, scale: 7, r: 0.6 });
  kit.prop('hex_nature', 'flag_blue', W.barracks.x + 2, W.barracks.z + 5, { scale: 9 });
  kit.prop('hex_nature', 'flag_red', W.inn.x + 4.5, W.inn.z + 3, { scale: 7 });

  // The smithy's forge and anvil.
  const smithFire = kit.campfire(W.smithy.x - 4.2, W.smithy.z - 3.2, 0.7);
  void smithFire;
  {
    const anvil = new THREE.Group();
    const iron = new THREE.MeshStandardMaterial({ color: '#2e2c2a', roughness: 0.45, metalness: 0.75 });
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.36, 0.6, 8), new THREE.MeshStandardMaterial({ color: '#4a3526', roughness: 0.9 }));
    base.position.y = 0.3;
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.26, 0.34), iron);
    body.position.y = 0.73;
    const horn = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.45, 8), iron);
    horn.rotation.z = Math.PI / 2;
    horn.position.set(0.6, 0.76, 0);
    anvil.add(base, body, horn);
    anvil.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = true; });
    anvil.position.set(W.smithy.x - 5.2, kit.y(W.smithy.x - 5.2, W.smithy.z + 1.2), W.smithy.z + 1.2);
    root.add(anvil);
    col.addCircle(W.smithy.x - 5.2, W.smithy.z + 1.2, 0.5);
  }

  // The broken shrine: the church, a cracked altar and cold candles.
  kit.prop('halloween', 'shrine', W.shrine.x + 4.4, W.shrine.z + 4.6, { rot: -Math.PI * 0.75, scale: 0.9, r: 0.6 });
  kit.prop('halloween', 'candle_melted', W.shrine.x + 5.2, W.shrine.z + 3.8, { scale: 0.7 });
  kit.prop('halloween', 'candle_thin', W.shrine.x + 3.6, W.shrine.z + 5.4, { scale: 0.7 });
  kit.prop('dungeon', 'rubble_half', W.shrine.x - 4, W.shrine.z + 4, { rot: 2, scale: 0.4, box: [0.9, 0.5] });

  // Wenna's garden.
  for (let i = 0; i < 14; i++) {
    const x = W.wenna.x + 4 + (i % 4) * 1.3, z = W.wenna.z - 4 + Math.floor(i / 4) * 1.4;
    kit.flora.add(i % 3 ? 'bush' : 'berry', x, kit.y(x, z), z, i, 0.45);
  }
  kit.prop('hex_nature', 'bucket_water', W.wenna.x + 3, W.wenna.z + 3, { scale: 6 });

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
  kit.prop('dungeon', 'trunk_medium_B', G.x + 2.5, G.z + 4.5, { rot: 0.7, scale: 0.8, r: 0.5, tag: 'garden_chest' });
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
    start: { x: W.south.x, z: W.south.z - 4, facing: Math.PI },
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
