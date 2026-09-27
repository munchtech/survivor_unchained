import * as THREE from 'three';
import { bakeVat, VatCrowd, type AnimRole } from './vat';
import { visualSpec, visualTint } from './visuals';
import type { Battle } from '@/sim/battle';
import type { Enemy } from '@/sim/entities';
import { DIE_TIME } from '@/sim/ai';

/* The horde on screen: one VatCrowd per kind of creature, refilled every
 * frame from the simulation. Deciding which clip a creature plays, and how
 * far into it, lives here - the simulation only says what it is doing. */

const RISE_TIME = 1.1;

export class CrowdRenderer {
  readonly group = new THREE.Group();
  private crowds = new Map<string, VatCrowd>();
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private p = new THREE.Vector3();
  private s = new THREE.Vector3();
  private up = new THREE.Vector3(0, 1, 0);
  private tint = new THREE.Color();
  private glowTint = new THREE.Color();
  /** Bake timings, for the loading screen and the log. */
  bakeMs: Record<string, number> = {};

  constructor() { this.group.name = 'crowd'; }

  /** Bake ahead of time so the first wolf does not hitch the frame. */
  prepare(visuals: Iterable<string>) {
    for (const v of visuals) this.crowd(v);
  }

  private crowd(visual: string) {
    let c = this.crowds.get(visual);
    if (!c) {
      const t0 = performance.now();
      const asset = bakeVat(visualSpec(visual));
      c = new VatCrowd(asset, visual.startsWith('wolf') || visual === 'skeleton_minion' ? 400 : 200);
      this.bakeMs[visual] = Math.round(performance.now() - t0);
      c.mesh.name = `crowd:${visual}`;
      this.crowds.set(visual, c);
      this.group.add(c.mesh);
    }
    return c;
  }

  update(b: Battle, heightAt: (x: number, z: number) => number, time: number) {
    for (const c of this.crowds.values()) c.begin();
    const items = b.enemies.items;
    for (let i = 0; i < items.length; i++) {
      const e = items[i];
      if (!e.alive) continue;
      this.draw(e, heightAt, time);
    }
    for (const c of this.crowds.values()) c.end(time);
  }

  private draw(e: Enemy, heightAt: (x: number, z: number) => number, time: number) {
    const crowd = this.crowd(e.def.visual);
    let role: AnimRole = 'idle';
    let t = e.animT;
    let dissolve = 0;
    let y = heightAt(e.x, e.z);
    const speed = Math.hypot(e.vx, e.vz);
    switch (e.state) {
      case 'rising':
        role = 'rise';
        t = e.animT * (crowd.clipDuration('rise') / RISE_TIME);
        break;
      case 'dying': {
        role = 'die';
        const dieClip = crowd.clipDuration('die');
        t = e.dieT * Math.max(1, dieClip / (DIE_TIME * 0.62));
        dissolve = THREE.MathUtils.smoothstep(e.dieT, DIE_TIME * 0.55, DIE_TIME);
        break;
      }
      case 'burrowed':
        role = 'burrow';
        y -= 0.25;
        t = time + e.seed * 3;
        break;
      case 'surfacing':
        role = 'rise';
        t = (0.55 - e.stateT) * 1.2;
        break;
      case 'windup':
        role = 'windup';
        t = time;
        break;
      case 'casting':
        role = 'cast';
        t = time;
        break;
      case 'lunging':
        role = 'move';
        t = time * 1.8 + e.seed * 5;
        break;
      default:
        if (e.anim === 'attack' && e.animT < crowd.clipDuration('attack')) { role = 'attack'; t = e.animT; }
        else if (speed > 0.35) { role = 'move'; t = (time + e.seed * 7) * THREE.MathUtils.clamp(speed / Math.max(0.5, e.def.speed), 0.6, 1.6); }
        else { role = 'idle'; t = time + e.seed * 9; }
    }
    const sc = e.def.scale ?? 1;
    this.p.set(e.x, y, e.z);
    this.q.setFromAxisAngle(this.up, Math.PI / 2 - e.facing);
    this.s.setScalar(sc);
    this.m.compose(this.p, this.q, this.s);
    const frozen = e.status.frozen ? 1 : e.status.chill ? Math.min(0.5, e.status.chill.stacks * 0.09) : 0;
    const burning = e.status.burn ? 1 : 0;
    let glow = visualTint(e.def.visual, this.tint);
    if (e.elite) { glow = Math.max(glow, 0.05); this.tint.multiply(this.glowTint.setRGB(1.08, 1.02, 0.92)); }
    if (e.named) { glow = 0.25; this.tint.multiply(this.glowTint.setRGB(1.3, 0.75, 0.6)); }
    if (e.disposition === 'neutral' && !e.provoked) this.tint.multiplyScalar(0.95);
    crowd.push(this.m, role, t, e.flash, dissolve, frozen, burning, this.tint, glow);
  }
}
