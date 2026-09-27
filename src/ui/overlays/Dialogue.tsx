import { useEffect, useState } from 'preact/hooks';
import { dialogue, character } from '../store';
import { actions } from '@/game/actions';
import { Input } from '@/core/input';
import { Glyph } from '../components/Icon';
import './dialogue.css';

/* A conversation. The person on the left, as they look to you; what they
 * say, arriving at the pace of speech (a click or a key hurries it); what
 * you can say back. Choices your background or kit opens carry a badge in
 * its colour; choices you cannot take are shown anyway, greyed, with the
 * reason - so the player learns there was another way. */

const BADGE_TONE: Record<string, string> = { Beastlore: 'hunter', Arcana: 'scholar', Underworld: 'outcast', Faith: 'devout', Outcast: 'outcast', Hunter: 'hunter', Scholar: 'scholar', Devout: 'devout' };

export function Dialogue() {
  const d = dialogue.value;
  if (!d) return null;
  return <Talk key={d.key} d={d} />;
}

function Talk({ d }: { d: NonNullable<typeof dialogue.value> }) {
  const [shown, setShown] = useState(0);
  const full = shown >= d.text.length;
  useEffect(() => {
    if (full) return;
    const t = setInterval(() => setShown((n) => Math.min(d.text.length, n + 2)), 22);
    return () => clearInterval(t);
  }, [full, d.text]);
  const enabled = d.choices.filter((c) => c.enabled);
  useEffect(() => Input.on((a) => {
    const n = ['pick1', 'pick2', 'pick3', 'pick4'].indexOf(a);
    if (n < 0 && a !== 'confirm' && a !== 'interact' && a !== 'dash') {
      if (a === 'cancel' || a === 'pause') { const leave = d.choices.find((c) => c.ends && c.enabled); if (leave) actions.choose(leave.index); return true; }
      return;
    }
    if (!full) { setShown(d.text.length); return true; }
    if (n >= 0) { const c = d.choices[n]; if (c?.enabled) actions.choose(c.index); return true; }
    if (d.canContinue) actions.advance();
    else if (enabled.length === 1) actions.choose(enabled[0].index);
    return true;
  }), [d, full]);
  const name = character.value?.name ?? '';
  return (
    <div class="dlg-overlay" onClick={() => { if (!full) setShown(d.text.length); }}>
      <div class="dlg-shade" />
      <div class="dlg rise-in">
        <div class="dlg-portrait">
          <div class="dlg-frame">
            {d.portrait && <img src={d.portrait} alt="" draggable={false} />}
            {!d.portrait && d.glyph && <div class="dlg-glyph"><Glyph k={d.glyph} size={96} color="#e8c890" glow="rgba(255,170,80,0.5)" stroke={1.2} /></div>}
          </div>
          <div class="dlg-name">{d.name}</div>
          <div class="dlg-title">{d.title}</div>
          <div class="dlg-mood"><Glyph k="eye" size={12} /> {d.mood}</div>
        </div>
        <div class="dlg-main">
          {d.speaker !== 'npc' && <div class="dlg-speaker">{d.speaker === 'player' ? name : ''}</div>}
          <div class={`dlg-text ${d.speaker}`}>
            {d.text.slice(0, shown)}
            <span class="dlg-rest">{d.text.slice(shown)}</span>
          </div>
          <div class={`dlg-choices${full ? ' ready' : ''}`}>
            {d.choices.map((c, i) => (
              <button key={c.index} class={`dlg-choice${c.enabled ? '' : ' locked'}${c.ends ? ' ends' : ''}${c.action ? ' act' : ''}`} disabled={!c.enabled}
                style={{ animationDelay: `${i * 50}ms` }}
                onClick={(e) => { e.stopPropagation(); if (!full) { setShown(d.text.length); return; } if (c.enabled) actions.choose(c.index); }}>
                <span class="key">{i + 1}</span>
                {c.badge && <span class={`dlg-badge ${BADGE_TONE[c.badge] ?? 'item'}`}>{c.badge}</span>}
                <span class="dlg-choice-text">{c.text}</span>
                {c.locked && <span class="dlg-lock"><Glyph k="lock" size={12} /> {c.locked}</span>}
              </button>
            ))}
            {d.canContinue && (
              <button class="dlg-choice cont" onClick={(e) => { e.stopPropagation(); if (!full) setShown(d.text.length); else actions.advance(); }}>
                <span class="key">{Input.keyLabel('confirm')}</span><span class="dlg-choice-text">Continue</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
