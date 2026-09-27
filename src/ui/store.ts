import { signal } from '@preact/signals';
import type { Offer } from '@/sim/battle';
import type { School } from '@/sim/types';
import type { CharacterData } from '@/rpg/character';
import type { WorldState } from '@/world/state';

/* Everything the interface shows, as signals.
 *
 * The game writes; components read. Nothing in here knows about Three.js
 * or the simulation's internals: the game folds its state into these plain
 * shapes (the HUD at about 12 Hz, the rest when it changes), so the
 * interface can be built, styled and screenshotted on its own. */

export type Screen = 'boot' | 'title' | 'create' | 'play';
export type Overlay =
  | null | 'levelup' | 'inventory' | 'character' | 'journal' | 'dialogue' | 'shop'
  | 'pause' | 'death' | 'chapter' | 'map' | 'rest' | 'stash';

export const screen = signal<Screen>('boot');
export const overlay = signal<Overlay>(null);

/* ------------------------------------------------------------------ HUD -- */

export interface HudWeapon {
  id: string;
  name: string;
  glyph: string;
  school: School;
  rank: number;
  maxRank: number;
  evolved: boolean;
  /** 0 just fired, 1 ready. */
  ready: number;
  /** Rank 8 with a catalyst met: an evolution is waiting in the next draft. */
  canEvolve: boolean;
}

export interface HudBoon { id: string; name: string; glyph: string; rank: number; max: number; synergy: boolean; rarity: string }

export interface HudStatus { id: string; label: string; glyph: string; tone: 'bad' | 'good'; left?: number }

export interface HudState {
  combat: boolean;
  hp: number;
  maxHp: number;
  shield: number;
  /** Health a moment ago, for the trailing bar. */
  level: number;
  ember: number;
  emberNext: number;
  weapons: HudWeapon[];
  boons: HudBoon[];
  dash: { charges: number; max: number; recharge: number };
  ability: { id: string; name: string; glyph: string; ready: number; left: number; active: boolean } | null;
  gold: number;
  kills: number;
  time: number;
  statuses: HudStatus[];
  /** Consumable in the quick slot. */
  quick: { icon: string; name: string; qty: number } | null;
}

export const hud = signal<HudState | null>(null);

export interface BossBar {
  name: string;
  title?: string;
  hp: number;
  maxHp: number;
  /** Fractions of the bar where phases change. */
  phases?: number[];
  /** A channel the survivor can break, 0..1. */
  channel?: { label: string; progress: number } | null;
  shielded?: boolean;
}
export const boss = signal<BossBar | null>(null);

export interface ZoneInfo { name: string; region?: string; day: number; time: 'dawn' | 'day' | 'dusk' | 'night' }
export const zoneInfo = signal<ZoneInfo | null>(null);

export interface Objective { id: string; title: string; steps: Array<{ text: string; done?: boolean; optional?: boolean }>; tone?: 'main' | 'side' | 'tutorial' }
export const objectives = signal<Objective[]>([]);

export interface Prompt { key: string; verb: string; target: string; hint?: string; locked?: string }
export const prompt = signal<Prompt | null>(null);

/* ------------------------------------------------------------- notices -- */

export type NoticeKind = 'loot' | 'gold' | 'quest' | 'world' | 'relation' | 'warning' | 'lore' | 'level' | 'discovery';
export interface Toast { id: number; kind: NoticeKind; text: string; sub?: string; icon?: string; rarity?: number; born: number; life: number }
export const toasts = signal<Toast[]>([]);

let toastId = 1;
let uiClock = 0;

/** Advance the interface clock; expires toasts and announcements. */
export function tickUi(dt: number) {
  uiClock += dt;
  const list = toasts.value;
  if (list.length && list.some((t) => uiClock - t.born > t.life)) toasts.value = list.filter((t) => uiClock - t.born <= t.life);
  const a = announcement.value;
  if (a && uiClock - a.born > a.life) announcement.value = null;
  const s = subtitle.value;
  if (s && uiClock - s.born > s.life) subtitle.value = null;
}

