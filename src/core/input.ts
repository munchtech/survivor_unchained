/* Input: keyboard, mouse and gamepad folded into named actions.
 *
 * The simulation never reads keys. It reads `move` (a vector, analog on a
 * pad), and actions that are either held or were pressed since the last
 * fixed tick. Presses are latched until consumed so a tap between two
 * simulation ticks is never lost. Bindings are data so the settings screen
 * can rebind them. */

export type Action =
  | 'dash' | 'ability' | 'ultimate' | 'interact' | 'inventory' | 'journal' | 'map'
  | 'pause' | 'confirm' | 'cancel' | 'reroll' | 'banish' | 'pick1' | 'pick2' | 'pick3' | 'pick4'
  | 'up' | 'down' | 'left' | 'right' | 'tabNext' | 'tabPrev' | 'character';

export const DEFAULT_BINDINGS: Record<Action, string[]> = {
  up: ['KeyW', 'ArrowUp'],
  down: ['KeyS', 'ArrowDown'],
  left: ['KeyA', 'ArrowLeft'],
  right: ['KeyD', 'ArrowRight'],
  dash: ['Space', 'ShiftLeft'],
  ability: ['KeyQ', 'Mouse2'],
  ultimate: ['KeyR'],
  interact: ['KeyE', 'KeyF'],
  inventory: ['KeyI', 'Tab'],
  character: ['KeyC'],
  journal: ['KeyJ'],
  map: ['KeyM'],
  pause: ['Escape', 'KeyP'],
  confirm: ['Enter', 'NumpadEnter'],
  cancel: ['Escape', 'Backspace'],
  reroll: ['KeyX'],
  banish: ['KeyB'],
  pick1: ['Digit1'],
  pick2: ['Digit2'],
  pick3: ['Digit3'],
  pick4: ['Digit4'],
  tabNext: ['BracketRight'],
  tabPrev: ['BracketLeft'],
};

/** The actions a player can move to other keys. Menus keep theirs (Escape,
 *  Enter, the number keys of the draft) so nobody can lock themselves out. */
export const REBINDABLE: Action[] = ['up', 'left', 'down', 'right', 'dash', 'ability', 'ultimate', 'interact', 'inventory', 'character', 'journal', 'map', 'reroll', 'banish'];
const RESERVED = ['Escape', 'Enter', 'NumpadEnter', 'Backspace', 'Digit1', 'Digit2', 'Digit3', 'Digit4', 'BracketLeft', 'BracketRight'];
const BINDINGS_KEY = 'survivor-unchained.bindings';

// Standard gamepad mapping. View opens the pack; the self, journal and map
// are in the pause menu (Menu), so a pad reaches everything.
const PAD: Partial<Record<Action, number[]>> = {
  dash: [0], ability: [2], ultimate: [3], interact: [1], confirm: [0], cancel: [1],
  inventory: [8], pause: [9], up: [12], down: [13], left: [14], right: [15],
  tabNext: [5], tabPrev: [4], reroll: [2], banish: [3],
};

class InputState {
  bindings: Record<Action, string[]> = structuredClone(DEFAULT_BINDINGS);
  private down = new Set<string>();
  private latched = new Set<Action>();
  private padPrev = new Map<number, boolean>();
  /** Movement intent, magnitude <= 1. */
  moveX = 0;
  moveZ = 0;
  /** Pointer in normalised device coordinates, and whether it has moved recently. */
  pointerX = 0;
  pointerY = 0;
  pointerActive = false;
  usingPad = false;
  /** When true, gameplay ignores input (a menu or dialogue has focus). */
  captured = false;
  private listeners = new Set<(a: Action, e?: KeyboardEvent) => boolean | void>();

