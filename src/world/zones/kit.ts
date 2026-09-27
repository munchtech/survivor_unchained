import * as THREE from 'three';
import { Assets, type PropPack } from '@/render/assets';
import { ParticleSystem } from '@/render/particles';
import { FloraField } from '@/render/scatter';
import type { Terrain } from '@/render/terrain';
import type { CollisionWorld } from '@/sim/collision';
import { hash1 } from '@/core/math';

/* The toolbox every zone is built with.
 *
 *   prop()      a KayKit piece on the ground, with a collider if it blocks
 *   source()    a light in the world (a lantern, a fire, a window); the
 *               zone may have dozens, but only the few nearest the camera
 *               get a real point light from the pool, so the shaders never
 *               recompile and a town full of windows costs what one lamp does
 *   campfire()  stones, logs, a bed of embers, flames, sparks and smoke
 *   lamp()      a lantern post, lit or dark
 *
 * tick() animates all of it: flicker, flames, drifting sparks. */

export interface LightSource {
  x: number; y: number; z: number;
  color: THREE.Color;
  intensity: number;
  distance: number;
  flicker: number;
  phase: number;
  on: boolean;
  /** Emissive bits that go dark with it (flame meshes, glass). */
  glow: THREE.Object3D[];
}

interface Fire { x: number; y: number; z: number; size: number; acc: number; src: LightSource }

const POOL_SIZE = 6;

export class ZoneKit {
  readonly root = new THREE.Group();
  readonly sources: LightSource[] = [];
  readonly flames = new ParticleSystem(5000, true);
  readonly smoke = new ParticleSystem(2500, false);
  readonly flora = new FloraField(2600);
  private pool: THREE.PointLight[] = [];
  private fires: Fire[] = [];
  private time = 0;
  private focus = new THREE.Vector3();
  private emberColor = new THREE.Color('#ffb060');

  constructor(readonly terrain: Terrain, readonly col: CollisionWorld) {
    for (let i = 0; i < POOL_SIZE; i++) {
      const l = new THREE.PointLight(0xffffff, 0, 10, 1.7);
      l.castShadow = false;
      this.root.add(l);
      this.pool.push(l);
    }
    this.root.add(this.flames.mesh, this.smoke.mesh);
  }

  y(x: number, z: number) { return this.terrain.heightAt(x, z); }

  /** A prop on the ground. `r` adds a round collider, `box` an oriented one. */
  prop(pack: PropPack, name: string, x: number, z: number, o: {
    rot?: number; scale?: number; r?: number; box?: [number, number]; y?: number; tag?: string; soft?: boolean; tilt?: [number, number]; sink?: number;
  } = {}) {
    const obj = Assets.prop(pack, name);
    obj.position.set(x, (o.y ?? this.y(x, z)) - (o.sink ?? 0), z);
    obj.rotation.set(o.tilt?.[0] ?? 0, o.rot ?? 0, o.tilt?.[1] ?? 0);
    obj.scale.setScalar(o.scale ?? 1);
    this.root.add(obj);
    const opts = { tag: o.tag, soft: o.soft };
    if (o.r) this.col.addCircle(x, z, o.r, opts);
    // Collision boxes turn the other way round from Three's rotation.y.
    if (o.box) this.col.addBox(x, z, o.box[0], o.box[1], -(o.rot ?? 0), opts);
    return obj;
  }

  source(x: number, y: number, z: number, color: THREE.ColorRepresentation, intensity: number, distance: number, flicker = 0.12, glow: THREE.Object3D[] = []): LightSource {
    const s: LightSource = { x, y, z, color: new THREE.Color(color), intensity, distance, flicker, phase: hash1(this.sources.length, 7) * 100, on: true, glow };
    this.sources.push(s);
    return s;
  }

  setLit(s: LightSource, on: boolean) {
    s.on = on;
    for (const g of s.glow) g.visible = on;
  }

