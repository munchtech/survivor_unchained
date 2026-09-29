import * as THREE from 'three';
import type { ParticleSystem } from '../particles';
import type { Family } from '@/sim/types';

const WHITE = new THREE.Color(1, 1, 1);

/* Gore: what a blade and a fire do to the things they kill.
 *
 *   - sprays: a hit on anything that bleeds throws blood (streaks and
 *     droplets, falling); on the dead, bone chips and grave dust;
 *   - splats: blood on the ground, spattered by hits and pooled under the
 *     fallen, darkening as it dries and fading after a while; flat
 *     instanced quads cut into ragged shapes in the shader, lit like the
 *     ground so it is not bright at night;
 *   - gibs: a blow far bigger than what it killed bursts the body; meat,
 *     bone and the odd skull are thrown with simple physics, bounce, settle,
 *     bleed where they land, and sink into the ground in their time.
 *
 * `level` scales all of it (the Gore setting): 1 full, 0.35 reduced (a
 * little blood, nothing thrown), 0 none. */

type Blood = { spray: THREE.Color; pool: THREE.Color; flesh: boolean };

const RED: Blood = { spray: new THREE.Color('#8e0c0c'), pool: new THREE.Color('#4a0404'), flesh: true };
const ICHOR: Blood = { spray: new THREE.Color('#3a4a10'), pool: new THREE.Color('#1c240a'), flesh: true };
const TAR: Blood = { spray: new THREE.Color('#2a1a10'), pool: new THREE.Color('#140c08'), flesh: true };

/** What a family bleeds (null: it does not). */
export function bloodOf(family: Family, def = ''): Blood | null {
  if (family === 'undead' || family === 'elemental' || family === 'construct') return null;
  if (family === 'blighted' || /blight/.test(def)) return ICHOR;
  if (family === 'lampling') return TAR;
  return RED;
}

/* ------------------------------------------------------------ splats -- */

const SPLAT_MAX = 420;

class SplatLayer {
  readonly mesh: THREE.InstancedMesh;
  private aGore: THREE.InstancedBufferAttribute;
  private next = 0;
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private up = new THREE.Vector3(0, 1, 0);
  readonly uniforms = { uTime: { value: 0 } };

  constructor() {
    const g = new THREE.PlaneGeometry(1, 1);
    g.rotateX(-Math.PI / 2);
    const mat = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.32, metalness: 0, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 });
    mat.onBeforeCompile = (sh) => {
      Object.assign(sh.uniforms, this.uniforms);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', `#include <common>
attribute vec4 aGore; // seed, born, life, kind
varying vec4 vGore;
varying vec2 vQuad;`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
vGore = aGore;
vQuad = position.xz * 2.0;`);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
uniform float uTime;
varying vec4 vGore;
varying vec2 vQuad;
float gh(float n) { return fract(sin(n) * 43758.5453); }`)
        .replace('#include <color_fragment>', `#include <color_fragment>
{
  float seed = vGore.x, age = uTime - vGore.y, life = vGore.z;
  float k = clamp(age / life, 0.0, 1.0);
  // A pool spreads for a few seconds; a splat is there at once.
  float grow = vGore.w > 0.5 ? smoothstep(0.0, 4.0, age) * 0.75 + 0.25 : 1.0;
  vec2 p = vQuad / grow;
  float a = atan(p.y, p.x), r = length(p);
  // A ragged edge: a few lobes, and finer teeth on them.
  float edge = 0.48 + 0.12 * sin(a * 3.0 + seed * 6.0) + 0.07 * sin(a * 7.0 + seed * 13.0) + 0.04 * sin(a * 17.0 + seed * 3.0);
  float body = 1.0 - smoothstep(edge - 0.03, edge + 0.02, r);
  // Flung drops around it.
  float drops = 0.0;
  for (int i = 0; i < 6; i++) {
    float fi = float(i);
    float da = gh(seed * 7.1 + fi * 1.7) * 6.2832;
    float dr = 0.55 + gh(seed * 3.3 + fi) * 0.4;
    float ds = 0.03 + gh(seed * 9.7 + fi * 2.3) * 0.06;
    drops = max(drops, 1.0 - smoothstep(ds * 0.7, ds, length(p - vec2(cos(da), sin(da)) * dr)));
  }
  float shape = max(body, drops * (vGore.w > 0.5 ? 0.0 : 1.0));
  if (shape < 0.01) discard;
  // Wet and dark at the middle, thinner at the rim; it dries brown.
  float dry = smoothstep(0.1, 0.7, k);
  diffuseColor.rgb *= mix(0.75, 1.15, smoothstep(0.1, edge, r));
  diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.8, 0.62, 0.55), dry);
  diffuseColor.a = shape * 0.92 * (1.0 - smoothstep(0.75, 1.0, k));
}`)
        .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
roughnessFactor = mix(0.28, 0.85, smoothstep(0.05, 0.5, (uTime - vGore.y) / vGore.z));`);
    };
    mat.customProgramCacheKey = () => 'gore-splat';
    this.mesh = new THREE.InstancedMesh(g, mat, SPLAT_MAX);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = 4;
    this.mesh.receiveShadow = true;
    this.aGore = new THREE.InstancedBufferAttribute(new Float32Array(SPLAT_MAX * 4), 4);
    g.setAttribute('aGore', this.aGore);
    // Nothing shows until it is written.
    this.m.makeScale(0, 0, 0);
    for (let i = 0; i < SPLAT_MAX; i++) {
      this.mesh.setMatrixAt(i, this.m);
      this.mesh.setColorAt(i, RED.pool);
      this.aGore.setXYZW(i, 0, -1e6, 1, 0);
    }
  }

  add(x: number, y: number, z: number, size: number, color: THREE.Color, time: number, life: number, pool = false) {
    const i = this.next;
    this.next = (this.next + 1) % SPLAT_MAX;
    this.q.setFromAxisAngle(this.up, Math.random() * Math.PI * 2);
    this.m.compose(new THREE.Vector3(x, y + 0.035 + i * 0.00002, z), this.q, new THREE.Vector3(size, 1, size * (0.8 + Math.random() * 0.4)));
    this.mesh.setMatrixAt(i, this.m);
    this.mesh.setColorAt(i, color);
    this.aGore.setXYZW(i, Math.random() * 100, time, life, pool ? 1 : 0);
    this.mesh.instanceMatrix.needsUpdate = true;
    if (this.mesh.instanceColor) this.mesh.instanceColor.needsUpdate = true;
    this.aGore.needsUpdate = true;
  }
}

