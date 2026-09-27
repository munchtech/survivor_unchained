import { ARCHETYPES, BACKGROUNDS, TRAITS, type ArchetypeId, type BackgroundId } from '@/content/archetypes';
import { ITEMS, AFFIXES, EQUIP_SLOTS, type EquipSlot, type ItemDef, RARITY_NAMES } from '@/content/items';
import { StatBlock, type StatMod } from '@/sim/stats';
import type { TriggerDef } from '@/sim/procs';
import type { AbilityKind } from '@/content/abilities';
import type { StatusKind } from '@/sim/types';
import type { CharacterModel } from '@/render/assets';
import { Rng } from '@/core/rng';

/* The persistent character: everything about the survivor that outlives an
 * expedition. The ember build (weapon ranks, boons, evolutions) belongs to
 * the Battle and fades when you rest; this is what is left when it does. */

export interface ItemInstance {
  uid: string;
  def: string;
  qty: number;
  rarity: number;
  affixes: Array<{ id: string; tier: number }>;
  /** Given name for storied items ("Maeca's Last Arrow"). */
  name?: string;
  /** Where it came from, one line per owner ("Taken from Ash-Fang"). */
  history?: string[];
}

export interface Condition {
  id: 'wounded' | 'blightsick' | 'poisoned' | 'blessed' | 'rested' | 'wolfscent' | 'hunted';
  days: number;
  note?: string;
}

export interface Attributes { might: number; finesse: number; wits: number; resolve: number }

export interface CharacterData {
  version: number;
  id: string;
  name: string;
  archetype: ArchetypeId;
  background: BackgroundId;
  model: CharacterModel;
  palette: string;
  /** Wears the archetype's helm or hat. */
  headgear?: boolean;
  /** Look: a dyed cloak (or none), and skin. */
  cloak?: string;
  skin?: string;
  level: number;
  xp: number;
  attributes: Attributes;
  points: number;
  traits: string[];
  /** Pending trait picks from levels gained. */
  traitPicks: number;
  knowledge: string[];
  equipment: Record<EquipSlot, ItemInstance | null>;
  pack: Array<ItemInstance | null>;
  gold: number;
  ability: AbilityKind;
  startBoon: string;
  conditions: Condition[];
  /** Kills with each weapon, across every expedition. */
  mastery: Record<string, number>;
  stats: { kills: number; deaths: number; expeditions: number; bossesSlain: number; goldEarned: number; evolutions: string[] };
  alive: boolean;
  createdDay: number;
  nextUid: number;
}

export const PACK_SIZE = 24;

const START_ATTRS: Record<ArchetypeId, Attributes> = {
  warden: { might: 6, finesse: 3, wits: 3, resolve: 6 },
  reaver: { might: 7, finesse: 4, wits: 2, resolve: 5 },
  arcanist: { might: 2, finesse: 4, wits: 8, resolve: 4 },
  stalker: { might: 3, finesse: 8, wits: 4, resolve: 3 },
};

export interface CreationChoice {
  name: string;
  archetype: ArchetypeId;
  background: BackgroundId;
  palette: string;
  model?: CharacterModel;
  weaponItem: string;
  ability: AbilityKind;
  startBoon: string;
  headgear?: boolean;
  cloak?: string;
  skin?: string;
}

export function createCharacter(c: CreationChoice, day = 1, seed = Date.now()): CharacterData {
  const a = ARCHETYPES[c.archetype];
  const bg = BACKGROUNDS[c.background];
  const ch: CharacterData = {
    version: 1, id: `hero-${seed.toString(36)}`, name: c.name.trim() || 'Nameless', archetype: c.archetype, background: c.background,
    model: c.model ?? a.model, palette: c.palette, headgear: c.headgear ?? true, cloak: c.cloak, skin: c.skin, level: 1, xp: 0, attributes: { ...START_ATTRS[c.archetype] }, points: 0,
    traits: [], traitPicks: 0, knowledge: [...bg.knowledge],
    equipment: Object.fromEntries(EQUIP_SLOTS.map((s) => [s, null])) as Record<EquipSlot, ItemInstance | null>,
    pack: new Array(PACK_SIZE).fill(null), gold: 25, ability: c.ability, startBoon: c.startBoon, conditions: [],
    mastery: {}, stats: { kills: 0, deaths: 0, expeditions: 0, bossesSlain: 0, goldEarned: 0, evolutions: [] },
    alive: true, createdDay: day, nextUid: 1,
  };
  const weapon = makeItem(ch, c.weaponItem);
  equip(ch, weapon, 'weapon');
  for (const id of bg.items) {
    const it = makeItem(ch, id);
    const slot = slotFor(ITEMS[id]);
    if (slot && !ch.equipment[slot]) equip(ch, it, slot);
    else addToPack(ch, it);
  }
  addToPack(ch, makeItem(ch, 'health_draught', { qty: 2 }));
  return ch;
}

