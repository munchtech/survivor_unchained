import type { GoreSetting } from '@/render/gore';
import type { CreationChoice } from '@/rpg/character';
import type { Quality } from '@/render/renderer';

/* What the interface can ask the game to do. The game fills this in when it
 * boots; components call it without importing the game (no cycles, and the
 * interface can be exercised on its own with a stub). */

export interface GameActions {
  newJourney(): void;
  cancelCreation(): void;
  beginJourney(c: CreationChoice): void;
  continueJourney(slot: number): void;
  deleteSlot(slot: number): void;
  setQuality(q: Quality): void;
  resume(): void;
  saveNow(): void;
  quitToTitle(): void;
  /** Save and close the game (the desktop build). */
  quitGame(): void;
  cycleSound(): 'on' | 'quiet' | 'off';
  setSound(level: 'on' | 'quiet' | 'off'): void;
  quality(): 'low' | 'medium' | 'high';
  soundLevel(): 'on' | 'quiet' | 'off';
  /** Blood and bodies: full, reduced (a little blood) or off. */
  gore(): GoreSetting;
  setGore(v: GoreSetting): void;
  openOverlay(o: 'inventory' | 'character' | 'journal' | 'pause' | 'map'): void;
  closeOverlay(): void;
  /** Death screen: get up again. */
  rise(): void;
  /** Inventory. */
  equipItem(uid: string, slot?: string): void;
  unequip(slot: string): void;
  useItem(uid: string): void;
  dropItem(uid: string): void;
  /** Dialogue. */
  choose(index: number): void;
  advance(): void;
  /** Shops and the inn. */
  buy(shop: string, uid: string): void;
  sell(uid: string): void;
  stash(uid: string): void;
  unstash(uid: string): void;
  rest(mode: 'sleep' | 'night'): void;
  finishRest(): void;
  priceOf(uid: string, side: 'buy' | 'sell'): number | null;
  /** Trait picks and attribute points on the character sheet. */
  spendPoint(attr: 'might' | 'finesse' | 'wits' | 'resolve'): void;
  pickTrait(id: string): void;
}

export const actions = {} as GameActions;
