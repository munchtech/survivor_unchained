import * as THREE from 'three';
import { CharacterView } from '@/render/characterView';
import type { NpcDef } from '@/content/npcs';
import type { BarkLayer } from '@/ui/hud/barks';
import { dampAngle } from '@/core/math';

/* People standing in the world.
 *
 * An actor keeps to its spot and its pose. When the survivor comes near it
 * turns to look at them; when they leave it goes back to what it was doing.
 * Now and then, when someone walks past, it says something to the air. In
 * conversation it faces you and moves its hands. */

export class NpcActor {
  readonly view: CharacterView;
  x: number;
  z: number;
  private facing: number;
  private barkT: number;
  talking = false;
  hidden = false;
  /** After dark: they say different things. */
  night = false;
  private poseLoop: string;

  constructor(readonly def: NpcDef, parent: THREE.Object3D, private heightAt: (x: number, z: number) => number, private barks: BarkLayer | null, at?: { x: number; z: number; facing: number }) {
    const spot = at ?? def.spot;
    this.x = spot.x; this.z = spot.z; this.facing = spot.facing;
    const v = new CharacterView(def.model, { scale: 0.8 * (def.scale ?? 1) });
    v.showOnly(def.show);
    // Their cloth in their own colour (the calling's swatches, repainted).
    if (def.tint) v.paint({ cloth: def.tint });
    this.poseLoop = def.idle;
    v.loop(def.idle, 0, def.idle === '1H_Melee_Attack_Chop' ? 0.55 : 1);
    v.face(spot.facing, true);
    parent.add(v.root);
    this.view = v;
    this.barkT = 6 + Math.random() * 14;
  }

  get seated() { return this.poseLoop.startsWith('Sit'); }
  get pose() { return this.poseLoop; }

  /** Somewhere else now (a routine, a change in their circumstances). */
  place(spot: { x: number; z: number; facing: number }, idle = this.def.idle) {
    this.x = spot.x; this.z = spot.z; this.facing = spot.facing;
    this.view.face(spot.facing, true);
    if (idle !== this.poseLoop) {
      this.poseLoop = idle;
      this.view.loop(idle, 0.3, idle === '1H_Melee_Attack_Chop' ? 0.55 : 1);
    }
  }

  update(dt: number, px: number, pz: number) {
    const v = this.view;
    v.root.visible = !this.hidden;
    if (this.hidden) return;
    const y = this.heightAt(this.x, this.z) + (this.poseLoop === 'Sit_Chair_Idle' ? 0.05 : 0);
    v.root.position.set(this.x, y, this.z);
    const d = Math.hypot(px - this.x, pz - this.z);
    const toPlayer = Math.atan2(px - this.x, pz - this.z);
    // Look at whoever comes close; seated people only turn a little.
    let want = this.facing;
    if (this.talking || d < 5.5) {
      want = toPlayer;
      if (this.seated) want = this.facing + Math.max(-0.7, Math.min(0.7, Math.atan2(Math.sin(toPlayer - this.facing), Math.cos(toPlayer - this.facing))));
    }
    v.heading = dampAngle(v.heading, want, 4, dt);
    v.face(v.heading);
    // A hammering smith stops to talk.
    if (this.talking && this.poseLoop === '1H_Melee_Attack_Chop') { v.loop('Idle', 0.3); this.poseLoop = 'Idle:talk'; }
    if (!this.talking && this.poseLoop === 'Idle:talk') { v.loop(this.def.idle, 0.4, 0.55); this.poseLoop = this.def.idle; }
    v.update(dt);
    // Things said to nobody.
    this.barkT -= dt;
    if (this.barkT <= 0 && !this.talking && d < 9 && d > 2.5 && this.barks) {
      this.barkT = 30 + Math.random() * 30;
      const pool = this.night && this.def.nightBarks?.length ? this.def.nightBarks : this.def.barks;
      const line = pool[Math.floor(Math.random() * pool.length)];
      this.barks.speech(line, undefined, this.x, y + (this.def.scale ?? 1) * 0.4 - 0.2, this.z);
    }
  }

