import { useEffect, useState } from 'preact/hooks';
import { levelUp, type LevelUpView } from '../store';
import { Glyph } from '../components/Icon';
import { SCHOOL_UI, RARITY_UI } from '../palette';
import { Input } from '@/core/input';
import { BOONS } from '@/content/boons';
import { WEAPONS } from '@/content/weapons';
import { SCHOOLS, type School } from '@/sim/types';
import type { Offer } from '@/sim/battle';
import './levelup.css';

/* The ember draft.
 *
 * Time stops; three cards rise out of the dark. Every card says in one
 * glance what it is (the kicker: a new weapon, a rank, a boon, a rule), what
 * it touches (school colour, tags - lit when the build already has them),
 * and how rare it is (the frame). Evolutions arrive in gold and are never
 * mixed in by chance.
 *
 * Keys 1-4 take a card; the arrows and Enter work too, and a pad. For the
 * first moment after the cards appear they cannot be taken, so a key still
 * held from the fight does not spend a level by accident. */

const ARM_TIME = 380;

export function LevelUp() {
  const v = levelUp.value;
  if (!v) return null;
  return <Draft key={`${v.level}:${v.offers.map((o) => o.id + o.kind).join()}`} v={v} />;
}

function Draft({ v }: { v: LevelUpView }) {
  const [focus, setFocus] = useState(0);
  const [armed, setArmed] = useState(false);
  const [chosen, setChosen] = useState<number | null>(null);
  const [banishing, setBanishing] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setArmed(true), ARM_TIME);
    return () => clearTimeout(t);
  }, []);

  const take = (i: number) => {
    if (!armed || chosen !== null || i < 0 || i >= v.offers.length) return;
    if (banishing) {
      if (v.banishes > 0) v.banish(i);
      setBanishing(false);
      return;
    }
    setChosen(i);
    setTimeout(() => v.pick(i), 300);
  };

  useEffect(() => Input.on((a) => {
    if (a === 'pick1') take(0);
    else if (a === 'pick2') take(1);
    else if (a === 'pick3') take(2);
    else if (a === 'pick4') take(3);
    else if (a === 'left') setFocus((f) => (f + v.offers.length - 1) % v.offers.length);
    else if (a === 'right') setFocus((f) => (f + 1) % v.offers.length);
    else if (a === 'confirm' || a === 'dash') take(focus);
    else if (a === 'reroll') { if (armed && v.rerolls > 0 && chosen === null) v.reroll(); }
    else if (a === 'banish') { if (v.banishes > 0) setBanishing((b) => !b); }
    else if (a === 'cancel') setBanishing(false);
    else return;
    return true;
  }), [v, focus, armed, chosen, banishing]);

  return (
    <div class={`levelup${banishing ? ' banishing' : ''}${chosen !== null ? ' leaving' : ''}`}>
      <div class="lu-scrim" />
      <div class="lu-rays" />
      <div class="lu-head">
        <div class="lu-kicker">The ember rises</div>
        <div class="lu-level">
          <span class="lu-orn" />
          <span>Ember {v.level}</span>
          <span class="lu-orn r" />
        </div>
        {v.queued > 0 && <div class="lu-queued">{v.queued} more to choose</div>}
      </div>
      {v.tip && <div class="lu-tip"><Glyph k="scroll" size={15} /> {v.tip}</div>}
      <div class="lu-cards">
        {v.offers.map((o, i) => (
          <Card key={`${o.kind}:${o.id}:${o.branch ?? ''}`} o={o} i={i} fits={v.fits[i] ?? []}
            focused={focus === i} chosen={chosen === i} dimmed={chosen !== null && chosen !== i} armed={armed}
            onPick={() => take(i)} onHover={() => setFocus(i)} />
        ))}
      </div>
      <div class="lu-foot">
        <button class="btn small" disabled={v.rerolls <= 0 || !armed} onClick={() => v.reroll()}>
          <span class="key">{Input.keyLabel('reroll')}</span> Reroll <em>{v.rerolls}</em>
        </button>
        <button class={`btn small${banishing ? ' focus' : ''}`} disabled={v.banishes <= 0} onClick={() => setBanishing((b) => !b)}>
          <span class="key">{Input.keyLabel('banish')}</span> {banishing ? 'Choose a card to banish' : 'Banish'} <em>{v.banishes}</em>
        </button>
      </div>
    </div>
  );
}

