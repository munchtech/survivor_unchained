import type { School, StatusKind, Family } from './types';

/* What the simulation tells the rest of the game each tick. The renderer
 * turns these into light and sound, the HUD into numbers, and the world
 * layer into history ("killed 40 wolves tonight", "was killed by X").
 * The simulation never waits on a consumer; events are a one-way stream. */

export type CombatEvent =
  | { t: 'hit'; x: number; z: number; amount: number; crit: boolean; school: School; target: number; dot?: boolean; blocked?: boolean }
  | { t: 'kill'; x: number; z: number; enemy: number; def: string; family: Family; school: School; elite: boolean; boss: boolean; byPlayer: boolean }
  | { t: 'playerHit'; x: number; z: number; amount: number; school: School; source: string; dodged?: boolean; blocked?: boolean }
  | { t: 'playerHeal'; amount: number }
  | { t: 'playerDeath'; x: number; z: number; killer: string; killerId: number }
  | { t: 'status'; target: number; kind: StatusKind; x: number; z: number }
  | { t: 'nova'; x: number; z: number; radius: number; school: School; duration: number; rings?: number }
  | { t: 'explosion'; x: number; z: number; radius: number; school: School; power: number }
  | { t: 'chain'; points: number[]; school: School }
  | { t: 'beam'; x0: number; z0: number; x1: number; z1: number; width: number; school: School; duration: number }
  | { t: 'strike'; x: number; z: number; radius: number; school: School; delay: number }
  | { t: 'slash'; x: number; z: number; angle: number; arc: number; reach: number; school: School }
  | { t: 'muzzle'; x: number; z: number; angle: number; school: School; weapon: string }
  | { t: 'telegraph'; id: number; shape: 'circle' | 'line' | 'cone' | 'ring'; x: number; z: number; x1?: number; z1?: number; radius: number; width?: number; angle?: number; arc?: number; duration: number; hostile: boolean }
  | { t: 'spawn'; enemy: number; x: number; z: number; def: string; style: 'rise' | 'burrow' | 'walk' | 'drop' }
  | { t: 'pickup'; kind: string; amount: number; x: number; z: number }
  | { t: 'levelUp'; level: number }
  | { t: 'evolve'; weapon: string; into: string }
  | { t: 'discovery'; id: string }
  | { t: 'dash'; x0: number; z0: number; x1: number; z1: number }
  | { t: 'ability'; id: string; x: number; z: number; angle: number; radius: number }
  | { t: 'bark'; x: number; z: number; text: string; speaker?: string }
  | { t: 'announce'; title: string; subtitle?: string; kicker?: string; tone?: 'danger' | 'info' | 'boon' | 'story' }
  | { t: 'shake'; amount: number }
  | { t: 'sound'; id: string; x?: number; z?: number; volume?: number };

export class EventStream {
  readonly events: CombatEvent[] = [];
  emit(e: CombatEvent) { this.events.push(e); }
  drain(): CombatEvent[] {
    const out = this.events.splice(0, this.events.length);
    return out;
  }
}
