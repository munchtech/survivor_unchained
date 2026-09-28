import type { Loadout } from '@/render/playerView';
import type { CharacterModel } from '@/render/assets';
import { ARCHETYPES, type ArchetypeId } from '@/content/archetypes';
import { CLOAK_DYES, SKINS, HAIRS, HAIR_STYLES, outfitFor } from '@/content/looks';
import type { PersonSpec, Sex } from '@/render/people';

/* What the survivor looks like and visibly carries: a person (a man or a
 * woman in their calling's clothes, render/people.ts) with the weapon in
 * hand as a real model (render/arms.ts), the stance they hold it in, and
 * the swings the arm makes when the blade fires.
 *
 * The KayKit figures (a model with every weapon and hat attached, shown
 * or hidden) remain for anything that asks for one by name. */

interface Arms { show: string[]; attack: string[]; heavy: string; cast?: string }

const ARMS: Record<string, Arms> = {
  worn_oathblade: { show: ['1H_Sword', 'Round_Shield'], attack: ['1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Slice_Horizontal', '1H_Melee_Attack_Chop'], heavy: '1H_Melee_Attack_Chop' },
  judgement_disc_item: { show: ['1H_Sword', 'Badge_Shield'], attack: ['Throw'], heavy: '1H_Melee_Attack_Chop' },
  butchers_cleaver: { show: ['2H_Axe'], attack: ['2H_Melee_Attack_Slice', '2H_Melee_Attack_Chop'], heavy: '2H_Melee_Attack_Spin' },
  gyre_axes: { show: ['1H_Axe', '1H_Axe_Offhand'], attack: ['Dualwield_Melee_Attack_Slice', 'Dualwield_Melee_Attack_Chop'], heavy: '2H_Melee_Attack_Spin' },
  apprentice_wand: { show: ['1H_Wand', 'Spellbook'], attack: ['Spellcast_Shoot'], heavy: 'Spellcast_Raise', cast: 'Spellcast_Shoot' },
  ember_staff: { show: ['2H_Staff'], attack: ['Spellcast_Shoot'], heavy: 'Spellcast_Raise', cast: 'Spellcast_Shoot' },
  rime_rod: { show: ['2H_Staff'], attack: ['Spellcast_Shoot'], heavy: 'Spellcast_Raise', cast: 'Spellcast_Shoot' },
  hunting_bow: { show: ['1H_Crossbow', 'Knife_Offhand'], attack: ['1H_Ranged_Shoot'], heavy: 'Dualwield_Melee_Attack_Slice' },
  knife_belt: { show: ['Knife', 'Knife_Offhand'], attack: ['Throw'], heavy: 'Dualwield_Melee_Attack_Slice' },
};

/** A person's weapons, by the item in hand: what each hand holds, the
 *  stance, and library clips (Universal Animation Libraries). */
interface Held { right: string; left?: string; forearm?: string; idle: string; attack: string[]; heavy: string; cast?: string }
const SWORD = ['Sword_Regular_A', 'Sword_Regular_B', 'Sword_Regular_C'];
const SPELL = { attack: ['Spell_Simple_Shoot'], heavy: 'Spell_Simple_Enter', cast: 'Spell_Simple_Shoot' };
const HELD: Record<string, Held> = {
  worn_oathblade: { right: 'chevalier_sword', forearm: 'shield_round', idle: 'Sword_Idle', attack: SWORD, heavy: 'Sword_Attack' },
  judgement_disc_item: { right: 'viking_sword', forearm: 'shield_round', idle: 'Sword_Idle', attack: ['OverhandThrow'], heavy: 'Sword_Attack' },
  butchers_cleaver: { right: 'viking_axe', idle: 'Sword_Idle', attack: ['Sword_Attack', 'Sword_Regular_B'], heavy: 'Sword_Heavy_Combo' },
  gyre_axes: { right: 'viking_axe', left: 'viking_axe', idle: 'Sword_Idle', attack: ['Sword_Regular_A', 'Sword_Regular_C'], heavy: 'Sword_Heavy_Combo' },
  apprentice_wand: { right: 'short_staff', idle: 'Idle_Loop', ...SPELL },
  // A staff stands upright in both hands.
  ember_staff: { right: 'mage_staff', idle: 'Pistol_Idle_Loop', ...SPELL },
  rime_rod: { right: 'mage_staff', idle: 'Pistol_Idle_Loop', ...SPELL },
  hunting_bow: { right: 'crossbow', idle: 'Pistol_Idle_Loop', attack: ['Pistol_Shoot'], heavy: 'Pistol_Shoot' },
  knife_belt: { right: 'daggers', left: 'dagger_b', idle: 'Sword_Idle', attack: ['OverhandThrow'], heavy: 'Sword_Regular_Combo' },
};