  attach(el: HTMLElement | Window = window) {
    el.addEventListener('keydown', (ev) => {
      const e = ev as KeyboardEvent;
      if (e.repeat) return;
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA')) return;
      this.down.add(e.code);
      this.usingPad = false;
      // One key can mean several actions (Escape is pause and cancel): the
      // first one something handles is the one it meant. Offering the rest
      // too would let Escape open the pause menu and close it again.
      let handled = false;
      for (const a of this.actionsFor(e.code)) {
        this.latched.add(a);
        if (handled) continue;
        for (const l of this.listeners) if (l(a, e) === true) { e.preventDefault(); handled = true; break; }
      }
      if (e.code === 'Tab' || e.code === 'Space') e.preventDefault();
    });
    el.addEventListener('keyup', (ev) => this.down.delete((ev as KeyboardEvent).code));
    window.addEventListener('blur', () => this.down.clear());
    window.addEventListener('pointermove', (e) => {
      this.pointerX = (e.clientX / window.innerWidth) * 2 - 1;
      this.pointerY = -(e.clientY / window.innerHeight) * 2 + 1;
      this.pointerActive = true;
    });
    window.addEventListener('mousedown', (e) => {
      const code = `Mouse${e.button}`;
      this.down.add(code);
      for (const a of this.actionsFor(code)) this.latched.add(a);
    });
    window.addEventListener('mouseup', (e) => this.down.delete(`Mouse${e.button}`));
    window.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  /** UI listens for actions as they happen (menus navigate on press). A
   *  listener returning true consumes the event. */
  on(fn: (a: Action, e?: KeyboardEvent) => boolean | void) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private actionsFor(code: string): Action[] {
    const out: Action[] = [];
    for (const [a, codes] of Object.entries(this.bindings) as [Action, string[]][]) if (codes.includes(code)) out.push(a);
    return out;
  }

  held(a: Action) {
    for (const c of this.bindings[a]) if (this.down.has(c)) return true;
    return false;
  }

  /** True once per press; consumes the latch. */
  pressed(a: Action) {
    if (this.latched.has(a)) {
      this.latched.delete(a);
      return true;
    }
    return false;
  }

  clearLatches() { this.latched.clear(); }

  /** A synthetic press, as if the key went down (tools, the autopilot). */
  press(a: Action) {
    this.latched.add(a);
    for (const l of this.listeners) if (l(a) === true) break;
  }

  /** Called once per rendered frame: polls pads and recomputes movement. */
  poll() {
    let x = 0, z = 0;
    if (this.held('left')) x -= 1;
    if (this.held('right')) x += 1;
    if (this.held('up')) z -= 1;
    if (this.held('down')) z += 1;
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const pad of pads) {
      if (!pad) continue;
      const ax = pad.axes[0] ?? 0, az = pad.axes[1] ?? 0;
      const m = Math.hypot(ax, az);
      if (m > 0.18) {
        const s = Math.min(1, (m - 0.18) / 0.72) / m;
        x += ax * s;
        z += az * s;
        this.usingPad = true;
      }
      // As with keys: a button that means several actions is taken as the
      // first one something handles.
      const handled = new Set<number>(), pressed = new Set<number>();
      for (const [a, buttons] of Object.entries(PAD) as [Action, number[]][]) {
        for (const b of buttons) {
          const key = pad.index * 100 + b;
          const now = !!pad.buttons[b]?.pressed;
          if (now && (!this.padPrev.get(key) || pressed.has(key))) {
            pressed.add(key);
            this.latched.add(a);
            this.usingPad = true;
            if (!handled.has(key)) for (const l of this.listeners) if (l(a) === true) { handled.add(key); break; }
          }
        }
      }
      for (const buttons of Object.values(PAD)) for (const b of buttons) this.padPrev.set(pad.index * 100 + b, !!pad.buttons[b]?.pressed);
    }
    const m = Math.hypot(x, z);
    if (m > 1) { x /= m; z /= m; }
    this.moveX = this.captured ? 0 : x;
    this.moveZ = this.captured ? 0 : z;
  }

  /** Put this key on this action (its first keyboard key; a mouse button
   *  stays). A key can only mean one of the rebindable actions, so it leaves
   *  whichever had it. Saved for next time. */
  rebind(a: Action, code: string) {
    if (!REBINDABLE.includes(a) || RESERVED.includes(code)) return false;
    for (const b of REBINDABLE) if (b !== a) this.bindings[b] = this.bindings[b].filter((c) => c !== code);
    const list = [...this.bindings[a]];
    const i = list.findIndex((c) => !c.startsWith('Mouse'));
    if (i >= 0) list[i] = code; else list.unshift(code);
    this.bindings[a] = [...new Set(list)];
    this.saveBindings();
    return true;
  }

  resetBindings() {
    this.bindings = structuredClone(DEFAULT_BINDINGS);
    this.saveBindings();
  }

  loadBindings() {
    try {
      const raw = localStorage.getItem(BINDINGS_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw) as Partial<Record<Action, unknown>>;
      for (const a of REBINDABLE) {
        const v = saved[a];
        if (Array.isArray(v) && v.every((c) => typeof c === 'string')) this.bindings[a] = v as string[];
      }
    } catch { /* no storage, or nothing sensible in it */ }
  }

  private saveBindings() {
    try {
      const out: Partial<Record<Action, string[]>> = {};
      for (const a of REBINDABLE) out[a] = this.bindings[a];
      localStorage.setItem(BINDINGS_KEY, JSON.stringify(out));
    } catch { /* no storage */ }
  }

  keyLabel(a: Action) {
    return codeLabel(this.bindings[a][0] ?? '');
  }

  /** Every key bound to an action, as the player would name them. */
  keyLabels(a: Action) {
    return this.bindings[a].map(codeLabel);
  }

  /** The pad buttons bound to an action (standard mapping). */
  padLabels(a: Action) {
    return (PAD[a] ?? []).map((b) => PAD_NAMES[b] ?? `B${b}`);
  }
}

const PAD_NAMES: Record<number, string> = { 0: 'A', 1: 'B', 2: 'X', 3: 'Y', 4: 'LB', 5: 'RB', 8: 'View', 9: 'Menu', 12: 'D-pad up', 13: 'D-pad down', 14: 'D-pad left', 15: 'D-pad right' };

function codeLabel(c: string) {
  const named: Record<string, string> = {
    Mouse0: 'LMB', Mouse1: 'MMB', Mouse2: 'RMB', ShiftLeft: 'Shift', ShiftRight: 'Shift', ControlLeft: 'Ctrl', ControlRight: 'Ctrl',
    AltLeft: 'Alt', AltRight: 'Alt', CapsLock: 'Caps', ArrowUp: '↑', ArrowDown: '↓', ArrowLeft: '←', ArrowRight: '→',
    BracketLeft: '[', BracketRight: ']', NumpadEnter: 'Enter', Escape: 'Esc', Backspace: 'Backspace', Semicolon: ';', Quote: "'",
    Comma: ',', Period: '.', Slash: '/', Backslash: '\\', Minus: '-', Equal: '=', Backquote: '`',
  };
  return named[c] ?? c.replace(/^Key/, '').replace(/^Digit/, '').replace(/^Numpad/, 'Num ');
}

export const Input = new InputState();
