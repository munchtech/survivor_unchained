import type { Conversation, DChoice } from '@/world/dialogue';
import { hist } from './town';

/* The Verge's voices: an old wolf who cannot talk, a bandit who would
 * rather, a lampling foreman who should not be in charge of anything, and
 * a digger who went too deep. */

const bye = (text = 'Leave.'): DChoice => ({ text, end: true });

export const GREYMUZZLE: Conversation = {
  npc: 'greymuzzle',
  entry: [{ when: { fact: 'greymuzzle', eq: 'met' }, node: 'again' }, { when: { fact: 'greymuzzle', eq: 'ally' }, node: 'again' }, { node: 'first' }],
  nodes: {
    first: {
      id: 'first', speaker: 'narrator',
      text: 'The old wolf comes out of the rocks alone. He is grey to the eyes, and thin, and he does not growl. He looks at you for a long time. Behind him, in the shadow of the stones, wolves lie in the dirt and do not get up.',
      choices: [
        { text: 'Kneel, and hold out an empty hand.', when: { any: [{ knows: 'beastlore' }, { knows: 'hint.greymuzzle' }, { hasTag: 'wolf_fang' }] }, badge: 'Beastlore', locked: 'You do not know how to speak to him', goto: 'show' },
        { text: 'Draw your weapon.', effects: [{ set: { 'hollow.hostile': true } }], end: true },
        bye('Back away slowly.'),
      ],
    },
    show: {
      id: 'show', speaker: 'narrator',
      text: 'He turns and walks into the Hollow, and you follow. The sick ones\' eyes are milky; their gums are black. One of them tries to stand when it sees you, and cannot. Greymuzzle looks east, toward the stream, then back at you, and waits.',
      effects: [
        { set: { greymuzzle: 'met', 'hollow.peace': true } }, { learn: 'clue.sick_wolf', text: 'The Pack is sick, not bold.' },
        { quest: { id: 'beasts', status: 'active', entry: 'greymuzzle_met' } }, { quest: { id: 'beasts', entry: 'clue.sick_wolf' } },
        { rel: { npc: 'greymuzzle', trust: 40 }, quiet: true },
      ],
      choices: [
        { text: '"I will stop whatever is poisoning you."', effects: [{ trait: 'wolf_friend' }], end: true },
        { text: '"The men in the ravine are no friends of yours. Run with me."', when: { any: [{ knows: 'hint.roost' }, { quest: { id: 'caravan', entry: 'roost_found' } }] }, locked: 'You would need somewhere to lead them', goto: 'ally' },
        bye('Leave them in peace.'),
      ],
    },
    ally: {
      id: 'ally', speaker: 'narrator',
      text: 'Greymuzzle lifts his head and howls, once. Four of the stronger wolves get up and come to stand beside you. The old wolf lies back down among the sick. He is not coming. They are his answer.',
      effects: [
        { set: { greymuzzle: 'ally', 'pack.allied': true } }, { trait: 'wolf_friend' },
        { if: { not: { fact: 'beasts.outcome', exists: true } }, then: [{ set: { 'beasts.outcome': 'allied' } }, { quest: { id: 'beasts', status: 'resolved', outcome: 'allied' } }] },
        hist('pack_allied', 'ran with the Pack of Thornhollow', ['beasts', 'wolves'], 2, undefined, { maeca: { respect: 25, affection: 15 }, holloway: { trust: -20 }, brannoc: { trust: -10 } }),
      ],
      choices: [bye('Go.')],
    },
    again: {
      id: 'again', speaker: 'narrator',
      text: [{ when: { fact: 'beasts.outcome', eq: 'cured' }, text: 'Greymuzzle is on his feet. So are the others. He looks at you, and then away, which from a wolf is as good as thanks.' }, { text: 'Greymuzzle watches you from the rocks. He does not get up.' }],
      choices: [bye()],
    },
  },
};

