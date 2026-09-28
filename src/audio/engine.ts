/* The sound of the world, made on the spot.
 *
 * No samples: every sound is built from oscillators and noise when it is
 * needed, through four buses (music, ambience, effects, interface) that
 * share one room: a long, dark, generated reverb, so a sword ring in the
 * Verge and a bell in the Waystation sound like they happen in the same
 * place. A compressor on the way out keeps a hundred hits in a second
 * from turning into mud.
 *
 * The context starts on the first key or click (browsers insist), and
 * everything is a no-op until then, so nothing that calls in here has to
 * care whether sound exists. */

export type Bus = 'music' | 'amb' | 'sfx' | 'ui';

export interface ToneOpts {
  f: number; type?: OscillatorType; t?: number; a?: number; d: number; g: number; bus?: Bus; pan?: number;
  /** Hold at full level this long before the decay (pads, drones). */
  hold?: number;
  /** Glide to this frequency over the note. */
  f2?: number; glide?: number;
  lp?: number; lp2?: number; q?: number; hp?: number;
  detune?: number; verb?: number;
}
export interface NoiseOpts {
  t?: number; a?: number; d: number; g: number; bus?: Bus; pan?: number;
  bp?: number; bp2?: number; q?: number; lp?: number; lp2?: number; hp?: number; brown?: boolean; verb?: number;
}
export interface FmOpts { f: number; ratio: number; index: number; t?: number; a?: number; d: number; g: number; bus?: Bus; pan?: number; verb?: number; f2?: number }

const SEND: Record<Bus, number> = { music: 0.55, amb: 0.3, sfx: 0.2, ui: 0.08 };

export class AudioEngine {
  ctx: AudioContext | null = null;
  private out!: GainNode;
  private buses = {} as Record<Bus, GainNode>;
  private sends = {} as Record<Bus, GainNode>;
  private verbIn!: GainNode;
  private white!: AudioBuffer;
  private brownBuf!: AudioBuffer;
  private gates = new Map<string, number[]>();
  private started: Array<() => void> = [];
  level: Record<Bus | 'master', number> = { master: 0.9, music: 0.8, amb: 0.9, sfx: 0.85, ui: 0.7 };
  private duck = 1;
  /** The final mix, for tools that want to listen in. */
  master: AudioNode | null = null;

  get ready() { return !!this.ctx && this.ctx.state === 'running'; }
  get now() { return this.ctx?.currentTime ?? 0; }

  /** Run once the context exists (ambience beds, music). */
  onStart(fn: () => void) { if (this.ctx) fn(); else this.started.push(fn); }

