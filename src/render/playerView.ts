import * as THREE from 'three';
import { CharacterView } from './characterView';
import type { Paint } from './recolor';
import type { CharacterModel } from './assets';
import type { PersonSpec } from './people';
import type { Battle } from '@/sim/battle';
import { damp } from '@/core/math';

/* The survivor on screen: the one character that gets a full skeleton,
 * blended clips and a light of their own.
 *
 * Reads the simulation's player state every frame and turns it into motion:
 * running that matches ground speed, a roll on a dash, the sword actually
 * swinging when the blade weapon fires (alternating chops, a heavy two-hand
 * swing for wide arcs), a flinch when struck, an arc through the air on a
 * leap, and a fall that stays down. The carried light is the ember itself -
 * it gutters when you are hurt and flares when you level. */

export interface Loadout {
  model: CharacterModel;
  show: string[];
  attackClips: string[];
  heavyClip: string;
  castClip?: string;
  /** A plain multiply over the cloth (for figures without a painted look). */
  tint?: string;
  /** The survivor's look: swatches of the atlas repainted (render/recolor.ts);
   *  the cloak's own on top of the body's. */
  paint?: { body: Paint; cloak: Paint };
  /** A person (render/people.ts) rather than the KayKit model: the body,
   *  outfit and hair, the weapons in hand (render/arms.ts) and the stance
   *  they stand in. */
  person?: PersonSpec;
  wield?: { right?: string; left?: string; forearm?: string };
  idle?: string;
}

/** The figure a loadout makes, dressed and armed (the survivor, portraits,
 *  the figure by the title's fire). */
export function dressedView(lo: Loadout, opts: { scale?: number } = {}) {
  const v = new CharacterView(lo.person ?? lo.model, opts);
  if (lo.person) {
    if (lo.wield?.right) v.wield('handslot.r', lo.wield.right);
    if (lo.wield?.left) v.wield('handslot.l', lo.wield.left);
    if (lo.wield?.forearm) v.wield('forearm.l', lo.wield.forearm);
  } else {
    v.showOnly(lo.show);
    applyLook(v, lo);
  }
  if (lo.idle) v.idleClip = lo.idle;
  else if (lo.model === 'mage' || lo.model === 'knight') v.idleClip = 'Idle';
  return v;
}

/** Apply a loadout's colours to a character view (the survivor, portraits). */
export function applyLook(view: { tintParts(c: string, m: RegExp): void; paint(body: Paint, cloak?: Paint): void }, lo: Loadout) {
  if (lo.paint) view.paint(lo.paint.body, lo.paint.cloak);
  else if (lo.tint) view.tintParts(lo.tint, CLOTH);
}

export const LOADOUTS: Record<string, Loadout> = {
  warden: { model: 'knight', show: ['1H_Sword', 'Round_Shield', 'Knight_Cape'], attackClips: ['1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Slice_Horizontal', '1H_Melee_Attack_Chop'], heavyClip: '1H_Melee_Attack_Chop' },
  reaver: { model: 'barbarian', show: ['2H_Axe', 'Barbarian_Cape'], attackClips: ['2H_Melee_Attack_Slice', '2H_Melee_Attack_Chop'], heavyClip: '2H_Melee_Attack_Spin' },
  arcanist: { model: 'mage', show: ['2H_Staff', 'Mage_Hat', 'Mage_Cape'], attackClips: ['Spellcast_Shoot'], heavyClip: 'Spellcast_Raise', castClip: 'Spellcast_Shoot' },
  stalker: { model: 'rogue_hooded', show: ['1H_Crossbow', 'Rogue_Cape', 'Knife_Offhand'], attackClips: ['1H_Ranged_Shoot'], heavyClip: 'Dualwield_Melee_Attack_Slice' },
};

/** Parts that are cloth or armour, not skin: what a palette recolours. */
export const CLOTH = /Cape|Hat|Helmet|Body|Leg/;

export class PlayerView {
  readonly view: CharacterView;
  readonly light: THREE.PointLight;
  private lastAttack = -1;
  private swing = 0;
  private dashing = false;
  private hurtSeen = 0;
  private dead = false;
  private flare = 0;
  private lightBase = 5;
  private castT = 0;

