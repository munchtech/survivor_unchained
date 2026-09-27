import { useMemo } from 'preact/hooks';
import { character, worldView, rev } from '../store';
import { actions } from '@/game/actions';
import { chapterSummary } from '@/content/chapter';
import { Glyph } from '../components/Icon';
import './chapter.css';

/* The end of the first chapter: the survivor's own book, closed for now.
 * Left page: what was done and what is still waiting. Right page: who
 * remembers, and how. It is read back from the world, not written down. */

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export function ChapterEnd() {
  void rev.value;
  const ch = character.value, w = worldView.value;
  const sum = useMemo(() => (ch && w ? chapterSummary(ch, w) : null), [ch, w, rev.value]);
  if (!sum) return null;
  let beat = 0;
  const d = () => ({ animationDelay: `${0.5 + (beat++) * 0.12}s` });
  return (
    <div class="chapter-overlay">
      <div class="ch-vignette fade-in" />
      <div class="ch-wrap">
        <div class="ch-head">
          <div class="ch-kicker">The end of the first chapter</div>
          <h1 class="ch-title">The Waystation</h1>
          <div class="ch-epithet">{sum.epithet}</div>
        </div>
        <div class="ch-book parchment">
          <div class="ch-page">
            <h2 class="ch-h" style={d()}>What was done</h2>
            {sum.threads.map((t) => (
              <div key={t.id} class={`ch-thread tone-${t.tone}`} style={d()}>
                <div class="ch-thread-head">
                  <span class="ch-thread-name"><Glyph k="quest" size={15} /> {t.name}</span>
                  <span class="ch-verdict">{t.verdict}</span>
                </div>
                <p class="ch-outcome">{t.outcome}</p>
                {t.beats.length > 0 && <ul class="ch-beats">{t.beats.slice(-3).map((b) => <li key={b}>{b}</li>)}</ul>}
              </div>
            ))}
            <h2 class="ch-h" style={d()}>Still waiting</h2>
            {sum.open.map((o) => (
              <div key={o.id} class="ch-open" style={d()}>
                <div class="ch-open-name"><Glyph k="eye" size={15} /> {o.name}</div>
                <p>{o.line}</p>
              </div>
            ))}
          </div>
          <div class="ch-page">
            <h2 class="ch-h" style={d()}>Who remembers you</h2>
            {sum.people.length === 0 && <p class="ch-empty" style={d()}>Nobody, yet. You kept to yourself.</p>}
            {sum.people.map((p) => (
              <div key={p.id} class="ch-person" style={d()}>
                <div class="ch-person-head">
                  <span class="ch-person-name">{p.name}</span>
                  <span class="ch-person-role">{p.role}</span>
                </div>
                <div class={`ch-regard${p.warmth >= 25 ? ' warm' : p.warmth <= -25 ? ' cold' : ''}`}>{cap(p.regard)}</div>
                {p.knows && <div class="ch-knows">Knows that you {p.knows}.</div>}
              </div>
            ))}
            <h2 class="ch-h" style={d()}>What the world says you did</h2>
            {sum.deeds.length === 0 && <p class="ch-empty" style={d()}>Nothing it has noticed. Give it time.</p>}
            <ul class="ch-deeds" style={d()}>{sum.deeds.map((t) => <li key={t}>You {t}.</li>)}</ul>
            <div class="ch-stats" style={d()}>
              {sum.stats.map((s) => <div key={s.label}><b>{s.value}</b><span>{s.label}</span></div>)}
            </div>
          </div>
        </div>
        <div class="ch-actions">
          <button class="btn" onClick={() => actions.closeOverlay()}>Keep walking</button>
          <button class="btn primary" onClick={() => actions.quitToTitle()}>Return to the fire</button>
        </div>
        <div class="ch-note">Your journey is saved. The second chapter begins where this one leaves off.</div>
      </div>
    </div>
  );
}
