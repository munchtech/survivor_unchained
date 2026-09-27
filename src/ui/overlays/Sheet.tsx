import { useMemo } from 'preact/hooks';
import { character, rev } from '../store';
import { actions } from '@/game/actions';
import { ARCHETYPES, BACKGROUNDS, TRAITS, LEVELUP_TRAITS } from '@/content/archetypes';
import { ABILITIES } from '@/content/abilities';
import { deriveKit, xpForLevel, type Attributes } from '@/rpg/character';
import { armorReduction } from '@/sim/stats';
import { Glyph } from '../components/Icon';
import { renderPortrait } from '../portrait';
import { loadoutFor } from '@/game/loadout';
import './sheet.css';

/* Who the survivor has become: level, attributes to spend, traits chosen
 * and earned, what they know, and what ails them. */

const ATTRS: Array<{ id: keyof Attributes; name: string; text: string }> = [
  { id: 'might', name: 'Might', text: '+2.5% damage and +4 health per point' },
  { id: 'finesse', name: 'Finesse', text: '+0.6% critical chance and +1% speed per point' },
  { id: 'wits', name: 'Wits', text: '+1% weapon speed, +2% area and ember per point' },
  { id: 'resolve', name: 'Resolve', text: '+3 health, +0.5 armour, +0.08 regeneration per point' },
];
const KNOW: Record<string, string> = { beastlore: 'Beastlore', arcana: 'Arcana', underworld: 'The Underworld', faith: 'The Faith' };
const COND: Record<string, string> = { wounded: 'Wounded: 20% less health until it heals', blightsick: 'Blight-sick: your wounds close slowly', poisoned: 'Poisoned', blessed: 'Blessed: +15% holy damage', rested: 'Rested: +5% health', wolfscent: 'Wolf-scented', hunted: 'Hunted' };

export function Sheet() {
  void rev.value;
  const ch = character.value;
  const portrait = useMemo(() => ch && renderPortrait(loadoutFor({ archetype: ch.archetype, weaponItem: ch.equipment.weapon?.def ?? ARCHETYPES[ch.archetype].weapons[0], model: ch.model, palette: ch.palette, headgear: ch.headgear }), 260, 360), [ch?.equipment.weapon?.def]);
  const offer = useMemo(() => {
    if (!ch) return [];
    const pool = LEVELUP_TRAITS.filter((t) => !ch.traits.includes(t));
    const seed = ch.level * 7 + ch.traits.length * 13;
    return [...pool].sort((a, b) => ((a.length * seed) % 17) - ((b.length * seed) % 17)).slice(0, 3);
  }, [ch?.level, ch?.traits.length]);
  if (!ch) return null;
  const k = deriveKit(ch).stats;
  const need = xpForLevel(ch.level);
  return (
    <div class="inv-overlay">
      <div class="scrim fade-in" onClick={() => actions.closeOverlay()} />
      <div class="inv panel rise-in sheet">
        <div class="inv-head">
          <div class="title-cap">{ch.name}</div>
          <button class="btn small" onClick={() => actions.closeOverlay()}><span class="key">C</span> Close</button>
        </div>
        <div class="sheet-body">
          <section class="sheet-left">
            {portrait && <img src={portrait} alt="" draggable={false} />}
            <div class="sheet-id">Level {ch.level} {BACKGROUNDS[ch.background].name} {ARCHETYPES[ch.archetype].name}</div>
            <div class="xp"><div class="xp-fill" style={{ width: `${Math.min(1, ch.xp / need) * 100}%` }} /><span>{ch.xp} / {need}</span></div>
            <div class="sheet-ab"><Glyph k={ABILITIES[ch.ability].icon} size={18} /> {ABILITIES[ch.ability].name}</div>
            <div class="sheet-know">Knows: {ch.knowledge.filter((x) => KNOW[x]).map((x) => KNOW[x]).join(', ') || 'little'}</div>
          </section>
          <section>
            <div class="sub-label">Attributes {ch.points > 0 && <span class="pts">{ch.points} to spend</span>}</div>
            {ATTRS.map((a) => (
              <div key={a.id} class="attr">
                <div class="attr-val">{ch.attributes[a.id]}</div>
                <div><div class="attr-name">{a.name}</div><div class="attr-text">{a.text}</div></div>
                {ch.points > 0 && <button class="btn small" onClick={() => actions.spendPoint(a.id)}>+</button>}
              </div>
            ))}
            <div class="sub-label" style={{ marginTop: '16px' }}>Standing</div>
            <div class="doll-stats sheet-stats">
              <div><span>Health</span><b>{Math.round(k.get('maxHealth'))}</b></div>
              <div><span>Armour</span><b>{Math.round(armorReduction(k.get('armor')) * 100)}%</b></div>
              <div><span>Damage</span><b>+{Math.round((k.get('damage') - 1) * 100)}%</b></div>
              <div><span>Speed</span><b>{k.get('moveSpeed').toFixed(1)}</b></div>
              <div><span>Critical</span><b>{Math.round(k.get('critChance') * 100)}%</b></div>
              <div><span>Area</span><b>+{Math.round((k.get('area') - 1) * 100)}%</b></div>
            </div>
          </section>
          <section>
            <div class="sub-label">Traits {ch.traitPicks > 0 && <span class="pts">choose {ch.traitPicks}</span>}</div>
            {ch.traits.length === 0 && ch.traitPicks === 0 && <p class="sheet-empty">None yet. Traits come with levels, and with what you do.</p>}
            {ch.traits.map((t) => (
              <div key={t} class={`trait ${TRAITS[t]?.source}`}>
                <div class="trait-name">{TRAITS[t]?.name ?? t}{TRAITS[t]?.source === 'world' && <span> · earned</span>}</div>
                <div class="trait-text">{TRAITS[t]?.text}</div>
              </div>
            ))}
            {ch.traitPicks > 0 && offer.map((t) => (
              <button key={t} class="trait offer" onClick={() => actions.pickTrait(t)}>
                <div class="trait-name">{TRAITS[t].name}</div>
                <div class="trait-text">{TRAITS[t].text}</div>
              </button>
            ))}
            {ch.conditions.length > 0 && <div class="sub-label" style={{ marginTop: '16px' }}>Conditions</div>}
            {ch.conditions.map((c) => <div key={c.id} class={`cond ${c.id === 'blessed' || c.id === 'rested' ? 'good' : 'bad'}`}>{COND[c.id] ?? c.id} <span>{c.days} day{c.days === 1 ? '' : 's'}</span></div>)}
          </section>
        </div>
      </div>
    </div>
  );
}
