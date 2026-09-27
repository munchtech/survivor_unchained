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

/** When both the teamsters' fate and the cargo's are known, the quest is settled. */
export const CARAVAN_SETTLE: Effect = { if: { all: [{ fact: 'caravan.survivors', exists: true }, { fact: 'caravan.cargo', exists: true }] }, then: { quest: { id: 'caravan', status: 'resolved' } } };

export const RULES: DailyRule[] = [
  /* ------------------------------------------------ the beast problem -- */
  { id: 'beasts.escalate', when: { all: [{ not: { fact: 'beasts.outcome', exists: true } }, { fact: 'prologue.done', eq: true }] }, effect: { add: { 'beasts.severity': 1 } } },
  { id: 'beasts.howl', once: true, when: { all: [{ fact: 'beasts.severity', gte: 2 }, { not: { fact: 'beasts.outcome', exists: true } }] }, effect: [],
    report: 'The wolves howled close to the walls last night. Tam says one of them was coughing.' },
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
  // Fixed, but for Pell's profit: the stream still clears; the story is different.
  { id: 'stream.clear_sold', once: true, when: { all: [{ fact: 'blight.days_clean', gte: 2 }, { fact: 'dig.pell_cut', eq: true }, { not: { fact: 'beasts.outcome', exists: true } }] },
    effect: [{ set: { 'beasts.outcome': 'exploited' } }, { quest: { id: 'beasts', status: 'resolved', outcome: 'exploited' } }],
    report: 'The stream is running clear. Wenna says so, and does not look at you when she says it. Pell Varrow was seen coming back from the Verge, whistling.' },
  { id: 'stream.clear', once: true, when: { all: [{ fact: 'blight.days_clean', gte: 2 }, { not: { fact: 'beasts.outcome', eq: 'slaughtered' } }, { not: { fact: 'dig.pell_cut', eq: true } }] },
    effect: [{ set: { 'beasts.outcome': 'cured' } }, { quest: { id: 'beasts', status: 'resolved', outcome: 'cured' } },
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
  // The clock, felt: what the town is like while nobody has found them.
  { id: 'caravan.watch', once: true, when: { all: [{ fact: 'caravan.days', gte: 1 }, { not: { fact: 'caravan.survivors', exists: true } }] }, effect: [],
    report: 'Harlan Coyle was at the east gate before dawn, watching the Old Road. He did not eat.' },
  { id: 'caravan.despair', once: true, when: { all: [{ fact: 'caravan.days', gte: 3 }, { not: { fact: 'caravan.survivors', exists: true } }] }, effect: { rel: { npc: 'harlan', trust: -5 }, quiet: true },
    report: 'Harlan has stopped watching the road. Rook says he sat in the tavern until she put the lamps out, and asked her whether anyone was even looking.' },
  // The strongbox, once it leaves the Roost with you: Harlan hears, and waits.
  { id: 'caravan.box_clock', when: { all: [{ fact: 'caravan.box_taken', eq: true }, { not: { fact: 'caravan.cargo', exists: true } }] }, effect: { add: { 'caravan.box_days': 1 } } },
  { id: 'caravan.box_asks', once: true, when: { all: [{ fact: 'caravan.box_days', gte: 1 }, { not: { fact: 'caravan.cargo', exists: true } }] }, effect: [],
    report: 'Harlan asked in the tavern whether anyone had seen a Coyle strongbox. Rook says he did not look at your door when he said it. He did not need to.' },
  { id: 'caravan.box_kept', once: true, when: { all: [{ fact: 'caravan.box_days', gte: 3 }, { not: { fact: 'caravan.cargo', exists: true } }] },
    effect: [{ set: { 'caravan.cargo': 'kept' } }, { quest: { id: 'caravan', entry: 'cargo_kept', outcome: 'kept' } },
      h('kept_cargo', 'kept the Coyle strongbox for themselves', ['caravan', 'greed'], 2), { rel: { npc: 'harlan', trust: -40, affection: -30 }, quiet: true }],
    report: 'Harlan Coyle has written the strongbox off, and says so to anyone who will listen. He says your name when he says it.' },
  // Left in the Roost once the prisoners' fate is settled: the Kerchiefs do not
  // sit on stolen goods (unless there are no Kerchiefs left to move them).
  { id: 'caravan.box_waits', when: { all: [{ fact: 'caravan.survivors', exists: true }, { not: { fact: 'caravan.box_taken', eq: true } }, { not: { fact: 'caravan.cargo', exists: true } }, { not: { fact: 'redcowl', eq: 'dead' } }, { not: { fact: 'roost.cleared', eq: true } }] },
    effect: { add: { 'caravan.box_left': 1 } } },
  { id: 'caravan.box_moved', once: true, when: { all: [{ fact: 'caravan.box_left', gte: 3 }, { not: { fact: 'caravan.box_taken', eq: true } }, { not: { fact: 'caravan.cargo', exists: true } }] },
    effect: [{ set: { 'caravan.cargo': 'with_kerchiefs' } }, { quest: { id: 'caravan', entry: 'cargo_moved', outcome: 'with_kerchiefs' } }],
    report: 'A pedlar off the south road was selling Coyle cloth at half its price. Harlan bought a bolt of his own goods back and did not say a word.' },
  // Both halves known: the Missing Caravan is settled, one way or another.
  { id: 'caravan.settled', once: true, when: { all: [{ fact: 'caravan.survivors', exists: true }, { fact: 'caravan.cargo', exists: true }] }, effect: CARAVAN_SETTLE },
  { id: 'kerchief.prices', once: true, when: { fact: 'kerchief.raids', gte: 2 }, effect: [],
    report: 'Harlan has put his prices up. So has everyone. Nothing is coming down the Old Road that the Kerchiefs have not had first.' },
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