/* -------------------------------------------------------------- gibs -- */

const GIB_MAX = 360;
type GibKind = 'meat' | 'bone' | 'skull';

interface Gib { kind: GibKind; slot: number; x: number; y: number; z: number; vx: number; vy: number; vz: number; ax: THREE.Vector3; ang: number; spin: number; r: number; age: number; life: number; resting: boolean; bled: boolean; blood: Blood | null; size: number }

class GibLayer {
  readonly group = new THREE.Group();
  private meshes: Record<GibKind, THREE.InstancedMesh>;
  private free: Record<GibKind, number[]>;
  private live: Gib[] = [];
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private p = new THREE.Vector3();
  private s = new THREE.Vector3();

  constructor() {
    const chunk = new THREE.IcosahedronGeometry(0.5, 0);
    // Knock the chunks out of round.
    const pos = chunk.getAttribute('position');
    for (let i = 0; i < pos.count; i++) pos.setXYZ(i, pos.getX(i) * (0.7 + Math.random() * 0.6), pos.getY(i) * (0.6 + Math.random() * 0.5), pos.getZ(i) * (0.7 + Math.random() * 0.6));
    chunk.computeVertexNormals();
    const bone = new THREE.CylinderGeometry(0.12, 0.16, 1, 5);
    const skull = new THREE.SphereGeometry(0.5, 8, 6);
    skull.scale(1, 0.9, 1.1);
    const meat = new THREE.MeshStandardMaterial({ color: '#6a1010', roughness: 0.38, metalness: 0.05, flatShading: true });
    const boneM = new THREE.MeshStandardMaterial({ color: '#c8bca4', roughness: 0.75 });
    const mk = (g: THREE.BufferGeometry, mat: THREE.Material, n: number) => {
      const im = new THREE.InstancedMesh(g, mat, n);
      im.frustumCulled = false;
      im.castShadow = true;
      im.receiveShadow = true;
      this.m.makeScale(0, 0, 0);
      for (let i = 0; i < n; i++) im.setMatrixAt(i, this.m);
      this.group.add(im);
      return im;
    };
    this.meshes = { meat: mk(chunk, meat, GIB_MAX), bone: mk(bone, boneM, GIB_MAX / 2), skull: mk(skull, boneM, 48) };
    // Meat takes the colour of what it came from: the colours exist from the
    // start (made on first use, they would change the shader mid-fight).
    for (let i = 0; i < GIB_MAX; i++) this.meshes.meat.setColorAt(i, WHITE);
    this.free = { meat: [...Array(GIB_MAX).keys()], bone: [...Array(GIB_MAX / 2).keys()], skull: [...Array(48).keys()] };
  }

