import type { Ctx, Cond, Effect } from './logic';
import { test, apply, witness, npc } from './logic';

/* The world goes on without you.
 *
 * A day passes when the survivor rests. Then, in order:
 *
 *   1. scheduled consequences come due ("the survivors die on day 5 if
 *      nobody came");
 *   2. every daily rule is checked - faction agendas, quest escalations, the
 *      blight spreading or receding, the Kerchiefs raiding a road nobody
 *      guards - and fires if its condition holds;
 *   3. gossip moves one step along who-talks-to-whom: an event someone knows
 *      has a chance to reach each person they talk to, and when it arrives it
 *      changes how that person feels about you;
 *   4. conditions on the survivor heal (or worsen);
 *   5. whatever the survivor would notice is written into the morning
 *      report the inn gives them.
 *
 * Rules are content (world/rules.ts), not code, so the world's behaviour can
 * be read, tested and tuned as data. */

export interface DailyRule {
  id: string;
  /** Checked each new day. */
  when: Cond;
  effect: Effect | Effect[];
  /** Fire at most once. */
  once?: boolean;
  /** What the survivor hears about it in the morning, if anything. */
  report?: string;
}

export interface SocialLinks { [npc: string]: string[] }

export interface DayReport {
  day: number; lines: string[];
  /** Who heard what overnight: the talk of the town, for the report. */
  heard: Array<{ npc: string; event: string }>;
}

export function advanceDay(ctx: Ctx, rules: DailyRule[], social: SocialLinks, rng: () => number = Math.random): DayReport {
  const w = ctx.world;
  w.day++;
  w.time = 'dawn';
  const lines: string[] = [];

  // 1. What was scheduled for today.
  const due = w.scheduled.filter((s) => s.day <= w.day);
  w.scheduled = w.scheduled.filter((s) => s.day > w.day);
  for (const s of due) apply(s.effect as Effect, ctx);

  // 2. The world's own agendas.
  const fired = (w.facts['_rules.fired'] as string | null)?.split(',') ?? [];
  for (const r of rules) {
    if (r.once && fired.includes(r.id)) continue;
    if (!test(r.when, ctx)) continue;
    apply(r.effect, ctx);
    if (r.once) fired.push(r.id);
    if (r.report) lines.push(r.report);
  }
  w.facts['_rules.fired'] = fired.join(',');

  // 3. Gossip: one step along the links.
  const heard: DayReport['heard'] = [];
  const spreading = w.history.filter((h) => h.spread > 0);
  for (const [who, circle] of Object.entries(social)) {
    const me = npc(w, who);
    if (!me.alive) continue;
    for (const ev of spreading) {
      if (me.memories.includes(ev.id)) continue;
      const told = circle.some((o) => npc(w, o).memories.includes(ev.id));
      const p = told ? 0.45 * ev.spread : ev.spread >= 2 ? 0.15 : 0;
      if (p > 0 && rng() < p && witness(w, who, ev)) heard.push({ npc: who, event: ev.id });
    }
  }

  // 4. The survivor's conditions.
  const ch = ctx.ch;
  const hardy = ch.traits.includes('iron_constitution');
  for (const c of ch.conditions) c.days -= hardy && c.id === 'wounded' ? 2 : 1;
  const healed = ch.conditions.filter((c) => c.days <= 0);
  ch.conditions = ch.conditions.filter((c) => c.days > 0);
  for (const c of healed) if (c.id === 'wounded') lines.push('Your wounds have closed.');
  ch.conditions.push({ id: 'rested', days: 1 });

  return { day: w.day, lines, heard };
}

/** Evening falls: the time of day moves on without a full day passing. */
export function passTime(ctx: Ctx, to: 'dawn' | 'day' | 'dusk' | 'night') {
  ctx.world.time = to;
}
