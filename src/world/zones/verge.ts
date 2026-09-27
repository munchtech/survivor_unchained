import * as THREE from 'three';
import { PRESETS } from '@/render/atmosphere';
import { Terrain, type TerrainPaint } from '@/render/terrain';
import { Grass } from '@/render/grass';
import { createStream, waterUniforms } from '@/render/water';
import { CollisionWorld } from '@/sim/collision';
import { Noise2D, smoothstep, hash2, hash1 } from '@/core/math';
import { meander, PathIndex, type Pt } from '@/world/paths';
import type { ZoneBuild } from '@/game/scene';
import { ZoneKit, type LightSource } from './kit';
import { bushGeometry, floraMaterial } from '@/render/flora';

/* Thornhollow Verge: the wood east of the Waystation.
 *
 * The Old Road runs through it west to east. Off the road, everything the
 * two questlines need:
 *
 *   the wreck         Coyle's wagons, led off the road; ruts into the trees
 *   Watch-post        a ruin with a fire you can light (a field rest)
 *   Hunters' Blind    Maeca's platform over the Hollow
 *   Wolf Hollow       the Pack's den in a bowl of rocks
 *   the stream        green below the Dig; a dead wolf beside it
 *   the Dig           Grimtunnel's crew, a pump and a pipe into the water
 *   Redcowl's Roost   the Kerchief camp down in a ravine: tents, cargo, cages
 *   the Sealed Vault  a black door in the hillside (breadcrumb)
 *   the Sinkhole      something enormous and dead at the bottom (breadcrumb)
 *   the Moon Grove    behind a wall of brambles only fire opens quickly
 *
 * Everything the story touches is returned by name. */

/* Key points; the paths wander between them (see meander). */
const ROAD_KEYS: Pt[] = [[-150, 8], [-105, 10], [-72, 6], [-40, 14], [-8, 10], [22, 0], [52, -6], [84, -4], [118, 4], [150, 8]];
const RUT_KEYS: Pt[] = [[-70, 26], [-46, 44], [-14, 58], [16, 66], [34, 72]];
const STREAM_KEYS: Pt[] = [[102, -104], [84, -84], [66, -68], [40, -54], [12, -40], [-18, -26], [-40, -8], [-52, 10], [-72, 34], [-96, 58], [-130, 88], [-150, 104]];
export const VROAD = meander(ROAD_KEYS, 1.6, 3, 4.1);
export const RUTS = meander(RUT_KEYS, 1.1, 2.5, 0.6);
export const STREAM = meander(STREAM_KEYS, 2.6, 2.2, 1.7);

export const V = {
  entry: { x: -132, z: 8 },
  exitEast: { x: 142, z: 8 },
  wreck: { x: -70, z: 28 },
  post: { x: -10, z: 40 },
  blind: { x: -26, z: -40 },
  hollow: { x: -64, z: -86 },
  carcass: { x: -8, z: -34 },
  sample: { x: 20, z: -46 },
  pipe: { x: 82, z: -86 },
  dig: { x: 104, z: -104 },
  pump: { x: 94, z: -94 },
  roost: { x: 52, z: 78 },
  cages: { x: 62, z: 84 },
  cargo: { x: 44, z: 86 },
  redcowl: { x: 54, z: 90 },
  vault: { x: -106, z: -56 },
  sinkhole: { x: 106, z: 54 },
  grove: { x: -114, z: 80 },
  brambles: { x: -100, z: 72 },
};

export interface VergeBuild {
  zone: ZoneBuild;
  kit: ZoneKit;
  roadDist: (x: number, z: number) => number;
  streamDist: (x: number, z: number) => number;
  postFire: LightSource;
  blindFire: LightSource;
  /** The bramble wall: one mesh and collider per bush (they burn). */
  brambles: Array<{ mesh: THREE.Mesh; collider: number; x: number; z: number }>;
  /** Powder kegs at the Dig and the Roost (tagged colliders). */
  pumpWheel: THREE.Object3D;
  thing: THREE.Object3D;
  cageBars: THREE.Object3D[];
  vaultGlow: THREE.Object3D;
}

/** How the wood is when you walk into it: poisoned, or healing. */
export interface VergeState { cleanDays: number }

