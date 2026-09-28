/* How much the picture moves when things hit: screen shake, and the few
 * frames the world holds still on a heavy blow (hitstop). Some players get
 * sick from it, some just want to see; like gore, it is a setting. Reduced
 * keeps the hitstop and a little shake; off keeps neither. */

export type MotionSetting = 'full' | 'reduced' | 'off';

const KEY = 'survivor-unchained.motion';
let current: MotionSetting | null = null;

export function motionSetting(): MotionSetting {
  if (current) return current;
  let v: string | null = null;
  try { v = localStorage.getItem(KEY); } catch { /* no storage */ }
  current = v === 'reduced' || v === 'off' ? v : 'full';
  return current;
}

export function setMotionSetting(v: MotionSetting) {
  current = v;
  try { localStorage.setItem(KEY, v); } catch { /* no storage */ }
}

/** What camera trauma is multiplied by. */
export const shakeScale = () => ({ full: 1, reduced: 0.4, off: 0 })[motionSetting()];

export const hitstopOn = () => motionSetting() !== 'off';
