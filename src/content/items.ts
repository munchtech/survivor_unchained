import type { StatMod } from '@/sim/stats';
import type { TriggerDef } from '@/sim/procs';
import type { StatusKind } from '@/sim/types';

/* Things the survivor can carry.
 *
 * The rule for this game's gear: an item should change how you play or how
 * the world treats you, not only what a number says. So beside stat mods,
 * items carry:
 *
 *   weapon     the automatic weapon it puts in your hands
 *   triggers   rules it adds to the machine (see sim/procs.ts)
 *   tags       what the WORLD sees: a wolf-fang necklace is a statement to a
 *              wolf; a red kerchief is a statement to a Kerchief and to the
 *              Watch; a plague mask lets you walk where the air is poison
 *   statuses   what it applies, so evolutions keyed to a status can see it
 *   downside   the price, said plainly
 *
 * Plain drops (a leather cap, a copper ring) roll affixes from AFFIXES.
 * Named things never roll: they are what they are. */

export type Slot = 'weapon' | 'offhand' | 'head' | 'body' | 'cloak' | 'amulet' | 'ring' | 'relic';
export type ItemKind = Slot | 'material' | 'consumable' | 'quest' | 'tool' | 'trophy';
export const EQUIP_SLOTS = ['weapon', 'offhand', 'head', 'body', 'cloak', 'amulet', 'ring1', 'ring2', 'relic'] as const;
export type EquipSlot = (typeof EQUIP_SLOTS)[number];

export const RARITY_NAMES = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Storied'];

export interface ItemDef {
  id: string;
  name: string;
  kind: ItemKind;
  rarity: number;
  icon: string;
  value: number;
  description: string;
  lore?: string;
  weapon?: { id: string; rank: number };
  mods?: StatMod[];
  triggers?: TriggerDef[];
  tags?: string[];
  statuses?: StatusKind[];
  downside?: string;
  stack?: number;
  /** Rolls affixes when it drops. */
  base?: boolean;
  consumable?: { heal?: number; cure?: string[]; buff?: string };
  unique?: boolean;
}

const mod = (stat: StatMod['stat'], kind: StatMod['kind'], value: number, when?: StatMod['when']): StatMod => ({ stat, kind, value, source: 'item', when });

