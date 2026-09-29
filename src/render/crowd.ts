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
/** How long the dead lie where they fell, then how long the ground takes
 *  to swallow them; and how many may lie about at once. */
const CORPSE_LIE = 16;
const CORPSE_SINK = 3;
const CORPSE_MAX = 160;

interface Corpse { visual: string; x: number; z: number; facing: number; scale: number; tint: THREE.Color; glow: number; born: number }

/** What the renderer keeps per creature between frames (the simulation
 *  pools creatures, so a new one in an old slot is known by its seed). */
interface Gait { seed: number; phase: number; walking: boolean; facing: number }

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
  /** The dead, kept by the renderer after the simulation lets them go. */
  private corpses: Corpse[] = [];
  private laidOut = new Set<string>();
  private battle: Battle | null = null;
  private time = 0;
  private dt = 0;
  private gaits = new Map<number, Gait>();

  constructor() { this.group.name = 'crowd'; }

  /** Bake ahead of time (behind the fade) so the first wolf does not hitch
   *  the frame. Bakes are kept for the session (render/vat.ts), so a zone
   *  visited again costs nothing. */
  prepare(visuals: Iterable<string>) {
    for (const v of visuals) this.crowd(v, true);
  }

  private crowd(visual: string, ahead = false) {
    let c = this.crowds.get(visual);
    if (!c) {
      // A bake in play stalls the frame: the zone should have listed it.
      if (!ahead) console.warn(`crowd: ${visual} baked mid-play (list its creature in the zone's creatures)`);
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
    if (b !== this.battle) { this.battle = b; this.corpses = []; this.laidOut.clear(); this.gaits.clear(); }
    this.dt = THREE.MathUtils.clamp(time - this.time, 0, 0.1);
    this.time = time;
    for (const c of this.crowds.values()) c.begin();
    const items = b.enemies.items;
    for (let i = 0; i < items.length; i++) {
      const e = items[i];
      if (!e.alive) continue;
      this.draw(e, heightAt, time);
    }
    // The dead after the living, so a full crowd drops a body, not a foe.
    this.drawCorpses(heightAt, time);
    for (const c of this.crowds.values()) c.end(time);
  }

  private draw(e: Enemy, heightAt: (x: number, z: number) => number, time: number) {
    // Bosses with a full skeleton are drawn by their zone.
    if (e.def.visual.startsWith('view:')) return;
    const crowd = this.crowd(e.def.visual);
    let role: AnimRole = 'idle';
    let t = e.animT;
    let dissolve = 0;
    let y = heightAt(e.x, e.z);
    const speed = Math.hypot(e.vx, e.vz);
    let g = this.gaits.get(e.id);
    if (!g || g.seed !== e.seed) this.gaits.set(e.id, g = { seed: e.seed, phase: e.seed * 7, walking: false, facing: e.facing });
    // Walking or standing, with a margin between the two, so a creature
    // jostled at the edge of walking pace does not flicker between clips.
    g.walking = speed > (g.walking ? 0.2 : 0.45);
    switch (e.state) {
      case 'rising':
        role = 'rise';
        t = e.animT * (crowd.clipDuration('rise') / RISE_TIME);
        break;
      case 'dying': {
        // Burst apart: there is nothing left to fall (gore.ts threw it).
        if (e.burst) return;
        role = 'die';
        const dieClip = crowd.clipDuration('die');
        t = e.dieT * Math.max(1, dieClip / (DIE_TIME * 0.62));
        // Summons fade; the rest fall and stay (a corpse, below).
        if (e.disposition === 'ally') dissolve = THREE.MathUtils.smoothstep(e.dieT, DIE_TIME * 0.55, DIE_TIME);
        else if (e.dieT >= DIE_TIME - 0.12) this.layOut(e, g.facing);
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
        else if (g.walking) {
          // Its own walk clock, run faster or slower with its pace: time
          // times pace would leap to a new pose at every change of speed.
          role = 'move';
          g.phase += this.dt * THREE.MathUtils.clamp(speed / Math.max(0.5, e.def.speed), 0.6, 1.6);
          t = g.phase;
        } else { role = 'idle'; t = time + e.seed * 9; }
    }
    // Turned toward where it is going when it walks (steered round a tree or
    // shouldered by the crowd, it does not moonwalk), toward what it wants
    // when it stands or strikes; never in a single frame.
    const aim = g.walking && e.state === 'active' && e.anim !== 'attack' ? Math.atan2(e.vz, e.vx) : e.facing;
    if (e.state !== 'dying') {
      const turn = Math.atan2(Math.sin(aim - g.facing), Math.cos(aim - g.facing));
      g.facing += turn * Math.min(1, this.dt * (e.state === 'active' && e.anim !== 'attack' ? 9 : 18));
    }
    const sc = e.def.scale ?? 1;
    // Struck: a squash, and a flinch along the blow, gone in a tenth of a
    // second (the flash's own life).
    const f = e.state === 'dying' ? 0 : e.flash;
    this.p.set(e.x + e.lastDx * f * 0.14, y, e.z + e.lastDz * f * 0.14);
    this.q.setFromAxisAngle(this.up, Math.PI / 2 - g.facing);
    this.s.set(sc * (1 + f * 0.1), sc * (1 - f * 0.1), sc * (1 + f * 0.1));
    this.m.compose(this.p, this.q, this.s);
    const frozen = e.status.frozen ? 1 : e.status.chill ? Math.min(0.5, e.status.chill.stacks * 0.09) : 0;
    const burning = e.status.burn ? 1 : 0;
    let glow = visualTint(e.def.visual, this.tint);
    if (e.elite) { glow = Math.max(glow, 0.05); this.tint.multiply(this.glowTint.setRGB(1.08, 1.02, 0.92)); }
    if (e.named) { glow = 0.25; this.tint.multiply(this.glowTint.setRGB(1.3, 0.75, 0.6)); }
    if (e.disposition === 'neutral' && !e.provoked) this.tint.multiplyScalar(0.95);
    crowd.push(this.m, role, t, e.flash, dissolve, frozen, burning, this.tint, glow);
  }

  private layOut(e: Enemy, facing: number) {
    const key = `${e.id}:${e.seed}`;
    if (this.laidOut.has(key)) return;
    this.laidOut.add(key);
    const tint = new THREE.Color();
    const glow = visualTint(e.def.visual, tint);
    this.corpses.push({ visual: e.def.visual, x: e.x, z: e.z, facing, scale: e.def.scale ?? 1, tint, glow: glow * 0.3, born: this.time });
    if (this.corpses.length > CORPSE_MAX) this.corpses.shift();
  }

  private drawCorpses(heightAt: (x: number, z: number) => number, time: number) {
    this.corpses = this.corpses.filter((c) => time - c.born < CORPSE_LIE + CORPSE_SINK);
    for (const c of this.corpses) {
      const crowd = this.crowd(c.visual);
      const age = time - c.born;
      const sink = THREE.MathUtils.smoothstep(age, CORPSE_LIE, CORPSE_LIE + CORPSE_SINK);
      this.p.set(c.x, heightAt(c.x, c.z) - sink * 1.1 * c.scale, c.z);
      this.q.setFromAxisAngle(this.up, Math.PI / 2 - c.facing);
      this.s.setScalar(c.scale);
      this.m.compose(this.p, this.q, this.s);
      // Dead flesh greys a little as it lies.
      this.tint.copy(c.tint).multiplyScalar(1 - Math.min(0.25, age * 0.02));
      crowd.push(this.m, 'die', crowd.clipDuration('die') * 0.999, 0, sink > 0.6 ? (sink - 0.6) * 2.5 : 0, 0, 0, this.tint, c.glow);
    }
  }
}
