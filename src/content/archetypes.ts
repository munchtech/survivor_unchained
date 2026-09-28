import type { StatMod } from '@/sim/stats';
import type { AbilityKind } from './abilities';
import type { CharacterModel } from '@/render/assets';
import type { TriggerDef } from '@/sim/procs';

/* Who the survivor is, before anything happens to them.
 *
 * An archetype is how they fight: a body (model), a base, the weapons they
 * can start with and the two abilities they can choose between. A
 * background is where they came from, and it is deliberately NOT a stat
 * bonus: it is knowledge (what you can notice and understand), a starting
 * possession, and how the world first reads you. Traits are what a
 * character becomes over time - some chosen at level-ups, some given by the
 * world for what you did in it. */

export type ArchetypeId = 'warden' | 'reaver' | 'arcanist' | 'stalker';
export type BackgroundId = 'hunter' | 'scholar' | 'outcast' | 'devout';

export interface Archetype {
  id: ArchetypeId;
  name: string;
  tagline: string;
  description: string;
  model: CharacterModel;
  altModel?: CharacterModel;
  base: { maxHealth: number; moveSpeed: number; armor: number; regen: number; pickupRadius: number; critChance: number };
  /** Items that grant each starting weapon choice. */
  weapons: string[];
  abilities: AbilityKind[];
  /** The kinds of skill the calling leans toward (tags): the level-up draft
   *  offers them a little more often. Anyone can take any skill. */
  favours: string[];
  /** Their colours: which of the model's cloth swatches become what (see
   *  render/recolor.ts). The first is the model as it came. `ui` is the
   *  chip shown on the creation screen. */
  palettes: Array<{ id: string; name: string; ui: string; paint: Record<string, string> }>;
}

export const ARCHETYPES: Record<ArchetypeId, Archetype> = {
  warden: {
    id: 'warden', name: 'Warden', tagline: 'Hold the line.', model: 'knight',
    description: 'Armoured and patient. Wardens stand where others run, and the blows that reach them land on steel.',
    base: { maxHealth: 170, moveSpeed: 5.0, armor: 5, regen: 0.2, pickupRadius: 2.4, critChance: 0.04 },
    weapons: ['worn_oathblade', 'judgement_disc_item'], favours: ['holy', 'steel', 'melee', 'aura', 'thrown'], abilities: ['shield_bash', 'bulwark'],
    palettes: [
      { id: 'steel', name: 'Watch Steel', ui: 'linear-gradient(135deg, #a7b5bb 50%, #c2212b 50%)', paint: {} },
      { id: 'dusk', name: 'Duskbound', ui: 'linear-gradient(135deg, #5c6c8e 50%, #2e4080 50%)', paint: { plate: '#5c6c8e', cloth: '#2e4080', trim: '#d0d6e4' } },
      { id: 'sun', name: 'Sun Guard', ui: 'linear-gradient(135deg, #c8a050 50%, #f2ead6 50%)', paint: { plate: '#d2b25a', cloth: '#f0e4c8', trim: '#f2ead6', leather: '#6a4a2c' } },
      { id: 'oak', name: 'Old Oak', ui: 'linear-gradient(135deg, #8a6a48 50%, #35603a 50%)', paint: { plate: '#8a7a64', cloth: '#35603a', trim: '#dcd2b4' } },
      { id: 'ash', name: 'Blackened', ui: 'linear-gradient(135deg, #3c3836 50%, #8a2a22 50%)', paint: { plate: '#46403c', cloth: '#7a2620', trim: '#8a8078', under: '#1e1c1a' } },
    ],
  },
  reaver: {
    id: 'reaver', name: 'Reaver', tagline: 'Wade in.', model: 'barbarian',
    description: 'Heavy, reckless and very hard to stop. Reavers kill what is close, and make sure everything is close.',
    base: { maxHealth: 185, moveSpeed: 5.1, armor: 3, regen: 0.4, pickupRadius: 2.4, critChance: 0.05 },
    weapons: ['butchers_cleaver', 'gyre_axes'], favours: ['melee', 'steel', 'orbit', 'nova'], abilities: ['leap', 'warcry'],
    palettes: [
      { id: 'hide', name: 'Raw Hide', ui: '#53748d', paint: {} },
      { id: 'ember', name: 'Ember-Scarred', ui: '#a8322a', paint: { cloth: '#a8322a', fur: '#6a5a50' } },
      { id: 'frost', name: 'Frostborn', ui: '#9cc6e0', paint: { cloth: '#8cbcd8', fur: '#e4e8ec' } },
      { id: 'bog', name: 'Bogland', ui: '#5a6a2c', paint: { cloth: '#56662a', fur: '#6a6048' } },
      { id: 'soot', name: 'Soot and Bone', ui: '#3a3634', paint: { cloth: '#3a3634', fur: '#d8d0c0' } },
    ],
  },
  arcanist: {
    id: 'arcanist', name: 'Arcanist', tagline: 'Burn brighter.', model: 'mage',
    description: 'Fragile and far-reaching. Arcanists turn ember into fire, frost and seeking light, and never let anything get near.',
    base: { maxHealth: 130, moveSpeed: 5.3, armor: 1, regen: 0.2, pickupRadius: 2.8, critChance: 0.06 },
    weapons: ['apprentice_wand', 'ember_staff', 'rime_rod'], favours: ['spell'], abilities: ['blink', 'time_slip'],
    palettes: [
      { id: 'violet', name: 'Low Cloister', ui: '#54507f', paint: {} },
      { id: 'crimson', name: 'Crimson Order', ui: '#8e1c28', paint: { cloth: '#8e1c28', under: '#3a0e14', trim: '#d8a040' } },
      { id: 'azure', name: 'Tidewater', ui: '#2c5c9c', paint: { cloth: '#2c5c9c', under: '#12284a', trim: '#e8c060' } },
      { id: 'verdant', name: 'Greenhall', ui: '#2c6c4c', paint: { cloth: '#2c6c4c', under: '#10301e', trim: '#c8a050' } },
      { id: 'grey', name: 'Ashen Scholar', ui: '#6a6864', paint: { cloth: '#6a6864', under: '#2a2826', trim: '#b8b0a0' } },
    ],
  },
  stalker: {
    id: 'stalker', name: 'Stalker', tagline: 'Strike first.', model: 'rogue_hooded', altModel: 'rogue',
    description: 'Quick, patient and precise. Stalkers pick the fight\'s shape, mark what matters and are gone before it lands.',
    base: { maxHealth: 140, moveSpeed: 5.6, armor: 2, regen: 0.2, pickupRadius: 2.6, critChance: 0.1 },
    weapons: ['hunting_bow', 'knife_belt'], favours: ['ranged', 'thrown', 'nature', 'projectile'], abilities: ['mark_prey', 'smoke_bomb'],
    palettes: [
      { id: 'forest', name: 'Greenwood', ui: '#008e56', paint: {} },
      { id: 'night', name: 'Nightcloak', ui: '#2c3244', paint: { cloth: '#2c3244', under: '#161a24' } },
      { id: 'sand', name: 'Dustreach', ui: '#b89a68', paint: { cloth: '#b89a68', under: '#7a6444' } },
      { id: 'blood', name: 'Bloodfern', ui: '#7c2222', paint: { cloth: '#7c2222', under: '#3a1212' } },
      { id: 'slate', name: 'Slate', ui: '#56687a', paint: { cloth: '#56687a', under: '#2c3642' } },
    ],
  },
};

