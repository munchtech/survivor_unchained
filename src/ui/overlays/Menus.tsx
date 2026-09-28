import { useEffect, useState } from 'preact/hooks';
import { actions } from '@/game/actions';
import { desktop } from '@/core/desktop';
import { Input } from '@/core/input';
import { Controls } from '../components/Controls';
import { overlayBack } from '../store';
import './menus.css';

/* The small overlays: the pause menu and the fall. */

export function Pause() {
  const [sound, setSound] = useState(() => actions.soundLevel());
  const [quality, setQuality] = useState(() => actions.quality());
  const [gore, setGore] = useState(() => actions.gore());
  const GORES = ['full', 'reduced', 'off'] as const;
  const [showControls, setShow] = useState(false);
  // Set at once, not in an effect: effects run after paint, and a quick
  // second Escape would find the old value.
  const setShowControls = (on: boolean) => { overlayBack.value = on ? () => setShowControls(false) : null; setShow(on); };
  const QUALITIES = ['high', 'medium', 'low'] as const;
  const items = [
    { label: 'Resume', act: () => actions.resume() },
    { label: 'Save', act: () => actions.saveNow() },
    { label: `Sound: ${{ on: 'On', quiet: 'Quiet', off: 'Off' }[sound]}`, act: () => setSound(actions.cycleSound()) },
    { label: `Graphics: ${quality[0].toUpperCase()}${quality.slice(1)}`, act: () => { const q = QUALITIES[(QUALITIES.indexOf(quality) + 1) % QUALITIES.length]; actions.setQuality(q); setQuality(q); } },
    { label: `Gore: ${gore[0].toUpperCase()}${gore.slice(1)}`, act: () => { const g = GORES[(GORES.indexOf(gore) + 1) % GORES.length]; actions.setGore(g); setGore(g); } },
    { label: 'Controls', act: () => setShowControls(true) },
    { label: 'Pack', act: () => actions.openOverlay('inventory') },
    { label: 'Self', act: () => actions.openOverlay('character') },
    { label: 'Journal', act: () => actions.openOverlay('journal') },
    { label: 'Map', act: () => actions.openOverlay('map') },
    { label: 'Leave to the title', act: () => actions.quitToTitle() },
    ...(desktop ? [{ label: 'Quit the game', act: () => actions.quitGame() }] : []),
  ];
  const [focus, setFocus] = useState(0);
  useEffect(() => Input.on((a) => {
    // The controls list is read, not navigated: confirm goes back (and
    // Escape, through overlayBack, which the game checks first).
    if (showControls) {
      if (a === 'confirm') { setShowControls(false); return true; }
      return;
    }
    if (a === 'up') setFocus((f) => (f + items.length - 1) % items.length);
    else if (a === 'down') setFocus((f) => (f + 1) % items.length);
    else if (a === 'confirm') items[focus].act();
    else return;
    return true;
  }), [focus, showControls]);
  useEffect(() => () => { overlayBack.value = null; }, []);
  if (showControls) return (
    <div class="menu-overlay">
      <div class="scrim fade-in" onClick={() => setShowControls(false)} />
      <div class="pause panel rise-in controls-panel">
        <div class="pause-title title-cap">Controls</div>
        <div class="rule" />
        <Controls />
        <button class="btn" onClick={() => setShowControls(false)}>Back</button>
      </div>
    </div>
  );
  return (
    <div class="menu-overlay">
      <div class="scrim fade-in" onClick={() => actions.resume()} />
      <div class="pause panel rise-in">
        <div class="pause-title title-cap">Paused</div>
        <div class="rule" />
        {items.map((it, i) => (
          <button key={it.label} class={`pause-item${focus === i ? ' focus' : ''}`} onMouseEnter={() => setFocus(i)} onClick={it.act}>{it.label}</button>
        ))}
        <div class="pause-keys">
          <span><span class="key">{Input.keyLabel('inventory')}</span> Pack</span>
          <span><span class="key">{Input.keyLabel('character')}</span> Self</span>
          <span><span class="key">{Input.keyLabel('journal')}</span> Journal</span>
          <span><span class="key">{Input.keyLabel('map')}</span> Map</span>
        </div>
      </div>
    </div>
  );
}

export function Death() {
  return (
    <div class="menu-overlay">
      <div class="death fade-in">
        <div class="death-title">You fell</div>
        <p class="death-text">The ember gutters and goes out. But the world is not finished with you, and it will remember this.</p>
        <button class="btn primary" onClick={() => actions.rise()}>Rise</button>
      </div>
    </div>
  );
}
