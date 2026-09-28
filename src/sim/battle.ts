import { Rng } from '@/core/rng';
import { clamp, TAU } from '@/core/math';
import { ENEMIES, scaleFor, type EnemyDef } from '@/content/enemies';
import { WEAPONS, MAX_WEAPONS, WEAPON_MAX_RANK, type StatusPayload } from '@/content/weapons';
import { BOONS } from '@/content/boons';
import { ABILITIES, DASH, type AbilityKind } from '@/content/abilities';
import { SYNERGY_PAIRS } from '@/content/discoveries';
import { EventStream } from './events';
import { SpatialHash } from './spatial';
import { CollisionWorld, FlowField } from './collision';
import { StatBlock, armorReduction, type StatKey } from './stats';
import {
  Pool, blankEnemy, blankProjectile, blankZone, blankPickup,
  type Enemy, type Projectile, type GroundZone, type Pickup, type PickupKind,
} from './entities';
import { makeWeapon, tickWeapon, schoolOf, tagsOf, cooldownOf, type WeaponInst } from './weapons';
import type { TriggerDef, TriggerEvent, TriggerInstance, Effect, TriggerCond } from './procs';
import type { School, Tag, FactionId, StatusKind } from './types';
import { updateEnemy } from './ai';
import { chainFrom } from './weapons';

/* One fight, from the first creature to the last: the survivor, the horde,
 * everything in the air and on the ground, and the rules that connect them.
 *
 * It knows nothing about towns, quests or save files. The world layer builds
 * a Battle for an area (with the survivor's stats, kit and the area's
 * collision), hooks the events it cares about, and reads the outcome. In
 * town the same Battle runs with combat off, so walking, colliding and the
 * camera are one system everywhere. */

export interface PlayerState {
  x: number; z: number;
  vx: number; vz: number;
  facing: number;
  radius: number;
  hp: number;
  alive: boolean;
  iframes: number;
  hurtT: number;
  dashCharges: number;
  dashRecharge: number;
  dashT: number;
  dashDX: number; dashDZ: number;
  abilityCd: number;
  abilityActive: number;
  moving: boolean;
  stillT: number;
  slowT: number;
  slowF: number;
  blockT: number;
  shield: number;
  shieldT: number;
  invisibleT: number;
  sureCritT: number;
  bulwarkT: number;
  leap: { t: number; dur: number; x0: number; z0: number; x1: number; z1: number } | null;
  attackAnim: { weapon: string; angle: number; t: number; heavy: boolean } | null;
  /** Standing in a hazard: burning, poisoned. */
  burnT: number; burnDps: number;
  poisonT: number; poisonDps: number;
  revives: number;
  lastKiller: Enemy | null;
}

export interface BattleHooks {
  /** Every death, player-caused or not. */
  onKill?(e: Enemy, byPlayer: boolean): void;
  /** Extra drops for a death (items, materials). */
  /** What a creature drops besides ember and gold. `rarity` colours an item's
   *  beam of light (and, for gear, is the rarity it is made at). */
  onLoot?(e: Enemy): Array<{ kind: PickupKind; ref: string | null; value: number; persistent?: boolean; rarity?: number }>;
  /** An item/material/quest pickup reached the survivor. Return false to
   *  leave it on the ground (a full pack). */
  onPickup?(p: Pickup): boolean;
  /** The survivor fell. Return true if something saved them. */
  onPlayerDeath?(killer: Enemy | null): boolean;
  /** A boss or scripted creature's per-tick behaviour. */
  bossTick?(e: Enemy, dt: number): boolean;
  /** Something damaged a tagged collider (a barrel, a bramble wall, a ward). */
  onHitProp?(tag: string, colliderId: number, school: School, damage: number, x: number, z: number): void;
}

export interface BattleSetup {
  seed: number;
  collision: CollisionWorld;
  heightAt: (x: number, z: number) => number;
  combat: boolean;
  stats: StatBlock;
  start: { x: number; z: number; facing?: number };
  weapons: Array<{ id: string; rank: number }>;
  triggers?: Array<{ def: TriggerDef; source: string }>;
  ability: AbilityKind | null;
  hostility?: Partial<Record<FactionId, FactionId[]>>;
  /** Carried ember from an expedition that did not end. */
  ember?: { level: number; xp: number };
  hp?: number;
}

export interface Offer {
  kind: 'weapon' | 'rank' | 'boon' | 'evolve' | 'heal' | 'gold';
  id: string;
  /** For evolve: which branch. */
  branch?: string;
  rarity: string;
  title: string;
  text: string;
  from?: number;
  to?: number;
  icon: string;
  tags: string[];
}

const DEFAULT_WAR: Partial<Record<FactionId, FactionId[]>> = {
  pack: ['kerchief', 'lampling', 'dead'],
  kerchief: ['pack', 'wild', 'dead'],
  dead: ['pack', 'kerchief', 'wild', 'lampling'],
  wild: ['kerchief'],
  lampling: ['pack'],
};

interface Strike { x: number; z: number; r: number; dmg: number; school: School; tags: readonly Tag[]; t: number; weapon: WeaponInst | null; owner: 'player' | 'enemy'; depth: number }
interface Buff { t: number; stacks: number; stat: StatKey; value: number; kind: 'inc' | 'more' | 'flat'; max: number }

export interface HitOpts {
  weapon?: WeaponInst;
  crit?: boolean;
  canCrit?: boolean;
  knockback?: number;
  dirX?: number; dirZ?: number;
  status?: StatusPayload | null;
  dot?: boolean;
  depth?: number;
  bossDamage?: number;
  /** Damage from the survivor's summons. */
  summon?: boolean;
  /** Projectile direction, for frontal guards. */
  fromX?: number; fromZ?: number;
  projectile?: boolean;
  noProcs?: boolean;
  execute?: boolean;
  /** A deliberate blow that may start a fight with a neutral creature. */
  provoke?: boolean;
}

export class Battle {
  time = 0;
  readonly rng: Rng;
  readonly events = new EventStream();
  readonly stats: StatBlock;
  readonly player: PlayerState;
  weapons: WeaponInst[] = [];
  boons: Record<string, number> = {};
  triggers: TriggerInstance[] = [];
  readonly enemies = new Pool(blankEnemy, 900);
  readonly projectiles = new Pool(blankProjectile, 1400);
  readonly zones = new Pool(blankZone, 160);
  readonly pickups = new Pool(blankPickup, 1400);
  readonly spatial: SpatialHash;
  readonly collision: CollisionWorld;
  readonly flow: FlowField;
  heightAt: (x: number, z: number) => number;
  combat: boolean;
  hooks: BattleHooks = {};
  ability: AbilityKind | null;
  war: Partial<Record<FactionId, FactionId[]>>;
  /** Recent deaths, for grave-callers and necromancy. */
  graves: Array<{ x: number; z: number; def: string; t: number }> = [];
  private strikes: Strike[] = [];
  buffs = new Map<string, Buff>();
  ember = { level: 1, xp: 0, next: 12 };
  pendingLevels = 0;
  discoveries = new Set<string>();
  /** Where the fight is coming from, for the adaptive director. */
  profile = { projectile: 0, area: 0, melee: 0, summon: 0, still: 0, moving: 0 };
  killCount = 0;
  killsByFamily: Record<string, number> = {};
  damageTaken = 0;
  goldGained = 0;
  /** Aim point for directional abilities (pointer on the ground), if any. */
  aim: { x: number; z: number } | null = null;
  /** Time-slip: everything but the survivor runs at this rate. */
  worldRate = 1;
  worldRateT = 0;
  over: null | 'death' | 'victory' | 'left' = null;
  /** Equipped item ids and the statuses gear applies, for evolution
   *  catalysts and the draft. */
  gearIds = new Set<string>();
  gearStatuses = new Set<StatusKind>();
  bannedCards = new Set<string>();
  /** What the survivor's calling favours (skill tags), for the draft. */
  favours = new Set<string>();
  rerolls = 2;
  banishes = 1;
  private q: number[] = [];
  private retreatT = 0;

  constructor(s: BattleSetup) {
    this.rng = new Rng(s.seed);
    this.collision = s.collision;
    this.heightAt = s.heightAt;
    this.combat = s.combat;
    this.stats = s.stats;
    this.ability = s.ability;
    this.war = s.hostility ?? DEFAULT_WAR;
    this.spatial = new SpatialHash(s.collision.size, 3, 900);
    this.flow = new FlowField(s.collision, 44);
    const maxHp = this.stats.get('maxHealth');
    this.player = {
      x: s.start.x, z: s.start.z, vx: 0, vz: 0, facing: s.start.facing ?? 0, radius: 0.42,
      hp: s.hp ?? maxHp, alive: true, iframes: 0, hurtT: 0,
      dashCharges: Math.round(this.stats.get('dashCharges')), dashRecharge: 0, dashT: 0, dashDX: 0, dashDZ: 0,
      abilityCd: 0, abilityActive: 0, moving: false, stillT: 0, slowT: 0, slowF: 1, blockT: 0, shield: 0, shieldT: 0,
      invisibleT: 0, sureCritT: 0, bulwarkT: 0, leap: null, attackAnim: null, burnT: 0, burnDps: 0, poisonT: 0, poisonDps: 0,
      revives: 0, lastKiller: null,
    };
    for (const w of s.weapons) this.addWeapon(w.id, w.rank);
    for (const t of s.triggers ?? []) this.addTrigger(t.def, t.source);
    if (s.ember) {
      this.ember.level = s.ember.level;
      this.ember.xp = s.ember.xp;
      this.ember.next = emberNeed(s.ember.level);
    }
  }

  /* ============================================================== tick == */

