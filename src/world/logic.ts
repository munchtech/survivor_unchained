import type { WorldState, FactValue, Axis, NpcState, HistoryEvent } from './state';
import { blankNpc } from './state';
import type { CharacterData } from '@/rpg/character';
import { makeItem, addToPack, takeItem, countItem, worldTags } from '@/rpg/character';
import { ITEMS } from '@/content/items';
import { TRAITS } from '@/content/archetypes';

/* The language the world is written in.
 *
 * Quests, dialogue, zone events, shops and the daily simulation never touch
 * state directly: they ask questions (Cond) and make changes (Effect), both
 * as plain data. That is what lets one quest have six solutions without six
 * code paths - each solution is just a different set of facts arriving at a
 * different outcome - and it is what the journal, the debug inspector and
 * the tests read to explain why the world is the way it is.
 *
 * Every change also produces a Notice, so the interface can tell the player
 * what just happened ("Maeca will remember that.") without the content having
 * to say it twice. */

export type Cmp = { eq?: FactValue; ne?: FactValue; gte?: number; lte?: number; gt?: number; lt?: number; exists?: boolean };

export type Cond =
  | ({ fact: string } & Cmp)
  | { knows: string } | { notKnows: string }
  | { bg: string } | { archetype: string }
  | { hasItem: string; qty?: number } | { hasTag: string }
  | { trait: string }
  | { rel: { npc: string; axis: Axis } & Cmp }
  | { met: string }
  | { npcFlag: { npc: string; key: string } & Cmp }
  | { npcKnows: { npc: string; event: string } }
  | { faction: { id: string } & Cmp }
  | { quest: { id: string; status?: string; entry?: string } }
  | { day: Cmp } | { time: WorldState['time'] | Array<WorldState['time']> }
  | { level: Cmp } | { gold: Cmp }
  | { history: string }
  | { zone: { id: string; key: string } & Cmp }
  | { all: Cond[] } | { any: Cond[] } | { not: Cond };

export type Effect =
  | { set: Record<string, FactValue> }
  | { add: Record<string, number> }
  | { learn: string | string[]; text?: string }
  | { rel: { npc: string } & Partial<Record<Axis, number>>; quiet?: boolean }
  | { npcFlag: { npc: string; key: string; value: FactValue } }
  | { faction: { id: string; standing?: number; strength?: number } }
  | { give: string; qty?: number; rarity?: number }
  | { take: string; qty?: number }
  | { gold: number }
  | { quest: { id: string; status?: WorldState['quests'][string]['status']; entry?: string; outcome?: string } }
  | { history: Omit<HistoryEvent, 'day'>; witnesses?: string[] }
  | { tell: { npc: string; event: string } }
  | { trait: string }
  | { condition: { id: CharacterData['conditions'][number]['id']; days: number; note?: string } }
  | { cure: string }
  | { zone: { id: string; key: string; value: FactValue } }
  | { later: { days: number; id: string; effect: Effect | Effect[] } }
  | { xp: number }
  | { notice: string; tone?: Notice['tone'] }
  | { if: Cond; then: Effect | Effect[]; else?: Effect | Effect[] };

export interface Notice { text: string; tone: 'item' | 'gold' | 'rel' | 'journal' | 'history' | 'learn' | 'faction' | 'trait' | 'warn' | 'info' }

export interface Ctx {
  world: WorldState;
  ch: CharacterData;
  notify: (n: Notice) => void;
  /** Display names, for notices. */
  npcName?: (id: string) => string;
  questName?: (id: string) => string;
  entryText?: (quest: string, entry: string) => string;
}

export function npc(world: WorldState, id: string): NpcState {
  return (world.npcs[id] ??= blankNpc(id));
}

export function fact(world: WorldState, key: string): FactValue {
  return world.facts[key] ?? null;
}

function cmp(v: FactValue, c: Cmp): boolean {
  if (c.exists !== undefined) return c.exists ? v !== null && v !== undefined : v === null || v === undefined;
  if ('eq' in c && c.eq !== undefined && v !== c.eq) return false;
  if ('ne' in c && c.ne !== undefined && v === c.ne) return false;
  const n = typeof v === 'number' ? v : v === null ? 0 : Number(v);
  if (c.gte !== undefined && !(n >= c.gte)) return false;
  if (c.lte !== undefined && !(n <= c.lte)) return false;
  if (c.gt !== undefined && !(n > c.gt)) return false;
  if (c.lt !== undefined && !(n < c.lt)) return false;
  return true;
}

