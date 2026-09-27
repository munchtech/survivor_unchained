import type { CharacterModel } from '@/render/assets';

/* The people of the Waystation.
 *
 * Built from the same five bodies as everyone else, told apart by what
 * they carry, what they wear, how they stand and what colour their cloth
 * has faded to. Each has a place they are usually found, a pose that says
 * what they are doing there, and a few things they say to nobody in
 * particular when you walk past. */

export interface NpcDef {
  id: string;
  name: string;
  title: string;
  model: CharacterModel;
  show: string[];
  /** Cloth colour (skin and faces keep their own). */
  tint?: string;
  scale?: number;
  /** A looping pose: what they do while they wait. */
  idle: string;
  /** Where they stand in the Waystation, by day. */
  spot: { x: number; z: number; facing: number };
  /** Said aloud when the survivor passes. */
  barks: string[];
  /** ...and after dark, if different. */
  nightBarks?: string[];
  /** Short line for the nameplate once met ("Innkeeper"). */
  role: string;
}

export const NPCS: Record<string, NpcDef> = {
  rook: {
    id: 'rook', name: 'Mother Rook', title: 'Keeper of the Last Lamp', role: 'Innkeeper',
    model: 'barbarian', show: ['Mug'], tint: '#8a5a6a', scale: 0.95, idle: 'Idle',
    spot: { x: -11.2, z: 12.6, facing: Math.PI / 2 },
    barks: ['Beds are dry and the stew is hot. That is more than most can say.', 'Wipe your boots.', 'If you are bleeding, bleed outside.'],
    nightBarks: ['Lamps stay lit till the last one\'s in.', 'Bed\'s warm if you want it. Stew\'s gone.', 'Quietly, now. People are sleeping.'],
  },
  holloway: {
    id: 'holloway', name: 'Captain Holloway', title: 'Of the Waystation Watch', role: 'Watch captain',
    model: 'knight', show: ['1H_Sword', 'Rectangle_Shield', 'Knight_Cape'], tint: '#9aa8c0', idle: 'Idle',
    spot: { x: -3.6, z: -9.5, facing: 0.6 },
    barks: ['Five gold a pelt. Fifty for the old grey one.', 'Keep to the road, and keep your blade where I can see it.', 'Three caravans this month. Three.'],
    nightBarks: ['Curfew\'s not law. Yet.', 'Two on the walls, one on each gate. It is not enough.', 'Go to bed, traveller.'],
  },
  maeca: {
    id: 'maeca', name: 'Maeca Barefoot', title: 'Last of the Ashford Garrison', role: 'Hunter',
    model: 'rogue', show: ['1H_Crossbow', 'Rogue_Cape'], tint: '#6a7a4a', idle: 'Idle_B',
    spot: { x: 33.5, z: 3.6, facing: -Math.PI / 2 },
    barks: ['They are not hunting. They are running.', 'Something has the whole wood on edge.', 'Mind the east road after dark.'],
    nightBarks: ['Hear that? No. Neither do I. That is what worries me.', 'One more, then I sleep.', 'The Pack is loud tonight.'],
  },
  chid: {
    id: 'chid', name: 'Chid', title: '"The Fool", of the Morning Light', role: 'Priest',
    model: 'mage', show: ['Spellbook'], tint: '#d8ccb0', idle: 'Idle',
    spot: { x: -20.6, z: -20.8, facing: Math.PI * 0.25 },
    barks: ['It used to work, you know. The shrine.', 'The light is patient. I am trying to be.', 'Morning comes. It always has.'],
    nightBarks: ['Even in the dark, the morning is on its way.', 'I leave a candle lit. Somebody might need it.', 'Can\'t sleep either?'],
  },
  rav: {
    id: 'rav', name: 'Dr. Rav McBreathless', title: 'Late of the Kerchiefs', role: 'Physician, of a sort',
    model: 'rogue_hooded', show: ['Knife'], tint: '#8a3a34', idle: 'Sit_Chair_Idle',
    spot: { x: -11.4, z: -7.6, facing: Math.PI / 2 },
    barks: ['I am a doctor. Mostly.', 'Red cloth is a hard habit to break.', 'Buy me a drink and I will tell you a lie worth hearing.'],
    nightBarks: ['Night surgery costs double. Night anything costs double.', 'The best stories come after the third cup.', 'Pull up a stool. Mind the blood.'],
  },
  harlan: {
    id: 'harlan', name: 'Harlan Coyle', title: 'Of the Coyle Company', role: 'Merchant',
    model: 'barbarian', show: [], tint: '#a0784a', idle: 'Idle',
    spot: { x: 10.4, z: -10.4, facing: -Math.PI / 2 },
    barks: ['Three days late. Jory is never late.', 'Salt, iron, cloth. Whatever you need, when the wagons come.', 'Somebody knows something.'],
    nightBarks: ['I keep the books by candlelight. It helps me not think.', 'Every wagon on that road is his, in the dark.', 'Can\'t sleep. Won\'t.'],
  },
  pell: {
    id: 'pell', name: 'Pell Varrow', title: 'Factor and Warehouseman', role: 'Factor',
    model: 'mage', show: ['1H_Wand'], tint: '#3e4a3a', idle: 'Idle',
    spot: { x: 20.2, z: 22.2, facing: Math.PI },
    barks: ['Everything has a price. Most things have two.', 'Terrible business, Coyle\'s caravan. Terrible.', 'My warehouse is closed to the public.'],
    nightBarks: ['Closed. Closed! Come back in daylight.', 'A man can\'t count in peace in this town.', 'Who\'s there?'],
  },
  wenna: {
    id: 'wenna', name: 'Old Wenna', title: 'Herbalist', role: 'Herbalist',
    model: 'mage', show: ['Mage_Hat', '2H_Staff'], tint: '#5e7a4a', scale: 0.9, idle: 'Idle',
    spot: { x: -23.6, z: 21.2, facing: Math.PI * 0.6 },
    barks: ['The animals were never like this. Never.', 'Bitterroot, bitterroot. Always need more.', 'The water tastes wrong this year.'],
    nightBarks: ['Moon\'s up. Good for picking. Bad for knees.', 'Mind the nettles in the dark.', 'Night air\'s full of things. Some of them are herbs.'],
  },
  tam: {
    id: 'tam', name: 'Tam', title: 'A farm boy from the Verge', role: 'Farm boy',
    model: 'rogue', show: [], tint: '#b8a070', scale: 0.76, idle: 'Sit_Floor_Idle',
    spot: { x: 2.6, z: 2.8, facing: Math.PI * 0.8 },
    barks: ['They drank from the stream and fell down.', 'Pa says stay in town.', 'Something is killing them. Nobody listens.'],
  },
  brannoc: {
    id: 'brannoc', name: 'Brannoc', title: 'Smith', role: 'Blacksmith',
    model: 'barbarian', show: ['1H_Axe'], tint: '#5a4a3a', idle: '1H_Melee_Attack_Chop',
    spot: { x: 11.6, z: 14.6, facing: -Math.PI / 2 },
    barks: ['Good steel does not come cheap. Neither do good pelts.', 'Mind the sparks.', 'Bring me hides, and I will make you something worth wearing.'],
    nightBarks: ['Forge is banked. Come back at first light.', 'My arm aches worse at night. Old iron does.', 'The fire keeps me company.'],
  },
  vonnra: {
    id: 'vonnra', name: 'Vonnra Hydrocheck', title: 'Far Seer, Keeper of the Toll', role: 'Toll-keeper',
    model: 'mage', show: ['Mage_Hat', 'Spellbook_open'], tint: '#5a4a7a', idle: 'Spellcasting',
    spot: { x: 28.4, z: -4.4, facing: -Math.PI / 2 },
    barks: ['The toll is the toll.', 'I see a great deal. I say very little. You will find that is the arrangement.', 'Payment, always.'],
    nightBarks: ['The toll does not sleep, and neither do I.', 'The dark is also a customer.', 'Payment, even now.'],
  },
  keegan: {
    id: 'keegan', name: 'Professor Keegan', title: 'Knight of the Argent Vigil (probationary)', role: 'Gatekeeper',
    model: 'knight', show: ['Knight_Helmet', '2H_Sword', 'Knight_Cape'], tint: '#dfe4ec', idle: '2H_Melee_Idle',
    spot: { x: 0, z: -33, facing: 0 },
    barks: ['None pass north. Not yet.', 'You are not ready for what is beyond there.', 'Probationary. It is a real title.'],
    nightBarks: ['Night watch. Probationary night watch.', 'Something moved out there. Probably.', 'Stand back from the gate, please.'],
  },
};

