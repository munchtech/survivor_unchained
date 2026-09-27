/* Static geometry the fight happens around, and how the horde gets around it.
 *
 * Colliders are circles (trunks, rocks, posts) and oriented boxes (walls,
 * houses, wagons). Movers are circles; resolve() pushes a mover out of
 * whatever it overlaps so it slides along walls instead of sticking.
 *
 * The flow field is what lets two hundred creatures find their way around a
 * forest to you without two hundred path searches: one Dijkstra flood from
 * the survivor's cell across a window of the navigation grid, every few
 * ticks, and each creature just reads the downhill direction under its feet.
 *
 * Colliders can be tagged and removed at runtime (a bramble wall burned
 * away, a gate opened), which rebakes the navigation grid locally. */

export interface Collider {
  id: number;
  kind: 'circle' | 'box';
  x: number; z: number;
  r: number; // circle radius, or bounding radius for a box
  hw: number; hd: number; rot: number; // box half-width, half-depth, rotation (radians)
  tag?: string;
  /** Soft colliders block movement but not projectiles (a hedge, a fence). */
  soft?: boolean;
  /** Blocks movement for the survivor only (an invisible edge of the zone). */
  playerOnly?: boolean;
}

export interface RayHit { t: number; collider: Collider }

export class CollisionWorld {
  readonly half: number;
  private colliders = new Map<number, Collider>();
  private buckets: Map<number, number[]> = new Map();
  private nextId = 1;
  readonly navCell = 1;
  readonly navSize: number;
  navBlocked: Uint8Array;
  /** Playable bounds (square, centred). */
  bound: number;

  constructor(readonly size: number, readonly bucket = 6) {
    this.half = size / 2;
    this.bound = this.half - 2;
    this.navSize = Math.ceil(size / this.navCell);
    this.navBlocked = new Uint8Array(this.navSize * this.navSize);
  }

  private bkey(bx: number, bz: number) { return bz * 4096 + bx; }

  private bucketsFor(c: Collider, fn: (key: number) => void) {
    const b0x = Math.floor((c.x - c.r + this.half) / this.bucket), b1x = Math.floor((c.x + c.r + this.half) / this.bucket);
    const b0z = Math.floor((c.z - c.r + this.half) / this.bucket), b1z = Math.floor((c.z + c.r + this.half) / this.bucket);
    for (let bz = b0z; bz <= b1z; bz++) for (let bx = b0x; bx <= b1x; bx++) fn(this.bkey(bx, bz));
  }

  addCircle(x: number, z: number, r: number, opts: Partial<Collider> = {}) {
    return this.insert({ id: this.nextId++, kind: 'circle', x, z, r, hw: r, hd: r, rot: 0, ...opts });
  }

  addBox(x: number, z: number, hw: number, hd: number, rot = 0, opts: Partial<Collider> = {}) {
    return this.insert({ id: this.nextId++, kind: 'box', x, z, r: Math.hypot(hw, hd), hw, hd, rot, ...opts });
  }

  private insert(c: Collider) {
    this.colliders.set(c.id, c);
    this.bucketsFor(c, (k) => {
      let b = this.buckets.get(k);
      if (!b) this.buckets.set(k, (b = []));
      b.push(c.id);
    });
    if (!c.playerOnly) this.bakeNav(c.x - c.r - 1, c.z - c.r - 1, c.x + c.r + 1, c.z + c.r + 1);
    return c;
  }

  remove(id: number) {
    const c = this.colliders.get(id);
    if (!c) return;
    this.colliders.delete(id);
    this.bucketsFor(c, (k) => {
      const b = this.buckets.get(k);
      if (b) { const i = b.indexOf(id); if (i >= 0) b.splice(i, 1); }
    });
    this.bakeNav(c.x - c.r - 1, c.z - c.r - 1, c.x + c.r + 1, c.z + c.r + 1);
  }

  removeTagged(tag: string) {
    for (const c of [...this.colliders.values()]) if (c.tag === tag) this.remove(c.id);
  }

  byTag(tag: string) { return [...this.colliders.values()].filter((c) => c.tag === tag); }
  /** Every collider (the map draws the walls and houses from these). */
  all() { return [...this.colliders.values()]; }

  private near(x: number, z: number, r: number, out: Collider[]) {
    out.length = 0;
    const b0x = Math.floor((x - r + this.half) / this.bucket), b1x = Math.floor((x + r + this.half) / this.bucket);
    const b0z = Math.floor((z - r + this.half) / this.bucket), b1z = Math.floor((z + r + this.half) / this.bucket);
    let seen: Set<number> | null = null;
    for (let bz = b0z; bz <= b1z; bz++) {
      for (let bx = b0x; bx <= b1x; bx++) {
        const b = this.buckets.get(this.bkey(bx, bz));
        if (!b) continue;
        for (const id of b) {
          if (b0x !== b1x || b0z !== b1z) {
            if (!seen) seen = new Set();
            if (seen.has(id)) continue;
            seen.add(id);
          }
          out.push(this.colliders.get(id)!);
        }
      }
    }
    return out;
  }

