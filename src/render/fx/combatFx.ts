import * as THREE from 'three';
import { ParticleSystem } from '../particles';
import { DecalLayer } from './decals';
import { RibbonLayer } from './ribbons';
import { ProjectileRenderer } from './projectiles';
import { PickupRenderer } from './pickups';
import { DamageNumbers } from './numbers';
import { SCHOOL, HOSTILE, schoolOfArt } from './palette';
import type { CombatEvent } from '@/sim/events';
import type { Battle } from '@/sim/battle';
import type { School } from '@/sim/types';
import type { FollowCamera } from '../camera';

/* The fight made visible.
 *
 * The simulation says what happened; this decides what it looks like and
 * how it feels. Every event is answered in the language of its school
 * (palette.ts) and scaled by how much it matters: a dot tick is a whisper, a
 * crit is a spark shower and a gold number, an elite's death is a burst of
 * light that briefly lights the ground around it, a boss's lunge is a lane on
 * the floor you can read the timing off.
 *
 * Point lights are few and precious; a pool hands them to the brightest
 * recent moments (explosions, strikes, level-ups) and lets them fade. */

interface Flash { light: THREE.PointLight; t: number; life: number; peak: number }

export class CombatFx {
  readonly group = new THREE.Group();
  readonly sparks = new ParticleSystem(24000, true);
  readonly smoke = new ParticleSystem(9000, false);
  readonly decals: DecalLayer;
  readonly ribbons = new RibbonLayer();
  readonly projectiles: ProjectileRenderer;
  readonly pickups: PickupRenderer;
  readonly numbers = new DamageNumbers();
  private flashes: Flash[] = [];
  private zoneDecals = new Map<number, ReturnType<DecalLayer['circle']>>();
  private auraT = 0;
  time = 0;
  /** Filled by the game with the survivor's position each frame. */
  playerPos = new THREE.Vector3();
  cam: FollowCamera | null = null;
  onDamageFlash: (v: number) => void = () => {};

  constructor(private heightAt: (x: number, z: number) => number) {
    this.group.name = 'combat-fx';
    this.decals = new DecalLayer(heightAt);
    this.projectiles = new ProjectileRenderer(this.sparks, this.smoke);
    this.pickups = new PickupRenderer(this.sparks);
    this.group.add(this.sparks.mesh, this.smoke.mesh, this.decals.group, this.ribbons.group, this.projectiles.group, this.pickups.group, this.numbers.mesh);
    for (let i = 0; i < 8; i++) {
      const l = new THREE.PointLight(0xffffff, 0, 10, 1.6);
      l.castShadow = false;
      this.group.add(l);
      this.flashes.push({ light: l, t: 1, life: 1, peak: 0 });
    }
  }

  private y(x: number, z: number) { return this.heightAt(x, z); }

  flash(x: number, y: number, z: number, color: number | THREE.Color, peak: number, life: number, range = 9) {
    // Reuse the dimmest light.
    let best = this.flashes[0];
    for (const f of this.flashes) if (f.light.intensity < best.light.intensity) best = f;
    best.light.position.set(x, y, z);
    best.light.color.set(color);
    best.light.distance = range;
    best.t = 0; best.life = life; best.peak = peak;
  }

