/* How a survivor can look, beyond their calling's colours: the dye of the
 * cloak on their back (or none) and the tone of their skin. Each is a
 * multiply over the model's own texture, so they stay in its palette. */

export const CLOAK_DYES: Array<{ id: string; name: string; color: string }> = [
  { id: 'calling', name: 'Their calling\'s', color: '' },
  { id: 'watch', name: 'Watch Blue', color: '#6a86c8' },
  { id: 'crimson', name: 'Crimson', color: '#c8605a' },
  { id: 'forest', name: 'Forest', color: '#7aa06a' },
  { id: 'ochre', name: 'Ochre', color: '#d8b060' },
  { id: 'violet', name: 'Violet', color: '#9a7ac0' },
  { id: 'bone', name: 'Bone', color: '#e8e0cc' },
  { id: 'soot', name: 'Soot', color: '#6a6660' },
  { id: 'none', name: 'No cloak', color: '' },
];

export const SKINS: Array<{ id: string; name: string; color: string }> = [
  { id: 'fair', name: 'Fair', color: '#ffffff' },
  { id: 'warm', name: 'Warm', color: '#f0d4bc' },
  { id: 'olive', name: 'Olive', color: '#dcc09a' },
  { id: 'brown', name: 'Brown', color: '#b8896a' },
  { id: 'deep', name: 'Deep', color: '#8a624c' },
];
