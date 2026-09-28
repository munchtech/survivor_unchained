import type { Conversation, DChoice } from '@/world/dialogue';
import type { Cond, Effect } from '@/world/logic';
import type { Axis } from '@/world/state';
import { CARAVAN_SETTLE } from '../rules';

/* The Waystation, in its own words.
 *
 * Each conversation starts somewhere different depending on who you are to
 * the speaker and what they have heard. Choices a background opens carry
 * its badge; choices you cannot take yet are shown greyed with the reason.
 * Every quest hook is an Effect, so the journal, the world's memory and the
 * people who hear about it later all agree on what happened. */

const bye = (text = 'Goodbye.'): DChoice => ({ text, end: true });
const back = (to = 'hub'): DChoice => ({ text: 'Something else...', goto: to });
const notMet = (id: string): Cond => ({ not: { met: id } });
const beastsOpen: Cond = { not: { fact: 'beasts.outcome', exists: true } };
type Feel = Partial<Record<Axis, number>>;
/** Something the world will remember, who takes it personally, and how. */
export const hist = (id: string, text: string, tags: string[], spread: number, sentiment?: Feel, reactions?: Record<string, Feel>): Effect =>
  ({ history: { id, text, tags, spread, sentiment, reactions } });
/** The same deed, done in front of people: they know at once, the rest hear later. */
export const seen = (e: Effect, ...who: string[]): Effect => ({ ...(e as Extract<Effect, { history: unknown }>), witnesses: who });

/* ================================================================ Rook == */

const rookHub: DChoice[] = [
  { text: 'I need a bed.', action: 'rest' },
  { text: 'Can you keep some things for me?', action: 'stash' },
  { text: 'What is the talk in town?', goto: 'rumours' },
  { text: 'Tell me about the Waystation.', goto: 'town' },
  { text: 'That lamp over the door — it is from the Chapel of the Morning Light.', when: { bg: 'devout' }, badge: 'Faith', once: 'lamp', goto: 'lamp' },
  { text: 'There is a grave in the garden behind the walls. A captain, with his lamp.', when: { knows: 'lore.firstlamp' }, badge: 'Found', once: 'firstlamp', goto: 'firstlamp' },
  bye('Another time.'),
];

export const ROOK: Conversation = {
  npc: 'rook',
  entry: [
    { when: notMet('rook'), node: 'first' },
    { when: { fact: 'player.wanted', eq: true }, node: 'wanted' },
    { node: 'hub' },
  ],
  marker: [{ when: notMet('rook'), mark: '!' }],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { history: 'ford_warden_slain' }, text: 'Well. The one who walked up from the Low Ford at dawn. Chid came in babbling about blue lights going out at the crossing, and here you are, still bleeding a bit. I\'m Rook. This is the Last Lamp. Sit down before you fall down.' },
        { text: 'Another one off the Low Ford road. I\'m Rook, and this is the Last Lamp: bed, bread, a bath if you ask nicely, and I keep things safe for those who pay.' },
      ],
      choices: rookHub,
    },
    hub: {
      id: 'hub',
      text: [
        { when: { time: 'night' }, text: 'Late, {name}. The stew is cold but the beds are not.' },
        { when: { rel: { npc: 'rook', axis: 'affection', gte: 30 } }, text: 'There you are. I kept a bowl back for you.' },
        { text: 'Back again, {name}. What will it be?' },
      ],
      choices: rookHub,
    },
    rumours: {
      id: 'rumours',
      text: [
        { when: { fact: 'beasts.outcome', eq: 'cured' }, text: 'Wenna says the stream is running clean. The wolves have gone quiet, and Holloway is sulking because he cannot pay anyone for anything. Harlan is still asking after his boy.' },
        { when: { fact: 'beasts.outcome', eq: 'slaughtered' }, text: 'No wolves on the road now. None at all. Brannoc says he has never seen so many pelts, and Maeca has not been in since. Make of that what you will.' },
        { text: 'Wolves, mostly. Holloway is paying for pelts, Maeca says the wolves are sick, Harlan says they ate his caravan, and the Coyle boy is still missing. And a toll clerk has been drinking at the Crooked Flagon like he came into money. Pick a story.' },
      ],
      effects: [{ quest: { id: 'beasts', entry: 'rumour' } }, { quest: { id: 'caravan', entry: 'harlan_plea' } }],
      choices: [
        { text: 'A toll clerk with money?', goto: 'clerk' },
        back(),
      ],
    },
    clerk: {
      id: 'clerk',
      text: 'Clerks do not buy rounds. This one bought three, the night Coyle\'s wagons went missing, and kept telling the room he had "done somebody a favour". Rav was there. Rav is always there.',
      choices: [back()],
    },
    town: {
      id: 'town',
      text: 'Three roads meet here. South to the Low Ford, east to the Old Road and the Verge, and north... north is shut, and a boy in shiny armour will tell you why at length. Vonnra takes the toll, Holloway keeps the peace, Brannoc keeps the steel, Chid keeps the shrine, badly. Harlan and Pell keep each other honest. Mostly. And Sella keeps the blue room upstairs, and my third of it, and her mouth shut when it matters.',
      choices: [back()],
    },
    firstlamp: {
      id: 'firstlamp',
      text: 'You found old Ashe. Captain of the first Watch, when it was forty lamps and not four. This inn is named for his: the Last Lamp, because it was the last one lit on the night they closed the north road. We light the hearth from it every winter. Nobody goes out there now. ...Thank you for not digging him up.',
      effects: [{ rel: { npc: 'rook', trust: 10, affection: 10 } }, { learn: 'lore.ashe' }],
      choices: [back()],
    },
    lamp: {
      id: 'lamp',
      text: 'It is. My mother carried it up from the chapel when the Order left, and it has not gone out since. You carry one too, I see. Talk to Chid. He needs someone who knows what the light is for.',
      effects: [{ rel: { npc: 'rook', trust: 10, affection: 10 } }],
      choices: [back()],
    },
    wanted: {
      id: 'wanted',
      text: 'Holloway\'s men were in asking after you. I told them you owed me money, which is true. Do not make trouble under my roof.',
      choices: rookHub,
    },
  },
};

/* ============================================================ Holloway == */

const hollowayHub: DChoice[] = [
  { text: 'Tell me about the wolves.', goto: 'wolves' },
  { text: 'I have come about the bounty.', when: { any: [{ hasItem: 'wolf_pelt' }, { hasItem: 'greymuzzle_fang' }] }, locked: 'Bring pelts or the alpha\'s fang', goto: 'bounty' },
  { text: 'Harlan Coyle\'s caravan. What do you know?', goto: 'caravan' },
  { text: 'The wolves are sick, not bold.', when: { any: [{ knows: 'beastlore' }, { knows: 'clue.sick_wolf' }] }, badge: 'Beastlore', once: 'sick', goto: 'sick' },
  { text: 'The wolves are poisoned. The Dig is dumping ember slurry into the stream.', when: { knows: 'root_cause' }, once: 'cause', goto: 'cause' },
  { text: 'The beasts are dealt with. You can stop worrying.', show: { all: [beastsOpen, { not: { fact: 'beasts.told_holloway', exists: true } }] }, when: { hasItem: 'wolf_pelt', qty: 3 }, locked: 'You would need something to show for it', goto: 'lie' },
  { text: 'Pell Varrow paid the Kerchiefs to take Coyle\'s caravan. Here is his ledger.', when: { hasItem: 'pell_ledger' }, once: 'expose', goto: 'expose' },
  bye(),
];