export const ITEMS: Record<string, ItemDef> = {
  /* ----------------------------------------------------------- weapons -- */
  worn_oathblade: { id: 'worn_oathblade', name: 'Worn Oathblade', kind: 'weapon', rarity: 0, icon: 'sword', value: 20,
    description: 'Swings itself at whatever is nearest, in a wide arc.', weapon: { id: 'oathblade', rank: 1 },
    lore: 'Every Watch recruit swore on a blade like this. Most of the oaths outlasted the recruits.' },
  judgement_disc_item: { id: 'judgement_disc_item', name: 'Watch Buckler', kind: 'weapon', rarity: 0, icon: 'shield', value: 20,
    description: 'A thrown shield that ricochets between foes.', weapon: { id: 'judgement_disc', rank: 1 } },
  butchers_cleaver: { id: 'butchers_cleaver', name: 'Butcher\'s Cleaver', kind: 'weapon', rarity: 0, icon: 'cleaver', value: 20,
    description: 'A wide, heavy chop in front of you that opens wounds.', weapon: { id: 'cleaver', rank: 1 }, statuses: ['bleed'] },
  gyre_axes: { id: 'gyre_axes', name: 'Pair of Gyre Axes', kind: 'weapon', rarity: 0, icon: 'axe', value: 20,
    description: 'Axes that circle you, shredding whatever closes in.', weapon: { id: 'axe_gyre', rank: 1 } },
  apprentice_wand: { id: 'apprentice_wand', name: 'Apprentice\'s Wand', kind: 'weapon', rarity: 0, icon: 'wand', value: 20,
    description: 'Looses seeking motes that find their own way.', weapon: { id: 'seeking_motes', rank: 1 } },
  ember_staff: { id: 'ember_staff', name: 'Ember Staff', kind: 'weapon', rarity: 0, icon: 'staff', value: 20,
    description: 'Hurls slow cinders that burst and set things burning.', weapon: { id: 'cinderfall', rank: 1 }, statuses: ['burn'] },
  rime_rod: { id: 'rime_rod', name: 'Rime Rod', kind: 'weapon', rarity: 0, icon: 'staff', value: 20,
    description: 'Piercing shards of cold that chill and, in time, freeze.', weapon: { id: 'rimeshard', rank: 1 }, statuses: ['chill'] },
  hunting_bow: { id: 'hunting_bow', name: 'Hunter\'s Crossbow', kind: 'weapon', rarity: 0, icon: 'bow', value: 20,
    description: 'Looses a spread of bolts at the nearest foe.', weapon: { id: 'volley', rank: 1 } },
  knife_belt: { id: 'knife_belt', name: 'Knife Belt', kind: 'weapon', rarity: 0, icon: 'dagger', value: 20,
    description: 'Throws a ring of knives in every direction.', weapon: { id: 'knifestorm', rank: 1 } },
  storm_totem: { id: 'storm_totem', name: 'Storm-Carved Totem', kind: 'offhand', rarity: 2, icon: 'totem', value: 80,
    description: 'Calls lightning that leaps between foes.', weapon: { id: 'arcweb', rank: 2 }, statuses: ['shock'],
    lore: 'The Karrash carve these from lightning-struck oak. This one still hums.' },
  censer_of_dawn: { id: 'censer_of_dawn', name: 'Censer of Dawn', kind: 'offhand', rarity: 2, icon: 'censer', value: 90,
    description: 'Pulses searing Light outward from you. The dead hate it.', weapon: { id: 'dawnpulse', rank: 2 }, statuses: ['sear'],
    mods: [mod('damage.holy', 'inc', 0.1)] },
  moonbrand_charm: { id: 'moonbrand_charm', name: 'Moonbrand Charm', kind: 'offhand', rarity: 1, icon: 'moon', value: 60,
    description: 'Moonlit flame that tracks its prey and marks it.', weapon: { id: 'moonbrand', rank: 1 }, statuses: ['mark'] },
  thornseed_pouch: { id: 'thornseed_pouch', name: 'Thornseed Pouch', kind: 'offhand', rarity: 1, icon: 'seed', value: 55,
    description: 'Brambles burst up under the nearest crowd.', weapon: { id: 'thornbloom', rank: 1 } },
  grave_tether_wand: { id: 'grave_tether_wand', name: 'Grave Tether', kind: 'offhand', rarity: 2, icon: 'wand_dark', value: 85,
    description: 'Coils of dark that wound the living and knit your own flesh.', weapon: { id: 'grave_tether', rank: 2 },
    downside: 'The Order of Morning Light does not approve.', tags: ['necromantic'] },

  /* ------------------------------------------------ named, world-facing -- */
  old_hunters_cloak: { id: 'old_hunters_cloak', name: 'Old Hunter\'s Cloak', kind: 'cloak', rarity: 1, icon: 'cloak', value: 40,
    description: '25% less from beasts. 10% faster while beasts are near.',
    mods: [mod('from.wolf', 'flat', 0.25), mod('from.boar', 'flat', 0.25), mod('from.beast', 'flat', 0.25), mod('moveSpeed', 'inc', 0.1, 'nearBeasts'), mod('resist.fire', 'flat', -0.15)],
    downside: '15% more damage from fire: old wool, older grease.',
    tags: ['beastscent'], lore: 'It smells of pine, smoke and wolf. The wolves notice.' },
  wolf_fang_necklace: { id: 'wolf_fang_necklace', name: 'Wolf-Fang Necklace', kind: 'amulet', rarity: 2, icon: 'fang', value: 90,
    description: 'Hits have a 12% chance to bleed. +30% critical chance against the bleeding.',
    triggers: [{ on: 'hit', chance: 0.12, effects: [{ do: 'status', target: 'hit', status: { kind: 'bleed', chance: 1, power: 0.35, duration: 3 } }] }],
    statuses: ['bleed'], tags: ['wolf_fang'],
    lore: 'A wolf does not give up a fang. A wolf that sees you wearing one will want to know how you came by it.' },
  ashen_plate: { id: 'ashen_plate', name: 'Ashen Plate', kind: 'body', rarity: 3, icon: 'armor_heavy', value: 160,
    description: '+8 armour. 40% fire resistance. +20% fire damage. Standing in fire grants 8 more armour.',
    mods: [mod('armor', 'flat', 8), mod('resist.fire', 'flat', 0.4), mod('damage.fire', 'inc', 0.2), mod('armor', 'flat', 8, 'inBurning'), mod('moveSpeed', 'inc', -0.08)],
    downside: '8% slower. It weighs what it weighs.', tags: ['fireproof'],
    lore: 'Forged in a burning house by a smith who would not leave it.' },
  red_kerchief: { id: 'red_kerchief', name: 'Red Kerchief', kind: 'head', rarity: 1, icon: 'kerchief', value: 15,
    description: 'Kerchiefs take you for one of their own - until you draw on them.',
    tags: ['kerchief_colors'], downside: 'The Watch takes you for one of them, too.',
    lore: 'Red cloth over the face. The rest of the uniform is attitude.' },
  blightward_mask: { id: 'blightward_mask', name: 'Blightward Mask', kind: 'head', rarity: 2, icon: 'mask', value: 110,
    description: 'Breathe blighted air unharmed. 50% nature resistance.',
    mods: [mod('resist.nature', 'flat', 0.5), mod('resist.shadow', 'flat', 0.15)], tags: ['plague_mask'],
    lore: 'Wenna stuffs the beak with bitterroot and something she will not name.' },
  pilgrims_lantern: { id: 'pilgrims_lantern', name: 'Pilgrim\'s Ember-Lantern', kind: 'relic', rarity: 1, icon: 'lantern', value: 50,
    description: 'Your light reaches 40% farther. The dead take 15% more from you.',
    mods: [mod('lightRadius', 'inc', 0.4), mod('vs.undead', 'flat', 0.15)], tags: ['holy_light'],
    lore: 'Lit from the last lamp in the Chapel of the Morning Light. It has never gone out.' },
  cracked_lens: { id: 'cracked_lens', name: 'Cracked Lens', kind: 'relic', rarity: 1, icon: 'lens', value: 45,
    description: '+5% critical chance. Old script becomes legible through it.',
    mods: [mod('critChance', 'flat', 0.05)], tags: ['scholar_lens'],
    lore: 'Ground in the Low Cloister for reading palimpsests. The crack is newer.' },
  lockpicks: { id: 'lockpicks', name: 'Lockpicks', kind: 'tool', rarity: 0, icon: 'picks', value: 10,
    description: 'Opens simple locks. Carried, not worn.', tags: ['lockpick'] },
  moonsilver_circlet: { id: 'moonsilver_circlet', name: 'Moonsilver Circlet', kind: 'head', rarity: 4, icon: 'circlet', value: 400, unique: true,
    description: '+15% damage at night. Critical strikes at night call a shaft of moonlight.',
    mods: [mod('damage', 'inc', 0.15, 'night')],
    triggers: [{ on: 'crit', chance: 0.25, icd: 0.5, effects: [{ do: 'strike', count: 1, radius: 1.4, damage: 30, basis: 'flat', school: 'arcane', area: 3 }] }],
    tags: ['moon_touched'], lore: 'It was in the grove, under the brambles, where the wolves go when one of them is dying.' },
  grimtunnels_lamp: { id: 'grimtunnels_lamp', name: 'Grimtunnel\'s Spare Lamp', kind: 'relic', rarity: 3, icon: 'lamp', value: 220, unique: true,
    description: '+25% fire damage. Lamplings hesitate before they strike you.',
    mods: [mod('damage.fire', 'inc', 0.25), mod('from.lampling', 'flat', 0.3)], tags: ['digger_lamp'],
    lore: 'He dropped it climbing into his pod. It is still warm, and it is still his, and he will want it back.' },
  wardens_lampiron: { id: 'wardens_lampiron', name: 'The Warden\'s Lamp-Iron', kind: 'relic', rarity: 3, icon: 'lantern', value: 240, unique: true,
    description: '+20% damage to the dead. Killing one has a 12% chance to loose a pale flame that strikes the next.',
    mods: [mod('vs.undead', 'flat', 0.2)],
    triggers: [{ on: 'kill', chance: 0.12, icd: 0.3, when: { targetFamily: 'undead' }, effects: [{ do: 'strike', count: 1, radius: 1.3, damage: 22, basis: 'flat', school: 'holy', area: 7 }] }],
    tags: ['holy_light', 'warden_iron'], lore: 'The iron cage of the lamp the Ford-Warden carried. Whatever burned in it went down a hole in Grimtunnel\'s arms. The cage still remembers the light.' },
  bone_charm: { id: 'bone_charm', name: 'Barrow-Bone Charm', kind: 'amulet', rarity: 2, icon: 'bone', value: 90,
    description: '+20% damage to the dead. Kills have a 3% chance to raise a servant for 10 s.',
    mods: [mod('vs.undead', 'flat', 0.2)],
    triggers: [{ on: 'kill', chance: 0.03, effects: [{ do: 'raise', kind: 'ghoul', duration: 10, max: 3 }] }],
    tags: ['necromantic'], downside: 'Chid will know what it is.' },

  /* ------------------------------------------------ plain gear (affixes) -- */
  leather_cap: { id: 'leather_cap', name: 'Leather Cap', kind: 'head', rarity: 0, icon: 'helm_light', value: 8, base: true, description: 'A cap. It keeps rain off.', mods: [mod('armor', 'flat', 1)] },
  iron_helm: { id: 'iron_helm', name: 'Iron Helm', kind: 'head', rarity: 0, icon: 'helm', value: 18, base: true, description: 'Dented, but it was dented protecting someone.', mods: [mod('armor', 'flat', 3), mod('moveSpeed', 'inc', -0.02)] },
  padded_jerkin: { id: 'padded_jerkin', name: 'Padded Jerkin', kind: 'body', rarity: 0, icon: 'armor_light', value: 12, base: true, description: 'Quilted linen.', mods: [mod('armor', 'flat', 2), mod('maxHealth', 'flat', 10)] },
  chain_shirt: { id: 'chain_shirt', name: 'Chain Shirt', kind: 'body', rarity: 0, icon: 'armor', value: 30, base: true, description: 'Rings on rings.', mods: [mod('armor', 'flat', 5), mod('moveSpeed', 'inc', -0.04)] },
  travelers_cloak: { id: 'travelers_cloak', name: 'Traveller\'s Cloak', kind: 'cloak', rarity: 0, icon: 'cloak', value: 10, base: true, description: 'Grey wool.', mods: [mod('moveSpeed', 'inc', 0.03)] },
  copper_ring: { id: 'copper_ring', name: 'Copper Ring', kind: 'ring', rarity: 0, icon: 'ring', value: 10, base: true, description: 'Green at the edges.' },
  silver_ring: { id: 'silver_ring', name: 'Silver Ring', kind: 'ring', rarity: 1, icon: 'ring', value: 25, base: true, description: 'Bright, and a little cold.' },
  bone_amulet: { id: 'bone_amulet', name: 'Knucklebone Amulet', kind: 'amulet', rarity: 0, icon: 'bone', value: 12, base: true, description: 'Someone\'s knuckle, on a string.' },
  watch_buckler: { id: 'watch_buckler', name: 'Old Watch Shield', kind: 'offhand', rarity: 0, icon: 'shield', value: 20, base: true, description: 'Carries the Watch\'s faded torch.', mods: [mod('armor', 'flat', 3), mod('block', 'flat', 1)] },

  /* ----------------------------------------------------------- materials -- */
  wolf_pelt: { id: 'wolf_pelt', name: 'Wolf Pelt', kind: 'material', rarity: 0, icon: 'pelt', value: 12, stack: 20, description: 'Thick grey fur. Brannoc pays for these; Holloway counts them.' },
  boar_hide: { id: 'boar_hide', name: 'Boar Hide', kind: 'material', rarity: 0, icon: 'hide', value: 10, stack: 20, description: 'Bristled and tough.' },
  bitterroot: { id: 'bitterroot', name: 'Bitterroot', kind: 'material', rarity: 0, icon: 'root', value: 6, stack: 20, description: 'Grows where the water is bad. Wenna wants it.' },
  moonpetal: { id: 'moonpetal', name: 'Moonpetal', kind: 'material', rarity: 2, icon: 'flower', value: 40, stack: 10, description: 'Opens only at night, only where the ground is clean.' },
  bone_dust: { id: 'bone_dust', name: 'Barrow Dust', kind: 'material', rarity: 0, icon: 'dust', value: 5, stack: 20, description: 'What the risen leave behind.' },
  ember_shard: { id: 'ember_shard', name: 'Ember Shard', kind: 'material', rarity: 1, icon: 'ember', value: 18, stack: 20, description: 'A stone that kept some of its light. It does not keep forever.' },
  kerchief_cloth: { id: 'kerchief_cloth', name: 'Red Cloth', kind: 'material', rarity: 0, icon: 'kerchief', value: 3, stack: 20, description: 'Cut from a Kerchief. Proof, of a sort.' },

  /* --------------------------------------------------------- consumables -- */
  health_draught: { id: 'health_draught', name: 'Health Draught', kind: 'consumable', rarity: 0, icon: 'potion', value: 15, stack: 10, description: 'Heals 40% of your health.', consumable: { heal: 0.4 } },
  antidote: { id: 'antidote', name: 'Antidote', kind: 'consumable', rarity: 0, icon: 'antidote', value: 12, stack: 10, description: 'Cures poison and the blight-sickness.', consumable: { cure: ['poisoned', 'blightsick'] } },
  bandages: { id: 'bandages', name: 'Clean Bandages', kind: 'consumable', rarity: 0, icon: 'bandage', value: 8, stack: 10, description: 'Treats a wound: an injury heals a day sooner.', consumable: { cure: ['wounded'] } },

  /* ---------------------------------------------------------- quest items -- */
  greymuzzle_fang: { id: 'greymuzzle_fang', name: 'Greymuzzle\'s Fang', kind: 'trophy', rarity: 3, icon: 'fang', value: 60, description: 'The old wolf\'s fang. Holloway would pay for it. Maeca would not want to see it.' },
  stream_sample: { id: 'stream_sample', name: 'Stream Sample', kind: 'quest', rarity: 1, icon: 'vial', value: 0, description: 'A stoppered bottle of green water from the Thornhollow stream.' },
  slurry_sample: { id: 'slurry_sample', name: 'Ember Slurry', kind: 'quest', rarity: 1, icon: 'vial_orange', value: 0, description: 'Warm, faintly glowing sludge scraped from a pipe.' },
  caravan_manifest: { id: 'caravan_manifest', name: 'Torn Manifest', kind: 'quest', rarity: 1, icon: 'scroll', value: 0, description: 'A Coyle Company manifest: salt, cloth, iron... and six crates marked only "B.E.", for a buyer named G.' },
  coyle_strongbox: { id: 'coyle_strongbox', name: 'Coyle Strongbox', kind: 'quest', rarity: 2, icon: 'chest', value: 250, description: 'Heavy, locked, stamped with the Coyle Company seal. Harlan wants it back. Rav knows someone who would want it more.' },
  pell_ledger: { id: 'pell_ledger', name: 'Pell\'s Ledger', kind: 'quest', rarity: 2, icon: 'book', value: 0, description: 'Payments to "R." on the night the caravan was taken. And one to the toll clerk.' },
  clerks_key: { id: 'clerks_key', name: 'Toll Clerk\'s Key', kind: 'quest', rarity: 1, icon: 'key', value: 0, description: 'A key to Pell\'s warehouse, which the clerk should not have had.' },
  sigil_fragment: { id: 'sigil_fragment', name: 'Sigil Fragment', kind: 'quest', rarity: 3, icon: 'sigil', value: 0, description: 'Black stone, cut in a shape that fits the sealed door. It hums against your teeth.', lore: 'Found in the hand of someone who did not make it out.' },
  map_fragment: { id: 'map_fragment', name: 'Digger\'s Map', kind: 'quest', rarity: 2, icon: 'map', value: 0, description: 'A lampling survey of the tunnels under the Verge. The last tunnel just says "DOWN" and keeps going.' },
  blasting_ember: { id: 'blasting_ember', name: 'Blasting Ember', kind: 'tool', rarity: 1, icon: 'bomb', value: 30, stack: 5, description: 'A crate-charge of unstable ember. Something could be blown open with this. Or up.', tags: ['explosive'] },
};

