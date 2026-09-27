/* The world's memory: everything that persists between expeditions, between
 * sessions, between one character and the next.
 *
 * Facts are the world's state, as plain keyed values ('beasts.population',
 * 'caravan.cargo'). Knowledge is what the PLAYER knows (clues, lore,
 * background learning) - kept apart from facts, because the world can be one
 * way and the player can not know it yet. History is what happened, with who
 * saw it; NPCs carry memories of those events and opinions shaped by them.
 *
 * Every piece is JSON-shaped so the save is the state, with no translation. */

import type { ItemInstance } from '@/rpg/character';

export type FactValue = string | number | boolean | null;

export type Axis = 'trust' | 'affection' | 'respect' | 'fear';

export interface NpcState {
  id: string;
  alive: boolean;
  /** -100..100 on each axis. Contradictions are allowed and are the point:
   *  someone can respect you and fear you and not like you at all. */
  trust: number;
  affection: number;
  respect: number;
  fear: number;
  /** History event ids this person knows about (witnessed or heard). */
  memories: string[];
  /** Where they are now, when it differs from their schedule. */
  location?: string;
  /** Free per-NPC flags ('met', 'told_about_pipe', 'angry_about_pelts'). */
  flags: Record<string, FactValue>;
  /** Dialogue nodes already seen, for "once" choices. */
  seen: string[];
}

export interface FactionState {
  id: string;
  /** How the faction regards the player, -100..100. */
  standing: number;
  /** How strong it is in the region, 0..100. */
  strength: number;
  flags: Record<string, FactValue>;
}

export interface HistoryEvent {
  id: string;
  day: number;
  /** One line in the voice of someone telling it ("burned the Kerchief camp"). */
  text: string;
  tags: string[];
  /** How far it travels as gossip: 0 private, 1 local, 2 the whole town. */
  spread: number;
  /** How people who hear of it feel, by default (can be overridden per NPC). */
  sentiment?: Partial<Record<Axis, number>>;
  /** Who takes it personally, and how. */
  reactions?: Record<string, Partial<Record<Axis, number>>>;
}

export interface QuestState {
  id: string;
  status: 'unknown' | 'active' | 'resolved' | 'failed' | 'abandoned';
  /** Journal entry ids unlocked, in order discovered. */
  entries: string[];
  outcome?: string;
  startedDay?: number;
}

export interface CorpseState {
  zone: string;
  x: number;
  z: number;
  gold: number;
  items: ItemInstance[];
  day: number;
  killer: string;
  heroName: string;
}

export interface NemesisState {
  zone: string;
  def: string; // enemy def id
  title: string;
  level: number;
  carries: ItemInstance[];
  heroName: string;
  killed: boolean;
}

export interface LegacyEntry {
  name: string;
  archetype: string;
  background: string;
  level: number;
  day: number;
  killer: string;
  zone: string;
  epitaph: string;
}

export interface ScheduledEffect {
  day: number;
  id: string;
  effect: unknown; // Effect, stored as data
}

export interface WorldState {
  version: number;
  seed: number;
  day: number;
  time: 'dawn' | 'day' | 'dusk' | 'night';
  facts: Record<string, FactValue>;
  knowledge: string[];
  npcs: Record<string, NpcState>;
  factions: Record<string, FactionState>;
  quests: Record<string, QuestState>;
  history: HistoryEvent[];
  scheduled: ScheduledEffect[];
  /** Zone-persistent objects: opened chests, burned walls, picked herbs. */
  zones: Record<string, Record<string, FactValue>>;
  corpse: CorpseState | null;
  nemesis: NemesisState | null;
  /** Discoveries recorded in the codex (weapon pairs, secrets). */
  codex: string[];
  /** Bestiary kill counts by creature def. */
  bestiary: Record<string, number>;
  /** Items on the ground in a zone that must persist (dropped quest items). */
  groundItems: Array<{ zone: string; x: number; z: number; item: ItemInstance }>;
  /** The inn's storage: it belongs to the world, so it outlives a character. */
  stash: Array<ItemInstance | null>;
  /** Those who came before. */
  legacy: LegacyEntry[];
  /** Shop stock and prices, by shop. */
  shops: Record<string, { stock: ItemInstance[]; restockDay: number; priceMult: number }>;
}

export function freshWorld(seed: number): WorldState {
  return {
    version: 1, seed, day: 1, time: 'dusk',
    facts: {}, knowledge: [], npcs: {}, factions: {}, quests: {}, history: [], scheduled: [],
    zones: {}, corpse: null, nemesis: null, codex: [], bestiary: {}, groundItems: [],
    stash: new Array(48).fill(null), legacy: [], shops: {},
  };
}

export function blankNpc(id: string): NpcState {
  return { id, alive: true, trust: 0, affection: 0, respect: 0, fear: 0, memories: [], flags: {}, seen: [] };
}
