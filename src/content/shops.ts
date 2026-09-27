/* Who sells what, and what they will buy.
 *
 * Stock is generated when a shop first opens and again every few days
 * (plain gear rolls fresh affixes each time). Some stock depends on the
 * world: Harlan's shelves fill up if his caravan comes home, Brannoc runs
 * out of hides to work if the wolves are gone, Pell sells things he should
 * not. Prices bend with how the seller feels about you. */

import type { Cond } from '@/world/logic';

export interface ShopLine { id: string; rarity?: number; qty?: number; when?: Cond; chance?: number }

export interface ShopDef {
  id: string;
  name: string;
  /** Multiplier on item value when selling to the survivor. */
  markup: number;
  /** What they will buy, by item kind ('all' for a fence). */
  buys: string[] | 'all';
  /** Fraction of value paid when buying from the survivor. */
  pays: number;
  lines: ShopLine[];
  restockDays: number;
}

export const SHOPS: Record<string, ShopDef> = {
  brannoc: {
    id: 'brannoc', name: 'Brannoc\'s Smithy', markup: 1.1, pays: 0.4, restockDays: 3,
    buys: ['weapon', 'offhand', 'head', 'body', 'material'],
    lines: [
      { id: 'iron_helm', rarity: 1 }, { id: 'chain_shirt', rarity: 1 }, { id: 'padded_jerkin', rarity: 1 }, { id: 'watch_buckler', rarity: 1 },
      { id: 'leather_cap', rarity: 2, chance: 0.6 }, { id: 'chain_shirt', rarity: 2, chance: 0.4 }, { id: 'iron_helm', rarity: 3, chance: 0.25 },
      { id: 'ashen_plate', chance: 0.5, when: { day: { gte: 2 } } },
      { id: 'butchers_cleaver', chance: 0.5 }, { id: 'gyre_axes', chance: 0.5 }, { id: 'worn_oathblade', chance: 0.5 }, { id: 'knife_belt', chance: 0.5 },
    ],
  },
  harlan: {
    id: 'harlan', name: 'Coyle Trading Post', markup: 1.0, pays: 0.35, restockDays: 2,
    buys: ['material', 'consumable', 'trophy', 'ring', 'amulet', 'cloak'],
    lines: [
      { id: 'health_draught', qty: 4 }, { id: 'bandages', qty: 3 }, { id: 'antidote', qty: 2 }, { id: 'travelers_cloak', rarity: 1 },
      { id: 'copper_ring', rarity: 1 }, { id: 'bone_amulet', rarity: 1 },
      // When the caravan is home, the shelves are full.
      { id: 'health_draught', qty: 4, when: { fact: 'caravan.cargo', eq: 'returned' } },
      { id: 'silver_ring', rarity: 2, when: { fact: 'caravan.cargo', eq: 'returned' } },
      { id: 'travelers_cloak', rarity: 3, when: { fact: 'caravan.cargo', eq: 'returned' } },
    ],
  },
  wenna: {
    id: 'wenna', name: 'Wenna\'s Remedies', markup: 1.0, pays: 0.5, restockDays: 2,
    buys: ['material'],
    lines: [{ id: 'antidote', qty: 3 }, { id: 'health_draught', qty: 2 }, { id: 'bandages', qty: 2 }, { id: 'thornseed_pouch', chance: 0.6 }],
  },
  rav: {
    id: 'rav', name: 'Rav\'s Table', markup: 1.2, pays: 0.55, restockDays: 3,
    buys: 'all',
    lines: [{ id: 'lockpicks' }, { id: 'red_kerchief' }, { id: 'antidote', qty: 2 }, { id: 'knife_belt', chance: 0.4 }, { id: 'wolf_fang_necklace', chance: 0.3 }],
  },
  vonnra: {
    id: 'vonnra', name: 'Vonnra\'s Curiosities', markup: 1.5, pays: 0.3, restockDays: 5,
    buys: ['relic', 'quest', 'amulet', 'ring'],
    lines: [
      { id: 'cracked_lens' }, { id: 'moonbrand_charm' }, { id: 'storm_totem' }, { id: 'silver_ring', rarity: 3 },
      { id: 'moonsilver_circlet', chance: 0.15, when: { day: { gte: 3 } } },
    ],
  },
  pell: {
    id: 'pell', name: 'Varrow Imports', markup: 1.3, pays: 0.3, restockDays: 3,
    buys: ['weapon', 'offhand', 'relic', 'trophy'],
    lines: [{ id: 'censer_of_dawn' }, { id: 'bone_charm' }, { id: 'grave_tether_wand' }, { id: 'blasting_ember', qty: 2 }, { id: 'apprentice_wand', chance: 0.5 }, { id: 'rime_rod', chance: 0.5 }],
  },
};
