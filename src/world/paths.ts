import { distToSegment } from '@/core/math';

/* Paths across a zone: roads, ruts, streams.
 *
 * Written by hand as a few key points, then made to wander (nothing that
 * water or wheels made runs dead straight for thirty metres), and indexed
 * on a grid so the terrain builder can ask "how far to the stream, and how
 * far along it" a million times without walking every segment. */

export type Pt = [number, number];

/** Wander between key points: the path still passes through every key,
 *  but swings side to side between them in two overlapping waves. */
export function meander(keys: Pt[], amp: number, step = 2.5, seed = 0): Pt[] {
  const out: Pt[] = [];
  let run = 0;
  for (let i = 0; i < keys.length - 1; i++) {
    const [ax, az] = keys[i], [bx, bz] = keys[i + 1];
    const l = Math.hypot(bx - ax, bz - az);
    const n = Math.max(1, Math.ceil(l / step));
    const nx = -(bz - az) / l, nz = (bx - ax) / l;
    for (let k = 0; k < n; k++) {
      const t = k / n, s = run + t * l;
      // Pinned at the keys, free in between.
      const pin = Math.sin(Math.PI * t);
      const off = amp * pin * (Math.sin(s * 0.21 + seed) * 0.65 + Math.sin(s * 0.37 + seed * 2.3) * 0.35);
      out.push([ax + (bx - ax) * t + nx * off, az + (bz - az) * t + nz * off]);
    }
    run += l;
  }
  out.push(keys[keys.length - 1]);
  return out;
}

/** Nearest point on a path, fast: exact within `reach`, the key-point
 *  outline beyond (close enough for "is this far from the water"). */
export class PathIndex {
  private cells = new Map<number, number[]>();
  private runs: number[] = [];
  readonly length: number;

  constructor(readonly pts: Pt[], private reach = 14, private cell = 8, private coarse?: Pt[]) {
    let run = 0;
    for (let i = 0; i < pts.length - 1; i++) {
      this.runs.push(run);
      const [ax, az] = pts[i], [bx, bz] = pts[i + 1];
      run += Math.hypot(bx - ax, bz - az);
      const x0 = Math.floor((Math.min(ax, bx) - reach) / cell), x1 = Math.floor((Math.max(ax, bx) + reach) / cell);
      const z0 = Math.floor((Math.min(az, bz) - reach) / cell), z1 = Math.floor((Math.max(az, bz) + reach) / cell);
      for (let cx = x0; cx <= x1; cx++) for (let cz = z0; cz <= z1; cz++) {
        const k = this.key(cx, cz);
        let list = this.cells.get(k);
        if (!list) this.cells.set(k, (list = []));
        list.push(i);
      }
    }
    this.length = run;
  }

  private key(cx: number, cz: number) { return (cx + 2048) * 4096 + (cz + 2048); }

  /** Distance to the path, and how far along it the nearest point lies. */
  nearest(x: number, z: number): { d: number; s: number } {
    const list = this.cells.get(this.key(Math.floor(x / this.cell), Math.floor(z / this.cell)));
    let best = Infinity, bestS = 0;
    if (list) {
      for (const i of list) {
        const [ax, az] = this.pts[i], [bx, bz] = this.pts[i + 1];
        const dx = bx - ax, dz = bz - az, l2 = dx * dx + dz * dz;
        const t = l2 > 0 ? Math.max(0, Math.min(1, ((x - ax) * dx + (z - az) * dz) / l2)) : 0;
        const d = Math.hypot(x - ax - dx * t, z - az - dz * t);
        if (d < best) { best = d; bestS = this.runs[i] + t * Math.sqrt(l2); }
      }
    }
    if (best <= this.reach) return { d: best, s: bestS };
    return { d: Math.max(this.reach, this.far(x, z)), s: bestS };
  }

  dist(x: number, z: number) { return this.nearest(x, z).d; }

  private far(x: number, z: number) {
    const p = this.coarse ?? this.pts;
    let d = Infinity;
    for (let i = 0; i < p.length - 1; i++) d = Math.min(d, distToSegment(x, z, p[i][0], p[i][1], p[i + 1][0], p[i + 1][1]));
    return d;
  }
}
