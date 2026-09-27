import { audio as A } from './engine';

/* The world's own noise, underneath everything.
 *
 * A handful of beds that run for as long as the game does: wind in the
 * trees, water, a town's murmur, a fire. Each is noise shaped by filters
 * and slow wobbles, and each has a level the zone sets every frame from
 * where the survivor is standing (near the stream, the water rises; at
 * night the birds stop and the crickets start). On top of the beds, a
 * scheduler drops in the things that happen now and then: a bird, an owl,
 * a crackle, the smith's hammer. */

export interface AmbienceMix {
  wind: number; leaves: number; water: number; town: number; fire: number;
  birds: number; crickets: number; owl: number; smithy: number; hum: number;
}
export const SILENT: AmbienceMix = { wind: 0, leaves: 0, water: 0, town: 0, fire: 0, birds: 0, crickets: 0, owl: 0, smithy: 0, hum: 0 };

interface Bed { gain: GainNode; scale: number }

export class Ambience {
  private beds: Partial<Record<keyof AmbienceMix, Bed>> = {};
  private target: AmbienceMix = { ...SILENT };
  private cur: AmbienceMix = { ...SILENT };
  private next: Record<string, number> = {};
  private built = false;

  constructor() { A.onStart(() => this.build()); }

  set(m: Partial<AmbienceMix>) { this.target = { ...SILENT, ...m }; }

  private build() {
    const ctx = A.ctx!;
    const bus = A.bus('amb');
    const lfo = (freq: number, depth: number, param: AudioParam) => {
      const o = ctx.createOscillator(); o.frequency.value = freq;
      const g = ctx.createGain(); g.gain.value = depth;
      o.connect(g).connect(param); o.start();
    };
    const bed = (key: keyof AmbienceMix, brown: boolean, chain: (src: AudioNode) => AudioNode, scale: number) => {
      const src = ctx.createBufferSource();
      src.buffer = A.noise(brown); src.loop = true;
      src.start(0, Math.random() * 1.9);
      const gain = ctx.createGain(); gain.gain.value = 0;
      chain(src).connect(gain).connect(bus);
      this.beds[key] = { gain, scale };
    };
    // Wind: low and heaving.
    bed('wind', true, (s) => {
      const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 420; f.Q.value = 0.8;
      lfo(0.06, 220, f.frequency);
      const g = ctx.createGain(); g.gain.value = 0.7; lfo(0.11, 0.3, g.gain);
      s.connect(f).connect(g);
      return g;
    }, 0.2);
    // Leaves: the high hiss of a canopy, gusting with the wind.
    bed('leaves', false, (s) => {
      const f = ctx.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = 3800; f.Q.value = 0.5;
      const g = ctx.createGain(); g.gain.value = 0.6; lfo(0.09, 0.45, g.gain);
      s.connect(f).connect(g);
      return g;
    }, 0.018);
    // Water: two bands, fluttering.
    bed('water', false, (s) => {
      const a = ctx.createBiquadFilter(); a.type = 'bandpass'; a.frequency.value = 650; a.Q.value = 0.8;
      const b = ctx.createBiquadFilter(); b.type = 'bandpass'; b.frequency.value = 1900; b.Q.value = 1.6;
      lfo(3.1, 180, a.frequency); lfo(5.3, 400, b.frequency);
      const m = ctx.createGain(); m.gain.value = 1;
      s.connect(a).connect(m); s.connect(b).connect(m);
      return m;
    }, 0.09);
    // A town: the low murmur of many people not quite talking.
    bed('town', true, (s) => {
      const f = ctx.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = 380; f.Q.value = 1.2;
      lfo(0.37, 90, f.frequency);
      const g = ctx.createGain(); g.gain.value = 0.7; lfo(0.23, 0.3, g.gain);
      s.connect(f).connect(g);
      return g;
    }, 0.12);
    // A fire's body; the crackles are scheduled.
    bed('fire', true, (s) => {
      const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 260;
      const g = ctx.createGain(); g.gain.value = 0.8; lfo(1.7, 0.25, g.gain);
      s.connect(f).connect(g);
      return g;
    }, 0.1);
    // The blight's hum near the Dig: something electrical in the water.
    {
      const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = 55;
      const o2 = ctx.createOscillator(); o2.type = 'sawtooth'; o2.frequency.value = 55.6;
      const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 300; lfo(0.2, 120, f.frequency);
      const gain = ctx.createGain(); gain.gain.value = 0;
      o.connect(f); o2.connect(f); f.connect(gain).connect(bus);
      o.start(); o2.start();
      this.beds.hum = { gain, scale: 0.03 };
    }
    // Crickets: a high tone chopped into chirps, in waves.
    {
      const o = ctx.createOscillator(); o.frequency.value = 4400;
      const chop = ctx.createGain(); chop.gain.value = 0.5;
      const sq = ctx.createOscillator(); sq.type = 'square'; sq.frequency.value = 26;
      const sqg = ctx.createGain(); sqg.gain.value = 0.5;
      sq.connect(sqg).connect(chop.gain);
      const wave = ctx.createGain(); wave.gain.value = 0.5; lfo(0.7, 0.5, wave.gain);
      const gain = ctx.createGain(); gain.gain.value = 0;
      o.connect(chop).connect(wave).connect(gain).connect(bus);
      o.start(); sq.start();
      this.beds.crickets = { gain, scale: 0.012 };
    }
    this.built = true;
  }

