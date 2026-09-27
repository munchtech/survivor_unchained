import { audio as A } from './engine';

/* The score, composed as it plays.
 *
 * D minor, mostly, because it is that kind of story. A slow bed of pads
 * walks a four-chord progression; over it a plucked line wanders near the
 * chord tones, sparse on the road and busier in town. When the fighting
 * starts, a frame drum and a low ostinato come in under it, as loud as the
 * fight is thick; a boss brings a brass drone and a heavier drum. All of it
 * is scheduled a little ahead of time on a sixteenth-note grid, so it never
 * drifts however the frame rate wobbles. */

export type Mood = 'silence' | 'title' | 'explore' | 'town' | 'night' | 'combat' | 'boss' | 'mystery';

const D = 146.83; // D3
const st = (n: number) => D * Math.pow(2, n / 12);

interface Style {
  bpm: number;
  /** Chords as semitone offsets from D3, one per two bars. */
  chords: number[][];
  /** Scale (semitones above D) the melody walks on. */
  scale: number[];
  pluck: number; pad: number; drums: number; brass: number;
  /** Instrument of the melody. */
  voice: 'pluck' | 'bell' | 'flute';
}

const STYLES: Record<Exclude<Mood, 'silence'>, Style> = {
  title: { bpm: 64, chords: [[0, 3, 7], [-2, 3, 5], [-5, 2, 7], [-3, 1, 4]], scale: [0, 2, 3, 5, 7, 8, 10, 12, 14, 15], pluck: 0.35, pad: 1, drums: 0, brass: 0, voice: 'bell' },
  explore: { bpm: 76, chords: [[0, 3, 7], [-4, 0, 3], [-2, 2, 5], [-5, -1, 2]], scale: [0, 2, 3, 5, 7, 9, 10, 12, 14], pluck: 0.22, pad: 0.85, drums: 0, brass: 0, voice: 'pluck' },
  night: { bpm: 60, chords: [[0, 3, 7], [-4, 0, 3], [-7, -3, 0], [-5, -2, 2]], scale: [0, 3, 5, 7, 10, 12, 15], pluck: 0.12, pad: 0.8, drums: 0, brass: 0, voice: 'flute' },
  town: { bpm: 88, chords: [[3, 7, 10], [-2, 2, 5], [0, 3, 7], [-4, 0, 3]], scale: [0, 2, 3, 5, 7, 9, 10, 12, 14, 15], pluck: 0.45, pad: 0.7, drums: 0, brass: 0, voice: 'pluck' },
  combat: { bpm: 104, chords: [[0, 3, 7], [0, 3, 7], [-4, 0, 3], [-2, 2, 5]], scale: [0, 2, 3, 5, 7, 8, 10, 12], pluck: 0.1, pad: 0.7, drums: 1, brass: 0, voice: 'pluck' },
  boss: { bpm: 112, chords: [[0, 3, 7], [1, 5, 8], [0, 3, 7], [-1, 2, 5]], scale: [0, 1, 3, 5, 7, 8, 10, 12], pluck: 0.08, pad: 0.8, drums: 1, brass: 1, voice: 'pluck' },
  mystery: { bpm: 56, chords: [[0, 3, 6], [-1, 3, 6], [0, 4, 7], [-2, 1, 6]], scale: [0, 1, 3, 6, 7, 9, 12], pluck: 0.14, pad: 0.9, drums: 0, brass: 0, voice: 'bell' },
};

// Combat grooves, sixteenths: 2 = accent, 1 = ghost.
const TOM = [2, 0, 0, 1, 0, 0, 2, 0, 2, 0, 0, 1, 0, 1, 0, 0];
const SLAP = [0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 2, 0, 1, 0];
const OSTINATO = [0, 0, 3, 0, 2, 0, 0, -2];

export class Music {
  private mood: Mood = 'silence';
  private style: Style | null = null;
  private step = 0;
  private nextT = 0;
  private chordIx = 0;
  private melodyAt = 7;
  /** 0..1: how thick the fighting is; drives the drums. */
  intensity = 0;
  private drumLevel = 0;
  private ahead = 0.3;
  private lastWall = 0;

  set(m: Mood) {
    if (m === this.mood) return;
    this.mood = m;
    this.style = m === 'silence' ? null : STYLES[m];
    // A new piece starts on its first chord, at the next bar.
    this.step = 0;
    this.chordIx = 0;
  }