  tick(dt: number, moveX: number, moveZ: number) {
    if (this.over) return;
    this.time += dt;
    if (this.worldRateT > 0) {
      this.worldRateT -= dt;
      if (this.worldRateT <= 0) this.worldRate = 1;
    }
    const wdt = dt * this.worldRate;

    this.rebuildSpatial();
    this.updatePlayer(dt, moveX, moveZ);
    this.flow.update(this.player.x, this.player.z);
    if (this.combat) {
      for (const w of this.weapons) tickWeapon(this, w, dt);
      this.tickAuras(dt);
      this.tickTriggers(dt);
    }
    this.enemies.forEach((e) => updateEnemy(this, e, wdt));
    this.updateProjectiles(dt, wdt);
    this.updateZones(dt);
    this.updateStrikes(dt);
    this.updatePickups(dt);
    this.updateBuffs(dt);
    if (this.graves.length > 40) this.graves.splice(0, this.graves.length - 40);
  }

  private rebuildSpatial() {
    this.spatial.clear();
    const items = this.enemies.items;
    for (let i = 0; i < items.length; i++) {
      const e = items[i];
      if (e.alive && e.state !== 'dying' && e.state !== 'burrowed') this.spatial.insert(e.id, e.x, e.z);
    }
  }

  /* ============================================================ player == */

  private updatePlayer(dt: number, mx: number, mz: number) {
    const p = this.player;
    if (!p.alive) return;
    const st = this.stats;
    p.iframes = Math.max(0, p.iframes - dt);
    p.hurtT = Math.max(0, p.hurtT - dt);
    p.abilityCd = Math.max(0, p.abilityCd - dt);
    p.invisibleT = Math.max(0, p.invisibleT - dt);
    p.sureCritT = Math.max(0, p.sureCritT - dt);
    p.bulwarkT = Math.max(0, p.bulwarkT - dt);
    p.slowT = Math.max(0, p.slowT - dt);
    if (p.slowT <= 0) p.slowF = 1;
    if (p.shieldT > 0) { p.shieldT -= dt; if (p.shieldT <= 0) p.shield = 0; }
    if (p.attackAnim && this.time - p.attackAnim.t > 0.6) p.attackAnim = null;

    // Dash charges come back one at a time.
    const maxCharges = Math.round(st.get('dashCharges'));
    if (p.dashCharges < maxCharges) {
      p.dashRecharge += dt / st.get('dashCooldown');
      if (p.dashRecharge >= DASH.recharge) { p.dashRecharge = 0; p.dashCharges++; }
    }

    // Warding light recharges.
    const blockRank = Math.round(st.get('block'));
    if (blockRank > 0 && p.blockT > 0) p.blockT = Math.max(0, p.blockT - dt);

    // Regeneration and hazards on the survivor.
    const regen = st.get('regen');
    if (regen > 0 && p.hp < this.maxHp) this.healPlayer(regen * dt, 'regen', true);
    if (p.burnT > 0) { p.burnT -= dt; this.hurtPlayerRaw(p.burnDps * dt, 'fire', 'burning', null, true); }
    if (p.poisonT > 0) { p.poisonT -= dt; this.hurtPlayerRaw(p.poisonDps * dt, 'nature', 'poison', null, true); }

    // Leaping: an arc through the air, untouchable until landing.
    if (p.leap) {
      p.leap.t += dt;
      const k = Math.min(1, p.leap.t / p.leap.dur);
      p.x = p.leap.x0 + (p.leap.x1 - p.leap.x0) * k;
      p.z = p.leap.z0 + (p.leap.z1 - p.leap.z0) * k;
      p.iframes = Math.max(p.iframes, 0.05);
      if (k >= 1) { this.landLeap(); p.leap = null; }
      this.collision.resolve(p, p.radius, true);
      return;
    }

    // Dashing: fast, fixed direction, invulnerable.
    if (p.dashT > 0) {
      p.dashT -= dt;
      const sp = DASH.distance / DASH.time;
      p.x += p.dashDX * sp * dt;
      p.z += p.dashDZ * sp * dt;
      this.collision.resolve(p, p.radius, true);
      return;
    }

    let speed = st.get('moveSpeed') * p.slowF;
    if (p.bulwarkT > 0) speed *= 0.45;
    // Standing in your own slowing ground does not slow you; enemy mud does.
    const targetVX = mx * speed, targetVZ = mz * speed;
    const accel = 1 - Math.exp(-dt * 14);
    p.vx += (targetVX - p.vx) * accel;
    p.vz += (targetVZ - p.vz) * accel;
    p.x += p.vx * dt;
    p.z += p.vz * dt;
    this.collision.resolve(p, p.radius, true);
    const sp = Math.hypot(p.vx, p.vz);
    p.moving = sp > 0.6;
    if (p.moving) {
      p.facing = Math.atan2(p.vx, p.vz);
      p.stillT = 0;
      this.profile.moving += dt;
    } else {
      p.stillT += dt;
      this.profile.still += dt;
    }
    const conds: Array<'moving' | 'still' | 'lowHealth' | 'fullHealth' | 'afterDash'> = [p.moving ? 'moving' : 'still'];
    if (p.hp < this.maxHp * 0.35) conds.push('lowHealth');
    if (p.hp >= this.maxHp - 0.01) conds.push('fullHealth');
    this.stats.setActive(conds);
  }

  get maxHp() { return Math.max(1, this.stats.get('maxHealth')); }

  /** Space: a short, invulnerable burst of movement. */
  dash(dirX: number, dirZ: number) {
    const p = this.player;
    if (!p.alive || p.dashCharges <= 0 || p.dashT > 0 || p.leap) return false;
    let dx = dirX, dz = dirZ;
    if (Math.hypot(dx, dz) < 0.1) { dx = Math.sin(p.facing); dz = Math.cos(p.facing); }
    const m = Math.hypot(dx, dz);
    p.dashDX = dx / m; p.dashDZ = dz / m;
    p.dashT = DASH.time;
    p.iframes = Math.max(p.iframes, DASH.iframes);
    p.dashCharges--;
    const x0 = p.x, z0 = p.z;
    this.events.emit({ t: 'dash', x0, z0, x1: x0 + p.dashDX * DASH.distance, z1: z0 + p.dashDZ * DASH.distance });
    this.fire('dash', { x: p.x, z: p.z });
    return true;
  }

  /** Q: the ability chosen at creation. */
  useAbility(dirX: number, dirZ: number) {
    const p = this.player;
    if (!this.combat || !p.alive || !this.ability || p.abilityCd > 0 || p.leap) return false;
    const def = ABILITIES[this.ability];
    let ax = dirX, az = dirZ;
    if (this.aim) { ax = this.aim.x - p.x; az = this.aim.z - p.z; }
    if (Math.hypot(ax, az) < 0.1) { ax = Math.sin(p.facing); az = Math.cos(p.facing); }
    const m = Math.hypot(ax, az);
    ax /= m; az /= m;
    const angle = Math.atan2(az, ax);
    const power = this.stats.get('abilityPower');
    p.abilityCd = def.cooldown * this.stats.get('abilityCooldown');
    switch (def.id) {
      case 'shield_bash': {
        this.events.emit({ t: 'ability', id: def.id, x: p.x, z: p.z, angle, radius: 3.4 });
        this.forEachHostileInRadius(p.x, p.z, 3.4, (e, d) => {
          let da = Math.atan2(e.z - p.z, e.x - p.x) - angle;
          da = Math.atan2(Math.sin(da), Math.cos(da));
          if (Math.abs(da) > 1.2) return;
          this.hitEnemy(e, 22 * power, 'physical', ['melee', 'physical'], { knockback: 2.4, dirX: (e.x - p.x) / (d || 1), dirZ: (e.z - p.z) / (d || 1), canCrit: true });
          this.applyStatus(e, { kind: 'stun', chance: 1, power: 1, duration: e.boss ? 0.6 : 1.5 }, 0);
          this.interrupt(e);
        });
        this.events.emit({ t: 'shake', amount: 0.35 });
        break;
      }
      case 'bulwark':
        p.bulwarkT = 3;
        this.events.emit({ t: 'ability', id: def.id, x: p.x, z: p.z, angle, radius: 2 });
        break;
      case 'leap': {
        const dist = Math.min(7, this.aim ? Math.hypot(this.aim.x - p.x, this.aim.z - p.z) : 7);
        const x1 = p.x + ax * dist, z1 = p.z + az * dist;
        p.leap = { t: 0, dur: 0.42, x0: p.x, z0: p.z, x1, z1 };
        this.events.emit({ t: 'ability', id: def.id, x: x1, z: z1, angle, radius: 3 });
        break;
      }
      case 'warcry':
        this.events.emit({ t: 'ability', id: def.id, x: p.x, z: p.z, angle, radius: 8 });
        this.forEachHostileInRadius(p.x, p.z, 8, (e) => {
          if (!e.elite && !e.boss) this.applyStatus(e, { kind: 'fear', chance: 1, power: 1, duration: 2.5 }, 0);
          this.interrupt(e);
        });
        this.addBuff('warcry', 'damage', 0.25 * power, 'inc', 6, 1);
        break;
      case 'blink': {
        const x0 = p.x, z0 = p.z;
        const tx = p.x + ax * 6, tz = p.z + az * 6;
        // Blink as far along the line as is open ground.
        let best = 0;
        for (let k = 1; k <= 12; k++) {
          const x = x0 + (tx - x0) * (k / 12), z = z0 + (tz - z0) * (k / 12);
          if (!this.collision.blocked(x, z, p.radius)) best = k;
        }
        p.x = x0 + (tx - x0) * (best / 12);
        p.z = z0 + (tz - z0) * (best / 12);
        p.iframes = Math.max(p.iframes, 0.3);
        this.events.emit({ t: 'ability', id: def.id, x: x0, z: z0, angle, radius: 3 });
        this.events.emit({ t: 'dash', x0, z0, x1: p.x, z1: p.z });
        this.forEachHostileInRadius(x0, z0, 3.2, (e) => {
          this.hitEnemy(e, 14 * power, 'frost', ['spell', 'frost', 'area'], { status: { kind: 'chill', chance: 1, power: 3, duration: 3 } });
        });
        break;
      }
      case 'time_slip':
        this.worldRate = 1 / 3;
        this.worldRateT = 3.5 * power;
        this.events.emit({ t: 'ability', id: def.id, x: p.x, z: p.z, angle, radius: 30 });
        this.enemies.forEach((e) => this.interrupt(e));
        break;
      case 'mark_prey': {
        let best: Enemy | null = null;
        this.forEachHostileInRadius(p.x, p.z, 16, (e) => { if (!best || e.maxHp > best.maxHp) best = e; });
        if (!best) { p.abilityCd = 0.5; return false; }
        const t = best as Enemy;
        this.applyStatus(t, { kind: 'mark', chance: 1, power: 2, duration: 8 }, 0);
        t.tag = t.tag ?? 'prey';
        this.events.emit({ t: 'ability', id: def.id, x: t.x, z: t.z, angle, radius: 1 });
        break;
      }
      case 'smoke_bomb':
        p.invisibleT = 3;
        p.sureCritT = 3.5;
        this.events.emit({ t: 'ability', id: def.id, x: p.x, z: p.z, angle, radius: 4 });
        this.enemies.forEach((e) => { if (e.target === -1) { e.target = -2; e.retargetT = 3; } });
        break;
    }
    this.fire('ability', { x: p.x, z: p.z });
    return true;
  }

