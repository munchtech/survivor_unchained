import { Input, type Action } from '@/core/input';
import './controls.css';

/* Every binding, keyboard and pad, in the words a player uses. Shown from
 * the title's settings and the pause menu. */

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

export function Controls() {
  return (
    <div class="controls">
      <div class="ctl-row ctl-head"><span /><span>Keyboard and mouse</span><span>Pad</span></div>
      {ROWS.map((r) => {
        const keys = [...new Set(r.actions.flatMap((a) => Input.keyLabels(a)))];
        // Four directions read better as their two usual sets.
        const shown = r.label === 'Move' ? ['WASD', '↑←↓→'] : r.actions.length > 1 && r.actions[0].startsWith('pick') ? ['1–4'] : keys;
        const pad = r.pad ?? [...new Set(r.actions.flatMap((a) => Input.padLabels(a)))].join(' / ');
        return (
          <div key={r.label} class="ctl-row">
            <span class="ctl-label">{r.label}</span>
            <span class="ctl-keys">{shown.map((k) => <span key={k} class="key">{k}</span>)}</span>
            <span class="ctl-pad">{pad || '—'}</span>
          </div>
        );
      })}
      <div class="ctl-note">Aim follows the mouse, or the way you are moving on a pad. Most attacks fire on their own.</div>
    </div>
  );
}
