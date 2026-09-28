/* How a survivor can look, beyond their calling's colours: the dye of the
 * cloak on their back (or none) and the tone of their skin. Each repaints
 * its swatch of the model's atlas (render/recolor.ts), keeping its shading:
 * 'calling' and 'fair' leave the model as it came. */

export const CLOAK_DYES: Array<{ id: string; name: string; color: string }> = [
  { id: 'calling', name: 'Their calling\'s', color: '' },
  { id: 'watch', name: 'Watch Blue', color: '#34508c' },
  { id: 'crimson', name: 'Crimson', color: '#9c1e24' },
  { id: 'forest', name: 'Forest', color: '#2e5c34' },
  { id: 'ochre', name: 'Ochre', color: '#c89030' },
  { id: 'violet', name: 'Violet', color: '#5c3a86' },
  { id: 'bone', name: 'Bone', color: '#dcd4c0' },
  { id: 'soot', name: 'Soot', color: '#34302e' },
  { id: 'none', name: 'No cloak', color: '' },
];

export const SKINS: Array<{ id: string; name: string; color: string }> = [
  { id: 'fair', name: 'Fair', color: '' },
  { id: 'rose', name: 'Rose', color: '#f0b8a0' },
  { id: 'warm', name: 'Warm', color: '#e0a47c' },
  { id: 'olive', name: 'Olive', color: '#c4945e' },
  { id: 'brown', name: 'Brown', color: '#946040' },
  { id: 'deep', name: 'Deep', color: '#5e3c2a' },
];

/** Hair, for those who show it. */
export const HAIRS: Array<{ id: string; name: string; color: string }> = [
  { id: 'as_is', name: 'As it grew', color: '' },
  { id: 'black', name: 'Black', color: '#2a2422' },
  { id: 'brown', name: 'Brown', color: '#5e3e28' },
  { id: 'auburn', name: 'Auburn', color: '#8e3e20' },
  { id: 'fair', name: 'Fair', color: '#d8b870' },
  { id: 'grey', name: 'Grey', color: '#a8a4a0' },
];

/** Cuts of hair for a man and for a woman (people's hairstyles; 'none' is
 *  shorn). The first is the one they start with. */
export const HAIR_STYLES: Record<'male' | 'female', string[]> = {
  male: ['Hair_SimpleParted', 'Hair_Buzzed', 'Hair_Long'],
  female: ['Hair_Long', 'Hair_Buns', 'Hair_BuzzedFemale'],
};

/** A person's clothes by kind (render/people.ts part names): the peasant's
 *  shirt, vest and trousers; the ranger's leathers; or bare to the waist
 *  (trousers and boots). A hood and a pauldron go on top. */
export function outfitFor(sex: 'male' | 'female', kind: 'peasant' | 'ranger' | 'bare', o: { hood?: boolean; pauldron?: boolean } = {}): string[] {
  const S = sex === 'male' ? 'Male' : 'Female';
  const out = kind === 'ranger'
    ? [`${S}_Ranger_Arms`, `${S}_Ranger_Body`, `${S}_Ranger_Legs`, sex === 'male' ? 'Male_Ranger_Feet_Boots' : 'Female_Ranger_Feet']
    : kind === 'bare' ? [`${S}_Peasant_Legs`, `${S}_Peasant_Feet`]
    : [`${S}_Peasant_Arms`, `${S}_Peasant_Body`, `${S}_Peasant_Legs`, `${S}_Peasant_Feet`];
  if (o.pauldron) out.push(sex === 'male' ? 'Male_Ranger_Acc_Pauldron' : 'Female_Ranger_Acc_Pauldrons');
  if (o.hood) out.push(`${S}_Ranger_Head_Hood`);
  return out;
}