export const HOLLOWAY: Conversation = {
  npc: 'holloway',
  entry: [
    { when: { all: [{ fact: 'player.wanted', eq: true }, { not: { fact: 'player.fined', eq: true } }] }, node: 'arrest' },
    { when: { all: [{ fact: 'holloway.lied_to', eq: true }, { not: { fact: 'holloway.lie_settled', exists: true } }] }, node: 'liar' },
    { when: notMet('holloway'), node: 'first' },
    { node: 'hub' },
  ],
  marker: [
    { when: notMet('holloway'), mark: '!' },
    { when: { hasItem: 'greymuzzle_fang' }, mark: '?' },
    { when: { hasItem: 'pell_ledger' }, mark: '?' },
  ],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { hasTag: 'kerchief_colors' }, text: 'You came up the Low Ford road wearing Kerchief red. Either you are one of them, or you are a fool. Take that rag off in my town, or I will take it off you. Holloway. Captain of what is left of the Watch.' },
        { when: { history: 'ford_warden_slain' }, text: 'You are the one who put the Ford-Warden down. The Watch lit those lamps once. I would thank you, but thanks do not pay my men. Holloway. Captain of what is left of the Watch.' },
        { text: 'You came up the Low Ford road. At night. Either you are very good or very lucky, and I do not need either kind of trouble in my town. Holloway, Captain of the Watch.' },
      ],
      effects: [{ quest: { id: 'beasts', status: 'active', entry: 'holloway_bounty' } }],
      choices: hollowayHub,
    },
    hub: {
      id: 'hub',
      text: [
        { when: { fact: 'beasts.outcome', eq: 'cured' }, text: 'The water is clean and the wolves are back in the deep wood. I was wrong about them. Do not tell anyone I said so.' },
        { when: { fact: 'wolves.at_gate', eq: true }, text: 'You heard. Aldo. He had a wife in Ashford and a bad knee, and they took him at my gate. The bounty is still five gold a pelt. What do you want?' },
        { when: { rel: { npc: 'holloway', axis: 'trust', lte: -30 } }, text: 'You. Keep your hands where I can see them.' },
        { when: { fact: 'beasts.outcome', eq: 'slaughtered' }, text: 'The road is quiet. I paid for every pelt of it. Do you know how quiet? Maeca has stopped coming in to argue with me.' },
        { when: { all: [{ fact: 'beasts.bounty_claimed', eq: true }, { not: { fact: 'beasts.outcome', exists: true } }] }, text: 'I pay for a pelt and two more wolves come down the road. I am starting to think Maeca is right, and I hate that. What is it?' },
        { text: 'Captain Holloway. What is it?' },
      ],
      choices: hollowayHub,
    },
    wolves: {
      id: 'wolves',
      text: 'They are bolder. Two nights ago they came right up to the east gate. Five gold a pelt, fifty for the grey one they call Greymuzzle. Bring me proof and I pay; bring me excuses and I do not.',
      effects: [{ quest: { id: 'beasts', status: 'active', entry: 'holloway_bounty' } }],
      choices: hollowayHub,
    },
    bounty: {
      id: 'bounty',
      text: [
        { when: { hasItem: 'greymuzzle_fang' }, text: 'That is his fang. That is the old devil himself. Here — fifty, as promised, and my thanks with it.' },
        { text: 'Pelts. Good. Let me count them.' },
      ],
      choices: [
        { text: 'Hand over the fang.', when: { hasItem: 'greymuzzle_fang' }, effects: [
          { take: 'greymuzzle_fang' }, { gold: 50 }, { set: { 'beasts.bounty_claimed': true, 'greymuzzle': 'dead' } },
          { quest: { id: 'beasts', entry: 'bounty_claimed' } }, { rel: { npc: 'holloway', trust: 15, respect: 15 } },
          seen(hist('greymuzzle_fang_sold', 'turned in Greymuzzle\'s fang for the bounty', ['beasts', 'bounty'], 2, undefined, { maeca: { affection: -40, respect: -20 }, holloway: { respect: 10 } }), 'holloway'),
        ], goto: 'hub' },
        { text: 'Hand over the pelts.', when: { hasItem: 'wolf_pelt' }, action: 'bounty' },
        back(),
      ],
    },
    liar: {
      id: 'liar',
      text: 'Dealt with. That is what you said. I paid you thirty gold of the Watch\'s money for "dealt with", and this morning I had a drover bleeding on my gate. So. Tell me why I should not put you in the cells.',
      choices: [
        { text: 'Pay back the thirty. [30 gold]', when: { gold: { gte: 30 } }, locked: 'You do not have it', effects: [
          { gold: -30 }, { set: { 'holloway.lie_settled': 'repaid' } }, { rel: { npc: 'holloway', trust: 15 } },
        ], goto: 'repaid' },
        { text: 'They were dealt with. These are new ones. The wood is sick; they keep coming.', when: { any: [{ knows: 'clue.sick_wolf' }, { knows: 'root_cause' }] }, badge: 'Clue', effects: [
          { set: { 'holloway.lie_settled': 'argued' } }, { rel: { npc: 'holloway', respect: 5 } },
        ], goto: 'argued' },
        { text: 'You got your pelts. Take it up with the wolves.', effects: [
          { set: { 'holloway.lie_settled': 'defied' } }, { rel: { npc: 'holloway', trust: -15, fear: 5 } },
        ], goto: 'defied' },
      ],
    },
    repaid: {
      id: 'repaid',
      text: 'Hm. A liar who pays his debts. That is a rarer beast than a wolf. I will not forget it — either half of it.',
      choices: hollowayHub,
    },
    argued: {
      id: 'argued',
      text: '...New ones. From a sick wood. Then the pelts buy me nothing, and you are telling me the bounty is a bucket against a flood. Find me the hole in the bucket, and we will call it even.',
      choices: hollowayHub,
    },
    defied: {
      id: 'defied',
      text: 'Out of my sight. And if I see you near my gate with a blade out, you will find out how the cells feel on a cold night.',
      choices: [bye('Go.')],
    },
    caravan: {
      id: 'caravan',
      text: 'Coyle\'s wagons never reached my gate. The Old Road was open all day; I had men on it from dawn to dusk. Whatever happened to them happened off the road, and whoever told them otherwise lied.',
      effects: [{ quest: { id: 'caravan', status: 'active', entry: 'guard_says' } }],
      choices: hollowayHub,
    },
    sick: {
      id: 'sick',
      text: 'Sick or bold, they bite the same. ...But. If you are right, and you can show me what is sickening them, I would rather fix the cause than pay for pelts until I am old.',
      effects: [{ rel: { npc: 'holloway', respect: 10 } }, { npcFlag: { npc: 'holloway', key: 'open_to_cure', value: true } }],
      choices: hollowayHub,
    },
    cause: {
      id: 'cause',
      text: 'The lamplings. Of course it is the lamplings. Deal with the pump, and I will stop paying for pelts. I will not stop watching the road.',
      effects: [{ rel: { npc: 'holloway', trust: 15, respect: 10 } }],
      choices: hollowayHub,
    },
    lie: {
      id: 'lie',
      text: 'Dealt with. Hm. The road has been quiet today, I will grant you. Thirty gold for the trouble, and if I find wolves at my gate tomorrow night, we will talk again.',
      effects: [
        { gold: 30 }, { set: { 'beasts.told_holloway': true } }, { quest: { id: 'beasts', entry: 'told_holloway' } },
        hist('lied_to_holloway', 'told Holloway the wolves were dealt with, and took his money', ['lie', 'beasts'], 1, { trust: -10 }, { holloway: { trust: -40 }, maeca: { respect: -10 } }),
      ],
      choices: [bye()],
    },
    expose: {
      id: 'expose',
      text: 'Payments to "R." — Redcowl. And to my toll clerk. On the night. Pell Varrow, you greedy, careful little man. My men will have him in irons before dark. The Watch owes you, {name}. I do not say that lightly, because I do not have much to pay you with.',
      effects: [
        { take: 'pell_ledger' }, { set: { 'caravan.pell': 'exposed' } }, { quest: { id: 'caravan', entry: 'pell_exposed' } },
        { gold: 40 }, { rel: { npc: 'holloway', trust: 30, respect: 25 } },
        seen(hist('exposed_pell', 'exposed Pell Varrow for paying the Kerchiefs to take the Coyle caravan', ['justice', 'caravan'], 2, { trust: 10, respect: 10 }, { harlan: { trust: 40, affection: 30 }, pell: { fear: 30, trust: -80 } }), 'holloway', 'harlan'),
      ],
      choices: [bye()],
    },
    arrest: {
      id: 'arrest',
      text: 'You kept the Coyle cargo. Everyone in the Waystation knows it, and so do I. A hundred gold to the Watch and we will say no more about it. Or you can leave my town.',
      choices: [
        { text: 'Pay the hundred.', when: { gold: { gte: 100 } }, locked: 'You do not have a hundred gold', effects: [{ gold: -100 }, { set: { 'player.fined': true } }, { rel: { npc: 'holloway', trust: 10 } }], goto: 'hub' },
        { text: 'You should be asking who paid the Kerchiefs.', when: { hasItem: 'pell_ledger' }, badge: 'Evidence', goto: 'expose' },
        { text: 'I will keep out of your way.', effects: [{ rel: { npc: 'holloway', trust: -10 } }], end: true },
      ],
    },
  },
};

/* =============================================================== Maeca == */

const maecaHub: DChoice[] = [
  { text: 'What is driving them out?', goto: 'driving' },
  { text: 'Their tracks are wrong. They are dragging their back legs.', when: { knows: 'beastlore' }, badge: 'Beastlore', once: 'tracks', goto: 'tracks' },
  { text: 'It is the stream. Ember slurry from the Dig.', when: { knows: 'root_cause' }, once: 'truth', goto: 'truth' },
  { text: 'Can the wolves be spoken to?', when: { any: [{ knows: 'beastlore' }, { knows: 'root_cause' }] }, goto: 'speak' },
  { text: 'Where can I find you?', goto: 'where' },
  bye(),
];

