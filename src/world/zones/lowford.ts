import * as THREE from 'three';
import { PRESETS } from '@/render/atmosphere';
import { Terrain, type TerrainPaint } from '@/render/terrain';
import { Grass } from '@/render/grass';
import { createWater, waterUniforms } from '@/render/water';
import { CollisionWorld } from '@/sim/collision';
import { Noise2D, distToSegment, smoothstep, hash2, hash1 } from '@/core/math';
import type { ZoneBuild } from '@/game/scene';
import { ZoneKit, type LightSource } from './kit';

/* The Low Ford road, at night.
 *
 * A valley road running north to the Waystation, with the forest pressed in
 * on both sides. South to north, it is also the tutorial:
 *
 *   the campfire      where the survivor wakes, and where the dead first rise
 *   the cart          a broken wagon on the road: the first stretch of travel
 *   the Watch-post    a ruin with a dead watchman and his chest (equipment)
 *   the barrow        a fenced graveyard and a crypt; a Grave-Caller (ability)
 *   the Low Ford      a shallow crossing ringed by three old lamp pylons,
 *                     where something very large lies in the water (the boss)
 *   the gate          the Waystation's wall and its shut gate, at the far end
 *
 * Everything the prologue script needs to touch is returned by name. */

export const ROAD: Array<[number, number]> = [
  [6, 128], [2, 104], [-2, 88], [1, 70], [8, 52], [10, 36], [4, 18], [-3, 2], [-2, -16], [2, -30], [0, -44], [-1, -60], [2, -78], [0, -96], [0, -128],
];

export const LOWFORD = {
  camp: { x: -9, z: 89 },
  fire: { x: -10.5, z: 90.5 },
  cart: { x: 5, z: 60 },
  post: { x: 18, z: 33 },
  watchman: { x: 12.8, z: 29.5 },
  chest: { x: 14.2, z: 28.2 },
  barrow: { x: -17, z: 4 },
  crypt: { x: -26, z: 1 },
  ford: { x: 0, z: -44 },
  gate: { x: 0, z: -112 },
  exitZ: -104,
};

export const riverZ = (x: number) => -44 + Math.sin(x * 0.032) * 4.5 + Math.sin(x * 0.011 + 1) * 3;
export const WATER_Y = -1.05;

export interface LowFordBuild {
  zone: ZoneBuild;
  kit: ZoneKit;
  pylons: Array<{ x: number; z: number; src: LightSource; flame: THREE.Object3D; collider: number; top: number }>;
  campfire: LightSource;
  gate: THREE.Object3D[];
  roadDist: (x: number, z: number) => number;
}

