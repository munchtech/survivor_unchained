import type { Cond } from '@/world/logic';
import type { CharacterModel } from '@/render/assets';

/* The people of the Waystation nobody names.
 *
 * They come out of their doors in the morning, haggle at the stalls, draw
 * water, read the board, and go home when the light goes. What they mutter
 * as the survivor walks past is the town's opinion, and it changes with
 * what the survivor has done: the wolves, the caravan, Pell, a death. Lines
 * with a condition are news, and are said first while they are fresh; the
 * rest is the weather and the price of bread. */

export interface FolkLook { model: CharacterModel; show: string[]; tint: string; under?: string; scale?: number }

/** Plain clothes on the same five bodies the heroes use. */
export const FOLK_LOOKS: FolkLook[] = [
  { model: 'rogue', show: [], tint: '#7a5a3a', under: '#4a3a2a' },
  { model: 'rogue', show: [], tint: '#5a6a4a', under: '#3a4430' },
  { model: 'rogue', show: [], tint: '#8a4a4a', under: '#4a2e2a', scale: 0.94 },
  { model: 'rogue', show: [], tint: '#6a7a8a', under: '#3a4450' },
  { model: 'barbarian', show: [], tint: '#6a5040' },
  { model: 'barbarian', show: [], tint: '#4a5a6a' },
  { model: 'barbarian', show: [], tint: '#8a7a4a', scale: 1.04 },
  { model: 'mage', show: [], tint: '#8a7a5a', under: '#4a4030' },
  { model: 'mage', show: [], tint: '#6a3a3a', under: '#3a2020' },
  { model: 'mage', show: [], tint: '#4a5a48', under: '#2a3228', scale: 0.96 },
  { model: 'mage', show: [], tint: '#b8a888', under: '#6a5e4a' },
  { model: 'rogue_hooded', show: [], tint: '#4a4a3a', under: '#2a2a22' },
  { model: 'rogue_hooded', show: [], tint: '#6a5a4a', under: '#3a3028' },
  { model: 'rogue_hooded', show: [], tint: '#5a3a4a', under: '#32222a' },
];

export const CHILD_LOOKS: FolkLook[] = [
  { model: 'rogue', show: [], tint: '#9a6a4a', under: '#5a3e2a', scale: 0.62 },
  { model: 'rogue', show: [], tint: '#5a7a8a', under: '#344854', scale: 0.58 },
  { model: 'rogue', show: [], tint: '#a8844a', under: '#5e4a2a', scale: 0.6 },
  { model: 'barbarian', show: [], tint: '#8a8a5a', scale: 0.6 },
];

export const WATCH_LOOK: FolkLook = { model: 'knight', show: ['Knight_Helmet', '1H_Sword'], tint: '#8a98b0' };

export interface FolkLine {
  text: string;
  when?: Cond;
  /** Only after dark (true) or only by day (false). */
  night?: boolean;
  /** Only from someone who has died and come back (the survivor). */
  died?: boolean;
  /** Children say different things. */
  child?: boolean;
  /** The watch on its rounds. */
  watch?: boolean;
}

const BEASTS_OPEN: Cond = { all: [{ quest: { id: 'beasts', status: 'active' } }, { not: { fact: 'beasts.outcome', exists: true } }] };
const CARAVAN_OPEN: Cond = { all: [{ quest: { id: 'caravan', status: 'active' } }, { not: { fact: 'caravan.survivors', exists: true } }] };

