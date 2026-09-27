import { useEffect, useState } from 'preact/hooks';
import { actions } from '@/game/actions';
import { Input } from '@/core/input';
import './menus.css';

/* The small overlays: the pause menu and the fall. */

export function Pause() {
  const [sound, setSound] = useState(() => actions.soundLevel());
  const items = [
    { label: 'Resume', act: () => actions.resume() },
    { label: 'Save', act: () => actions.saveNow() },
    { label: `Sound: ${{ on: 'On', quiet: 'Quiet', off: 'Off' }[sound]}`, act: () => setSound(actions.cycleSound()) },
    { label: 'Pack', act: () => actions.openOverlay('inventory') },
    { label: 'Journal', act: () => actions.openOverlay('journal') },
    { label: 'Leave to the title', act: () => actions.quitToTitle() },
  ];
  const [focus, setFocus] = useState(0);
  useEffect(() => Input.on((a) => {
    if (a === 'up') setFocus((f) => (f + items.length - 1) % items.length);
    else if (a === 'down') setFocus((f) => (f + 1) % items.length);
    else if (a === 'confirm') items[focus].act();
    else return;
    return true;
  }), [focus]);
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