/* ----------------------------------------------------------------- items -- */

export function makeItem(ch: CharacterData | null, defId: string, o: { qty?: number; rarity?: number; seed?: number; affixes?: ItemInstance['affixes'] } = {}): ItemInstance {
  const def = ITEMS[defId];
  if (!def) throw new Error(`unknown item ${defId}`);
  const uid = ch ? `i${ch.nextUid++}` : `i${Math.floor(Math.random() * 1e9).toString(36)}`;
  const it: ItemInstance = { uid, def: defId, qty: o.qty ?? 1, rarity: o.rarity ?? def.rarity, affixes: o.affixes ?? [] };
  if (def.base && !o.affixes) {
    const rng = new Rng(o.seed ?? Math.floor(Math.random() * 1e9));
    const n = Math.min(3, it.rarity);
    const pool = AFFIXES.filter((a) => a.slots.includes(def.kind));
    const picked = new Set<string>();
    let hasPrefix = false, hasSuffix = false;
    for (let k = 0; k < n && pool.length; k++) {
      const cands = pool.filter((a) => !picked.has(a.id) && (a.prefix ? !hasPrefix || n > 2 : !hasSuffix || n > 2));
      if (!cands.length) break;
      const a = rng.pick(cands);
      picked.add(a.id);
      if (a.prefix) hasPrefix = true; else hasSuffix = true;
      it.affixes.push({ id: a.id, tier: Math.max(0, Math.min(3, it.rarity - 1 + rng.int(0, 1))) });
    }
  }
  return it;
}

export function itemName(it: ItemInstance) {
  if (it.name) return it.name;
  const def = ITEMS[it.def];
  const pre = it.affixes.map((a) => AFFIXES.find((x) => x.id === a.id)!).find((a) => a?.prefix);
  const suf = it.affixes.map((a) => AFFIXES.find((x) => x.id === a.id)!).find((a) => a && !a.prefix);
  return [pre?.name, def.name, suf?.name].filter(Boolean).join(' ');
}

export function rarityName(it: ItemInstance) { return RARITY_NAMES[Math.min(RARITY_NAMES.length - 1, it.rarity)]; }

export function itemMods(it: ItemInstance): StatMod[] {
  const def = ITEMS[it.def];
  const out: StatMod[] = (def.mods ?? []).map((m) => ({ ...m, source: `item:${it.uid}` }));
  for (const a of it.affixes) {
    const ad = AFFIXES.find((x) => x.id === a.id);
    if (ad) for (const m of ad.mods(a.tier)) out.push({ ...m, source: `item:${it.uid}` });
  }
  return out;
}

export function itemLines(it: ItemInstance): string[] {
  return it.affixes.map((a) => AFFIXES.find((x) => x.id === a.id)?.text(a.tier) ?? '');
}

export function slotFor(def: ItemDef): EquipSlot | null {
  switch (def.kind) {
    case 'weapon': return 'weapon';
    case 'offhand': return 'offhand';
    case 'head': return 'head';
    case 'body': return 'body';
    case 'cloak': return 'cloak';
    case 'amulet': return 'amulet';
    case 'ring': return 'ring1';
    case 'relic': return 'relic';
    default: return null;
  }
}

export function fitsSlot(def: ItemDef, slot: EquipSlot) {
  if (slot === 'ring1' || slot === 'ring2') return def.kind === 'ring';
  if (slot === 'offhand') return def.kind === 'offhand' || (def.kind === 'weapon' && !!def.weapon);
  return def.kind === slot;
}

export function addToPack(ch: CharacterData, it: ItemInstance): boolean {
  const def = ITEMS[it.def];
  if (def.stack) {
    for (const p of ch.pack) {
      if (p && p.def === it.def && p.qty < def.stack) {
        const room = def.stack - p.qty;
        const take = Math.min(room, it.qty);
        p.qty += take;
        it.qty -= take;
        if (it.qty <= 0) return true;
      }
    }
  }
  const i = ch.pack.indexOf(null);
  if (i < 0) return false;
  ch.pack[i] = it;
  return true;
}

export function packFree(ch: CharacterData) { return ch.pack.filter((p) => !p).length; }