export const REDCOWL: Conversation = {
  npc: 'redcowl',
  entry: [{ when: { met: 'redcowl' }, node: 'hub' }, { node: 'first' }],
  nodes: {
    first: {
      id: 'first',
      text: [
        { when: { hasTag: 'kerchief_colors' }, text: 'Look at the colours on you. You are not one of mine, and you are not stupid enough to be one of Holloway\'s. Redcowl. You are standing in my Roost. Talk.' },
        { text: 'Redcowl. You are standing in my camp, which means my sentries are drunk or you are interesting. Which is it?' },
      ],
      choices: [
        { text: '"Redcowl owes Rav a leg."', when: { knows: 'pass.redcowl' }, badge: 'Underworld', goto: 'rav' },
        { text: 'I have come for the Coyle wagons.', goto: 'goods' },
        { text: 'Let the teamsters go.', when: { not: { fact: 'caravan.survivors', exists: true } }, goto: 'prisoners' },
        { text: 'Pell Varrow sold you out. It is in his ledger.', when: { hasItem: 'pell_ledger' }, badge: 'Evidence', goto: 'pell' },
        { text: 'The Watch is on its way. You have an hour.', when: { any: [{ knows: 'underworld' }, { knows: 'arcana' }, { rel: { npc: 'holloway', axis: 'trust', gte: 30 } }] }, locked: 'He would not believe you', goto: 'trick' },
        bye('I will be going.'),
      ],
    },
    hub: {
      id: 'hub', text: 'Still here?',
      choices: [
        { text: 'About the Coyle wagons.', when: { not: { fact: 'redcowl', eq: 'bargained' } }, goto: 'goods' },
        { text: 'Let the teamsters go.', when: { not: { fact: 'caravan.survivors', exists: true } }, goto: 'prisoners' },
        { text: 'Pell Varrow sold you out.', when: { hasItem: 'pell_ledger' }, badge: 'Evidence', goto: 'pell' },
        bye('Nothing.'),
      ],
    },
    rav: {
      id: 'rav',
      text: 'Ha! HA. That old saw-bones. He does too, and he knows it. All right. Rav\'s friends get to talk before they get shot. So: talk.',
      effects: [{ rel: { npc: 'redcowl', trust: 25 } }, { faction: { id: 'kerchief', standing: 10 } }],
      choices: [
        { text: 'I have come for the Coyle wagons.', goto: 'goods' },
        { text: 'Let the teamsters go.', when: { not: { fact: 'caravan.survivors', exists: true } }, goto: 'prisoners' },
        bye('Just saying hello.'),
      ],
    },
    goods: {
      id: 'goods',
      text: 'The wagons are salvage, and salvage is mine. You want the strongbox, you buy it. A hundred gold and I throw in the teamsters, since they eat more than they are worth.',
      choices: [
        { text: 'Pay a hundred gold.', when: { gold: { gte: 100 } }, locked: 'A hundred gold', effects: [{ gold: -100 }], goto: 'deal' },
        { text: 'Five good wolf pelts instead.', when: { hasItem: 'wolf_pelt', qty: 5 }, locked: 'Five wolf pelts', effects: [{ take: 'wolf_pelt', qty: 5 }], goto: 'deal' },
        { text: 'I have killed a dozen of your people today. Give me the box.', when: { fact: 'verge.kerchief_kills', gte: 12 }, locked: 'He is not afraid of you', effects: [{ rel: { npc: 'redcowl', fear: 40 } }], goto: 'deal' },
        { text: 'Your wolf trouble is over. That is worth something.', when: { any: [{ fact: 'pack.allied', eq: true }, { fact: 'beasts.outcome', eq: 'cured' }] }, goto: 'favour' },
        bye('No deal.'),
      ],
    },
    deal: {
      id: 'deal',
      text: 'Pleasure. Box is by the tents; the teamsters are in the cages. Open them yourself, my lads will not stop you. And {name} — if Holloway asks, you have never seen my face.',
      effects: [
        { set: { redcowl: 'bargained' } }, { quest: { id: 'caravan', entry: 'redcowl_met' } },
        hist('bargained_redcowl', 'struck a bargain with Redcowl for the Coyle goods', ['kerchief', 'caravan'], 1, undefined, { holloway: { trust: -10 }, rav: { respect: 10 } }),
      ],
      choices: [bye('Done.')],
    },
    favour: {
      id: 'favour',
      text: 'Is it, now. The howling has been keeping my lads up at night, I will admit. ...Fine. The teamsters, for the favour. The box, you still pay for — fifty, for a friend.',
      effects: [{ set: { 'redcowl.releases': true } }],
      choices: [
        { text: 'Fifty, then.', when: { gold: { gte: 50 } }, locked: 'Fifty gold', effects: [{ gold: -50 }], goto: 'deal' },
        { text: 'Just the teamsters.', effects: [{ set: { redcowl: 'bargained' } }], end: true },
      ],
    },
    prisoners: {
      id: 'prisoners',
      text: 'The teamsters? They eat my food and pray a great deal. Fifty for their keep and they are yours.',
      choices: [
        { text: 'Pay fifty.', when: { gold: { gte: 50 } }, locked: 'Fifty gold', effects: [{ gold: -50 }, { set: { 'redcowl.releases': true } }], goto: 'released' },
        bye('Not today.'),
      ],
    },
    released: { id: 'released', text: 'Cages are over there. Mind the one on the end, he bites.', choices: [bye()] },
    pell: {
      id: 'pell',
      text: '...Give me that. "R., for the Coyle job." And to the clerk. And — "tell Holloway where they camp, after." After! Varrow, you soft-handed little —. Take your wagons. Take your teamsters. I have business in the Waystation.',
      effects: [
        { set: { redcowl: 'furious', 'caravan.pell': 'fled', 'redcowl.releases': true } }, { quest: { id: 'caravan', entry: 'redcowl_met' } },
        hist('turned_redcowl', 'showed Redcowl that Pell Varrow meant to sell him to the Watch', ['kerchief', 'caravan', 'cunning'], 2, undefined, { pell: { fear: 60 }, rav: { respect: 20 } }),
      ],
      choices: [bye()],
    },
    trick: {
      id: 'trick',
      text: 'The Watch. Holloway has not got the men to — (a whistle, from the ridge; everyone in the camp stops) — Pack it up! PACK IT UP! Leave the heavy stuff!',
      effects: [
        { set: { redcowl: 'tricked' } },
        hist('tricked_redcowl', 'bluffed the Kerchiefs out of their own camp', ['kerchief', 'cunning'], 2, { respect: 5 }, { rav: { respect: 25, affection: 10 } }),
      ],
      choices: [bye('Watch them run.')],
    },
  },
};

