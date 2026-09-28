import type { EnemyDef } from '@/content/enemies';
import type { School, FactionId, StatusKind, Tag } from './types';
import type { StatusPayload } from '@/content/weapons';

/* The things a fight is made of. Plain objects, pooled by the battle so
 * nothing is allocated in the middle of a horde. */

export type EnemyState =
  | 'rising' | 'active' | 'windup' | 'lunging' | 'recover' | 'burrowed' | 'surfacing'
  | 'casting' | 'dying' | 'dead' | 'stunned' | 'fleeing' | 'idle';

export interface StatusSlot { t: number; stacks: number; power: number; tick: number }

export interface Enemy {
  id: number;
  alive: boolean;
  def: EnemyDef;
  level: number;
  x: number; z: number;
  vx: number; vz: number;
  kbx: number; kbz: number;
  facing: number;
  radius: number;
  mass: number;
  hp: number;
  maxHp: number;
  damage: number;
  speed: number;
  faction: FactionId;
  /** 'hostile' attacks the player; 'neutral' ignores until provoked;
   *  'ally' fights for the player. */
  disposition: 'hostile' | 'neutral' | 'ally';
  elite: boolean;
  boss: boolean;
  state: EnemyState;
  stateT: number;
  attackT: number;
  rangedT: number;
  raiseT: number;
  target: number; // -1 = player, otherwise enemy id, -2 = none
  retargetT: number;
  slot: number; // pack slot angle, orbit phase
  seed: number;
  lungeX: number; lungeZ: number;
  status: Partial<Record<StatusKind, StatusSlot>>;
  flash: number;
  /** Visual clock for the renderer, and what it should be playing. */
  anim: 'move' | 'idle' | 'attack' | 'hit' | 'die' | 'rise' | 'windup' | 'cast' | 'burrow';
  animT: number;
  lastSchool: School;
  lastWeapon: string | null;
  /** The last blow: how hard, whether it crit, which way it was going
   *  (what the gore makes of a death). */
  lastBlow: number;
  lastCrit: boolean;
  lastDx: number;
  lastDz: number;
  /** Its death burst it apart: nothing left to lie there. */
  burst: boolean;
  dieT: number;
  /** A named creature: promoted when it killed the survivor, carrying what
   *  it took. */
  named?: { title: string; carries: string[]; sourceHero: string };
  /** Summons and raised dead expire. */
  lifeT: number;
  /** Tag for quest logic ("the alpha", "caravan guard"). */
  tag?: string;
  /** Deaths caused by player's damage (for credit). */
  credit: boolean;
  /** Hurt by the player recently: neutral creatures turn hostile. */
  provoked: boolean;
  /** Where this creature belongs; it drifts home when it has nothing to do. */
  homeX: number; homeZ: number; leash: number;
  /** Multiplier on damage taken (a ward, a vulnerable moment). */
  takenMul: number;
}

export interface Projectile {
  id: number;
  alive: boolean;
  owner: 'player' | 'enemy' | 'ally';
  ownerId: number;
  x: number; z: number; y: number;
  vx: number; vz: number; vy: number;
  speed: number;
  damage: number;
  school: School;
  tags: readonly Tag[];
  radius: number;
  pierce: number;
  bounces: number;
  life: number;
  age: number;
  homing: number;
  seek: 'nearest' | 'elite' | 'strongest' | 'random' | 'marked' | null;
  target: number;
  weapon: string | null;
  art: string;
  status: StatusPayload | null;
  splash: number;
  splitOnHit: number;
  heal: number;
  knockback: number;
  /** Out-and-back: flips to returning at half life. */
  chakram: boolean;
  returning: boolean;
  /** Lobbed pots: ignore collisions until they land. */
  lob: boolean;
  landX: number; landZ: number;
  groundOnHit: { radius: number; duration: number; dpsPct: number } | null;
  hits: number[];
  /** When each entry of `hits` was struck, for weapons that can hit the same
   *  creature again after `rehit` seconds (orbits, herds). */
  hitTimes: number[];
  rehit: number;
  hitCount: number;
  orbitR: number;
  orbitW: number;
  orbitA: number;
  /** Weapon instance that owns an orbiting blade (for cleanup). */
  slotId: number;
  rank: number;
  depth: number;
  bossDamage: number;
  /** Frontal guards can deflect projectiles; the angle it came from. */
  dirX: number; dirZ: number;
}