  burst(x: number, y: number, z: number, school: School, n: number, speed: number, opts: { up?: number; size?: number; life?: number; shape?: 0 | 1 | 2 | 3 | 4 | 5; gravity?: number } = {}) {
    const pal = SCHOOL[school];
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2;
      const v = speed * (0.4 + Math.random() * 0.8);
      this.sparks.spawn({
        x, y, z, vx: Math.cos(a) * v, vy: (opts.up ?? 1.5) * (0.5 + Math.random()), vz: Math.sin(a) * v,
        gravity: opts.gravity ?? 6, drag: 3, life: (opts.life ?? 0.45) * (0.7 + Math.random() * 0.6),
        size: opts.size ?? 0.09, sizeEnd: 0.01, color: pal.core, colorEnd: pal.glow, shape: opts.shape ?? 1,
      });
    }
  }

  handle(events: CombatEvent[], b: Battle) {
    for (const ev of events) {
      switch (ev.t) {
        case 'hit': {
          const y = this.y(ev.x, ev.z) + 1.0;
          if (ev.dot) {
            if (Math.random() < 0.35) this.numbers.spawn(ev.x, y, ev.z, ev.amount, 'dot', this.time);
            break;
          }
          this.numbers.spawn(ev.x + (Math.random() - 0.5) * 0.3, y, ev.z, ev.amount, ev.blocked ? 'blocked' : ev.crit ? 'crit' : 'hit', this.time);
          if (ev.blocked) { this.burst(ev.x, y, ev.z, 'physical', 5, 3, { up: 2, size: 0.06 }); break; }
          this.burst(ev.x, y, ev.z, ev.school, ev.crit ? 10 : 4, ev.crit ? 5 : 3, { size: ev.crit ? 0.12 : 0.08 });
          if (ev.crit) {
            this.sparks.spawn({ x: ev.x, y, z: ev.z, life: 0.2, size: 0.55, sizeEnd: 0.15, color: SCHOOL[ev.school].core, shape: 3 });
            this.cam?.addTrauma(0.04);
          }
          break;
        }
        case 'kill': {
          const gy = this.y(ev.x, ev.z);
          const school = ev.school;
          this.burst(ev.x, gy + 0.9, ev.z, school, ev.elite ? 40 : 10, ev.elite ? 7 : 4, { up: 3, life: 0.6 });
          // Something of it goes back up: the light the stone keeps.
          for (let i = 0; i < (ev.elite ? 14 : 4); i++) {
            this.sparks.spawn({ x: ev.x + (Math.random() - 0.5) * 0.6, y: gy + 0.5, z: ev.z + (Math.random() - 0.5) * 0.6, vy: 1.4 + Math.random() * 1.5, life: 1 + Math.random() * 0.6, size: 0.07, sizeEnd: 0.02, color: 0xffb060, colorEnd: 0xff5a20, drag: 0.8, shape: 0 });
          }
          if (ev.family === 'undead') {
            for (let i = 0; i < 6; i++) this.smoke.spawn({ x: ev.x, y: gy + 0.6, z: ev.z, vx: (Math.random() - 0.5) * 3, vy: 2 + Math.random() * 2, vz: (Math.random() - 0.5) * 3, gravity: 9, life: 0.9, size: 0.07, color: 0xd8d2c0, shape: 5, spin: 8, alpha: 1 });
          }
          this.smoke.spawn({ x: ev.x, y: gy + 0.3, z: ev.z, vy: 0.5, life: 0.9, size: 0.5, sizeEnd: 1.3, color: 0x3a3430, colorEnd: 0x1a1816, alpha: 0.35, shape: 4 });
          if (ev.elite || ev.boss) {
            this.flash(ev.x, gy + 1.5, ev.z, SCHOOL[school].light, 16, 0.6, 12);
            this.ribbons.nova(ev.x, gy + 0.3, ev.z, 5, SCHOOL[school].core, SCHOOL[school].glow, 0.45, 2);
            this.cam?.addTrauma(0.35);
          }
          break;
        }
        case 'playerHit': {
          if (ev.dodged || ev.blocked) {
            this.numbers.spawn(ev.x, this.y(ev.x, ev.z) + 1.2, ev.z, 0, 'blocked', this.time);
            this.burst(ev.x, this.y(ev.x, ev.z) + 1, ev.z, ev.blocked ? 'holy' : 'physical', 12, 4);
            break;
          }
          this.numbers.spawn(ev.x, this.y(ev.x, ev.z) + 1.4, ev.z, ev.amount, 'player', this.time);
          this.burst(ev.x, this.y(ev.x, ev.z) + 1, ev.z, 'fire', 6, 3, { size: 0.07 });
          this.cam?.addTrauma(Math.min(0.5, 0.12 + ev.amount / 60));
          this.onDamageFlash(Math.min(1, 0.35 + ev.amount / 40));
          break;
        }
        case 'playerHeal':
          if (ev.amount >= 3) this.numbers.spawn(this.playerPos.x, this.playerPos.y + 1.6, this.playerPos.z, ev.amount, 'heal', this.time);
          break;
        case 'nova': {
          const gy = this.y(ev.x, ev.z) + 0.35;
          const pal = SCHOOL[ev.school];
          this.ribbons.nova(ev.x, gy, ev.z, ev.radius, pal.core, pal.glow, ev.duration, ev.rings ?? 1);
          if ((ev.rings ?? 1) > 0) this.flash(ev.x, gy + 1, ev.z, pal.light, 6, 0.35, ev.radius * 2);
          break;
        }
        case 'explosion': {
          const gy = this.y(ev.x, ev.z);
          const pal = SCHOOL[ev.school];
          const r = ev.radius;
          this.flash(ev.x, gy + 1.2, ev.z, pal.light, 10 + ev.power * 10, 0.35, r * 3 + 3);
          this.ribbons.nova(ev.x, gy + 0.25, ev.z, r * 1.15, pal.core, pal.glow, 0.22, 1);
          const n = Math.min(40, 10 + Math.round(r * 8));
          for (let i = 0; i < n; i++) {
            const a = Math.random() * Math.PI * 2, v = r * (2 + Math.random() * 3);
            this.sparks.spawn({ x: ev.x, y: gy + 0.6, z: ev.z, vx: Math.cos(a) * v, vy: 2 + Math.random() * 4, vz: Math.sin(a) * v, gravity: 8, drag: 2.5, life: 0.4 + Math.random() * 0.4, size: 0.1 + Math.random() * 0.08, sizeEnd: 0.01, color: pal.core, colorEnd: pal.glow, shape: 1 });
          }
          this.sparks.spawn({ x: ev.x, y: gy + 0.8, z: ev.z, life: 0.25, size: r * 1.3, sizeEnd: r * 1.8, color: pal.core, colorEnd: pal.glow, alpha: 0.9 });
          if (ev.school === 'fire' || ev.school === 'shadow' || ev.school === 'physical') {
            for (let i = 0; i < 6; i++) this.smoke.spawn({ x: ev.x + (Math.random() - 0.5) * r, y: gy + 0.5, z: ev.z + (Math.random() - 0.5) * r, vy: 1 + Math.random(), life: 1.2, size: r * 0.4, sizeEnd: r * 0.9, color: 0x2a2420, colorEnd: 0x121010, alpha: 0.45, shape: 4, drag: 1.2 });
          }
          if (ev.school === 'frost') {
            for (let i = 0; i < 10; i++) this.smoke.spawn({ x: ev.x, y: gy + 0.6, z: ev.z, vx: (Math.random() - 0.5) * r * 4, vy: 3 + Math.random() * 3, vz: (Math.random() - 0.5) * r * 4, gravity: 12, life: 0.8, size: 0.09, color: 0xe0f4ff, shape: 5, spin: 10 });
          }
          this.cam?.addTrauma(Math.min(0.3, 0.05 + ev.power * 0.1));
          break;
        }
        case 'chain': {
          const pal = SCHOOL[ev.school];
          const p = ev.points;
          const y = this.y(p[0], p[1]) + 1.0;
          this.ribbons.lightning(p, y, pal.core, pal.glow, 0.24, ev.school === 'storm' ? 0.14 : 0.08);
          for (let k = 2; k + 1 < p.length; k += 2) this.burst(p[k], y, p[k + 1], ev.school, 4, 3, { size: 0.06 });
          if (ev.school === 'storm') this.flash(p[p.length - 2], y + 1, p[p.length - 1], pal.light, 6, 0.2, 8);
          break;
        }
        case 'beam': {
          const pal = SCHOOL[ev.school];
          const y = this.y(ev.x0, ev.z0) + 1.0;
          this.ribbons.beam(ev.x0, ev.z0, ev.x1, ev.z1, y, ev.width * 0.6, pal.core, pal.glow, ev.duration);
          this.flash((ev.x0 + ev.x1) / 2, y, (ev.z0 + ev.z1) / 2, pal.light, 6, ev.duration, 12);
          break;
        }
        case 'strike': {
          const gy = this.y(ev.x, ev.z);
          const pal = SCHOOL[ev.school];
          if (ev.delay > 0.05) {
            this.decals.circle(ev.x, ev.z, ev.radius, 8, pal.glow.clone().multiplyScalar(0.6), { life: ev.delay, additive: true });
            setTimeout(() => this.ribbons.pillar(ev.x, gy, ev.z, 16, 0.35 + ev.radius * 0.1, pal.core, pal.glow, 0.3), ev.delay * 1000);
          } else {
            this.ribbons.pillar(ev.x, gy, ev.z, 16, 0.35, pal.core, pal.glow, 0.3);
          }
          break;
        }
        case 'slash': {
          const gy = this.y(ev.x, ev.z) + 1.0;
          const pal = SCHOOL[ev.school];
          this.ribbons.slash(ev.x, gy, ev.z, ev.angle, ev.arc, ev.reach, pal.core, pal.glow, 0.22);
          break;
        }
        case 'muzzle':
          break;
        case 'telegraph': {
          const col = ev.hostile ? HOSTILE.danger : SCHOOL.holy.glow;
          if (ev.shape === 'line') this.decals.lane(ev.x, ev.z, ev.x1 ?? ev.x, ev.z1 ?? ev.z, ev.width ?? 1, col, ev.duration, ev.id);
          else if (ev.shape === 'ring') this.decals.circle(ev.x, ev.z, ev.radius, 8, col, { life: ev.duration, key: ev.id });
          else this.decals.circle(ev.x, ev.z, ev.radius, 0, col, { life: ev.duration, progress: true, key: ev.id });
          break;
        }
        case 'spawn': {
          const gy = this.y(ev.x, ev.z);
          if (ev.style === 'rise') {
            for (let i = 0; i < 10; i++) this.smoke.spawn({ x: ev.x + (Math.random() - 0.5) * 0.8, y: gy + 0.1, z: ev.z + (Math.random() - 0.5) * 0.8, vx: (Math.random() - 0.5) * 2, vy: 1 + Math.random() * 2, vz: (Math.random() - 0.5) * 2, gravity: 6, life: 0.7, size: 0.08, color: 0x3a2e22, shape: 5 });
            this.smoke.spawn({ x: ev.x, y: gy + 0.2, z: ev.z, vy: 0.3, life: 1.0, size: 0.6, sizeEnd: 1.2, color: 0x2e2620, alpha: 0.4, shape: 4 });
            this.sparks.spawn({ x: ev.x, y: gy + 0.3, z: ev.z, vy: 0.6, life: 0.8, size: 0.5, sizeEnd: 0.1, color: 0x6aa0ff, alpha: 0.35 });
          } else if (ev.style === 'burrow') {
            for (let i = 0; i < 8; i++) this.smoke.spawn({ x: ev.x, y: gy + 0.1, z: ev.z, vx: (Math.random() - 0.5) * 3, vy: 1.5 + Math.random() * 2, vz: (Math.random() - 0.5) * 3, gravity: 8, life: 0.6, size: 0.07, color: 0x4a3a28, shape: 5 });
          }
          break;
        }
        case 'pickup':
          if (ev.kind === 'ember' || ev.kind === 'gold') {
            this.sparks.spawn({ x: this.playerPos.x, y: this.playerPos.y + 1, z: this.playerPos.z, vy: 1, life: 0.3, size: 0.25, sizeEnd: 0.05, color: ev.kind === 'gold' ? 0xffd070 : 0xffa050, alpha: 0.6 });
          }
          break;
        case 'levelUp': {
          const p = this.playerPos;
          // It comes every level: a warm rise, not a detonation that hides the fight.
          this.ribbons.nova(p.x, p.y + 0.2, p.z, 3.6, SCHOOL.holy.core, SCHOOL.fire.glow, 0.5, 1);
          this.ribbons.pillar(p.x, p.y, p.z, 7, 0.55, SCHOOL.holy.core, SCHOOL.fire.glow, 0.55);
          this.flash(p.x, p.y + 2, p.z, 0xffc070, 10, 0.7, 9);
          for (let i = 0; i < 30; i++) {
            const a = Math.random() * Math.PI * 2;
            this.sparks.spawn({ x: p.x + Math.cos(a) * 0.8, y: p.y + 0.2, z: p.z + Math.sin(a) * 0.8, vx: Math.cos(a) * 0.5, vy: 3 + Math.random() * 4, vz: Math.sin(a) * 0.5, drag: 1.5, life: 1.2, size: 0.1, sizeEnd: 0.02, color: 0xffe0a0, colorEnd: 0xff7020, shape: 3 });
          }
          break;
        }
        case 'evolve':
        case 'discovery': {
          const p = this.playerPos;
          this.ribbons.nova(p.x, p.y + 0.2, p.z, 9, SCHOOL.arcane.core, SCHOOL.holy.glow, 0.8, 3);
          this.flash(p.x, p.y + 2, p.z, 0xffe0ff, 30, 1.2, 18);
          this.cam?.addTrauma(0.3);
          break;
        }
        case 'dash': {
          const n = 14;
          for (let i = 0; i < n; i++) {
            const t = i / n;
            const x = ev.x0 + (ev.x1 - ev.x0) * t, z = ev.z0 + (ev.z1 - ev.z0) * t;
            this.sparks.spawn({ x, y: this.y(x, z) + 0.9, z, life: 0.35, size: 0.5, sizeEnd: 0.1, color: 0x9ab8ff, colorEnd: 0x3a4a8a, alpha: 0.35 });
            this.smoke.spawn({ x, y: this.y(x, z) + 0.15, z, vy: 0.4, life: 0.6, size: 0.3, sizeEnd: 0.7, color: 0x4a4038, alpha: 0.35, shape: 4 });
          }
          break;
        }
        case 'ability':
          this.ability(ev, b);
          break;
        case 'status':
          if (ev.kind === 'frozen') {
            const gy = this.y(ev.x, ev.z);
            for (let i = 0; i < 8; i++) this.sparks.spawn({ x: ev.x, y: gy + 0.8, z: ev.z, vx: (Math.random() - 0.5) * 2, vy: Math.random() * 2, vz: (Math.random() - 0.5) * 2, life: 0.5, size: 0.1, color: 0xd8f4ff, shape: 3, drag: 3 });
          }
          break;
        case 'shake':
          this.cam?.addTrauma(ev.amount);
          break;
        default:
          break;
      }
    }
  }

  private ability(ev: Extract<CombatEvent, { t: 'ability' }>, _b: Battle) {
    const gy = this.y(ev.x, ev.z);
    switch (ev.id) {
      case 'shield_bash':
        this.ribbons.slash(ev.x, gy + 0.9, ev.z, ev.angle, 2.4, ev.radius, SCHOOL.holy.core, SCHOOL.physical.glow, 0.25);
        this.burst(ev.x + Math.cos(ev.angle) * 1.5, gy + 1, ev.z + Math.sin(ev.angle) * 1.5, 'physical', 20, 6);
        this.flash(ev.x, gy + 1.2, ev.z, 0xfff0d0, 10, 0.3);
        break;
      case 'bulwark':
        this.ribbons.nova(ev.x, gy + 0.3, ev.z, 2.4, SCHOOL.holy.core, SCHOOL.holy.glow, 0.3, 1);
        break;
      case 'leap':
        this.decals.circle(ev.x, ev.z, ev.radius, 0, HOSTILE.rim.clone().multiplyScalar(0.3).add(SCHOOL.physical.glow), { life: 0.42, progress: true });
        break;
      case 'warcry':
        this.ribbons.nova(ev.x, gy + 0.3, ev.z, ev.radius, SCHOOL.fire.core, SCHOOL.fire.glow, 0.5, 2);
        this.cam?.addTrauma(0.3);
        break;
      case 'blink':
        this.ribbons.nova(ev.x, gy + 0.3, ev.z, ev.radius, SCHOOL.frost.core, SCHOOL.frost.glow, 0.3, 1);
        this.burst(ev.x, gy + 1, ev.z, 'frost', 24, 5, { shape: 3 });
        this.flash(ev.x, gy + 1, ev.z, SCHOOL.frost.light, 10, 0.4);
        break;
      case 'time_slip':
        this.ribbons.nova(ev.x, gy + 0.3, ev.z, 14, SCHOOL.arcane.core, SCHOOL.arcane.glow, 0.8, 3);
        break;
      case 'mark_prey':
        this.ribbons.pillar(ev.x, gy, ev.z, 6, 0.5, SCHOOL.fire.core, HOSTILE.rim, 0.5);
        break;
      case 'smoke_bomb':
        for (let i = 0; i < 40; i++) this.smoke.spawn({ x: ev.x + (Math.random() - 0.5) * 2, y: gy + 0.4, z: ev.z + (Math.random() - 0.5) * 2, vx: (Math.random() - 0.5) * 3, vy: 0.6 + Math.random(), vz: (Math.random() - 0.5) * 3, drag: 1.4, life: 2.6, size: 0.8, sizeEnd: 2.2, color: 0x6a6660, colorEnd: 0x2a2826, alpha: 0.6, shape: 4 });
        break;
    }
  }

  update(b: Battle, dt: number, time: number, camera: THREE.PerspectiveCamera, viewW: number, viewH: number) {
    this.time = time;
    this.sparks.update(time);
    this.smoke.update(time);
    this.decals.update(dt, time);
    this.ribbons.update(dt, time, camera);
    this.projectiles.update(b, dt, time, this.heightAt);
    this.pickups.update(b, dt, time, this.heightAt);
    this.numbers.update(time, viewW, viewH);
    for (const f of this.flashes) {
      f.t += dt;
      const k = f.t / f.life;
      f.light.intensity = k >= 1 ? 0 : f.peak * (1 - k) * (1 - k);
    }
    this.statusFx(b, dt);
    this.zones(b);
  }

  /** Ongoing effects on creatures: fire, poison, the elite's halo. */
  private statusFx(b: Battle, dt: number) {
    this.auraT -= dt;
    const tick = this.auraT <= 0;
    if (tick) this.auraT = 0.06;
    b.enemies.forEach((e) => {
      if (e.state === 'dying' || e.state === 'burrowed') return;
      const gy = this.heightAt(e.x, e.z);
      if (tick && e.status.burn && Math.random() < 0.6) {
        this.sparks.spawn({ x: e.x + (Math.random() - 0.5) * 0.4, y: gy + 0.4 + Math.random() * 0.8, z: e.z + (Math.random() - 0.5) * 0.4, vy: 1.5, life: 0.5, size: 0.16, sizeEnd: 0.04, color: 0xffc060, colorEnd: 0xff3a0a, drag: 1 });
      }
      if (tick && e.status.poison && Math.random() < 0.3) {
        this.sparks.spawn({ x: e.x + (Math.random() - 0.5) * 0.4, y: gy + 0.8, z: e.z + (Math.random() - 0.5) * 0.4, vy: 0.6, life: 0.7, size: 0.08, color: 0x9aff5a, colorEnd: 0x3a8a20, shape: 2 });
      }
      if (tick && e.status.bleed && Math.random() < 0.3) {
        this.smoke.spawn({ x: e.x, y: gy + 0.9, z: e.z, vx: (Math.random() - 0.5), vy: 0.5, vz: (Math.random() - 0.5), gravity: 9, life: 0.5, size: 0.05, color: 0x8a1010, shape: 0, alpha: 0.9 });
      }
      if (tick && e.status.shock && Math.random() < 0.25) {
        this.sparks.spawn({ x: e.x + (Math.random() - 0.5) * 0.6, y: gy + 0.5 + Math.random(), z: e.z + (Math.random() - 0.5) * 0.6, life: 0.12, size: 0.25, color: 0xb8d0ff, shape: 3 });
      }
      if (tick && e.status.mark && Math.random() < 0.25) {
        this.sparks.spawn({ x: e.x, y: gy + 2.3, z: e.z, vy: 0.3, life: 0.5, size: 0.35, sizeEnd: 0.2, color: 0xff6a3a, shape: 2 });
      }
      if ((e.elite || e.named) && tick && Math.random() < 0.3) {
        const a = Math.random() * Math.PI * 2;
        this.sparks.spawn({ x: e.x + Math.cos(a) * e.radius * 1.3, y: gy + 0.1, z: e.z + Math.sin(a) * e.radius * 1.3, vy: 1.2, life: 0.9, size: 0.08, color: e.named ? 0xff5a3a : 0xffd070, drag: 0.5 });
      }
    });
  }

  /** Keep a decal for every live ground zone. */
  private zones(b: Battle) {
    const seen = new Set<number>();
    b.zones.forEach((z) => {
      const key = z.id * 7919 + Math.round(z.life * 1000);
      seen.add(key);
      if (this.zoneDecals.has(key)) return;
      const school = z.owner === 'enemy' ? z.school : schoolOfArt(z.art) === 'physical' ? z.school : schoolOfArt(z.art);
      const pal = SCHOOL[school];
      const kind = z.owner === 'enemy' ? (z.school === 'fire' ? 3 : 4)
        : school === 'holy' ? 2 : school === 'fire' ? 3 : school === 'shadow' ? 10 : school === 'frost' ? 5 : school === 'nature' ? (/blight|plague/.test(z.art) ? 4 : 6) : 7;
      const color2 = kind === 3 ? new THREE.Color('#ff3a0a').multiplyScalar(1.2) : kind === 4 ? new THREE.Color('#1a2a10') : kind === 10 ? new THREE.Color('#0a0610') : pal.dim;
      const zz = z;
      const d = this.decals.circle(z.x, z.z, z.radius, kind, pal.glow.clone().multiplyScalar(kind === 10 ? 0.6 : 0.9), {
        life: z.life - z.age, color2, additive: kind !== 10 && kind !== 4, fadeIn: 0.2, fadeOut: 0.4,
        follow: z.follow ? () => ({ x: zz.x, z: zz.z }) : null,
      });
      this.zoneDecals.set(key, d);
    });
    for (const k of [...this.zoneDecals.keys()]) if (!seen.has(k)) this.zoneDecals.delete(k);
  }
}