export const SNIB: Conversation = {
  npc: 'snib',
  entry: [{ when: { met: 'snib' }, node: 'hub' }, { node: 'first' }],
  nodes: {
    first: {
      id: 'first',
      text: 'Oi! OI! Surface-meat! No surface-meat past the pump! Foreman\'s orders! ...I\'m the foreman. Snib. What do you want? Quick. The pump does not pump itself. It does, actually. But quick.',
      choices: [
        { text: 'Your pump is poisoning the stream.', goto: 'poison' },
        { text: 'Your blasting ember came off the Coyle wagons.', when: { knows: 'clue.blasting_ember' }, once: 'ember', goto: 'ember' },
        { text: 'Pump it into the old sinkhole instead. Closer, and deeper.', when: { knows: 'arcana' }, badge: 'Arcana', goto: 'move' },
        { text: 'Grimtunnel sent me. He wants the outflow moved.', when: { any: [{ hasItem: 'grimtunnels_lamp' }, { hasTag: 'digger_lamp' }] }, badge: 'His lamp', goto: 'move' },
        { text: 'How much to shut it off for a week?', when: { knows: 'underworld' }, badge: 'Underworld', goto: 'bribe' },
        { text: 'Then I will shut it off myself.', effects: [{ set: { 'dig.hostile': true } }], end: true },
        bye(),
      ],
    },
    hub: {
      id: 'hub', text: 'You again. Pump is still pumping. Foreman is still foreman.',
      choices: [
        { text: 'Your blasting ember came off the Coyle wagons.', when: { knows: 'clue.blasting_ember' }, once: 'ember', goto: 'ember' },
        { text: 'Your pump is poisoning the stream.', goto: 'poison' },
        { text: 'Pump it into the sinkhole instead.', when: { knows: 'arcana' }, badge: 'Arcana', goto: 'move' },
        { text: 'Then I will shut it off myself.', effects: [{ set: { 'dig.hostile': true } }], end: true },
        bye(),
      ],
    },
    ember: {
      id: 'ember',
      text: 'Snib does not KNOW where powder comes from. Powder comes in a crate. Crate comes from the Kerchiefs. The Kerchiefs get crates from a man with soft hands and a big book. Boss pays the man. Man pays the Kerchiefs. Everybody is happy except wagons. ...Snib did not say any of this.',
      effects: [{ learn: 'grimtunnel' }, { quest: { id: 'below', status: 'active', entry: 'grimtunnel' } }, { rel: { npc: 'snib', fear: 10 } }],
      choices: [{ text: 'Soft hands, big book. I know who that is.', end: true }],
    },
    poison: {
      id: 'poison',
      text: 'Poison? It is slurry. Waste. Has to go somewhere. Boss says dig deeper, dig faster, the heart is hungry, the heart wants DOWN. Grimtunnel has a heart to feed and I have a pump to run. The wolves can drink somewhere else.',
      effects: [{ learn: ['root_cause', 'grimtunnel'], text: 'The Dig is poisoning the stream.' }, { quest: { id: 'beasts', entry: 'root_cause' } }, { quest: { id: 'below', status: 'active', entry: 'grimtunnel' } }],
      choices: [
        { text: 'Pump it into the sinkhole instead.', when: { knows: 'arcana' }, badge: 'Arcana', goto: 'move' },
        { text: 'How much to shut it off?', when: { knows: 'underworld' }, badge: 'Underworld', goto: 'bribe' },
        { text: 'Then I will shut it off myself.', effects: [{ set: { 'dig.hostile': true } }], end: true },
        bye(),
      ],
    },
    move: {
      id: 'move',
      text: '...The sinkhole. Deeper. Deeper is good. Boss likes deeper. Fine! FINE. Lads! Turn the pipe! Snib has had an idea!',
      effects: [
        { set: { 'dig.pump': 'moved' } }, { quest: { id: 'beasts', entry: 'pump_moved' } },
        hist('moved_pump', 'talked the diggers into moving their outflow away from the stream', ['beasts', 'cunning'], 1, { respect: 5 }, { wenna: { respect: 20 }, maeca: { respect: 15 } }),
      ],
      choices: [bye('Good idea, Snib.')],
    },
    bribe: {
      id: 'bribe',
      text: 'A week? Snib could lose a week. Snib could lose a week for forty. The pump could break. Pumps break.',
      choices: [
        { text: 'Forty gold.', when: { gold: { gte: 40 } }, locked: 'Forty gold', effects: [{ gold: -40 }, { set: { 'dig.pump': 'moved' } }, { quest: { id: 'beasts', entry: 'pump_moved' } }], goto: 'bribed' },
        bye('Never mind.'),
      ],
    },
    bribed: { id: 'bribed', text: 'Oh no. Oh dear. The pump has broken. What a shame. Snib will be SO sad.', choices: [bye()] },
  },
};

