import type { Family, FactionId, Resists, School, Tag } from '@/sim/types';

/* The things that come out of the dark.
 *
 * Every creature is data: stats at level 1, a behaviour, and optional verbs
 * (a lunge, a ranged attack, ground left behind, a death burst, a split).
 * Behaviours are what stop two hundred creatures from being one creature two
 * hundred times - each asks the survivor a different question:
 *
 *   chase     the baseline: come at you along the flow field
 *   pack      wolves: fan out to surround, then close together
 *   charger   boars: plant, paw the ground, run a straight line; a charge
 *             that ends in a tree stuns the boar
 *   ranged    keep a distance and shoot; step toward them
 *   orbit     hold a ring and walk it, so circling away stops working
 *   tunneler  lamplings: go under, come up beside you
 *   caster    stand behind the others and raise the dead / hurl frost
 *   guard     a shield toward you: projectiles from the front mostly glance
 *             off - go around, or use something that is not a projectile
 *   stationary  totems, turrets, lanterns
 *
 * Levels scale health and damage (see scaleFor); the zone and the night's
 * threat decide the level. */

export type Behavior = 'chase' | 'pack' | 'charger' | 'ranged' | 'orbit' | 'tunneler' | 'caster' | 'guard' | 'stationary' | 'boss' | 'flee';

export interface RangedSpec {
  range: number; cooldown: number; speed: number; school: School;
  count?: number; spread?: number; damagePct?: number; lob?: boolean;
  /** A lobbed pot leaves burning ground where it lands. */
  zone?: { radius: number; duration: number; dpsPct: number };
  slow?: { factor: number; duration: number };
  art?: string;
}

export interface EnemyDef {
  id: string;
  name: string;
  family: Family;
  faction: FactionId;
  /** Renderer key: which model or procedural creature, and its colouring. */
  visual: string;
  scale?: number;
  health: number;
  speed: number;
  damage: number;
  radius: number;
  mass?: number;
  xp: number;
  gold?: number;
  resists?: Resists;
  behavior: Behavior;
  ranged?: RangedSpec;
  lunge?: { range: number; cooldown: number; windup: number; time: number; speed: number };
  charge?: { range: number; cooldown: number; windup: number; speed: number; time: number };
  trail?: { interval: number; radius: number; life: number; dpsPct: number; school: School };
  burst?: { radius: number; damagePct: number; fuse: number; school: School; status?: 'poison' | 'burn' | 'chill' };
  split?: { into: string; count: number };
  /** Raises fallen dead nearby as fresh risen. */
  raise?: { every: number; count: number; into: string; range: number };
  guard?: { arc: number; reduction: number };
  /** Contact attack rhythm. */
  attackEvery?: number;
  elite?: boolean;
  boss?: boolean;
  aggroRange?: number;
  /** Tags it carries for items and procs ('undead' reacts to holy, etc.). */
  tags?: Tag[];
  loot?: string;
  /** What the bestiary says once it has been put down. */
  note: string;
}

const undeadResist: Resists = { frost: 0.25, shadow: 0.35, holy: -0.5, fire: -0.15 };
const beastResist: Resists = { fire: -0.25, nature: 0.2 };
const kerchiefResist: Resists = {};

