import * as THREE from 'three';
import type { Renderer } from '@/render/renderer';
import { Atmosphere, PRESETS, type PresetName } from '@/render/atmosphere';
import { Terrain, type TerrainPaint } from '@/render/terrain';
import { Grass } from '@/render/grass';
import { FollowCamera } from '@/render/camera';
import { CharacterView } from '@/render/characterView';
import { tickWind } from '@/render/instancing';
import { FloraField } from '@/render/scatter';
import { floraUniforms, setOccluder } from '@/render/flora';
import { Assets, type PropPack } from '@/render/assets';
import { Input } from '@/core/input';
import { Noise2D, distToSegment, smoothstep, hash2, hash1, clamp } from '@/core/math';

/* Development scene for judging the look: a moonlit clearing on a forest
 * road. ?dev=sandbox&time=night */

export function sandbox(r: Renderer, params: URLSearchParams) {
  const atmo = new Atmosphere(r);
  atmo.set(PRESETS[(params.get('time') as PresetName) || 'night']);
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
      const rd = roadDist(x, z);
      h = THREE.MathUtils.lerp(h * 0.4, h, smoothstep(2, 9, rd));
      const edge = Math.max(Math.abs(x), Math.abs(z));
      h += smoothstep(60, 88, edge) * 14;
      return h;
    },
    paint: (x: number, z: number, o: TerrainPaint) => {
      const rd = roadDist(x, z);
      o.dirt = 1 - smoothstep(1.6, 3.4, rd + noise.noise(x * 0.3, z * 0.3) * 0.8);
      const plaza = Math.hypot(x - 2, z + 1);
      o.stone = 1 - smoothstep(5.5, 6.5, plaza);
      o.dirt = Math.max(o.dirt, (1 - smoothstep(6, 11, plaza)) * 0.9);
      o.blight = 1 - smoothstep(4, 12, Math.hypot(x + 18, z + 16) + noise.noise(x * 0.2, z * 0.2) * 3);
      o.mud = 1 - smoothstep(1.5, 4, Math.hypot(x - 14, z - 10) + noise.noise(x * 0.4, z * 0.4) * 1.5);
    },
  });
  r.scene.add(terrain.mesh);
  const grass = new Grass(terrain, { density: r.spec.grassDensity });
  r.scene.add(grass.mesh);

  // Forest: pines and broadleaves off the road, dead and sick trees in the
  // blight, bushes at the forest edge, rocks everywhere.
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
      if (hash2(gx, gz, 8) < 0.07 && rd > 2.5) flora.add(hash2(gx, gz, 9) < 0.2 ? 'boulder' : 'rock', x + 1.3, terrain.heightAt(x + 1.3, z), z, rot, 0.6 + h);
      if (rd < 6 || clearing < 16 || forest < -0.1) continue;
      if (hash2(gx * 7, gz * 7, 3) > 0.5 + forest * 0.45) continue;
      const sc = 0.8 + hash2(gx, gz, 4) * 0.5;
      if (blighted) flora.add(h < 0.5 ? 'dead' : 'sick', x, y - 0.1, z, rot, sc);
      else if (h < 0.07) flora.add('dead', x, y - 0.1, z, rot, sc);
      else if (forest > 0.15 || h < 0.55) flora.add('pine', x, y - 0.15, z, rot, sc);
      else if (h < 0.62) flora.add('autumn', x, y - 0.1, z, rot, sc);
      else flora.add('broadleaf', x, y - 0.1, z, rot, sc);
    }
  }
  for (let i = 0; i < 400; i++) {
    const x = (hash1(i, 31) - 0.5) * 160, z = (hash1(i, 32) - 0.5) * 160;
    if (Math.hypot(x - 2, z + 1) < 6.5) continue;
    flora.add('pebble', x, terrain.heightAt(x, z), z, hash1(i, 33) * 6.28, 0.6 + hash1(i, 34));
  }
  flora.finalize();
  r.scene.add(flora.group);

  // A few scattered props to judge scale.
  const place = (pack: PropPack, name: string, x: number, z: number, rot = 0, s = 0.8) => {
    const o = Assets.prop(pack, name);
    o.position.set(x, terrain.heightAt(x, z), z);
    o.rotation.y = rot;
    o.scale.setScalar(s);
    r.scene.add(o);
    return o;
  };
  place('halloween', 'shrine_candles', 2, -2, 0.3);
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2;
    place('halloween', i % 3 === 0 ? 'gravestone' : 'gravemarker_A', 2 + Math.cos(a) * 5, -1 + Math.sin(a) * 5, -a + Math.PI / 2);
  }
  place('halloween', 'lantern_standing', -6, 6);
  place('halloween', 'lantern_standing', 9, -4);
  place('dungeon', 'barrel_large', 12, 2, 0, 0.5);
  place('dungeon', 'box_stacked', 13.5, 3.5, 0.4, 0.5);

  // Warm light pools: the shrine candles and the two lanterns.
  const lights: THREE.PointLight[] = [];
  for (const [x, z, c, i] of [[2, -2, 0xffa050, 6], [-6, 6, 0xffb060, 8], [9, -4, 0xffb060, 8]] as const) {
    const l = new THREE.PointLight(c, i, 14, 1.6);
    l.position.set(x, terrain.heightAt(x, z) + 1.4, z);
    r.scene.add(l);
    lights.push(l);
  }

  // The survivor.
  const hero = new CharacterView('knight');
  hero.showOnly(['1H_Sword', 'Round_Shield', 'Knight_Cape']);
  r.scene.add(hero.root);
  const pos = new THREE.Vector3(0, 0, 6);
  const vel = new THREE.Vector3();
  const cam = new FollowCamera(r.camera);
  if (params.get('camdist')) cam.targetDistance = Number(params.get('camdist'));
  if (params.get('pitch')) cam.pitch = THREE.MathUtils.degToRad(Number(params.get('pitch')));
  if (params.get('px')) { pos.x = Number(params.get('px')); pos.z = Number(params.get('pz') || 0); }
  // The survivor carries their own small light: the ember they burn.
  const carried = new THREE.PointLight(0xffb070, 5, 11, 1.4);
  carried.castShadow = false;
  r.scene.add(carried);
  const scripted = params.get('walk');

  return (dt: number, t: number) => {
    Input.poll();
    let mx = Input.moveX, mz = Input.moveZ;
    if (scripted) { mx = Math.cos(t * 0.4); mz = Math.sin(t * 0.4); }
    const speed = 5.2;
    vel.x = THREE.MathUtils.damp(vel.x, mx * speed, 12, dt);
    vel.z = THREE.MathUtils.damp(vel.z, mz * speed, 12, dt);
    pos.x = clamp(pos.x + vel.x * dt, -70, 70);
    pos.z = clamp(pos.z + vel.z * dt, -70, 70);
    pos.y = terrain.heightAt(pos.x, pos.z);
    hero.root.position.copy(pos);
    carried.position.set(pos.x, pos.y + 2.4, pos.z + 0.4);
    carried.intensity = 5 + Math.sin(t * 7.3) * 0.25 + Math.sin(t * 17.1) * 0.15;
    const sp = Math.hypot(vel.x, vel.z);
    if (sp > 0.3) hero.face(Math.atan2(vel.x, vel.z));
    hero.locomotion(sp);
    hero.update(dt);
    cam.update(dt, pos.x, pos.y, pos.z, vel.x, vel.z);
    atmo.follow(cam.focus.x, cam.focus.y, cam.focus.z);
    atmo.update(t, r.camera.position);
    grass.setPusher(0, pos.x, pos.z, 1.1, 1);
    grass.update(t, cam.focus.x, cam.focus.z);
    terrain.time = t;
    tickWind(t);
    floraUniforms.uTime.value = t;
    // Where the survivor is on screen, for the occlusion cut-out.
    const sp3 = new THREE.Vector3(pos.x, pos.y + 1, pos.z).project(r.camera);
    const buf = r.gl.getDrawingBufferSize(new THREE.Vector2());
    const depth = r.camera.position.distanceTo(new THREE.Vector3(pos.x, pos.y + 1, pos.z));
    setOccluder((sp3.x * 0.5 + 0.5) * buf.x, (sp3.y * 0.5 + 0.5) * buf.y, depth * 0.98, buf.y * 0.14);
    lights.forEach((l, i) => { l.intensity = 7 + Math.sin(t * 9 + i * 3) * 0.6 + Math.sin(t * 23 + i) * 0.4; });
  };
}
