import * as THREE from 'three';
import type { School } from '@/sim/types';

/* One colour language for every effect: a school is always the same hue,
 * so a player learns to read a fight by colour alone - orange is fire,
 * pale blue is frost, violet is arcane - whatever shape it arrives in. The
 * `core` is the hot centre, the `glow` the light it throws, `dim` the smoke
 * or residue it leaves. Values above 1 are intentional: they drive bloom. */

export interface SchoolColors { core: THREE.Color; glow: THREE.Color; dim: THREE.Color; light: number }

const c = (hex: string, k = 1) => new THREE.Color(hex).multiplyScalar(k);

export const SCHOOL: Record<School, SchoolColors> = {
  physical: { core: c('#fff6e4', 2.2), glow: c('#ffd9a0', 1.4), dim: c('#8a7a66'), light: 0xffd9a0 },
  fire: { core: c('#ffe29a', 4), glow: c('#ff6a1a', 3), dim: c('#3a2a24'), light: 0xff7a2a },
  frost: { core: c('#f0fbff', 3), glow: c('#6cc8ff', 2.4), dim: c('#a8c8d8'), light: 0x8fd0ff },
  storm: { core: c('#ffffff', 4), glow: c('#8ab4ff', 3), dim: c('#5a6a9a'), light: 0x9ab8ff },
  nature: { core: c('#e8ffd0', 3), glow: c('#7aff4a', 2.4), dim: c('#3a5a2a'), light: 0x9aff6a },
  arcane: { core: c('#fff0ff', 3.2), glow: c('#c870ff', 2.8), dim: c('#4a3a6a'), light: 0xcc88ff },
  holy: { core: c('#fffbe8', 3.6), glow: c('#ffd46a', 2.8), dim: c('#b8a070'), light: 0xffe0a0 },
  shadow: { core: c('#e8d8ff', 2.4), glow: c('#8a4aff', 2.6), dim: c('#1a1024'), light: 0x9a5cff },
};

export const HOSTILE = { rim: c('#ff5a2a', 2.2), fill: c('#ff3a1a', 0.9), danger: c('#ff2a1a', 2.4) };

/** Art key -> school, for projectiles and zones that carry only an art. */
export function schoolOfArt(art: string): School {
  if (/cinder|star|flame|fire|pyre|ember|firepot/.test(art)) return 'fire';
  if (/shard|frost|ice|hail|spear_ice|deep/.test(art)) return 'frost';
  if (/arc|storm|static/.test(art)) return 'storm';
  if (/green|blight|thorn|bloom|herd|root|plague|venom|gaze/.test(art)) return 'nature';
  if (/mote|moon|arcane/.test(art)) return 'arcane';
  if (/holy|disc|dawn|sun|sanct|reckon|aegis|crescent/.test(art)) return 'holy';
  if (/umbral|ruin|siphon|tether|blood|rend|harrow|shadow/.test(art)) return 'shadow';
  return 'physical';
}
