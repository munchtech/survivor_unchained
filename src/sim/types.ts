/* The vocabulary the whole combat simulation shares. Kept free of rendering
 * so the simulation runs headless: in tests, in the balance tools, and in the
 * browser under the renderer. */

/** Damage schools. Every hit has one; every creature resists some. */
export type School = 'physical' | 'fire' | 'frost' | 'storm' | 'nature' | 'arcane' | 'holy' | 'shadow';
export const SCHOOLS: School[] = ['physical', 'fire', 'frost', 'storm', 'nature', 'arcane', 'holy', 'shadow'];

/** Who someone fights for. Hostility between factions is data (see
 *  factions in content) so the wolves and the Kerchiefs can be made to meet. */
export type FactionId =
  | 'player' | 'ally' | 'pack' | 'kerchief' | 'dead' | 'lampling' | 'blight' | 'wild' | 'watch' | 'town';

/** Families drive "damage vs beasts", bestiary counts and who recognises
 *  whom (a wolf-fang necklace is a statement to a wolf). */
export type Family = 'beast' | 'wolf' | 'boar' | 'undead' | 'kerchief' | 'lampling' | 'blighted' | 'elemental' | 'human' | 'construct';

/** Tags describe what a weapon, projectile or effect IS, so passives and
 *  items can say what they apply to without naming weapons. */
export type Tag =
  | 'projectile' | 'area' | 'melee' | 'summon' | 'aura' | 'beam' | 'chain' | 'orbit' | 'nova' | 'zone'
  | 'storm' | 'bounce' | 'ranged' | 'dot' | 'explosion' | 'trap' | 'heal' | 'thrown' | 'spell' | 'steel'
  | School;

export type StatusKind = 'burn' | 'bleed' | 'chill' | 'frozen' | 'poison' | 'shock' | 'mark' | 'sear' | 'stun' | 'fear' | 'charm';

export interface Vec { x: number; z: number }

/** Resistances as fractions: 0.25 takes 25% less, -0.5 takes 50% more. */
export type Resists = Partial<Record<School, number>>;
