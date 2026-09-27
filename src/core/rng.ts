/* Seeded random stream (mulberry32). The simulation draws from one of these
 * instead of Math.random so an expedition can be replayed from its seed and
 * so tests are deterministic. */

export class Rng {
  private s: number;
  constructor(seed = 0x9e3779b9) {
    this.s = seed >>> 0 || 1;
  }

  get state() { return this.s; }
  set state(v: number) { this.s = v >>> 0 || 1; }

  /** [0, 1) */
  next() {
    let t = (this.s = (this.s + 0x6d2b79f5) >>> 0);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  range(lo: number, hi: number) { return lo + (hi - lo) * this.next(); }
  int(lo: number, hiInclusive: number) { return lo + Math.floor(this.next() * (hiInclusive - lo + 1)); }
  chance(p: number) { return this.next() < p; }
  sign() { return this.next() < 0.5 ? -1 : 1; }
  pick<T>(arr: readonly T[]): T { return arr[Math.floor(this.next() * arr.length)]; }

  /** Weighted pick over `{ weight }` entries. */
  weighted<T extends { weight: number }>(arr: readonly T[]): T {
    let total = 0;
    for (const a of arr) total += a.weight;
    let r = this.next() * total;
    for (const a of arr) {
      r -= a.weight;
      if (r <= 0) return a;
    }
    return arr[arr.length - 1];
  }

  shuffle<T>(arr: T[]): T[] {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(this.next() * (i + 1));
      const t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }

  /** Gaussian-ish via sum of uniforms. */
  normal(mean = 0, sd = 1) {
    return mean + sd * ((this.next() + this.next() + this.next() + this.next() - 2) * 1.7320508);
  }
}

/** Shared stream for purely cosmetic randomness (particles, idle offsets).
 *  Never used by the simulation, so visuals can't desync gameplay. */
export const fxRng = new Rng(0xc0ffee);