export const MAECA: Conversation = {
  npc: 'maeca',
  entry: [
    { when: { fact: 'beasts.outcome', eq: 'slaughtered' }, node: 'cold' },
    { when: { npcKnows: { npc: 'maeca', event: 'greymuzzle_fang_sold' } }, node: 'cold' },
    { when: notMet('maeca'), node: 'first' },
    { when: { fact: 'beasts.outcome', eq: 'cured' }, node: 'thanks' },
    { node: 'hub' },
  ],
  marker: [{ when: notMet('maeca'), mark: '!' }, { when: { all: [{ knows: 'root_cause' }, { not: { npcFlag: { npc: 'maeca', key: 'once:truth', eq: true } } }] }, mark: '?' }],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { bg: 'hunter' }, text: 'You walk like someone who has tracked something to its den. Hunter? Then you have seen it too, out there. They are not hunting. They are running. Maeca. Barefoot, before you ask; the Ashford Garrison never had the boots to spare.' },
        { when: { hasTag: 'wolf_pelts' }, text: 'That cloak is made of wolves. I can smell it from here, and so can they. Maeca Barefoot. What do you want?' },
        { text: 'Another sword for Holloway\'s bounty? The wolves are not the problem. They are what the problem looks like from the road. Maeca Barefoot, of the Ashford Garrison, what is left of it.' },
      ],
      effects: [{ quest: { id: 'beasts', status: 'active', entry: 'maeca_theory' } }],
      choices: maecaHub,
    },
    hub: {
      id: 'hub',
      text: [
        { when: { rel: { npc: 'maeca', axis: 'respect', gte: 30 } }, text: 'Hunter. What have you found?' },
        { text: 'You again. What is it?' },
      ],
      choices: maecaHub,
    },
    driving: {
      id: 'driving',
      text: 'Something in the deep wood. The deer are thin, the pack is thinner, and the old alpha, Greymuzzle, has brought them closer to people than he ever would have. Find out why, and you will have done more than a hundred pelts ever could. Ask Tam, by the well. He has seen something, and nobody listens to children.',
      effects: [{ quest: { id: 'beasts', entry: 'maeca_theory' } }],
      choices: maecaHub,
    },
    tracks: {
      id: 'tracks',
      text: 'You saw that? Nobody sees that. Dragging, yes — weak in the hindquarters, the way a dog gets when it has eaten something it should not. So. Not bold. Sick.',
      effects: [{ rel: { npc: 'maeca', respect: 20, trust: 10 } }, { learn: 'clue.sick_wolf', text: 'The wolves are sick, not bold.' }, { quest: { id: 'beasts', entry: 'clue.sick_wolf' } }],
      choices: maecaHub,
    },
    truth: {
      id: 'truth',
      text: 'Grimtunnel\'s diggers. I should have known; every bad thing under Thornhollow has a lamp in its hand. If you can stop that pump, the pack will come back to itself. It may take days. It will happen.',
      effects: [{ rel: { npc: 'maeca', respect: 20, trust: 15 } }],
      choices: maecaHub,
    },
    speak: {
      id: 'speak',
      text: 'Spoken to? Not with words. But Greymuzzle is old and he is not stupid. Go into the Hollow with no wolf blood on your blade — none, not this whole trip — and do not run. He will decide what you are. If he decides wrong, well. Run then.',
      effects: [{ learn: 'hint.greymuzzle' }],
      choices: maecaHub,
    },
    where: {
      id: 'where',
      text: 'The Hunters\' Blind, out past the wreck on the Old Road, most days. I watch the Hollow from there. You will know it by the smoke; I am the only one fool enough to light a fire in that wood.',
      choices: maecaHub,
    },
    thanks: {
      id: 'thanks',
      text: 'The Hollow is quiet. The pack is eating again — deer, not travellers. I have been a hunter all my life, {name}, and I have never once saved anything. Thank you.',
      effects: [{ rel: { npc: 'maeca', affection: 10 }, quiet: true }],
      choices: [bye('Look after them.')],
    },
    cold: {
      id: 'cold',
      text: 'You emptied the Hollow. I heard. I hope Holloway\'s gold keeps you warm.',
      choices: [bye('...')],
    },
  },
};

/* =============================================================== Wenna == */

const wennaHub: DChoice[] = [
  { text: 'Holloway says the wolves are getting bolder.', goto: 'animals' },
  { text: 'Tam says the wolves drank from the stream and fell down.', when: { all: [{ knows: 'hint.stream' }, { not: { knows: 'clue.analysis' } }] }, once: 'tam', goto: 'tamsays' },
  { text: 'I brought you water from the stream.', show: { not: { knows: 'clue.analysis' } }, when: { hasItem: 'stream_sample' }, locked: 'Bring her a sample from the Thornhollow stream', goto: 'analyse' },
  { text: 'Let me help you test it.', when: { all: [{ knows: 'arcana' }, { hasItem: 'stream_sample' }] }, badge: 'Arcana', goto: 'analyse_arcana' },
  { text: 'I brought bitterroot.', when: { hasItem: 'bitterroot', qty: 3 }, locked: 'She wants three bitterroot', effects: [{ take: 'bitterroot', qty: 3 }, { gold: 15 }, { rel: { npc: 'wenna', affection: 12, trust: 6 } }], goto: 'root' },
  { text: 'That beaked mask on the wall...', when: { rel: { npc: 'wenna', axis: 'affection', gte: 20 } }, locked: 'She does not know you well enough', once: 'mask', goto: 'mask' },
  { text: 'What do you sell?', action: 'trade' },
  bye(),
];

export const WENNA: Conversation = {
  npc: 'wenna',
  entry: [{ when: notMet('wenna'), node: 'first' }, { node: 'hub' }],
  marker: [{ when: notMet('wenna'), mark: '!' }, { when: { hasItem: 'stream_sample' }, mark: '?' }],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { bg: 'scholar' }, text: 'A Cloister lens, and a Cloister squint. Scholar? Then do not touch anything, you will only want to catalogue it. I am Wenna. What do you want?' },
        { text: 'Do not touch that. Or that. Or — yes, that too. I am Wenna. I make things that stop you dying, mostly. What do you want?' },
      ],
      choices: wennaHub,
    },
    hub: { id: 'hub', text: 'Well? I have roots to boil.', choices: wennaHub },
    animals: {
      id: 'animals',
      text: 'The animals were never like this. Never. And the water tastes wrong this year — metal and smoke. Bring me some from the Thornhollow stream, above the blight if you can, below it if you must, and I will tell you what is in it.',
      effects: [{ quest: { id: 'beasts', status: 'active', entry: 'wenna_request' } }],
      choices: wennaHub,
    },
    tamsays: {
      id: 'tamsays',
      text: 'Tam. Of course Tam saw it; nobody looks at the ground like a boy with nothing to do. Drank and fell down. Not fought, not starved: drank. ...Bring me that water. A bottle of it, from where he saw them. I have been smelling metal in the well for a month and telling myself I was old.',
      effects: [{ quest: { id: 'beasts', status: 'active', entry: 'wenna_request' } }, { rel: { npc: 'wenna', respect: 10 } }, { rel: { npc: 'tam', trust: 5 }, quiet: true }],
      choices: wennaHub,
    },
    analyse: {
      id: 'analyse',
      text: [
        { when: { hasItem: 'slurry_sample' }, text: 'Green water, and — what is this? From a pipe? Ember. Ember slurry: the dust of the stones, cooked and watered down. It rots the belly of anything that drinks it. And nobody spills this much by accident. Someone upstream is getting rid of it.' },
        { text: 'Hm. Hmm. Green, and warm, and it smells like a chapel lamp. Ember slurry: the dust of the stones, cooked and watered. It rots the belly of anything that drinks it. Nobody spills this by accident, {name}. Someone upstream is getting rid of it.' },
      ],
      effects: [
        { take: 'stream_sample' }, { learn: 'clue.analysis', text: 'The stream is poisoned with ember slurry.' }, { quest: { id: 'beasts', entry: 'clue.analysis' } },
        { if: { any: [{ knows: 'clue.pipe' }, { hasItem: 'slurry_sample' }, { knows: 'clue.lampling_tracks' }] }, then: [{ learn: 'root_cause', text: 'The Dig is poisoning the stream.' }, { quest: { id: 'beasts', entry: 'root_cause' } }] },
        { rel: { npc: 'wenna', trust: 20, respect: 10 } }, { give: 'antidote', qty: 2 },
      ],
      choices: [{ text: 'Who would do that?', goto: 'who' }, back()],
    },
    analyse_arcana: {
      id: 'analyse_arcana',
      text: 'You know your salts. Yes — precipitate it, there, and... ember. Slurry, and fresh. Look at the grain: it has been through a pump. Nobody pumps ember but the lamplings, and the lamplings answer to Grimtunnel.',
      effects: [
        { take: 'stream_sample' }, { learn: ['clue.analysis', 'root_cause'], text: 'The Dig is poisoning the stream.' },
        { quest: { id: 'beasts', entry: 'clue.analysis' } }, { quest: { id: 'beasts', entry: 'root_cause' } },
        { rel: { npc: 'wenna', trust: 25, respect: 25 } }, { give: 'antidote', qty: 2 },
      ],
      choices: [back()],
    },
    who: {
      id: 'who',
      text: 'Who digs? Who burns ember by the barrow-load? The lamplings. Find where it goes into the water, and you will find their pipe. Take an antidote or two, and do not drink from anything out there.',
      choices: [back()],
    },
    root: { id: 'root', text: 'Good. Fat ones, too. Here — and come back with more, I am always short.', choices: [back()] },
    mask: {
      id: 'mask',
      text: 'My blightward. I made it for the fever year. Stuff the beak with bitterroot and you can walk through air that would drop a horse. Take it. I am too old to go where it is needed.',
      effects: [{ give: 'blightward_mask' }, { rel: { npc: 'wenna', affection: 10 } }],
      choices: [back()],
    },
  },
};