  /** A gesture while speaking. */
  gesture() {
    if (this.seated || this.poseLoop === 'Spellcasting') return;
    const clips = ['Interact', 'Cheer', 'Idle_B'];
    this.view.act(clips[Math.floor(Math.random() * 2)], { speed: 0.9 });
  }

  dispose() { this.view.dispose(); }
}

/* ------------------------------------------------------------ nameplates -- */

export interface PlateInfo { name: string; role?: string; marker?: '!' | '?' | null }

interface Plate { el: HTMLDivElement; name: HTMLDivElement; role: HTMLDivElement; mark: HTMLDivElement; key: string }

const v3 = new THREE.Vector3();

/** Names over heads, and the marks that say someone has something for you. */
export class PlateLayer {
  readonly root: HTMLDivElement;
  private plates = new Map<string, Plate>();

  constructor(parent: HTMLElement) {
    this.root = document.createElement('div');
    this.root.className = 'plates';
    parent.appendChild(this.root);
  }

  update(items: Array<{ id: string; x: number; y: number; z: number; info: PlateInfo }>, px: number, pz: number, camera: THREE.Camera, w: number, h: number, hush: Array<{ x: number; z: number }> = []) {
    const seen = new Set<string>();
    for (const it of items) {
      const d = Math.hypot(it.x - px, it.z - pz);
      if (d > 20) continue;
      seen.add(it.id);
      let p = this.plates.get(it.id);
      if (!p) {
        const el = document.createElement('div');
        el.className = 'plate';
        const mark = document.createElement('div'); mark.className = 'plate-mark';
        const name = document.createElement('div'); name.className = 'plate-name';
        const role = document.createElement('div'); role.className = 'plate-role';
        el.append(mark, name, role);
        this.root.appendChild(el);
        p = { el, name, role, mark, key: '' };
        this.plates.set(it.id, p);
      }
      const key = `${it.info.name}|${it.info.role ?? ''}|${it.info.marker ?? ''}`;
      if (key !== p.key) {
        p.key = key;
        p.name.textContent = it.info.name;
        p.role.textContent = it.info.role ?? '';
        p.mark.textContent = it.info.marker ?? '';
        p.mark.className = `plate-mark${it.info.marker === '!' ? ' new' : it.info.marker === '?' ? ' turn' : ''}`;
      }
      v3.set(it.x, it.y, it.z).project(camera);
      if (v3.z > 1) { p.el.style.opacity = '0'; continue; }
      const sx = (v3.x * 0.5 + 0.5) * w, sy = (-v3.y * 0.5 + 0.5) * h;
      const fadeIn = 1 - Math.max(0, Math.min(1, (d - 14) / 6));
      p.el.style.transform = `translate(${sx}px, ${sy}px) translate(-50%, -100%)`;
      // Someone speaking keeps their bubble; the plate steps aside.
      const speaking = hush.some((q) => Math.hypot(q.x - it.x, q.z - it.z) < 1.6);
      // Names give way to the interface: out near the top and bottom edges,
      // and under the zone's name in the corner.
      const clamp01 = (t: number) => Math.max(0, Math.min(1, t));
      const edge = clamp01((sy - 70) / 50) * clamp01((h - 130 - sy) / 50) * clamp01((sx - 30) / 40) * clamp01((w - 30 - sx) / 40);
      const corner = 1 - clamp01((sx - (w - 380)) / 60) * clamp01((190 - sy) / 50);
      p.el.style.opacity = String(speaking ? 0 : fadeIn * edge * corner);
      p.el.classList.toggle('near', d < 5);
    }
    for (const [id, p] of this.plates) if (!seen.has(id)) { p.el.remove(); this.plates.delete(id); }
  }

  clear() {
    for (const p of this.plates.values()) p.el.remove();
    this.plates.clear();
  }
}
