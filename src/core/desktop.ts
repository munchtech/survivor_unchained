/* The desktop shell (desktop/main.cjs), when the game runs in it: quitting,
 * and fullscreen. In a browser there is none, and these do nothing. */

interface DesktopBridge {
  quit(): Promise<void>;
  /** Set fullscreen (true/false), or ask (no argument); resolves to the state. */
  fullscreen(on?: boolean): Promise<boolean>;
}

export const desktop: DesktopBridge | null = (window as unknown as { desktop?: DesktopBridge }).desktop ?? null;

const KEY = 'survivor-unchained.fullscreen';

/** Fullscreen unless the player chose a window. */
export function wantsFullscreen() {
  try { return localStorage.getItem(KEY) !== '0'; } catch { return true; }
}

export function setFullscreen(on: boolean) {
  try { localStorage.setItem(KEY, on ? '1' : '0'); } catch { /* no storage */ }
  return desktop?.fullscreen(on) ?? Promise.resolve(false);
}