  /** On a user gesture: make (or wake) the context. */
  start() {
    if (this.ctx) { if (this.ctx.state === 'suspended') void this.ctx.resume(); return; }
    const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AC) return;
    let ctx: AudioContext;
    try { ctx = new AC({ latencyHint: 'interactive' }); } catch { return; }
    this.ctx = ctx;
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -16; comp.knee.value = 14; comp.ratio.value = 4; comp.attack.value = 0.004; comp.release.value = 0.25;
    this.out = ctx.createGain();
    this.out.gain.value = this.level.master;
    this.out.connect(comp).connect(ctx.destination);
    this.master = comp;
    // The room.
    const verb = ctx.createConvolver();
    verb.buffer = this.impulse(3.4, 2.6);
    this.verbIn = ctx.createGain();
    this.verbIn.gain.value = 1;
    const verbOut = ctx.createGain();
    verbOut.gain.value = 0.8;
    this.verbIn.connect(verb).connect(verbOut).connect(this.out);
    for (const b of ['music', 'amb', 'sfx', 'ui'] as Bus[]) {
      const g = ctx.createGain();
      g.gain.value = this.level[b];
      g.connect(this.out);
      const s = ctx.createGain();
      s.gain.value = SEND[b];
      g.connect(s).connect(this.verbIn);
      this.buses[b] = g;
      this.sends[b] = s;
    }
    this.white = this.noiseBuffer(false);
    this.brownBuf = this.noiseBuffer(true);
    for (const fn of this.started) fn();
    this.started = [];
  }

  setLevel(b: Bus | 'master', v: number) {
    this.level[b] = v;
    if (!this.ctx) return;
    const node = b === 'master' ? this.out : this.buses[b];
    node.gain.setTargetAtTime(b === 'music' ? v * this.duck : v, this.ctx.currentTime, 0.1);
  }

  /** Lower the music under a conversation or a menu. */
  duckMusic(k: number) {
    if (Math.abs(k - this.duck) < 0.01) return;
    this.duck = k;
    if (this.ctx) this.buses.music.gain.setTargetAtTime(this.level.music * k, this.ctx.currentTime, 0.4);
  }

  bus(b: Bus) { return this.buses[b]; }
  noise(brown = false) { return brown ? this.brownBuf : this.white; }

  /** At most `max` of this sound per `ms`: a hundred hits a second must
   *  not become a hundred sounds. */
  gate(key: string, max: number, ms: number) {
    const now = performance.now();
    let list = this.gates.get(key);
    if (!list) this.gates.set(key, (list = []));
    while (list.length && now - list[0] > ms) list.shift();
    if (list.length >= max) return false;
    list.push(now);
    return true;
  }

  /* ---------------------------------------------------------- voices -- */

  private dest(bus: Bus, pan: number | undefined, verb: number | undefined, end: number): AudioNode {
    const ctx = this.ctx!;
    let node: AudioNode = this.buses[bus];
    if (verb !== undefined) {
      // An extra send for this voice alone (a bell wants more room).
      const s = ctx.createGain();
      s.gain.value = verb;
      s.connect(this.verbIn);
      const split = ctx.createGain();
      split.connect(node);
      split.connect(s);
      node = split;
      this.cleanup(end, s, split);
    }
    if (pan) {
      const p = ctx.createStereoPanner();
      p.pan.value = Math.max(-1, Math.min(1, pan));
      p.connect(node);
      this.cleanup(end, p);
      node = p;
    }
    return node;
  }

  private cleanup(at: number, ...nodes: AudioNode[]) {
    const ctx = this.ctx!;
    const ms = Math.max(0, (at - ctx.currentTime) * 1000 + 200);
    setTimeout(() => { for (const n of nodes) { try { n.disconnect(); } catch { /* gone */ } } }, ms);
  }

  private envelope(g: GainNode, t: number, a: number, d: number, peak: number, hold = 0) {
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(peak, t + a);
    if (hold > 0) g.gain.setValueAtTime(peak, t + a + hold);
    g.gain.exponentialRampToValueAtTime(0.0001, t + a + hold + d);
  }

  tone(o: ToneOpts) {
    const ctx = this.ctx;
    if (!ctx || ctx.state !== 'running') return;
    const t = o.t ?? ctx.currentTime, a = o.a ?? 0.005, hold = o.hold ?? 0, end = t + a + hold + o.d;
    const osc = ctx.createOscillator();
    osc.type = o.type ?? 'sine';
    osc.frequency.setValueAtTime(o.f, t);
    if (o.f2) osc.frequency.exponentialRampToValueAtTime(Math.max(1, o.f2), t + (o.glide ?? a + o.d));
    if (o.detune) osc.detune.value = o.detune;
    const g = ctx.createGain();
    this.envelope(g, t, a, o.d, o.g, hold);
    let node: AudioNode = osc;
    const extra: AudioNode[] = [];
    if (o.lp) {
      const f = ctx.createBiquadFilter();
      f.type = 'lowpass'; f.frequency.setValueAtTime(o.lp, t); f.Q.value = o.q ?? 0.7;
      if (o.lp2) f.frequency.exponentialRampToValueAtTime(o.lp2, end);
      node.connect(f); node = f; extra.push(f);
    }
    if (o.hp) {
      const f = ctx.createBiquadFilter();
      f.type = 'highpass'; f.frequency.value = o.hp;
      node.connect(f); node = f; extra.push(f);
    }
    node.connect(g).connect(this.dest(o.bus ?? 'sfx', o.pan, o.verb, end));
    osc.start(t);
    osc.stop(end + 0.05);
    this.cleanup(end, osc, g, ...extra);
  }

  hiss(o: NoiseOpts) {
    const ctx = this.ctx;
    if (!ctx || ctx.state !== 'running') return;
    const t = o.t ?? ctx.currentTime, a = o.a ?? 0.003, end = t + a + o.d;
    const src = ctx.createBufferSource();
    src.buffer = o.brown ? this.brownBuf : this.white;
    src.loop = true;
    src.playbackRate.value = 0.9 + Math.random() * 0.2;
    const g = ctx.createGain();
    this.envelope(g, t, a, o.d, o.g);
    let node: AudioNode = src;
    const extra: AudioNode[] = [];
    if (o.bp) {
      const f = ctx.createBiquadFilter();
      f.type = 'bandpass'; f.frequency.setValueAtTime(o.bp, t); f.Q.value = o.q ?? 1;
      if (o.bp2) f.frequency.exponentialRampToValueAtTime(o.bp2, end);
      node.connect(f); node = f; extra.push(f);
    }
    if (o.lp) {
      const f = ctx.createBiquadFilter();
      f.type = 'lowpass'; f.frequency.setValueAtTime(o.lp, t);
      if (o.lp2) f.frequency.exponentialRampToValueAtTime(o.lp2, end);
      node.connect(f); node = f; extra.push(f);
    }
    if (o.hp) {
      const f = ctx.createBiquadFilter();
      f.type = 'highpass'; f.frequency.value = o.hp;
      node.connect(f); node = f; extra.push(f);
    }
    node.connect(g).connect(this.dest(o.bus ?? 'sfx', o.pan, o.verb, end));
    src.start(t, Math.random() * 1.5);
    src.stop(end + 0.05);
    this.cleanup(end, src, g, ...extra);
  }

  /** Two-operator FM: bells, clinks, chimes, anything struck. */
  fm(o: FmOpts) {
    const ctx = this.ctx;
    if (!ctx || ctx.state !== 'running') return;
    const t = o.t ?? ctx.currentTime, a = o.a ?? 0.002, end = t + a + o.d;
    const car = ctx.createOscillator(), mod = ctx.createOscillator();
    car.frequency.setValueAtTime(o.f, t);
    if (o.f2) car.frequency.exponentialRampToValueAtTime(o.f2, end);
    mod.frequency.setValueAtTime(o.f * o.ratio, t);
    const mg = ctx.createGain();
    mg.gain.setValueAtTime(o.f * o.index, t);
    mg.gain.exponentialRampToValueAtTime(Math.max(1, o.f * o.index * 0.05), end);
    mod.connect(mg).connect(car.frequency);
    const g = ctx.createGain();
    this.envelope(g, t, a, o.d, o.g);
    car.connect(g).connect(this.dest(o.bus ?? 'sfx', o.pan, o.verb, end));
    car.start(t); mod.start(t);
    car.stop(end + 0.05); mod.stop(end + 0.05);
    this.cleanup(end, car, mod, mg, g);
  }

  /* --------------------------------------------------------- buffers -- */

  private noiseBuffer(brown: boolean) {
    const ctx = this.ctx!;
    const len = ctx.sampleRate * 2;
    const buf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    let last = 0;
    for (let i = 0; i < len; i++) {
      const w = Math.random() * 2 - 1;
      if (brown) { last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; } else d[i] = w;
    }
    return buf;
  }

  /** A dark stone room: decorrelated noise, darkening as it decays. */
  private impulse(seconds: number, decay: number) {
    const ctx = this.ctx!;
    const len = Math.floor(ctx.sampleRate * seconds);
    const buf = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let c = 0; c < 2; c++) {
      const d = buf.getChannelData(c);
      let lp = 0;
      for (let i = 0; i < len; i++) {
        const k = i / len;
        // The high end dies first.
        const a = 0.55 - k * 0.45;
        lp = lp + a * ((Math.random() * 2 - 1) - lp);
        const early = i < ctx.sampleRate * 0.08 && Math.random() < 0.004 ? (Math.random() - 0.5) * 3 : 0;
        d[i] = (lp + early) * Math.pow(1 - k, decay);
      }
    }
    return buf;
  }
}

export const audio = new AudioEngine();
if (typeof window !== 'undefined') (window as unknown as { __audio: AudioEngine }).__audio = audio;