  private scratch: Collider[] = [];

  /** Push a circle out of every collider it overlaps. Returns true if it
   *  touched anything. `isPlayer` lets player-only edges apply. */
  resolve(p: { x: number; z: number }, r: number, isPlayer = false): boolean {
    let touched = false;
    for (let iter = 0; iter < 3; iter++) {
      let moved = false;
      for (const c of this.near(p.x, p.z, r + 0.5, this.scratch)) {
        if (c.playerOnly && !isPlayer) continue;
        if (c.kind === 'circle') {
          const dx = p.x - c.x, dz = p.z - c.z;
          const d2 = dx * dx + dz * dz, min = c.r + r;
          if (d2 < min * min) {
            const d = Math.sqrt(d2) || 0.0001;
            const push = min - d;
            p.x += (dx / d) * push;
            p.z += (dz / d) * push;
            moved = touched = true;
          }
        } else {
          // Into box space.
          const cos = Math.cos(-c.rot), sin = Math.sin(-c.rot);
          const lx = (p.x - c.x) * cos - (p.z - c.z) * sin;
          const lz = (p.x - c.x) * sin + (p.z - c.z) * cos;
          const qx = Math.max(-c.hw, Math.min(c.hw, lx));
          const qz = Math.max(-c.hd, Math.min(c.hd, lz));
          let dx = lx - qx, dz = lz - qz;
          let d2 = dx * dx + dz * dz;
          if (d2 < r * r) {
            let nx: number, nz: number, push: number;
            if (d2 < 1e-8) {
              // Centre inside the box: leave by the nearest face.
              const px = c.hw - Math.abs(lx), pz = c.hd - Math.abs(lz);
              if (px < pz) { nx = Math.sign(lx) || 1; nz = 0; push = px + r; }
              else { nx = 0; nz = Math.sign(lz) || 1; push = pz + r; }
            } else {
              const d = Math.sqrt(d2);
              nx = dx / d; nz = dz / d; push = r - d;
            }
            // Back to world space.
            const wc = Math.cos(c.rot), ws = Math.sin(c.rot);
            p.x += (nx * wc - nz * ws) * push;
            p.z += (nx * ws + nz * wc) * push;
            moved = touched = true;
            dx = dz = d2 = 0;
          }
        }
      }
      if (!moved) break;
    }
    const b = this.bound;
    if (p.x < -b) { p.x = -b; touched = true; } else if (p.x > b) { p.x = b; touched = true; }
    if (p.z < -b) { p.z = -b; touched = true; } else if (p.z > b) { p.z = b; touched = true; }
    return touched;
  }

  /** Is a circle at (x, z) overlapping anything solid? */
  blocked(x: number, z: number, r: number, includeSoft = true) {
    for (const c of this.near(x, z, r + 0.5, this.scratch)) {
      if (c.playerOnly || (!includeSoft && c.soft)) continue;
      if (this.overlaps(c, x, z, r)) return true;
    }
    return false;
  }

  private overlaps(c: Collider, x: number, z: number, r: number) {
    if (c.kind === 'circle') {
      const dx = x - c.x, dz = z - c.z;
      return dx * dx + dz * dz < (c.r + r) * (c.r + r);
    }
    const cos = Math.cos(-c.rot), sin = Math.sin(-c.rot);
    const lx = (x - c.x) * cos - (z - c.z) * sin;
    const lz = (x - c.x) * sin + (z - c.z) * cos;
    const qx = Math.max(-c.hw, Math.min(c.hw, lx)), qz = Math.max(-c.hd, Math.min(c.hd, lz));
    return (lx - qx) ** 2 + (lz - qz) ** 2 < r * r;
  }