  throw(kind: GibKind, x: number, y: number, z: number, vx: number, vy: number, vz: number, size: number, blood: Blood | null, tint?: THREE.Color) {
    let slot = this.free[kind].pop();
    if (slot === undefined) {
      // Full: the oldest of this kind goes.
      const old = this.live.find((g) => g.kind === kind);
      if (!old) return;
      this.retire(old);
      slot = this.free[kind].pop()!;
    }
    if (kind === 'meat') {
      this.meshes.meat.setColorAt(slot, tint ?? WHITE);
      this.meshes.meat.instanceColor!.needsUpdate = true;
    }
    this.live.push({
      kind, slot, x, y, z, vx, vy, vz, ax: new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize(),
      ang: Math.random() * 6, spin: 6 + Math.random() * 10, r: size * 0.4, age: 0, life: 16 + Math.random() * 6, resting: false, bled: false, blood, size,
    });
  }

  private retire(g: Gib) {
    this.m.makeScale(0, 0, 0);
    this.meshes[g.kind].setMatrixAt(g.slot, this.m);
    this.meshes[g.kind].instanceMatrix.needsUpdate = true;
    this.free[g.kind].push(g.slot);
    this.live.splice(this.live.indexOf(g), 1);
  }

  update(dt: number, heightAt: (x: number, z: number) => number, onLand: (g: Gib) => void) {
    const dirty = new Set<GibKind>();
    for (const g of [...this.live]) {
      g.age += dt;
      if (g.age > g.life) { this.retire(g); dirty.add(g.kind); continue; }
      const ground = heightAt(g.x, g.z);
      if (!g.resting) {
        g.vy -= 22 * dt;
        g.x += g.vx * dt; g.y += g.vy * dt; g.z += g.vz * dt;
        g.ang += g.spin * dt;
        if (g.y < ground + g.r) {
          g.y = ground + g.r;
          if (!g.bled) { g.bled = true; onLand(g); }
          if (Math.abs(g.vy) < 2.2) { g.resting = true; g.vx = g.vz = g.vy = 0; }
          else { g.vy *= -0.28; g.vx *= 0.55; g.vz *= 0.55; g.spin *= 0.5; }
        }
      }
      // In their time the ground takes them.
      const sink = Math.max(0, g.age - (g.life - 2.5)) * 0.35;
      this.p.set(g.x, Math.max(g.y, ground + g.r) - sink, g.z);
      this.q.setFromAxisAngle(g.ax, g.ang);
      const sz = g.size;
      if (g.kind === 'bone') this.s.set(sz * 0.55, sz * 1.6, sz * 0.55);
      else this.s.setScalar(sz);
      this.m.compose(this.p, this.q, this.s);
      this.meshes[g.kind].setMatrixAt(g.slot, this.m);
      dirty.add(g.kind);
    }
    for (const k of dirty) {
      this.meshes[k].instanceMatrix.needsUpdate = true;
      if (this.meshes[k].instanceColor) this.meshes[k].instanceColor!.needsUpdate = true;
    }
  }

  clear() {
    for (const g of [...this.live]) this.retire(g);
  }
}

/* -------------------------------------------------------------- gore -- */

export class Gore {
  readonly group = new THREE.Group();
  private splats = new SplatLayer();
  private gibs = new GibLayer();
  private time = 0;
  /** 1 full, 0.35 reduced, 0 none (the Gore setting). */
  level = 1;

  constructor(private heightAt: (x: number, z: number) => number, private matter: ParticleSystem) {
    this.group.name = 'gore';
    this.group.add(this.splats.mesh, this.gibs.group);
  }

  /** A blow landing: blood thrown the way it was struck. */
  hit(x: number, y: number, z: number, amount: number, maxHp: number, blood: Blood | null, undead: boolean, dirX = 0, dirZ = 0, crit = false) {
    if (this.level <= 0) return;
    const force = Math.min(1, amount / Math.max(1, maxHp)) * (crit ? 1.6 : 1);
    const n = Math.round((3 + force * 14) * this.level);
    if (blood) {
      for (let i = 0; i < n; i++) {
        const sp = 2 + Math.random() * 4 + force * 4;
        const a = Math.random() * Math.PI * 2;
        this.matter.spawn({
          x, y, z,
          vx: dirX * sp + Math.cos(a) * sp * 0.45, vy: 1.5 + Math.random() * 3.5, vz: dirZ * sp + Math.sin(a) * sp * 0.45,
          gravity: 16, drag: 0.6, life: 0.35 + Math.random() * 0.35, size: 0.05 + Math.random() * 0.07, sizeEnd: 0.03,
          color: blood.spray, colorEnd: blood.pool, alpha: 0.95, shape: i % 3 === 0 ? 1 : 0,
        });
      }
      // Some of it reaches the ground.
      if (Math.random() < 0.35 + force) {
        const d = 0.4 + Math.random() * (0.8 + force * 1.6);
        this.splats.add(x + dirX * d, this.heightAt(x + dirX * d, z + dirZ * d), z + dirZ * d, 0.5 + force * 1.1 + Math.random() * 0.4, blood.pool, this.time, 40 + Math.random() * 20);
      }
    } else if (undead) {
      for (let i = 0; i < Math.ceil(n * 0.6); i++) {
        const a = Math.random() * Math.PI * 2, sp = 2 + Math.random() * 3;
        this.matter.spawn({ x, y, z, vx: dirX * sp + Math.cos(a) * 1.5, vy: 2 + Math.random() * 3, vz: dirZ * sp + Math.sin(a) * 1.5, gravity: 14, drag: 0.4, life: 0.5, size: 0.06, sizeEnd: 0.04, color: 0xd8cdb4, colorEnd: 0x8a8070, alpha: 1, shape: 5, spin: 10 });
      }
    }
  }