export function countItem(ch: CharacterData, defId: string) {
  let n = 0;
  for (const p of ch.pack) if (p?.def === defId) n += p.qty;
  for (const s of EQUIP_SLOTS) if (ch.equipment[s]?.def === defId) n += 1;
  return n;
}

export function takeItem(ch: CharacterData, defId: string, qty = 1): number {
  let left = qty;
  for (let i = 0; i < ch.pack.length && left > 0; i++) {
    const p = ch.pack[i];
    if (!p || p.def !== defId) continue;
    const t = Math.min(left, p.qty);
    p.qty -= t;
    left -= t;
    if (p.qty <= 0) ch.pack[i] = null;
  }
  return qty - left;
}

export function findItem(ch: CharacterData, uid: string): { where: 'pack' | 'equip'; index: number | EquipSlot; item: ItemInstance } | null {
  const i = ch.pack.findIndex((p) => p?.uid === uid);
  if (i >= 0) return { where: 'pack', index: i, item: ch.pack[i]! };
  for (const s of EQUIP_SLOTS) if (ch.equipment[s]?.uid === uid) return { where: 'equip', index: s, item: ch.equipment[s]! };
  return null;
}

/** Equip an item into a slot; whatever was there goes back to the pack. */
export function equip(ch: CharacterData, it: ItemInstance, slot: EquipSlot): boolean {
  const def = ITEMS[it.def];
  if (!fitsSlot(def, slot)) return false;
  const loc = findItem(ch, it.uid);
  if (loc?.where === 'pack') ch.pack[loc.index as number] = null;
  if (loc?.where === 'equip') ch.equipment[loc.index as EquipSlot] = null;
  const prev = ch.equipment[slot];
  ch.equipment[slot] = it;
  if (prev) {
    if (loc?.where === 'pack') ch.pack[loc.index as number] = prev;
    else if (!addToPack(ch, prev)) { ch.equipment[slot] = prev; return false; }
  }
  return true;
}

export function unequip(ch: CharacterData, slot: EquipSlot): boolean {
  const it = ch.equipment[slot];
  if (!it) return false;
  if (!addToPack(ch, it)) return false;
  ch.equipment[slot] = null;
  return true;
}

/** Everything the survivor has on them that the world can see. */
export function worldTags(ch: CharacterData): Set<string> {
  const tags = new Set<string>();
  for (const s of EQUIP_SLOTS) for (const t of ITEMS[ch.equipment[s]?.def ?? '']?.tags ?? []) tags.add(t);
  for (const p of ch.pack) if (p && ITEMS[p.def].kind === 'tool') for (const t of ITEMS[p.def].tags ?? []) tags.add(t);
  for (const t of ch.traits) for (const tag of TRAITS[t]?.tags ?? []) tags.add(tag);
  for (const k of ch.knowledge) tags.add(`knows:${k}`);
  tags.add(`bg:${ch.background}`);
  tags.add(`class:${ch.archetype}`);
  return tags;
}

/* -------------------------------------------------------------- progress -- */

export function xpForLevel(level: number) {
  return Math.round(120 * Math.pow(level, 1.55));
}

/** Character experience from the fight; returns levels gained. */
export function gainXp(ch: CharacterData, xp: number): number {
  ch.xp += xp;
  let gained = 0;
  while (ch.xp >= xpForLevel(ch.level)) {
    ch.xp -= xpForLevel(ch.level);
    ch.level++;
    ch.points += 2;
    if (ch.level % 2 === 0) ch.traitPicks++;
    gained++;
  }
  return gained;
}

/* ------------------------------------------------------------ derivation -- */

export interface CombatKit {
  stats: StatBlock;
  weapons: Array<{ id: string; rank: number }>;
  triggers: Array<{ def: TriggerDef; source: string }>;
  ability: AbilityKind;
  gearIds: Set<string>;
  gearStatuses: Set<StatusKind>;
  startLevels: number;
  revives: number;
  rerolls: number;
}

