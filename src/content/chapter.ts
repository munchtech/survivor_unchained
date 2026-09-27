import type { WorldState, NpcState } from '@/world/state';
import type { CharacterData } from '@/rpg/character';
import { QUESTS } from './quests';
import { NPCS } from './npcs';
import { attitude } from '@/world/logic';

/* The end of the chapter, read back from the world.
 *
 * Nothing here is stored: every line is worked out from the facts, the
 * journal, the people and the history, so two survivors who took different
 * roads close the same chapter on two different pages. */

export type Tone = 'good' | 'grey' | 'bad' | 'open';

export interface Thread { id: string; name: string; verdict: string; tone: Tone; outcome: string; beats: string[] }
export interface Remembered { id: string; name: string; role: string; regard: string; knows?: string; warmth: number }
export interface ChapterSummary {
  /** "Wren, who cleared the water" */
  epithet: string;
  threads: Thread[];
  open: Array<{ id: string; name: string; line: string }>;
  people: Remembered[];
  deeds: string[];
  stats: Array<{ label: string; value: string | number }>;
}

const pick = (w: WorldState, quest: string, ids: string[]) =>
  (w.quests[quest]?.entries ?? []).filter((e) => ids.includes(e)).map((e) => QUESTS[quest].entries[e]).filter(Boolean);

function beasts(w: WorldState): Thread {
  const f = w.facts, q = QUESTS.beasts;
  const out = f['beasts.outcome'] as string | undefined;
  const v: Record<string, [string, Tone]> = {
    cured: ['Cured at the source', 'good'],
    allied: ['Ran with the Pack', 'grey'],
    slaughtered: [f.greymuzzle === 'dead' ? 'Put down, alpha and all' : 'Put down', 'grey'],
    ignored: ['Left to fester', 'bad'],
    exploited: ['Settled, for a price', 'grey'],
  };
  const [verdict, tone] = out ? v[out] ?? ['Settled', 'grey'] : ['Not yet settled', 'open' as Tone];
  return {
    id: 'beasts', name: q.name, verdict, tone,
    outcome: (out && q.outcomes?.[out]) || 'The wolves are still out there, and still sick.',
    beats: pick(w, 'beasts', ['greymuzzle_met', 'root_cause', 'dig_sold', 'pump_moved', 'pump_broken', 'pump_blown', 'alpha_dead', 'bounty_claimed', 'told_holloway', 'pelts_sold', 'pack_led']),
  };
}

function caravan(w: WorldState): Thread {
  const f = w.facts, q = QUESTS.caravan;
  const surv = f['caravan.survivors'] as string | undefined, cargo = f['caravan.cargo'] as string | undefined;
  let verdict = 'Not yet found', tone: Tone = 'open', outcome = 'Jory and the others are still somewhere in the Verge. The clock is running.';
  if (surv === 'rescued' && cargo === 'returned') { verdict = 'Brought home'; tone = 'good'; outcome = q.outcomes!.returned; }
  else if (surv === 'rescued' && (cargo === 'sold' || cargo === 'kept')) { verdict = 'Rescued, and robbed'; tone = 'grey'; outcome = q.outcomes!.kept; }
  else if (surv === 'rescued' && cargo === 'with_kerchiefs') { verdict = 'The teamsters freed'; tone = 'good'; outcome = `Jory is home. ${q.outcomes!.with_kerchiefs}`; }
  else if (surv === 'rescued' && cargo === 'lost') { verdict = 'The teamsters freed'; tone = 'good'; outcome = 'Jory is home. The cargo burned with the Roost.'; }
  else if (surv === 'rescued') { verdict = 'The teamsters freed'; tone = 'good'; outcome = 'Jory is home. The cargo is another story.'; }
  else if (surv === 'dead' && cargo === 'returned') { verdict = 'The goods, not the men'; tone = 'grey'; outcome = 'Harlan has his strongbox back. He would give it all to have Jory.'; }
  else if (surv === 'dead' && (cargo === 'sold' || cargo === 'kept')) { verdict = 'Too late, and robbed'; tone = 'bad'; outcome = 'The prisoners did not come home, and the cargo went where you took it.'; }
  else if (surv === 'dead') { verdict = 'Too late'; tone = 'bad'; outcome = 'The prisoners in the Roost did not come home.'; }
  else if (cargo === 'returned') { verdict = 'The goods, not the men'; tone = 'grey'; outcome = q.outcomes!.returned; }
  const beats = pick(w, 'caravan', ['roost_found', 'redcowl_met', 'survivors_freed', 'survivors_dead', 'cargo_returned', 'cargo_sold', 'cargo_kept', 'cargo_lost', 'cargo_moved', 'pell_exposed', 'pell_joined']);
  if (f.redcowl === 'tricked') beats.push('You bluffed the Kerchiefs out of their own camp.');
  if (f.redcowl === 'dead') beats.push('Redcowl is dead.');
  if (f['caravan.pell'] === 'fled') beats.push('Pell Varrow fled the Waystation in the night.');
  return { id: 'caravan', name: q.name, verdict, tone, outcome, beats };
}

