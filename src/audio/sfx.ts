import { audio as A } from './engine';

/* Every one-shot the game makes, by name.
 *
 * Each is a little recipe: a thump, a hiss through a filter, a struck
 * bell, layered and pitched a bit differently every time so that the
 * two-hundredth sword hit does not sound like the first one played again.
 * `pan` and `near` (0..1, how close to the survivor) come from where the
 * thing happened. */

type School = string;
const r = (a: number, b: number) => a + Math.random() * (b - a);
const semis = (n: number) => Math.pow(2, n / 12);

export interface Where { pan?: number; near?: number }

export const SFX = {
  /* ------------------------------------------------------------ combat -- */
  hit(school: School, crit: boolean, w: Where = {}) {
    if (!A.gate('hit', 7, 70)) return;
    const pan = w.pan, g = 0.5 + 0.5 * (w.near ?? 1);
    switch (school) {
      case 'fire':
        A.hiss({ d: r(0.1, 0.16), g: 0.1 * g, lp: 3200, lp2: 600, pan });
        A.tone({ f: r(120, 150), f2: 60, d: 0.1, g: 0.12 * g, pan });
        break;
      case 'frost':
        A.fm({ f: r(2200, 2800), ratio: 3.07, index: 1.2, d: 0.2, g: 0.035 * g, pan, verb: 0.3 });
        A.hiss({ d: 0.05, g: 0.06 * g, hp: 4200, pan });
        break;
      case 'lightning':
        A.hiss({ d: 0.07, g: 0.1 * g, bp: 3200, q: 0.6, pan });
        A.tone({ f: r(80, 110), type: 'square', d: 0.06, g: 0.035 * g, lp: 1400, pan });
        break;
      case 'holy':
        A.fm({ f: r(800, 1000), ratio: 2, index: 0.8, d: 0.35, g: 0.04 * g, pan, verb: 0.4 });
        A.hiss({ d: 0.05, g: 0.05 * g, bp: 2400, pan });
        break;
      case 'nature': case 'poison':
        A.hiss({ d: 0.1, g: 0.09 * g, bp: 500, bp2: 1400, q: 3, pan });
        break;
      case 'shadow': case 'arcane':
        A.tone({ f: r(200, 260), f2: 90, type: 'sawtooth', d: 0.13, g: 0.06 * g, lp: 1100, pan });
        A.hiss({ d: 0.06, g: 0.05 * g, bp: 1400, pan });
        break;
      default:
        A.hiss({ d: r(0.05, 0.08), g: 0.14 * g, bp: r(1500, 2200), bp2: 600, q: 1.2, pan });
        A.tone({ f: r(130, 160), f2: 65, d: 0.08, g: 0.16 * g, pan });
    }
    if (crit && A.gate('crit', 3, 90)) A.fm({ f: r(1100, 1400), ratio: 2.71, index: 2.5, d: 0.28, g: 0.05 * g, pan, verb: 0.25 });
  },

  blocked(w: Where = {}) {
    if (!A.gate('block', 2, 90)) return;
    A.fm({ f: r(520, 640), ratio: 1.41, index: 3.5, d: 0.35, g: 0.06, pan: w.pan, verb: 0.3 });
  },

  /** A ward giving way: a bright crack, and glass going everywhere. */
  shatter() {
    if (!A.gate('shatter', 1, 250)) return;
    A.fm({ f: r(1700, 1900), ratio: 2.76, index: 4, d: 0.5, g: 0.05, verb: 0.45 });
    A.fm({ t: A.now + 0.03, f: r(2500, 2800), ratio: 3.41, index: 3, d: 0.6, g: 0.035, verb: 0.5 });
    A.hiss({ a: 0.002, d: 0.35, g: 0.05, hp: 3500, verb: 0.3 });
  },

  /** Your own heart, when you are close to the end: lub, dub. */
  heartbeat(urgency: number) {
    const g = 0.05 + 0.06 * urgency;
    A.tone({ f: 58, f2: 42, d: 0.16, g, lp: 220, bus: 'sfx' });
    A.tone({ t: A.now + 0.24, f: 52, f2: 38, d: 0.2, g: g * 0.75, lp: 200, bus: 'sfx' });
  },

  kill(family: string, elite: boolean, boss: boolean, w: Where = {}) {
    if (!A.gate('kill', 5, 90)) return;
    const pan = w.pan, g = 0.5 + 0.5 * (w.near ?? 1);
    A.tone({ f: r(95, 115), f2: 38, d: 0.2, g: 0.2 * g, pan });
    A.hiss({ d: 0.14, g: 0.07 * g, lp: 1100, lp2: 200, pan });
    if (family === 'undead') {
      // Bones: two dry cracks.
      A.hiss({ d: 0.03, g: 0.08 * g, bp: 2600, q: 4, pan });
      A.hiss({ t: A.now + 0.045, d: 0.025, g: 0.06 * g, bp: 3400, q: 4, pan });
    } else if (family === 'wolf' || family === 'beast') {
      A.tone({ f: r(800, 1000), f2: 420, type: 'triangle', d: 0.12, g: 0.035 * g, pan });
    } else if (family === 'lampling' || family === 'kerchief' || family === 'humanoid') {
      A.tone({ f: r(260, 320), f2: 150, type: 'triangle', d: 0.14, g: 0.03 * g, lp: 900, pan });
    }
    if (elite || boss) {
      A.tone({ f: 70, f2: 28, d: boss ? 1.6 : 0.8, g: boss ? 0.45 : 0.3, pan });
      A.hiss({ d: boss ? 1.4 : 0.7, g: 0.12, lp: 900, lp2: 120, brown: true });
      if (boss) SFX.stinger('triumph');
    }
  },

  hurt(amount: number) {
    if (!A.gate('hurt', 2, 160)) return;
    const k = Math.min(1, amount / 30);
    A.tone({ f: 120, f2: 55, type: 'sawtooth', d: 0.22, g: 0.12 + 0.12 * k, lp: 520 });
    A.hiss({ d: 0.16, g: 0.08 + 0.06 * k, lp: 1400, lp2: 300 });
  },

  dodge() {
    A.hiss({ a: 0.02, d: 0.18, g: 0.08, bp: 900, bp2: 3200, q: 1.4, bus: 'sfx' });
  },

  dash() {
    A.hiss({ a: 0.02, d: 0.26, g: 0.1, bp: 500, bp2: 2600, q: 1.1 });
    A.tone({ f: 180, f2: 90, d: 0.2, g: 0.05 });
  },

  swing(w: Where = {}) {
    if (!A.gate('swing', 3, 110)) return;
    A.hiss({ a: 0.01, d: 0.09, g: 0.04, bp: r(2000, 2600), bp2: 800, q: 2, pan: w.pan });
  },

  shoot(school: School, w: Where = {}) {
    if (!A.gate('shoot', 4, 90)) return;
    if (school === 'physical') {
      A.tone({ f: r(280, 330), f2: 190, type: 'triangle', d: 0.08, g: 0.035, pan: w.pan });
      A.hiss({ d: 0.05, g: 0.03, hp: 3000, pan: w.pan });
    } else {
      A.tone({ f: r(800, 1000), f2: 300, d: 0.1, g: 0.025, pan: w.pan });
    }
  },

  explosion(power: number, w: Where = {}) {
    if (!A.gate('boom', 3, 150)) return;
    const g = Math.min(1.4, 0.5 + power * 0.4) * (0.5 + 0.5 * (w.near ?? 1));
    A.tone({ f: 80, f2: 28, d: 0.7, g: 0.35 * g, pan: w.pan });
    A.hiss({ d: 0.9, g: 0.25 * g, lp: 1600, lp2: 140, brown: true, pan: w.pan });
    A.hiss({ d: 0.25, g: 0.1 * g, bp: 2400, q: 0.6, pan: w.pan });
  },

  nova(school: School) {
    if (!A.gate('nova', 2, 200)) return;
    A.tone({ f: 190, f2: 55, d: 0.4, g: 0.18 });
    A.hiss({ a: 0.02, d: 0.35, g: 0.08, bp: 700, bp2: 2200, q: 0.8 });
    if (school === 'frost') A.fm({ f: 1800, ratio: 3.1, index: 1, d: 0.5, g: 0.03, verb: 0.4 });
    if (school === 'holy') A.fm({ f: 660, ratio: 2, index: 0.6, d: 0.8, g: 0.04, verb: 0.5 });
  },

  bash() {
    A.tone({ f: 140, f2: 50, d: 0.25, g: 0.28 });
    A.fm({ f: 420, ratio: 1.41, index: 3, d: 0.3, g: 0.05, verb: 0.25 });
    A.hiss({ d: 0.18, g: 0.1, lp: 1800, lp2: 300 });
  },

  spawn(style: string, w: Where = {}) {
    if (!A.gate('spawn', 2, 250) || (w.near ?? 1) < 0.2) return;
    if (style === 'rise') A.hiss({ a: 0.15, d: 0.5, g: 0.05 * (w.near ?? 1), lp: 500, brown: true, pan: w.pan });
    else if (style === 'burrow') A.hiss({ a: 0.05, d: 0.35, g: 0.06 * (w.near ?? 1), bp: 300, q: 1.5, brown: true, pan: w.pan });
  },

  /* --------------------------------------------------------- pickups --- */
  xp(streak: number) {
    if (!A.gate('xp', 8, 100)) return;
    const f = 1150 * semis(Math.min(24, streak) * 0.5);
    A.tone({ f, f2: f * 1.5, d: 0.05, g: 0.02, bus: 'sfx' });
  },

  gold() {
    if (!A.gate('gold', 3, 80)) return;
    A.fm({ f: r(2400, 2700), ratio: 1.93, index: 1.5, d: 0.12, g: 0.035 });
    A.fm({ t: A.now + 0.045, f: r(3100, 3500), ratio: 1.93, index: 1.5, d: 0.14, g: 0.03 });
  },

  loot(rare = false) {
    A.fm({ f: 1320, ratio: 2.01, index: 0.9, d: 0.7, g: 0.045, verb: 0.4 });
    A.fm({ t: A.now + 0.06, f: 1980, ratio: 2.01, index: 0.9, d: 0.8, g: 0.035, verb: 0.4 });
    if (rare) A.fm({ t: A.now + 0.14, f: 2640, ratio: 3.01, index: 0.7, d: 1.2, g: 0.03, verb: 0.6 });
    A.hiss({ a: 0.05, d: 0.5, g: 0.02, hp: 6000 });
  },

  heal() {
    if (!A.gate('heal', 1, 400)) return;
    A.fm({ f: 660, ratio: 2, index: 0.5, a: 0.05, d: 0.6, g: 0.04, verb: 0.5 });
    A.fm({ t: A.now + 0.08, f: 990, ratio: 2, index: 0.5, a: 0.05, d: 0.7, g: 0.03, verb: 0.5 });
  },

  /* ---------------------------------------------------------- growth --- */
  levelUp() {
    const base = 587.33; // D5
    [0, 3, 7, 12, 15].forEach((s, i) => A.fm({ t: A.now + i * 0.075, f: base * semis(s), ratio: 3.5, index: 0.35, d: 1.3, g: 0.05, verb: 0.6 }));
    A.tone({ f: 146.8, a: 0.2, d: 1.6, g: 0.1, type: 'triangle' });
    A.hiss({ a: 0.3, d: 0.9, g: 0.025, hp: 6500 });
  },

  evolve() {
    const base = 293.66;
    [0, 7, 12, 16, 19, 24].forEach((s, i) => A.fm({ t: A.now + i * 0.09, f: base * semis(s), ratio: 2.01, index: 0.8, d: 2.2, g: 0.045, verb: 0.7 }));
    A.tone({ f: 73.4, a: 0.3, d: 2.4, g: 0.16, type: 'sawtooth', lp: 400, lp2: 1400 });
  },

  discovery() {
    [0, 3, 10].forEach((s, i) => A.fm({ t: A.now + i * 0.16, f: 880 * semis(s), ratio: 3.01, index: 0.5, d: 1.6, g: 0.04, verb: 0.7, bus: 'ui' }));
  },

  /* ------------------------------------------------------------ story --- */
  stinger(kind: 'danger' | 'boss' | 'triumph' | 'story' | 'zone') {
    const t = A.now;
    if (kind === 'boss' || kind === 'danger') {
      const big = kind === 'boss';
      for (const f of big ? [73.4, 110, 146.8] : [110, 164.8]) A.tone({ t, f, type: 'sawtooth', a: 0.4, d: big ? 2.6 : 1.4, g: big ? 0.07 : 0.05, lp: 350, lp2: 1500, detune: r(-8, 8), bus: 'music', verb: 0.5 });
      A.tone({ t, f: 60, f2: 30, d: 1.2, g: big ? 0.4 : 0.25 });
      A.hiss({ t, d: 1, g: 0.12, lp: 700, lp2: 100, brown: true });
    } else if (kind === 'triumph') {
      [0, 4, 7, 12].forEach((s, i) => A.tone({ t: t + 0.25 + i * 0.12, f: 293.66 * semis(s), type: 'triangle', a: 0.05, d: 1.8, g: 0.06, bus: 'music', verb: 0.6 }));
    } else if (kind === 'story') {
      [0, 5, 7].forEach((s, i) => A.fm({ t: t + i * 0.22, f: 440 * semis(s), ratio: 2.01, index: 0.6, d: 1.8, g: 0.04, verb: 0.7, bus: 'ui' }));
    } else if (kind === 'zone') {
      A.tone({ t, f: 146.8, type: 'triangle', a: 0.6, d: 2.8, g: 0.05, bus: 'music', verb: 0.8 });
      A.tone({ t: t + 0.3, f: 220, type: 'triangle', a: 0.6, d: 2.6, g: 0.04, bus: 'music', verb: 0.8 });
      A.fm({ t: t + 0.6, f: 587.3, ratio: 3.5, index: 0.3, d: 2.4, g: 0.03, verb: 0.9, bus: 'music' });
    }
  },

  death() {
    A.tone({ f: 110, f2: 36, type: 'sawtooth', a: 0.1, d: 2.8, g: 0.12, lp: 700, lp2: 120, bus: 'music', verb: 0.7 });
    A.tone({ f: 55, f2: 27, a: 0.1, d: 2.6, g: 0.25 });
    A.hiss({ a: 1.2, d: 1.2, g: 0.06, bp: 900, bp2: 250, q: 0.7 });
  },

  quest() {
    A.tone({ f: 440, type: 'triangle', a: 0.02, d: 0.35, g: 0.05, bus: 'ui', verb: 0.4 });
    A.tone({ t: A.now + 0.14, f: 587.33, type: 'triangle', a: 0.02, d: 0.7, g: 0.05, bus: 'ui', verb: 0.5 });
  },

  rel(good: boolean) {
    const f = good ? 659.25 : 415.3;
    A.fm({ f, ratio: 2, index: 0.4, d: 0.6, g: 0.03, bus: 'ui', verb: 0.5 });
    A.fm({ t: A.now + 0.1, f: good ? f * semis(4) : f * semis(-3), ratio: 2, index: 0.4, d: 0.7, g: 0.025, bus: 'ui', verb: 0.5 });
  },

  door() {
    A.tone({ f: 90, f2: 60, d: 0.3, g: 0.12 });
    A.hiss({ a: 0.08, d: 0.4, g: 0.05, bp: 400, bp2: 200, q: 2, brown: true });
  },

  /* -------------------------------------------------------- interface --- */
  hover() {
    if (!A.gate('hover', 1, 45)) return;
    A.tone({ f: 2100, d: 0.025, g: 0.008, bus: 'ui' });
  },
  click() {
    if (!A.gate('click', 2, 60)) return;
    A.hiss({ d: 0.02, g: 0.03, hp: 2600, bus: 'ui' });
    A.tone({ f: 820, f2: 700, d: 0.04, g: 0.03, bus: 'ui' });
  },
  open() {
    A.hiss({ a: 0.03, d: 0.2, g: 0.04, bp: 1600, bp2: 900, q: 0.7, bus: 'ui' });
    A.tone({ f: 160, f2: 110, d: 0.12, g: 0.05, bus: 'ui' });
  },
  close() {
    A.hiss({ a: 0.01, d: 0.12, g: 0.03, bp: 900, bp2: 1800, q: 0.7, bus: 'ui' });
  },
  page() {
    if (!A.gate('page', 1, 120)) return;
    A.hiss({ a: 0.01, d: 0.07, g: 0.025, bp: r(2600, 3200), q: 0.9, bus: 'ui' });
  },
  pick() {
    A.fm({ f: 740, ratio: 2, index: 0.7, d: 0.3, g: 0.04, bus: 'ui', verb: 0.3 });
    A.tone({ f: 220, f2: 180, d: 0.12, g: 0.04, bus: 'ui' });
  },
  equip() {
    A.fm({ f: r(380, 460), ratio: 1.41, index: 2.2, d: 0.22, g: 0.04, bus: 'ui' });
    A.hiss({ d: 0.06, g: 0.03, bp: 1800, bus: 'ui' });
  },
  deny() {
    A.tone({ f: 180, type: 'square', d: 0.08, g: 0.02, lp: 900, bus: 'ui' });
    A.tone({ t: A.now + 0.09, f: 150, type: 'square', d: 0.1, g: 0.02, lp: 900, bus: 'ui' });
  },
};