  constructor(readonly loadout: Loadout, scene: THREE.Object3D) {
    this.view = dressedView(loadout);
    scene.add(this.view.root);
    this.light = new THREE.PointLight(0xffb070, this.lightBase, 11, 1.4);
    this.light.castShadow = false;
    scene.add(this.light);
  }

  levelFlare() { this.flare = 1; }

  /** Up again after a fall (the prologue's second chances). */
  revive() {
    this.dead = false;
    this.view.act('Lie_StandUp', { blocksLegs: true, speed: 1.2 });
  }

  update(b: Battle, dt: number, time: number, heightAt: (x: number, z: number) => number) {
    const p = b.player;
    const v = this.view;
    let y = heightAt(p.x, p.z);
    if (p.leap) {
      const k = Math.min(1, p.leap.t / p.leap.dur);
      y += Math.sin(k * Math.PI) * 2.2;
    }
    v.root.position.set(p.x, y, p.z);

    if (!p.alive) {
      if (!this.dead) {
        this.dead = true;
        v.act('Death_A', { clamp: true, blocksLegs: true, fade: 0.1 });
      }
      v.update(dt);
      this.light.intensity = damp(this.light.intensity, 0.6, 2, dt);
      this.light.position.set(p.x, y + 1.2, p.z);
      return;
    }

    const speed = Math.hypot(p.vx, p.vz);
    // Face where you are going, or where you just struck.
    if (p.attackAnim && time - p.attackAnim.t < 0.35) v.face(Math.PI / 2 - p.attackAnim.angle);
    else if (speed > 0.4) v.face(Math.atan2(p.vx, p.vz));

    // Dash: a roll.
    if (p.dashT > 0 && !this.dashing) {
      this.dashing = true;
      v.face(Math.atan2(p.dashDX, p.dashDZ), true);
      v.act('Dodge_Forward', { speed: 1.9, blocksLegs: true, fade: 0.05 });
    } else if (p.dashT <= 0) this.dashing = false;

    if (p.leap && p.leap.t < dt * 2) v.act('Jump_Full_Short', { speed: 1.3, blocksLegs: true });

    // Weapon swings: the blade weapon drives the arm.
    if (p.attackAnim && p.attackAnim.t !== this.lastAttack) {
      this.lastAttack = p.attackAnim.t;
      const clip = p.attackAnim.heavy ? this.loadout.heavyClip : this.loadout.attackClips[this.swing++ % this.loadout.attackClips.length];
      v.act(clip, { speed: 1.6, fade: 0.05 });
    }
    // Casters raise a hand now and then as their spells go.
    this.castT -= dt;
    if (this.loadout.castClip && this.castT <= 0 && b.weapons.length && !v.busy && speed < 3) {
      this.castT = 1.6;
      v.act(this.loadout.castClip, { speed: 1.4 });
    }

    // Flinch.
    if (p.hurtT > 0.25 && this.hurtSeen <= 0) {
      this.hurtSeen = 0.4;
      v.hitFlash(0.32);
      if (!v.busy) v.act('Hit_A', { speed: 1.6 });
    }
    this.hurtSeen -= dt;

    v.locomotion(speed);
    v.update(dt);

    // The carried light: steadier at full health, guttering when hurt.
    const hp = p.hp / b.maxHp;
    this.flare = Math.max(0, this.flare - dt * 0.8);
    const flicker = Math.sin(time * 7.3) * 0.25 + Math.sin(time * 17.1) * 0.15 + (hp < 0.35 ? Math.sin(time * 31) * 0.6 : 0);
    this.light.intensity = this.lightBase * (0.7 + 0.3 * hp) + flicker + this.flare * 20;
    this.light.distance = 11 + this.flare * 6;
    this.light.position.set(p.x, y + 2.4, p.z + 0.4);
    // Invisible: fade toward a ghost.
    v.root.visible = !(p.invisibleT > 0 && Math.floor(time * 12) % 3 === 0);
  }
}
