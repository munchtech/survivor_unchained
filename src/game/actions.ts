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
  openOverlay(o: 'inventory' | 'character' | 'journal' | 'pause'): void;
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
  rest(): void;
  /** Trait picks and attribute points on the character sheet. */
  spendPoint(attr: 'might' | 'finesse' | 'wits' | 'resolve'): void;
  pickTrait(id: string): void;
}

export const actions = {} as GameActions;
