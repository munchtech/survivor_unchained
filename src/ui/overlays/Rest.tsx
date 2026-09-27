import { restView } from '../store';
import { actions } from '@/game/actions';
import { Glyph } from '../components/Icon';
import './menus.css';

/* A night at the Last Lamp: the choice, then the morning after. */

export function Rest() {
  const r = restView.value;
  if (!r) return null;
  if (r.phase === 'report') {
    return (
      <div class="menu-overlay">
        <div class="report parchment rise-in">
          <div class="report-day">Day {r.day}</div>
          <div class="report-sub">Morning, at the Last Lamp</div>
          <div class="report-rule" />
          {r.lines.map((l, i) => <p key={i} style={{ animationDelay: `${300 + i * 350}ms` }}>{l}</p>)}
          <button class="btn primary" onClick={() => actions.finishRest()}>Get up</button>
        </div>
      </div>
    );
  }
  return (
    <div class="menu-overlay">
      <div class="scrim fade-in" onClick={() => actions.closeOverlay()} />
      <div class="pause panel rise-in rest">
        <div class="pause-title title-cap">The Last Lamp</div>
        <div class="rule" />
        <button class="pause-item" disabled={!r.afford} onClick={() => actions.rest('sleep')}>
          Sleep until morning <span class="rest-cost">{r.cost ? <><Glyph k="coin" size={13} /> {r.cost}</> : 'on the house'}</span>
        </button>
        {r.canNight && <button class="pause-item" onClick={() => actions.rest('night')}>Wait until nightfall</button>}
        <button class="pause-item" onClick={() => actions.closeOverlay()}>Not yet</button>
        <p class="rest-note">Sleeping lets a day pass. The world will not wait for you — and the ember goes out while you sleep.</p>
      </div>
    </div>
  );
}