  private landLeap() {
    const p = this.player;
    const power = this.stats.get('abilityPower');
    this.events.emit({ t: 'explosion', x: p.x, z: p.z, radius: 3, school: 'physical', power: 1 });
    this.events.emit({ t: 'shake', amount: 0.5 });
    this.forEachHostileInRadius(p.x, p.z, 3, (e, d) => {
      this.hitEnemy(e, 34 * power, 'physical', ['melee', 'area', 'physical'], { knockback: 2, dirX: (e.x - p.x) / (d || 1), dirZ: (e.z - p.z) / (d || 1), canCrit: true });
      this.interrupt(e);
    });
  }

  /** Stop a channel or cast in progress. */
  interrupt(e: Enemy) {
    if (e.state === 'casting' || e.state === 'windup') {
      e.state = 'stunned';
      e.stateT = 0.8;
      e.raiseT = Math.max(e.raiseT, 3);
      this.events.emit({ t: 'bark', x: e.x, z: e.z, text: 'Interrupted!' });
    }
  }

  /* =========================================================== queries == */

  /** Can the survivor's side hurt this creature? */
  hostileToPlayer(e: Enemy) {
    if (!e.alive || e.state === 'dying' || e.state === 'burrowed') return false;
    if (e.disposition === 'ally') return false;
    if (e.disposition === 'neutral') return e.provoked;
    return true;
  }

  /** Targetable by weapons: hostile, or neutral (you can pick a fight). */
  targetable(e: Enemy) {
    return e.alive && e.state !== 'dying' && e.state !== 'burrowed' && e.disposition !== 'ally' && (e.disposition === 'hostile' || e.provoked);
  }

  factionsAtWar(a: FactionId, b: FactionId) {
    if (a === b) return false;
    return !!(this.war[a]?.includes(b) || this.war[b]?.includes(a));
  }

  nearestHostile(x: number, z: number, r: number, filter?: (e: Enemy) => boolean): Enemy | null {
    let best: Enemy | null = null, bd = r * r;
    this.spatial.query(x, z, r, this.q);
    for (const id of this.q) {
      const e = this.enemies.items[id];
      if (!this.targetable(e) || (filter && !filter(e))) continue;
      const d = (e.x - x) ** 2 + (e.z - z) ** 2;
      if (d < bd) { bd = d; best = e; }
    }
    return best;
  }

  hostilesInRadius(x: number, z: number, r: number): Enemy[] {
    const out: Enemy[] = [];
    this.spatial.query(x, z, r, this.q);
    for (const id of this.q) {
      const e = this.enemies.items[id];
      if (this.targetable(e) && (e.x - x) ** 2 + (e.z - z) ** 2 <= (r + e.radius) ** 2) out.push(e);
    }
    return out;
  }

  forEachHostileInRadius(x: number, z: number, r: number, fn: (e: Enemy, d: number) => void) {
    const list = this.hostilesInRadius(x, z, r);
    for (const e of list) fn(e, Math.hypot(e.x - x, e.z - z));
  }

  forEachHostileNearSegment(x0: number, z0: number, x1: number, z1: number, w: number, fn: (e: Enemy) => void) {
    const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
    const half = Math.hypot(x1 - x0, z1 - z0) / 2 + w + 1;
    const dx = x1 - x0, dz = z1 - z0, l2 = dx * dx + dz * dz;
    for (const e of this.hostilesInRadius(cx, cz, half)) {
      const t = clamp(((e.x - x0) * dx + (e.z - z0) * dz) / l2, 0, 1);
      const d = Math.hypot(e.x - (x0 + dx * t), e.z - (z0 + dz * t));
      if (d <= w / 2 + e.radius) fn(e);
    }
  }

  /** The hostile with the most other hostiles around it. */
  densestHostile(x: number, z: number, r: number, cluster: number): Enemy | null {
    const list = this.hostilesInRadius(x, z, r);
    let best: Enemy | null = null, bn = -1;
    for (let i = 0; i < list.length; i += Math.max(1, Math.floor(list.length / 24))) {
      const e = list[i];
      let n = 0;
      for (const o of list) if ((o.x - e.x) ** 2 + (o.z - e.z) ** 2 < cluster * cluster) n++;
      if (n > bn) { bn = n; best = e; }
    }
    return best;
  }

  /* ========================================================= damage in == */

  /** Everything the survivor's side does to a creature passes through here. */
  hitEnemy(e: Enemy, base: number, school: School, tags: readonly Tag[], o: HitOpts = {}): number {
    if (!e.alive || e.state === 'dying') return 0;
    // The survivor's side never hurts its allies, and never hurts a
    // creature minding its own business by accident: auras, ground fires
    // and swings that happen to reach a neutral pass it by. Picking a fight
    // is a choice (a word, a match to the powder), not a stray spark.
    if (e.disposition === 'ally' || (e.disposition === 'neutral' && !e.provoked && !o.provoke)) return 0;
    const st = this.stats;
    let dmg = base * st.damageMult(school, tags, e.def.family);
    if (o.summon) dmg *= st.get('summonDamage');
    if (e.boss || e.elite) dmg *= o.bossDamage ?? o.weapon?.def.bossDamage ?? 1;
    // Vulnerabilities.
    const s = e.status;
    if (s.mark) dmg *= 1 + 0.3 * (s.mark.power || 1);
    if (s.frozen) dmg *= this.boons.deep_chill ? 1.35 : 1.15;
    if (s.sear && school === 'holy') dmg *= 1.3;
    if (s.shock && !o.dot) { dmg *= 1.35; if (!this.boons.static_charge) delete s.shock; }
    dmg *= e.takenMul;
    // Resistances.
    const res = e.def.resists?.[school] ?? 0;
    dmg *= 1 - res;
    // Frontal guard: projectiles into a raised shield mostly glance off.
    let blocked = false;
    if (o.projectile && e.def.guard && e.state !== 'stunned' && !s.frozen && !s.stun) {
      const fx = Math.cos(e.facing), fz = Math.sin(e.facing);
      const ix = -(o.fromX ?? 0), iz = -(o.fromZ ?? 0);
      const dot = fx * ix + fz * iz;
      if (dot > Math.cos(e.def.guard.arc / 2)) { dmg *= 1 - e.def.guard.reduction; blocked = true; }
    }
    if (e.takenMul < 0.7) blocked = true;
    // Criticals.
    let crit = o.crit ?? false;
    if (!crit && o.canCrit !== false && !o.dot) {
      const chance = st.get('critChance') + (this.player.sureCritT > 0 ? 1 : 0);
      crit = this.rng.next() < chance;
    }
    if (crit) dmg *= st.get('critDamage');
    dmg = Math.max(0.5, dmg);

    const before = e.hp;
    e.hp -= dmg;
    e.flash = 1;
    e.lastSchool = school;
    e.lastWeapon = o.weapon?.id ?? null;
    if (e.disposition === 'neutral') this.provoke(e);
    if (o.weapon) o.weapon.damageDealt += Math.min(dmg, before);
    // Where the damage is coming from, for the director.
    if (tags.includes('summon') || o.summon) this.profile.summon += dmg;
    else if (tags.includes('projectile')) this.profile.projectile += dmg;
    else if (tags.includes('melee')) this.profile.melee += dmg;
    else this.profile.area += dmg;

    this.events.emit({ t: 'hit', x: e.x, z: e.z, amount: dmg, crit, school, target: e.id, dot: o.dot, blocked });

    // Lifesteal.
    const ls = st.get('lifesteal');
    if (ls > 0 && !o.dot) this.healPlayer(dmg * ls, 'lifesteal', true);

    // Knockback: heavier things move less, bosses not at all.
    if (o.knockback && !e.boss && e.def.behavior !== 'stationary') {
      const k = o.knockback * st.get('knockback') * 7 / Math.max(0.5, e.mass) * (e.elite ? 0.35 : 1);
      e.kbx += (o.dirX ?? 0) * k;
      e.kbz += (o.dirZ ?? 0) * k;
    }

    // Status payloads ride the hit.
    if (o.status) this.applyStatus(e, o.status, dmg, o.depth);

    const depth = o.depth ?? 0;
    if (!o.noProcs && depth < 3) {
      const ctx = { target: e, x: e.x, z: e.z, damage: dmg, school, tags, crit, weapon: o.weapon, depth: depth + 1 };
      this.fire('hit', ctx);
      if (crit) this.fire('crit', ctx);
    }

    if (e.hp <= 0 && e.alive && (e.state as string) !== 'dying') this.killEnemy(e, true, o.weapon ?? null, depth);
    return dmg;
  }

  provoke(e: Enemy) {
    if (e.provoked) return;
    e.provoked = true;
    // A pack answers for its own.
    this.forEachEnemyNear(e.x, e.z, 12, (o) => {
      if (o.faction === e.faction && o.disposition === 'neutral') o.provoked = true;
    });
  }