/* ================================================================= Tam == */

export const TAM: Conversation = {
  npc: 'tam',
  entry: [
    { when: { fact: 'beasts.outcome', eq: 'cured' }, node: 'happy' },
    { when: notMet('tam'), node: 'first' },
    { node: 'again' },
  ],
  marker: [{ when: notMet('tam'), mark: '!' }],
  nodes: {
    first: {
      id: 'first',
      text: 'They drank from the stream and they fell down. Three of them. Nobody listens to me. ...You will listen?',
      choices: [
        { text: 'I am listening.', goto: 'story' },
        { text: 'Where is your farm?', goto: 'farm' },
        bye('Stay by the well.'),
      ],
    },
    story: {
      id: 'story',
      text: 'Down by the green water, past the old fence where Pa lost the goat. Three wolves. They drank and lay down and did not get up, and their eyes went all milky. The water smells like the chapel lamps. Pa says stay in town. I stayed in town.',
      effects: [{ quest: { id: 'beasts', status: 'active', entry: 'tam_plea' } }, { learn: 'hint.stream' }, { rel: { npc: 'tam', trust: 20, affection: 10 } }],
      choices: [
        { text: 'You did right to tell someone.', effects: [{ rel: { npc: 'tam', affection: 15 } }], goto: 'again' },
        { text: 'Where is your farm?', goto: 'farm' },
      ],
    },
    farm: {
      id: 'farm',
      text: 'Out past the Old Road, where the wood starts. Pa will not leave it. He says wolves are wolves. But these ones are not right.',
      effects: [{ npcFlag: { npc: 'tam', key: 'farm_told', value: true } }],
      choices: [bye('Stay by the well, Tam.')],
    },
    again: {
      id: 'again',
      text: [
        { when: { fact: 'beasts.outcome', eq: 'ignored' }, text: 'They came right up to the gate. I heard them. Pa says we are not going home. Not ever, maybe.' },
        { when: { fact: 'tam.farm', eq: 'raided' }, text: 'Pa is at Wenna\'s. She says he will keep the arm. The Watch says it was wolves. I told them it was wolves, weeks ago. Nobody listens.' },
        { when: { fact: 'beasts.severity', gte: 4 }, text: 'Pa did not come in last night. He always comes in.' },
        { text: 'Did you find out what is wrong with them?' },
      ],
      choices: [
        { text: 'Tell me again what you saw.', goto: 'story' },
        bye('Not yet.'),
      ],
    },
    happy: {
      id: 'happy',
      text: 'The water is clear! Pa says I can come home! Pa says you did it. Did you do it?',
      choices: [{ text: 'I did.', effects: [{ rel: { npc: 'tam', affection: 20 } }], end: true }, { text: 'Lots of people did.', effects: [{ rel: { npc: 'tam', respect: 20 } }], end: true }],
    },
  },
};

/* ============================================================= Brannoc == */

const brannocHub: DChoice[] = [
  { text: 'Show me what you have made.', action: 'trade' },
  { text: 'I have wolf pelts to sell.', when: { hasItem: 'wolf_pelt' }, locked: 'You have no pelts', action: 'sellpelts' },
  { text: 'Make me a cloak from five wolf pelts.', when: { all: [{ hasItem: 'wolf_pelt', qty: 5 }, { gold: { gte: 30 } }] }, locked: 'Five pelts and thirty gold', effects: [{ take: 'wolf_pelt', qty: 5 }, { gold: -30 }, { give: 'wolfhide_cloak' }], goto: 'cloak' },
  { text: 'Can you improve my weapon?', action: 'reforge' },
  bye(),
];

export const BRANNOC: Conversation = {
  npc: 'brannoc',
  entry: [{ when: notMet('brannoc'), node: 'first' }, { node: 'hub' }],
  marker: [{ when: notMet('brannoc'), mark: '!' }],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { bg: 'hunter' }, text: 'A hunter. Good; you know what a clean pelt looks like. Brannoc. I make things out of iron and I buy things with fur on them.' },
        { text: 'Brannoc. I make things out of iron and I buy things with fur on them. Which are you here about?' },
      ],
      choices: brannocHub,
    },
    hub: { id: 'hub', text: 'Steel or fur?', choices: brannocHub },
    cloak: { id: 'cloak', text: 'There. Warmest thing you will ever wear, and every wolf in Thornhollow will know what it is. Worth it.', choices: brannocHub },
  },
};

/* ============================================================== Harlan == */

const harlanHub: DChoice[] = [
  { text: 'What happened to the caravan?', goto: 'what' },
  { text: 'Which road were they on?', goto: 'route' },
  { text: 'It was not wolves. Your wagons were driven off the road.', when: { quest: { id: 'caravan', entry: 'wreck' } }, once: 'notwolves', goto: 'notwolves' },
  { text: 'Jory is alive. He is on his way.', when: { fact: 'caravan.survivors', eq: 'rescued' }, once: 'jory', goto: 'jory' },
  { text: 'I found your strongbox.', when: { hasItem: 'coyle_strongbox' }, goto: 'box' },
  { text: 'Pell Varrow paid the Kerchiefs to take your caravan.', when: { hasItem: 'pell_ledger' }, badge: 'Evidence', once: 'pell', goto: 'pell' },
  { text: 'What were you carrying, besides salt and cloth?', when: { quest: { id: 'caravan', entry: 'manifest' } }, once: 'be', goto: 'be' },
  bye(),
];

export const HARLAN: Conversation = {
  npc: 'harlan',
  entry: [
    { when: { fact: 'caravan.cargo', eq: 'kept' }, node: 'betrayed' },
    { when: { fact: 'caravan.cargo', eq: 'sold' }, node: 'betrayed' },
    { when: notMet('harlan'), node: 'first' },
    { node: 'hub' },
  ],
  marker: [
    { when: notMet('harlan'), mark: '!' },
    { when: { any: [{ hasItem: 'coyle_strongbox' }, { fact: 'caravan.survivors', eq: 'rescued' }] }, mark: '?' },
  ],
  nodes: {
    first: {
      id: 'first',
      text: 'Harlan Coyle, of the Coyle Company. You came up the south road? Then you did not pass three wagons and a boy called Jory. No. No, of course not. Forgive me. Four days. He has never been four days late.',
      effects: [{ quest: { id: 'caravan', status: 'active', entry: 'harlan_plea' } }, { quest: { id: 'beasts', entry: 'harlan_view' } }],
      choices: harlanHub,
    },
    hub: {
      id: 'hub',
      text: [
        { when: { fact: 'caravan.survivors', eq: 'rescued' }, text: 'Jory is sleeping upstairs at Rook\'s. Sleeping! What can I do for you, friend?' },
        { when: { fact: 'caravan.survivors', eq: 'dead' }, text: 'I heard. I heard. You need not say it. What do you want?' },
        { when: { fact: 'caravan.days', gte: 3 }, text: '(He does not get up.) Three days of watching that road. I stopped. Somebody has to keep the stock, I told myself. Any word? No. There never is.' },
        { when: { fact: 'caravan.days', gte: 1 }, text: '(He keeps his eyes on the bend in the Old Road while he talks.) I keep thinking the lead wagon will come round there, Jory shouting that he got lost. Any word?' },
        { text: 'Any word?' },
      ],
      choices: harlanHub,
    },
    what: {
      id: 'what',
      text: 'The wolves, that is what. Three caravans this month. A hundred gold to whoever brings Jory home, and another hundred for my goods. The goods I can lose. Jory I cannot.',
      choices: harlanHub,
    },
    route: {
      id: 'route',
      text: 'The east road. The Old Road, through Thornhollow. They should have come through Vonnra\'s gate at dusk, four days ago. Holloway had men on the road. Nobody saw them.',
      choices: harlanHub,
    },
    notwolves: {
      id: 'notwolves',
      text: 'Driven...? Wolves do not drive wagons. Who — no. Find out who. Please.',
      effects: [{ rel: { npc: 'harlan', trust: 20 } }],
      choices: harlanHub,
    },
    jory: {
      id: 'jory',
      text: 'Alive. Alive! I — here. A hundred, as I said, and I will not forget this. The Coyle Company does not forget. Whatever you need that I can sell you, you pay cost.',
      effects: [{ gold: 100 }, { rel: { npc: 'harlan', trust: 40, affection: 40 } }, { npcFlag: { npc: 'harlan', key: 'discount', value: true } }],
      choices: harlanHub,
    },
    box: {
      id: 'box',
      text: 'The strongbox! Unopened. You could have walked off with this and I would never have known. A hundred gold, and my thanks.',
      effects: [
        { take: 'coyle_strongbox' }, { gold: 100 }, { set: { 'caravan.cargo': 'returned' } }, { quest: { id: 'caravan', entry: 'cargo_returned', outcome: 'returned' } }, CARAVAN_SETTLE,
        { rel: { npc: 'harlan', trust: 30, affection: 20 } },
        seen(hist('returned_cargo', 'brought the Coyle strongbox back unopened', ['honest', 'caravan'], 2, { trust: 10 }), 'harlan'),
      ],
      choices: harlanHub,
    },
    pell: {
      id: 'pell',
      text: 'Pell. Pell! We shook hands on this square at midsummer. Give me that. Holloway will see it, if I have to nail it to his door.',
      effects: [
        { take: 'pell_ledger' }, { set: { 'caravan.pell': 'exposed' } }, { quest: { id: 'caravan', entry: 'pell_exposed' } },
        { rel: { npc: 'harlan', trust: 30 } },
        seen(hist('exposed_pell', 'exposed Pell Varrow for paying the Kerchiefs to take the Coyle caravan', ['justice', 'caravan'], 2, { trust: 10 }, { pell: { fear: 30, trust: -80 }, holloway: { respect: 20 } }), 'harlan'),
      ],
      choices: harlanHub,
    },
    be: {
      id: 'be',
      text: '...Six crates for a buyer I will not name. Paid in advance, in gold, which is why I asked no questions. B.E. Blasting ember. Somebody out there wants to dig a very big hole.',
      effects: [{ quest: { id: 'caravan', entry: 'blasting_ember' } }, { learn: 'clue.blasting_ember' }],
      choices: harlanHub,
    },
    betrayed: {
      id: 'betrayed',
      text: 'You. You found it and you kept it. Get away from my stall.',
      choices: [bye('...')],
    },
  },
};

