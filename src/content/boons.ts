import type { StatMod } from '@/sim/stats';
import type { TriggerDef } from '@/sim/procs';
import type { Tag } from '@/sim/types';

/* What an ember level can buy besides weapons.
 *
 * BOONS are the passives - numbers, but numbers a build is shaped around
 * (and several of them are the catalysts that decide what a weapon evolves
 * into). SYNERGIES are rules: each adds a trigger to the machine. They are
 * rarer, they only appear once the build has something for them to act on
 * (a synergy about burning waits until something burns), and they are where
 * the "wait, these interact?" moments come from.
 *
 * Every entry says what it touches with `tags`, so the level-up draft can
 * lean toward what the build is already doing without ever forcing it. */

/** Blessings (boons and combos) are milestones, not ordinary picks: one is
 *  chosen at the start of every expedition, and another each time the
 *  ember reaches a multiple of this, on top of that level's skill. */
export const MILESTONE_EVERY = 85;
export const isMilestone = (level: number) => level > 0 && level % MILESTONE_EVERY === 0;

export type Rarity = 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';

export interface BoonDef {
  id: string;
  name: string;
  icon: string;
  rarity: Rarity;
  max: number;
  kind: 'boon' | 'synergy';
  /** Plain-language summary; {v} is replaced with the per-rank value. */
  text: string;
  detail?: string;
  mods?: (rank: number) => StatMod[];
  triggers?: TriggerDef[];
  /** Offered only when the build meets this. */
  requires?: BoonRequirement;
  tags: Tag[];
}

export type BoonRequirement =
  | { status: 'burn' | 'bleed' | 'chill' | 'poison' | 'shock' | 'mark' | 'sear' }
  | { tag: Tag }
  | { boon: string }
  | { any: BoonRequirement[] };

const inc = (stat: StatMod['stat'], v: number, source: string): StatMod => ({ stat, kind: 'inc', value: v, source });
const flat = (stat: StatMod['stat'], v: number, source: string): StatMod => ({ stat, kind: 'flat', value: v, source });
const more = (stat: StatMod['stat'], v: number, source: string): StatMod => ({ stat, kind: 'more', value: v, source });