  forEachEnemyNear(x: number, z: number, r: number, fn: (e: Enemy) => void) {
    this.spatial.query(x, z, r, this.q);
    for (const id of [...this.q]) {
      const e = this.enemies.items[id];
      if (e.alive && e.state !== 'dying' && (e.x - x) ** 2 + (e.z - z) ** 2 <= r * r) fn(e);
    }
  }

  killEnemy(e: Enemy, byPlayer: boolean, weapon: WeaponInst | null, depth = 0) {
    e.hp = 0;
    e.state = 'dying';
    e.stateT = 0;
    e.dieT = 0;
    e.anim = 'die';
    e.animT = 0;
    e.credit = byPlayer || e.credit;
    const credited = e.credit;
    if (weapon) weapon.kills++;
    if (credited && e.disposition !== 'ally') {
      this.killCount++;
      this.killsByFamily[e.def.family] = (this.killsByFamily[e.def.family] ?? 0) + 1;
    }
    this.events.emit({ t: 'kill', x: e.x, z: e.z, enemy: e.id, def: e.def.id, family: e.def.family, school: e.lastSchool, elite: e.elite, boss: e.boss, byPlayer: credited });
    this.graves.push({ x: e.x, z: e.z, def: e.def.id, t: this.time });

    if (e.disposition !== 'ally') {
      // The dead leave a stone with light still in it.
      const sc = scaleFor(e.level).xp;
      const xp = e.def.xp * sc;
      if (xp > 0) this.dropEmber(e.x, e.z, xp);
      if (credited) {
        const luck = this.stats.get('luck');
        if (e.def.gold && this.rng.next() < 0.55 + luck * 0.1) this.spawnPickup('gold', e.x, e.z, Math.ceil(e.def.gold * (0.6 + this.rng.next() * 0.8)));
        if (this.rng.next() < 0.012 * luck + (e.elite ? 0.4 : 0)) this.spawnPickup('heal', e.x, e.z, e.elite ? 40 : 25);
        if (this.rng.next() < 0.004 * luck) this.spawnPickup('magnet', e.x, e.z, 1);
        for (const d of this.hooks.onLoot?.(e) ?? []) {
          const pk = this.spawnPickup(d.kind, e.x, e.z, d.value, d.ref);
          if (pk && d.persistent) pk.persistent = true;
          if (pk && d.rarity !== undefined) pk.tier = d.rarity;
        }
      }
    }
    // Death verbs.
    if (e.def.burst) {
      const b = e.def.burst;
      this.events.emit({ t: 'telegraph', id: e.id, shape: 'circle', x: e.x, z: e.z, radius: b.radius, duration: b.fuse, hostile: true });
      this.strikes.push({ x: e.x, z: e.z, r: b.radius, dmg: e.damage * b.damagePct, school: b.school, tags: ['explosion'], t: b.fuse, weapon: null, owner: 'enemy', depth: 0 });
    }
    if (e.def.split) {
      for (let i = 0; i < e.def.split.count; i++) {
        const a = (i / e.def.split.count) * TAU;
        this.spawnEnemy(e.def.split.into, e.x + Math.cos(a) * 0.8, e.z + Math.sin(a) * 0.8, { level: e.level, style: 'walk', faction: e.faction });
      }
    }
    if (credited && depth < 3) this.fire('kill', { target: e, x: e.x, z: e.z, damage: e.maxHp, school: e.lastSchool, tags: [], crit: false, weapon: weapon ?? undefined, depth: depth + 1 });
    this.hooks.onKill?.(e, credited);
  }

  /* =========================================================== status == */

  applyStatus(e: Enemy, p: StatusPayload, hitDamage: number, depth = 0) {
    if (!e.alive || e.state === 'dying') return;
    const chance = p.chance * (1 + this.stats.get('statusChance'));
    if (this.rng.next() >= chance) return;
    const s = e.status;
    const sd = this.stats.get('statusDamage');
    const dps = (hitDamage * p.power / Math.max(0.5, p.duration)) * sd;
    switch (p.kind) {
      case 'burn': {
        const cur = s.burn ?? (s.burn = { t: 0, stacks: 0, power: 0, tick: 0.5 });
        cur.stacks = Math.min(5, cur.stacks + 1);
        cur.power = Math.max(cur.power, dps);
        cur.t = Math.max(cur.t, p.duration);
        break;
      }
      case 'bleed': {
        const cur = s.bleed ?? (s.bleed = { t: 0, stacks: 1, power: 0, tick: 0.5 });
        cur.power = Math.max(cur.power, dps);
        cur.t = Math.max(cur.t, p.duration);
        break;
      }
      case 'poison': {
        const cur = s.poison ?? (s.poison = { t: 0, stacks: 0, power: 0, tick: 0.5 });
        cur.stacks = Math.min(10, cur.stacks + 1);
        cur.power = Math.max(cur.power, dps);
        cur.t = Math.max(cur.t, p.duration);
        break;
      }
      case 'chill': {
        if (s.frozen) { s.frozen.t = Math.max(s.frozen.t, 0.4); break; }
        const cur = s.chill ?? (s.chill = { t: 0, stacks: 0, power: 0, tick: 0 });
        cur.stacks += p.power * (this.boons.deep_chill ? 2 : 1);
        cur.t = Math.max(cur.t, p.duration);
        if (cur.stacks >= 5 && !e.boss) {
          delete s.chill;
          s.frozen = { t: e.elite ? 0.9 : 1.7, stacks: 1, power: 0, tick: 0 };
          if (e.state === 'casting' || e.state === 'windup') this.interrupt(e);
          this.events.emit({ t: 'status', target: e.id, kind: 'frozen', x: e.x, z: e.z });
          if (depth < 3) this.fire('freeze', { target: e, x: e.x, z: e.z, damage: hitDamage, school: 'frost', tags: [], crit: false, depth: depth + 1 });
        }
        break;
      }
      case 'stun':
      case 'fear':
      case 'charm': {
        if (e.boss && p.kind !== 'stun') return;
        s[p.kind] = { t: Math.max(s[p.kind]?.t ?? 0, p.duration), stacks: 1, power: p.power, tick: 0 };
        break;
      }
      default: {
        const cur = s[p.kind] ?? (s[p.kind] = { t: 0, stacks: 1, power: p.power, tick: 0.5 });
        cur.t = Math.max(cur.t, p.duration);
        cur.power = Math.max(cur.power, p.power);
        if (p.kind === 'sear' && e.def.family === 'undead') cur.power = Math.max(cur.power, dps || 2);
      }
    }
    this.events.emit({ t: 'status', target: e.id, kind: p.kind, x: e.x, z: e.z });
    if (depth < 3) this.fire('status', { target: e, x: e.x, z: e.z, damage: hitDamage, school: 'physical', tags: [], crit: false, applied: p.kind, depth: depth + 1 });
  }

  /** Called by the AI each tick: status timers and damage over time. */
  tickStatus(e: Enemy, dt: number) {
    const s = e.status;
    for (const k of Object.keys(s) as StatusKind[]) {
      const slot = s[k]!;
      slot.t -= dt;
      if (k === 'burn' || k === 'bleed' || k === 'poison' || (k === 'sear' && e.def.family === 'undead')) {
        slot.tick -= dt;
        if (slot.tick <= 0) {
          slot.tick += 0.5;
          let d = slot.power * 0.5;
          if (k === 'burn') d *= slot.stacks;
          if (k === 'poison') d *= slot.stacks;
          if (k === 'bleed' && Math.hypot(e.vx, e.vz) > 0.5) d *= 1.6;
          const school: School = k === 'burn' ? 'fire' : k === 'bleed' ? 'physical' : k === 'sear' ? 'holy' : 'nature';
          if (d > 0) this.hitEnemy(e, d, school, ['dot', school], { dot: true, canCrit: false, noProcs: k !== 'burn', depth: 2 });
          if (!e.alive || (e.state as string) === 'dying') return;
        }
      }
      if (slot.t <= 0) delete s[k];
    }
  }

  /* ========================================================= damage out == */

  /** A creature's blow on the survivor, after dodge, block and armour. */
  hurtPlayer(amount: number, school: School, source: string, from: Enemy | null) {
    const p = this.player;
    if (!p.alive || !this.combat) return 0;
    if (p.iframes > 0 || p.leap) return 0;
    const st = this.stats;
    // Dodge.
    if (this.rng.next() < Math.min(0.75, st.get('dodge'))) {
      this.events.emit({ t: 'playerHit', x: p.x, z: p.z, amount: 0, school, source, dodged: true });
      this.fire('dodge', { x: p.x, z: p.z });
      return 0;
    }
    // Warding light.
    const blockRank = Math.round(st.get('block'));
    if (blockRank > 0 && p.blockT <= 0) {
      p.blockT = [12, 9, 6][Math.min(3, blockRank) - 1];
      p.iframes = 0.25;
      this.events.emit({ t: 'playerHit', x: p.x, z: p.z, amount: 0, school, source, blocked: true });
      this.fire('block', { x: p.x, z: p.z });
      return 0;
    }
    // Thorns answer before the armour question.
    const thorns = st.get('thorns');
    if (thorns > 0 && from && from.alive) {
      this.hitEnemy(from, (4 + amount * 0.2) * thorns, 'nature', ['aura'], { canCrit: false, noProcs: true });
    }
    let dmg = amount;
    let armor = st.get('armor');
    for (const z of this.zones.items) if (z.alive && z.armor > 0 && Math.hypot(z.x - p.x, z.z - p.z) < z.radius) armor += z.armor;
    dmg *= 1 - armorReduction(armor);
    dmg *= 1 - clamp(st.getRaw(`resist.${school}` as StatKey), -1, 0.8);
    if (from) dmg *= 1 - clamp(st.getRaw(`from.${from.def.family}` as StatKey), -1, 0.8);
    if (p.bulwarkT > 0) dmg *= 0.35;
    return this.hurtPlayerRaw(dmg, school, source, from);
  }

