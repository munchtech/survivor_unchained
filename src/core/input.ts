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

// Standard gamepad mapping.
const PAD: Partial<Record<Action, number[]>> = {
  dash: [0], ability: [2], ultimate: [3], interact: [1], confirm: [0], cancel: [1],
  inventory: [8], pause: [9], journal: [8], up: [12], down: [13], left: [14], right: [15],
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
      for (const a of this.actionsFor(e.code)) {
        this.latched.add(a);
        for (const l of this.listeners) if (l(a, e) === true) { e.preventDefault(); break; }
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
      for (const [a, buttons] of Object.entries(PAD) as [Action, number[]][]) {
        for (const b of buttons) {
          const now = !!pad.buttons[b]?.pressed;
          const key = pad.index * 100 + b;
          if (now && !this.padPrev.get(key)) {
            this.latched.add(a);
            this.usingPad = true;
            for (const l of this.listeners) if (l(a) === true) break;
          }
          this.padPrev.set(key, now);
        }
      }
    }
    const m = Math.hypot(x, z);
    if (m > 1) { x /= m; z /= m; }
    this.moveX = this.captured ? 0 : x;
    this.moveZ = this.captured ? 0 : z;
  }

  keyLabel(a: Action) {
    const c = this.bindings[a][0] ?? '';
    return c.replace(/^Key/, '').replace(/^Digit/, '').replace('Mouse2', 'RMB').replace('Mouse0', 'LMB').replace('ShiftLeft', 'Shift');
  }
}

export const Input = new InputState();