/* ================================================================ Pell == */

const pellHub: DChoice[] = [
  { text: 'What do you trade in?', action: 'trade' },
  { text: 'You smell of Kerchief money.', when: { knows: 'underworld' }, badge: 'Underworld', once: 'smell', goto: 'smell' },
  { text: 'I have read your ledger.', when: { hasItem: 'pell_ledger' }, badge: 'Evidence', goto: 'confront' },
  { text: 'Terrible business, the caravan.', goto: 'caravan' },
  { text: 'I know what is killing the wolves. It is worth something.', when: { all: [{ knows: 'root_cause' }, { not: { fact: 'dig.sold', exists: true } }, { not: { fact: 'beasts.outcome', exists: true } }, { any: [{ not: { fact: 'dig.pump', exists: true } }, { fact: 'dig.pump', eq: 'running' }] }] }, goto: 'dig' },
  bye(),
];

export const PELL: Conversation = {
  npc: 'pell',
  entry: [{ when: notMet('pell'), node: 'first' }, { when: { fact: 'caravan.pell', eq: 'ally' }, node: 'ally' }, { node: 'hub' }],
  nodes: {
    first: {
      id: 'first',
      text: 'Pell Varrow. Factor. If it can be bought, stored or sold in the Waystation, it has been through my books. Terrible business, Coyle\'s wagons. Terrible.',
      choices: pellHub,
    },
    hub: { id: 'hub', text: 'Yes?', choices: pellHub },
    caravan: {
      id: 'caravan',
      text: 'The wolves, one hears. Such a shame for Harlan. Such a shame for the Company. I have offered to buy him out, of course. As a friend.',
      choices: pellHub,
    },
    smell: {
      id: 'smell',
      text: '...Careful. That is the kind of thing that gets said once. Walk with me. You understand how things are done, I think. Coyle is finished; the only question is who picks up the pieces. Sixty gold now, and more later, to let the Kerchiefs keep what they have. You need not do a thing. Just not do certain other things.',
      choices: [
        { text: 'Take the money.', effects: [
          { gold: 60 }, { set: { 'caravan.pell': 'ally' } }, { quest: { id: 'caravan', entry: 'pell_joined' } }, { faction: { id: 'kerchief', standing: 20 } },
          { rel: { npc: 'pell', trust: 30 } },
          seen(hist('joined_pell', 'took Pell Varrow\'s money to leave the Coyle cargo with the Kerchiefs', ['corrupt', 'caravan'], 1, { trust: -15 }, { harlan: { trust: -60, affection: -40 }, rav: { respect: 10 } }), 'pell'),
        ], end: true },
        { text: 'I will think about it.', end: true },
        { text: 'I think Holloway would like to hear this.', effects: [{ rel: { npc: 'pell', fear: 20, trust: -30 } }], end: true },
      ],
    },
    confront: {
      id: 'confront',
      text: 'Where did you — the clerk. Of course. Let us be civilised. There is gold in this for you, a good deal of gold, if that book were to go into the fire.',
      choices: [
        { text: 'Name a price.', goto: 'bribe' },
        { text: 'Holloway will want to see this.', end: true, effects: [{ rel: { npc: 'pell', fear: 30 } }] },
      ],
    },
    bribe: {
      id: 'bribe',
      text: 'Eighty gold. And the book.',
      choices: [
        { text: 'Done.', effects: [
          { take: 'pell_ledger' }, { gold: 80 }, { set: { 'caravan.pell': 'ally' } }, { quest: { id: 'caravan', entry: 'pell_joined' } },
          seen(hist('sold_ledger', 'sold Pell Varrow his own ledger back', ['corrupt', 'caravan'], 1, { trust: -10 }), 'pell'),
        ], end: true },
        { text: 'No.', end: true },
      ],
    },
    dig: {
      id: 'dig',
      text: 'Is it? Go on. ...The Dig. Grimtunnel\'s little lamp-people, pumping their slurry into the stream. Oh, that is worth something. Not to Holloway: to the diggers. A pipe can be moved, for a consideration, and a consideration can be split. Forty gold, and the wolves stop dying. Everyone is happy. Especially me.',
      choices: [
        { text: 'Forty. Done.', effects: [
          { gold: 40 }, { set: { 'dig.sold': true } }, { quest: { id: 'beasts', entry: 'dig_sold' } }, { rel: { npc: 'pell', trust: 20 } },
          // Pell's men have a word with Snib; two days later the pipe goes into the sinkhole.
          { later: { days: 2, id: 'pell.dig', effect: { if: { any: [{ not: { fact: 'dig.pump', exists: true } }, { fact: 'dig.pump', eq: 'running' }] }, then: [{ set: { 'dig.pump': 'moved', 'dig.pell_cut': true } }] } } },
          seen(hist('sold_dig', 'sold what the Dig was doing to Pell Varrow, instead of stopping it', ['corrupt', 'beasts'], 1, { trust: -5 }, { wenna: { trust: -25, respect: -20 }, maeca: { respect: -25 }, pell: { respect: 15 } }), 'pell'),
        ], goto: 'dig_done' },
        { text: 'On second thought, I will deal with it myself.', goto: 'hub' },
      ],
    },
    dig_done: { id: 'dig_done', text: 'A pleasure. Give it two days. And if anyone asks, you and I talked about the weather.', choices: pellHub },
    ally: { id: 'ally', text: 'Our arrangement stands. Discreetly, please.', choices: [{ text: 'What do you have?', action: 'trade' }, bye()] },
  },
};

/* ================================================================= Rav == */

const ravHub: DChoice[] = [
  { text: 'Tell me about the Kerchiefs.', goto: 'kerchiefs' },
  { text: 'Did anyone come through with news of Coyle\'s caravan?', goto: 'clerk' },
  { text: 'Know anyone who would buy this, quietly?', when: { hasItem: 'coyle_strongbox' }, goto: 'fence' },
  { text: 'Can you get me into the Roost alive?', when: { knows: 'underworld' }, badge: 'Underworld', once: 'roost', goto: 'roost' },
  { text: 'What do you have for sale?', action: 'trade' },
  bye(),
];

export const RAV: Conversation = {
  npc: 'rav',
  entry: [{ when: notMet('rav'), node: 'first' }, { node: 'hub' }],
  marker: [{ when: notMet('rav'), mark: '!' }],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { bg: 'outcast' }, text: 'Well, well. Somebody who knows how to wear a kerchief without looking like a parrot. Sit. I\'m Rav. Doctor Rav, if you are bleeding. Doctor McBreathless, if you are the Watch.' },
        { when: { hasTag: 'kerchief_colors' }, text: 'Red cloth, walking into my tavern in daylight. Brave, or someone gave it to you as a joke. Rav. Sit, before Holloway sees you.' },
        { text: 'You are blocking my light. ...Oh, sit, then. Rav. I was a doctor. Then I was a Kerchief. Now I am a doctor again, mostly, and I drink here.' },
      ],
      choices: ravHub,
    },
    hub: { id: 'hub', text: [{ when: { rel: { npc: 'rav', axis: 'trust', gte: 30 } }, text: 'Friend. Pull up a stool.' }, { text: 'Hm?' }], choices: ravHub },
    kerchiefs: {
      id: 'kerchiefs',
      text: 'Redcowl runs them. He would rather talk than bleed, and he would rather you bled than he talked. Their camp is in the ravine off the Old Road — the Roost. Wear red, walk slowly, keep your hands empty, and you might get to say hello before they shoot you.',
      effects: [{ learn: 'hint.roost' }],
      choices: ravHub,
    },
    clerk: {
      id: 'clerk',
      text: [
        { when: { knows: 'underworld' }, text: 'A toll clerk bought the room a round the night the caravan vanished. Clerks do not buy rounds. He had "done somebody a favour": told Coyle\'s teamsters the road was shut and sent them down the forest track. Between us — he also has a key he should not have. Pell\'s warehouse. He showed it to me like a boy with a frog.' },
        { text: 'A toll clerk bought the room a round the night the caravan vanished. Clerks do not buy rounds. He had "done somebody a favour": told Coyle\'s teamsters the road was shut and sent them down the forest track. Draw your own lines.' },
      ],
      effects: [
        { quest: { id: 'caravan', status: 'active', entry: 'clerk_turned' } },
        { if: { knows: 'underworld' }, then: [{ quest: { id: 'caravan', entry: 'clerks_key' } }, { give: 'clerks_key' }, { notice: 'Rav slides a key across the table: "He left it on his stool."' }] },
      ],
      choices: ravHub,
    },
    fence: {
      id: 'fence',
      text: 'Coyle\'s strongbox. Oh, dear. Yes, I know a man. A hundred and fifty, and nobody asks where it came from — at first. People always find out, in the end.',
      choices: [
        { text: 'Sell it.', effects: [
          { take: 'coyle_strongbox' }, { gold: 150 }, { set: { 'caravan.cargo': 'sold', 'player.wanted': true } }, { quest: { id: 'caravan', entry: 'cargo_sold', outcome: 'kept' } }, CARAVAN_SETTLE,
          seen(hist('fenced_cargo', 'sold the Coyle strongbox to a fence', ['theft', 'caravan'], 2, { trust: -20 }, { harlan: { trust: -80, affection: -60 }, holloway: { trust: -40 } }), 'rav'),
        ], goto: 'hub' },
        { text: 'On second thought.', goto: 'hub' },
      ],
    },
    roost: {
      id: 'roost',
      text: 'Alive, and talking? Wear this, walk in the front, and say "Redcowl owes Rav a leg." He will laugh. If he laughs, you are in. If he does not laugh, I was never here.',
      effects: [{ if: { not: { hasItem: 'red_kerchief' } }, then: { give: 'red_kerchief' } }, { learn: 'pass.redcowl' }, { rel: { npc: 'rav', trust: 10 } }],
      choices: ravHub,
    },
  },
};

