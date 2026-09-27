import type { DailyRule, SocialLinks } from '@/world/simulation';
import type { Effect } from '@/world/logic';

/* How the world moves while the survivor sleeps.
 *
 * Every rule is a condition over the world and what happens if it holds.
 * Together they are the clocks the design promised: the wolves escalate
 * while nobody deals with the cause, the caged survivors do not wait
 * forever, a cured stream heals over days, factions push where nobody
 * pushes back. The morning report is written from the `report` lines. */

const h = (id: string, text: string, tags: string[], spread: number): Effect => ({ history: { id, text, tags, spread } });

export const RULES: DailyRule[] = [
  /* ------------------------------------------------ the beast problem -- */
  { id: 'beasts.escalate', when: { all: [{ not: { fact: 'beasts.outcome', exists: true } }, { fact: 'prologue.done', eq: true }] }, effect: { add: { 'beasts.severity': 1 } } },
  { id: 'beasts.caravans', once: true, when: { fact: 'beasts.severity', gte: 3 }, effect: { set: { 'road.dangerous': true } },
    report: 'Another cart turned back on the Old Road. The drover says the wolves followed him to the gate.' },
  { id: 'beasts.farm', once: true, when: { all: [{ fact: 'beasts.severity', gte: 5 }, { not: { fact: 'beasts.outcome', exists: true } }] },
    effect: [{ set: { 'tam.farm': 'raided' } }, h('farm_raided', 'Tam\'s father\'s farm was raided by the Pack', ['beasts'], 2), { rel: { npc: 'tam', trust: -10 }, quiet: true }],
    report: 'Tam\'s father did not come in last night. Holloway has sent two men out to the farm.' },
  { id: 'beasts.gate', once: true, when: { all: [{ fact: 'beasts.severity', gte: 7 }, { not: { fact: 'beasts.outcome', exists: true } }] },
    effect: [{ set: { 'wolves.at_gate': true } }, { set: { 'beasts.outcome': 'ignored' } }, { quest: { id: 'beasts', status: 'failed', outcome: 'ignored' } }],
    report: 'Wolves at the east gate in the night, a dozen of them, sick and bold. The Watch lost a man.' },
  // A stopped pump heals the stream, slowly.
  { id: 'stream.heal', when: { any: [{ fact: 'dig.pump', eq: 'broken' }, { fact: 'dig.pump', eq: 'moved' }, { fact: 'dig.pump', eq: 'blown' }] }, effect: { add: { 'blight.days_clean': 1 } } },
  { id: 'stream.clear', once: true, when: { all: [{ fact: 'blight.days_clean', gte: 2 }, { not: { fact: 'beasts.outcome', eq: 'slaughtered' } }] },
    effect: [{ set: { 'beasts.outcome': 'cured', 'blight.level': 0 } }, { quest: { id: 'beasts', status: 'resolved', outcome: 'cured' } },
      h('stream_cleared', 'stopped the poison in the Thornhollow stream', ['deed', 'beasts'], 2)],
    report: 'Wenna came in at dawn, muddy to the knees: the stream is running clear. The Pack has gone back into the deep wood.' },
  // A lie about the wolves lasts exactly as long as the wolves stay quiet.
  { id: 'lie.found', once: true, when: { all: [{ fact: 'beasts.told_holloway', eq: true }, { not: { fact: 'beasts.outcome', exists: true } }] },
    effect: [{ tell: { npc: 'holloway', event: 'lied_to_holloway' } }, { set: { 'holloway.lied_to': true } }],
    report: 'A drover came in at dawn with his arm torn open, wolves on the east road. Captain Holloway listened to him, and then looked for you.' },
  { id: 'wolves.gone', once: true, when: { all: [{ fact: 'beasts.population', lte: 5 }, { not: { fact: 'beasts.outcome', exists: true } }] },
    effect: [{ set: { 'beasts.outcome': 'slaughtered' } }, { quest: { id: 'beasts', status: 'resolved', outcome: 'slaughtered' } }],
    report: 'No howling last night. None at all. Brannoc says it is the quietest he has ever heard the Verge.' },

  /* ---------------------------------------------- the missing caravan -- */
  { id: 'caravan.clock', when: { all: [{ not: { fact: 'caravan.survivors', exists: true } }, { fact: 'prologue.done', eq: true }] }, effect: { add: { 'caravan.days': 1 } } },
  { id: 'caravan.starve', once: true, when: { all: [{ fact: 'caravan.days', gte: 4 }, { not: { fact: 'caravan.survivors', exists: true } }] },
    effect: [{ set: { 'caravan.survivors': 'dead' } }, { quest: { id: 'caravan', entry: 'survivors_dead' } },
      h('prisoners_died', 'let the Coyle teamsters die in the Kerchief cages', ['caravan'], 1), { rel: { npc: 'harlan', affection: -20 }, quiet: true }],
    report: 'Word from the Old Road: the Kerchiefs have stopped feeding their prisoners. Harlan has not come out of his shop.' },
  { id: 'kerchief.raid', when: { all: [{ fact: 'road.dangerous', eq: true }, { not: { fact: 'redcowl', exists: true } }, { day: { gte: 4 } }] },
    effect: { add: { 'kerchief.raids': 1 } }, report: 'The Kerchiefs stopped a pedlar on the Old Road and took his boots. The Watch is stretched thin.' },

  /* ------------------------------------------------ the chapter's end -- */
  { id: 'chapter.ready', once: true, when: { all: [{ fact: 'beasts.outcome', exists: true }, { any: [{ fact: 'caravan.survivors', exists: true }, { fact: 'caravan.cargo', exists: true }] }] },
    effect: { set: { 'chapter.ready': true } }, report: 'A note under your door, in violet ink: "Come and have your fortune read. No charge, this once. — V."' },

  /* ------------------------------------------------- the thing below -- */
  { id: 'dig.deeper', when: { all: [{ fact: 'prologue.done', eq: true }, { not: { fact: 'dig.pump', eq: 'blown' } }] }, effect: { add: { 'dig.depth': 1 } } },
  { id: 'tremor', once: true, when: { fact: 'dig.depth', gte: 3 }, effect: [{ set: { 'tremor.felt': true } }, { quest: { id: 'below', entry: 'tremor' } }],
    report: 'The cups rattled on Rook\'s shelves in the night. Nobody could say why. Chid says the ground turned over in its sleep.' },
];

/** Who talks to whom: how news travels. The innkeeper hears everything. */
export const SOCIAL: SocialLinks = {
  rook: ['holloway', 'rav', 'chid', 'harlan', 'wenna', 'brannoc'],
  holloway: ['rook', 'harlan', 'vonnra', 'brannoc'],
  harlan: ['holloway', 'rook', 'pell', 'brannoc'],
  pell: ['harlan', 'rav', 'vonnra'],
  rav: ['rook', 'pell'],
  maeca: ['wenna', 'tam', 'brannoc'],
  wenna: ['maeca', 'chid', 'tam', 'rook'],
  tam: ['maeca', 'wenna'],
  chid: ['rook', 'wenna'],
  brannoc: ['harlan', 'holloway', 'maeca', 'rook'],
  vonnra: ['holloway', 'pell'],
};