  hurtPlayerRaw(dmg: number, school: School, source: string, from: Enemy | null, silent = false) {
    const p = this.player;
    if (!p.alive || !this.combat) return 0;
    if (p.shield > 0) {
      const a = Math.min(p.shield, dmg);
      p.shield -= a;
      dmg -= a;
    }
    if (dmg <= 0) return 0;
    p.hp -= dmg;
    this.damageTaken += dmg;
    if (!silent) {
      // The Survivors contract: a crowd is dangerous, not instantly lethal.
      // Each blow buys a moment of invulnerability, so intake is capped by
      // rhythm rather than by how many creatures are touching you.
      p.hurtT = 0.3;
      p.iframes = Math.max(p.iframes, 0.45);
      this.events.emit({ t: 'playerHit', x: p.x, z: p.z, amount: dmg, school, source });
      this.fire('hurt', { x: p.x, z: p.z, damage: dmg });
    }
    if (from) p.lastKiller = from;
    if (p.hp <= 0) {
      if (p.revives > 0) {
        p.revives--;
        p.hp = this.maxHp * 0.5;
        p.iframes = 2;
        this.events.emit({ t: 'announce', title: 'You rise again', tone: 'boon' });
      } else if (this.hooks.onPlayerDeath?.(p.lastKiller)) {
        p.hp = Math.max(p.hp, 1);
      } else {
        p.hp = 0;
        p.alive = false;
        this.over = 'death';
        this.events.emit({ t: 'playerDeath', x: p.x, z: p.z, killer: p.lastKiller?.def.name ?? source, killerId: p.lastKiller?.id ?? -1 });
      }
    }
    return dmg;
  }

  healPlayer(amount: number, _source: string, silent = false) {
    const p = this.player;
    if (!p.alive) return;
    const h = amount * this.stats.get('healing');
    const before = p.hp;
    p.hp = Math.min(this.maxHp, p.hp + h);
    if (!silent && p.hp - before > 0.5) this.events.emit({ t: 'playerHeal', amount: p.hp - before });
  }

  /* ========================================================== spawning == */

  spawnEnemy(defId: string, x: number, z: number, o: { level?: number; style?: 'rise' | 'burrow' | 'walk' | 'drop'; faction?: FactionId; disposition?: Enemy['disposition']; elite?: boolean; tag?: string; home?: { x: number; z: number; leash: number } } = {}): Enemy | null {
    const def: EnemyDef | undefined = ENEMIES[defId];
    if (!def) throw new Error(`unknown enemy ${defId}`);
    const e = this.enemies.spawn();
    if (!e) return null;
    const lvl = o.level ?? 1;
    const sc = scaleFor(lvl);
    e.def = def;
    e.level = lvl;
    e.x = x; e.z = z; e.vx = 0; e.vz = 0; e.kbx = 0; e.kbz = 0;
    e.facing = Math.atan2(this.player.z - z, this.player.x - x);
    e.radius = def.radius;
    e.mass = def.mass ?? 1;
    e.maxHp = e.hp = def.health * sc.health * (o.elite && !def.elite ? 3 : 1);
    e.damage = def.damage * sc.damage;
    e.speed = def.speed * (0.92 + this.rng.next() * 0.16);
    e.faction = o.faction ?? def.faction;
    e.disposition = o.disposition ?? (def.faction === 'ally' ? 'ally' : 'hostile');
    e.elite = !!def.elite || !!o.elite;
    e.boss = !!def.boss;
    e.state = o.style === 'rise' ? 'rising' : o.style === 'burrow' ? 'burrowed' : 'active';
    e.stateT = o.style === 'rise' ? 1.1 : o.style === 'burrow' ? 0.3 : 0;
    e.attackT = 0.5 + this.rng.next() * 0.5;
    e.rangedT = (def.ranged?.cooldown ?? 3) * (0.4 + this.rng.next() * 0.6);
    e.raiseT = def.raise?.every ?? 0;
    e.target = e.disposition === 'ally' ? -2 : -1;
    e.retargetT = this.rng.next() * 0.5;
    e.slot = this.rng.next() * TAU;
    e.seed = this.rng.next();
    e.status = {};
    e.flash = 0;
    e.anim = o.style === 'rise' ? 'rise' : 'move';
    e.animT = 0;
    e.dieT = 0;
    e.lifeT = 0;
    e.named = undefined;
    e.tag = o.tag;
    e.credit = false;
    e.provoked = false;
    e.homeX = o.home?.x ?? x; e.homeZ = o.home?.z ?? z; e.leash = o.home?.leash ?? 0;
    e.lastWeapon = null;
    e.takenMul = 1;
    this.events.emit({ t: 'spawn', enemy: e.id, x, z, def: defId, style: o.style ?? 'walk' });
    return e;
  }

  spawnProjectile(o: Partial<Projectile> & { owner: Projectile['owner']; x: number; z: number; damage: number; school: School }): Projectile | null {
    const pr = this.projectiles.spawn();
    if (!pr) return null;
    const defaults = blankProjectile(pr.id);
    Object.assign(pr, defaults, o, { id: pr.id, alive: true, age: 0, hits: pr.hits, hitTimes: pr.hitTimes });
    pr.hits.length = 0;
    pr.hitTimes.length = 0;
    pr.hitCount = 0;
    const sp = Math.hypot(pr.vx, pr.vz);
    if (sp > 0) { pr.dirX = pr.vx / sp; pr.dirZ = pr.vz / sp; }
    return pr;
  }

  spawnZone(o: Partial<GroundZone> & { owner: GroundZone['owner']; x: number; z: number; radius: number; life: number; dps: number; school: School }): GroundZone | null {
    const z = this.zones.spawn();
    if (!z) return null;
    Object.assign(z, blankZone(z.id), { tick: 0.5 }, o, { id: z.id, alive: true, age: 0, tickT: 0 });
    return z;
  }

  spawnPickup(kind: PickupKind, x: number, z: number, value: number, ref: string | null = null): Pickup | null {
    const p = this.pickups.spawn();
    if (!p) return null;
    const a = this.rng.next() * TAU, v = 1.5 + this.rng.next() * 2;
    Object.assign(p, { kind, x, z, vx: Math.cos(a) * v, vz: Math.sin(a) * v, value, ref, age: 0, pulled: false, persistent: false, tier: 0 });
    if (kind === 'ember') p.tier = value >= 40 ? 3 : value >= 12 ? 2 : value >= 4 ? 1 : 0;
    return p;
  }

  private dropEmber(x: number, z: number, xp: number) {
    // Many small stones for a big creature reads better than one.
    let left = xp;
    let guard = 0;
    while (left > 0 && guard++ < 6) {
      const v = left > 40 ? Math.min(left, 40) : left;
      this.spawnPickup('ember', x + (this.rng.next() - 0.5), z + (this.rng.next() - 0.5), v);
      left -= v;
    }
  }

  scheduleStrike(x: number, z: number, r: number, dmg: number, school: School, tags: readonly Tag[], delay: number, weapon: WeaponInst | null, owner: 'player' | 'enemy' = 'player', depth = 0) {
    this.strikes.push({ x, z, r, dmg, school, tags, t: delay, weapon, owner, depth });
    this.events.emit({ t: 'strike', x, z, radius: r, school, delay });
    if (owner === 'enemy') this.events.emit({ t: 'telegraph', id: -1, shape: 'circle', x, z, radius: r, duration: delay, hostile: true });
  }

  /* ======================================================= projectiles == */

  private updateProjectiles(dt: number, wdt: number) {
    const p = this.player;
    const items = this.projectiles.items;
    for (let i = 0; i < items.length; i++) {
      const pr = items[i];
      if (!pr.alive) continue;
      const step = pr.owner === 'enemy' ? wdt : dt;
      pr.age += step;
      if (pr.age >= pr.life) { this.expireProjectile(pr); continue; }

      if (pr.orbitR > 0) {
        pr.orbitA += pr.orbitW * step;
        pr.x = p.x + Math.cos(pr.orbitA) * pr.orbitR;
        pr.z = p.z + Math.sin(pr.orbitA) * pr.orbitR;
        pr.dirX = -Math.sin(pr.orbitA); pr.dirZ = Math.cos(pr.orbitA);
      } else if (pr.lob) {
        // Lobbed: a parabola to the landing point, harmless until it lands.
        const k = pr.age / pr.life;
        pr.x += pr.vx * step;
        pr.z += pr.vz * step;
        pr.y = 0.6 + Math.sin(k * Math.PI) * 3.2;
        continue;
      } else {
        // Homing: turn toward the target, or find a new one.
        if (pr.homing > 0 && pr.owner !== 'enemy') {
          let t = pr.target >= 0 ? this.enemies.items[pr.target] : null;
          if (!t || !this.targetable(t) || pr.hits.includes(t.id)) {
            t = this.pickSeekTarget(pr);
            pr.target = t ? t.id : -2;
          }
          if (t) {
            const want = Math.atan2(t.z - pr.z, t.x - pr.x);
            const cur = Math.atan2(pr.vz, pr.vx);
            let d = want - cur;
            d = Math.atan2(Math.sin(d), Math.cos(d));
            const turn = clamp(d, -pr.homing * step, pr.homing * step);
            const a = cur + turn;
            pr.vx = Math.cos(a) * pr.speed;
            pr.vz = Math.sin(a) * pr.speed;
          }
        }
        if (pr.chakram && !pr.returning && pr.age > pr.life * 0.45) {
          pr.returning = true;
          pr.hits.length = 0; pr.hitTimes.length = 0;
        }
        if (pr.returning) {
          const a = Math.atan2(p.z - pr.z, p.x - pr.x);
          pr.vx = Math.cos(a) * pr.speed * 1.15;
          pr.vz = Math.sin(a) * pr.speed * 1.15;
          if (Math.hypot(p.x - pr.x, p.z - pr.z) < 0.8) { this.projectiles.release(pr); continue; }
        }
        pr.x += pr.vx * step;
        pr.z += pr.vz * step;
        const sp = Math.hypot(pr.vx, pr.vz);
        if (sp > 0) { pr.dirX = pr.vx / sp; pr.dirZ = pr.vz / sp; }
        // Walls stop bolts; hitting a tagged prop tells the world.
        if (!pr.chakram && this.collision.blocked(pr.x, pr.z, 0.05, false)) {
          const hit = this.collision.within(pr.x, pr.z, 0.6).find((c) => c.tag);
          if (hit?.tag) this.hooks.onHitProp?.(hit.tag, hit.id, pr.school, pr.damage, pr.x, pr.z);
          this.expireProjectile(pr, true);
          continue;
        }
      }

      if (pr.owner === 'enemy') {
        if (p.alive && Math.hypot(p.x - pr.x, p.z - pr.z) < pr.radius + p.radius) {
          if (p.bulwarkT > 0) {
            // Turned back on whoever loosed it.
            pr.owner = 'player'; pr.vx *= -1; pr.vz *= -1; pr.homing = 6; pr.target = pr.ownerId; pr.age = 0;
            pr.tags = ['projectile', 'physical'];
            continue;
          }
          const src = pr.ownerId >= 0 ? this.enemies.items[pr.ownerId] : null;
          this.hurtPlayer(pr.damage, pr.school, pr.art, src && src.alive ? src : null);
          if (pr.status?.kind === 'chill') { p.slowT = pr.status.duration; p.slowF = 0.6; }
          this.projectiles.release(pr);
        }
        continue;
      }

      // Player and ally projectiles against the horde.
      this.spatial.query(pr.x, pr.z, pr.radius + 1.2, this.q);
      for (const id of this.q) {
        const e = this.enemies.items[id];
        if (!this.targetable(e)) continue;
        const rr = pr.radius + e.radius;
        if ((e.x - pr.x) ** 2 + (e.z - pr.z) ** 2 > rr * rr) continue;
        const k = pr.hits.indexOf(e.id);
        if (k >= 0) {
          if (!pr.rehit || this.time - pr.hitTimes[k] < pr.rehit) continue;
          pr.hitTimes[k] = this.time;
        } else {
          pr.hits.push(e.id);
          pr.hitTimes.push(this.time);
        }
        this.projectileHit(pr, e);
        if (!pr.alive) break;
      }
    }
  }