export function test(c: Cond | undefined, ctx: Ctx): boolean {
  if (!c) return true;
  const w = ctx.world, ch = ctx.ch;
  if ('all' in c) return c.all.every((x) => test(x, ctx));
  if ('any' in c) return c.any.some((x) => test(x, ctx));
  if ('not' in c) return !test(c.not, ctx);
  if ('fact' in c) return cmp(fact(w, c.fact), c);
  if ('knows' in c) return ch.knowledge.includes(c.knows);
  if ('notKnows' in c) return !ch.knowledge.includes(c.notKnows);
  if ('bg' in c) return ch.background === c.bg;
  if ('archetype' in c) return ch.archetype === c.archetype;
  if ('hasItem' in c) return countItem(ch, c.hasItem) >= (c.qty ?? 1);
  if ('hasTag' in c) return worldTags(ch).has(c.hasTag);
  if ('trait' in c) return ch.traits.includes(c.trait);
  if ('rel' in c) return cmp(npc(w, c.rel.npc)[c.rel.axis], c.rel);
  if ('met' in c) return !!npc(w, c.met).flags.met;
  if ('npcFlag' in c) return cmp(npc(w, c.npcFlag.npc).flags[c.npcFlag.key] ?? null, c.npcFlag);
  if ('npcKnows' in c) return npc(w, c.npcKnows.npc).memories.includes(c.npcKnows.event);
  if ('faction' in c) return cmp(w.factions[c.faction.id]?.standing ?? 0, c.faction);
  if ('quest' in c) {
    const q = w.quests[c.quest.id];
    if (c.quest.status && (q?.status ?? 'unknown') !== c.quest.status) return false;
    if (c.quest.entry && !q?.entries.includes(c.quest.entry)) return false;
    return true;
  }
  if ('day' in c) return cmp(w.day, c.day);
  if ('time' in c) return Array.isArray(c.time) ? c.time.includes(w.time) : w.time === c.time;
  if ('level' in c) return cmp(ch.level, c.level);
  if ('gold' in c) return cmp(ch.gold, c.gold);
  if ('history' in c) return w.history.some((h) => h.id === c.history);
  if ('zone' in c) return cmp(w.zones[c.zone.id]?.[c.zone.key] ?? null, c.zone);
  return false;
}

const AXIS_WORDS: Record<Axis, [string, string]> = {
  trust: ['trusts you more', 'trusts you less'],
  affection: ['warms to you', 'cools toward you'],
  respect: ['respects you more', 'thinks less of you'],
  fear: ['is more afraid of you', 'is less afraid of you'],
};