/** Each calling's clothes. The Reaver goes bare-chested (a woman keeps the
 *  band the body is painted with). A hood, where worn, covers the hair. */
const outfitOf = (archetype: ArchetypeId, sex: Sex, hood: boolean) =>
  outfitFor(sex, archetype === 'reaver' ? 'bare' : archetype === 'arcanist' ? 'peasant' : 'ranger', { hood, pauldron: archetype === 'warden' });

const darker = (hex: string) => `#${[1, 3, 5].map((i) => Math.round(parseInt(hex.slice(i, i + 2), 16) * 0.45).toString(16).padStart(2, '0')).join('')}`;

const CAPE: Record<ArchetypeId, string> = { warden: 'Knight_Cape', reaver: 'Barbarian_Cape', arcanist: 'Mage_Cape', stalker: 'Rogue_Cape' };
const HEAD: Partial<Record<ArchetypeId, string>> = { warden: 'Knight_Helmet', reaver: 'Barbarian_Hat', arcanist: 'Mage_Hat' };

export interface LookChoice {
  archetype: ArchetypeId; weaponItem: string; model?: CharacterModel; palette?: string; headgear?: boolean; cloak?: string; skin?: string; hair?: string;
  sex?: Sex; hairStyle?: string; beard?: boolean; figure?: number;
}

/** Whether the calling's hood is up: the Stalker's by their model (hood up
 *  or down), the Warden's and Arcanist's as their headgear. */
const hooded = (c: LookChoice) => c.archetype === 'stalker' ? (c.model ?? 'rogue_hooded') === 'rogue_hooded' : c.archetype !== 'reaver' && (c.headgear ?? true);

export function loadoutFor(c: LookChoice): Loadout {
  const a = ARCHETYPES[c.archetype];
  const arms = ARMS[c.weaponItem] ?? ARMS[a.weapons[0]];
  const show = [...arms.show];
  if (c.cloak !== 'none') show.push(CAPE[c.archetype]);
  const dye = CLOAK_DYES.find((d) => d.id === c.cloak)?.color || '';
  const skin = SKINS.find((s) => s.id === c.skin)?.color || '';
  const hair = HAIRS.find((h) => h.id === c.hair)?.color || '';
  const head = HEAD[c.archetype];
  if (head && c.headgear) show.push(head);
  const pal = a.palettes.find((p) => p.id === c.palette) ?? a.palettes[0];
  const held = HELD[c.weaponItem] ?? HELD[a.weapons[0]];
  const sex = c.sex ?? 'male';
  const hood = hooded(c);
  const person: PersonSpec = {
    sex, outfit: outfitOf(c.archetype, sex, hood),
    hair: hood || c.hairStyle === 'none' ? null : c.hairStyle ?? HAIR_STYLES[sex][0],
    beard: sex === 'male' && (c.beard ?? true),
    hairColor: hair || undefined, skin: skin || undefined, figure: c.figure,
    // The calling's colours dye the cloth; trousers take the darker colour
    // (or the cloth's, darker still).
    dye: pal.paint.cloth ? { cloth: pal.paint.cloth, under: pal.paint.under ?? darker(pal.paint.cloth) } : undefined,
  };
  return {
    model: c.model ?? a.model, show, attackClips: held.attack, heavyClip: held.heavy, castClip: held.cast,
    // The calling's colours on the cloth, the chosen skin and hair; the
    // cloak takes a dye of its own, or follows the calling.
    paint: { body: { ...pal.paint, skin, hair }, cloak: { cloak: dye } },
    person, wield: { right: held.right, left: held.left, forearm: held.forearm }, idle: held.idle,
  };
}

/** A survivor's own look, from their character: one place, so the figure in
 *  play, the pack, the sheet and every portrait always agree. */
export function lookOf(ch: Omit<LookChoice, 'weaponItem'> & { equipment: { weapon?: { def: string } | null } }): Loadout {
  return loadoutFor({
    archetype: ch.archetype, weaponItem: ch.equipment.weapon?.def ?? ARCHETYPES[ch.archetype].weapons[0],
    model: ch.model, palette: ch.palette, headgear: ch.headgear, cloak: ch.cloak, skin: ch.skin, hair: ch.hair,
    sex: ch.sex, hairStyle: ch.hairStyle, beard: ch.beard, figure: ch.figure,
  });
}