/* ================================================================ Chid == */

const chidHub: DChoice[] = [
  { text: 'Used to work?', goto: 'shrine' },
  { text: 'Let me try. I know the rite.', when: { all: [{ bg: 'devout' }, { hasItem: 'pilgrims_lantern' }, { not: { fact: 'shrine.lit', eq: true } }] }, badge: 'Faith', goto: 'relight' },
  { text: 'Bless me, Chid.', when: { fact: 'shrine.lit', eq: true }, effects: [{ condition: { id: 'blessed', days: 2 } }, { notice: 'The flame\'s warmth stays with you. (Blessed: +15% holy damage)' }], goto: 'blessed' },
  { text: 'There is a sealed door in the Verge.', when: { quest: { id: 'vault', entry: 'seen' } }, once: 'vault', goto: 'vault' },
  { text: 'Something is digging under the Verge.', when: { knows: 'grimtunnel' }, once: 'below', goto: 'below' },
  { text: 'The Warden at the Low Ford. The lamps fed it. Who made it?', when: { knows: 'lore.warden' }, once: 'warden', goto: 'warden' },
  bye(),
];

export const CHID: Conversation = {
  npc: 'chid',
  entry: [{ when: { fact: 'player.just_died', eq: true }, node: 'woke' }, { when: notMet('chid'), node: 'first' }, { node: 'hub' }],
  marker: [{ when: notMet('chid'), mark: '!' }],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { bg: 'devout' }, text: 'Oh! A lantern of the Order! Lit! Oh, sit down, sit, sit. I\'m Chid. They call me the Fool, which is fair. This is the shrine of the Morning Light. It used to work.' },
        { text: 'Oh! A visitor. Hello. I\'m Chid. They call me the Fool, which is fair. This is the shrine of the Morning Light. It used to work.' },
      ],
      choices: chidHub,
    },
    hub: {
      id: 'hub',
      text: [{ when: { fact: 'shrine.lit', eq: true }, text: 'It is still burning. Every morning I check. It is still burning.' }, { text: 'Hello again! The light is patient. I am trying to be.' }],
      choices: chidHub,
    },
    woke: {
      id: 'woke',
      text: [
        { when: { fact: 'shrine.lit', eq: true }, text: 'You are awake! Good. Good. A carter found you on the Old Road and brought you here, and the flame — the flame kept you. I watched it. You will be sore for a day or two. Whatever did this to you is still out there, {name}. It will have your things. They always keep something.' },
        { text: 'Oh, you are awake. A carter found you on the Old Road and brought you here, and I did not know what else to do, so I prayed at the shrine and — well. Here you are. You will be sore for a day or two. Whatever did this is still out there. It will have your things.' },
      ],
      effects: [{ set: { 'player.just_died': false } }],
      choices: [
        { text: 'Thank you, Chid.', effects: [{ rel: { npc: 'chid', affection: 10 } }], end: true },
        { text: 'Where did I fall?', goto: 'where' },
      ],
    },
    where: {
      id: 'where',
      text: 'In the Verge. The carter said there was a grave-mark where you lay, and your purse under it — and a beast standing over it that would not let him near. Be careful. It knows your smell now.',
      choices: [bye('I will get it back.')],
    },
    shrine: {
      id: 'shrine',
      text: 'The flame. It blessed people. Kept the dead lying down. Then the Order left and the flame went out, and I have been... trying. With prayers. And candles. And a bellows, once. That was a bad day.',
      choices: chidHub,
    },
    relight: {
      id: 'relight',
      speaker: 'narrator',
      text: 'You open your lantern and say the words you learned at seven, the ones about the dark being only the part of the day that has not happened yet. The shrine takes the flame as if it had been waiting. Chid makes a sound like a kettle.',
      effects: [
        { set: { 'shrine.lit': true } }, { trait: 'lightbearer' }, { rel: { npc: 'chid', trust: 40, affection: 40 } },
        seen(hist('shrine_lit', 'relit the shrine of the Morning Light', ['faith', 'deed'], 2, { respect: 10, affection: 5 }), 'chid'),
      ],
      next: 'lit',
    },
    lit: { id: 'lit', text: 'It WORKS. It works! I knew it worked. I said it worked! Nobody — I have to tell Rook. I have to tell everyone. Thank you. Thank you!', choices: chidHub },
    blessed: { id: 'blessed', text: 'There. Go on, then, and be warm.', choices: chidHub },
    warden: {
      id: 'warden',
      text: 'The Order did, I think. Before the Watch. Before me, certainly, which is a long time. Everything the Morning Light made was made to guard something. That is the trouble with guards: they outlast whatever they were guarding against, and then they guard against us.',
      effects: [{ rel: { npc: 'chid', respect: 10 } }],
      choices: chidHub,
    },
    vault: {
      id: 'vault',
      text: 'The old empire did something there, before the Watch. I think the Watch was founded to keep it done. I do not know what. Vonnra does. Vonnra will not say. That, I think, is the answer.',
      effects: [{ quest: { id: 'vault', entry: 'chid_empire' } }],
      choices: chidHub,
    },
    below: {
      id: 'below',
      text: 'Digging. Down. The Order used to say the dark is only light that has not been found yet. I never liked that one. It sounds like a threat.',
      choices: chidHub,
    },
  },
};

/* ============================================================== Vonnra == */

const vonnraHub: DChoice[] = [
  { text: 'I will pay the toll.', show: { not: { fact: 'toll.paid', eq: true } }, when: { gold: { gte: 5 } }, locked: 'The toll is five gold', effects: [{ gold: -5 }, { set: { 'toll.paid': true } }], goto: 'paid' },
  { text: 'Did Coyle\'s caravan pay your toll?', when: { quest: { id: 'caravan', status: 'active' } }, goto: 'ledger' },
  { text: 'The sealed door in the Verge...', when: { quest: { id: 'vault', entry: 'seen' } }, once: 'vault', goto: 'vault' },
  { text: 'I have come to read your old script.', when: { knows: 'arcana' }, badge: 'Arcana', once: 'arcana', goto: 'arcana' },
  { text: 'What do you sell?', action: 'trade' },
  { text: [{ when: { fact: 'chapter.done', eq: true }, text: 'Read my fortune again.' }, { text: 'Tell me my fortune.' }], when: { fact: 'chapter.ready', eq: true }, goto: 'fortune' },
  bye(),
];