/* ------------------------------------------------------------------ affixes -- */

export interface AffixDef {
  id: string;
  name: string; // "of the Wolf", "Tempered"
  prefix: boolean;
  slots: ItemKind[];
  mods: (tier: number) => StatMod[];
  text: (tier: number) => string;
}

export const AFFIXES: AffixDef[] = [
  { id: 'sturdy', name: 'Sturdy', prefix: true, slots: ['head', 'body', 'cloak', 'offhand'], mods: (t) => [mod('armor', 'flat', 1 + t)], text: (t) => `+${1 + t} armour` },
  { id: 'hale', name: 'Hale', prefix: true, slots: ['body', 'amulet', 'ring', 'head'], mods: (t) => [mod('maxHealth', 'flat', 10 + t * 8)], text: (t) => `+${10 + t * 8} maximum health` },
  { id: 'fleet', name: 'Fleet', prefix: true, slots: ['cloak', 'ring', 'amulet'], mods: (t) => [mod('moveSpeed', 'inc', 0.03 + t * 0.02)], text: (t) => `+${Math.round((0.03 + t * 0.02) * 100)}% movement speed` },
  { id: 'keen', name: 'Keen', prefix: true, slots: ['ring', 'amulet', 'head'], mods: (t) => [mod('critChance', 'flat', 0.02 + t * 0.015)], text: (t) => `+${(2 + t * 1.5).toFixed(1)}% critical chance` },
  { id: 'searing', name: 'Searing', prefix: true, slots: ['ring', 'amulet', 'offhand'], mods: (t) => [mod('damage.fire', 'inc', 0.08 + t * 0.05)], text: (t) => `+${Math.round((0.08 + t * 0.05) * 100)}% fire damage` },
  { id: 'rimed', name: 'Rimed', prefix: true, slots: ['ring', 'amulet', 'offhand'], mods: (t) => [mod('damage.frost', 'inc', 0.08 + t * 0.05)], text: (t) => `+${Math.round((0.08 + t * 0.05) * 100)}% frost damage` },
  { id: 'honed', name: 'Honed', prefix: true, slots: ['ring', 'amulet', 'offhand'], mods: (t) => [mod('damage.physical', 'inc', 0.08 + t * 0.05)], text: (t) => `+${Math.round((0.08 + t * 0.05) * 100)}% physical damage` },
  { id: 'hallowed', name: 'Hallowed', prefix: true, slots: ['amulet', 'ring', 'relic'], mods: (t) => [mod('damage.holy', 'inc', 0.1 + t * 0.05)], text: (t) => `+${Math.round((0.1 + t * 0.05) * 100)}% holy damage` },
  { id: 'of_haste', name: 'of Haste', prefix: false, slots: ['ring', 'amulet', 'cloak'], mods: (t) => [mod('cooldown', 'more', -(0.03 + t * 0.02))], text: (t) => `${Math.round((0.03 + t * 0.02) * 100)}% faster weapons` },
  { id: 'of_reach', name: 'of Reach', prefix: false, slots: ['ring', 'amulet', 'head'], mods: (t) => [mod('area', 'inc', 0.05 + t * 0.03)], text: (t) => `+${Math.round((0.05 + t * 0.03) * 100)}% area` },
  { id: 'of_the_wolf', name: 'of the Wolf', prefix: false, slots: ['cloak', 'body', 'head', 'amulet'], mods: (t) => [mod('from.wolf', 'flat', 0.1 + t * 0.05)], text: (t) => `${Math.round((0.1 + t * 0.05) * 100)}% less damage from wolves` },
  { id: 'of_embers', name: 'of Embers', prefix: false, slots: ['ring', 'amulet', 'relic'], mods: (t) => [mod('xpGain', 'inc', 0.05 + t * 0.03)], text: (t) => `+${Math.round((0.05 + t * 0.03) * 100)}% ember gained` },
  { id: 'of_mending', name: 'of Mending', prefix: false, slots: ['body', 'amulet', 'ring'], mods: (t) => [mod('regen', 'flat', 0.2 + t * 0.2)], text: (t) => `+${(0.2 + t * 0.2).toFixed(1)} health per second` },
  { id: 'of_the_grave', name: 'of the Grave', prefix: false, slots: ['cloak', 'body', 'amulet'], mods: (t) => [mod('resist.shadow', 'flat', 0.08 + t * 0.05), mod('from.undead', 'flat', 0.05 + t * 0.03)], text: (t) => `+${Math.round((0.08 + t * 0.05) * 100)}% shadow resistance; less from the dead` },
  { id: 'of_greed', name: 'of Greed', prefix: false, slots: ['ring', 'amulet'], mods: (t) => [mod('goldGain', 'inc', 0.1 + t * 0.08), mod('pickupRadius', 'flat', 0.5 + t * 0.3)], text: (t) => `+${Math.round((0.1 + t * 0.08) * 100)}% gold, longer reach for pickups` },
];