  /** A little flame that blooms: for lanterns, torches and candles. */
  flameGlow(x: number, y: number, z: number, size = 0.18, color = '#ffb35a') {
    const m = new THREE.Mesh(
      new THREE.SphereGeometry(size, 10, 8),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(5), toneMapped: true }),
    );
    m.scale.set(1, 1.5, 1);
    m.position.set(x, y, z);
    this.root.add(m);
    return m;
  }

  /** A lantern post (the Watch's lights). Dark ones say the road is lost. */
  lamp(x: number, z: number, rot = 0, lit = true, scale = 0.9) {
    const post = this.prop('halloween', 'post_lantern', x, z, { rot, scale, r: 0.3 });
    // The lantern hangs off the arm, 1.1 m out along local +z, near the top.
    const off = new THREE.Vector3(0, 2.72 * scale, 1.12 * scale).applyAxisAngle(new THREE.Vector3(0, 1, 0), rot);
    const gy = this.y(x, z);
    const glow = this.flameGlow(x + off.x, gy + off.y - 0.55 * scale, z + off.z, 0.11 * scale);
    const src = this.source(x + off.x, gy + off.y - 0.4, z + off.z, 0xffa860, 9, 13, 0.1, [glow]);
    this.setLit(src, lit);
    return { post, src };
  }

  /** A campfire: the survivor's first light. */
  campfire(x: number, z: number, size = 1) {
    const y = this.y(x, z);
    const stoneMat = new THREE.MeshStandardMaterial({ color: '#6a655c', roughness: 0.95, flatShading: true });
    const ring = new THREE.Group();
    const n = 9;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2 + hash1(i, 3) * 0.3;
      const s = new THREE.Mesh(new THREE.DodecahedronGeometry(0.22 * size * (0.8 + hash1(i, 4) * 0.5), 0), stoneMat);
      s.position.set(Math.cos(a) * 0.72 * size, 0.08 * size, Math.sin(a) * 0.72 * size);
      s.rotation.set(hash1(i, 5) * 3, hash1(i, 6) * 3, 0);
      s.scale.y = 0.7;
      s.castShadow = true;
      ring.add(s);
    }
    const logMat = new THREE.MeshStandardMaterial({ color: '#3a2618', roughness: 0.9 });
    const charMat = new THREE.MeshStandardMaterial({ color: '#140c08', roughness: 1, emissive: new THREE.Color('#ff5a1a'), emissiveIntensity: 0.9 });
    for (let i = 0; i < 4; i++) {
      const a = (i / 4) * Math.PI * 2 + 0.4;
      const log = new THREE.Mesh(new THREE.CylinderGeometry(0.07 * size, 0.09 * size, 0.95 * size, 7), i % 2 ? logMat : charMat);
      log.position.set(Math.cos(a) * 0.18 * size, 0.2 * size, Math.sin(a) * 0.18 * size);
      log.rotation.set(0, -a, 1.05);
      log.rotateOnWorldAxis(new THREE.Vector3(0, 1, 0), 0);
      log.castShadow = true;
      ring.add(log);
    }
    const bed = new THREE.Mesh(new THREE.CircleGeometry(0.42 * size, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color('#ff6a1a').multiplyScalar(2.2) }));
    bed.rotation.x = -Math.PI / 2;
    bed.position.y = 0.04;
    ring.add(bed);
    ring.position.set(x, y, z);
    this.root.add(ring);
    this.col.addCircle(x, z, 0.8 * size, { soft: true });
    const src = this.source(x, y + 1.1 * size, z, 0xff9a48, 16 * size, 16 * size, 0.28, [bed]);
    this.fires.push({ x, y, z, size, acc: 0, src });
    return src;
  }

  /** A felled log: bark all round, pale cut ends. For sitting on. */
  log(x: number, z: number, rot: number, len = 2.2, r = 0.26, collide = true) {
    const g = new THREE.Group();
    const bark = new THREE.MeshStandardMaterial({ color: '#4a3526', roughness: 0.95, flatShading: true });
    const cut = new THREE.MeshStandardMaterial({ color: '#b08a5a', roughness: 0.9 });
    const geo = new THREE.CylinderGeometry(r * 0.92, r, len, 9, 3, true);
    const pos = geo.getAttribute('position');
    for (let i = 0; i < pos.count; i++) {
      const k = 1 + (hash1(i, 13) - 0.5) * 0.12;
      pos.setX(i, pos.getX(i) * k);
      pos.setZ(i, pos.getZ(i) * k);
    }
    geo.computeVertexNormals();
    const body = new THREE.Mesh(geo, bark);
    g.add(body);
    for (const s of [-1, 1]) {
      const cap = new THREE.Mesh(new THREE.CircleGeometry(r * (s > 0 ? 0.9 : 1), 9), cut);
      cap.position.y = (s * len) / 2;
      cap.rotation.x = s > 0 ? -Math.PI / 2 : Math.PI / 2;
      g.add(cap);
      const ring = new THREE.Mesh(new THREE.RingGeometry(r * 0.35, r * 0.4, 9), new THREE.MeshStandardMaterial({ color: '#7a5a3a', roughness: 0.9 }));
      ring.position.y = (s * len) / 2 + s * 0.002;
      ring.rotation.x = cap.rotation.x;
      g.add(ring);
    }
    // A stub of a branch.
    const stub = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.07, 0.4, 6), bark);
    stub.position.set(r * 0.9, len * 0.15, 0);
    stub.rotation.z = -1.1;
    g.add(stub);
    g.rotation.set(0, rot, Math.PI / 2);
    g.position.set(x, this.y(x, z) + r * 0.85, z);
    g.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = o.receiveShadow = true; });
    this.root.add(g);
    if (collide) this.col.addBox(x, z, len / 2, r, -rot);
    return g;
  }

  /** A bedroll on the ground: a blanket with a rolled head. */
  bedroll(x: number, z: number, rot: number, color = '#6a2e26') {
    const g = new THREE.Group();
    const wool = new THREE.MeshStandardMaterial({ color, roughness: 1 });
    const geo = new THREE.BoxGeometry(0.95, 0.1, 1.95, 6, 1, 10);
    const pos = geo.getAttribute('position');
    for (let i = 0; i < pos.count; i++) {
      const px = pos.getX(i), pz = pos.getZ(i);
      if (pos.getY(i) > 0) pos.setY(i, pos.getY(i) + Math.sin(pz * 5 + px * 2) * 0.03 + Math.cos(px * 7) * 0.015);
    }
    geo.computeVertexNormals();
    g.add(new THREE.Mesh(geo, wool));
    const edge = new THREE.Mesh(new THREE.BoxGeometry(0.97, 0.06, 0.18), new THREE.MeshStandardMaterial({ color: '#c8b890', roughness: 1 }));
    edge.position.set(0, 0.04, -0.55);
    g.add(edge);
    const roll = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.98, 12), new THREE.MeshStandardMaterial({ color: '#8a7a60', roughness: 1 }));
    roll.rotation.z = Math.PI / 2;
    roll.position.set(0, 0.14, -0.92);
    g.add(roll);
    g.position.set(x, this.y(x, z) + 0.05, z);
    g.rotation.y = rot;
    g.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = o.receiveShadow = true; });
    this.root.add(g);
    return g;
  }

  /** How close a lit fire is, 0..1: for the crackle in the ambience. */
  warmth(x: number, z: number, reach = 13) {
    let k = 0;
    for (const s of this.sources) {
      if (!s.on || s.flicker < 0.18 || s.color.r < s.color.b) continue;
      const d = Math.hypot(s.x - x, s.z - z);
      if (d < reach) k = Math.max(k, (1 - d / reach) ** 2 * Math.min(1, s.intensity / 6));
    }
    return k;
  }

  /** Put the brightest nearby sources into the light pool. Call per frame. */
  tick(dt: number, focusX: number, focusZ: number) {
    this.time += dt;
    const t = this.time;
    this.focus.set(focusX, 0, focusZ);
    // Rank lit sources by distance, weighted by how bright they are.
    const ranked = this.sources
      .filter((s) => s.on)
      .map((s) => ({ s, d: Math.hypot(s.x - focusX, s.z - focusZ) - s.distance * 0.4 }))
      .sort((a, b) => a.d - b.d);
    for (let i = 0; i < this.pool.length; i++) {
      const l = this.pool[i];
      const r = ranked[i];
      if (!r || r.d > 45) { l.intensity = 0; continue; }
      const s = r.s;
      const f = 1 + (Math.sin(t * 8.3 + s.phase) * 0.5 + Math.sin(t * 19.7 + s.phase * 1.7) * 0.3 + Math.sin(t * 3.1 + s.phase) * 0.2) * s.flicker;
      // Fade lights in and out at the edge of the pool so swaps are invisible.
      const edge = 1 - Math.max(0, Math.min(1, (r.d - 30) / 15));
      l.color.copy(s.color);
      l.intensity = s.intensity * f * edge;
      l.distance = s.distance;
      l.position.set(s.x, s.y + Math.sin(t * 11 + s.phase) * 0.03 * s.flicker, s.z);
    }
    // Fires: flames, sparks and smoke.
    for (const fire of this.fires) {
      if (!fire.src.on) continue;
      if (Math.hypot(fire.x - focusX, fire.z - focusZ) > 60) continue;
      fire.acc += dt * 60 * fire.size;
      while (fire.acc >= 1) {
        fire.acc -= 1;
        const a = Math.random() * Math.PI * 2, r = Math.random() * 0.3 * fire.size;
        this.flames.spawn({
          x: fire.x + Math.cos(a) * r, y: fire.y + 0.15, z: fire.z + Math.sin(a) * r,
          vx: (Math.random() - 0.5) * 0.3, vy: 1.1 + Math.random() * 0.9, vz: (Math.random() - 0.5) * 0.3,
          gravity: -0.6, drag: 1.2, life: 0.45 + Math.random() * 0.35,
          size: (0.55 + Math.random() * 0.35) * fire.size, sizeEnd: 0.1, color: 0xffc860, colorEnd: 0xff3a0a, alpha: 0.9, shape: 0,
        });
        if (Math.random() < 0.18) {
          this.flames.spawn({
            x: fire.x, y: fire.y + 0.4, z: fire.z,
            vx: (Math.random() - 0.5) * 1.4, vy: 2 + Math.random() * 2.5, vz: (Math.random() - 0.5) * 1.4,
            gravity: -0.2, drag: 0.6, life: 1.2 + Math.random() * 1.4, size: 0.06, sizeEnd: 0.02,
            color: this.emberColor, colorEnd: 0xff3000, alpha: 1, shape: 1,
          });
        }
        if (Math.random() < 0.2) {
          this.smoke.spawn({
            x: fire.x + (Math.random() - 0.5) * 0.3, y: fire.y + 1.0 * fire.size, z: fire.z + (Math.random() - 0.5) * 0.3,
            vx: 0.15 + (Math.random() - 0.5) * 0.2, vy: 0.9 + Math.random() * 0.4, vz: (Math.random() - 0.5) * 0.2,
            drag: 0.3, life: 3.5, size: 0.6 * fire.size, sizeEnd: 2.4 * fire.size, color: 0x3a3634, colorEnd: 0x1a1a1c, alpha: 0.28, shape: 4,
          });
        }
      }
    }
    this.flames.update(t);
    this.smoke.update(t);
  }
}