  private pickSeekTarget(pr: Projectile): Enemy | null {
    const range = 14;
    if (pr.seek === 'elite' || pr.seek === 'strongest') {
      let best: Enemy | null = null;
      for (const e of this.hostilesInRadius(pr.x, pr.z, range)) {
        if (pr.hits.includes(e.id)) continue;
        if (!best || (e.elite || e.boss ? 1e6 : 0) + e.maxHp > (best.elite || best.boss ? 1e6 : 0) + best.maxHp) best = e;
      }
      return best;
    }
    if (pr.seek === 'marked') {
      const m = this.hostilesInRadius(pr.x, pr.z, range).find((e) => e.status.mark && !pr.hits.includes(e.id));
      if (m) return m;
    }
    return this.nearestHostile(pr.x, pr.z, range, (e) => !pr.hits.includes(e.id));
  }

  private projectileHit(pr: Projectile, e: Enemy) {
    const weapon = pr.weapon ? this.weapons.find((w) => w.id === pr.weapon) : undefined;
    this.hitEnemy(e, pr.damage, pr.school, pr.tags, {
      weapon, knockback: pr.knockback, dirX: pr.dirX, dirZ: pr.dirZ, status: pr.status, depth: pr.depth,
      bossDamage: pr.bossDamage, projectile: pr.tags.includes('projectile'), fromX: pr.dirX, fromZ: pr.dirZ,
      summon: pr.owner === 'ally',
    });
    if (pr.heal) this.healPlayer(pr.heal, 'weapon', true);
    pr.hitCount++;
    if (pr.splash > 0) this.explode(pr.x, pr.z, pr.splash, pr.damage * 0.75, pr.school, pr.tags, weapon ?? null, pr.depth, e.id);
    if (pr.groundOnHit) {
      const g = pr.groundOnHit;
      this.spawnZone({ owner: 'player', x: pr.x, z: pr.z, radius: g.radius * this.stats.get('area'), life: g.duration, dps: pr.damage * g.dpsPct, school: pr.school, tags: ['zone', pr.school], art: pr.art + '_ground', weapon: pr.weapon });
    }
    if (pr.splitOnHit > 0 && pr.depth < 1) {
      for (let i = 0; i < pr.splitOnHit; i++) {
        const a = Math.atan2(pr.vz, pr.vx) + (i - (pr.splitOnHit - 1) / 2) * 0.9 + Math.PI * (pr.splitOnHit > 3 ? i / pr.splitOnHit * 2 : 0);
        const sp = pr.speed * 0.85;
        const c = this.spawnProjectile({
          owner: pr.owner, x: pr.x, z: pr.z, y: pr.y, vx: Math.cos(a) * sp, vz: Math.sin(a) * sp, speed: sp,
          damage: pr.damage * 0.45, school: pr.school, tags: pr.tags, radius: pr.radius * 0.7, pierce: 0, life: 0.9,
          homing: Math.max(pr.homing, 3), weapon: pr.weapon, art: pr.art, status: pr.status, depth: pr.depth + 1, rank: pr.rank,
        });
        if (c) { c.hits.push(e.id); c.hitTimes.push(this.time); }
      }
    }
    if (pr.bounces > 0) {
      const next = this.nearestHostile(pr.x, pr.z, 8, (o) => !pr.hits.includes(o.id));
      if (next) {
        pr.bounces--;
        pr.target = next.id;
        const a = Math.atan2(next.z - pr.z, next.x - pr.x);
        pr.vx = Math.cos(a) * pr.speed; pr.vz = Math.sin(a) * pr.speed;
        pr.age = Math.min(pr.age, pr.life * 0.5);
        pr.damage *= 1.04;
        return;
      }
    }
    if (pr.orbitR > 0 || pr.rehit > 0) return;
    if (pr.pierce > 0) { pr.pierce--; return; }
    this.projectiles.release(pr);
  }

  private expireProjectile(pr: Projectile, hitWall = false) {
    if (pr.lob) {
      // A pot lands: a burst, and burning ground.
      if (pr.owner === 'enemy') {
        const p = this.player;
        const r = 1.6;
        this.events.emit({ t: 'explosion', x: pr.x, z: pr.z, radius: r, school: pr.school, power: 0.6 });
        if (Math.hypot(p.x - pr.x, p.z - pr.z) < r + p.radius) {
          const src = pr.ownerId >= 0 ? this.enemies.items[pr.ownerId] : null;
          this.hurtPlayer(pr.damage, pr.school, pr.art, src && src.alive ? src : null);
        }
        if (pr.groundOnHit) {
          this.spawnZone({ owner: 'enemy', x: pr.x, z: pr.z, radius: pr.groundOnHit.radius, life: pr.groundOnHit.duration, dps: pr.damage * pr.groundOnHit.dpsPct, school: pr.school, tags: ['zone'], art: 'zone_fire_enemy' });
        }
        // Fire spreads to whatever burns (bramble walls, powder kegs).
        for (const c of this.collision.within(pr.x, pr.z, r)) if (c.tag) this.hooks.onHitProp?.(c.tag, c.id, pr.school, pr.damage, pr.x, pr.z);
      }
    } else if (pr.splash > 0 && hitWall && pr.owner === 'player') {
      this.explode(pr.x, pr.z, pr.splash, pr.damage * 0.75, pr.school, pr.tags, null, pr.depth, -1);
    }
    this.projectiles.release(pr);
  }

  /** An area blast from the survivor's side. Raises 'explode' for procs. */
  explode(x: number, z: number, r: number, dmg: number, school: School, tags: readonly Tag[], weapon: WeaponInst | null, depth = 0, skip = -1) {
    this.events.emit({ t: 'explosion', x, z, radius: r, school, power: Math.min(2, dmg / 40) });
    const t2 = tags.includes('explosion') ? tags : [...tags, 'explosion' as Tag];
    this.forEachHostileInRadius(x, z, r, (e, d) => {
      if (e.id === skip) return;
      this.hitEnemy(e, dmg, school, t2, { weapon: weapon ?? undefined, knockback: 0.5, dirX: (e.x - x) / (d || 1), dirZ: (e.z - z) / (d || 1), depth: depth + 1 });
    });
    for (const c of this.collision.within(x, z, r)) if (c.tag) this.hooks.onHitProp?.(c.tag, c.id, school, dmg, x, z);
    if (depth < 3) this.fire('explode', { x, z, damage: dmg, school, tags: t2, crit: false, depth: depth + 1 });
  }

  /* ============================================================= zones == */

  private updateZones(dt: number) {
    const p = this.player;
    this.zones.forEach((z) => {
      z.age += dt;
      if (z.age >= z.life) { this.zones.release(z); return; }
      if (z.follow) { z.x = p.x; z.z = p.z; }
      z.tickT -= dt;
      if (z.tickT > 0) return;
      z.tickT = z.tick;
      if (z.owner === 'enemy' || z.owner === 'world') {
        if (Math.hypot(p.x - z.x, p.z - z.z) < z.radius + p.radius * 0.5) {
          this.hurtPlayer(z.dps * z.tick, z.school, 'burning ground', null);
          if (z.school === 'fire') { p.burnT = 1.5; p.burnDps = z.dps * 0.25; }
        }
        // World hazards hurt everything standing in them.
        if (z.owner === 'world') {
          this.forEachEnemyNear(z.x, z.z, z.radius, (e) => this.hitEnemy(e, z.dps * z.tick, z.school, ['zone'], { canCrit: false, noProcs: true, dot: true }));
        }
        return;
      }
      const weapon = z.weapon ? this.weapons.find((w) => w.id === z.weapon) : undefined;
      this.forEachHostileInRadius(z.x, z.z, z.radius, (e) => {
        this.hitEnemy(e, z.dps * z.tick, z.school, z.tags, { weapon, status: z.status, canCrit: true, bossDamage: z.bossDamage });
        if (z.slow > 0) { e.status.chill = e.status.chill ?? { t: 0, stacks: 0, power: 0, tick: 0 }; e.status.chill.t = Math.max(e.status.chill.t, z.tick + 0.1); e.status.chill.stacks = Math.max(e.status.chill.stacks, (1 - z.slow) * 8); }
      });
    });
  }