export function buildLowFord(grassDensity = 1): LowFordBuild {
  const noise = new Noise2D(31);
  const roadDist = (x: number, z: number) => {
    let d = 1e9;
    for (let i = 0; i < ROAD.length - 1; i++) d = Math.min(d, distToSegment(x, z, ROAD[i][0], ROAD[i][1], ROAD[i + 1][0], ROAD[i + 1][1]));
    return d;
  };
  const L = LOWFORD;
  const clearings: Array<[number, number, number]> = [
    [L.camp.x, L.camp.z, 15], [L.post.x - 2, L.post.z, 13], [L.barrow.x - 2, L.barrow.z, 15], [L.ford.x, L.ford.z, 22], [L.gate.x, L.gate.z + 4, 16], [L.cart.x, L.cart.z, 8],
  ];
  const clearingAt = (x: number, z: number) => {
    let k = 0;
    for (const [cx, cz, r] of clearings) k = Math.max(k, 1 - smoothstep(r * 0.7, r, Math.hypot(x - cx, z - cz)));
    return k;
  };
  const riverD = (x: number, z: number) => Math.abs(z - riverZ(x));
  const fordK = (x: number) => 1 - smoothstep(13, 20, Math.abs(x));

  const height = (x: number, z: number) => {
    let h = noise.fbm(x * 0.02, z * 0.02, 4) * 2.4 + noise.ridged(x * 0.009 + 5, z * 0.009, 3) * 2.2;
    const rd = roadDist(x, z);
    h = THREE.MathUtils.lerp(h * 0.25, h, smoothstep(2.5, 11, rd));
    h *= 1 - clearingAt(x, z) * 0.65;
    // The valley walls.
    const edge = Math.abs(x) - 70 - Math.sin(z * 0.03) * 12;
    h += smoothstep(0, 40, edge) * 22;
    h += smoothstep(100, 128, Math.abs(z)) * 10;
    // The river bed: deep, except at the ford, where it is a shallow,
    // level crossing a hand's depth under the water.
    const rv = riverD(x, z);
    const bed = THREE.MathUtils.lerp(WATER_Y - 2.6, WATER_Y - 0.28, fordK(x)) + noise.noise(x * 0.2, z * 0.2) * 0.12;
    const k = 1 - smoothstep(3.5 + fordK(x) * 4, 10 + fordK(x) * 4, rv);
    return THREE.MathUtils.lerp(h, bed, k);
  };
  const terrain = new Terrain({
    size: 260, resolution: 261,
    height,
    paint: (x: number, z: number, o: TerrainPaint) => {
      const rd = roadDist(x, z);
      const n = noise.noise(x * 0.3, z * 0.3);
      o.dirt = 1 - smoothstep(1.7, 3.6, rd + n * 0.9);
      // Cart ruts: two dark lines worn into the road.
      o.mud = (1 - smoothstep(0.12, 0.4, Math.abs(rd - 0.95) + n * 0.08)) * 0.55 * (1 - smoothstep(1.2, 1.8, rd));
      // Worn ground around the camp and the ruin.
      o.dirt = Math.max(o.dirt, (1 - smoothstep(3, 6.5, Math.hypot(x - L.fire.x, z - L.fire.z) + n)) * 0.85);
      o.dirt = Math.max(o.dirt, (1 - smoothstep(5, 9, Math.hypot(x - L.post.x, z - L.post.z) + n)) * 0.7);
      // Old flagstones: the Watch-post floor, the causeway at the ford, the gate apron.
      const postFloor = Math.max(Math.abs(x - L.post.x), Math.abs(z - L.post.z)) < 5.2 + n * 0.6 ? 1 : 0;
      const causeway = Math.abs(x) < 2.4 + n * 0.5 && riverD(x, z) > 7 && riverD(x, z) < 12 ? 0.9 : 0;
      const apron = Math.hypot(x - L.gate.x, z - L.gate.z - 4) < 9 + n ? 1 : 0;
      o.stone = Math.max(postFloor, causeway, apron);
      // Mud along the river, and a dark stain over the barrow.
      const rv = riverD(x, z);
      o.mud = Math.max(o.mud, (1 - smoothstep(4, 9.5, rv + n * 1.5)) * 0.95);
      // Nothing grows under the water.
      if (rv < 16 && height(x, z) < WATER_Y + 0.15) o.mud = 1;
      o.blight = (1 - smoothstep(5, 13, Math.hypot(x - L.barrow.x, z - L.barrow.z) + n * 3)) * 0.35;
    },
  });

  const col = new CollisionWorld(260);
  col.bound = 124;
  const kit = new ZoneKit(terrain, col);
  const root = kit.root;
  root.add(terrain.mesh);
  const grass = new Grass(terrain, { density: grassDensity });
  root.add(grass.mesh);

  // Water, and invisible banks where it is too deep to wade.
  const water = createWater({ width: 260, depth: 34, color: '#1c3a42', murk: '#081418', flow: [0.35, 0.02], opacity: 0.82, sky: '#2a4458' });
  water.position.set(0, WATER_Y, -44);
  root.add(water);
  for (let x = -128; x <= 128; x += 3) {
    if (Math.abs(x) < 15) continue;
    col.addCircle(x, riverZ(x), 3.6, { soft: true });
  }

  /* ------------------------------------------------------------ forest -- */
  const flora = kit.flora;
  const g = 3.3;
  for (let gz = -128; gz < 128; gz += g) {
    for (let gx = -128; gx < 128; gx += g) {
      const x = gx + (hash2(gx * 10, gz * 10, 1) - 0.5) * g * 0.9;
      const z = gz + (hash2(gx * 10, gz * 10, 2) - 0.5) * g * 0.9;
      const rd = roadDist(x, z);
      const clr = clearingAt(x, z);
      const rv = riverD(x, z);
      const forest = noise.fbm(x * 0.028 + 11, z * 0.028, 3);
      const y = terrain.heightAt(x, z);
      const rot = hash2(gx, gz, 5) * Math.PI * 2;
      const h = hash2(gx, gz, 6);
      if (rv < 7 && Math.abs(x) > 15) {
        // Reeds and stones on the banks.
        if (h < 0.3 && rv > 4.2) flora.add(h < 0.1 ? 'rock' : 'bush', x, y, z, rot, 0.5 + h);
        continue;
      }
      if (rv < 10) continue;
      const open = rd < 6.5 || clr > 0.25;
      if (!open && h < 0.16 && forest > -0.3) flora.add(h < 0.03 ? 'berry' : h < 0.1 ? 'bush' : 'bramble', x, y, z, rot, 0.7 + h * 2.2);
      if (hash2(gx, gz, 8) < 0.05 && rd > 3 && clr < 0.6) {
        const big = hash2(gx, gz, 9) < 0.25;
        const s = 0.6 + h * 0.8;
        flora.add(big ? 'boulder' : 'rock', x + 1.1, terrain.heightAt(x + 1.1, z), z, rot, s);
        col.addCircle(x + 1.1, z, (big ? 2.1 : 0.8) * s);
      }
      if (rd > 4 && clr < 0.6) kit.undergrowth(x, z, g, { under: !open && forest > -0.25, blight: Math.hypot(x - L.barrow.x, z - L.barrow.z) < 26 ? 0.4 : 0 });
      if (open) continue;
      const edgeWall = Math.abs(x) > 74 + Math.sin(z * 0.03) * 12;
      if (!edgeWall && hash2(gx * 7, gz * 7, 3) > 0.58 + forest * 0.4) continue;
      const sc = 0.85 + hash2(gx, gz, 4) * 0.55;
      const nearBarrow = Math.hypot(x - L.barrow.x, z - L.barrow.z) < 26;
      if (nearBarrow && h < 0.55) flora.add('dead', x, y - 0.1, z, rot, sc);
      else if (h < 0.05) flora.add('dead', x, y - 0.1, z, rot, sc);
      else if (forest > 0.05 || h < 0.6) flora.add('pine', x, y - 0.15, z, rot, sc);
      else if (h < 0.7) flora.add('autumn', x, y - 0.1, z, rot, sc);
      else flora.add('broadleaf', x, y - 0.1, z, rot, sc);
      col.addCircle(x, z, 0.5 * sc);
    }
  }
  // Cliffs where the valley wall rises.
  for (let i = 0; i < 70; i++) {
    const side = i % 2 ? 1 : -1;
    const z = -124 + (i / 70) * 248;
    const x = side * (80 + Math.sin(z * 0.03) * 12 + hash1(i, 3) * 8);
    flora.add('cliff', x, terrain.heightAt(x, z) - 2, z, hash1(i, 4) * 6, 1 + hash1(i, 5) * 0.8);
  }
  for (let i = 0; i < 520; i++) {
    const x = (hash1(i, 31) - 0.5) * 230, z = (hash1(i, 32) - 0.5) * 240;
    if (riverD(x, z) < 6) continue;
    flora.add('pebble', x, terrain.heightAt(x, z), z, hash1(i, 33) * 6.28, 0.6 + hash1(i, 34));
  }

  /* -------------------------------------------------------------- camp -- */
  const campfire = kit.campfire(L.fire.x, L.fire.z, 1);
  // Bedroll, pack and a log to sit on.
  kit.bedroll(L.fire.x - 2.4, L.fire.z + 1.9, 0.9);
  kit.prop('hex_nature', 'sack', L.fire.x - 1.1, L.fire.z + 2.9, { rot: 0.6, scale: 9 });
  kit.log(L.fire.x + 2.0, L.fire.z - 0.2, 1.35, 2.3, 0.27);
  kit.log(L.fire.x - 0.4, L.fire.z - 2.3, 0.1, 1.6, 0.22);
  // A tripod and a pot over the fire.
  {
    const iron = new THREE.MeshStandardMaterial({ color: '#2a2622', roughness: 0.55, metalness: 0.7 });
    const fy = kit.y(L.fire.x, L.fire.z);
    const tri = new THREE.Group();
    for (let i = 0; i < 3; i++) {
      const a = (i / 3) * Math.PI * 2;
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.03, 1.6, 5), iron);
      leg.position.set(Math.cos(a) * 0.4, 0.72, Math.sin(a) * 0.4);
      leg.lookAt(0, 1.45 + 0.72, 0);
      leg.rotateX(Math.PI / 2);
      tri.add(leg);
    }
    const chain = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.55, 4), iron);
    chain.position.y = 1.2;
    tri.add(chain);
    const pot = new THREE.Mesh(new THREE.SphereGeometry(0.24, 12, 8, 0, Math.PI * 2, 0.5, Math.PI - 0.5), iron);
    pot.position.y = 0.88;
    tri.add(pot);
    const stew = new THREE.Mesh(new THREE.CircleGeometry(0.21, 12), new THREE.MeshStandardMaterial({ color: '#5a3a1a', roughness: 0.4, emissive: '#2a1004' }));
    stew.rotation.x = -Math.PI / 2;
    stew.position.y = 1.0;
    tri.add(stew);
    tri.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = true; });
    tri.position.set(L.fire.x, fy, L.fire.z);
    root.add(tri);
  }
  kit.prop('halloween', 'lantern_standing', L.fire.x - 3.2, L.fire.z - 1.4, { scale: 0.7, r: 0.25 });
  kit.prop('dungeon', 'trunk_small_A', L.fire.x - 1.6, L.fire.z - 2.2, { rot: -0.5, scale: 0.9 });
  // Your light by the road: the one lamp still burning.
  kit.lamp(-3.5, 94, Math.PI * 0.5, true);

  /* -------------------------------------------------------------- cart -- */
  const cartRot = 0.5;
  const cart = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({ color: '#5a4030', roughness: 0.9 });
  const bedM = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.22, 3.4), wood);
  bedM.position.y = 0.9;
  bedM.rotation.z = 0.28;
  cart.add(bedM);
  for (const sx of [-1, 1]) {
    const side = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.5, 3.4), wood);
    side.position.set(sx * 0.85, 1.15 + sx * 0.24, 0);
    side.rotation.z = 0.28;
    cart.add(side);
  }
  const wheelGeo = new THREE.TorusGeometry(0.55, 0.08, 6, 14);
  const wheel1 = new THREE.Mesh(wheelGeo, wood);
  wheel1.position.set(0.95, 0.62, 0.9);
  wheel1.rotation.y = Math.PI / 2;
  cart.add(wheel1);
  const wheel2 = new THREE.Mesh(wheelGeo, wood);
  wheel2.position.set(-1.8, 0.06, 1.4);
  wheel2.rotation.x = Math.PI / 2;
  cart.add(wheel2);
  cart.traverse((o) => { if ((o as THREE.Mesh).isMesh) { o.castShadow = o.receiveShadow = true; } });
  cart.position.set(L.cart.x, kit.y(L.cart.x, L.cart.z), L.cart.z);
  cart.rotation.y = cartRot;
  root.add(cart);
  col.addBox(L.cart.x, L.cart.z, 1.0, 1.8, -cartRot);
  kit.prop('dungeon', 'box_small', L.cart.x + 2.2, L.cart.z + 1.4, { rot: 0.7, scale: 0.7, r: 0.5, tilt: [0.2, 0.1] });
  kit.prop('dungeon', 'barrel_small', L.cart.x - 1.8, L.cart.z - 2.4, { rot: 0.3, scale: 0.7, r: 0.4, tilt: [Math.PI / 2, 0] , y: kit.y(L.cart.x - 1.8, L.cart.z - 2.4) + 0.35 });
  kit.prop('halloween', 'gravemarker_A', L.cart.x + 3.2, L.cart.z - 2, { rot: -0.4, scale: 0.8 });

  /* -------------------------------------------------------- watch-post -- */
  const P = L.post;
  const wallS = 0.85;
  const walls: Array<[string, number, number, number]> = [
    ['wall_cracked', P.x, P.z - 4.4, 0], ['wall_broken', P.x + 4.4, P.z, Math.PI / 2], ['wall_half', P.x - 1, P.z + 4.4, Math.PI],
  ];
  for (const [name, x, z, rot] of walls) kit.prop('dungeon', name, x, z, { rot, scale: wallS, box: [1.8, 0.45] });
  kit.prop('dungeon', 'pillar', P.x + 4.2, P.z - 4.2, { scale: wallS, r: 0.7 });
  kit.prop('dungeon', 'pillar', P.x + 4.2, P.z + 4.2, { scale: wallS * 0.6, r: 0.7 });
  kit.prop('dungeon', 'rubble_large', P.x - 5.5, P.z - 3.2, { rot: 1.2, scale: 0.6, box: [2.2, 0.9] });
  kit.prop('dungeon', 'rubble_half', P.x + 2.2, P.z + 6.5, { rot: 0.4, scale: 0.55, box: [1.3, 0.8] });
  kit.prop('dungeon', 'banner_thin_red', P.x - 0.4, P.z - 4.1, { scale: 0.85 });
  kit.prop('dungeon', 'torch_mounted', P.x + 1.6, P.z - 4.0, { scale: 0.85, y: kit.y(P.x, P.z - 4) + 2.2 });
  kit.prop('dungeon', 'table_medium_broken', P.x + 1.8, P.z + 0.8, { rot: 0.5, scale: 0.75, r: 0.8 });
  kit.prop('dungeon', 'chair', P.x + 0.2, P.z + 2.2, { rot: 2.5, scale: 0.75, tilt: [0, 1.4], y: kit.y(P.x, P.z + 2) + 0.2 });
  kit.prop('dungeon', 'crates_stacked', P.x + 3.0, P.z - 2.8, { rot: 0.1, scale: 0.6, r: 1.0 });
  kit.prop('dungeon', 'trunk_large_A', L.chest.x, L.chest.z, { rot: 2.3, scale: 0.7, r: 0.6, tag: 'watch_chest' });
  kit.lamp(9.5, 38, Math.PI, false);
  // At the top of the road, where it leaves the ford behind: which way is town.
  kit.signpost(L.gate.x + 4.6, L.exitZ + 12, [-Math.PI / 2, Math.PI / 2]);

  /* ------------------------------------------------------------ barrow -- */
  const B = L.barrow;
  const fenceR = 9;
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2;
    if (Math.abs(Math.atan2(Math.sin(a), Math.cos(a))) < 0.4) continue; // the gap faces the road
    const x = B.x + Math.cos(a) * fenceR, z = B.z + Math.sin(a) * fenceR;
    kit.prop('halloween', i % 4 === 1 ? 'fence_broken' : 'fence', x, z, { rot: -a + Math.PI / 2, scale: 0.72, box: [1.45, 0.25], soft: true });
  }
  const graves: Array<[number, number, string]> = [
    [-3, -3, 'grave_A'], [0, -4, 'gravestone'], [3, -3, 'grave_B'], [-4, 1, 'gravemarker_A'], [-1, 2, 'grave_A_destroyed'],
    [2.5, 1.5, 'gravestone'], [-2.5, 5, 'gravemarker_B'], [1, 5.5, 'grave_B'], [4.5, -0.5, 'gravemarker_A'],
  ];
  for (const [dx, dz, name] of graves) {
    kit.prop('halloween', name, B.x + dx, B.z + dz, { rot: Math.PI / 2 + hash1(dx * 7 + dz, 3) * 0.3 - 0.15, scale: 0.72, r: name.startsWith('grave_') ? 0.55 : 0.3, tilt: [0, hash1(dx + dz * 3, 4) * 0.12 - 0.06] });
  }
  kit.prop('halloween', 'crypt', L.crypt.x, L.crypt.z, { rot: Math.PI / 2, scale: 0.72, box: [2.9, 2.2] });
  kit.prop('halloween', 'skull_candle', L.crypt.x + 3.6, L.crypt.z + 1.8, { scale: 0.6 });
  kit.prop('halloween', 'candle_triple', L.crypt.x + 3.4, L.crypt.z - 1.6, { scale: 0.7 });
  const cryptGlow = kit.flameGlow(L.crypt.x + 3.6, kit.y(L.crypt.x + 3.6, L.crypt.z + 1.8) + 0.72, L.crypt.z + 1.8, 0.05, '#9aff8a');
  kit.source(L.crypt.x + 3.8, kit.y(L.crypt.x, L.crypt.z) + 1.2, L.crypt.z, 0x7aff9a, 5, 10, 0.2, [cryptGlow]);
  kit.prop('halloween', 'tree_dead_large', B.x + 7, B.z + 9, { rot: 1, scale: 0.8, r: 0.5 });

  /* ---------------------------------------------------------- the ford -- */
  const F = L.ford;
  const pylons: LowFordBuild['pylons'] = [];
  const pyl = [Math.PI / 2, Math.PI * 1.18, Math.PI * 1.82];
  for (let i = 0; i < 3; i++) {
    const x = F.x + Math.cos(pyl[i]) * 11.5, z = F.z + Math.sin(pyl[i]) * 10.5;
    const gy = Math.max(kit.y(x, z), WATER_Y - 0.3);
    const obj = kit.prop('halloween', 'pillar', x, z, { scale: 0.85, y: gy - 0.1 });
    const top = gy + 4.4 * 0.85;
    const bowl = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.3, 0.35, 10), new THREE.MeshStandardMaterial({ color: '#3a3430', roughness: 0.6, metalness: 0.5 }));
    bowl.position.set(x, top + 0.1, z);
    bowl.castShadow = true;
    root.add(bowl);
    const flame = kit.flameGlow(x, top + 0.45, z, 0.32, '#9ad8ff');
    const src = kit.source(x, top + 0.8, z, 0x8ac8ff, 14, 16, 0.16, [flame]);
    const collider = col.addCircle(x, z, 0.75, { tag: `pylon:${i}` }).id;
    pylons.push({ x, z, src, flame, collider, top });
    void obj;
  }
  // The old causeway: stepping stones across the ford.
  for (let i = 0; i < 9; i++) {
    const z = F.z - 9 + i * 2.2;
    for (const sx of [-1.6, 1.6]) {
      const x = sx + (hash1(i, 9 + sx) - 0.5) * 0.5;
      kit.flora.add('rock', x, Math.max(kit.y(x, z), WATER_Y - 0.25), z, hash1(i, 11) * 6, 0.55);
    }
  }
  kit.prop('halloween', 'post', 4, F.z + 13, { rot: -0.4, scale: 0.8, r: 0.25 });

  /* ------------------------------------------------------------ gate -- */
  const G = L.gate;
  const gate: THREE.Object3D[] = [];
  const ws = 5.2;
  gate.push(kit.prop('hex_buildings', 'wall_straight_gate', G.x, G.z, { scale: ws }));
  for (const side of [-1, 1]) {
    for (let k = 1; k <= 5; k++) {
      kit.prop('hex_buildings', 'wall_straight', G.x + side * k * 2 * ws, G.z, { scale: ws });
    }
    kit.prop('hex_buildings', 'building_tower_base_blue', G.x + side * 6.4, G.z + 0.8, { scale: ws * 0.9, r: 3.6, clay: true });
  }
  col.addBox(G.x - 34, G.z, 30, 2.2, 0);
  col.addBox(G.x + 34, G.z, 30, 2.2, 0);
  // The gate itself: shut until dawn.
  const gateBar = col.addBox(G.x, G.z, 3.6, 2.2, 0, { tag: 'gate' });
  for (const side of [-1, 1]) {
    const t = kit.prop('dungeon', 'torch_mounted', G.x + side * 4.2, G.z + 2.4, { rot: 0, scale: 1, y: kit.y(G.x, G.z) + 3.4 });
    void t;
    const glow = kit.flameGlow(G.x + side * 4.2, kit.y(G.x, G.z) + 4.15, G.z + 2.75, 0.14);
    kit.source(G.x + side * 4.2, kit.y(G.x, G.z) + 4.5, G.z + 3.2, 0xffa050, 12, 16, 0.2, [glow]);
  }
  void gateBar;

  // Dead lanterns along the road: the Watch's lights, long out.
  const lampZ = [74, 44, 12, -22, -64, -86];
  lampZ.forEach((z, i) => {
    let bx = 0, bd = 1e9;
    for (let x = -12; x <= 14; x += 0.5) { const d = Math.abs(roadDist(x, z) - 3.2); if (d < bd && x > (i % 2 ? -99 : 0) && x < (i % 2 ? 0 : 99)) { bd = d; bx = x; } }
    kit.lamp(bx, z, i % 2 ? Math.PI / 2 : -Math.PI / 2, false);
  });

  flora.finalize();
  root.add(flora.group);

  const zone: ZoneBuild = {
    id: 'lowford', terrain, grass, collision: col, root, atmosphere: PRESETS.night,
    map: { water: (x, z) => terrain.heightAt(x, z) < WATER_Y - 0.05 && Math.abs(z - riverZ(x)) < 20, flora: kit.flora.marks },
    start: { x: L.camp.x + 1.5, z: L.camp.z - 1.5, facing: Math.PI },
    tick: (dt, t, fx, fz) => {
      waterUniforms.uTime.value = t;
      kit.tick(dt, fx, fz);
    },
  };
  return { zone, kit, pylons, campfire, gate, roadDist };
}
