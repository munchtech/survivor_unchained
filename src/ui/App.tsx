import { render } from 'preact';
import { useEffect, useState } from 'preact/hooks';
import { screen, overlay, fade } from './store';
import { Hud } from './hud/Hud';
import { LevelUp } from './overlays/LevelUp';
import './theme.css';

/* The interface root. The HUD and overlays are laid out for a 900 px tall
 * screen and zoomed to the real one, so proportions hold everywhere and
 * text stays sharp (zoom re-lays out rather than scaling a bitmap). */

function useUiScale() {
  const calc = () => Math.max(0.72, Math.min(1.6, window.innerHeight / 900));
  const [s, setS] = useState(calc);
  useEffect(() => {
    const on = () => setS(calc());
    window.addEventListener('resize', on);
    return () => window.removeEventListener('resize', on);
  }, []);
  return s;
}

function App() {
  const s = useUiScale();
  const sc = screen.value;
  const ov = overlay.value;
  const f = fade.value;
  return (
    <div class="ui-root" style={{ zoom: s }}>
      {sc === 'play' && <Hud />}
      {ov === 'levelup' && <LevelUp />}
      <div class="fader" style={{ opacity: f.to, transitionDuration: `${f.seconds}s` }}>
        {f.caption && <div class="fader-caption">{f.caption}</div>}
        {f.sub && <div class="fader-sub">{f.sub}</div>}
      </div>
    </div>
  );
}

export function mountUi(el: HTMLElement) {
  render(<App />, el);
}