/** The survivor as the Battle needs them: stats with every source folded in. */
export function deriveKit(ch: CharacterData): CombatKit {
  const a = ARCHETYPES[ch.archetype];
  const st = new StatBlock();
  const at = ch.attributes;
  st.setBase({
    maxHealth: a.base.maxHealth + (ch.level - 1) * 8, regen: a.base.regen, armor: a.base.armor,
    moveSpeed: a.base.moveSpeed, pickupRadius: a.base.pickupRadius, critChance: a.base.critChance,
    critDamage: 1.5, luck: 1,
  });
  const src = 'attributes';
  st.addAll([
    { stat: 'damage', kind: 'inc', value: at.might * 0.025, source: src },
    { stat: 'maxHealth', kind: 'flat', value: at.might * 4 + at.resolve * 3, source: src },
    { stat: 'critChance', kind: 'flat', value: at.finesse * 0.006, source: src },
    { stat: 'moveSpeed', kind: 'inc', value: at.finesse * 0.01, source: src },
    { stat: 'projectileSpeed', kind: 'inc', value: at.finesse * 0.02, source: src },
    { stat: 'cooldown', kind: 'more', value: -Math.min(0.3, at.wits * 0.01), source: src },
    { stat: 'area', kind: 'inc', value: at.wits * 0.02, source: src },
    { stat: 'xpGain', kind: 'inc', value: at.wits * 0.02, source: src },
    { stat: 'armor', kind: 'flat', value: at.resolve * 0.5, source: src },
    { stat: 'regen', kind: 'flat', value: at.resolve * 0.08, source: src },
    { stat: 'healing', kind: 'inc', value: at.resolve * 0.03, source: src },
  ]);
  const weapons: CombatKit['weapons'] = [];
  const triggers: CombatKit['triggers'] = [];
  const gearIds = new Set<string>();
  const gearStatuses = new Set<StatusKind>();
  for (const s of EQUIP_SLOTS) {
    const it = ch.equipment[s];
    if (!it) continue;
    const def = ITEMS[it.def];
    gearIds.add(def.id);
    st.addAll(itemMods(it));
    for (const t of def.triggers ?? []) triggers.push({ def: t, source: `item:${it.uid}` });
    for (const k of def.statuses ?? []) gearStatuses.add(k);
    if (def.weapon && (s === 'weapon' || s === 'offhand')) {
      // Mastery: every 60 kills with a weapon starts it a rank higher, to +2.
      const bonus = Math.min(2, Math.floor((ch.mastery[def.weapon.id] ?? 0) / 60));
      weapons.push({ id: def.weapon.id, rank: def.weapon.rank + bonus + Math.max(0, it.rarity - def.rarity) });
    }
  }
  let startLevels = 0, revives = 0, rerolls = 2;
  for (const t of ch.traits) {
    const td = TRAITS[t];
    if (!td) continue;
    if (td.mods) st.addAll(td.mods.map((m) => ({ ...m, source: `trait:${t}` })));
    for (const tr of td.triggers ?? []) triggers.push({ def: tr, source: `trait:${t}` });
    if (td.tags?.includes('ember_start')) startLevels++;
    if (td.tags?.includes('revive')) revives++;
    if (td.tags?.includes('reroll')) rerolls++;
  }
  for (const c of ch.conditions) {
    if (c.id === 'wounded') st.add({ stat: 'maxHealth', kind: 'more', value: -0.2, source: 'cond:wounded' });
    if (c.id === 'blightsick') st.add({ stat: 'regen', kind: 'flat', value: -0.8, source: 'cond:blightsick' });
    if (c.id === 'blessed') st.add({ stat: 'damage.holy', kind: 'inc', value: 0.15, source: 'cond:blessed' });
    if (c.id === 'rested') st.add({ stat: 'maxHealth', kind: 'inc', value: 0.05, source: 'cond:rested' });
  }
  return { stats: st, weapons, triggers, ability: ch.ability, gearIds, gearStatuses, startLevels, revives, rerolls };
}

/** Stat differences if `it` replaced what is in `slot`, for the compare view. */
export function compareStats(ch: CharacterData, it: ItemInstance, slot: EquipSlot) {
  const before = deriveKit(ch).stats;
  const clone: CharacterData = JSON.parse(JSON.stringify(ch));
  const itClone = JSON.parse(JSON.stringify(it)) as ItemInstance;
  clone.equipment[slot] = itClone;
  const after = deriveKit(clone).stats;
  const keys = ['maxHealth', 'armor', 'damage', 'cooldown', 'area', 'critChance', 'moveSpeed', 'regen', 'damage.fire', 'damage.frost', 'damage.holy', 'damage.physical', 'resist.fire', 'resist.nature'] as const;
  const out: Array<{ key: string; before: number; after: number }> = [];
  for (const k of keys) {
    const b = k.startsWith('resist') ? before.getRaw(k) : before.get(k), a = k.startsWith('resist') ? after.getRaw(k) : after.get(k);
    if (Math.abs(a - b) > 1e-4) out.push({ key: k, before: b, after: a });
  }
  return out;
}
