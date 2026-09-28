import type { Cond, Effect, Ctx } from './logic';
import { test, apply, npc } from './logic';

/* Conversations.
 *
 * A conversation is a small graph. Where it starts depends on who you are to
 * the person and what they know about you: the same innkeeper greets a
 * stranger, a friend, a thief and someone she heard died last week in four
 * different ways, chosen by conditions, highest priority first.
 *
 * Choices are shown when their condition holds. Some are shown DISABLED
 * with a reason instead ("Requires: Beastlore") - that is the game telling
 * you there was another way, which is half of what makes a background feel
 * like it matters. Choices opened by a background, a piece of knowledge or
 * an item carry a badge saying so.
 *
 * Text can vary by condition, and can quote the world back at the player
 * ({name}, {day}, a fact) - that is how an NPC says "you're the one who
 * burned the camp" without a special case. */

/** One way a line can read. The first variant whose condition holds is
 *  used; `add` variants are instead all collected, in order, and joined
 *  (a notice board, a list of what someone has heard). */
export interface Variant { when?: Cond; text: string; add?: boolean }

export interface DChoice {
  text: string | Variant[];
  /** Offered at all only while this holds (a choice that no longer applies
   *  goes, rather than sitting there locked). */
  show?: Cond;
  when?: Cond;
  /** Show the choice greyed out, with this reason, when `when` fails. */
  locked?: string;
  badge?: string;
  effects?: Effect[];
  goto?: string;
  /** Can only be picked once in this person's lifetime. */
  once?: string;
  /** Special actions the game handles: services and computed trades. */
  action?: 'trade' | 'rest' | 'stash' | 'sell' | 'craft' | 'leave' | 'fortune' | 'bounty' | 'sellpelts' | 'reforge' | 'travel_verge';
  end?: boolean;
}

export interface DNode {
  id: string;
  /** Who speaks: the conversation's owner by default, 'player', 'narrator'. */
  speaker?: string;
  text: string | Variant[];
  choices?: DChoice[];
  effects?: Effect[];
  /** No choices: continue to this node on click. */
  next?: string;
}

export interface Conversation {
  npc: string;
  /** Entry points: the first whose condition holds is where it starts. */
  entry: Array<{ when?: Cond; node: string }>;
  nodes: Record<string, DNode>;
  /** The mark over their head: '!' something new to say, '?' waiting on you. */
  marker?: Array<{ when: Cond; mark: '!' | '?' }>;
}

export interface PresentedChoice { index: number; text: string; enabled: boolean; locked?: string; badge?: string; ends?: boolean; action?: DChoice['action'] }

export interface Presented { node: DNode; speaker: string; text: string; choices: PresentedChoice[] }

function pickText(t: string | Variant[], ctx: Ctx): string {
  if (typeof t === 'string') return t;
  if (t.some((v) => v.add)) return t.filter((v) => v.add && test(v.when, ctx)).map((v) => v.text).join('  ·  ');
  for (const v of t) if (test(v.when, ctx)) return v.text;
  return t[t.length - 1]?.text ?? '';
}

/** Fill {name}, {day}, {fact:key}, {gold} from the world. */
export function template(s: string, ctx: Ctx): string {
  return s
    .replace(/\{name\}/g, ctx.ch.name)
    .replace(/\{day\}/g, String(ctx.world.day))
    .replace(/\{gold\}/g, String(ctx.ch.gold))
    .replace(/\{fact:([\w.]+)\}/g, (_, k) => String(ctx.world.facts[k] ?? ''));
}

export class DialogueRunner {
  node: DNode | null = null;
  private seenKey: string;

  constructor(readonly convo: Conversation, readonly ctx: Ctx) {
    this.seenKey = convo.npc;
  }

  start(): Presented | null {
    const s = npc(this.ctx.world, this.convo.npc);
    const entry = this.convo.entry.find((e) => test(e.when, this.ctx));
    if (!entry) return null;
    const p = this.enter(entry.node);
    s.flags.met = true;
    return p;
  }

  private enter(id: string): Presented | null {
    const n = this.convo.nodes[id];
    if (!n) return null;
    this.node = n;
    apply(n.effects, this.ctx);
    const s = npc(this.ctx.world, this.seenKey);
    if (!s.seen.includes(id)) s.seen.push(id);
    return this.present();
  }

  present(): Presented | null {
    const n = this.node;
    if (!n) return null;
    const s = npc(this.ctx.world, this.seenKey);
    const choices: PresentedChoice[] = [];
    (n.choices ?? []).forEach((c, index) => {
      if (c.once && s.flags[`once:${c.once}`]) return;
      if (c.show && !test(c.show, this.ctx)) return;
      const ok = test(c.when, this.ctx);
      if (!ok && !c.locked) return;
      choices.push({ index, text: template(pickText(c.text, this.ctx), this.ctx), enabled: ok, locked: ok ? undefined : c.locked, badge: c.badge, ends: !!c.end || (!c.goto && !c.action), action: c.action });
    });
    return {
      node: n, speaker: n.speaker ?? this.convo.npc,
      text: template(pickText(n.text, this.ctx), this.ctx), choices,
    };
  }

  /** Pick a choice by its index in the node; returns the next view, or null
   *  when the conversation ends, plus any action the game must perform. */
  choose(index: number): { next: Presented | null; action?: DChoice['action'] } {
    const n = this.node;
    const c = n?.choices?.[index];
    if (!n || !c || !test(c.when, this.ctx)) return { next: this.present() };
    const s = npc(this.ctx.world, this.seenKey);
    if (c.once) s.flags[`once:${c.once}`] = true;
    apply(c.effects, this.ctx);
    if (c.end || (!c.goto && !c.action)) { this.node = null; return { next: null, action: c.action }; }
    if (c.action && !c.goto) return { next: this.present(), action: c.action };
    return { next: this.enter(c.goto!), action: c.action };
  }

  /** Nodes with no choices continue on click. */
  advance(): Presented | null {
    const n = this.node;
    if (!n) return null;
    if (n.next) return this.enter(n.next);
    this.node = null;
    return null;
  }
}

/** The marker a conversation shows right now, if any. */
export function markerOf(convo: Conversation, ctx: Ctx): '!' | '?' | null {
  for (const m of convo.marker ?? []) if (test(m.when, ctx)) return m.mark;
  return null;
}
