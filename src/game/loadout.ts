import type { Loadout } from '@/render/playerView';
import type { CharacterModel } from '@/render/assets';
import { ARCHETYPES, type ArchetypeId } from '@/content/archetypes';
import { CLOAK_DYES, SKINS } from '@/content/looks';

/* What the survivor visibly carries. The KayKit models ship with every
 * weapon and hat attached; this picks the ones that match the weapon in
 * hand, the archetype's cloak and (if worn) its headgear, and the swings
 * the arm makes when the blade fires. */

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

const CAPE: Record<ArchetypeId, string> = { warden: 'Knight_Cape', reaver: 'Barbarian_Cape', arcanist: 'Mage_Cape', stalker: 'Rogue_Cape' };
const HEAD: Partial<Record<ArchetypeId, string>> = { warden: 'Knight_Helmet', reaver: 'Barbarian_Hat', arcanist: 'Mage_Hat' };

export interface LookChoice { archetype: ArchetypeId; weaponItem: string; model?: CharacterModel; palette?: string; headgear?: boolean; cloak?: string; skin?: string }

export function loadoutFor(c: LookChoice): Loadout {
  const a = ARCHETYPES[c.archetype];
  const arms = ARMS[c.weaponItem] ?? ARMS[a.weapons[0]];
  const show = [...arms.show];
  if (c.cloak !== 'none') show.push(CAPE[c.archetype]);
  const dye = CLOAK_DYES.find((d) => d.id === c.cloak)?.color || undefined;
  const skin = SKINS.find((s) => s.id === c.skin)?.color;
  const head = HEAD[c.archetype];
  if (head && c.headgear) show.push(head);
  const pal = a.palettes.find((p) => p.id === c.palette) ?? a.palettes[0];
  return {
    model: c.model ?? a.model, show, attackClips: arms.attack, heavyClip: arms.heavy, castClip: arms.cast,
    tint: pal.tint === '#ffffff' ? undefined : pal.tint,
    capeTint: dye, skinTint: skin && skin !== '#ffffff' ? skin : undefined,
  };
}
