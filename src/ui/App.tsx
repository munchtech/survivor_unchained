import { render } from 'preact';
import { useEffect, useState } from 'preact/hooks';
import { screen, overlay, fade } from './store';
import { Hud } from './hud/Hud';
import { LevelUp } from './overlays/LevelUp';
import { Pause, Death } from './overlays/Menus';
import { ChapterEnd } from './overlays/Chapter';
import { WorldMap } from './overlays/Map';
import { Inventory } from './overlays/Inventory';
import { Dialogue } from './overlays/Dialogue';
import { Shop, Stash } from './overlays/Shop';
import { Rest } from './overlays/Rest';
import { Journal } from './overlays/Journal';
import { Sheet } from './overlays/Sheet';
import { Title } from './screens/Title';
import { Create } from './screens/Create';
import './theme.css';

/* The interface root. The HUD and overlays are laid out for a 900 px tall
 * screen and zoomed to the real one, so proportions hold everywhere and
 * text stays sharp (zoom re-lays out rather than scaling a bitmap). On a
 * squarer screen the width decides instead, so the widest panels (the shop,
 * the pack) still fit side to side. */

function useUiScale() {
  const calc = () => Math.max(0.6, Math.min(1.6, window.innerHeight / 900, window.innerWidth / 1320));
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
      {sc === 'title' && <Title />}
      {sc === 'create' && <Create />}
      {sc === 'play' && <Hud />}
      {ov === 'levelup' && <LevelUp />}
      {ov === 'pause' && <Pause />}
      {ov === 'inventory' && <Inventory />}
      {ov === 'dialogue' && <Dialogue />}
      {ov === 'shop' && <Shop />}
      {ov === 'stash' && <Stash />}
      {ov === 'rest' && <Rest />}
      {ov === 'journal' && <Journal />}
      {ov === 'character' && <Sheet />}
      {ov === 'death' && <Death />}
      {ov === 'chapter' && <ChapterEnd />}
      {ov === 'map' && <WorldMap />}
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