export interface Background {
  id: BackgroundId;
  name: string;
  summary: string;
  story: string;
  knowledge: string[];
  items: string[];
  /** How factions first regard you. */
  standing: Record<string, number>;
  /** How specific people first regard you. */
  npc: Record<string, { trust?: number; affection?: number; respect?: number; fear?: number }>;
  /** What it opens, said plainly on the creation screen. */
  opens: string[];
}

export const BACKGROUNDS: Record<BackgroundId, Background> = {
  hunter: {
    id: 'hunter', name: 'Hunter',
    summary: 'You read the ground and the animals on it.',
    story: 'You grew up following tracks through Thornhollow with a bow you were too small for. Animals are not mysteries to you; they are neighbours with reasons.',
    knowledge: ['beastlore'], items: ['old_hunters_cloak'],
    standing: { pack: 20 }, npc: { maeca: { trust: 15, respect: 10 }, brannoc: { respect: 5 } },
    opens: ['Read animal sign others walk past', 'Speak with the Pack, if they let you close', 'Maeca treats you as one of hers'],
  },
  scholar: {
    id: 'scholar', name: 'Scholar',
    summary: 'You know what old things mean.',
    story: 'Four years in the cellars of the Low Cloister taught you dead scripts, stranger chemistries and exactly how little the Cloister wanted you to know. You left with a cracked lens and a lot of questions.',
    knowledge: ['arcana'], items: ['cracked_lens'],
    standing: {}, npc: { wenna: { trust: 10, respect: 10 }, vonnra: { respect: 10 } },
    opens: ['Read inscriptions and old-empire script', 'Understand what the herbalist finds', 'Vonnra is curious about you'],
  },
  outcast: {
    id: 'outcast', name: 'Outcast',
    summary: 'You know how the other half gets by.',
    story: 'You have run with worse than the Kerchiefs and walked away from them too. You know the cant, the prices and which doors open at night.',
    knowledge: ['underworld'], items: ['red_kerchief', 'lockpicks'],
    standing: { kerchief: 25, watch: -10 }, npc: { rav: { trust: 20, affection: 10 }, holloway: { trust: -10 }, pell: { trust: 5 } },
    opens: ['Kerchief cant: parley instead of fight', 'Locks, fences and the night market', 'Rav trusts you; the Watch does not'],
  },
  devout: {
    id: 'devout', name: 'Devout',
    summary: 'You keep a light the dark respects.',
    story: 'The Order of the Morning Light raised you to tend lamps in chapels no one visits anymore. You carry one of them still. The dead have always been a little quieter around you.',
    knowledge: ['faith'], items: ['pilgrims_lantern'],
    standing: { order: 25 }, npc: { chid: { trust: 20, affection: 15 }, rook: { trust: 5 } },
    opens: ['Shrine rites others cannot perform', 'The dead speak, a little', 'Chid trusts you from the first word'],
  },
};

