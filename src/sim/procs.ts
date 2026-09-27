import type { School, StatusKind, Family, Tag } from './types';
import type { StatusPayload } from '@/content/weapons';

/* Triggers: the machinery a build is made of.
 *
 *   Fireball -> applies Burning
 *   Burning -> spreads when enemies die            (kindling: on kill, if burning)
 *   Burning enemies -> may explode                 (pyre burst: on kill, if burning, 25%)
 *   Explosions -> launch embers                     (emberseekers: on explode)
 *   Embers -> seek elites                           (seek: 'elite')
 *   Elite deaths -> open a fire portal              (on kill, if elite)
 *
 * Each of those lines is one TriggerDef below. None of them knows about the
 * others; the chain happens because an effect raises the same events a
 * weapon hit does. A depth limit keeps a chain from running forever inside a
 * single tick, and internal cooldowns keep a single rule from firing a
 * thousand times a second - but inside those two limits a build is allowed
 * to become absurd. That is the reward.
 *
 * Items, boons, evolutions, traits and shrines all speak this language. */

export type TriggerEvent =
  | 'hit' | 'crit' | 'kill' | 'status' | 'explode' | 'freeze' | 'shatter'
  | 'hurt' | 'dash' | 'ability' | 'ember' | 'tick' | 'levelUp' | 'block' | 'dodge';

export interface TriggerCond {
  targetStatus?: StatusKind;
  targetFamily?: Family;
  elite?: boolean;
  school?: School;
  tag?: Tag;
  notTag?: Tag;
  weapon?: string;
  /** Target health fraction below this, after the hit. */
  hpBelow?: number;
  /** For 'status' events: which status was applied. */
  applied?: StatusKind;
  /** Survivor health fraction below this. */
  selfHpBelow?: number;
  moving?: boolean;
}

export type Seek = 'nearest' | 'elite' | 'random' | 'strongest' | 'marked';

export type Effect =
  | { do: 'explode'; radius: number; damage: number; basis: 'hit' | 'maxhp' | 'flat'; school: School; status?: StatusPayload }
  | { do: 'status'; status: StatusPayload; target: 'hit' | 'nearby'; radius?: number; count?: number }
  | { do: 'spread'; kind: StatusKind; radius: number; count: number; stacks?: number }
  | { do: 'missiles'; count: number; damage: number; basis: 'hit' | 'flat' | 'maxhp'; school: School; seek: Seek; speed: number; art: string; status?: StatusPayload }
  | { do: 'chain'; count: number; range: number; damage: number; basis: 'hit' | 'flat'; school: School }
  | { do: 'heal'; amount: number; basis: 'flat' | 'maxhp' | 'hit' }
  | { do: 'shield'; amount: number; duration: number }
  | { do: 'zone'; radius: number; duration: number; dps: number; basis: 'hit' | 'flat'; school: School; slow?: number; art: string; status?: StatusPayload }
  | { do: 'buff'; id: string; stat: string; value: number; kind: 'inc' | 'more' | 'flat'; duration: number; maxStacks?: number }
  | { do: 'cooldown'; seconds: number; scope: 'all' | 'ability' | 'dash' }
  | { do: 'raise'; kind: 'ghoul' | 'spirit_wolf'; duration: number; max: number }
  | { do: 'pull'; radius: number; strength: number }
  | { do: 'execute'; threshold: number }
  | { do: 'nova'; radius: number; damage: number; basis: 'hit' | 'flat'; school: School; knockback?: number }
  | { do: 'strike'; count: number; radius: number; damage: number; basis: 'flat' | 'hit'; school: School; area: number }
  | { do: 'ember'; amount: number };

export interface TriggerDef {
  on: TriggerEvent;
  chance?: number;
  /** Internal cooldown in seconds. */
  icd?: number;
  when?: TriggerCond;
  effects: Effect[];
  /** Shown in tooltips so the player can see what the rule does. */
  text?: string;
}

export interface TriggerInstance {
  def: TriggerDef;
  source: string;
  cd: number;
  /** Rank scales damage-bearing effects. */
  rank: number;
  count: number;
}