export const SURVIVOR: Conversation = {
  npc: 'survivor',
  entry: [{ node: 'first' }],
  nodes: {
    first: {
      id: 'first',
      text: 'It moved. The dark moved. We dug, and we dug, and it MOVED. The others went down to see. Grimtunnel says it is ours now. Grimtunnel says it is hungry. Grimtunnel brought it a heart.',
      effects: [{ quest: { id: 'below', status: 'active', entry: 'survivor' } }],
      choices: [
        { text: 'What moved?', goto: 'what' },
        bye('Leave him to it.'),
      ],
    },
    what: {
      id: 'what',
      text: 'Down there. Under the one that is dead. There is another. There is always another. Take the map, take it, I do not want to know where the tunnels go any more.',
      effects: [{ if: { not: { hasItem: 'map_fragment' } }, then: [{ give: 'map_fragment' }, { quest: { id: 'below', entry: 'map' } }] }],
      choices: [bye()],
    },
  },
};

export const JORY: Conversation = {
  npc: 'jory',
  entry: [{ node: 'first' }],
  nodes: {
    first: {
      id: 'first',
      text: 'You are the one who opened the cage. I — thank you. Uncle Harlan has not stopped crying. It was not wolves, you know. A clerk at the gate said the road was shut, and sent us down the forest track, and they were waiting.',
      effects: [{ quest: { id: 'caravan', entry: 'clerk_turned' } }, { rel: { npc: 'jory', affection: 40, trust: 40 }, quiet: true }],
      choices: [bye('Rest, Jory.')],
    },
  },
};

export const VERGE_CONVOS: Record<string, Conversation> = { greymuzzle: GREYMUZZLE, redcowl: REDCOWL, snib: SNIB, survivor: SURVIVOR, jory: JORY };