function epithet(ch: CharacterData, w: WorldState) {
  const f = w.facts;
  if (f['beasts.outcome'] === 'allied') return `${ch.name}, who runs with wolves`;
  if (f['caravan.pell'] === 'ally') return `${ch.name}, in Pell Varrow's ledger`;
  if (f['beasts.outcome'] === 'exploited') return `${ch.name}, who sold the cure`;
  if (f['caravan.cargo'] === 'sold') return `${ch.name}, who sold the Coyle strongbox`;
  if (f['caravan.cargo'] === 'kept') return `${ch.name}, who kept the Coyle strongbox`;
  if (f['beasts.outcome'] === 'cured' && f['caravan.survivors'] === 'rescued') return `${ch.name}, who cleared the water and opened the cages`;
  if (f['beasts.outcome'] === 'cured') return `${ch.name}, who cleared the water`;
  if (f['caravan.survivors'] === 'rescued') return `${ch.name}, who opened the cages`;
  if (f['beasts.outcome'] === 'slaughtered') return `${ch.name}, the wolf-killer`;
  if (ch.traits.includes('risen_once')) return `${ch.name}, who would not stay dead`;
  return `${ch.name}, late of the Low Ford road`;
}

export function chapterSummary(ch: CharacterData, w: WorldState): ChapterSummary {
  const open = (['vault', 'below'] as const).map((id) => {
    const q = w.quests[id];
    const last = q?.entries[q.entries.length - 1];
    return { id, name: QUESTS[id].name, line: last ? QUESTS[id].entries[last] : QUESTS[id].summary };
  });
  const people = Object.values(NPCS)
    .map((d) => ({ d, s: w.npcs[d.id] as NpcState | undefined }))
    .filter(({ s }) => s?.flags.met)
    .map(({ d, s }) => {
      const weight = Math.abs(s!.trust) + Math.abs(s!.affection) + Math.abs(s!.respect) + Math.abs(s!.fear);
      const latest = [...s!.memories].reverse().map((m) => w.history.find((h) => h.id === m)).find((h) => h && h.id !== 'fortune_read');
      return { weight, r: { id: d.id, name: d.name, role: s!.alive ? d.role : `${d.role}, dead`, regard: attitude(s!), knows: latest?.text, warmth: s!.trust + s!.affection } };
    })
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 4)
    .map((x) => x.r);
  const deeds = w.history.filter((h) => h.id !== 'fortune_read').slice(-5).reverse().map((h) => h.text);
  return {
    epithet: epithet(ch, w),
    threads: [beasts(w), caravan(w)],
    open, people, deeds,
    stats: [
      { label: 'Days', value: w.day },
      { label: 'Level', value: ch.level },
      { label: 'Slain', value: ch.stats.kills },
      { label: 'Falls', value: ch.stats.deaths },
      { label: 'Gold earned', value: ch.stats.goldEarned },
    ],
  };
}
