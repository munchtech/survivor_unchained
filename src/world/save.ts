import type { CharacterData } from '@/rpg/character';
import type { WorldState } from './state';
import { BOONS, START_BLESSINGS } from '@/content/boons';

/* Persistence: the proof that this is not a run.
 *
 * One record per slot holds the character, the world and where the survivor
 * stands. It is written on rest, on changing zone and on every event the
 * world would not want to forget (a quest resolved, a death), and it can be
 * exported as a code or a file so a save is never trapped in one browser.
 *
 * Versioned: a save from an older build is migrated forward on load, never
 * discarded. A save that fails to parse is set aside, not overwritten. */

export const SAVE_VERSION = 1;
const PREFIX = 'survivor-unchained.save.';
const META = 'survivor-unchained.meta';

export interface SaveLocation { zone: string; x: number; z: number; facing: number }

export interface SaveData {
  version: number;
  savedAt: number;
  playtime: number;
  character: CharacterData;
  world: WorldState;
  location: SaveLocation;
  /** Mid-expedition ember, if saved at a field camp. */
  ember?: { level: number; xp: number; weapons: Array<{ id: string; rank: number; evolution: string | null }>; boons: Record<string, number> } | null;
}

export interface SlotInfo { slot: number; name: string; level: number; archetype: string; day: number; zone: string; savedAt: number; alive: boolean }

function storage(): Storage | null {
  try {
    const s = window.localStorage;
    const k = '__su_probe';
    s.setItem(k, '1');
    s.removeItem(k);
    return s;
  } catch {
    return null;
  }
}

function migrate(d: SaveData): SaveData {
  // Version 1 is the first; later versions add steps here, oldest first.
  if (!d.world.stash) d.world.stash = new Array(48).fill(null);
  if (!d.world.legacy) d.world.legacy = [];
  if (!d.world.shops) d.world.shops = {};
  if (!d.world.groundItems) d.world.groundItems = [];
  // The starting pick is a blessing now; a survivor who began with a passive
  // skill (from before passives and blessings were told apart) is given the
  // first blessing in its place.
  if (d.character.startBoon && BOONS[d.character.startBoon]?.kind !== 'blessing') d.character.startBoon = START_BLESSINGS[0];
  d.version = SAVE_VERSION;
  return d;
}

export const Saves = {
  write(slot: number, data: Omit<SaveData, 'version' | 'savedAt'>) {
    const s = storage();
    const full: SaveData = { ...data, version: SAVE_VERSION, savedAt: Date.now() };
    const json = JSON.stringify(full);
    if (s) {
      try {
        s.setItem(PREFIX + slot, json);
        s.setItem(META, JSON.stringify({ last: slot }));
      } catch (e) {
        console.warn('save failed', e);
        return false;
      }
    }
    memory.set(slot, json);
    return true;
  },

  read(slot: number): SaveData | null {
    const s = storage();
    const raw = s?.getItem(PREFIX + slot) ?? memory.get(slot) ?? null;
    if (!raw) return null;
    try {
      const d = JSON.parse(raw) as SaveData;
      if (!d.character || !d.world) throw new Error('incomplete save');
      return migrate(d);
    } catch (e) {
      // Keep the broken record aside for a bug report; never overwrite it.
      s?.setItem(`${PREFIX}${slot}.broken.${Date.now()}`, raw);
      console.warn('save unreadable', e);
      return null;
    }
  },

  slots(): SlotInfo[] {
    const out: SlotInfo[] = [];
    for (let i = 0; i < 3; i++) {
      const d = this.read(i);
      if (d) out.push({ slot: i, name: d.character.name, level: d.character.level, archetype: d.character.archetype, day: d.world.day, zone: d.location.zone, savedAt: d.savedAt, alive: d.character.alive });
    }
    return out;
  },

  lastSlot(): number | null {
    try {
      const m = JSON.parse(storage()?.getItem(META) ?? 'null');
      return typeof m?.last === 'number' ? m.last : null;
    } catch { return null; }
  },

  remove(slot: number) {
    storage()?.removeItem(PREFIX + slot);
    memory.delete(slot);
  },

  /** A compact code for moving a save between machines. */
  exportCode(slot: number): string | null {
    const s = storage();
    const raw = s?.getItem(PREFIX + slot) ?? memory.get(slot);
    if (!raw) return null;
    return btoa(unescape(encodeURIComponent(raw)));
  },

  importCode(slot: number, code: string): boolean {
    try {
      const raw = decodeURIComponent(escape(atob(code.trim())));
      const d = JSON.parse(raw) as SaveData;
      if (!d.character || !d.world) return false;
      storage()?.setItem(PREFIX + slot, JSON.stringify(migrate(d)));
      memory.set(slot, raw);
      return true;
    } catch {
      return false;
    }
  },
};

// When storage is unavailable (private windows, sandboxed previews) the game
// still works for the session.
const memory = new Map<number, string>();
