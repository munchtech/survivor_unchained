import { useMemo, useState } from 'preact/hooks';
import { character, rev } from '../store';
import { actions } from '@/game/actions';
import { ITEMS, type EquipSlot } from '@/content/items';
import { ARCHETYPES, BACKGROUNDS } from '@/content/archetypes';
import { deriveKit, slotFor, itemName, type ItemInstance, type CharacterData } from '@/rpg/character';
import { armorReduction } from '@/sim/stats';
import { Glyph, Icon } from '../components/Icon';
import { ItemCard } from '../components/ItemCard';
import { renderPortrait } from '../portrait';
import { lookOf } from '@/game/loadout';
import './inventory.css';

/* The pack. On the left, the survivor as they stand, with what they wear
 * around them; on the right, what they carry. Hover to read and compare,
 * click to choose, and the choice's panel says what can be done with it. */

const LEFT: EquipSlot[] = ['head', 'amulet', 'body', 'cloak'];
const RIGHT: EquipSlot[] = ['weapon', 'offhand', 'ring1', 'ring2', 'relic'];
const SLOT_NAME: Record<EquipSlot, string> = { weapon: 'Weapon', offhand: 'Off-hand', head: 'Head', body: 'Body', cloak: 'Cloak', amulet: 'Amulet', ring1: 'Ring', ring2: 'Ring', relic: 'Relic' };
const SLOT_GLYPH: Record<EquipSlot, string> = { weapon: 'sword', offhand: 'shield', head: 'helm', body: 'armor', cloak: 'cloak', amulet: 'amulet', ring1: 'ring', ring2: 'ring', relic: 'relic' };

export function Inventory() {
  void rev.value;
  const ch = character.value;
  const [hover, setHover] = useState<{ it: ItemInstance; x: number; y: number } | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  const portraitKey = ch ? `${ch.archetype}|${ch.model}|${ch.equipment.weapon?.def}|${ch.palette}|${ch.headgear}` : '';
  const portrait = useMemo(() => ch && renderPortrait(lookOf(ch)), [portraitKey]);
  if (!ch) return null;
  const selected = sel ? findAny(ch, sel) : null;

  const onHover = (it: ItemInstance | null, e?: MouseEvent) => {
    if (!it || !e) { setHover(null); return; }
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const zoom = Number((document.querySelector('.ui-root') as HTMLElement)?.style.zoom || 1);
    setHover({ it, x: r.right / zoom + 10, y: r.top / zoom });
  };

  return (
    <div class="inv-overlay">
      <div class="scrim fade-in" onClick={() => actions.closeOverlay()} />
      <div class="inv panel rise-in">
        <div class="inv-head">
          <div class="title-cap">Pack</div>
          <button class="btn small" onClick={() => actions.closeOverlay()}><span class="key">I</span> Close</button>
        </div>
        <div class="inv-body">
          <section class="doll">
            <div class="doll-col">{LEFT.map((s) => <EquipSlotView key={s} slot={s} ch={ch} sel={sel} onSel={setSel} onHover={onHover} />)}</div>
            <div class="doll-figure">
              <div class="doll-halo" />
              {portrait && <img src={portrait} draggable={false} alt="" />}
              <div class="doll-name">{ch.name}</div>
              <div class="doll-sub">Level {ch.level} {BACKGROUNDS[ch.background].name} {ARCHETYPES[ch.archetype].name}</div>
            </div>
            <div class="doll-col">{RIGHT.map((s) => <EquipSlotView key={s} slot={s} ch={ch} sel={sel} onSel={setSel} onHover={onHover} />)}</div>
            <Stats ch={ch} />
          </section>
          <section class="pack">
            <div class="pack-grid">
              {ch.pack.map((it, i) => (
                <div key={i} class={`pslot${it ? ` rb-${it.rarity} filled` : ''}${it && sel === it.uid ? ' sel' : ''}`}
                  onMouseEnter={(e) => onHover(it, e)} onMouseLeave={() => onHover(null)}
                  onClick={() => it && setSel(sel === it.uid ? null : it.uid)}
                  onDblClick={() => it && primary(it)}>
                  {it && <Icon k={ITEMS[it.def].icon} size={52} />}
                  {it && it.qty > 1 && <span class="pslot-qty">{it.qty}</span>}
                  {it && slotFor(ITEMS[it.def]) && <span class="pslot-dot" />}
                </div>
              ))}
            </div>
            <div class="pack-foot">
              <span class="gold"><Glyph k="coin" size={16} color="#f3d9a0" /> {ch.gold}</span>
              <span class="pack-count">{ch.pack.filter(Boolean).length} / {ch.pack.length}</span>
              <span class="pack-hint">Double-click to wear or use</span>
            </div>
          </section>
          <section class="inv-detail">
            {selected ? (
              <ItemCard it={selected.it} ch={ch} compare={selected.where === 'pack'}>
                <div class="ic-actions">
                  {selected.where === 'pack' && ITEMS[selected.it.def].kind === 'consumable' && <button class="btn small primary" onClick={() => actions.useItem(selected.it.uid)}>Use</button>}
                  {selected.where === 'pack' && slotFor(ITEMS[selected.it.def]) && <button class="btn small primary" onClick={() => actions.equipItem(selected.it.uid)}>Wear</button>}
                  {selected.where === 'equip' && selected.slot !== 'weapon' && <button class="btn small" onClick={() => { actions.unequip(selected.slot!); }}>Take off</button>}
                  {selected.where === 'pack' && ITEMS[selected.it.def].kind !== 'quest' && <button class="btn small" onClick={() => { actions.dropItem(selected.it.uid); setSel(null); }}>Leave behind</button>}
                </div>
              </ItemCard>
            ) : (
              <div class="inv-empty">
                <Glyph k="hand" size={28} />
                <p>Choose something to look at it closely.</p>
                <p class="dim">Gear stays with you. Ember fades when you rest; what you carry, and what you wear, does not.</p>
              </div>
            )}
          </section>
        </div>
      </div>
      {hover && hover.it.uid !== sel && (
        <div class="inv-tip" style={{ left: `${hover.x}px`, top: `${hover.y}px` }}>
          <ItemCard it={hover.it} ch={ch} compare />
        </div>
      )}
    </div>
  );
}

