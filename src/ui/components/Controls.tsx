import { useEffect, useRef, useState } from 'preact/hooks';
import { Input, REBINDABLE, type Action } from '@/core/input';
import './controls.css';

/* Every binding, keyboard and pad, in the words a player uses; shown from
 * the title's settings and the pause menu. A key in gold can be moved: click
 * it and press the new one (Escape leaves it as it was). */

const ROWS: Array<{ label: string; actions: Action[]; pad?: string }> = [
  { label: 'Move', actions: ['up', 'left', 'down', 'right'], pad: 'Left stick' },
  { label: 'Dash', actions: ['dash'] },
  { label: 'Ability', actions: ['ability'] },
  { label: 'Draught', actions: ['ultimate'] },
  { label: 'Talk, use, pick up', actions: ['interact'] },
  { label: 'Pack', actions: ['inventory'] },
  { label: 'Self', actions: ['character'], pad: 'Menu' },
  { label: 'Journal', actions: ['journal'], pad: 'Menu' },
  { label: 'Map', actions: ['map'], pad: 'Menu' },
  { label: 'Pause', actions: ['pause'] },
  { label: 'Draft: take a card', actions: ['pick1', 'pick2', 'pick3', 'pick4'], pad: 'D-pad, A' },
  { label: 'Draft: reroll', actions: ['reroll'] },
  { label: 'Draft: banish', actions: ['banish'] },
];

const DIRS: Record<string, string> = { up: 'up', left: 'left', down: 'down', right: 'right' };

export function Controls() {
  const [waiting, setWaitingState] = useState<Action | null>(null);
  const [, setRev] = useState(0);
  const bump = () => setRev((r) => r + 1);
  // The listener is there from the start and reads this, so a key pressed
  // the moment after a click is not missed (effects run after paint).
  const waitingRef = useRef<Action | null>(null);
  const setWaiting = (a: Action | null) => { waitingRef.current = a; setWaitingState(a); };

  // While waiting for a key, the key goes to the binding and nowhere else.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const a = waitingRef.current;
      if (!a) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      if (e.code !== 'Escape') Input.rebind(a, e.code);
      setWaiting(null);
      bump();
    };
    window.addEventListener('keydown', onKey, { capture: true });
    return () => window.removeEventListener('keydown', onKey, { capture: true });
  }, []);

  const chip = (a: Action, label: string, title: string) => (
    <button key={a} class={`key rebind${waiting === a ? ' waiting' : ''}`} title={title}
      onClick={(e) => { e.stopPropagation(); setWaiting(waiting === a ? null : a); }}>
      {waiting === a ? '…' : label}
    </button>
  );

  return (
    <div class="controls">
      <div class="ctl-row ctl-head"><span /><span>Keyboard and mouse</span><span>Pad</span></div>
      {ROWS.map((r) => {
        const pad = r.pad ?? [...new Set(r.actions.flatMap((a) => Input.padLabels(a)))].join(' / ');
        let keys;
        if (r.label === 'Move') {
          // Each direction's own key can move; the arrows always work too.
          keys = <>{r.actions.map((a) => chip(a, Input.keyLabel(a), `Move ${DIRS[a]}: click, then press a key`))}<span class="key">↑←↓→</span></>;
        } else if (r.actions[0].startsWith('pick')) {
          keys = <span class="key">1–4</span>;
        } else {
          const a = r.actions[0];
          const all = [...new Set(Input.keyLabels(a))];
          keys = REBINDABLE.includes(a)
            ? <>{chip(a, all[0] ?? '—', `${r.label}: click, then press a key`)}{all.slice(1).map((k) => <span key={k} class="key">{k}</span>)}</>
            : all.map((k) => <span key={k} class="key">{k}</span>);
        }
        return (
          <div key={r.label} class="ctl-row">
            <span class="ctl-label">{r.label}</span>
            <span class="ctl-keys">{keys}</span>
            <span class="ctl-pad">{pad || '—'}</span>
          </div>
        );
      })}
      <div class="ctl-foot">
        <span class="ctl-note">{waiting ? 'Press the new key, or Escape to leave it.' : 'Click a gold key to change it. Aim follows the mouse, or the way you move on a pad; most attacks fire on their own.'}</span>
        <button class="btn small" onClick={(e) => { e.stopPropagation(); Input.resetBindings(); setWaiting(null); bump(); }}>Defaults</button>
      </div>
    </div>
  );
}
