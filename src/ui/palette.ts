import type { School } from '@/sim/types';

/* The effect palette, in interface colours: the same hue language as the
 * spells on the field, toned for text and trim instead of bloom. */
export const SCHOOL_UI: Record<School, string> = {
  physical: '#e6d2ae',
  fire: '#ff8a3a',
  frost: '#8fd4ff',
  storm: '#a6c0ff',
  nature: '#93e05e',
  arcane: '#cf94ff',
  holy: '#ffd36a',
  shadow: '#a47aff',
};

export const RARITY_UI: Record<string, number> = { common: 0, uncommon: 1, rare: 2, epic: 3, legendary: 4, storied: 5 };
