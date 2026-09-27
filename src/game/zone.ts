import type { AmbienceMix } from '@/audio/ambience';

export interface MapMark { x: number; z: number; label: string; kind: 'place' | 'quest' | 'turn' | 'exit' | 'danger' | 'person' | 'mystery' }
import type { ZoneBuild } from './scene';
import type { Battle, BattleHooks } from '@/sim/battle';
import type { CombatEvent } from '@/sim/events';
import type { WorldState } from '@/world/state';
import type { NpcActor } from './actors';

/* A place the survivor can be, as the game runs it.
 *
 * The build (zone/*.ts) is the look and the collision; the runtime is what
 * happens there: who stands where, what can be used, what the night sends,
 * what the place remembers. Runtimes read and write the world only through
 * the game's logic context, so a quest can be moved between zones without
 * the zone knowing. */

export interface Interactable {
  id: string;
  x: number;
  z: number;
  /** How close the survivor must be. */
  r: number;
  verb: string;
  name: string;
  hint?: () => string | undefined;
  /** Not offered at all unless this holds. */
  when?: () => boolean;
  /** Offered but refused, with the reason ("Locked"). */
  locked?: () => string | null;
  act: () => void;
  /** Height of the prompt anchor. */
  y?: number;
}

export interface Arrival { x: number; z: number; facing?: number }

export interface ZoneRuntime {
  id: string;
  name: string;
  region?: string;
  build: ZoneBuild;
  combat: boolean;
  /** Where you stand arriving from another zone (null: a fresh load). */
  arrival(from: string | null): Arrival;
  /** The Battle exists; set hooks, spawn residents. */
  begin(b: Battle): void;
  /** Each fixed step of the simulation. */
  step?(dt: number): void;
  /** Each rendered frame. */
  frame?(dt: number): void;
  events?(evs: CombatEvent[]): void;
  interactables: Interactable[];
  /** People standing here, by id. */
  actors?: Map<string, NpcActor>;
  hooks?: Partial<BattleHooks>;
  /** Time of day the zone shows, from the world. */
  timeOf?(w: WorldState): WorldState['time'];
  /** A death here: return true if the zone handled it (the prologue does). */
  onDeath?(killer: string): boolean;
  /** Places, people and exits to show on the map (only what is known). */
  mapMarks?(): MapMark[];
  /** What the place sounds like where the survivor (or the camera) is. */
  ambience?(x: number, z: number): Partial<AmbienceMix>;
  /** Internal state for tools (the autopilot, the debug readout). */
  debug?(): Record<string, unknown>;
  dispose?(): void;
}