function schoolOf(o: Offer): School | null {
  for (const t of o.tags) if ((SCHOOLS as string[]).includes(t)) return t as School;
  if (o.kind === 'weapon' || o.kind === 'rank') return WEAPONS[o.id]?.school ?? null;
  return null;
}

function kicker(o: Offer): string {
  switch (o.kind) {
    case 'weapon': return 'New skill';
    case 'rank': return `Skill · rank ${o.from} → ${o.to}`;
    case 'evolve': return 'Skill evolves';
    case 'boon': {
      const syn = BOONS[o.id]?.kind === 'synergy';
      if (!o.from) return syn ? 'Passive · combo' : 'Passive';
      return `Passive · rank ${o.from} → ${o.to}`;
    }
    default: return 'Respite';
  }
}

function Card({ o, i, fits, focused, chosen, dimmed, armed, onPick, onHover }: {
  o: Offer; i: number; fits: string[]; focused: boolean; chosen: boolean; dimmed: boolean; armed: boolean;
  onPick: () => void; onHover: () => void;
}) {
  const r = RARITY_UI[o.rarity] ?? 0;
  const school = schoolOf(o);
  const color = o.kind === 'evolve' ? '#ffd88a' : school ? SCHOOL_UI[school] : `var(--r${r})`;
  const syn = o.kind === 'boon' && BOONS[o.id]?.kind === 'synergy';
  const max = o.kind === 'rank' ? 8 : o.kind === 'boon' ? BOONS[o.id]?.max ?? 1 : 0;
  const cls = ['card', `rb-${r}`, `k-${o.kind}`, syn ? 'syn' : '', focused ? 'focus' : '', chosen ? 'chosen' : '', dimmed ? 'dimmed' : '', armed ? 'armed' : ''].filter(Boolean).join(' ');
  const evoFrom = o.kind === 'evolve' ? WEAPONS[o.id]?.name : null;
  return (
    <button class={cls} style={{ '--sc': color, animationDelay: `${60 + i * 80}ms` }} onClick={onPick} onMouseEnter={onHover}>
      <div class="card-frame" />
      <div class="card-kicker">{kicker(o)}</div>
      <div class="card-art">
        <div class="card-halo" />
        <div class="card-sigil" />
        <Glyph k={o.icon} size={62} color={color} stroke={1.4} glow={color} />
      </div>
      <div class="card-title">{o.title}</div>
      {evoFrom && <div class="card-evo">{evoFrom} <Glyph k="next" size={12} /> {o.title}</div>}
      {max > 1 && (
        <div class="card-pips">
          {Array.from({ length: max }, (_, k) => <i key={k} class={k < (o.from ?? 0) ? 'had' : k < (o.to ?? 0) ? 'gain' : ''} />)}
        </div>
      )}
      <div class="card-text">{o.kind === 'evolve' ? o.text.replace(/^.*? becomes .*?\. /, '') : o.text}</div>
      <div class="card-tags">
        {o.tags.filter((t) => t !== school).slice(0, 4).map((t) => <span key={t} class={fits.includes(t) ? 'fit' : ''}>{t}</span>)}
      </div>
      {fits.length > 0 && <div class="card-fit"><Glyph k="arcane" size={11} /> Fits your build</div>}
      <div class="card-foot">
        <span class={`card-rarity rarity-${r}`}>{o.kind === 'evolve' ? 'Legendary' : o.rarity}</span>
        <span class="key">{i + 1}</span>
      </div>
      <div class="card-banish"><Glyph k="lock" size={22} /> Banish</div>
    </button>
  );
}
