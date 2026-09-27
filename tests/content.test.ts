import { describe, it, expect } from 'vitest';
import { CONVOS } from '@/content/dialogue';
import { QUESTS } from '@/content/quests';
import { ITEMS } from '@/content/items';
import { TRAITS } from '@/content/archetypes';
import { SHOPS } from '@/content/shops';
import { RULES } from '@/content/rules';
import { ENEMIES } from '@/content/enemies';
import { NPCS, OUTSIDERS, SPEAKERS } from '@/content/npcs';
import type { Cond, Effect } from '@/world/logic';

/* The content is data; these tests read all of it and check that every
 * reference points at something real. A typo in a quest entry id is a
 * silent bug in play; here it is a red line. */

const ACTIONS = new Set(['trade', 'rest', 'stash', 'sell', 'craft', 'leave', 'fortune', 'bounty', 'sellpelts', 'reforge', 'travel_verge']);

function walkEffects(e: Effect | Effect[] | undefined, fn: (e: Effect) => void) {
  if (!e) return;
  if (Array.isArray(e)) { e.forEach((x) => walkEffects(x, fn)); return; }
  fn(e);
  if ('if' in e) { walkEffects(e.then, fn); walkEffects(e.else, fn); }
  if ('later' in e) walkEffects(e.later.effect as Effect, fn);
}

function walkConds(c: Cond | undefined, fn: (c: Cond) => void) {
  if (!c) return;
  fn(c);
  if ('all' in c) c.all.forEach((x) => walkConds(x, fn));
  if ('any' in c) c.any.forEach((x) => walkConds(x, fn));
  if ('not' in c) walkConds(c.not, fn);
}

const problems: string[] = [];
function checkEffect(where: string) {
  return (e: Effect) => {
    if ('give' in e && !ITEMS[e.give]) problems.push(`${where}: gives unknown item ${e.give}`);
    if ('take' in e && !ITEMS[e.take]) problems.push(`${where}: takes unknown item ${e.take}`);
    if ('trait' in e && !TRAITS[e.trait]) problems.push(`${where}: unknown trait ${e.trait}`);
    if ('quest' in e) {
      const q = QUESTS[e.quest.id];
      if (!q) problems.push(`${where}: unknown quest ${e.quest.id}`);
      else {
        if (e.quest.entry && !q.entries[e.quest.entry]) problems.push(`${where}: quest ${e.quest.id} has no entry ${e.quest.entry}`);
        if (e.quest.outcome && q.outcomes && !q.outcomes[e.quest.outcome]) problems.push(`${where}: quest ${e.quest.id} has no outcome ${e.quest.outcome}`);
      }
    }
  };
}
function checkCond(where: string) {
  return (c: Cond) => {
    if ('hasItem' in c && !ITEMS[c.hasItem]) problems.push(`${where}: checks unknown item ${c.hasItem}`);
    if ('trait' in c && !TRAITS[c.trait]) problems.push(`${where}: checks unknown trait ${c.trait}`);
    if ('quest' in c && !QUESTS[c.quest.id]) problems.push(`${where}: checks unknown quest ${c.quest.id}`);
    if ('quest' in c && c.quest.entry && !QUESTS[c.quest.id]?.entries[c.quest.entry]) problems.push(`${where}: checks unknown entry ${c.quest.id}.${c.quest.entry}`);
  };
}

describe('content', () => {
  it('every conversation is well formed', () => {
    for (const [id, convo] of Object.entries(CONVOS)) {
      const known = !!(NPCS[id] || OUTSIDERS[id] || SPEAKERS[id]);
      if (!known) problems.push(`${id}: speaker has no definition`);
      for (const e of convo.entry) {
        if (!convo.nodes[e.node]) problems.push(`${id}: entry points at missing node ${e.node}`);
        walkConds(e.when, checkCond(`${id} entry`));
      }
      for (const m of convo.marker ?? []) walkConds(m.when, checkCond(`${id} marker`));
      for (const [nid, n] of Object.entries(convo.nodes)) {
        const where = `${id}.${nid}`;
        if (n.id !== nid) problems.push(`${where}: id mismatch (${n.id})`);
        if (n.next && !convo.nodes[n.next]) problems.push(`${where}: next points at missing node ${n.next}`);
        if (!n.next && !(n.choices?.length)) problems.push(`${where}: a dead end with no choices`);
        walkEffects(n.effects, checkEffect(where));
        for (const c of n.choices ?? []) {
          if (c.goto && !convo.nodes[c.goto]) problems.push(`${where}: choice goes to missing node ${c.goto}`);
          if (c.action && !ACTIONS.has(c.action)) problems.push(`${where}: unknown action ${c.action}`);
          walkEffects(c.effects, checkEffect(where));
          walkConds(c.when, checkCond(where));
        }
      }
    }
    expect(problems).toEqual([]);
  });

  it('rules, shops and enemies reference real things', () => {
    const p: string[] = [];
    for (const r of RULES) {
      walkEffects(r.effect, (e) => { if ('quest' in e && e.quest.entry && !QUESTS[e.quest.id]?.entries[e.quest.entry]) p.push(`rule ${r.id}: bad entry`); });
    }
    for (const s of Object.values(SHOPS)) for (const l of s.lines) if (!ITEMS[l.id]) p.push(`shop ${s.id}: unknown item ${l.id}`);
    for (const e of Object.values(ENEMIES)) if (e.raise && !ENEMIES[e.raise.into]) p.push(`enemy ${e.id}: raises unknown ${e.raise.into}`);
    expect(p).toEqual([]);
  });

  it('every item has an icon, a value and words', () => {
    for (const it of Object.values(ITEMS)) {
      expect(it.icon, it.id).toBeTruthy();
      expect(it.description.length, it.id).toBeGreaterThan(8);
      expect(it.value, it.id).toBeGreaterThanOrEqual(0);
    }
  });
});