export function buildVerge(grassDensity = 1, state: VergeState = { cleanDays: 0 }): VergeBuild {
  // Once the poison stops, the blight draws back a little more each day.
  const heal = Math.min(1, state.cleanDays / 3);
  const noise = new Noise2D(911);
  const roadIx = new PathIndex(VROAD, 14, 8, ROAD_KEYS);
  const rutIx = new PathIndex(RUTS, 14, 8, RUT_KEYS);
  const streamIx = new PathIndex(STREAM, 14, 8, STREAM_KEYS);
  const roadDist = (x: number, z: number) => roadIx.dist(x, z);
  const rutDist = (x: number, z: number) => rutIx.dist(x, z);
  const streamDist = (x: number, z: number) => streamIx.dist(x, z);
  const clear: Array<[number, number, number]> = [
    [V.wreck.x, V.wreck.z, 13], [V.post.x, V.post.z, 12], [V.blind.x, V.blind.z, 11], [V.hollow.x, V.hollow.z, 20], [V.dig.x - 4, V.dig.z + 4, 22],
    [V.roost.x, V.roost.z + 6, 22], [V.vault.x + 4, V.vault.z + 4, 12], [V.sinkhole.x, V.sinkhole.z, 24], [V.grove.x, V.grove.z, 14], [V.entry.x + 6, V.entry.z, 10],
    [V.carcass.x, V.carcass.z, 7], [V.sample.x, V.sample.z, 7], [V.pipe.x, V.pipe.z, 8],
  ];
  const clearing = (x: number, z: number) => {
    let k = 0;
    for (const [cx, cz, r] of clear) k = Math.max(k, 1 - smoothstep(r * 0.7, r, Math.hypot(x - cx, z - cz)));
    return k;
  };
  const ravine = (x: number, z: number) => {
    // An elongated bowl, open to the west where the ruts come in.
    const dx = (x - V.roost.x) / 26, dz = (z - V.roost.z - 6) / 17;
    return 1 - smoothstep(0.55, 1.05, Math.hypot(dx, dz));
  };
  const sink = (x: number, z: number) => 1 - smoothstep(9, 15, Math.hypot(x - V.sinkhole.x, z - V.sinkhole.z));
  const hollowBowl = (x: number, z: number) => 1 - smoothstep(10, 18, Math.hypot(x - V.hollow.x, z - V.hollow.z));

  const baseHeight = (x: number, z: number) => {
    let h = noise.fbm(x * 0.016, z * 0.016, 4) * 3.2 + noise.ridged(x * 0.008 + 9, z * 0.008, 3) * 3;
    h = THREE.MathUtils.lerp(h * 0.2, h, smoothstep(3, 12, roadDist(x, z)));
    h *= 1 - clearing(x, z) * 0.55;
    // Hillsides at the edges, and the hill the Vault is cut into.
    h += smoothstep(112, 140, Math.max(Math.abs(x), Math.abs(z))) * 14;
    h += (1 - smoothstep(6, 20, Math.hypot(x - V.vault.x + 6, z - V.vault.z + 8))) * 7;
    // The ravine, the sinkhole and the Hollow.
    h -= ravine(x, z) * 5.5;
    h -= sink(x, z) * 9 + (1 - smoothstep(5, 9, Math.hypot(x - V.sinkhole.x, z - V.sinkhole.z))) * 3;
    h -= hollowBowl(x, z) * 2.2;
    h += (1 - smoothstep(18, 26, Math.hypot(x - V.hollow.x, z - V.hollow.z))) * (1 - hollowBowl(x, z)) * 2.4;
    return h;
  };
  // The stream's water line: the ground along its course, never rising, so
  // the water runs downhill all the way from the Dig.
  const profile: number[] = [];
  {
    let run = 0, lo = Infinity;
    for (let i = 0; i < STREAM.length - 1; i++) {
      const [ax, az] = STREAM[i], [bx, bz] = STREAM[i + 1];
      const l = Math.hypot(bx - ax, bz - az);
      for (let d = 0; d < l; d += 1) {
        const t = d / l;
        lo = Math.min(lo, baseHeight(ax + (bx - ax) * t, az + (bz - az) * t) - 0.3);
        profile[Math.floor(run + d)] = lo;
      }
      run += l;
    }
  }
  const waterLine = (s: number) => profile[Math.max(0, Math.min(profile.length - 1, Math.floor(s)))] ?? 0;
  const height = (x: number, z: number) => {
    const h = baseHeight(x, z);
    const n = streamIx.nearest(x, z);
    if (n.d > 8) return h;
    // Near the water the ground takes the channel's shape exactly - cut
    // down where it is high, banked up where it is low - and blends back
    // into the wood further out.
    // The banks wander in and out a little, so the waterline does too.
    const wob = noise.noise(x * 0.3, z * 0.3) * 0.5 + noise.noise(x * 1.1 + 5, z * 1.1) * 0.15;
    const bed = waterLine(n.s) - 0.75;
    const channel = bed + Math.max(0, n.d - 1.3 - wob) * 0.85;
    const k = 1 - smoothstep(3.4, 8, n.d);
    const shaped = n.d < 3.4 ? channel : Math.min(h, channel) + Math.max(0, channel - h) * 0.6;
    return THREE.MathUtils.lerp(h, shaped, k);
  };
  const blightAt = (x: number, z: number) => {
    // Poison runs downstream of the pipe; strongest near the Dig.
    const sd = streamDist(x, z);
    const alongDig = 1 - smoothstep(10, 150, Math.hypot(x - V.pipe.x, z - V.pipe.z));
    return (1 - smoothstep(2.6, 3.6 + alongDig * 2.5, sd + noise.noise(x * 0.25, z * 0.25) * 1.2)) * (0.15 + alongDig * 0.4);
  };
  /** The blight on the ground now; what it killed stays dead. */
  const blightNow = (x: number, z: number) => blightAt(x, z) * (1 - heal * 0.85);

  const terrain = new Terrain({
    size: 290, resolution: 291, height,
    paint: (x: number, z: number, o: TerrainPaint) => {
      const n = noise.noise(x * 0.3, z * 0.3);
      const rd = roadDist(x, z);
      o.dirt = 1 - smoothstep(1.8, 3.8, rd + n * 0.9);
      o.mud = (1 - smoothstep(0.12, 0.45, Math.abs(rd - 1.0) + n * 0.08)) * 0.5 * (1 - smoothstep(1.3, 1.9, rd));
      // Ruts where the wagons were driven off.
      const ru = rutDist(x, z);
      o.mud = Math.max(o.mud, (1 - smoothstep(0.1, 0.35, Math.abs(ru - 0.9) + n * 0.1)) * 0.75 * (1 - smoothstep(1.2, 2, ru)));
      o.dirt = Math.max(o.dirt, (1 - smoothstep(1.2, 2.8, ru + n)) * 0.5);
      // Trodden ground at every camp.
      o.dirt = Math.max(o.dirt, clearing(x, z) * (0.35 + n * 0.3), ravine(x, z) * 0.9, hollowBowl(x, z) * 0.6);
      o.stone = (1 - smoothstep(4, 6, Math.max(Math.abs(x - V.post.x), Math.abs(z - V.post.z)) + n)) * 0.9;
      o.stone = Math.max(o.stone, (1 - smoothstep(3, 6, Math.hypot(x - V.vault.x, z - V.vault.z) + n)) * 0.8);
      // The sinkhole: raw earth fallen in, wet at the bottom.
      o.dirt = Math.max(o.dirt, sink(x, z));
      o.mud = Math.max(o.mud, (1 - smoothstep(5, 9, Math.hypot(x - V.sinkhole.x, z - V.sinkhole.z) + n * 1.5)) * 0.85);
      o.blight = blightNow(x, z);
      // Bare mud banks: nothing grows at the water's edge.
      o.mud = Math.max(o.mud, 1 - smoothstep(3.0, 4.6, streamDist(x, z) + n * 0.8));
    },
    palette: { blightGlow: '#9aff4a' },
  });

  const col = new CollisionWorld(290);
  col.bound = 142;
  const kit = new ZoneKit(terrain, col);
  const root = kit.root;
  root.add(terrain.mesh);
  const grass = new Grass(terrain, { density: grassDensity });
  root.add(grass.mesh);

  // The stream: a ribbon of water down its carved bed, poisoned green.
  // Poisoned green, or running clear again.
  const mix = (a: string, b: string) => '#' + new THREE.Color(a).lerp(new THREE.Color(b), heal).getHexString();
  root.add(createStream(STREAM, 6.8, (x, z) => waterLine(streamIx.nearest(x, z).s),
    {
      color: mix('#2a4a1e', '#22485a'), murk: mix('#0c1e06', '#071620'), flow: [0, 0.6], opacity: 0.94, glow: 0.45 * (1 - heal), sky: mix('#2e4a30', '#2c4658'),
      shallow: mix('#4e5a2a', '#5a5238'), foam: mix('#b8c890', '#dfe6e2'),
    },
    (x, z) => terrain.heightAt(x, z)));

  /* ------------------------------------------------------------ forest -- */
  const flora = kit.flora;
  const g = 3.4;
  for (let gz = -142; gz < 142; gz += g) {
    for (let gx = -142; gx < 142; gx += g) {
      const x = gx + (hash2(gx * 10, gz * 10, 1) - 0.5) * g * 0.9;
      const z = gz + (hash2(gx * 10, gz * 10, 2) - 0.5) * g * 0.9;
      const rd = roadDist(x, z), sd = streamDist(x, z), ru = rutDist(x, z);
      const clr = Math.max(clearing(x, z), ravine(x, z), sink(x, z) > 0.05 ? 1 : 0);
      const forest = noise.fbm(x * 0.024 + 3, z * 0.024, 3);
      const y = terrain.heightAt(x, z);
      const rot = hash2(gx, gz, 5) * Math.PI * 2;
      const h = hash2(gx, gz, 6);
      const blight = blightAt(x, z);
      if (sd < 3.5) continue;
      const open = rd < 6.5 || ru < 3 || clr > 0.25;
      if (!open && h < 0.14 && forest > -0.35) flora.add(blight > 0.3 ? 'bramble' : h < 0.03 ? 'berry' : h < 0.09 ? 'bush' : 'bramble', x, y, z, rot, 0.7 + h * 2.2);
      if (hash2(gx, gz, 8) < 0.055 && rd > 3 && clr < 0.6) {
        const big = hash2(gx, gz, 9) < 0.28;
        const s = 0.6 + h * 0.9;
        flora.add(big ? 'boulder' : 'rock', x + 1.1, terrain.heightAt(x + 1.1, z), z, rot, s);
        col.addCircle(x + 1.1, z, (big ? 2.1 : 0.8) * s);
      }
      if (open) continue;
      const edgeWall = Math.max(Math.abs(x), Math.abs(z)) > 118;
      // Glades: the wood opens up here and there, room to fight in.
      const glade = noise.fbm(x * 0.012 + 40, z * 0.012 - 7, 2);
      // Inside, the wood is a place to fight in: stands of trees with room
      // between them. The edges stay a wall.
      if (!edgeWall && (glade > 0.16 || hash2(gx * 7, gz * 7, 3) > 0.34 + forest * 0.36)) continue;
      const sc = 0.85 + hash2(gx, gz, 4) * 0.6;
      if (blight > 0.35) flora.add(h < 0.6 ? 'dead' : 'sick', x, y - 0.1, z, rot, sc);
      else if (h < 0.05) flora.add('dead', x, y - 0.1, z, rot, sc);
      else if (forest > 0.1 || h < 0.5) flora.add('pine', x, y - 0.15, z, rot, sc);
      else if (h < 0.72) flora.add('autumn', x, y - 0.1, z, rot, sc);
      else flora.add('broadleaf', x, y - 0.1, z, rot, sc);
      col.addCircle(x, z, 0.5 * sc);
    }
  }
  // Rocks ringing the Hollow.
  for (let i = 0; i < 26; i++) {
    const a = (i / 26) * Math.PI * 2 + hash1(i, 3) * 0.2;
    if (Math.abs(a - Math.PI * 0.3) < 0.35) continue; // the way in
    const r = 17 + hash1(i, 4) * 3;
    const x = V.hollow.x + Math.cos(a) * r, z = V.hollow.z + Math.sin(a) * r;
    flora.add(hash1(i, 5) < 0.5 ? 'boulder' : 'cliff', x, terrain.heightAt(x, z) - 0.5, z, a, 0.6 + hash1(i, 6) * 0.5);
    col.addCircle(x, z, 2.4);
  }
  /* The den itself: across the bowl from the way in, a mouth of stacked
   * rock with the dark going back into the hill; flattened beds of dry
   * grass where the Pack sleeps; what they have eaten, lying about. */
  {
    const H = V.hollow;
    const away = Math.PI * 0.3 + Math.PI; // opposite the way in
    const dx = Math.cos(away), dz = Math.sin(away);
    const mx = H.x + dx * 11.5, mz = H.z + dz * 11.5;
    const facing = Math.atan2(-dx, -dz); // the mouth looks into the bowl
    // A mound of the same rock that rings the bowl, and in its face a low
    // black mouth going back into the hill.
    const bx = mx + dx * 5.2, bz = mz + dz * 5.2;
    flora.add('boulder', bx, kit.y(bx, bz) - 1.0, bz, facing, 1.1);
    flora.add('cliff', bx - Math.cos(facing) * 3.2, kit.y(bx, bz) - 0.8, bz + Math.sin(facing) * 3.2, facing + 0.6, 1.05);
    flora.add('cliff', bx + Math.cos(facing) * 3.4, kit.y(bx, bz) - 0.8, bz - Math.sin(facing) * 3.4, facing - 0.5, 1.0);
    // A ragged opening, wider than it is high, lower on one side.
    const ragged = (grow: number) => {
      const sh = new THREE.Shape();
      const n = 14;
      for (let i = 0; i <= n; i++) {
        const a = Math.PI - (i / n) * Math.PI;
        const r = (1 + (hash1(i, 57) - 0.5) * 0.22) * grow;
        const x = Math.cos(a) * 1.5 * r, y = Math.sin(a) * 1.55 * r * (1 - (i / n) * 0.18);
        if (i === 0) sh.moveTo(x, 0); else sh.lineTo(x, y);
      }
      sh.lineTo(1.5 * grow, 0);
      return sh;
    };
    const mouth = new THREE.Mesh(new THREE.ShapeGeometry(ragged(1)), new THREE.MeshBasicMaterial({ color: '#040303' }));
    const rim = new THREE.Mesh(new THREE.ShapeGeometry(ragged(1.25)), new THREE.MeshStandardMaterial({ color: '#4a453e', roughness: 1, flatShading: true }));
    rim.position.z = -0.03;
    const den = new THREE.Group();
    den.add(rim, mouth);
    // Rock either side of it and over it, so the hole is in the hill.
    const px = Math.cos(facing), pz = -Math.sin(facing);
    for (const [side, sc] of [[-1, 0.5], [1, 0.44]] as const) {
      const rx = mx + px * side * 3.0 + dx * 1.2, rz = mz + pz * side * 3.0 + dz * 1.2;
      flora.add('boulder', rx, kit.y(rx, rz) - 0.5, rz, facing + side, sc);
      col.addCircle(rx, rz, 1.2);
    }

    den.position.set(mx, kit.y(mx, mz) - 0.25, mz);
    den.rotation.y = facing;
    root.add(den);
    // Trodden bare in front of it.
    const worn = new THREE.Mesh(new THREE.CircleGeometry(2.6, 20), new THREE.MeshBasicMaterial({ color: '#000000', transparent: true, opacity: 0.22, depthWrite: false }));
    worn.rotation.x = -Math.PI / 2;
    worn.scale.set(1, 0.7, 1);
    worn.position.set(mx + dx * -1.4, kit.y(mx, mz) + 0.04, mz + dz * -1.4);
    worn.renderOrder = 2;
    root.add(worn);
    col.addCircle(bx, bz, 3.4);
    // Beds of flattened grass.
    const strawTex = (() => {
      const c = document.createElement('canvas');
      c.width = c.height = 128;
      const g2 = c.getContext('2d')!;
      // A worn, matted base, fading at the edge...
      const base = g2.createRadialGradient(64, 64, 6, 64, 64, 62);
      base.addColorStop(0, 'rgba(150, 124, 78, 0.9)');
      base.addColorStop(0.7, 'rgba(140, 116, 72, 0.75)');
      base.addColorStop(1, 'rgba(140, 116, 72, 0)');
      g2.fillStyle = base;
      g2.fillRect(0, 0, 128, 128);
      // ...and stalks laid round it the way a body turns before it lies down.
      let seed = 1234567;
      const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
      for (let i = 0; i < 900; i++) {
        const a = rnd() * Math.PI * 2, r = 4 + rnd() * 56, len = 6 + rnd() * 12, tw = a + Math.PI / 2 + (rnd() - 0.5) * 0.7;
        const x = 64 + Math.cos(a) * r, y = 64 + Math.sin(a) * r;
        const lit = rnd();
        g2.strokeStyle = `rgba(${150 + lit * 70 | 0}, ${122 + lit * 56 | 0}, ${70 + lit * 40 | 0}, ${(0.5 + lit * 0.4) * (1 - Math.max(0, r - 44) / 16)})`;
        g2.lineWidth = 1 + rnd() * 1.2;
        g2.beginPath(); g2.moveTo(x, y); g2.lineTo(x + Math.cos(tw) * len, y + Math.sin(tw) * len); g2.stroke();
      }
      const t = new THREE.CanvasTexture(c);
      t.colorSpace = THREE.SRGBColorSpace;
      return t;
    })();
    const strawMat = new THREE.MeshStandardMaterial({ map: strawTex, transparent: true, roughness: 1, depthWrite: false });
    for (let i = 0; i < 4; i++) {
      const a = away + (i - 1.5) * 0.55, d = 6 + (i % 2) * 2.2;
      const x = H.x + Math.cos(a) * d, z = H.z + Math.sin(a) * d;
      const bed = new THREE.Mesh(new THREE.CircleGeometry(1.1 + hash1(i, 81) * 0.4, 18), strawMat);
      bed.rotation.set(-Math.PI / 2, 0, i);
      bed.scale.set(1, 0.75, 1);
      bed.position.set(x, kit.y(x, z) + 0.05, z);
      bed.receiveShadow = true;
      bed.renderOrder = 2;
      root.add(bed);
    }
    // What they have eaten.
    const bones: Array<[string, number]> = [['ribcage', 0.8], ['bone_A', 0.8], ['bone_B', 0.8], ['bone_C', 0.8], ['skull', 0.4], ['bone_A', 0.7], ['bone_C', 0.7], ['bone_B', 0.6], ['ribcage', 0.6], ['bone_A', 0.6]];
    bones.forEach(([name, sc], i) => {
      const a = hash1(i, 71) * Math.PI * 2, d = 2.5 + hash1(i, 72) * 8;
      const x = H.x + Math.cos(a) * d, z = H.z + Math.sin(a) * d;
      kit.prop('halloween', name, x, z, { rot: hash1(i, 73) * 6.28, scale: sc });
    });
    // A dead tree by the mouth, bark scored where they sharpen their claws.
    const tx = mx + Math.cos(away + 1.3) * 5, tz = mz + Math.sin(away + 1.3) * 5;
    kit.prop('halloween', 'tree_dead_large', tx, tz, { rot: 0.7, scale: 0.9, r: 0.5 });
    kit.log(H.x + Math.cos(away - 1.1) * 7, H.z + Math.sin(away - 1.1) * 7, away + 0.4, 3.2, 0.34);
  }
  for (let i = 0; i < 600; i++) {
    const x = (hash1(i, 31) - 0.5) * 270, z = (hash1(i, 32) - 0.5) * 270;
    if (streamDist(x, z) < 3) continue;
    flora.add('pebble', x, terrain.heightAt(x, z), z, hash1(i, 33) * 6.28, 0.6 + hash1(i, 34));
  }

  /* ------------------------------------------------------------- wreck -- */
  const W = V.wreck;
  const wood = new THREE.MeshStandardMaterial({ color: '#5e4430', roughness: 0.9 });
  const canvas = new THREE.MeshStandardMaterial({ color: '#c8b890', roughness: 1, side: THREE.DoubleSide });
  const wagon = (x: number, z: number, rot: number, tipped: boolean) => {
    const grp = new THREE.Group();
    const bed = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.25, 3.6), wood);
    bed.position.y = 0.95;
    grp.add(bed);
    for (const sx of [-0.9, 0.9]) {
      const side = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.55, 3.6), wood);
      side.position.set(sx, 1.3, 0);
      grp.add(side);
    }
    // Canvas hoops, torn.
    for (let i = 0; i < 3; i++) {
      const hoop = new THREE.Mesh(new THREE.TorusGeometry(0.95, 0.04, 5, 12, Math.PI), wood);
      hoop.position.set(0, 1.3, -1.2 + i * 1.2);
      hoop.rotation.y = Math.PI / 2;
      grp.add(hoop);
    }
    const cover = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 0.95, 2.2, 10, 1, true, 0, Math.PI * (tipped ? 0.6 : 1)), canvas);
    cover.rotation.z = Math.PI / 2;
    cover.rotation.y = Math.PI / 2;
    cover.position.set(0, 1.3, 0.3);
    grp.add(cover);
    for (const [wx, wz] of [[-1, -1.2], [1, -1.2], [-1, 1.2], [1, 1.2]] as const) {
      if (tipped && wx > 0 && wz > 0) continue;
      const wh = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.08, 6, 14), wood);
      wh.position.set(wx, 0.6, wz);
      wh.rotation.y = Math.PI / 2;
      grp.add(wh);
    }
    grp.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = o.receiveShadow = true; });
    grp.position.set(x, kit.y(x, z) + (tipped ? 0.35 : 0), z);
    grp.rotation.set(0, rot, tipped ? 1.2 : 0);
    root.add(grp);
    col.addBox(x, z, tipped ? 1.6 : 1.0, 1.9, -rot);
  };
  wagon(W.x - 3, W.z - 1, 0.9, false);
  wagon(W.x + 4, W.z + 2, -0.4, true);
  wagon(W.x - 1, W.z + 7, 2.1, false);
  for (let i = 0; i < 6; i++) {
    const a = hash1(i, 41) * 6.28, d = 2 + hash1(i, 42) * 6;
    const x = W.x + Math.cos(a) * d, z = W.z + Math.sin(a) * d;
    kit.prop('dungeon', i % 3 === 0 ? 'box_small' : i % 3 === 1 ? 'barrel_small' : 'box_small_decorated', x, z, { rot: a, scale: 0.6, r: 0.45, tilt: [i % 2 ? 0.3 : 0, 0.2] });
  }
  // Arrows stuck in the sideboards: red fletching.
  for (let i = 0; i < 5; i++) {
    const arrow = new THREE.Group();
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.7, 4), wood);
    const flet = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.16, 3), new THREE.MeshStandardMaterial({ color: '#c02a20', roughness: 0.8 }));
    flet.position.y = 0.32;
    arrow.add(shaft, flet);
    arrow.position.set(W.x - 3 + (hash1(i, 51) - 0.5) * 3, kit.y(W.x, W.z) + 1.1 + hash1(i, 52) * 0.5, W.z - 1 + (hash1(i, 53) - 0.5) * 2);
    arrow.rotation.set(1.1 + hash1(i, 54) * 0.4, hash1(i, 55) * 6, 0.3);
    root.add(arrow);
  }

  /* -------------------------------------------------------- watch-post -- */
  const P = V.post;
  kit.prop('dungeon', 'wall_broken', P.x, P.z - 4.2, { scale: 0.85, box: [1.8, 0.45] });
  kit.prop('dungeon', 'wall_half', P.x - 4.2, P.z, { rot: Math.PI / 2, scale: 0.85, box: [1.8, 0.45] });
  kit.prop('dungeon', 'pillar', P.x + 4, P.z - 4, { scale: 0.85, r: 0.7 });
  kit.prop('dungeon', 'rubble_half', P.x + 3.5, P.z + 3.5, { rot: 2.4, scale: 0.5, box: [1.2, 0.7] });
  kit.prop('dungeon', 'banner_thin_red', P.x + 1.5, P.z - 4, { scale: 0.85 });
  const postFire = kit.campfire(P.x, P.z + 0.5, 0.9);
  kit.setLit(postFire, false);
  kit.log(P.x + 2.2, P.z + 1.5, 1.2, 1.8, 0.24);
  kit.lamp(P.x + 6.5, P.z - 6, Math.PI, false);

  /* ------------------------------------------------------ hunters' blind -- */
  const B = V.blind;
  {
    const plat = new THREE.Group();
    const logM = new THREE.MeshStandardMaterial({ color: '#5a4230', roughness: 0.9 });
    for (const [sx, sz] of [[-1.6, -1.6], [1.6, -1.6], [-1.6, 1.6], [1.6, 1.6]] as const) {
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.15, 3.2, 6), logM);
      leg.position.set(sx, 1.6, sz);
      plat.add(leg);
    }
    const floor = new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.18, 3.8), logM);
    floor.position.y = 3.2;
    plat.add(floor);
    const roof = new THREE.Mesh(new THREE.ConeGeometry(3.0, 1.4, 4), new THREE.MeshStandardMaterial({ color: '#4a5a3a', roughness: 1 }));
    roof.position.y = 5.4;
    roof.rotation.y = Math.PI / 4;
    plat.add(roof);
    for (const [sx, sz] of [[-1.6, -1.6], [1.6, -1.6], [-1.6, 1.6], [1.6, 1.6]] as const) {
      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 1.6, 5), logM);
      post.position.set(sx, 4.1, sz);
      plat.add(post);
    }
    const ladder = new THREE.Mesh(new THREE.BoxGeometry(0.6, 3.4, 0.08), logM);
    ladder.position.set(0, 1.7, 2.1);
    ladder.rotation.x = -0.25;
    plat.add(ladder);
    plat.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = o.receiveShadow = true; });
    plat.position.set(B.x, kit.y(B.x, B.z), B.z);
    root.add(plat);
    for (const [sx, sz] of [[-1.6, -1.6], [1.6, -1.6], [-1.6, 1.6], [1.6, 1.6]] as const) col.addCircle(B.x + sx, B.z + sz, 0.25);
  }
  const blindFire = kit.campfire(B.x + 4, B.z + 3, 0.7);
  kit.prop('hex_nature', 'tent', B.x - 4.5, B.z + 2, { rot: 0.6, scale: 7, r: 1.6 });
  kit.prop('hex_nature', 'bucket_arrows', B.x + 2.2, B.z + 4, { scale: 6 });
  kit.prop('hex_nature', 'target', B.x - 2, B.z - 4.5, { rot: 0.3, scale: 6 });

  /* ------------------------------------------------------------ the Dig -- */
  const D = V.dig;
  kit.prop('hex_buildings', 'building_mine_blue', D.x + 4, D.z - 4, { rot: -Math.PI * 0.75, scale: 7.5, r: 6 });
  kit.prop('hex_buildings', 'building_scaffolding', D.x - 8, D.z - 6, { rot: 0.4, scale: 6, r: 4 });
  kit.prop('dungeon', 'crates_stacked', D.x - 3, D.z + 8, { rot: 0.2, scale: 0.8, r: 1.2 });
  kit.prop('dungeon', 'barrel_large', D.x + 7, D.z + 5, { scale: 0.7, r: 0.7, tag: 'powder' });
  kit.prop('dungeon', 'barrel_large', D.x + 8.4, D.z + 6.4, { scale: 0.65, r: 0.7, tag: 'powder' });
  kit.prop('dungeon', 'keg_decorated', D.x + 5.5, D.z + 7.5, { rot: 1, scale: 0.55, r: 0.9, tag: 'powder' });
  // The spoil heap: what came out of the hole, tipped down the slope.
  for (let i = 0; i < 7; i++) {
    const a = i * 0.9, d = i === 0 ? 0 : 1.6 + hash1(i, 51) * 1.4;
    const x = D.x - 10 + Math.cos(a) * d, z = D.z + 4 + Math.sin(a) * d;
    kit.flora.add(i < 3 ? 'boulder' : 'rock', x, kit.y(x, z) - 0.4, z, a, i === 0 ? 1.2 : 0.6 + hash1(i, 52) * 0.5);
  }
  col.addCircle(D.x - 10, D.z + 4, 2.6);
  kit.prop('hex_nature', 'wheelbarrow', D.x - 6, D.z + 10, { rot: 2, scale: 7, r: 0.8 });
  for (const [dx, dz] of [[-2, 3], [9, -2], [-12, -2], [2, 12]] as const) {
    const x = D.x + dx, z = D.z + dz;
    kit.prop('dungeon', 'torch_lit', x, z, { scale: 1, y: kit.y(x, z) + 0.4 });
    const gl = kit.flameGlow(x, kit.y(x, z) + 1.1, z, 0.1);
    kit.source(x, kit.y(x, z) + 1.5, z, 0xffa040, 8, 11, 0.25, [gl]);
  }
  // The pump: a frame, a great wheel, and a pipe down to the stream.
  const pumpWheel = new THREE.Group();
  {
    const Pp = V.pump;
    const iron = new THREE.MeshStandardMaterial({ color: '#3a3430', roughness: 0.5, metalness: 0.7 });
    const frame = new THREE.Group();
    for (const sx of [-1.4, 1.4]) {
      const post = new THREE.Mesh(new THREE.BoxGeometry(0.3, 3.4, 0.3), wood);
      post.position.set(sx, 1.7, 0);
      frame.add(post);
    }
    const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 3.2, 8), iron);
    axle.rotation.z = Math.PI / 2;
    axle.position.y = 2.6;
    frame.add(axle);
    const wheelT = new THREE.Mesh(new THREE.TorusGeometry(1.5, 0.1, 6, 20), wood);
    pumpWheel.add(wheelT);
    for (let i = 0; i < 8; i++) {
      const sp = new THREE.Mesh(new THREE.BoxGeometry(0.08, 3, 0.08), wood);
      sp.rotation.z = (i / 8) * Math.PI;
      pumpWheel.add(sp);
    }
    pumpWheel.position.y = 2.6;
    pumpWheel.rotation.y = Math.PI / 2;
    frame.add(pumpWheel);
    const tank = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.2, 1.8, 12), iron);
    tank.position.set(0, 0.9, 2.2);
    frame.add(tank);
    const glowM = new THREE.MeshBasicMaterial({ color: new THREE.Color('#9aff4a').multiplyScalar(1.25) });
    const slurry = new THREE.Mesh(new THREE.CircleGeometry(1.0, 16), glowM);
    slurry.rotation.x = -Math.PI / 2;
    slurry.position.set(0, 1.7, 2.2);
    frame.add(slurry);
    // A riveted lip, and the slurry crusted green down the sides.
    const lip = new THREE.Mesh(new THREE.TorusGeometry(1.1, 0.1, 6, 20), iron);
    lip.rotation.x = Math.PI / 2;
    lip.position.set(0, 1.8, 2.2);
    frame.add(lip);
    for (let i = 0; i < 5; i++) {
      const a = i * 1.3 + 0.4;
      const drip = new THREE.Mesh(new THREE.CapsuleGeometry(0.07, 0.4 + (i % 3) * 0.25, 3, 6), new THREE.MeshStandardMaterial({ color: '#5a8a2a', emissive: '#4a9a1a', emissiveIntensity: 0.6, roughness: 0.3 }));
      drip.position.set(Math.cos(a) * 1.13, 1.45 - (i % 3) * 0.12, 2.2 + Math.sin(a) * 1.13);
      frame.add(drip);
    }
    frame.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = true; });
    frame.position.set(Pp.x, kit.y(Pp.x, Pp.z), Pp.z);
    frame.rotation.y = Math.PI * 0.25;
    root.add(frame);
    col.addCircle(Pp.x, Pp.z, 2.2, { tag: 'pump' });
    kit.source(Pp.x, kit.y(Pp.x, Pp.z) + 2.4, Pp.z, 0x8aff5a, 6, 10, 0.1, [slurry]);
    // The pipe: riveted iron from the tank to the water.
    const from = new THREE.Vector3(Pp.x, kit.y(Pp.x, Pp.z) + 0.8, Pp.z);
    const to = new THREE.Vector3(V.pipe.x, height(V.pipe.x, V.pipe.z) + 0.6, V.pipe.z);
    const mid = from.clone().lerp(to, 0.5);
    mid.y = Math.max(from.y, to.y) + 0.4;
    const curve = new THREE.QuadraticBezierCurve3(from, mid, to);
    const pipe = new THREE.Mesh(new THREE.TubeGeometry(curve, 24, 0.32, 10), iron);
    pipe.castShadow = true;
    root.add(pipe);
    for (let i = 1; i < 6; i++) {
      const p = curve.getPoint(i / 6);
      const band = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.05, 6, 14), iron);
      band.position.copy(p);
      band.lookAt(curve.getPoint(i / 6 + 0.01));
      root.add(band);
      const tp = curve.getPoint(i / 6);
      col.addCircle(tp.x, tp.z, 0.5, { soft: true });
    }
  }

  /* ------------------------------------------------------------- Roost -- */
  const R = V.roost;
  const tents: Array<[number, number, number]> = [[R.x - 10, R.z + 2, 0.5], [R.x - 4, R.z - 4, 1.2], [R.x + 6, R.z - 2, -0.4], [R.x - 15, R.z - 5, 2.8], [R.x - 13, R.z + 14, 3.6]];
  // Canvas on a ridge pole, patched and weighted, guyed out to stakes.
  const canvasMs = ['#a89878', '#9a8c70', '#b0a080', '#8e8068'].map((c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.95, side: THREE.DoubleSide }));
  const patchM = new THREE.MeshStandardMaterial({ color: '#8a2a22', roughness: 0.95, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  const poleM = new THREE.MeshStandardMaterial({ color: '#4a3626', roughness: 0.9 });
  const ropeM = new THREE.MeshStandardMaterial({ color: '#7a6a50', roughness: 1 });
  const tent = (x: number, z: number, rot: number, w: number, l: number, h: number, seed: number) => {
    const g = new THREE.Group();
    const canvasM = canvasMs[seed % canvasMs.length];
    // Each side: a sagging sheet from the ridge to the ground.
    const slant = Math.hypot(w / 2, h);
    const sagAt = (lx: number, ly: number) => {
      const u = lx / l + 0.5, v = ly / slant + 0.5;
      // Sags between the poles and at mid-slope; the hem flares out a little.
      return Math.sin(u * Math.PI) * Math.sin(v * Math.PI) * 0.22 - (1 - v) * (1 - v) * 0.1;
    };
    const sagged = (geo: THREE.BufferGeometry, ox: number, oy: number) => {
      const pos = geo.attributes.position;
      for (let i = 0; i < pos.count; i++) pos.setZ(i, sagAt(pos.getX(i) + ox, pos.getY(i) + oy));
      geo.computeVertexNormals();
      return geo;
    };
    for (const side of [-1, 1]) {
      const sheet = new THREE.Mesh(sagged(new THREE.PlaneGeometry(l, slant, 8, 4), 0, 0), canvasM);
      // Plane x runs along the ridge, plane y up the slope, and its normal
      // points into the tent (so the sag hangs inward) on both sides.
      const X = new THREE.Vector3(0, 0, side), Y = new THREE.Vector3(-side * w / 2 / slant, h / slant, 0);
      sheet.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, X.clone().cross(Y)));
      sheet.position.set(side * w / 4, h / 2, 0);
      g.add(sheet);
      // A red patch or two: the Kerchiefs mend with what they have.
      if (hash1(seed * 7 + side, 3) > 0.35) {
        const px = (hash1(seed, side + 9) - 0.5) * l * 0.55, py = (hash1(seed, side + 11) - 0.5) * slant * 0.4;
        const patch = new THREE.Mesh(sagged(new THREE.PlaneGeometry(0.7 + hash1(seed, side + 5) * 0.5, 0.5, 3, 2), px, py), patchM);
        patch.position.set(px, py, 0);
        sheet.add(patch);
      }
    }
    // Poles: two uprights and the ridge.
    for (const e of [-1, 1]) {
      const up = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.06, h + 0.3, 5), poleM);
      up.position.set(0, (h + 0.3) / 2, e * l / 2);
      g.add(up);
      // Guy ropes from the pole tops to stakes.
      const top = new THREE.Vector3(0, h + 0.15, e * l / 2), stake = new THREE.Vector3(0, 0.1, e * (l / 2 + h * 0.8));
      const rope = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, top.distanceTo(stake), 3), ropeM);
      rope.position.copy(top).lerp(stake, 0.5);
      rope.lookAt(stake);
      rope.rotateX(Math.PI / 2);
      g.add(rope);
      const peg = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.02, 0.4, 4), poleM);
      peg.position.copy(stake);
      g.add(peg);
    }
    const ridge = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, l + 0.4, 5), poleM);
    ridge.rotation.x = Math.PI / 2;
    ridge.position.y = h + 0.02;
    g.add(ridge);
    // The back is closed; the front flap is tied open.
    const endGeo = new THREE.BufferGeometry();
    endGeo.setAttribute('position', new THREE.Float32BufferAttribute([-w / 2, 0, 0, w / 2, 0, 0, 0, h, 0], 3));
    endGeo.computeVertexNormals();
    const back = new THREE.Mesh(endGeo, canvasM);
    back.position.z = -l / 2;
    g.add(back);
    for (const side of [-1, 1]) {
      const flapGeo = new THREE.BufferGeometry();
      flapGeo.setAttribute('position', new THREE.Float32BufferAttribute([0, h, 0, side * w / 2, 0, 0, side * w * 0.42, 0, 0.35], 3));
      flapGeo.computeVertexNormals();
      const flap = new THREE.Mesh(flapGeo, canvasM);
      flap.position.z = l / 2;
      g.add(flap);
    }
    g.traverse((o) => { if ((o as THREE.Mesh).isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    g.position.set(x, kit.y(x, z) - 0.05, z);
    g.rotation.y = rot;
    root.add(g);
    col.addBox(x, z, w / 2 + 0.1, l / 2 + 0.1, -rot);
  };
  tents.forEach(([x, z, rot], i) => tent(x, z, rot, 3.2 + hash1(i, 41) * 0.8, 3.6 + hash1(i, 42) * 1.2, 2.1 + hash1(i, 43) * 0.4, i));
  // Bedrolls, benches and a spit by the fire: people live here.
  kit.bedroll(R.x - 2, R.z + 8, 0.4);
  kit.bedroll(R.x + 4, R.z + 8.5, -0.6);
  kit.log(R.x + 1, R.z + 1.8, 0.1);
  kit.log(R.x + 4.2, R.z + 4.6, 1.5);
  {
    const fx = R.x + 1, fz = R.z + 5, fy = kit.y(fx, fz);
    const spit = new THREE.Group();
    for (const sx of [-0.9, 0.9]) {
      const fork = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.045, 1.2, 5), poleM);
      fork.position.set(sx, 0.6, 0);
      spit.add(fork);
    }
    const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 2.1, 5), poleM);
    bar.rotation.z = Math.PI / 2;
    bar.position.y = 1.15;
    spit.add(bar);
    const meat = new THREE.Mesh(new THREE.SphereGeometry(0.22, 8, 6), new THREE.MeshStandardMaterial({ color: '#6a3420', roughness: 0.6 }));
    meat.scale.set(1.6, 0.9, 0.9);
    meat.position.y = 1.1;
    spit.add(meat);
    spit.position.set(fx, fy, fz);
    spit.rotation.y = 0.3;
    spit.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = true; });
    root.add(spit);
  }
  kit.prop('dungeon', 'sword_shield', R.x - 6.5, R.z + 3, { rot: 0.9, scale: 0.7, r: 0.5 });
  kit.prop('dungeon', 'stool', R.x - 1.8, R.z + 3.4, { rot: 0.3, scale: 0.7 });
  kit.prop('dungeon', 'table_long_broken', R.x + 8, R.z + 2, { rot: 1.1, scale: 0.7, r: 1.2 });
  kit.prop('dungeon', 'banner_thin_red', R.x - 6, R.z - 7, { rot: 0.2, scale: 0.8 });
  kit.prop('dungeon', 'banner_thin_red', R.x + 7, R.z - 8, { rot: -0.3, scale: 0.8 });
  const roostFire = kit.campfire(R.x + 1, R.z + 5, 1.1);
  void roostFire;
  kit.prop('dungeon', 'crates_stacked', V.cargo.x, V.cargo.z, { rot: 0.4, scale: 0.8, r: 1.2 });
  kit.prop('dungeon', 'box_stacked', V.cargo.x - 3, V.cargo.z + 1.5, { rot: -0.2, scale: 0.5, r: 1.1 });
  kit.prop('dungeon', 'trunk_large_B', V.cargo.x + 2.2, V.cargo.z - 1.4, { rot: 1.2, scale: 0.8, r: 0.6, tag: 'strongbox' });
  kit.prop('dungeon', 'barrel_large', R.x + 14, R.z - 6, { scale: 0.7, r: 0.7, tag: 'powder' });
  kit.prop('dungeon', 'barrel_small_stack', R.x + 15.5, R.z - 4, { scale: 0.7, r: 0.8, tag: 'powder' });
  kit.prop('hex_nature', 'flag_red', R.x - 2, R.z - 8, { scale: 10 });
  kit.prop('hex_nature', 'flag_red', R.x + 10, R.z - 9, { scale: 10 });
  kit.prop('dungeon', 'chair', V.redcowl.x, V.redcowl.z + 1, { rot: Math.PI, scale: 0.8 });
  kit.prop('dungeon', 'table_small_decorated_A', V.redcowl.x + 1.5, V.redcowl.z + 0.5, { scale: 0.8, r: 0.6 });
  // Three cages: iron bars on a wooden base.
  const cageBars: THREE.Object3D[] = [];
  for (let i = 0; i < 3; i++) {
    const cx = V.cages.x + i * 3.2, cz = V.cages.z - i * 0.8;
    const cage = new THREE.Group();
    const iron = new THREE.MeshStandardMaterial({ color: '#2e2a28', roughness: 0.6, metalness: 0.6 });
    const base = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.2, 2.2), wood);
    base.position.y = 0.1;
    cage.add(base);
    const top = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.12, 2.2), wood);
    top.position.y = 2.3;
    cage.add(top);
    const bars = new THREE.Group();
    for (let k = 0; k < 16; k++) {
      const side = Math.floor(k / 4), t = (k % 4) / 3 - 0.5;
      const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 2.1, 5), iron);
      const px = side === 0 ? t * 2 : side === 1 ? 1 : side === 2 ? -t * 2 : -1;
      const pz = side === 0 ? -1 : side === 1 ? t * 2 : side === 2 ? 1 : -t * 2;
      bar.position.set(px, 1.2, pz);
      bars.add(bar);
    }
    cage.add(bars);
    cageBars.push(bars);
    cage.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = true; });
    cage.position.set(cx, kit.y(cx, cz), cz);
    cage.rotation.y = 0.2;
    root.add(cage);
    col.addBox(cx, cz, 1.1, 1.1, -0.2, { tag: `cage:${i}` });
  }

  /* ------------------------------------------------------------ Vault -- */
  const VV = V.vault;
  const vaultGroup = new THREE.Group();
  const black = new THREE.MeshStandardMaterial({ color: '#16141a', roughness: 0.35, metalness: 0.3 });
  const frameStone = new THREE.MeshStandardMaterial({ color: '#3a3640', roughness: 0.8 });
  const doorM = new THREE.Mesh(new THREE.BoxGeometry(4.2, 5.4, 0.6), black);
  doorM.position.y = 2.7;
  vaultGroup.add(doorM);
  for (const sx of [-2.6, 2.6]) {
    const jamb = new THREE.Mesh(new THREE.BoxGeometry(1.0, 6.4, 1.2), frameStone);
    jamb.position.set(sx, 3.2, 0.1);
    vaultGroup.add(jamb);
  }
  const lintel = new THREE.Mesh(new THREE.BoxGeometry(6.4, 1.2, 1.4), frameStone);
  lintel.position.set(0, 6.6, 0.1);
  vaultGroup.add(lintel);
  const sigil = new THREE.Mesh(new THREE.RingGeometry(0.7, 0.9, 7), new THREE.MeshBasicMaterial({ color: new THREE.Color('#b08aff').multiplyScalar(2), side: THREE.DoubleSide }));
  sigil.position.set(0, 3.1, 0.32);
  vaultGroup.add(sigil);
  const sigilInner = new THREE.Mesh(new THREE.CircleGeometry(0.35, 7), new THREE.MeshBasicMaterial({ color: new THREE.Color('#6a4aa0').multiplyScalar(1.5) }));
  sigilInner.position.set(0, 3.1, 0.32);
  vaultGroup.add(sigilInner);
  vaultGroup.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = o.receiveShadow = true; });
  vaultGroup.position.set(VV.x, kit.y(VV.x, VV.z) - 0.2, VV.z);
  vaultGroup.rotation.y = Math.PI * 0.2;
  root.add(vaultGroup);
  col.addBox(VV.x, VV.z, 3.3, 1.0, -Math.PI * 0.2);
  kit.source(VV.x + 1, kit.y(VV.x, VV.z) + 3, VV.z + 2, 0xa07aff, 6, 10, 0.08, [sigil]);
  kit.prop('halloween', 'skull', VV.x + 3.5, VV.z + 3.5, { rot: 1, scale: 0.4 });
  kit.prop('halloween', 'ribcage', VV.x + 4.2, VV.z + 2.6, { rot: 2, scale: 0.8 });
  kit.prop('halloween', 'bone_A', VV.x + 3.1, VV.z + 4.4, { rot: 0.5, scale: 0.8 });

  /* ---------------------------------------------------------- Sinkhole -- */
  const S = V.sinkhole;
  const thing = new THREE.Group();
  const thingHead = new THREE.Group();
  {
    // Coiled round the floor of the pit, three-quarters of a turn, going
    // under the earth at the tail and lifting its head up the far slope.
    const floorY = kit.y(S.x, S.z);
    const chitin = new THREE.MeshStandardMaterial({ color: '#d8d0c2', roughness: 0.5, metalness: 0.02, emissive: '#1c1814' });
    const shell = new THREE.MeshStandardMaterial({ color: '#c4b8a2', roughness: 0.62, metalness: 0.02, emissive: '#16120d' });
    const flesh = new THREE.MeshStandardMaterial({ color: '#4a3a38', roughness: 0.55 });
    const joint = new THREE.MeshStandardMaterial({ color: '#8a7a70', roughness: 0.6 });
    const eyeM = new THREE.MeshStandardMaterial({ color: '#0c0a10', roughness: 0.08, metalness: 0.4 });
    const path: THREE.Vector3[] = [];
    for (let i = 0; i <= 10; i++) {
      const t = i / 10, a = -0.6 + t * Math.PI * 1.55;
      const r = 5.6 + Math.sin(t * 5) * 0.4;
      // Tail below ground, body along the floor, the head end up the slope.
      const lift = t < 0.18 ? -2.2 * (1 - t / 0.18) : t > 0.78 ? ((t - 0.78) / 0.22) ** 1.5 * 3.4 : 0;
      path.push(new THREE.Vector3(Math.cos(a) * r, lift, Math.sin(a) * r));
    }
    const curve = new THREE.CatmullRomCurve3(path);
    const N = 17;
    for (let i = 0; i < N; i++) {
      const t = i / (N - 1);
      const p = curve.getPoint(t), tan = curve.getTangent(t);
      const r = 1.3 + Math.sin(Math.min(1, t * 1.3) * Math.PI) * 1.2;
      const seg = new THREE.Group();
      // Dark flesh between the plates, so it reads as segments.
      const body = new THREE.Mesh(new THREE.SphereGeometry(r, 18, 12), flesh);
      body.scale.set(0.6, 0.74, 1);
      seg.add(body);
      // An armoured plate over the back of each segment, a ridge down it.
      const plate = new THREE.Mesh(new THREE.SphereGeometry(r * 1.07, 18, 8, 0, Math.PI * 2, 0, Math.PI * 0.42), shell);
      plate.scale.set(0.68, 0.84, 0.7);
      seg.add(plate);
      const ridge = new THREE.Mesh(new THREE.ConeGeometry(r * 0.16, r * 0.5, 4), flesh);
      ridge.position.y = r * 0.82;
      ridge.rotation.x = -0.5;
      seg.add(ridge);
      // Folded legs: a pair to a segment, each bent at the knee.
      for (const side of [-1, 1]) {
        const upper = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.16, r * 1.3, 5), joint);
        upper.position.set(side * r * 0.62, -r * 0.1, 0);
        upper.rotation.z = side * 1.05;
        seg.add(upper);
        const lower = new THREE.Mesh(new THREE.ConeGeometry(0.1, r * 1.5, 5), chitin);
        lower.position.set(side * r * 1.05, -r * 0.55, r * 0.2);
        lower.rotation.set(0.5, 0, side * -0.35);
        seg.add(lower);
      }
      seg.position.copy(p).setY(p.y + r * 0.35);
      seg.lookAt(seg.position.clone().add(tan));
      thing.add(seg);
    }
    // The head: heavier plates, mandibles, a cluster of dead eyes.
    const hp = curve.getPoint(1), ht = curve.getTangent(1);
    const skull = new THREE.Mesh(new THREE.SphereGeometry(1.9, 18, 12), shell);
    skull.scale.set(0.95, 0.8, 1.15);
    thingHead.add(skull);
    const crest = new THREE.Mesh(new THREE.SphereGeometry(1.95, 18, 8, 0, Math.PI * 2, 0, Math.PI * 0.3), flesh);
    crest.scale.set(1.0, 0.9, 1.2);
    crest.position.set(0, 0.1, -0.35);
    thingHead.add(crest);
    for (const side of [-1, 1]) {
      // Mandibles: long, curved inward, the tips nearly touching.
      const mand = new THREE.Mesh(new THREE.ConeGeometry(0.28, 2.6, 6), flesh);
      mand.position.set(side * 0.85, -0.55, 2.3);
      mand.rotation.set(Math.PI / 2 - 0.2, 0, side * -0.45);
      thingHead.add(mand);
      for (let k = 0; k < 3; k++) {
        const eye = new THREE.Mesh(new THREE.SphereGeometry(0.22 - k * 0.04, 10, 8), eyeM);
        eye.position.set(side * (0.55 + k * 0.32), 0.55 - k * 0.12, 1.65 - k * 0.25);
        thingHead.add(eye);
      }
    }
    thingHead.position.copy(hp).setY(hp.y + 1.2).addScaledVector(ht, 1.5);
    thingHead.lookAt(thingHead.position.clone().add(ht).add(new THREE.Vector3(0, 0.15, 0)));
    thing.add(thingHead);
    thing.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = o.receiveShadow = true; });
    thing.position.set(S.x, floorY - 0.6, S.z);
    thing.rotation.y = 0.8;
    root.add(thing);
    col.addCircle(S.x, S.z, 7.5);
    // A cold light at the bottom, as if the pit remembered being deeper.
    kit.source(S.x, floorY + 2.5, S.z, 0x8a90ff, 3.5, 14, 0.12);
    // What the diggers left at the rim: a windlass, a rope going down,
    // stakes with rags on them to say keep away.
    const rimA = 2.2, rx = S.x + Math.cos(rimA) * 13.5, rz = S.z + Math.sin(rimA) * 13.5;
    const woodD = new THREE.MeshStandardMaterial({ color: '#4e3a2a', roughness: 0.9 });
    const windlass = new THREE.Group();
    for (const sx of [-0.9, 0.9]) {
      const leg = new THREE.Mesh(new THREE.BoxGeometry(0.16, 1.5, 0.16), woodD);
      leg.position.set(sx, 0.75, 0);
      windlass.add(leg);
    }
    const drum = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.26, 1.8, 10), woodD);
    drum.rotation.z = Math.PI / 2;
    drum.position.y = 1.35;
    windlass.add(drum);
    const coil = new THREE.Mesh(new THREE.CylinderGeometry(0.33, 0.33, 1.0, 12), new THREE.MeshStandardMaterial({ color: '#8a7a5a', roughness: 1 }));
    coil.rotation.z = Math.PI / 2;
    coil.position.y = 1.35;
    windlass.add(coil);
    windlass.position.set(rx, kit.y(rx, rz), rz);
    windlass.lookAt(S.x, windlass.position.y, S.z);
    windlass.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = true; });
    root.add(windlass);
    col.addCircle(rx, rz, 1.0);
    // The rope hangs down the slope and stops short of the bottom.
    const ropePts: THREE.Vector3[] = [];
    for (let i = 0; i <= 12; i++) {
      const d = 13 - i * 0.62, x = S.x + Math.cos(rimA) * d, z = S.z + Math.sin(rimA) * d;
      ropePts.push(new THREE.Vector3(x, kit.y(x, z) + (i === 0 ? 1.35 : 0.12), z));
    }
    const rope = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(ropePts), 40, 0.045, 5), new THREE.MeshStandardMaterial({ color: '#8a7a5a', roughness: 1 }));
    rope.castShadow = true;
    root.add(rope);
    const rag = new THREE.MeshStandardMaterial({ color: '#a8a090', roughness: 1, side: THREE.DoubleSide });
    for (let i = 0; i < 7; i++) {
      const a = rimA + 0.5 + i * 0.62, d = 15.5 + hash1(i, 81) * 1.2;
      const x = S.x + Math.cos(a) * d, z = S.z + Math.sin(a) * d;
      const stake = new THREE.Group();
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.07, 1.7, 5), woodD);
      pole.position.y = 0.85;
      stake.add(pole);
      const cloth = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.5, 1, 2), rag);
      cloth.position.set(0.18, 1.35, 0);
      cloth.rotation.y = hash1(i, 82) * 0.6;
      stake.add(cloth);
      stake.position.set(x, kit.y(x, z), z);
      stake.rotation.set((hash1(i, 83) - 0.5) * 0.3, a, (hash1(i, 84) - 0.5) * 0.3);
      stake.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = true; });
      root.add(stake);
    }
    // Broken slabs of turf slumped over the lip.
    for (let i = 0; i < 12; i++) {
      const a = hash1(i, 91) * Math.PI * 2, d = 10.5 + hash1(i, 92) * 3;
      const x = S.x + Math.cos(a) * d, z = S.z + Math.sin(a) * d;
      kit.flora.add(hash1(i, 93) < 0.5 ? 'rock' : 'boulder', x, kit.y(x, z) - 0.3, z, a, 0.5 + hash1(i, 94) * 0.5);
    }
  }
  for (let i = 0; i < 18; i++) {
    const a = (i / 18) * Math.PI * 2;
    const x = S.x + Math.cos(a) * 16, z = S.z + Math.sin(a) * 16;
    if (i % 5 === 0) continue;
    col.addCircle(x, z, 1.8, { soft: true });
    if (i % 2) kit.flora.add('rock', x, kit.y(x, z), z, a, 1.1);
  }

  /* --------------------------------------------------------- Moon Grove -- */
  const G = V.grove;
  const brambles: VergeBuild['brambles'] = [];
  const brambleMat = floraMaterial({ wind: 0.25, rim: 0.2, occlude: false, flatShading: true });
  for (let i = 0; i < 9; i++) {
    const t = i / 8;
    const x = V.brambles.x - 7 + t * 14 * 0.6, z = V.brambles.z - 5 + t * 12;
    const mesh = new THREE.Mesh(bushGeometry(30 + i, 1.4, 'bramble'), brambleMat);
    mesh.position.set(x, kit.y(x, z), z);
    mesh.rotation.y = i * 1.3;
    mesh.scale.setScalar(1.9);
    mesh.castShadow = true;
    root.add(mesh);
    brambles.push({ mesh, collider: col.addCircle(x, z, 1.6, { tag: `bramble:${i}` }).id, x, z });
  }
  // Rocks close the rest of the grove.
  for (let i = 0; i < 14; i++) {
    const a = Math.PI * 0.45 + (i / 13) * Math.PI * 1.25;
    const x = G.x + Math.cos(a) * 15, z = G.z + Math.sin(a) * 13;
    kit.flora.add('boulder', x, kit.y(x, z) - 0.4, z, a, 0.8 + hash1(i, 3) * 0.4);
    col.addCircle(x, z, 2.4);
  }
  for (let i = 0; i < 26; i++) {
    const a = hash1(i, 61) * 6.28, d = hash1(i, 62) * 10;
    const x = G.x + Math.cos(a) * d, z = G.z + Math.sin(a) * d;
    const petal = new THREE.Mesh(new THREE.SphereGeometry(0.12, 6, 4), new THREE.MeshBasicMaterial({ color: new THREE.Color('#bfe0ff').multiplyScalar(2.2) }));
    petal.position.set(x, kit.y(x, z) + 0.35, z);
    root.add(petal);
  }
  kit.source(G.x, kit.y(G.x, G.z) + 3, G.z, 0xa8d0ff, 10, 16, 0.05);
  kit.prop('halloween', 'shrine', G.x, G.z - 2, { rot: 0.4, scale: 0.9, r: 0.6 });

  /* ----------------------------------------------------- road furniture -- */
  kit.lamp(-120, 13, -Math.PI / 2, false);
  kit.lamp(-30, 18, -Math.PI / 2, false);
  kit.lamp(60, -10, Math.PI / 2, false);
  kit.prop('halloween', 'post', 26, 4, { rot: -0.3, scale: 0.8, r: 0.25 });
  // The road east is washed out.
  for (let i = 0; i < 7; i++) {
    const x = 132 + hash1(i, 71) * 6, z = -4 + i * 3;
    kit.flora.add('boulder', x, kit.y(x, z) - 0.5, z, i, 1 + hash1(i, 72) * 0.5);
    col.addCircle(x, z, 2.6);
  }

  flora.finalize();
  root.add(flora.group);

  const zone: ZoneBuild = {
    id: 'verge', terrain, grass, collision: col, root, atmosphere: PRESETS.day,
    map: {
      water: (x, z) => { const n = streamIx.nearest(x, z); return n.d < 3.4 && terrain.heightAt(x, z) < waterLine(n.s); },
      flora: kit.flora.marks,
    },
    start: { x: V.entry.x, z: V.entry.z, facing: Math.PI / 2 },
    tick: (dt, t, fx, fz) => {
      waterUniforms.uTime.value = t;
      kit.tick(dt, fx, fz);
      pumpWheel.rotation.x += dt * (pumpWheel.userData.stopped ? 0 : 0.8);
      sigil.rotation.z += dt * 0.1;
      // Probably dead. Every so often, the head settles, as if it breathed.
      const breath = Math.max(0, Math.sin(t * 0.21)) ** 12;
      thingHead.rotation.z = breath * 0.05;
      thingHead.position.y += (breath * 0.12 - (thingHead.userData.b ?? 0));
      thingHead.userData.b = breath * 0.12;
    },
  };
  return { zone, kit, roadDist, streamDist, postFire, blindFire, brambles, pumpWheel, thing, cageBars, vaultGlow: sigil };
}