  update(dt: number) {
    if (!this.built || !A.ready) return;
    const ctx = A.ctx!;
    for (const k of Object.keys(this.cur) as Array<keyof AmbienceMix>) {
      this.cur[k] += (this.target[k] - this.cur[k]) * Math.min(1, dt * 1.2);
      const b = this.beds[k];
      if (b) b.gain.gain.setTargetAtTime(this.cur[k] * b.scale, ctx.currentTime, 0.15);
    }
    const every = (key: string, level: number, lo: number, hi: number, fn: () => void) => {
      if (level < 0.02) return;
      this.next[key] = (this.next[key] ?? Math.random() * hi) - dt * level;
      if (this.next[key] <= 0) { this.next[key] = lo + Math.random() * (hi - lo); fn(); }
    };
    const c = this.cur;
    every('crackle', c.fire, 0.05, 0.35, () => A.hiss({ d: 0.01 + Math.random() * 0.03, g: 0.03 + Math.random() * 0.05, bp: 1800 + Math.random() * 4000, q: 2, bus: 'amb', pan: Math.random() - 0.5 }));
    every('bird', c.birds, 2.5, 7, () => this.bird());
    every('owl', c.owl, 18, 40, () => this.owl());
    every('smithy', c.smithy, 1.8, 4.5, () => this.hammer());
    every('creak', c.wind * c.leaves, 8, 20, () => A.tone({ f: 180 + Math.random() * 80, f2: 150, type: 'sawtooth', a: 0.3, d: 0.6, g: 0.008, lp: 700, bus: 'amb', pan: Math.random() - 0.5 }));
  }

  private bird() {
    const pan = Math.random() * 1.6 - 0.8;
    const base = 2600 + Math.random() * 1600, n = 2 + Math.floor(Math.random() * 5);
    const style = Math.random();
    for (let i = 0; i < n; i++) {
      const t = A.now + i * (0.09 + Math.random() * 0.06);
      const f = base * (1 + (style < 0.5 ? i * 0.04 : -i * 0.05) + (Math.random() - 0.5) * 0.08);
      A.tone({ t, f, f2: f * (style < 0.5 ? 1.3 : 0.75), d: 0.05 + Math.random() * 0.05, g: 0.024 * this.cur.birds, bus: 'amb', pan, verb: 0.4 });
    }
  }

  private owl() {
    const pan = Math.random() * 1.4 - 0.7;
    for (const [dt, len] of [[0, 0.35], [0.55, 0.22], [0.85, 0.5]]) {
      A.tone({ t: A.now + dt, f: 390, f2: 350, type: 'sine', a: 0.06, d: len, g: 0.025 * this.cur.owl, bus: 'amb', pan, verb: 0.7 });
    }
  }

  private hammer() {
    const n = 2 + Math.floor(Math.random() * 4);
    for (let i = 0; i < n; i++) A.fm({ t: A.now + i * 0.42, f: 1650 + Math.random() * 120, ratio: 2.76, index: 2.2, d: 0.5, g: 0.02 * this.cur.smithy, bus: 'amb', pan: 0.3, verb: 0.5 });
  }
}