export const FOLK_LINES: FolkLine[] = [
  // --- The weather and the price of bread.
  { text: 'Morning.', night: false },
  { text: 'Mind the cart.' },
  { text: 'Two coppers for a turnip. Two!', night: false },
  { text: 'Bread\'s up again. It\'s always up.', night: false },
  { text: 'Rain by evening, my knee says.', night: false },
  { text: 'You\'re not from the Waystation.' },
  { text: 'Another one off the road. They keep coming.' },
  { text: 'Don\'t stand in the well-queue unless you\'re drawing.', night: false },
  { text: 'Is that blood? Don\'t tell me.' },
  { text: 'Chid rang the bell twice this morning. Nobody knows why.', night: false },
  { text: 'The Flagon\'s ale is mostly water. The water\'s mostly ale.' },
  { text: 'Evening. Get indoors soon.', night: true },
  { text: 'Nothing good walks about after dark.', night: true },
  { text: 'Lamps are lit. Stay where they reach.', night: true },
  { text: 'Is that the watch? Oh. You.', night: true },
  // (Grown-ups talking.)
  { text: 'Shit weather, shit road, shit luck. Morning.', night: false },
  { text: 'Bloody wolves. Bloody Watch. Bloody bread.' },
  { text: 'Holloway couldn\'t find his own arse with a lantern and a map.' },
  { text: 'Pell counts his coin in bed. Alone, obviously.' },
  { text: 'If the wolves don\'t get you, Rook\'s stew will.' },
  { text: 'My husband went out to the Verge a month back. Some days I hope he stays out.' },
  { text: 'Sella took three coppers off me for a smile. Worth four.' },
  { text: 'Rook\'s upstairs rooms go by the hour now. Don\'t ask how I know.' },
  { text: 'Somebody\'s having a better night than me. Rook\'s walls are thin.', night: true },
  { text: 'Buried two this week. The ground\'s full and the priest\'s a boy.' },
  { text: 'They found the Aldo lad in the ditch. What was left of him.', night: true },
  { text: 'Keep walking, hero. I\'ve had my fill of heroes.' },
  { text: 'You smell like the dead. No offence. Everybody does, lately.' },

  // --- The Low Ford, the first thing anybody knows about you.
  { text: 'Came up the Low Ford at night? You\'re brave or daft.', when: { day: { lte: 2 } } },
  { text: 'They say the Ford-Warden\'s down. Was that you?', when: { day: { lte: 3 } } },
  { text: 'My gran swore the Warden was a story to keep children off the ford.', when: { day: { lte: 3 } } },

  // --- The Beast Problem.
  { text: 'Wolves took the Oswin goats. In daylight!', when: BEASTS_OPEN },
  { text: 'Holloway\'s paying five a pelt, if you\'ve the stomach.', when: BEASTS_OPEN },
  { text: 'Wolves don\'t behave like that. Not healthy ones.', when: BEASTS_OPEN },
  { text: 'Wolves at the gate last night. At the gate!', when: { fact: 'wolves.at_gate', eq: true } },
  { text: 'Tam\'s farm was hit. Poor lad\'s sleeping in the Watch-house.', when: { fact: 'tam.farm', eq: 'raided' } },
  { text: 'You\'re the one who cleared the wolves. My boy can walk to the mill again.', when: { fact: 'beasts.outcome', eq: 'slaughtered' } },
  { text: 'Quiet out east now. Too quiet, Maeca says.', when: { fact: 'beasts.outcome', eq: 'slaughtered' } },
  { text: 'They say wolves walk beside you out there. I\'d not believe it but for Maeca\'s face.', when: { fact: 'beasts.outcome', eq: 'allied' } },
  { text: 'Wolf-friend. Keep them out of my hen-house, that\'s all I ask.', when: { fact: 'beasts.outcome', eq: 'allied' } },
  { text: 'Tam says the stream runs clear again. Tam says a lot, but still.', when: { fact: 'beasts.outcome', eq: 'cured' } },
  { text: 'Wenna\'s been smiling. Wenna. Smiling.', when: { fact: 'beasts.outcome', eq: 'cured' } },
  { text: 'Pell\'s diggers moved their pipe. Pell, doing a kindness. Hm.', when: { fact: 'beasts.outcome', eq: 'exploited' } },
  { text: 'Heard somebody sold the Dig to Pell. Heard it was you.', when: { history: 'sold_dig' } },
  { text: 'You lied to Holloway about the wolves. Everybody knows. He does too.', when: { fact: 'holloway.lied_to', eq: true } },

  // --- The Missing Caravan.
  { text: 'Harlan\'s not slept since the wagons went.', when: CARAVAN_OPEN },
  { text: 'The Coyle wagons had the Aldo boy\'s wedding cloth on them.', when: CARAVAN_OPEN },
  { text: 'Kerchiefs, they say. Red rags and no mercy.', when: CARAVAN_OPEN },
  { text: 'Jory Coyle\'s home! Harlan wept in the street, I saw it.', when: { fact: 'caravan.survivors', eq: 'rescued' } },
  { text: 'Those poor teamsters. Harlan hasn\'t opened the shutters.', when: { fact: 'caravan.survivors', eq: 'dead' } },
  { text: 'Pell Varrow, selling his own neighbours. I bought eggs from that man.', when: { fact: 'caravan.pell', eq: 'exposed' } },
  { text: 'Pell\'s been generous lately. With you, mostly.', when: { fact: 'caravan.pell', eq: 'ally' } },
  { text: 'Kerchiefs hit the Aldo farm again. Prices\'ll climb, you watch.', when: { fact: 'kerchief.raids', gte: 1 } },
  { text: 'Salt\'s doubled. The Kerchiefs are bleeding the road dry.', when: { fact: 'kerchief.raids', gte: 2 } },
  { text: 'The Roost burned, they say. You could see the smoke from the wall.', when: { history: 'burned_roost' } },
  { text: 'Redcowl dead. I\'ll believe it when I see the hat.', when: { history: 'killed_redcowl' } },
  { text: 'You made a deal with Redcowl? With Redcowl?', when: { history: 'bargained_redcowl' } },
  { text: 'That\'s Coyle cloth on your back, isn\'t it.', when: { fact: 'caravan.cargo', eq: 'kept' } },
  { text: 'Harlan says you brought every crate home. Every one.', when: { fact: 'caravan.cargo', eq: 'returned' } },
  { text: 'Wanted, they said at the Watch. Wanted! You\'ve a nerve walking here.', when: { fact: 'player.wanted', eq: true } },

  // --- Stranger things.
  { text: 'Did you feel the ground go, last night? Like something rolling over.', when: { fact: 'tremor.felt', eq: true } },
  { text: 'The shrine lamp\'s lit. First time since I was a girl.', when: { fact: 'shrine.lit', eq: true } },
  { text: 'Vonnra read your fortune? She never reads for free.', when: { history: 'fortune_read' } },
  { text: 'Chid says you died. You look well on it.', died: true },
  { text: 'They carried you in past my door. I thought that was you done.', died: true },

  // --- Children.
  { text: 'Are you a knight?', child: true },
  { text: 'Tag! You\'re it!', child: true },
  { text: 'Mum says not to talk to you.', child: true },
  { text: 'Show us your sword! Go on!', child: true },
  { text: 'Did you kill a wolf? A big one?', child: true, when: { any: [{ quest: { id: 'beasts', status: 'active' } }, { quest: { id: 'beasts', status: 'resolved' } }] } },
  { text: 'Is it true you\'ve got a wolf for a friend?', child: true, when: { fact: 'beasts.outcome', eq: 'allied' } },

  // --- The watch on its rounds.
  { text: 'All quiet. Keep it that way.', watch: true },
  { text: 'Gates are shut till dawn.', watch: true },
  { text: 'Walk on, traveller.', watch: true },
  { text: 'Piss off home. It\'s past curfew.', watch: true },
  { text: 'Keep that blade sheathed or I\'ll sheathe it for you.', watch: true },
  { text: 'Captain\'s doubled the gate. Wolves.', watch: true, when: { fact: 'wolves.at_gate', eq: true } },
];
