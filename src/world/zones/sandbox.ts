import * as THREE from 'three';
import { PRESETS, type PresetName } from '@/render/atmosphere';
import { Terrain, type TerrainPaint } from '@/render/terrain';
import { Grass } from '@/render/grass';
import { FloraField } from '@/render/scatter';
import { Assets, type PropPack } from '@/render/assets';
import { CollisionWorld } from '@/sim/collision';
import { Noise2D, distToSegment, smoothstep, hash2, hash1 } from '@/core/math';
import type { ZoneBuild } from '@/game/scene';

/* A test clearing on a forest road: terrain, grass, forest, rocks, a little
 * shrine - and colliders for all of it, so the horde has to go round. */

export function buildSandboxZone(time: PresetName = 'night', grassDensity = 1): ZoneBuild {
  const root = new THREE.Group();
  const noise = new Noise2D(7);
  const road: Array<[number, number]> = [[-80, 30], [-40, 12], [-10, 4], [15, -6], [40, -20], [80, -26]];
  const roadDist = (x: number, z: number) => {
    let d = 1e9;
    for (let i = 0; i < road.length - 1; i++) d = Math.min(d, distToSegment(x, z, road[i][0], road[i][1], road[i + 1][0], road[i + 1][1]));
    return d;
  };
  const terrain = new Terrain({
    size: 180, resolution: 181,
    height: (x, z) => {
      let h = noise.fbm(x * 0.018, z * 0.018, 4) * 2.2 + noise.ridged(x * 0.008 + 3, z * 0.008, 3) * 3;
      h = THREE.MathUtils.lerp(h * 0.4, h, smoothstep(2, 9, roadDist(x, z)));
      h += smoothstep(60, 88, Math.max(Math.abs(x), Math.abs(z))) * 14;
      return h;
    },
    paint: (x: number, z: number, o: TerrainPaint) => {
      const rd = roadDist(x, z);
      o.dirt = 1 - smoothstep(1.6, 3.4, rd + noise.noise(x * 0.3, z * 0.3) * 0.8);
      const plaza = Math.hypot(x - 2, z + 1);
      o.stone = 1 - smoothstep(4.5, 7.5, plaza + noise.noise(x * 0.25, z * 0.25) * 1.2);
      o.dirt = Math.max(o.dirt, (1 - smoothstep(6, 11, plaza)) * 0.9);
      o.blight = 1 - smoothstep(4, 12, Math.hypot(x + 18, z + 16) + noise.noise(x * 0.2, z * 0.2) * 3);
      o.mud = 1 - smoothstep(1.5, 4, Math.hypot(x - 14, z - 10) + noise.noise(x * 0.4, z * 0.4) * 1.5);
    },
  });
  root.add(terrain.mesh);
  const grass = new Grass(terrain, { density: grassDensity });
  root.add(grass.mesh);
  const col = new CollisionWorld(180);
  col.bound = 70;

  const flora = new FloraField(700);
  for (let gz = -85; gz < 85; gz += 3.6) {
    for (let gx = -85; gx < 85; gx += 3.6) {
      const x = gx + (hash2(gx * 10, gz * 10, 1) - 0.5) * 3.2;
      const z = gz + (hash2(gx * 10, gz * 10, 2) - 0.5) * 3.2;
      const rd = roadDist(x, z);
      const clearing = Math.hypot(x - 2, z + 1);
      const forest = noise.fbm(x * 0.03 + 11, z * 0.03, 3);
      const y = terrain.heightAt(x, z);
      const rot = hash2(gx, gz, 5) * Math.PI * 2;
      const h = hash2(gx, gz, 6);
      const blighted = Math.hypot(x + 18, z + 16) < 14;
      const edge = rd > 4.5 && clearing > 13;
      if (edge && h < 0.18 && forest > -0.25) flora.add(h < 0.05 ? 'berry' : 'bush', x, y, z, rot, 0.8 + h * 2);
      if (hash2(gx, gz, 8) < 0.06 && rd > 2.5 && clearing > 8) {
        const big = hash2(gx, gz, 9) < 0.2;
        const s = 0.6 + h;
        flora.add(big ? 'boulder' : 'rock', x + 1.3, terrain.heightAt(x + 1.3, z), z, rot, s);
        col.addCircle(x + 1.3, z, (big ? 2.2 : 0.85) * s);
      }
      if (rd < 6 || clearing < 16 || forest < -0.1) continue;
      if (hash2(gx * 7, gz * 7, 3) > 0.5 + forest * 0.45) continue;
      const sc = 0.8 + hash2(gx, gz, 4) * 0.5;
      if (blighted) flora.add(h < 0.5 ? 'dead' : 'sick', x, y - 0.1, z, rot, sc);
      else if (h < 0.07) flora.add('dead', x, y - 0.1, z, rot, sc);
      else if (forest > 0.15 || h < 0.55) flora.add('pine', x, y - 0.15, z, rot, sc);
      else if (h < 0.62) flora.add('autumn', x, y - 0.1, z, rot, sc);
      else flora.add('broadleaf', x, y - 0.1, z, rot, sc);
      col.addCircle(x, z, 0.45 * sc);
    }
  }
  for (let i = 0; i < 400; i++) {
    const x = (hash1(i, 31) - 0.5) * 160, z = (hash1(i, 32) - 0.5) * 160;
    if (Math.hypot(x - 2, z + 1) < 7.5) continue;
    flora.add('pebble', x, terrain.heightAt(x, z), z, hash1(i, 33) * 6.28, 0.6 + hash1(i, 34));
  }
  flora.finalize();
  root.add(flora.group);

  const place = (pack: PropPack, name: string, x: number, z: number, rot = 0, s = 0.8, r = 0) => {
    const o = Assets.prop(pack, name);
    o.position.set(x, terrain.heightAt(x, z), z);
    o.rotation.y = rot;
    o.scale.setScalar(s);
    root.add(o);
    if (r > 0) col.addCircle(x, z, r);
    return o;
  };
  place('halloween', 'shrine_candles', 2, -2, 0.3, 0.8, 0.6);
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2;
    place('halloween', i % 3 === 0 ? 'gravestone' : 'gravemarker_A', 2 + Math.cos(a) * 5, -1 + Math.sin(a) * 5, -a + Math.PI / 2, 0.8, i % 3 === 0 ? 0.45 : 0);
  }
  place('halloween', 'lantern_standing', -6, 6, 0, 0.8, 0.3);
  place('halloween', 'lantern_standing', 9, -4, 0, 0.8, 0.3);
  place('dungeon', 'barrel_large', 12, 2, 0, 0.5, 0.5);
  place('dungeon', 'box_stacked', 13.5, 3.5, 0.4, 0.5, 0.7);

  const lights: THREE.PointLight[] = [];
  for (const [x, z, c] of [[2, -2, 0xffa050], [-6, 6, 0xffb060], [9, -4, 0xffb060]] as const) {
    const l = new THREE.PointLight(c, 7, 14, 1.6);
    l.position.set(x, terrain.heightAt(x, z) + 1.4, z);
    root.add(l);
    lights.push(l);
  }

  return {
    id: 'sandbox', terrain, grass, collision: col, root, atmosphere: PRESETS[time], start: { x: 0, z: 7 },
    tick: (_dt, t) => lights.forEach((l, i) => { l.intensity = 7 + Math.sin(t * 9 + i * 3) * 0.6 + Math.sin(t * 23 + i) * 0.4; }),
  };
}