function primary(it: ItemInstance) {
  const def = ITEMS[it.def];
  if (def.kind === 'consumable') actions.useItem(it.uid);
  else if (slotFor(def)) actions.equipItem(it.uid);
}

function findAny(ch: CharacterData, uid: string): { it: ItemInstance; where: 'pack' | 'equip'; slot?: EquipSlot } | null {
  for (const [s, it] of Object.entries(ch.equipment)) if (it?.uid === uid) return { it, where: 'equip', slot: s as EquipSlot };
  const it = ch.pack.find((p) => p?.uid === uid);
  return it ? { it, where: 'pack' } : null;
}

function EquipSlotView({ slot, ch, sel, onSel, onHover }: { slot: EquipSlot; ch: CharacterData; sel: string | null; onSel: (u: string | null) => void; onHover: (it: ItemInstance | null, e?: MouseEvent) => void }) {
  const it = ch.equipment[slot];
  return (
    <div class={`eslot${it ? ` rb-${it.rarity} filled` : ''}${it && sel === it.uid ? ' sel' : ''}`}
      onMouseEnter={(e) => it && onHover(it, e)} onMouseLeave={() => onHover(null)}
      onClick={() => it && onSel(sel === it.uid ? null : it.uid)} title={it ? itemName(it) : SLOT_NAME[slot]}>
      {it ? <Icon k={ITEMS[it.def].icon} size={56} /> : <Glyph k={SLOT_GLYPH[slot]} size={28} color="rgba(217,181,106,0.22)" />}
      <span class="eslot-name">{SLOT_NAME[slot]}</span>
    </div>
  );
}

function Stats({ ch }: { ch: CharacterData }) {
  const k = deriveKit(ch).stats;
  const rows: Array<[string, string]> = [
    ['Health', String(Math.round(k.get('maxHealth')))],
    ['Armour', `${Math.round(k.get('armor'))} (${Math.round(armorReduction(k.get('armor')) * 100)}%)`],
    ['Damage', `${Math.round((k.get('damage') - 1) * 100) >= 0 ? '+' : ''}${Math.round((k.get('damage') - 1) * 100)}%`],
    ['Speed', k.get('moveSpeed').toFixed(1)],
    ['Critical', `${Math.round(k.get('critChance') * 100)}%`],
    ['Regeneration', `${k.get('regen').toFixed(1)}/s`],
  ];
  return (
    <div class="doll-stats">
      {rows.map(([a, b]) => <div key={a}><span>{a}</span><b>{b}</b></div>)}
    </div>
  );
}
