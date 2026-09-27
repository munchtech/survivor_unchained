import type { Cond } from '@/world/logic';

/* What is on each person's mind, for the journal's People page.
 *
 * The first line whose condition holds is the one shown, so the list runs
 * from the most particular (what you did to them) down to who they are
 * when nothing much has happened. It reads the same facts the dialogue
 * does, so the page changes as the town does. */

export interface Concern { text: string; when?: Cond; died?: boolean }

export const CONCERNS: Record<string, Concern[]> = {
  rook: [
    { when: { fact: 'caravan.survivors', eq: 'rescued' }, text: 'Has put Jory Coyle in the good room, and will not take Harlan\'s money for it.' },
    { when: { fact: 'wolves.at_gate', eq: true }, text: 'Bars the inn door at dusk now, and sits up with the lamp.' },
    { text: 'Keeps the Last Lamp lit, the beds aired and the gossip moving.' },
  ],
  holloway: [
    { when: { all: [{ fact: 'holloway.lied_to', eq: true }, { not: { fact: 'holloway.lie_settled', exists: true } }] }, text: 'Knows you lied to him about the wolves, and is deciding what that costs.' },
    { when: { fact: 'beasts.outcome', eq: 'slaughtered' }, text: 'The bounty is paid and the road is quiet. He does not trust the quiet.' },
    { when: { fact: 'beasts.outcome', eq: 'allied' }, text: 'Has heard you run with wolves. Has doubled the gate, just in case.' },
    { when: { fact: 'wolves.at_gate', eq: true }, text: 'Had wolves at his gate. Has not slept since.' },
    { when: { quest: { id: 'beasts', status: 'active' } }, text: 'Wants the wolves dealt with before the Watch has to bury anyone else.' },
    { text: 'Holds the Waystation with too few men and too little sleep.' },
  ],
  maeca: [
    { when: { fact: 'beasts.outcome', eq: 'allied' }, text: 'Runs with the Pack now, and has stopped pretending she does not.' },
    { when: { fact: 'beasts.outcome', eq: 'slaughtered' }, text: 'Has not hunted since the wolves were killed. Drinks at the tavern instead.' },
    { when: { fact: 'beasts.outcome', eq: 'cured' }, text: 'Says the deep wood sounds right again.' },
    { text: 'Thinks the wolves are running from something, and means to find it.' },
  ],
  chid: [
    { died: true, text: 'Lights a candle for you each morning, since the day you came back through his door.' },
    { when: { fact: 'shrine.lit', eq: true }, text: 'The shrine lamp burns again. He has not stopped smiling.' },
    { text: 'Tends a shrine nobody visits and a lamp nobody lights.' },
  ],
  rav: [
    { when: { fact: 'caravan.pell', eq: 'exposed' }, text: 'Is enjoying Pell Varrow\'s fall more than a physician should.' },
    { when: { fact: 'caravan.cargo', eq: 'sold' }, text: 'Knows exactly where the Coyle cargo went. Will not say it twice.' },
    { text: 'Patches up anybody, asks nobody anything, and remembers every answer he did not ask for.' },
  ],
  harlan: [
    { when: { any: [{ fact: 'caravan.cargo', eq: 'kept' }, { fact: 'caravan.cargo', eq: 'sold' }] }, text: 'Has written off his strongbox, and says your name when he says it.' },
    { when: { fact: 'caravan.survivors', eq: 'rescued' }, text: 'Has Jory back. Keeps finding reasons to touch his shoulder.' },
    { when: { fact: 'caravan.survivors', eq: 'dead' }, text: 'Has closed the shutters on Coyle Trading and does not answer the door.' },
    { when: { fact: 'caravan.days', gte: 3 }, text: 'Has stopped watching the road. Sits outside the tavern instead.' },
    { when: { fact: 'caravan.days', gte: 1 }, text: 'Watches the east road from the gate, every morning, before he eats.' },
    { text: 'His caravan never came. His nephew was driving it.' },
  ],
  pell: [
    { when: { fact: 'caravan.pell', eq: 'fled' }, text: 'Gone. His warehouse is empty and his debts are not.' },
    { when: { fact: 'caravan.pell', eq: 'exposed' }, text: 'Exposed. Holloway has him watched, and the town will not look at him.' },
    { when: { fact: 'caravan.pell', eq: 'ally' }, text: 'Counts you among his investments.' },
    { when: { fact: 'dig.sold', eq: true }, text: 'Paid you for the Dig, and is making it pay him back.' },
    { text: 'Buys, sells, stores, and knows what everyone owes.' },
  ],
  wenna: [
    { when: { fact: 'beasts.outcome', eq: 'cured' }, text: 'Says she can die happy now, and then keeps living, to spite everyone.' },
    { when: { fact: 'beasts.outcome', eq: 'exploited' }, text: 'Knows who was paid to clean the stream. Has said so, loudly.' },
    { when: { quest: { id: 'beasts', entry: 'clue.analysis' } }, text: 'Knows what is in the stream, and is angry about it.' },
    { text: 'Old, sharp, and certain the animals were never like this.' },
  ],
  tam: [
    { when: { fact: 'tam.farm', eq: 'raided' }, text: 'His family\'s farm was raided. He sleeps in the Watch-house now.' },
    { when: { fact: 'beasts.outcome', eq: 'cured' }, text: 'Was right about the stream, and has told everyone.' },
    { text: 'Saw wolves drink from the stream and fall down. Nobody believes him.' },
  ],
  brannoc: [
    { when: { quest: { id: 'beasts', entry: 'pelts_sold' } }, text: 'Buys wolf pelts and does not ask where they came from.' },
    { text: 'Works iron from dawn to dark and says about four words a day.' },
  ],
  vonnra: [
    { when: { fact: 'chapter.done', eq: true }, text: 'Has read your fortune. Says the rest is not written yet, which she finds irritating.' },
    { when: { quest: { id: 'vault', entry: 'vonnra_refuses' } }, text: 'Will not speak of the black door in the hillside. Not for money.' },
    { text: 'Keeps the toll, reads the cards, and misses nothing that comes through the east gate.' },
  ],
  keegan: [
    { when: { knows: 'lore.warden' }, text: 'Has found in you someone who has read the old books. Or at least looked at the pictures.' },
    { text: 'Guards the north gate against something only he can see.' },
  ],
  jory: [
    { text: 'Home, and trying not to talk about the cage.' },
  ],
  redcowl: [
    { when: { history: 'killed_redcowl' }, text: 'Dead, in his own camp.' },
    { text: 'Would rather talk than bleed. Says so, anyway.' },
  ],
};