export interface GroundZone {
  id: number;
  alive: boolean;
  owner: 'player' | 'enemy' | 'ally' | 'world';
  x: number; z: number;
  radius: number;
  life: number;
  age: number;
  tick: number;
  tickT: number;
  dps: number;
  school: School;
  tags: readonly Tag[];
  slow: number;
  status: StatusPayload | null;
  art: string;
  weapon: string | null;
  follow: boolean;
  /** Blocks for the player standing in it (Sanctified Earth). */
  armor: number;
  bossDamage: number;
}

export type PickupKind = 'ember' | 'gold' | 'heal' | 'magnet' | 'item' | 'material' | 'chest' | 'quest' | 'relic';

export interface Pickup {
  id: number;
  alive: boolean;
  kind: PickupKind;
  x: number; z: number;
  vx: number; vz: number;
  value: number;
  /** For items and materials: which. */
  ref: string | null;
  age: number;
  pulled: boolean;
  /** Stays on the ground forever (a corpse's gear, a quest item). */
  persistent: boolean;
  tier: number;
}

export function blankEnemy(id: number): Enemy {
  return {
    id, alive: false, def: null as unknown as EnemyDef, level: 1, x: 0, z: 0, vx: 0, vz: 0, kbx: 0, kbz: 0, facing: 0,
    radius: 0.5, mass: 1, hp: 1, maxHp: 1, damage: 1, speed: 1, faction: 'dead', disposition: 'hostile',
    elite: false, boss: false, state: 'active', stateT: 0, attackT: 0, rangedT: 0, raiseT: 0, target: -1, retargetT: 0,
    slot: 0, seed: 0, lungeX: 0, lungeZ: 0, status: {}, flash: 0, anim: 'move', animT: 0, lastSchool: 'physical',
    lastWeapon: null, lastBlow: 0, lastCrit: false, lastDx: 0, lastDz: 0, burst: false, dieT: 0, lifeT: 0, credit: false, provoked: false, homeX: 0, homeZ: 0, leash: 0, takenMul: 1,
  };
}

export function blankProjectile(id: number): Projectile {
  return {
    id, alive: false, owner: 'player', ownerId: -1, x: 0, z: 0, y: 1, vx: 0, vz: 0, vy: 0, speed: 0, damage: 0,
    school: 'physical', tags: [], radius: 0.2, pierce: 0, bounces: 0, life: 1, age: 0, homing: 0, seek: null, target: -2,
    weapon: null, art: 'bolt', status: null, splash: 0, splitOnHit: 0, heal: 0, knockback: 0, chakram: false,
    returning: false, lob: false, landX: 0, landZ: 0, groundOnHit: null, hits: [], hitTimes: [], rehit: 0, hitCount: 0,
    orbitR: 0, orbitW: 0, orbitA: 0, slotId: -1, rank: 1, depth: 0,
    bossDamage: 1, dirX: 0, dirZ: 1,
  };
}

export function blankZone(id: number): GroundZone {
  return {
    id, alive: false, owner: 'player', x: 0, z: 0, radius: 1, life: 1, age: 0, tick: 0.5, tickT: 0, dps: 0,
    school: 'physical', tags: [], slow: 0, status: null, art: 'zone', weapon: null, follow: false, armor: 0, bossDamage: 1,
  };
}

export function blankPickup(id: number): Pickup {
  return { id, alive: false, kind: 'ember', x: 0, z: 0, vx: 0, vz: 0, value: 1, ref: null, age: 0, pulled: false, persistent: false, tier: 0 };
}

/** A fixed-capacity pool; ids are indices and stay stable while alive. */
export class Pool<T extends { id: number; alive: boolean }> {
  readonly items: T[] = [];
  private free: number[] = [];
  count = 0;

  constructor(make: (id: number) => T, readonly capacity: number) {
    for (let i = capacity - 1; i >= 0; i--) {
      this.items[i] = make(i);
      this.free.push(i);
    }
  }

  spawn(): T | null {
    const id = this.free.pop();
    if (id === undefined) return null;
    const it = this.items[id];
    it.alive = true;
    this.count++;
    return it;
  }

  release(it: T) {
    if (!it.alive) return;
    it.alive = false;
    this.free.push(it.id);
    this.count--;
  }

  *alive(): Generator<T> {
    for (const it of this.items) if (it.alive) yield it;
  }

  forEach(fn: (it: T) => void) {
    const items = this.items;
    for (let i = 0; i < items.length; i++) if (items[i].alive) fn(items[i]);
  }

  clear() {
    for (const it of this.items) if (it.alive) this.release(it);
  }
}