export const VONNRA: Conversation = {
  npc: 'vonnra',
  entry: [{ when: notMet('vonnra'), node: 'first' }, { node: 'hub' }],
  marker: [{ when: notMet('vonnra'), mark: '!' }, { when: { fact: 'chapter.ready', eq: true }, mark: '?' }],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { bg: 'scholar' }, text: 'A reader. You have the look. The toll is the toll: five gold to pass east. I am Vonnra. I see a great deal. I say very little. You, of all people, will find that frustrating.' },
        { text: 'The toll is the toll. Five gold to pass east, or no gold and I remember your face. I am Vonnra. I see a great deal. I say very little. You will find that is the arrangement.' },
      ],
      effects: [{ rel: { npc: 'vonnra', respect: 0 }, quiet: true }],
      choices: vonnraHub,
    },
    hub: {
      id: 'hub',
      text: [
        { when: { fact: 'chapter.done', eq: true }, text: 'Your chapter is written. The next one is not. Payment, always.' },
        { when: { fact: 'kerchief.raids', gte: 2 }, text: 'Fewer wagons, fewer tolls. The Kerchiefs are bad for everyone\'s business but their own. Payment, always.' },
        { text: 'Payment, always.' },
      ],
      choices: vonnraHub,
    },
    paid: { id: 'paid', text: 'The east gate is yours. Try to come back through it.', choices: vonnraHub },
    ledger: {
      id: 'ledger',
      text: 'Everything that passes my gate is written down. Reading it is not free.',
      choices: [
        { text: 'Pay five gold to see the ledger.', when: { gold: { gte: 5 } }, locked: 'Five gold', effects: [{ gold: -5 }, { quest: { id: 'caravan', entry: 'toll_ledger' } }], goto: 'ledger_read' },
        back(),
      ],
    },
    ledger_read: { id: 'ledger_read', text: 'There. The Coyle caravan did not pay my toll. It never came through my gate. Whatever happened to it happened before it reached me.', choices: vonnraHub },
    vault: {
      id: 'vault',
      text: 'No. Not for any price. That is the only thing I will ever say to you without charging for it.',
      effects: [{ quest: { id: 'vault', entry: 'vonnra_refuses' } }],
      choices: vonnraHub,
    },
    /* The fortune: what she sees is what you did. */
    fortune: {
      id: 'fortune',
      text: 'Sit. Give me your hand. No, the other one: the one you hold the blade with. No charge, this once. I have been waiting to see how it came out.',
      next: 'f_beasts',
    },
    f_beasts: {
      id: 'f_beasts',
      text: [
        { when: { fact: 'beasts.outcome', eq: 'cured' }, text: 'I see water running clear. Wolves in the deep wood where they belong, and a hole in the hillside with no poison coming out of it. You went looking for the cause and not the culprit. Most people never learn the difference.' },
        { when: { fact: 'beasts.outcome', eq: 'allied' }, text: 'I see wolves running beside you, not at you. The old grey one lets you walk in front. Holloway sleeps with his sword across his knees now. Be careful what you have taught them to follow.' },
        { when: { all: [{ fact: 'beasts.outcome', eq: 'slaughtered' }, { fact: 'greymuzzle', eq: 'dead' }] }, text: 'I see pelts. A great many pelts, and a grey one on top of the pile. The road is safe and the wood is quiet. Something that was sick got sicker, and then there was nothing left of it to be sick.' },
        { when: { fact: 'beasts.outcome', eq: 'slaughtered' }, text: 'I see a quiet wood. Too quiet. You made the road safe the way a fire makes a house warm.' },
        { when: { fact: 'beasts.outcome', eq: 'ignored' }, text: 'I see wolves at the east gate, and a man of the Watch who did not come home. You were busy. The world was not.' },
        { when: { fact: 'beasts.outcome', eq: 'exploited' }, text: 'I see clean water, and a ledger with a new line in it. The wolves are saved and Pell Varrow owns a hole in the ground. You were paid; he was paid. Someone always is. Wenna has not forgiven you, and she is the one who notices.' },
        { text: 'The wolves, I see only dimly. Whatever you meant to do about them, you have not done it yet.' },
      ],
      next: 'f_caravan',
    },
    f_caravan: {
      id: 'f_caravan',
      text: [
        { when: { all: [{ fact: 'caravan.survivors', eq: 'rescued' }, { fact: 'caravan.cargo', eq: 'returned' }] }, text: 'I see a boy asleep in a wagon, and his uncle sitting up beside him all night. Salt and iron back where they belong. The Coyle Company will say your name at every table it sits at.' },
        { when: { all: [{ fact: 'caravan.survivors', eq: 'rescued' }, { fact: 'caravan.cargo', eq: 'sold' }] }, text: 'I see a boy come home, and a strongbox go the other way. Harlan will learn where it went. People always do.' },
        { when: { fact: 'caravan.survivors', eq: 'rescued' }, text: 'I see three teamsters walking home, thinner than when they left. What became of the rest of it is between you and the Kerchiefs.' },
        { when: { fact: 'caravan.survivors', eq: 'dead' }, text: 'I see cages. I will not tell you what is in them. You know.' },
        { text: 'The caravan: a cold trail, cold cages. It is not finished. Neither are you.' },
      ],
      next: 'f_pell',
    },
    f_pell: {
      id: 'f_pell',
      text: [
        { when: { fact: 'caravan.pell', eq: 'exposed' }, text: 'And Pell. Pell in irons, being walked to the cells, telling everyone who will listen that he has friends. He does. They are not in this town.' },
        { when: { fact: 'caravan.pell', eq: 'ally' }, text: 'And a ledger, with your name in it, in Pell\'s small tidy hand. You were paid. So was everyone else in that book. I would keep an eye on all of them.' },
        { when: { fact: 'caravan.pell', eq: 'fled' }, text: 'And an empty warehouse, and a man on a fast horse who will not stop until he is somewhere that has never heard of the Coyle Company. He will not forget you.' },
        { text: 'And Pell Varrow, counting. He is always counting. One day he will count you.' },
      ],
      next: 'f_self',
    },
    f_self: {
      id: 'f_self',
      text: [
        { when: { trait: 'risen_once' }, text: 'And you. You have already died on this road. Most people only get to do that the once. Something did not want you to stay down, and I would very much like to know what.' },
        { when: { fact: 'player.wanted', eq: true }, text: 'And you. The Watch has your description. It is not flattering.' },
        { when: { trait: 'wolf_friend' }, text: 'And you, who smell of the Pack now. Dogs in the square will not bark at you. People will.' },
        { text: 'And you. You came up the Low Ford road at night, and the lamps lit for you. They have not done that for anyone in a long time.' },
      ],
      next: 'f_below',
    },
    f_below: {
      id: 'f_below',
      text: 'Last. Under the Verge, something is turning over in its sleep. The little lamp-people are digging down to it with the Warden\'s heart in their arms, and they think it will be grateful. And the door in the hillside...',
      choices: [{ text: 'What about the door?', goto: 'f_door' }],
    },
    f_door: {
      id: 'f_door',
      text: 'No. That is all. That is all I see for free. The rest you will have to walk into yourself, and you will, because you are the kind that does.',
      effects: [{ set: { 'chapter.done': true } }, hist('fortune_read', 'had your fortune read by Vonnra Hydrocheck', ['chapter'], 0)],
      choices: [{ text: 'Close the book on this chapter.', action: 'fortune' }],
    },
    arcana: {
      id: 'arcana',
      text: 'Hm. You do read. Then you know what "Legio Septima" means over a door, and you know better than to ask me what is behind it. Ask me something cheaper.',
      effects: [{ rel: { npc: 'vonnra', respect: 20 } }],
      choices: vonnraHub,
    },
  },
};

/* ============================================================== Keegan == */

export const KEEGAN: Conversation = {
  npc: 'keegan',
  entry: [{ when: notMet('keegan'), node: 'first' }, { node: 'hub' }],
  nodes: {
    first: {
      id: 'first',
      text: 'Halt! None pass north. Professor Keegan, Knight of the Argent Vigil. Probationary. It is a real title.',
      choices: [{ text: 'What is north?', goto: 'north' }, { text: 'Why "Professor"?', goto: 'prof' }, bye()],
    },
    hub: {
      id: 'hub', text: 'Still not ready. I would know.',
      choices: [
        { text: 'What is north?', goto: 'north' },
        { text: 'Why "Professor"?', goto: 'prof' },
        { text: 'The Ford-Warden. The Watch\'s lamps were feeding it.', when: { knows: 'lore.warden' }, once: 'warden', goto: 'warden' },
        { text: 'Captain Ashe is buried in the garden. Did the Vigil know him?', when: { knows: 'lore.ashe' }, once: 'ashe', goto: 'ashe' },
        bye(),
      ],
    },
    warden: {
      id: 'warden',
      text: '...Who told you that? The Vigil kept those lamps before the Watch did. Before the Watch was the Watch. The lamps were never to keep the dark out. They were to keep the Warden asleep. If somebody lit them again, somebody wanted it awake. Do not repeat that. I am probationary.',
      effects: [{ rel: { npc: 'keegan', respect: 15, trust: 10 } }],
      choices: [{ text: 'Who would want it awake?', goto: 'who' }, bye()],
    },
    who: {
      id: 'who',
      text: 'Someone who needed the ford closed. Someone who wanted a heart. You tell me; you were there.',
      choices: [bye()],
    },
    ashe: {
      id: 'ashe',
      text: 'Know him? The Vigil buried him. He closed the north road with forty lamps and walked back through it with one. What he saw up there is why I am standing here telling you no. When you are ready, he would have told you himself.',
      effects: [{ rel: { npc: 'keegan', respect: 10 } }],
      choices: [bye()],
    },
    north: { id: 'north', text: 'Things you are not ready for. When you are, I will know. It is in the probationary handbook, chapter four.', choices: [{ text: 'Why "Professor"?', goto: 'prof' }, bye()] },
    prof: { id: 'prof', text: 'I taught, before. Rhetoric. It is very useful for telling people no.', choices: [{ text: 'What is north?', goto: 'north' }, bye()] },
  },
};