  /** First solid collider along a segment (projectiles, charges, sight). */
  raycast(x0: number, z0: number, x1: number, z1: number, r = 0, solidOnly = true): RayHit | null {
    const len = Math.hypot(x1 - x0, z1 - z0);
    if (len < 1e-6) return null;
    const steps = Math.ceil(len / 0.35);
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      const x = x0 + (x1 - x0) * t, z = z0 + (z1 - z0) * t;
      for (const c of this.near(x, z, r + 0.5, this.scratch)) {
        if (c.playerOnly || (solidOnly && c.soft)) continue;
        if (this.overlaps(c, x, z, r)) return { t, collider: c };
      }
    }
    return null;
  }

  /** Colliders whose centre lies within a radius (for "what did the
   *  explosion touch": barrels, bramble walls, braziers). */
  within(x: number, z: number, r: number): Collider[] {
    return this.near(x, z, r, []).filter((c) => (c.x - x) ** 2 + (c.z - z) ** 2 <= (r + c.r) ** 2);
  }

  /* ---------------------------------------------------------- nav grid -- */
  private bakeNav(x0: number, z0: number, x1: number, z1: number) {
    const n = this.navSize, h = this.half;
    const i0 = Math.max(0, Math.floor(x0 + h)), i1 = Math.min(n - 1, Math.ceil(x1 + h));
    const j0 = Math.max(0, Math.floor(z0 + h)), j1 = Math.min(n - 1, Math.ceil(z1 + h));
    for (let j = j0; j <= j1; j++) {
      for (let i = i0; i <= i1; i++) {
        const x = -h + i + 0.5, z = -h + j + 0.5;
        this.navBlocked[j * n + i] = this.blocked(x, z, 0.42, true) ? 1 : 0;
      }
    }
  }

  isNavBlocked(i: number, j: number) {
    if (i < 0 || j < 0 || i >= this.navSize || j >= this.navSize) return true;
    return this.navBlocked[j * this.navSize + i] === 1;
  }
}

/** Downhill directions toward a target over a window of the nav grid. */
export class FlowField {
  readonly win: number;
  private dist: Uint16Array;
  private ox = 0;
  private oz = 0;
  private tx = 1e9;
  private tz = 1e9;
  ready = false;

  constructor(private world: CollisionWorld, readonly radius = 44) {
    this.win = radius * 2 + 1;
    this.dist = new Uint16Array(this.win * this.win);
  }

  /** Re-flood if the target has moved to another cell. */
  update(x: number, z: number, force = false) {
    const h = this.world.half;
    const ti = Math.floor(x + h), tj = Math.floor(z + h);
    if (!force && ti === this.tx && tj === this.tz) return;
    this.tx = ti; this.tz = tj;
    this.ox = ti - this.radius;
    this.oz = tj - this.radius;
    const W = this.win;
    this.dist.fill(65535);
    // Dial's algorithm: small integer costs, bucketed by distance.
    const buckets: number[][] = [];
    const push = (idx: number, d: number) => { (buckets[d] ??= []).push(idx); };
    const start = this.radius * W + this.radius;
    this.dist[start] = 0;
    push(start, 0);
    const w = this.world;
    for (let d = 0; d < buckets.length; d++) {
      const b = buckets[d];
      if (!b) continue;
      for (let k = 0; k < b.length; k++) {
        const idx = b[k];
        if (this.dist[idx] !== d) continue;
        const li = idx % W, lj = (idx / W) | 0;
        for (let dj = -1; dj <= 1; dj++) {
          for (let di = -1; di <= 1; di++) {
            if (!di && !dj) continue;
            const ni = li + di, nj = lj + dj;
            if (ni < 0 || nj < 0 || ni >= W || nj >= W) continue;
            const gi = this.ox + ni, gj = this.oz + nj;
            if (w.isNavBlocked(gi, gj)) continue;
            // No cutting corners past a blocked orthogonal neighbour.
            if (di && dj && (w.isNavBlocked(this.ox + li + di, this.oz + lj) || w.isNavBlocked(this.ox + li, this.oz + lj + dj))) continue;
            const nd = d + (di && dj ? 14 : 10);
            const nidx = nj * W + ni;
            if (nd < this.dist[nidx]) { this.dist[nidx] = nd; push(nidx, nd); }
          }
        }
      }
    }
    this.ready = true;
  }

  /** Write the downhill direction at (x, z) into out. False outside the
   *  window or on an unreachable cell. */
  dir(x: number, z: number, out: { x: number; z: number }): boolean {
    if (!this.ready) return false;
    const h = this.world.half;
    const li = Math.floor(x + h) - this.ox, lj = Math.floor(z + h) - this.oz;
    const W = this.win;
    if (li < 1 || lj < 1 || li >= W - 1 || lj >= W - 1) return false;
    const here = this.dist[lj * W + li];
    if (here === 65535) return false;
    let best = here, bx = 0, bz = 0;
    for (let dj = -1; dj <= 1; dj++) {
      for (let di = -1; di <= 1; di++) {
        if (!di && !dj) continue;
        const d = this.dist[(lj + dj) * W + li + di];
        if (d < best) { best = d; bx = di; bz = dj; }
      }
    }
    if (bx === 0 && bz === 0) return false;
    const m = Math.hypot(bx, bz);
    out.x = bx / m;
    out.z = bz / m;
    return true;
  }

  /** Path distance to the target in metres, or Infinity. */
  distanceAt(x: number, z: number) {
    const h = this.world.half;
    const li = Math.floor(x + h) - this.ox, lj = Math.floor(z + h) - this.oz;
    if (li < 0 || lj < 0 || li >= this.win || lj >= this.win) return Infinity;
    const d = this.dist[lj * this.win + li];
    return d === 65535 ? Infinity : d / 10;
  }
}