  private updateStrikes(dt: number) {
    for (let i = this.strikes.length - 1; i >= 0; i--) {
      const s = this.strikes[i];
      s.t -= dt;
      if (s.t > 0) continue;
      this.strikes.splice(i, 1);
      if (s.owner === 'enemy') {
        const p = this.player;
        this.events.emit({ t: 'explosion', x: s.x, z: s.z, radius: s.r, school: s.school, power: 1 });
        if (Math.hypot(p.x - s.x, p.z - s.z) < s.r + p.radius * 0.5) this.hurtPlayer(s.dmg, s.school, 'blast', null);
        // Death bursts hurt anything standing in them, which is the point of
        // killing a sapper next to its friends.
        this.forEachEnemyNear(s.x, s.z, s.r, (e) => { if (e.disposition !== 'ally') this.hitEnemy(e, s.dmg * 0.6, s.school, ['explosion'], { canCrit: false, noProcs: true }); });
        for (const c of this.collision.within(s.x, s.z, s.r)) if (c.tag) this.hooks.onHitProp?.(c.tag, c.id, s.school, s.dmg, s.x, s.z);
      } else {
        this.explode(s.x, s.z, s.r, s.dmg, s.school, s.tags, s.weapon, s.depth);
      }
    }
  }

  /* =========================================================== pickups == */

  private updatePickups(dt: number) {
    const p = this.player;
    const reach = this.stats.get('pickupRadius');
    this.pickups.forEach((k) => {
      k.age += dt;
      // Scatter, then settle.
      k.x += k.vx * dt; k.z += k.vz * dt;
      k.vx *= Math.exp(-dt * 5); k.vz *= Math.exp(-dt * 5);
      if (!p.alive) return;
      const dx = p.x - k.x, dz = p.z - k.z;
      const d = Math.hypot(dx, dz);
      const autoPull = k.kind === 'ember' || k.kind === 'gold' || k.kind === 'heal' || k.kind === 'magnet';
      if (autoPull && (k.pulled || (d < reach && k.age > 0.25))) {
        k.pulled = true;
        const sp = 4 + k.age * 2 + (k.pulled ? 10 : 0);
        k.x += (dx / (d || 1)) * Math.min(d, sp * dt);
        k.z += (dz / (d || 1)) * Math.min(d, sp * dt);
      }
      if (d < p.radius + 0.35 && (autoPull || k.age > 0.4)) this.collect(k);
      // Ember on the ground cools after a long while; gear does not.
      if (!k.persistent && k.kind === 'ember' && k.age > 90) this.pickups.release(k);
    });
  }

  private collect(k: Pickup) {
    switch (k.kind) {
      case 'ember': this.gainEmber(k.value); this.fire('ember', { x: k.x, z: k.z }); break;
      case 'gold': {
        const g = Math.round(k.value * this.stats.get('goldGain'));
        this.goldGained += g;
        break;
      }
      case 'heal': this.healPlayer(k.value * (this.maxHp / 100), 'potion'); break;
      case 'magnet': this.pickups.forEach((o) => { if (o.kind === 'ember' || o.kind === 'gold') o.pulled = true; }); break;
      default:
        if (this.hooks.onPickup && !this.hooks.onPickup(k)) { k.age = -2; return; }
    }
    this.events.emit({ t: 'pickup', kind: k.kind, amount: k.value, x: k.x, z: k.z });
    this.pickups.release(k);
  }

  gainEmber(v: number) {
    this.ember.xp += v * this.stats.get('xpGain');
    while (this.ember.xp >= this.ember.next) {
      this.ember.xp -= this.ember.next;
      this.ember.level++;
      this.ember.next = emberNeed(this.ember.level);
      this.pendingLevels++;
      this.events.emit({ t: 'levelUp', level: this.ember.level });
      this.fire('levelUp', { x: this.player.x, z: this.player.z });
    }
  }

  /* ============================================================ arsenal == */

  addWeapon(id: string, rank = 1) {
    if (!WEAPONS[id] || this.weapons.some((w) => w.id === id) || this.weapons.length >= MAX_WEAPONS) return null;
    const w = makeWeapon(id, rank, this.weapons.length);
    this.weapons.push(w);
    this.checkDiscoveries();
    return w;
  }

  removeWeapon(id: string) {
    const i = this.weapons.findIndex((w) => w.id === id);
    if (i < 0) return;
    this.weapons.splice(i, 1);
    this.weapons.forEach((w, k) => { w.slot = k; });
  }

  rankWeapon(id: string) {
    const w = this.weapons.find((x) => x.id === id);
    if (!w || w.rank >= WEAPON_MAX_RANK) return;
    w.rank++;
  }

  evolve(id: string, branch: string) {
    const w = this.weapons.find((x) => x.id === id);
    if (!w) return;
    const evo = w.def.evolutions.find((e) => e.id === branch);
    if (!evo) return;
    w.evolution = evo;
    this.events.emit({ t: 'evolve', weapon: w.id, into: evo.id });
    this.events.emit({ t: 'announce', kicker: `${w.def.name} evolves`, title: evo.name, subtitle: evo.description, tone: 'boon' });
  }

  addBoon(id: string) {
    const def = BOONS[id];
    if (!def) return;
    const r = (this.boons[id] ?? 0) + 1;
    if (r > def.max) return;
    this.boons[id] = r;
    this.stats.removeSource(`boon:${id}`);
    this.stats.removeSource(`syn:${id}`);
    if (def.mods) this.stats.addAll(def.mods(r).map((m) => ({ ...m, source: m.source ?? `boon:${id}` })));
    if (r === 1 && def.triggers) for (const t of def.triggers) this.addTrigger(t, `boon:${id}`);
    if (id === 'vitality') this.healPlayer(25, 'vitality');
    if (id === 'spirit_companion') this.summon('spirit_wolf', 0, 99);
    if (id === 'grave_call') this.summon('ghoul_ally', 0, 99);
  }

  addTrigger(def: TriggerDef, source: string, rank = 1) {
    this.triggers.push({ def, source, cd: 0, rank, count: 0 });
  }

  removeTriggers(source: string) {
    this.triggers = this.triggers.filter((t) => t.source !== source);
  }

  /** Weapon pairs that quietly do more together (The Ember Watch's
   *  discoveries). Recorded so the codex can remember them. */
  private checkDiscoveries() {
    const have = new Set(this.weapons.map((w) => w.id));
    for (const d of SYNERGY_PAIRS) {
      if (this.discoveries.has(d.id)) continue;
      if (!d.weapons.every((w) => have.has(w))) continue;
      this.discoveries.add(d.id);
      const [a, b] = d.weapons.map((id) => this.weapons.find((w) => w.id === id)!);
      d.apply(a, b, this);
      this.events.emit({ t: 'discovery', id: d.id });
      this.events.emit({ t: 'announce', kicker: 'Discovery', title: d.name, subtitle: d.description, tone: 'boon' });
    }
  }

  onWeaponFired(_w: WeaponInst) {
    // Reserved: momentum-style effects that care about firing.
  }

  /** Allies that fight for the survivor. */
  summon(kind: 'spirit_wolf' | 'ghoul_ally', life: number, max: number, x?: number, z?: number) {
    let n = 0;
    this.enemies.forEach((e) => { if (e.disposition === 'ally' && e.def.id === kind) n++; });
    if (n >= max) return null;
    const p = this.player;
    const a = this.rng.next() * TAU;
    const e = this.spawnEnemy(kind, x ?? p.x + Math.cos(a) * 1.5, z ?? p.z + Math.sin(a) * 1.5, { level: this.ember.level, disposition: 'ally', faction: 'ally', style: kind === 'ghoul_ally' ? 'rise' : 'walk' });
    if (e) {
      e.lifeT = life;
      e.maxHp = e.hp = e.def.health * (1 + 0.1 * this.ember.level);
      e.damage = e.def.damage * (1 + 0.08 * this.ember.level);
    }
    return e;
  }

  /* ============================================================ auras == */

  private auraT = 0;
  private tickAuras(dt: number) {
    const p = this.player;
    this.auraT -= dt;
    const chill = this.boons.chilling ?? 0;
    const sear = this.boons.searing ?? 0;
    if (!chill && !sear) return;
    const area = this.stats.get('area');
    if (chill) {
      const r = (2.4 + chill * 0.8) * area;
      this.forEachHostileInRadius(p.x, p.z, r, (e, d) => {
        if (e.boss) return;
        const k = 1 - d / r;
        const cur = e.status.chill ?? (e.status.chill = { t: 0, stacks: 0, power: 0, tick: 0 });
        cur.t = Math.max(cur.t, 0.3);
        cur.stacks = Math.max(cur.stacks, Math.min(4.5, (1.5 + chill) * k * 2));
      });
    }
    if (sear && this.auraT <= 0) {
      const r = (2.2 + sear * 0.5) * area;
      this.forEachHostileInRadius(p.x, p.z, r, (e) => {
        this.hitEnemy(e, 3 + sear * 3, 'holy', ['aura', 'holy', 'area'], { canCrit: true, noProcs: true });
      });
      this.events.emit({ t: 'nova', x: p.x, z: p.z, radius: r, school: 'holy', duration: 0.4, rings: 0 });
    }
    if (this.auraT <= 0) this.auraT = 0.5;
  }

  /* ============================================================= procs == */

