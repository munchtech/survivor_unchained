import { fact, test, type Ctx } from '@/world/logic';
import { QUESTS } from './quests';

/* What to do next, for the corner of the screen.
 *
 * The journal says what happened; this says where to go. Each quest's next
 * step is worked out from the same facts the quest is written in, so it
 * follows whichever way the survivor went about it: found the pipe before
 * Wenna asked, freed the cages before hearing of the Roost. Steps name a
 * place and, where it matters, the person. Optional leads come after the
 * main step, and the clocks (the cages do not wait) are said out loud.
 *
 * The Verge, for the directions: the Old Road runs west to east through it;
 * the stream comes down from the Dig in the north-east, turns green at the
 * wood's heart and crosses the road; Wolf Hollow is north, the Roost in the
 * ravine to the south-east. */

export interface Step { text: string; done?: boolean; optional?: boolean }
export interface Tracked { id: string; title: string; tone: 'main' | 'side' | 'tutorial'; steps: Step[] }

const TRACKED = ['beasts', 'caravan'];

export function objectives(c: Ctx): Tracked[] {
  const out: Tracked[] = [];
  for (const id of TRACKED) {
    if (c.world.quests[id]?.status !== 'active') continue;
    const steps = (id === 'beasts' ? beasts : caravan)(c);
    if (steps.length) out.push({ id, title: QUESTS[id].name, tone: 'main', steps: steps.slice(0, 3) });
  }
  // Just arrived, and nobody has told you anything yet.
  if (!out.length && fact(c.world, 'prologue.done') && TRACKED.every((id) => !c.world.quests[id])) {
    out.push({
      id: 'arrival', title: 'The Waystation', tone: 'tutorial', steps: [
        { text: 'Mother Rook, outside the Last Lamp, hears all the talk' },
        { text: 'Anyone marked ! has something to tell you', optional: true },
      ],
    });
  }
  return out;
}

function helpers(c: Ctx, quest: string) {
  return {
    knows: (k: string) => test({ knows: k }, c),
    has: (item: string) => test({ hasItem: item }, c),
    entry: (e: string) => test({ quest: { id: quest, entry: e } }, c),
    f: (key: string) => fact(c.world, key),
  };
}

function beasts(c: Ctx): Step[] {
  const { knows, has, entry, f } = helpers(c, 'beasts');
  const pump = f('dig.pump');
  const main: Step[] = [];
  if (pump === 'broken' || pump === 'moved' || pump === 'blown') main.push({ text: 'The slurry has stopped. Give the stream a few days to run clear' });
  else if (knows('root_cause')) main.push({ text: 'Stop the slurry at the Dig, up the stream in the north-east of the Verge' });
  else if (knows('clue.analysis')) main.push({ text: 'Follow the stream up into the north-east of the Verge, to whoever is dumping the slurry' });
  else if (has('stream_sample')) main.push({ text: 'Take the bottle of green water to Wenna' });
  else if (entry('wenna_request') || knows('clue.green_stream') || knows('clue.pipe') || knows('hint.stream')) main.push({ text: 'Fill a bottle at the green water in the Verge, and take it to Wenna' });
  else if (knows('clue.sick_wolf')) main.push({ text: 'The wolves are sick. Ask Old Wenna, the herbalist, what could do that' });
  else main.push({ text: 'Find out what is wrong with the wolves: ask around town, or look in the Verge' });
  const opt: Step[] = [];
  const early = !knows('clue.sick_wolf') && !knows('clue.green_stream') && !knows('clue.pipe');
  if (early && !entry('holloway_bounty')) opt.push({ text: 'Captain Holloway, on the square, is paying for wolves', optional: true });
  if (early && !entry('maeca_theory')) opt.push({ text: 'Maeca, the hunter by the east gate, thinks the wolves are running from something', optional: true });
  if (knows('hint.greymuzzle') && !entry('greymuzzle_met') && f('greymuzzle') !== 'dead') opt.push({ text: 'Greymuzzle, the old alpha, keeps to Wolf Hollow, north of the Old Road', optional: true });
  if (entry('holloway_bounty') && !entry('bounty_claimed') && (has('wolf_pelt') || has('greymuzzle_fang'))) opt.push({ text: 'Captain Holloway, on the square, pays for pelts', optional: true });
  return [...main, ...opt];
}

function caravan(c: Ctx): Step[] {
  const { knows, has, entry, f } = helpers(c, 'caravan');
  const survivors = f('caravan.survivors'), cargo = f('caravan.cargo');
  const main: Step[] = [];
  if (!survivors) {
    const days = Number(f('caravan.days') ?? 0);
    const clock = days >= 3 ? ' They will not last another night.' : days >= 2 ? ' They have a night or two left, no more.' : '';
    if (entry('roost_found')) main.push({ text: `Free the prisoners from the cages at Redcowl's Roost.${clock}` });
    else if (entry('ruts') || knows('hint.roost')) main.push({ text: `Find the Kerchief camp in the ravine, south-east in the Verge.${clock}` });
    else if (entry('wreck')) main.push({ text: `Follow the wheel ruts from the wreck, off the road and into the trees.${clock}` });
    else main.push({ text: `Search the Old Road through the Verge for the Coyle wagons.${clock}` });
  } else if (survivors === 'rescued' && !test({ npcFlag: { npc: 'harlan', key: 'once:jory', eq: true } }, c)) {
    main.push({ text: 'Tell Harlan Coyle that Jory is alive' });
  }
  if (!cargo && survivors) {
    if (has('coyle_strongbox')) main.push({ text: 'Take the Coyle strongbox back to Harlan, or keep it' });
    else if (!f('caravan.box_taken')) main.push({ text: 'The Coyle strongbox is still in the Roost, with the rest of the cargo' });
  }
  const opt: Step[] = [];
  if (!test({ met: 'harlan' }, c)) opt.push({ text: 'Harlan Coyle, outside Coyle Trading, is offering a reward', optional: true });
  if (has('pell_ledger') && !entry('pell_exposed') && !entry('pell_joined')) opt.push({ text: 'Pell Varrow\'s ledger: show it to Harlan, or to Captain Holloway', optional: true });
  else if (entry('clerk_turned') && !entry('pell_ledger')) opt.push({ text: 'Someone paid the toll clerk. Pell Varrow\'s warehouse may say who', optional: true });
  else if (entry('wreck') && !entry('clerk_turned')) opt.push({ text: 'Who sent the wagons off the road? Try the east-gate guard, or the tavern', optional: true });
  if (entry('manifest') && !entry('blasting_ember')) opt.push({ text: 'Ask Harlan about the crates marked "B.E." in the manifest', optional: true });
  return [...main, ...opt];
}