export function apply(e: Effect | Effect[] | undefined, ctx: Ctx): void {
  if (!e) return;
  if (Array.isArray(e)) { for (const x of e) apply(x, ctx); return; }
  const w = ctx.world, ch = ctx.ch;
  if ('if' in e) { apply(test(e.if, ctx) ? e.then : e.else, ctx); return; }
  if ('set' in e) { for (const [k, v] of Object.entries(e.set)) w.facts[k] = v; return; }
  if ('add' in e) { for (const [k, v] of Object.entries(e.add)) w.facts[k] = ((w.facts[k] as number) ?? 0) + v; return; }
  if ('learn' in e) {
    const list = Array.isArray(e.learn) ? e.learn : [e.learn];
    let fresh = false;
    for (const k of list) if (!ch.knowledge.includes(k)) { ch.knowledge.push(k); fresh = true; }
    if (fresh && e.text) ctx.notify({ text: e.text, tone: 'learn' });
    return;
  }
  if ('rel' in e) {
    const s = npc(w, e.rel.npc);
    for (const axis of ['trust', 'affection', 'respect', 'fear'] as Axis[]) {
      const d = e.rel[axis];
      if (!d) continue;
      s[axis] = Math.max(-100, Math.min(100, s[axis] + d));
      if (!e.quiet && Math.abs(d) >= 5) ctx.notify({ text: `${ctx.npcName?.(e.rel.npc) ?? e.rel.npc} ${AXIS_WORDS[axis][d > 0 ? 0 : 1]}.`, tone: 'rel' });
    }
    return;
  }
  if ('npcFlag' in e) { npc(w, e.npcFlag.npc).flags[e.npcFlag.key] = e.npcFlag.value; return; }
  if ('faction' in e) {
    const f = (w.factions[e.faction.id] ??= { id: e.faction.id, standing: 0, strength: 50, flags: {} });
    if (e.faction.standing) f.standing = Math.max(-100, Math.min(100, f.standing + e.faction.standing));
    if (e.faction.strength) f.strength = Math.max(0, Math.min(100, f.strength + e.faction.strength));
    return;
  }
  if ('give' in e) {
    const it = makeItem(ch, e.give, { qty: e.qty ?? 1, rarity: e.rarity });
    const name = ITEMS[e.give].name;
    if (addToPack(ch, it)) ctx.notify({ text: `${name}${(e.qty ?? 1) > 1 ? ` ×${e.qty}` : ''}`, tone: 'item' });
    else {
      w.stash[w.stash.indexOf(null)] = it;
      ctx.notify({ text: `${name} was sent to the inn - your pack is full.`, tone: 'warn' });
    }
    return;
  }
  if ('take' in e) { takeItem(ch, e.take, e.qty ?? 1); return; }
  if ('gold' in e) {
    ch.gold = Math.max(0, ch.gold + e.gold);
    if (e.gold > 0) ch.stats.goldEarned += e.gold;
    ctx.notify({ text: `${e.gold > 0 ? '+' : ''}${e.gold} gold`, tone: 'gold' });
    return;
  }
  if ('quest' in e) {
    const q = (w.quests[e.quest.id] ??= { id: e.quest.id, status: 'unknown', entries: [] });
    if (e.quest.status && q.status !== e.quest.status) {
      const was = q.status;
      q.status = e.quest.status;
      if (was === 'unknown' && q.status === 'active') { q.startedDay = w.day; ctx.notify({ text: `New: ${ctx.questName?.(q.id) ?? q.id}`, tone: 'journal' }); }
      if (q.status === 'resolved') ctx.notify({ text: `${ctx.questName?.(q.id) ?? q.id}: resolved`, tone: 'journal' });
    }
    if (e.quest.entry && !q.entries.includes(e.quest.entry)) {
      q.entries.push(e.quest.entry);
      if (q.status === 'unknown') { q.status = 'active'; q.startedDay = w.day; }
      ctx.notify({ text: ctx.entryText?.(q.id, e.quest.entry) ?? 'Journal updated', tone: 'journal' });
    }
    if (e.quest.outcome) q.outcome = e.quest.outcome;
    return;
  }
  if ('history' in e) {
    if (w.history.some((h) => h.id === e.history.id)) return;
    const ev: HistoryEvent = { ...e.history, day: w.day };
    w.history.push(ev);
    for (const who of e.witnesses ?? []) witness(w, who, ev, ctx);
    return;
  }
  if ('tell' in e) {
    const ev = w.history.find((h) => h.id === e.tell.event);
    if (ev) witness(w, e.tell.npc, ev, ctx);
    return;
  }
  if ('trait' in e) {
    if (!ch.traits.includes(e.trait)) {
      ch.traits.push(e.trait);
      ctx.notify({ text: `You have become: ${TRAITS[e.trait]?.name ?? e.trait}`, tone: 'trait' });
    }
    return;
  }
  if ('condition' in e) {
    const cur = ch.conditions.find((c) => c.id === e.condition.id);
    if (cur) cur.days = Math.max(cur.days, e.condition.days);
    else ch.conditions.push({ ...e.condition });
    return;
  }
  if ('cure' in e) { ch.conditions = ch.conditions.filter((c) => c.id !== e.cure); return; }
  if ('zone' in e) { (w.zones[e.zone.id] ??= {})[e.zone.key] = e.zone.value; return; }
  if ('later' in e) { w.scheduled.push({ day: w.day + e.later.days, id: e.later.id, effect: e.later.effect }); return; }
  if ('xp' in e) { ch.xp += e.xp; return; }
  if ('notice' in e) { ctx.notify({ text: e.notice, tone: e.tone ?? 'info' }); return; }
}

/** Someone learns of an event and it changes how they feel about you. */
export function witness(w: WorldState, who: string, ev: HistoryEvent, ctx?: Ctx) {
  const s = npc(w, who);
  if (s.memories.includes(ev.id) || !s.alive) return false;
  s.memories.push(ev.id);
  const r = ev.reactions?.[who] ?? ev.sentiment;
  if (r) {
    for (const axis of ['trust', 'affection', 'respect', 'fear'] as Axis[]) {
      const d = r[axis];
      if (d) s[axis] = Math.max(-100, Math.min(100, s[axis] + d));
    }
    if (ctx && ev.reactions?.[who]) ctx.notify({ text: `${ctx.npcName?.(who) ?? who} will remember that.`, tone: 'rel' });
  }
  return true;
}

/** A short read of how someone regards you, for the interface. */
export function attitude(s: NpcState): string {
  const parts: string[] = [];
  if (s.fear >= 40) parts.push('afraid of you');
  if (s.trust >= 40) parts.push('trusts you');
  else if (s.trust <= -40) parts.push('distrusts you');
  if (s.affection >= 40) parts.push('fond of you');
  else if (s.affection <= -40) parts.push('dislikes you');
  if (s.respect >= 40) parts.push('respects you');
  else if (s.respect <= -40) parts.push('holds you in contempt');
  if (!parts.length) return s.flags.met ? 'unsure of you' : 'a stranger';
  return parts.join(', ');
}