export const ENEMIES: Record<string, EnemyDef> = {
  /* ------------------------------------------------------------ the dead -- */
  risen: {
    id: 'risen', name: 'Risen', family: 'undead', faction: 'dead', visual: 'skeleton_minion',
    health: 20, speed: 2.7, damage: 8, radius: 0.45, xp: 2, resists: undeadResist, behavior: 'chase',
    note: 'The dead of the Low Ford, still marching. They do not hurry. They do not have to.',
  },
  risen_warrior: {
    id: 'risen_warrior', name: 'Risen Shieldman', family: 'undead', faction: 'dead', visual: 'skeleton_warrior',
    health: 46, speed: 2.4, damage: 11, radius: 0.5, mass: 1.6, xp: 4, resists: undeadResist, behavior: 'guard',
    guard: { arc: 1.4, reduction: 0.75 },
    note: 'Buried with his shield, and he has not let go of it. Arrows and bolts glance off the face of it; take him from the side.',
  },
  risen_archer: {
    id: 'risen_archer', name: 'Risen Bowman', family: 'undead', faction: 'dead', visual: 'skeleton_rogue',
    health: 22, speed: 2.5, damage: 7, radius: 0.45, xp: 4, resists: undeadResist, behavior: 'ranged',
    ranged: { range: 9, cooldown: 2.8, speed: 11, school: 'physical', art: 'bolt_bone' },
    note: 'Still keeps the ford the way it was taught: from behind the others, at a distance. Close it.',
  },
  grave_caller: {
    id: 'grave_caller', name: 'Grave-Caller', family: 'undead', faction: 'dead', visual: 'skeleton_mage',
    health: 34, speed: 2.2, damage: 9, radius: 0.45, xp: 7, resists: undeadResist, behavior: 'caster',
    ranged: { range: 10, cooldown: 3.4, speed: 7, school: 'frost', slow: { factor: 0.6, duration: 1.4 }, art: 'frost_orb' },
    raise: { every: 7, count: 2, into: 'risen', range: 7 },
    note: 'Wherever one of these walks, the fallen get up again. Kill it first, or you will be killing the same dead twice.',
  },
  barrow_knight: {
    id: 'barrow_knight', name: 'Barrow Knight', family: 'undead', faction: 'dead', visual: 'skeleton_warrior_elite', scale: 1.45,
    health: 420, speed: 2.6, damage: 22, radius: 0.8, mass: 5, xp: 40, gold: 12, resists: undeadResist, behavior: 'chase',
    lunge: { range: 8, cooldown: 5.5, windup: 0.75, time: 0.5, speed: 17 },
    elite: true, loot: 'elite', attackEvery: 1.1,
    note: 'A knight once, still standing a knight\'s watch over the wrong side. Plants, picks you, and comes down the line. Be off the line.',
  },

  /* ------------------------------------------------------------ lamplings -- */
  lampling: {
    id: 'lampling', name: 'Lampling Tunneler', family: 'lampling', faction: 'lampling', visual: 'lampling',
    health: 16, speed: 3.6, damage: 7, radius: 0.38, xp: 2, behavior: 'tunneler', resists: { fire: 0.3, frost: -0.3 },
    note: 'They dig toward light the way moths fly at it. A lampling will chew through a cellar wall to sit beside your candle, and then through you to keep it.',
  },
  lampling_sapper: {
    id: 'lampling_sapper', name: 'Lampling Sapper', family: 'lampling', faction: 'lampling', visual: 'lampling_sapper',
    health: 24, speed: 2.9, damage: 8, radius: 0.4, xp: 4, behavior: 'ranged', resists: { fire: 0.5, frost: -0.3 },
    ranged: { range: 8, cooldown: 3.6, speed: 8, school: 'fire', lob: true, zone: { radius: 1.6, duration: 3, dpsPct: 0.5 }, art: 'firepot' },
    burst: { radius: 2.2, damagePct: 1.2, fuse: 0.6, school: 'fire', status: 'burn' },
    note: 'Carries a satchel of the foreman\'s blasting ember and throws it at whatever looks brightest. Dies loudly. Stand clear.',
  },

  /* --------------------------------------------------------------- beasts -- */
  wolf: {
    id: 'wolf', name: 'Longtooth Wolf', family: 'wolf', faction: 'pack', visual: 'wolf',
    health: 30, speed: 5.0, damage: 9, radius: 0.5, xp: 4, resists: beastResist, behavior: 'pack', attackEvery: 0.9,
    tags: ['nature'], loot: 'wolf',
    note: 'Never alone. If you have counted one, count again. They come at you from every side at once, and they know which side you are not watching.',
  },
  wolf_blighted: {
    id: 'wolf_blighted', name: 'Blight-Sick Wolf', family: 'wolf', faction: 'pack', visual: 'wolf_blighted',
    health: 38, speed: 4.4, damage: 10, radius: 0.5, xp: 5, resists: { ...beastResist, shadow: 0.3 }, behavior: 'chase',
    burst: { radius: 2.4, damagePct: 0.6, fuse: 0.5, school: 'nature', status: 'poison' },
    loot: 'wolf',
    note: 'Its eyes are wrong and its breath is green. Something in the water. It is not hunting you; it is running from what hurts, and you are in the way.',
  },
  wolf_alpha: {
    id: 'wolf_alpha', name: 'Greymuzzle', family: 'wolf', faction: 'pack', visual: 'wolf_alpha', scale: 1.5,
    health: 520, speed: 5.4, damage: 18, radius: 0.85, mass: 5, xp: 55, resists: beastResist, behavior: 'pack',
    lunge: { range: 9, cooldown: 4.8, windup: 0.6, time: 0.45, speed: 19 },
    elite: true, loot: 'alpha', attackEvery: 0.8,
    note: 'The pack\'s oldest. Grey to the eyes and in no hurry. The others follow him because he has never once been wrong about where to go.',
  },
  boar: {
    id: 'boar', name: 'Thicket Tusker', family: 'boar', faction: 'wild', visual: 'boar',
    health: 44, speed: 3.2, damage: 12, radius: 0.6, mass: 2.5, xp: 5, resists: beastResist, behavior: 'charger',
    charge: { range: 10, cooldown: 4.5, windup: 0.9, speed: 13, time: 1.0 },
    loot: 'boar',
    note: 'Charges whatever moved last. It paws the ground first, which is your warning. A tusker that runs into a tree does not get up quickly.',
  },

  /* ------------------------------------------------------------ Kerchiefs -- */
  footpad: {
    id: 'footpad', name: 'Kerchief Footpad', family: 'kerchief', faction: 'kerchief', visual: 'kerchief_rogue',
    health: 36, speed: 4.2, damage: 10, radius: 0.48, xp: 5, gold: 2, resists: kerchiefResist, behavior: 'chase',
    loot: 'kerchief',
    note: 'Red cloth over the face and quick hands under it. They rob the dead first and the living second, which is at least an order.',
  },
  pillager: {
    id: 'pillager', name: 'Kerchief Pillager', family: 'kerchief', faction: 'kerchief', visual: 'kerchief_hooded',
    health: 30, speed: 3.4, damage: 9, radius: 0.48, xp: 6, gold: 3, behavior: 'ranged',
    ranged: { range: 9, cooldown: 3.2, speed: 8.5, school: 'fire', lob: true, zone: { radius: 1.7, duration: 3.5, dpsPct: 0.45 }, art: 'firepot' },
    loot: 'kerchief',
    note: 'The ones who throw. Firepots, bottles, once a boot: whatever the last wagon had in it.',
  },
  bruiser: {
    id: 'bruiser', name: 'Kerchief Bruiser', family: 'kerchief', faction: 'kerchief', visual: 'kerchief_brute', scale: 1.15,
    health: 90, speed: 3.0, damage: 15, radius: 0.62, mass: 3, xp: 9, gold: 5, behavior: 'guard',
    guard: { arc: 1.6, reduction: 0.8 },
    loot: 'kerchief',
    note: 'What the Kerchiefs send when the footpads come back empty-handed. Carries a barn door for a shield. Arrows do not bother him from the front.',
  },
  enforcer: {
    id: 'enforcer', name: 'Kerchief Enforcer', family: 'kerchief', faction: 'kerchief', visual: 'kerchief_enforcer', scale: 1.35,
    health: 480, speed: 3.4, damage: 22, radius: 0.8, mass: 5, xp: 45, gold: 20, behavior: 'chase',
    lunge: { range: 8.5, cooldown: 5.0, windup: 0.7, time: 0.45, speed: 18 },
    elite: true, loot: 'elite', attackEvery: 1.0,
    note: 'Plants its feet, picks you, and comes straight down the line. Step off the line.',
  },

  /* ---------------------------------------------------- your own, raised -- */
  spirit_wolf: {
    id: 'spirit_wolf', name: 'Spirit Wolf', family: 'wolf', faction: 'ally', visual: 'wolf_spirit',
    health: 60, speed: 6.2, damage: 14, radius: 0.45, xp: 0, behavior: 'pack', attackEvery: 0.7,
    note: 'A wolf made of the ember you carry. It hunts beside you, and it does not stay.',
  },
  ghoul_ally: {
    id: 'ghoul_ally', name: 'Risen Servant', family: 'undead', faction: 'ally', visual: 'risen_ally',
    health: 90, speed: 3.0, damage: 24, radius: 0.5, xp: 0, behavior: 'chase', attackEvery: 1.3,
    note: 'Something you killed, got up again on your side. It will not thank you.',
  },
};

/** Health and damage multipliers at a creature level. Gentle enough that a
 *  zone revisited a few levels later is easier, steep enough that the night
 *  deepening is felt. */
export function scaleFor(level: number) {
  const l = Math.max(1, level) - 1;
  return {
    health: 1 + l * 0.38 + l * l * 0.035,
    damage: 1 + l * 0.14,
    xp: 1 + l * 0.12,
  };
}
