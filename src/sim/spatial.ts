/* Uniform-grid spatial hash over integer ids, rebuilt once per tick.
 *
 * Queries return candidates from the overlapping cells into a caller-owned
 * array, so a query allocates nothing. Rebuilding a few hundred entries is
 * cheaper than maintaining a tree, and the world is bounded. */

export class SpatialHash {
  private heads: Int32Array;
  private next: Int32Array;
  private cols: number;
  private rows: number;

  constructor(readonly size: number, readonly cell: number, capacity: number) {
    this.cols = Math.ceil(size / cell);
    this.rows = this.cols;
    this.heads = new Int32Array(this.cols * this.rows).fill(-1);
    this.next = new Int32Array(capacity).fill(-1);
  }

  private half() { return this.size / 2; }

  clear() { this.heads.fill(-1); }

  insert(id: number, x: number, z: number) {
    const cx = Math.floor((x + this.half()) / this.cell);
    const cz = Math.floor((z + this.half()) / this.cell);
    if (cx < 0 || cz < 0 || cx >= this.cols || cz >= this.rows) return;
    const c = cz * this.cols + cx;
    if (id >= this.next.length) {
      const n = new Int32Array(Math.max(id + 1, this.next.length * 2)).fill(-1);
      n.set(this.next);
      this.next = n;
    }
    this.next[id] = this.heads[c];
    this.heads[c] = id;
  }

  /** Candidate ids whose cell overlaps the query circle's bounding square. */
  query(x: number, z: number, r: number, out: number[]) {
    out.length = 0;
    const h = this.half();
    const x0 = Math.max(0, Math.floor((x - r + h) / this.cell));
    const x1 = Math.min(this.cols - 1, Math.floor((x + r + h) / this.cell));
    const z0 = Math.max(0, Math.floor((z - r + h) / this.cell));
    const z1 = Math.min(this.rows - 1, Math.floor((z + r + h) / this.cell));
    for (let cz = z0; cz <= z1; cz++) {
      for (let cx = x0; cx <= x1; cx++) {
        for (let id = this.heads[cz * this.cols + cx]; id !== -1; id = this.next[id]) out.push(id);
      }
    }
    return out;
  }
}
