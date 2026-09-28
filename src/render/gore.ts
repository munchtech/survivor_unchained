/* The Gore setting: full, reduced (a little blood, nothing thrown) or off.
 * Kept per browser, read when a fight's effects are built. */

export type GoreSetting = 'full' | 'reduced' | 'off';
const KEY = 'survivor-unchained.gore';

export function goreSetting(): GoreSetting {
  try {
    const v = localStorage.getItem(KEY);
    return v === 'reduced' || v === 'off' ? v : 'full';
  } catch { return 'full'; }
}

export function setGoreSetting(v: GoreSetting) {
  try { localStorage.setItem(KEY, v); } catch { /* no storage */ }
}

export const goreLevel = (v: GoreSetting = goreSetting()) => (v === 'full' ? 1 : v === 'reduced' ? 0.35 : 0);