/* ========================================================= notice board == */

export const BOARD: Conversation = {
  npc: 'board',
  entry: [{ node: 'read' }],
  nodes: {
    read: {
      id: 'read', speaker: 'narrator',
      // The board is the town talking to itself: notices go up and come
      // down as things happen.
      text: [
        { add: true, when: { not: { fact: 'beasts.outcome', exists: true } }, text: 'WOLF BOUNTY — five gold the pelt, fifty for the grey alpha. Capt. Holloway, the Watch.' },
        { add: true, when: { fact: 'beasts.outcome', eq: 'cured' }, text: 'The wolf bounty is WITHDRAWN. The stream runs clear. (Someone has written underneath: "about time".)' },
        { add: true, when: { fact: 'beasts.outcome', eq: 'slaughtered' }, text: 'BOUNTY CLOSED. No more pelts wanted. The Watch thanks the hunters of the Waystation.' },
        { add: true, when: { fact: 'beasts.outcome', eq: 'allied' }, text: 'NOTICE: Travellers keep to the road. The Watch will not answer for wolves that WALK WITH PEOPLE. Capt. Holloway.' },
        { add: true, when: { fact: 'beasts.outcome', eq: 'ignored' }, text: 'CURFEW. East gate closed at dusk until further notice. One of ours did not come home. The Watch.' },
        { add: true, when: { not: { fact: 'caravan.survivors', exists: true } }, text: 'MISSING: Coyle Company caravan, three wagons, J. Coyle driving. REWARD. H. Coyle.' },
        { add: true, when: { fact: 'caravan.survivors', eq: 'rescued' }, text: 'THANK YOU, whoever you are, from all of the Coyle Company. Jory is home. — H.' },
        { add: true, when: { fact: 'caravan.survivors', eq: 'dead' }, text: '(Harlan\'s notice has been taken down. Only the nail is left.)' },
        { add: true, when: { fact: 'caravan.pell', eq: 'exposed' }, text: 'BY ORDER OF THE WATCH: the warehouse of P. Varrow is sealed pending inquiry.' },
        { add: true, when: { fact: 'caravan.pell', eq: 'fled' }, text: 'WANTED: Pell Varrow, factor, for questions about the Coyle caravan. He left in a hurry.' },
        { add: true, when: { fact: 'player.wanted', eq: true }, text: 'WANTED: a traveller seen selling Coyle goods. The likeness is poor, but not poor enough.' },
        { add: true, when: { fact: 'tremor.felt', eq: true }, text: 'Did anyone else feel that? — R.' },
        { add: true, text: 'WANTED: bitterroot, any quantity. Wenna.' },
        { add: true, when: { day: { lte: 3 } }, text: 'Has anyone seen my cat? Grey. Answers to nothing. M.' },
        { add: true, when: { day: { gte: 4 } }, text: 'Cat found. She was in the grain store the whole time. — M.' },
      ],
      effects: [{ if: { not: { fact: 'caravan.survivors', exists: true } }, then: { quest: { id: 'caravan', status: 'active', entry: 'harlan_plea' } } }, { if: { not: { fact: 'beasts.outcome', exists: true } }, then: { quest: { id: 'beasts', status: 'active', entry: 'holloway_bounty' } } }],
      choices: [bye('Step back.')],
    },
  },
};

/* =============================================================== Sella == */

/* She keeps the blue room at the top of Rook's stairs, by Rook's leave and
 * for Rook's cut. Frank, funny, nobody's fool; she hears what men say when
 * they think it does not matter. A night with her is paid for, agreed to,
 * and nobody's business: the scene fades, and what is left is the morning. */

const SELLA_PRICE = 15;
const sellaHub: DChoice[] = [
  { text: 'What do you hear, up there?', goto: 'hear' },
  { text: 'How much for the night?', goto: 'price' },
  { text: 'Does Rook mind?', once: 'rook', goto: 'rook' },
  bye('Not tonight.'),
];

export const SELLA: Conversation = {
  npc: 'sella',
  entry: [
    { when: notMet('sella'), node: 'first' },
    { when: { fact: 'sella.nights', gte: 1 }, node: 'again' },
    { node: 'hub' },
  ],
  marker: [{ when: notMet('sella'), mark: '!' }],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { history: 'ford_warden_slain' }, text: 'So you\'re the one who put the big dead bastard at the ford back in the ground. Half the tavern\'s been drinking to you, and the other half\'s been drinking to them. I\'m Sella. I keep the blue room at the top of Rook\'s stairs. Talk\'s free. The rest isn\'t.' },
        { text: 'You\'ve got the look of someone who\'s been sleeping in ditches, love. Sella. I keep the blue room at the top of Rook\'s stairs. Talk\'s free. The rest isn\'t.' },
      ],
      choices: sellaHub,
    },
    hub: {
      id: 'hub',
      text: [
        { when: { time: 'night' }, text: 'Evening, {name}. The lamp\'s lit upstairs, if you\'re asking. You look like you\'re asking.' },
        { text: 'Back again. People will talk. Let them; it\'s good for business.' },
      ],
      choices: sellaHub,
    },
    again: {
      id: 'again',
      text: [
        { when: { time: 'night' }, text: 'There you are. I was starting to think you\'d found someone cheaper. You\'d have been robbed.' },
        { text: '{name}. Still walking straight, I see. I\'ll take that as a compliment.' },
      ],
      choices: sellaHub,
    },
    hear: {
      id: 'hear',
      text: [
        { when: { quest: { id: 'caravan', status: 'active' } }, text: 'Men talk after. God, do they talk. There\'s a toll clerk who\'s been flush all month, paying me in new silver with the Varrow mark stamped on it. Last time he was pleased with himself: said he\'d "sent some wagons down the wrong road" and got paid twice for it. Then he fell asleep on my arm. Charming.' },
        { when: { fact: 'beasts.outcome', exists: true }, text: 'That the wolves are quiet, and Holloway\'s drinking more than he\'s paying. That Pell sleeps with his ledgers. That Harlan cries when he\'s had three. Same as ever.' },
        { text: 'That the wolves are sick and Holloway\'s a prick, and that nobody who goes up the north road comes back to tell me about it. Same as ever.' },
      ],
      // (Heard once is enough for the journal.)
      effects: [{ if: { all: [{ quest: { id: 'caravan', status: 'active' } }, { not: { fact: 'sella.told_clerk', eq: true } }] }, then: [{ quest: { id: 'caravan', entry: 'sella_clerk' } }, { set: { 'sella.told_clerk': true } }] }],
      choices: [back()],
    },
    rook: {
      id: 'rook',
      text: 'Rook minds everything. She also takes a third, keeps the drunks off the stairs, and once put a Kerchief through the front door for not paying. I\'ve had worse landladies. I\'ve had worse mothers.',
      effects: [{ rel: { npc: 'sella', affection: 5 } }],
      choices: [back()],
    },
    price: {
      id: 'price',
      text: `${SELLA_PRICE} gold, and I'll want it up front. For that you get the blue room, a bath that's mostly warm, and me, until morning. Anything you'd rather I didn't do, say so. Anything you'd rather I did, say that too.`,
      choices: [
        { text: `${SELLA_PRICE} gold, then. Lead the way.`, when: { gold: { gte: SELLA_PRICE } }, locked: `You would need ${SELLA_PRICE} gold`, goto: 'night' },
        { text: 'Just the talk, for now.', goto: 'hub' },
      ],
    },
    night: {
      id: 'night',
      speaker: 'narrator',
      text: 'She takes the coins first and your hand second, and leads you up Rook\'s narrow stairs. The blue room smells of lavender and lamp oil, and the bath is, as promised, mostly warm. What follows is nobody\'s business but yours: slow, and warm, and unhurried, and for a few hours the road and the dead on it are a long way off. You wake with her hair across you and the sun already up. She is dressed, and counting.',
      effects: [
        { gold: -SELLA_PRICE },
        { add: { 'sella.nights': 1 } },
        { rel: { npc: 'sella', affection: 8, trust: 4 } },
        { condition: { id: 'warmed', days: 1, note: 'A night in the blue room' } },
        { notice: 'You feel good. Better than good. (Warmed: +8% damage, +5% speed, one day)' },
      ],
      next: 'morning',
    },
    morning: {
      id: 'morning',
      text: [
        { when: { fact: 'sella.nights', gte: 3 }, text: 'You\'re getting to be a habit, {name}. I don\'t mind. Rook does; she says you\'re wearing out the stairs. Go on, the day\'s wasting, and somebody out there needs killing.' },
        { text: 'You snore, by the way. Not badly. Go on, then. Come back in one piece; the pieces are what I like.' },
      ],
      choices: [
        { text: 'Sleep a little longer first.', action: 'rest' },
        bye('Until next time.'),
      ],
    },
  },
};

export const TOWN_CONVOS: Record<string, Conversation> = {
  rook: ROOK, holloway: HOLLOWAY, maeca: MAECA, wenna: WENNA, tam: TAM, brannoc: BRANNOC, harlan: HARLAN, pell: PELL,
  rav: RAV, chid: CHID, vonnra: VONNRA, keegan: KEEGAN, board: BOARD, sella: SELLA,
};