  update(dt: number) {
    if (!A.ready) return;
    const want = this.style?.drums ? Math.min(1, this.intensity) : 0;
    this.drumLevel += (want - this.drumLevel) * Math.min(1, dt * 0.8);
    const s = this.style;
    const now = A.now;
    if (!s) { this.nextT = now; return; }
    const sixteenth = 60 / s.bpm / 4;
    if (this.nextT < now - 0.2) {
      // Fell behind (a long frame): skip what was missed so the grid stays
      // on time, and if a chord change was skipped, bring it in now.
      const missed = Math.ceil((now - this.nextT) / sixteenth);
      const before = Math.floor(this.step / 32);
      this.step += missed;
      this.nextT += missed * sixteenth;
      if (Math.floor(this.step / 32) !== before || this.step % 32 === 0) {
        const chord = s.chords[this.chordIx % s.chords.length];
        this.chordIx++;
        const left = (32 - (this.step % 32)) * sixteenth;
        this.pad(chord, now + 0.02, Math.max(2, left), s.pad);
        if (s.brass) this.brass(chord[0], now + 0.02, Math.max(2, left));
        if (this.step % 32 === 0) this.step++;
      }
    }
    // Look further ahead when frames are slow, so a hitch never leaves a gap.
    // (Real time between calls: the game clamps its own dt.)
    const wall = performance.now(), gap = this.lastWall ? (wall - this.lastWall) / 1000 : dt;
    this.lastWall = wall;
    this.ahead += (Math.min(4, Math.max(0.3, gap * 2.5)) - this.ahead) * (gap * 2.5 > this.ahead ? 1 : 0.05);
    while (this.nextT < now + this.ahead) {
      this.play(s, this.step, this.nextT, sixteenth);
      this.step++;
      this.nextT += sixteenth;
    }
  }

  private play(s: Style, step: number, t: number, sx: number) {
    const inBar = step % 16, bar = Math.floor(step / 16);
    // Chords change every two bars.
    if (inBar === 0 && bar % 2 === 0) {
      const chord = s.chords[this.chordIx % s.chords.length];
      this.chordIx++;
      this.pad(chord, t, sx * 32, s.pad);
      if (s.brass) this.brass(chord[0], t, sx * 32);
    }
    const chord = s.chords[(this.chordIx - 1 + s.chords.length) % s.chords.length];
    // The melody: sparse, on eighths, leaning on chord tones.
    if (inBar % 2 === 0 && Math.random() < s.pluck * (inBar === 0 ? 1.6 : 1)) {
      const tones = s.scale;
      const pullToChord = Math.random() < 0.55;
      if (pullToChord) {
        const target = chord[Math.floor(Math.random() * chord.length)] + 12;
        this.melodyAt = tones.reduce((best, n, i) => (Math.abs(n - target) < Math.abs(tones[best] - target) ? i : best), 0);
      } else this.melodyAt = Math.max(0, Math.min(tones.length - 1, this.melodyAt + (Math.random() < 0.5 ? -1 : 1)));
      const note = st(tones[this.melodyAt] + 12);
      if (s.voice === 'bell') A.fm({ t, f: note, ratio: 3.5, index: 0.3, a: 0.004, d: 2.6, g: 0.06, bus: 'music', verb: 0.6 });
      else if (s.voice === 'flute') A.tone({ t, f: note, type: 'sine', a: 0.12, d: 1.4, g: 0.055, bus: 'music', verb: 0.5 });
      else this.pluck(note, t);
    }
    // Drums and ostinato, as loud as the fighting.
    const dl = this.drumLevel;
    if (dl > 0.03) {
      const tom = TOM[inBar], slap = SLAP[inBar];
      if (tom) A.tone({ t, f: 110, f2: 46, d: 0.28, g: (tom === 2 ? 0.26 : 0.12) * dl, bus: 'music' });
      if (slap && dl > 0.3) A.hiss({ t, d: 0.11, g: (slap === 2 ? 0.07 : 0.03) * dl, bp: 1300, q: 0.9, bus: 'music' });
      if (inBar % 2 === 0) {
        const n = OSTINATO[(inBar / 2) % OSTINATO.length] + chord[0];
        A.tone({ t, f: st(n - 12), type: 'sawtooth', a: 0.005, d: sx * 1.6, g: 0.045 * dl, lp: 700 + 900 * dl, q: 3, bus: 'music' });
      }
      if (this.style?.brass && inBar === 0) A.tone({ t, f: 58, f2: 30, d: 0.9, g: 0.35 * dl, bus: 'music' });
    }
  }

  private pad(chord: number[], t: number, len: number, level: number) {
    for (const n of chord) {
      for (const det of [-7, 6]) A.tone({ t, f: st(n), type: 'sawtooth', a: 1.8, hold: len - 1.8, d: 2.6, g: 0.024 * level, lp: 520, lp2: 950, detune: det, bus: 'music', pan: det < 0 ? -0.3 : 0.3 });
    }
    A.tone({ t, f: st(chord[0] - 12), type: 'triangle', a: 1.2, hold: len - 1.2, d: 2.2, g: 0.09 * level, bus: 'music' });
  }

  private brass(root: number, t: number, len: number) {
    for (const k of [0, 7]) A.tone({ t, f: st(root - 12 + k), type: 'sawtooth', a: 0.8, hold: len - 1.6, d: 1.4, g: 0.03, lp: 300, lp2: 1100, q: 1.5, bus: 'music', detune: k ? 4 : -4 });
  }

  /** A plucked string: a bright attack, a quick fall, a darker ring. */
  private pluck(f: number, t: number) {
    A.tone({ t, f, type: 'triangle', a: 0.003, d: 1.3, g: 0.09, lp: 2600, lp2: 500, bus: 'music', verb: 0.35 });
    A.tone({ t, f: f * 2, type: 'sine', a: 0.002, d: 0.25, g: 0.025, bus: 'music' });
    A.hiss({ t, d: 0.02, g: 0.015, bp: f * 4, q: 2, bus: 'music' });
  }
}
