import { ITEMS, RARITY_NAMES, type EquipSlot } from '@/content/items';
import { WEAPONS } from '@/content/weapons';
import { itemName, itemLines, compareStats, slotFor, type ItemInstance, type CharacterData } from '@/rpg/character';
import { Glyph, Icon } from './Icon';
import { SCHOOL_UI } from '../palette';

/* Everything an item is, on one card: what it does to the fight, what it
 * says to the world, what it costs, and where it came from. Hovered items
 * compare themselves against what they would replace. */

export const TAG_LINES: Record<string, string> = {
  beastscent: 'Wolves smell the forest on you, not the town.',
  kerchief_colors: 'Kerchiefs read you as one of theirs. So does the Watch.',
  plague_mask: 'You can breathe where the air is blighted.',
  holy_light: 'The dead do not like its light.',
  necromantic: 'The Order of Morning Light will not approve.',
  lockpick: 'Opens simple locks.',
  scholar_lens: 'Old script becomes legible through it.',
  wolf_fang: 'A statement to any wolf that sees it.',
  fireproof: 'Fire finds little purchase.',
  digger_lamp: 'The lamplings know whose it is.',
  moon_touched: 'Something in the grove marked you.',
  explosive: 'Something could be blown open with this. Or up.',
  warden_iron: 'Remembers the light it held.',
};

const KIND_NAMES: Record<string, string> = {
  weapon: 'Weapon', offhand: 'Off-hand', head: 'Head', body: 'Body', cloak: 'Cloak', amulet: 'Amulet', ring: 'Ring', relic: 'Relic',
  material: 'Material', consumable: 'Consumable', quest: 'Quest item', tool: 'Tool', trophy: 'Trophy',
};

const STAT_NAMES: Record<string, string> = {
  maxHealth: 'Health', armor: 'Armour', damage: 'Damage', cooldown: 'Weapon speed', area: 'Area', critChance: 'Critical chance',
  moveSpeed: 'Speed', regen: 'Regeneration', 'damage.fire': 'Fire damage', 'damage.frost': 'Frost damage', 'damage.holy': 'Holy damage',
  'damage.physical': 'Physical damage', 'resist.fire': 'Fire resistance', 'resist.nature': 'Nature resistance',
};

function fmtDelta(key: string, before: number, after: number): { text: string; good: boolean } {
  const d = after - before;
  if (key === 'cooldown') {
    const pct = Math.round((before / after - 1) * 100);
    return { text: `${pct >= 0 ? '+' : ''}${pct}% ${STAT_NAMES[key]}`, good: pct >= 0 };
  }
  if (key === 'moveSpeed') {
    const pct = Math.round((after / before - 1) * 100);
    return { text: `${pct >= 0 ? '+' : ''}${pct}% ${STAT_NAMES[key]}`, good: pct >= 0 };
  }
  if (key === 'maxHealth' || key === 'armor') return { text: `${d > 0 ? '+' : ''}${Math.round(d * 10) / 10} ${STAT_NAMES[key]}`, good: d > 0 };
  if (key === 'regen') return { text: `${d > 0 ? '+' : ''}${d.toFixed(1)}/s ${STAT_NAMES[key]}`, good: d > 0 };
  const pct = Math.round(d * 1000) / 10;
  return { text: `${pct > 0 ? '+' : ''}${pct}% ${STAT_NAMES[key] ?? key}`, good: d > 0 };
}

export function ItemCard({ it, ch, compare, children }: { it: ItemInstance; ch: CharacterData | null; compare?: boolean; children?: preact.ComponentChildren }) {
  const def = ITEMS[it.def];
  const w = def.weapon ? WEAPONS[def.weapon.id] : null;
  const slot = slotFor(def);
  let diffs: Array<{ key: string; before: number; after: number }> = [];
  let against: ItemInstance | null = null;
  if (compare && ch && slot) {
    const target: EquipSlot = slot === 'ring1' && ch.equipment.ring1 && !ch.equipment.ring2 ? 'ring2' : slot;
    against = ch.equipment[target];
    const isWorn = Object.values(ch.equipment).some((e) => e?.uid === it.uid);
    if (!isWorn) diffs = compareStats(ch, it, target);
  }
  const lines = itemLines(it);
  return (
    <div class={`item-card rb-${it.rarity}`}>
      <div class="ic-head">
        <div class="ic-photo"><Icon k={def.icon} size={58} /></div>
        <div>
          <div class={`ic-name rarity-${it.rarity}`}>{itemName(it)}</div>
          <div class="ic-kind">{RARITY_NAMES[it.rarity]} {KIND_NAMES[def.kind] ?? def.kind}{def.unique ? ' · Unique' : ''}</div>
        </div>
      </div>
      {w && (
        <div class="ic-weapon" style={{ color: SCHOOL_UI[w.school] }}>
          <Glyph k={w.art} size={15} /> {w.name} · rank {def.weapon!.rank} · {w.school}
        </div>
      )}
      <div class="ic-desc">{def.description}</div>
      {lines.length > 0 && <div class="ic-affixes">{lines.map((l) => <div key={l}>{l}</div>)}</div>}
      {def.downside && <div class="ic-down">{def.downside}</div>}
      {(def.tags ?? []).filter((t) => TAG_LINES[t]).map((t) => <div key={t} class="ic-world"><Glyph k="eye" size={13} /> {TAG_LINES[t]}</div>)}
      {def.lore && <div class="ic-lore">{def.lore}</div>}
      {it.history && it.history.length > 0 && <div class="ic-history">{it.history.map((h) => <div key={h}>{h}</div>)}</div>}
      {diffs.length > 0 && (
        <div class="ic-compare">
          <div class="ic-compare-head">Instead of {against ? itemName(against) : 'nothing'}</div>
          {diffs.map((d) => { const f = fmtDelta(d.key, d.before, d.after); return <div key={d.key} class={f.good ? 'up' : 'down'}>{f.text}</div>; })}
        </div>
      )}
      <div class="ic-foot">
        {it.qty > 1 && <span>×{it.qty}</span>}
        <span class="ic-value"><Glyph k="coin" size={13} /> {def.value * Math.max(1, it.qty)}</span>
      </div>
      {children}
    </div>
  );
}