  /** A death. Burst: the blow was far more than it had left. */
  kill(x: number, y: number, z: number, scale: number, blood: Blood | null, undead: boolean, burst: boolean, dirX = 0, dirZ = 0) {
    if (this.level <= 0) return;
    const gy = this.heightAt(x, z);
    if (blood) {
      // It bleeds out where it lies.
      this.splats.add(x, gy, z, (1.3 + Math.random() * 0.7) * scale, blood.pool, this.time, 60 + Math.random() * 30, true);
      this.hit(x, y, z, 1, 1, blood, false, dirX, dirZ, true);
    }
    if (!burst || this.level < 0.5) return;
    // Burst: the body comes apart.
    const pieces = Math.round((blood ? 9 : 7) * Math.min(2, scale) * this.level);
    for (let i = 0; i < pieces; i++) {
      const a = Math.random() * Math.PI * 2, sp = 2 + Math.random() * 5;
      const vx = dirX * 4 + Math.cos(a) * sp, vz = dirZ * 4 + Math.sin(a) * sp, vy = 4 + Math.random() * 6;
      const kind: GibKind = blood ? (i % 4 === 3 ? 'bone' : 'meat') : 'bone';
      this.gibs.throw(kind, x + Math.cos(a) * 0.2, y + Math.random() * 0.6, z + Math.sin(a) * 0.2, vx, vy, vz, (0.14 + Math.random() * 0.16) * Math.min(1.6, scale), blood, blood?.pool.clone().lerp(new THREE.Color('#8a2a24'), Math.random() * 0.6));
    }
    // The head goes its own way.
    if (undead || Math.random() < 0.5) this.gibs.throw('skull', x, y + 0.8 * scale, z, dirX * 5 + (Math.random() - 0.5) * 3, 7 + Math.random() * 3, dirZ * 5 + (Math.random() - 0.5) * 3, 0.32 * Math.min(1.5, scale), blood);
    if (blood) {
      for (let i = 0; i < 26 * this.level; i++) {
        const a = Math.random() * Math.PI * 2, sp = 3 + Math.random() * 7;
        this.matter.spawn({ x, y: y + 0.3, z, vx: Math.cos(a) * sp + dirX * 3, vy: 2 + Math.random() * 6, vz: Math.sin(a) * sp + dirZ * 3, gravity: 18, drag: 0.5, life: 0.5 + Math.random() * 0.4, size: 0.08 + Math.random() * 0.1, sizeEnd: 0.04, color: blood.spray, colorEnd: blood.pool, alpha: 0.95, shape: i % 2 ? 1 : 0 });
      }
      for (let i = 0; i < 3; i++) {
        const a = Math.random() * Math.PI * 2, d = 0.8 + Math.random() * 1.8;
        this.splats.add(x + Math.cos(a) * d, gy, z + Math.sin(a) * d, 0.7 + Math.random() * 0.9, blood.pool, this.time, 50 + Math.random() * 20);
      }
    } else {
      for (let i = 0; i < 10; i++) this.matter.spawn({ x, y: y + 0.4, z, vx: (Math.random() - 0.5) * 3, vy: 1 + Math.random() * 2, vz: (Math.random() - 0.5) * 3, gravity: 2, drag: 1.5, life: 1.2, size: 0.4, sizeEnd: 1.1, color: 0x8a8272, colorEnd: 0x4a463e, alpha: 0.3, shape: 4 });
    }
  }

  update(dt: number) {
    this.time += dt;
    this.splats.uniforms.uTime.value = this.time;
    this.gibs.update(dt, this.heightAt, (g) => {
      if (g.blood && g.kind !== 'bone') this.splats.add(g.x, this.heightAt(g.x, g.z), g.z, 0.25 + g.size * 1.6, g.blood.pool, this.time, 30 + Math.random() * 15);
    });
  }

  clear() { this.gibs.clear(); }
}