/** People met outside the Waystation. */
export const OUTSIDERS: Record<string, NpcDef> = {
  redcowl: {
    id: 'redcowl', name: 'Redcowl', title: 'Of the Kerchiefs', role: 'Kerchief chief',
    model: 'rogue_hooded', show: ['2H_Crossbow', 'Rogue_Cape'], tint: '#a02820', scale: 1.08, idle: 'Idle',
    spot: { x: 54, z: 90, facing: Math.PI }, barks: ['Keep walking.', 'Salvage is salvage.', 'Talk or bleed. Your choice.'],
  },
  jory: {
    id: 'jory', name: 'Jory Coyle', title: 'Harlan\'s nephew', role: 'Teamster',
    model: 'rogue', show: [], tint: '#7a6a8a', scale: 0.9, idle: 'Sit_Floor_Idle',
    spot: { x: 12.4, z: -13.6, facing: -Math.PI / 2 }, barks: ['I thought I would die in that cage.', 'Uncle keeps hugging me. It is a lot.'],
  },
};

/** Voices with no human face: shown with a mark instead of a portrait. */
export const SPEAKERS: Record<string, { name: string; title: string; glyph: string }> = {
  greymuzzle: { name: 'Greymuzzle', title: 'Alpha of the Thornhollow Pack', glyph: 'howl' },
  snib: { name: 'Snib', title: 'Foreman of the Dig (self-appointed)', glyph: 'relic' },
  survivor: { name: 'A lampling', title: 'Babbling at the edge of the pit', glyph: 'relic' },
  board: { name: 'Notice Board', title: 'The square, the Waystation', glyph: 'scroll' },
};

/** The Watch on the gates. They say things; they do not have conversations. */
export const GUARDS = [
  { x: -4.6, z: 34.6, facing: Math.PI, line: 'Dawn arrivals. We do not get many that live.' },
  { x: 4.6, z: 34.6, facing: Math.PI, line: 'Keep your weapon sheathed in town.' },
  { x: 36.4, z: -4.6, facing: -Math.PI / 2, line: 'East road. Mind the wolves.' },
];