/* ------------------------------------------------------------------ traits -- */

export interface TraitDef {
  id: string;
  name: string;
  text: string;
  /** Chosen at level-ups (a pool), given by background, or earned in the world. */
  source: 'levelup' | 'world' | 'background';
  mods?: StatMod[];
  triggers?: TriggerDef[];
  /** World tags it carries ('wolf_friend' changes how the Pack reacts). */
  tags?: string[];
}

const m = (stat: StatMod['stat'], kind: StatMod['kind'], value: number): StatMod => ({ stat, kind, value, source: 'trait' });

export const TRAITS: Record<string, TraitDef> = {
  iron_constitution: { id: 'iron_constitution', name: 'Iron Constitution', source: 'levelup', text: '+25 maximum health. Injuries heal a day sooner.', mods: [m('maxHealth', 'flat', 25)], tags: ['hardy'] },
  ember_touched: { id: 'ember_touched', name: 'Ember-Touched', source: 'levelup', text: 'Every expedition begins with one free ember level.', tags: ['ember_start'] },
  quick_hands: { id: 'quick_hands', name: 'Quick Hands', source: 'levelup', text: 'Weapons fire 6% faster. +1 reroll on every draft.', mods: [m('cooldown', 'more', -0.06)], tags: ['reroll'] },
  far_reach: { id: 'far_reach', name: 'Far Reach', source: 'levelup', text: '+10% area and +1.5 m pickup reach.', mods: [m('area', 'inc', 0.1), m('pickupRadius', 'flat', 1.5)] },
  killers_eye: { id: 'killers_eye', name: 'Killer\'s Eye', source: 'levelup', text: '+6% critical chance, +20% critical damage.', mods: [m('critChance', 'flat', 0.06), m('critDamage', 'flat', 0.2)] },
  second_wind: { id: 'second_wind', name: 'Second Wind', source: 'levelup', text: 'Once per expedition, a killing blow leaves you standing at half health instead.', tags: ['revive'] },
  pyromancer: { id: 'pyromancer', name: 'Pyromancer', source: 'levelup', text: '+20% fire damage; what burns burns 30% longer.', mods: [m('damage.fire', 'inc', 0.2)] },
  frostheart: { id: 'frostheart', name: 'Frostheart', source: 'levelup', text: '+20% frost damage; chill builds faster.', mods: [m('damage.frost', 'inc', 0.2), m('statusChance', 'inc', 0.1)] },
  bloodletter: { id: 'bloodletter', name: 'Bloodletter', source: 'levelup', text: 'Bleeds hurt 30% more. Kills heal 1.', mods: [m('statusDamage', 'inc', 0.3)],
    triggers: [{ on: 'kill', effects: [{ do: 'heal', amount: 1, basis: 'flat' }] }] },
  swift: { id: 'swift', name: 'Swift', source: 'levelup', text: '+10% movement speed. Dash recharges 20% faster.', mods: [m('moveSpeed', 'inc', 0.1), m('dashCooldown', 'more', -0.2)] },
  stout_heart: { id: 'stout_heart', name: 'Stout Heart', source: 'levelup', text: '+3 armour and +10% healing received.', mods: [m('armor', 'flat', 3), m('healing', 'inc', 0.1)] },
  silver_tongue: { id: 'silver_tongue', name: 'Silver Tongue', source: 'levelup', text: 'Better prices everywhere, and people tell you a little more.', tags: ['persuasive'] },
  // Earned in the world.
  wolf_friend: { id: 'wolf_friend', name: 'Wolf-Friend', source: 'world', text: 'The Pack knows your scent. Wolves will not strike first, and some will hunt beside you.', tags: ['wolf_friend'] },
  beastslayer: { id: 'beastslayer', name: 'Beastslayer', source: 'world', text: '+20% damage against beasts. Beasts flee from you when hurt.', mods: [m('vs.wolf', 'flat', 0.2), m('vs.boar', 'flat', 0.2), m('vs.beast', 'flat', 0.2)], tags: ['beastslayer'] },
  kerchief_marked: { id: 'kerchief_marked', name: 'Kerchief-Marked', source: 'world', text: 'The Kerchiefs count you as one of theirs. The Watch counts you as one of theirs, too.', tags: ['kerchief_friend', 'wanted'] },
  risen_once: { id: 'risen_once', name: 'Risen Once', source: 'world', text: 'You have died and come back. The dead are quieter around you: +10% resistance to shadow.', mods: [m('resist.shadow', 'flat', 0.1)], tags: ['risen'] },
  lightbearer: { id: 'lightbearer', name: 'Lightbearer', source: 'world', text: 'The shrine burns for you again: +15% holy damage and +1 health regenerated per second at night.', mods: [m('damage.holy', 'inc', 0.15)], tags: ['lightbearer'] },
};

export const LEVELUP_TRAITS = Object.values(TRAITS).filter((t) => t.source === 'levelup').map((t) => t.id);