export const BOONS: Record<string, BoonDef> = {
  /* ----------------------------------------------------------- boons -- */
  might: { id: 'might', name: 'Might', icon: 'fist', rarity: 'common', max: 5, kind: 'boon', tags: [],
    text: '+10% damage with everything.', mods: (r) => [inc('damage', 0.1 * r, 'boon:might')] },
  haste: { id: 'haste', name: 'Haste', icon: 'wing', rarity: 'common', max: 5, kind: 'boon', tags: [],
    text: 'Every weapon fires 8% more often.', mods: (r) => [more('cooldown', Math.pow(0.92, r) - 1, 'boon:haste')] },
  fleetfoot: { id: 'fleetfoot', name: 'Fleetfoot', icon: 'boot', rarity: 'common', max: 5, kind: 'boon', tags: [],
    text: '+10% movement speed.', mods: (r) => [inc('moveSpeed', 0.1 * r, 'boon:fleetfoot')] },
  greed: { id: 'greed', name: 'Greed\'s Pull', icon: 'magnet', rarity: 'common', max: 5, kind: 'boon', tags: [],
    text: 'Ember, gold and potions fly to you from 1.2 m farther.', mods: (r) => [flat('pickupRadius', 1.2 * r, 'boon:greed')] },
  vitality: { id: 'vitality', name: 'Vitality', icon: 'heart', rarity: 'common', max: 5, kind: 'boon', tags: ['heal'],
    text: '+25 maximum health, and a heal when taken.', mods: (r) => [flat('maxHealth', 25 * r, 'boon:vitality')] },
  ironhide: { id: 'ironhide', name: 'Ironhide', icon: 'shield', rarity: 'common', max: 5, kind: 'boon', tags: [],
    text: '+3 armour. Each point helps a little less than the last.', mods: (r) => [flat('armor', 3 * r, 'boon:ironhide')] },
  precision: { id: 'precision', name: 'Precision', icon: 'crosshair', rarity: 'uncommon', max: 5, kind: 'boon', tags: [],
    text: '+7% critical strike chance.', mods: (r) => [flat('critChance', 0.07 * r, 'boon:precision')] },
  ferocity: { id: 'ferocity', name: 'Ferocity', icon: 'claw', rarity: 'uncommon', max: 4, kind: 'boon', tags: [],
    text: '+25% critical strike damage.', mods: (r) => [flat('critDamage', 0.25 * r, 'boon:ferocity')] },
  expanse: { id: 'expanse', name: 'Expanse', icon: 'expand', rarity: 'uncommon', max: 5, kind: 'boon', tags: ['area'],
    text: '+12% area: novas, fields, orbits, storms and auras are bigger; chains, beams and blades reach farther.',
    mods: (r) => [inc('area', 0.12 * r, 'boon:expanse')] },
  duplicity: { id: 'duplicity', name: 'Duplicity', icon: 'triple', rarity: 'rare', max: 3, kind: 'boon', tags: ['projectile'],
    text: '+1 projectile on everything that sends things out.', mods: (r) => [flat('projectiles', r, 'boon:duplicity')] },
  fortune: { id: 'fortune', name: 'Fortune', icon: 'coin', rarity: 'uncommon', max: 4, kind: 'boon', tags: [],
    text: '+10% luck: more and better drops, and rarer cards.', mods: (r) => [flat('luck', 0.1 * r, 'boon:fortune')] },
  wisdom: { id: 'wisdom', name: 'Wisdom', icon: 'book', rarity: 'uncommon', max: 4, kind: 'boon', tags: [],
    text: '+10% ember from every stone.', mods: (r) => [inc('xpGain', 0.1 * r, 'boon:wisdom')] },
  recovery: { id: 'recovery', name: 'Recovery', icon: 'leaf', rarity: 'common', max: 4, kind: 'boon', tags: ['heal'],
    text: '+0.6 health regenerated per second.', mods: (r) => [flat('regen', 0.6 * r, 'boon:recovery')] },
  velocity: { id: 'velocity', name: 'Velocity', icon: 'spear', rarity: 'common', max: 3, kind: 'boon', tags: ['projectile'],
    text: '+15% projectile speed.', mods: (r) => [inc('projectileSpeed', 0.15 * r, 'boon:velocity')] },
  perennial: { id: 'perennial', name: 'Perennial', icon: 'perennial', rarity: 'common', max: 5, kind: 'boon', tags: ['zone', 'orbit', 'summon'],
    text: '+10% duration: fields, gyres, beasts and ground effects last longer.', mods: (r) => [inc('duration', 0.1 * r, 'boon:perennial')] },
  evasion: { id: 'evasion', name: 'Evasion', icon: 'feint', rarity: 'uncommon', max: 4, kind: 'boon', tags: [],
    text: '+7% chance to avoid a blow entirely.', mods: (r) => [flat('dodge', 0.07 * r, 'boon:evasion')] },
  thorns: { id: 'thorns', name: 'Thorns', icon: 'thorn', rarity: 'uncommon', max: 5, kind: 'boon', tags: [],
    text: 'Whatever strikes you takes 4 + 20% of the blow back.', mods: (r) => [flat('thorns', r, 'boon:thorns')] },
  serration: { id: 'serration', name: 'Serration', icon: 'bleed', rarity: 'uncommon', max: 4, kind: 'boon', tags: ['physical', 'dot'],
    text: 'Critical strikes open a wound that bleeds 30% of the blow over 3 s.',
    detail: 'Bleeding hurts more while the victim moves. A fresh crit reopens the wound at whichever bleed is worse.',
    mods: (r) => [flat('critChance', 0.02 * r, 'boon:serration')],
    triggers: [{ on: 'crit', effects: [{ do: 'status', target: 'hit', status: { kind: 'bleed', chance: 1, power: 0.3, duration: 3 } }], text: 'Crits bleed.' }] },
  chilling: { id: 'chilling', name: 'Chilling Presence', icon: 'frostaura', rarity: 'rare', max: 3, kind: 'boon', tags: ['frost', 'aura'],
    text: 'Creatures near you are slowed by the cold, more as they come closer.', mods: () => [] },
  searing: { id: 'searing', name: 'Searing Aura', icon: 'retaura', rarity: 'rare', max: 4, kind: 'boon', tags: ['holy', 'aura', 'area'],
    text: 'A holy aura sears everything near you twice a second.', mods: () => [] },
  spirit_companion: { id: 'spirit_companion', name: 'Spirit Companion', icon: 'spiritwolf', rarity: 'rare', max: 3, kind: 'boon', tags: ['summon'],
    text: 'Call a spirit wolf that hunts beside you. Each rank calls another.', mods: () => [] },
  grave_call: { id: 'grave_call', name: 'Grave Call', icon: 'risen', rarity: 'rare', max: 3, kind: 'boon', tags: ['summon', 'shadow'],
    text: 'Raise a ghoul to shamble after the horde. Slow, and it hits very hard.', mods: () => [] },
  dread_command: { id: 'dread_command', name: 'Dread Command', icon: 'command', rarity: 'epic', max: 5, kind: 'boon', tags: ['summon'],
    text: '+30% damage and +10% attack speed for everything you have summoned.', requires: { tag: 'summon' },
    mods: (r) => [inc('summonDamage', 0.3 * r, 'boon:dread_command'), inc('summonHaste', 0.1 * r, 'boon:dread_command')] },
  dark_bargain: { id: 'dark_bargain', name: 'Dark Bargain', icon: 'skull', rarity: 'epic', max: 3, kind: 'boon', tags: [],
    text: 'The dark grows: more of them, and faster. You grow too: +15% ember and gold.',
    detail: 'A curse you choose. More creatures means more ember, more gold, and more danger. Stacks.',
    mods: (r) => [inc('xpGain', 0.15 * r, 'boon:dark_bargain'), inc('goldGain', 0.15 * r, 'boon:dark_bargain')] },
  warding: { id: 'warding', name: 'Warding Light', icon: 'aegis', rarity: 'rare', max: 3, kind: 'boon', tags: ['holy'],
    text: 'Blocks one blow completely, then recharges (12 / 9 / 6 s).', mods: (r) => [flat('block', r, 'boon:warding')] },

  /* -------------------------------------------------------- synergies -- */
  kindling: { id: 'kindling', name: 'Kindling', icon: 'kindling', rarity: 'rare', max: 1, kind: 'synergy', tags: ['fire', 'dot'],
    text: 'Anything that dies burning hands its fire to two neighbours.', requires: { status: 'burn' },
    triggers: [{ on: 'kill', when: { targetStatus: 'burn' }, effects: [{ do: 'spread', kind: 'burn', radius: 3.2, count: 2, stacks: 2 }] }] },
  pyre_burst: { id: 'pyre_burst', name: 'Pyre Burst', icon: 'pyre', rarity: 'rare', max: 1, kind: 'synergy', tags: ['fire', 'explosion'],
    text: 'Burning creatures have a 30% chance to explode when they die.', requires: { status: 'burn' },
    triggers: [{ on: 'kill', chance: 0.3, when: { targetStatus: 'burn' },
      effects: [{ do: 'explode', radius: 2.4, damage: 0.35, basis: 'maxhp', school: 'fire', status: { kind: 'burn', chance: 0.7, power: 0.25, duration: 3 } }] }] },
  emberseekers: { id: 'emberseekers', name: 'Emberseekers', icon: 'embers', rarity: 'epic', max: 1, kind: 'synergy', tags: ['fire', 'projectile'],
    text: 'Every explosion throws out two embers that seek the strongest creature near you.', requires: { tag: 'explosion' },
    triggers: [{ on: 'explode', icd: 0.12, effects: [{ do: 'missiles', count: 2, damage: 18, basis: 'flat', school: 'fire', seek: 'strongest', speed: 9, art: 'ember_seeker' }] }] },
  shatter: { id: 'shatter', name: 'Shatter', icon: 'shatter', rarity: 'rare', max: 1, kind: 'synergy', tags: ['frost', 'explosion'],
    text: 'Frozen creatures shatter when they die, spraying frost that chills everything nearby.', requires: { status: 'chill' },
    triggers: [{ on: 'kill', when: { targetStatus: 'frozen' },
      effects: [{ do: 'explode', radius: 2.6, damage: 0.45, basis: 'maxhp', school: 'frost', status: { kind: 'chill', chance: 1, power: 2, duration: 2.5 } }] }] },
  deep_chill: { id: 'deep_chill', name: 'Deep Chill', icon: 'frostaura', rarity: 'uncommon', max: 1, kind: 'synergy', tags: ['frost'],
    text: 'Chill builds twice as fast. Frozen creatures take 35% more from everything.', requires: { status: 'chill' },
    mods: () => [inc('statusDamage', 0.15, 'syn:deep_chill')] },
  static_charge: { id: 'static_charge', name: 'Static Charge', icon: 'static', rarity: 'rare', max: 1, kind: 'synergy', tags: ['storm', 'chain'],
    text: 'Hitting a shocked creature sends a spark leaping to two more.', requires: { status: 'shock' },
    triggers: [{ on: 'hit', icd: 0.08, when: { targetStatus: 'shock' }, effects: [{ do: 'chain', count: 2, range: 5, damage: 0.5, basis: 'hit', school: 'storm' }] }] },
  butchers_mark: { id: 'butchers_mark', name: 'Butcher\'s Mercy', icon: 'execute', rarity: 'epic', max: 1, kind: 'synergy', tags: ['physical'],
    text: 'Critical strikes on bleeding creatures finish anything below 15% health.', requires: { status: 'bleed' },
    triggers: [{ on: 'crit', when: { targetStatus: 'bleed', hpBelow: 0.15 }, effects: [{ do: 'execute', threshold: 0.15 }] }] },
  blood_scent: { id: 'blood_scent', name: 'Blood Scent', icon: 'scent', rarity: 'uncommon', max: 1, kind: 'synergy', tags: ['physical'],
    text: 'Killing something that bleeds quickens you: +8% speed and attack rate for 3 s, stacking three times.', requires: { status: 'bleed' },
    triggers: [{ on: 'kill', when: { targetStatus: 'bleed' }, effects: [{ do: 'buff', id: 'blood_scent', stat: 'moveSpeed', value: 0.08, kind: 'inc', duration: 3, maxStacks: 3 },
      { do: 'buff', id: 'blood_scent_cd', stat: 'cooldown', value: -0.06, kind: 'more', duration: 3, maxStacks: 3 }] }] },
  hunters_mark: { id: 'hunters_mark', name: 'Hunter\'s Mark', icon: 'mark', rarity: 'rare', max: 1, kind: 'synergy', tags: ['ranged'],
    text: 'Every 5 s the toughest thing near you is marked: it takes 30% more from everything, and its death eases your cooldowns.',
    triggers: [{ on: 'tick', icd: 5, effects: [{ do: 'status', target: 'nearby', radius: 12, count: 1, status: { kind: 'mark', chance: 1, power: 1, duration: 5 } }] },
      { on: 'kill', when: { targetStatus: 'mark' }, effects: [{ do: 'cooldown', seconds: 0.6, scope: 'all' }] }] },
  plague_bearer: { id: 'plague_bearer', name: 'Plague Bearer', icon: 'plague', rarity: 'rare', max: 1, kind: 'synergy', tags: ['dot', 'shadow', 'nature'],
    text: 'Poisoned creatures pass their poison to three neighbours when they die.', requires: { status: 'poison' },
    triggers: [{ on: 'kill', when: { targetStatus: 'poison' }, effects: [{ do: 'spread', kind: 'poison', radius: 3, count: 3, stacks: 3 }] }] },
  sanctify: { id: 'sanctify', name: 'Sanctify', icon: 'sanctify', rarity: 'uncommon', max: 1, kind: 'synergy', tags: ['holy'],
    text: 'Holy damage is 40% stronger, and the seared burn with it.', requires: { status: 'sear' },
    mods: () => [inc('damage.holy', 0.4, 'syn:sanctify')] },
  consecration: { id: 'consecration', name: 'Consecration', icon: 'consecrate', rarity: 'rare', max: 1, kind: 'synergy', tags: ['holy', 'zone'],
    text: 'The seared leave hallowed ground where they fall.', requires: { status: 'sear' },
    triggers: [{ on: 'kill', chance: 0.35, when: { targetStatus: 'sear' },
      effects: [{ do: 'zone', radius: 1.8, duration: 3, dps: 8, basis: 'flat', school: 'holy', art: 'zone_holy' }] }] },
  soul_harvest: { id: 'soul_harvest', name: 'Soul Harvest', icon: 'risen', rarity: 'epic', max: 1, kind: 'synergy', tags: ['summon', 'shadow'],
    text: 'Kills have a 6% chance to rise again on your side for 14 s (up to six at once).',
    triggers: [{ on: 'kill', chance: 0.06, effects: [{ do: 'raise', kind: 'ghoul', duration: 14, max: 6 }] }] },
  pack_leader: { id: 'pack_leader', name: 'Pack Leader', icon: 'howl', rarity: 'rare', max: 1, kind: 'synergy', tags: ['summon', 'nature'],
    text: 'Your dash howls: every ally near you strikes 40% harder for 4 s, and a spirit wolf answers.', requires: { tag: 'summon' },
    triggers: [{ on: 'dash', icd: 3, effects: [{ do: 'buff', id: 'pack', stat: 'summonDamage', value: 0.4, kind: 'inc', duration: 4 }, { do: 'raise', kind: 'spirit_wolf', duration: 8, max: 3 }] }] },
  momentum: { id: 'momentum', name: 'Momentum', icon: 'boot', rarity: 'legendary', max: 1, kind: 'synergy', tags: [],
    text: 'While you are moving your weapons fire 25% faster. Never stand still.',
    mods: () => [{ stat: 'cooldown', kind: 'more', value: -0.2, source: 'syn:momentum', when: 'moving' }] },
  bloodthirst: { id: 'bloodthirst', name: 'Bloodthirst', icon: 'drain', rarity: 'legendary', max: 1, kind: 'synergy', tags: ['heal'],
    text: 'Every 25 kills restore 6% of your health. The horde is your medicine.',
    triggers: [{ on: 'kill', icd: 0, effects: [{ do: 'heal', amount: 0.0024, basis: 'maxhp' }] }] },
  arcane_overflow: { id: 'arcane_overflow', name: 'Arcane Overflow', icon: 'arcane', rarity: 'legendary', max: 1, kind: 'synergy', tags: ['spell'],
    text: 'Each ember stone has an 8% chance to fire every weapon at once.',
    triggers: [{ on: 'ember', chance: 0.08, icd: 0.4, effects: [{ do: 'cooldown', seconds: 99, scope: 'all' }] }] },
  glass_cannon: { id: 'glass_cannon', name: 'Glass Cannon', icon: 'flame', rarity: 'legendary', max: 1, kind: 'synergy', tags: [],
    text: '45% more damage, and 35% less health. Live fast.',
    mods: () => [more('damage', 0.45, 'syn:glass'), more('maxHealth', -0.35, 'syn:glass')] },
  storm_caller: { id: 'storm_caller', name: 'Storm Caller', icon: 'bolt', rarity: 'epic', max: 1, kind: 'synergy', tags: ['storm'],
    text: 'Every 12th kill calls lightning down on the thickest knot of creatures near you.', requires: { tag: 'storm' },
    triggers: [{ on: 'kill', chance: 1 / 12, effects: [{ do: 'strike', count: 3, radius: 1.6, damage: 40, basis: 'flat', school: 'storm', area: 6 }] }] },
  fracture: { id: 'fracture', name: 'Fracture', icon: 'shatter', rarity: 'epic', max: 1, kind: 'synergy', tags: ['frost', 'fire'],
    text: 'Fire on the frozen is a violent thing: burning a frozen creature makes it explode.', requires: { any: [{ status: 'chill' }] },
    triggers: [{ on: 'hit', when: { school: 'fire', targetStatus: 'frozen' }, icd: 0.05,
      effects: [{ do: 'explode', radius: 2.6, damage: 1.2, basis: 'hit', school: 'frost' }] }] },
};

export const BOON_ORDER = Object.keys(BOONS);
