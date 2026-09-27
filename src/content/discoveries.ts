import type { WeaponInst } from '@/sim/weapons';
import type { Battle } from '@/sim/battle';

/* Discoveries: weapon pairs that quietly do more together. Nobody tells you
 * these exist. Carry both and the codex remembers the pairing forever, with
 * a cryptic line for the ones not yet found. From The Ember Watch, with a
 * few that only make sense in a world that has fire, frost and flesh. */

export interface Discovery {
  id: string;
  name: string;
  weapons: [string, string];
  description: string;
  hint: string;
  apply: (a: WeaponInst, b: WeaponInst, battle: Battle) => void;
}

export const SYNERGY_PAIRS: Discovery[] = [
  {
    id: 'frostfire', name: 'Frostfire Bolt', weapons: ['rimeshard', 'cinderfall'],
    description: 'Cinders chill what survives them, both bolts hit 10% harder, and fire on the frozen is violent.',
    hint: 'When frost meets flame, something ancient stirs...',
    apply: (a, b, battle) => {
      a.mods.damage *= 1.1; b.mods.damage *= 1.1;
      battle.addTrigger({ on: 'hit', icd: 0.1, when: { school: 'fire', targetStatus: 'frozen' },
        effects: [{ do: 'explode', radius: 2.2, damage: 0.8, basis: 'hit', school: 'frost' }] }, 'disc:frostfire');
    },
  },
  {
    id: 'shadowflame', name: 'Shadowflame', weapons: ['umbral_bolt', 'cinderfall'],
    description: 'Umbral bolts detonate on impact, scorching everything nearby.',
    hint: 'Shadow and flame were ever entwined.',
    apply: (a, _b, battle) => {
      battle.addTrigger({ on: 'hit', when: { weapon: a.id }, icd: 0.05, effects: [{ do: 'explode', radius: 1.4, damage: 0.5, basis: 'hit', school: 'fire' }] }, 'disc:shadowflame');
    },
  },
  {
    id: 'deadly_brew', name: 'Deadly Brew', weapons: ['knifestorm', 'rimeshard'],
    description: 'Every thrown knife is coated in a numbing venom that chills its victim.',
    hint: 'A rogue with access to the alchemist\'s icebox is a dangerous thing.',
    apply: (a, _b, battle) => {
      battle.addTrigger({ on: 'hit', when: { weapon: a.id }, effects: [{ do: 'status', target: 'hit', status: { kind: 'chill', chance: 1, power: 1, duration: 2 } }] }, 'disc:deadly_brew');
    },
  },
  {
    id: 'tempest_pact', name: 'Tempest Pact', weapons: ['axe_gyre', 'arcweb'],
    description: 'Axe Gyre blades sometimes call the storm, loosing lightning on those they strike.',
    hint: 'Blessed blades may yet call the storm...',
    apply: (a, _b, battle) => {
      battle.addTrigger({ on: 'hit', chance: 0.15, when: { weapon: a.id }, effects: [{ do: 'chain', count: 3, range: 5, damage: 0.8, basis: 'hit', school: 'storm' }] }, 'disc:tempest_pact');
    },
  },
  {
    id: 'radiant_gyre', name: 'Radiant Gyre', weapons: ['axe_gyre', 'dawnpulse'],
    description: 'Every spin of the Axe Gyre begins with a pulse of holy Light.',
    hint: 'Steel spun in faith becomes something more.',
    apply: (a, _b, battle) => { a.mods.damage *= 1.1; battle.addTrigger({ on: 'hit', icd: 3.5, when: { weapon: a.id }, effects: [{ do: 'nova', radius: 3, damage: 14, basis: 'flat', school: 'holy', knockback: 0.4 }] }, 'disc:radiant_gyre'); },
  },
  {
    id: 'truestrike', name: 'Truestrike', weapons: ['volley', 'seeking_motes'],
    description: 'Enchanted arrows curve in flight to seek their prey.',
    hint: 'The finest rangers fletch their arrows with a whisper of magic.',
    apply: (a) => { a.mods.damage *= 1.08; a.mods.homing += 3; },
  },
  {
    id: 'celestial', name: 'Celestial Alignment', weapons: ['moonbrand', 'dawnpulse'],
    description: 'Sun and moon align: an extra moonbeam, and wider rings of Light.',
    hint: 'What happens when the moon rises on the light of dawn?',
    apply: (a, b) => { a.mods.projectiles += 1; b.mods.area *= 1.12; },
  },
  {
    id: 'verdict', name: 'Verdict', weapons: ['judgement_disc', 'hallowed_ring'],
    description: 'The shield judges from hallowed ground: +1 ricochet and 10% more damage.',
    hint: 'A shield thrown from sacred ground carries a verdict.',
    apply: (a) => { a.mods.damage *= 1.1; a.mods.pierce += 1; },
  },
  {
    id: 'thunderpalm', name: 'Thunderpalm', weapons: ['iron_palms', 'arcweb'],
    description: 'Iron Palms carry the storm: some strikes loose lightning from what they hit.',
    hint: 'An open hand can hold lightning, if it is quick enough.',
    apply: (a, _b, battle) => { battle.addTrigger({ on: 'hit', chance: 0.18, when: { weapon: a.id }, effects: [{ do: 'chain', count: 3, range: 5, damage: 0.7, basis: 'hit', school: 'storm' }] }, 'disc:thunderpalm'); },
  },
  {
    id: 'hailwheel', name: 'Hailwheel', weapons: ['gale_chakram', 'rimeshard'],
    description: 'The chakram rimes whatever it cuts, and both hit 8% harder.',
    hint: 'A spinning edge through a hailstorm comes back cold.',
    apply: (a, b, battle) => {
      a.mods.damage *= 1.08; b.mods.damage *= 1.08;
      battle.addTrigger({ on: 'hit', when: { weapon: a.id }, effects: [{ do: 'status', target: 'hit', status: { kind: 'chill', chance: 1, power: 1, duration: 2 } }] }, 'disc:hailwheel');
    },
  },
  {
    id: 'razor_wind', name: 'Razor Wind', weapons: ['gale_chakram', 'knifestorm'],
    description: 'One more ring in every throw, cutting 10% deeper.',
    hint: 'Every blade that flies wants a blade beside it.',
    apply: (a) => { a.mods.projectiles += 1; a.mods.damage *= 1.1; },
  },
  {
    id: 'rotbloom', name: 'Rotbloom', weapons: ['thornbloom', 'blightfield'],
    description: 'Rot feeds the thicket: both fields hit 12% harder.',
    hint: 'Nothing grows as well as it does on something dead.',
    apply: (a, b) => { a.mods.damage *= 1.12; b.mods.damage *= 1.12; },
  },
  {
    id: 'oath_and_arc', name: 'Oath of the Storm', weapons: ['oathblade', 'arcweb'],
    description: 'The blade carries the storm: a swing that finds a shocked creature calls lightning onto it.',
    hint: 'A sworn blade will carry whatever you ask it to.',
    apply: (a, _b, battle) => { battle.addTrigger({ on: 'hit', when: { weapon: a.id, targetStatus: 'shock' }, icd: 0.2, effects: [{ do: 'strike', count: 1, radius: 1.4, damage: 1.2, basis: 'hit', school: 'storm', area: 2 }] }, 'disc:oath_arc'); },
  },
  {
    id: 'butchery', name: 'Butchery', weapons: ['cleaver', 'knifestorm'],
    description: 'Wounds opened by knives are torn wider by the cleaver: 40% more against the bleeding.',
    hint: 'Two blades, one purpose.',
    apply: (a, _b, battle) => { battle.addTrigger({ on: 'hit', when: { weapon: a.id, targetStatus: 'bleed' }, effects: [{ do: 'explode', radius: 0.1, damage: 0.4, basis: 'hit', school: 'physical' }] }, 'disc:butchery'); },
  },
];