export function toast(kind: NoticeKind, text: string, o: { sub?: string; icon?: string; rarity?: number; life?: number } = {}) {
  // Same loot twice in a row stacks instead of scrolling the feed.
  const list = toasts.value;
  const last = list[list.length - 1];
  if (last && last.kind === kind && last.text === text && uiClock - last.born < 2) {
    toasts.value = [...list.slice(0, -1), { ...last, born: uiClock, sub: o.sub ?? last.sub }];
    return;
  }
  const t: Toast = { id: toastId++, kind, text, sub: o.sub, icon: o.icon, rarity: o.rarity, born: uiClock, life: o.life ?? (kind === 'loot' || kind === 'gold' ? 4 : 6.5) };
  toasts.value = [...list.slice(-5), t];
}

export interface Announcement { id: number; title: string; subtitle?: string; kicker?: string; tone: 'danger' | 'info' | 'boon' | 'story' | 'zone'; born: number; life: number }
export const announcement = signal<Announcement | null>(null);

export function announce(title: string, sub?: string, tone: Announcement['tone'] = 'info', life = 3.6, kicker?: string) {
  announcement.value = { id: toastId++, title, subtitle: sub, kicker, tone, born: uiClock, life };
}

/** A line spoken in the world (a bark, a narrator line) at the bottom. */
export interface Subtitle { id: number; speaker?: string; text: string; born: number; life: number }
export const subtitle = signal<Subtitle | null>(null);
export function say(text: string, speaker?: string, life = Math.max(2.5, text.length * 0.06)) {
  subtitle.value = { id: toastId++, speaker, text, born: uiClock, life };
}

/* -------------------------------------------------------------- level up -- */

export interface LevelUpView {
  level: number;
  tip?: string;
  offers: Offer[];
  /** Per offer: which of its tags the build already has. */
  fits: string[][];
  rerolls: number;
  banishes: number;
  /** Levels still waiting after this one. */
  queued: number;
  pick(i: number): void;
  reroll(): void;
  banish(i: number): void;
}
export const levelUp = signal<LevelUpView | null>(null);

/* -------------------------------------------------------------- fading -- */

/** Full-screen fade, 0 clear .. 1 black, with an optional caption. */
export const fade = signal<{ to: number; caption?: string; sub?: string; seconds: number }>({ to: 0, seconds: 0.6 });

/* ------------------------------------------------------ title, creation -- */

export interface SlotView { slot: number; name: string; level: number; archetype: string; day: number; zone: string; savedAt: number; alive: boolean }
export const slots = signal<SlotView[]>([]);

export interface CreationDraft {
  step: number;
  name: string;
  archetype: 'warden' | 'reaver' | 'arcanist' | 'stalker';
  weaponItem: string;
  ability: string;
  startBoon: string;
  background: 'hunter' | 'scholar' | 'outcast' | 'devout';
  palette: string;
  model: string;
  headgear: boolean;
}
export const creation = signal<CreationDraft | null>(null);

/** Loading progress, 0..1, with what is being done. */
export const loading = signal<{ progress: number; label: string } | null>({ progress: 0, label: 'Kindling' });

/** A tutorial card: what to do, with the keys for it. */
export interface Hint { id: string; title: string; text: string; keys?: string[] }
export const hint = signal<Hint | null>(null);

/* ----------------------------------------------------------- character -- */


/** The survivor and the world, for the pack, sheet and journal. Mutated in
 *  place by the game; `rev` ticks so components re-read. */
export const character = signal<CharacterData | null>(null);
export const worldView = signal<WorldState | null>(null);
export const rev = signal(0);
export function touch() { rev.value++; }

/* ------------------------------------------------------------- dialogue -- */

export interface DialogueChoiceView { index: number; text: string; enabled: boolean; locked?: string; badge?: string; ends?: boolean; action?: string }
export interface DialogueView {
  npc: string;
  name: string;
  title: string;
  portrait: string | null;
  mood: string;
  /** Who is speaking this line: the npc, 'player' or 'narrator'. */
  speaker: 'npc' | 'player' | 'narrator';
  text: string;
  key: number;
  choices: DialogueChoiceView[];
  canContinue: boolean;
}
export const dialogue = signal<DialogueView | null>(null);