  private tickTriggers(dt: number) {
    for (const t of this.triggers) {
      if (t.cd > 0) t.cd -= dt;
      if (t.def.on === 'tick' && t.cd <= 0) {
        t.cd = t.def.icd ?? 1;
        this.runEffects(t, { x: this.player.x, z: this.player.z, depth: 1 });
      }
    }
  }

  fire(on: TriggerEvent, ctx: ProcCtx) {
    for (const t of this.triggers) {
      if (t.def.on !== on) continue;
      if (t.cd > 0) continue;
      if (t.def.chance !== undefined && this.rng.next() >= t.def.chance) continue;
      if (t.def.when && !this.matches(t.def.when, ctx)) continue;
      if (t.def.icd) t.cd = t.def.icd;
      t.count++;
      this.runEffects(t, ctx);
    }
  }

  private matches(c: TriggerCond, ctx: ProcCtx) {
    const e = ctx.target;
    if (c.targetStatus && (!e || !e.status[c.targetStatus])) return false;
    if (c.targetFamily && (!e || e.def.family !== c.targetFamily)) return false;
    if (c.elite !== undefined && (!e || (e.elite || e.boss) !== c.elite)) return false;
    if (c.school && ctx.school !== c.school) return false;
    if (c.tag && !(ctx.tags ?? []).includes(c.tag)) return false;
    if (c.notTag && (ctx.tags ?? []).includes(c.notTag)) return false;
    if (c.weapon && ctx.weapon?.id !== c.weapon) return false;
    if (c.hpBelow !== undefined && (!e || e.hp / e.maxHp >= c.hpBelow)) return false;
    if (c.applied && ctx.applied !== c.applied) return false;
    if (c.selfHpBelow !== undefined && this.player.hp / this.maxHp >= c.selfHpBelow) return false;
    if (c.moving !== undefined && this.player.moving !== c.moving) return false;
    return true;
  }

  private runEffects(t: TriggerInstance, ctx: ProcCtx) {
    const depth = ctx.depth ?? 1;
    for (const fx of t.def.effects) this.runEffect(fx, ctx, depth, t.rank);
  }

  private base(fx: { damage: number; basis: string }, ctx: ProcCtx) {
    if (fx.basis === 'hit') return fx.damage * (ctx.damage ?? 0);
    if (fx.basis === 'maxhp') return fx.damage * (ctx.target?.maxHp ?? 0);
    return fx.damage * (1 + 0.08 * (this.ember.level - 1));
  }

  private runEffect(fx: Effect, ctx: ProcCtx, depth: number, _rank: number) {
    const x = ctx.x ?? this.player.x, z = ctx.z ?? this.player.z;
    switch (fx.do) {
      case 'explode':
        this.explode(x, z, fx.radius * this.stats.get('area'), this.base(fx, ctx), fx.school, ['explosion', fx.school], null, depth, -1);
        if (fx.status) this.forEachHostileInRadius(x, z, fx.radius, (e) => this.applyStatus(e, fx.status!, this.base(fx, ctx), depth));
        break;
      case 'status':
        if (fx.target === 'hit' && ctx.target) this.applyStatus(ctx.target, fx.status, ctx.damage ?? 10, depth);
        else {
          const list = this.hostilesInRadius(x, z, fx.radius ?? 8).sort((a, b) => b.maxHp - a.maxHp).slice(0, fx.count ?? 1);
          for (const e of list) this.applyStatus(e, fx.status, 20, depth);
        }
        break;
      case 'spread': {
        const src = ctx.target?.status[fx.kind];
        if (!src) break;
        const near = this.hostilesInRadius(x, z, fx.radius).filter((e) => e !== ctx.target).slice(0, fx.count);
        for (const e of near) {
          const s = e.status[fx.kind] ?? (e.status[fx.kind] = { t: 0, stacks: 0, power: 0, tick: 0.5 });
          s.stacks = Math.min(fx.kind === 'poison' ? 10 : 5, s.stacks + (fx.stacks ?? 1));
          s.power = Math.max(s.power, src.power);
          s.t = Math.max(s.t, 3);
          this.events.emit({ t: 'chain', points: [x, z, e.x, e.z], school: fx.kind === 'burn' ? 'fire' : 'nature' });
        }
        break;
      }
      case 'missiles': {
        for (let i = 0; i < fx.count; i++) {
          const a = this.rng.next() * TAU;
          const sp = fx.speed;
          this.spawnProjectile({
            owner: 'player', x, z, y: 1.2, vx: Math.cos(a) * sp, vz: Math.sin(a) * sp, speed: sp,
            damage: this.base(fx, ctx), school: fx.school, tags: ['projectile', fx.school], radius: 0.2, pierce: 0,
            life: 2.5, homing: 6, seek: fx.seek, target: -2, weapon: null, art: fx.art, status: fx.status ?? null, depth,
          });
        }
        break;
      }
      case 'chain': {
        const first = this.nearestHostile(x, z, fx.range, (e) => e !== ctx.target);
        if (first) chainFrom(this, x, z, first, fx.count - 1, fx.range, this.base(fx, ctx), fx.school, ['chain', fx.school], null, false, false, depth);
        break;
      }
      case 'heal':
        this.healPlayer(fx.basis === 'maxhp' ? fx.amount * this.maxHp : fx.basis === 'hit' ? fx.amount * (ctx.damage ?? 0) : fx.amount, 'proc', true);
        break;
      case 'shield':
        this.player.shield = Math.max(this.player.shield, fx.amount);
        this.player.shieldT = fx.duration;
        break;
      case 'zone':
        this.spawnZone({ owner: 'player', x, z, radius: fx.radius * this.stats.get('area'), life: fx.duration, dps: this.base({ damage: fx.dps, basis: fx.basis }, ctx), school: fx.school, tags: ['zone', fx.school], slow: fx.slow ?? 0, status: fx.status ?? null, art: fx.art });
        break;
      case 'buff':
        this.addBuff(fx.id, fx.stat as StatKey, fx.value, fx.kind, fx.duration, fx.maxStacks ?? 1);
        break;
      case 'cooldown':
        if (fx.scope === 'all') for (const w of this.weapons) w.timer = Math.max(0, w.timer - fx.seconds);
        else if (fx.scope === 'ability') this.player.abilityCd = Math.max(0, this.player.abilityCd - fx.seconds);
        else if (fx.scope === 'dash') this.player.dashRecharge += fx.seconds;
        break;
      case 'raise':
        this.summon(fx.kind === 'ghoul' ? 'ghoul_ally' : 'spirit_wolf', fx.duration, fx.max, x, z);
        break;
      case 'pull':
        this.forEachHostileInRadius(x, z, fx.radius, (e, d) => {
          if (e.boss) return;
          e.kbx += ((x - e.x) / (d || 1)) * fx.strength;
          e.kbz += ((z - e.z) / (d || 1)) * fx.strength;
        });
        break;
      case 'execute':
        if (ctx.target && ctx.target.alive && ctx.target.hp / ctx.target.maxHp < fx.threshold && !ctx.target.boss) {
          this.events.emit({ t: 'bark', x: ctx.target.x, z: ctx.target.z, text: 'Executed' });
          this.killEnemy(ctx.target, true, ctx.weapon ?? null, depth);
        }
        break;
      case 'nova':
        this.events.emit({ t: 'nova', x, z, radius: fx.radius, school: fx.school, duration: 0.3 });
        this.forEachHostileInRadius(x, z, fx.radius, (e, d) => this.hitEnemy(e, this.base(fx, ctx), fx.school, ['nova', 'area', fx.school], { depth, knockback: fx.knockback, dirX: (e.x - x) / (d || 1), dirZ: (e.z - z) / (d || 1) }));
        break;
      case 'strike': {
        const list = this.hostilesInRadius(x, z, fx.area);
        for (let i = 0; i < fx.count && list.length; i++) {
          const t = list[this.rng.int(0, list.length - 1)];
          this.scheduleStrike(t.x, t.z, fx.radius, this.base(fx, ctx), fx.school, ['storm', fx.school], 0.3 + i * 0.08, null, 'player', depth);
        }
        break;
      }
      case 'ember':
        this.gainEmber(fx.amount);
        break;
    }
  }

  addBuff(id: string, stat: StatKey, value: number, kind: 'inc' | 'more' | 'flat', duration: number, max: number) {
    const b = this.buffs.get(id);
    if (b) {
      b.t = duration;
      b.stacks = Math.min(max, b.stacks + 1);
    } else {
      this.buffs.set(id, { t: duration, stacks: 1, stat, value, kind, max });
    }
    const cur = this.buffs.get(id)!;
    this.stats.removeSource(`buff:${id}`);
    this.stats.add({ stat, kind, value: value * cur.stacks, source: `buff:${id}` });
  }

  private updateBuffs(dt: number) {
    for (const [id, b] of this.buffs) {
      b.t -= dt;
      if (b.t <= 0) {
        this.buffs.delete(id);
        this.stats.removeSource(`buff:${id}`);
      }
    }
  }

  /** Stop the fight cleanly (leaving an area). */
  end(reason: 'victory' | 'left') {
    this.over = reason;
  }

  /** For the HUD: seconds left on a weapon, 0..1. */
  weaponReady(w: WeaponInst) {
    return clamp(1 - w.timer / Math.max(0.01, cooldownOf(this, w)), 0, 1);
  }

  get retreat() { return this.retreatT; }
  schoolOfWeapon(w: WeaponInst) { return schoolOf(w); }
  tagsOfWeapon(w: WeaponInst) { return tagsOf(w); }
}

export interface ProcCtx {
  target?: Enemy;
  x?: number; z?: number;
  damage?: number;
  school?: School;
  tags?: readonly Tag[];
  crit?: boolean;
  weapon?: WeaponInst;
  applied?: StatusKind;
  depth?: number;
}

/** Ember needed for the next ember level. Quick early, steep late. */
export function emberNeed(level: number) {
  const n = level - 1;
  return Math.floor(12 + n * 9 + n * n * 1.6 + (level > 20 ? (level - 20) ** 2 * 6 : 0));
}
