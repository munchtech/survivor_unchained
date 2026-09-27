import type { ZoneBuild } from '@/game/scene';
import type { TerrainPaint } from '@/render/terrain';

/* The map, drawn by hand (by a hand that is code).
 *
 * Everything on it comes from the zone itself: the ground's height becomes
 * hill shading and contour lines, what is painted on the ground (road dirt,
 * flagstones, mud, blight) tints the paper, water is washed in blue-grey,
 * each tree and boulder is an ink mark where it actually stands, and every
 * wall and house is its own footprint. Drawn once per zone, then kept. */

const cache = new Map<string, { url: string; extent: number }>();

function hash(x: number, y: number) {
  const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return s - Math.floor(s);
}

export function mapImage(z: ZoneBuild): { url: string; extent: number } {
  const hit = cache.get(z.id);
  if (hit) return hit;
  const extent = z.map?.extent ?? z.collision.bound * 2;
  const W = 900, G = 300; // canvas pixels; sample grid
  const cv = document.createElement('canvas');
  cv.width = W; cv.height = W;
  const g = cv.getContext('2d')!;
  const toPx = (v: number) => (v / extent + 0.5) * W;
  const at = (i: number, n: number) => (i / (n - 1) - 0.5) * extent;

  // Sample the ground.
  const h = new Float32Array(G * G);
  const tint = new Float32Array(G * G * 3);
  const wet = new Uint8Array(G * G);
  const paint: TerrainPaint = { dirt: 0, stone: 0, blight: 0, mud: 0 };
  let lo = Infinity, hi = -Infinity;
  for (let j = 0; j < G; j++) for (let i = 0; i < G; i++) {
    const x = at(i, G), zz = at(j, G), k = j * G + i;
    const y = z.terrain.heightAt(x, zz);
    h[k] = y; lo = Math.min(lo, y); hi = Math.max(hi, y);
    z.terrain.paintAt(x, zz, paint);
    // Paper, then what is on the ground.
    let r = 222, gg = 208, b = 172;
    const mix = (cr: number, cg: number, cb: number, a: number) => { r += (cr - r) * a; gg += (cg - gg) * a; b += (cb - b) * a; };
    mix(196, 196, 150, 0.35); // grass: a green wash
    mix(186, 150, 104, Math.min(1, paint.dirt * 1.2));
    mix(160, 154, 142, paint.stone);
    mix(140, 116, 84, paint.mud * 0.8);
    mix(150, 170, 90, paint.blight);
    tint[k * 3] = r; tint[k * 3 + 1] = gg; tint[k * 3 + 2] = b;
    wet[k] = z.map?.water?.(x, zz) ? 1 : 0;
  }
  // Paper texture.
  g.fillStyle = '#ddd0b0';
  g.fillRect(0, 0, W, W);
  const img = g.getImageData(0, 0, W, W);
  const d = img.data;
  const sample = (arr: Float32Array | Uint8Array, fx: number, fy: number, stride = 1, o = 0) => {
    const x = Math.max(0, Math.min(G - 1.001, fx)), y = Math.max(0, Math.min(G - 1.001, fy));
    const x0 = Math.floor(x), y0 = Math.floor(y), tx = x - x0, ty = y - y0;
    const a = arr[(y0 * G + x0) * stride + o], bb = arr[(y0 * G + x0 + 1) * stride + o];
    const c = arr[((y0 + 1) * G + x0) * stride + o], dd = arr[((y0 + 1) * G + x0 + 1) * stride + o];
    return (a * (1 - tx) + bb * tx) * (1 - ty) + (c * (1 - tx) + dd * tx) * ty;
  };
  const cell = extent / (G - 1);
  const contour = 1.5; // metres between lines
  for (let py = 0; py < W; py++) for (let px = 0; px < W; px++) {
    const fx = (px / W) * (G - 1), fy = (py / W) * (G - 1);
    const y = sample(h, fx, fy);
    // Hill shading, lit from the north-west.
    const dx = (sample(h, fx + 1, fy) - sample(h, fx - 1, fy)) / (2 * cell);
    const dz = (sample(h, fx, fy + 1) - sample(h, fx, fy - 1)) / (2 * cell);
    const shade = Math.max(0.55, Math.min(1.25, 1 + (-dx * 0.7 - dz * 0.7) * 0.55));
    let r = sample(tint, fx, fy, 3, 0), gg = sample(tint, fx, fy, 3, 1), b = sample(tint, fx, fy, 3, 2);
    // Water: a blue-grey wash, darker toward the middle.
    const w = sample(wet, fx, fy);
    if (w > 0.05) { const k = Math.min(1, w * 1.4); r += (118 - r) * k; gg += (146 - gg) * k; b += (150 - b) * k; }
    r *= shade; gg *= shade; b *= shade;
    // Contours: thin ink where the height crosses a line; every fifth heavier.
    const band = y / contour, next = sample(h, fx + 0.6, fy + 0.6) / contour;
    if (Math.floor(band) !== Math.floor(next) && w < 0.3) {
      const major = Math.floor(Math.max(band, next)) % 5 === 0;
      const k = major ? 0.42 : 0.2;
      r += (92 - r) * k; gg += (70 - gg) * k; b += (46 - b) * k;
    }
    // Grain of the paper.
    const n = (hash(px, py) - 0.5) * 14 + (hash(Math.floor(px / 7), Math.floor(py / 7)) - 0.5) * 10;
    const o = (py * W + px) * 4;
    d[o] = r + n; d[o + 1] = gg + n; d[o + 2] = b + n * 0.8; d[o + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  void lo; void hi;

  // Water's edge, inked.
  g.strokeStyle = 'rgba(52, 70, 78, 0.55)';
  g.lineWidth = 1.2;
  for (let j = 1; j < G - 1; j++) for (let i = 1; i < G - 1; i++) {
    const k = j * G + i;
    if (!wet[k]) continue;
    if (!wet[k - 1] || !wet[k + 1] || !wet[k - G] || !wet[k + G]) {
      const px = (i / (G - 1)) * W, py = (j / (G - 1)) * W;
      g.beginPath(); g.arc(px, py, 0.9, 0, Math.PI * 2); g.stroke();
    }
  }

  // Walls and houses: every solid box, as a footprint.
  for (const c of z.collision.all()) {
    if (c.kind !== 'box' || c.playerOnly || c.hw * c.hd < 0.6) continue;
    const s = W / extent;
    g.save();
    g.translate(toPx(c.x), toPx(c.z));
    g.rotate(-c.rot);
    g.fillStyle = c.soft ? 'rgba(110, 86, 58, 0.35)' : 'rgba(84, 60, 40, 0.8)';
    g.fillRect(-c.hw * s, -c.hd * s, c.hw * 2 * s, c.hd * 2 * s);
    g.strokeStyle = 'rgba(48, 32, 20, 0.9)';
    g.lineWidth = 1;
    g.strokeRect(-c.hw * s, -c.hd * s, c.hw * 2 * s, c.hd * 2 * s);
    g.restore();
  }

  // Houses: hexagons, roofed in two tones, with a shadow to the south-east.
  for (const bld of z.map?.buildings ?? []) {
    const px = toPx(bld.x), py = toPx(bld.z), r = bld.r * (W / extent);
    const hex = (ox: number, oy: number, rr: number) => {
      g.beginPath();
      for (let a = 0; a < 6; a++) {
        const t = bld.rot + a * Math.PI / 3 + Math.PI / 6;
        const x = px + ox + Math.cos(t) * rr, y = py + oy + Math.sin(t) * rr;
        a === 0 ? g.moveTo(x, y) : g.lineTo(x, y);
      }
      g.closePath();
    };
    hex(r * 0.18, r * 0.22, r); g.fillStyle = 'rgba(60, 40, 22, 0.35)'; g.fill();
    hex(0, 0, r); g.fillStyle = 'rgba(128, 74, 52, 0.95)'; g.fill();
    g.lineWidth = 1.4; g.strokeStyle = 'rgba(46, 28, 16, 0.95)'; g.stroke();
    hex(0, 0, r * 0.55); g.fillStyle = 'rgba(160, 100, 72, 0.9)'; g.fill();
    g.lineWidth = 0.8; g.stroke();
  }

  // Trees and rocks, one ink mark each.
  const s = W / extent;
  for (const [kind, x, zz, sc] of z.map?.flora ?? []) {
    const px = toPx(x), py = toPx(zz);
    if (px < -4 || py < -4 || px > W + 4 || py > W + 4) continue;
    const jit = hash(x, zz);
    g.lineWidth = 1;
    if (kind === 'pine') {
      const r = 2.2 * sc * s;
      g.fillStyle = `rgba(${70 + jit * 20}, ${88 + jit * 16}, 62, 0.85)`;
      g.strokeStyle = 'rgba(38, 44, 30, 0.9)';
      g.beginPath(); g.moveTo(px, py - r * 1.3); g.lineTo(px + r * 0.8, py + r * 0.7); g.lineTo(px - r * 0.8, py + r * 0.7); g.closePath();
      g.fill(); g.stroke();
    } else if (kind === 'broadleaf' || kind === 'autumn' || kind === 'sick') {
      const r = 2.6 * sc * s;
      g.fillStyle = kind === 'autumn' ? `rgba(${176 + jit * 30}, ${110 + jit * 30}, 60, 0.8)` : kind === 'sick' ? 'rgba(140, 150, 90, 0.8)' : `rgba(${96 + jit * 20}, ${122 + jit * 20}, 70, 0.8)`;
      g.strokeStyle = 'rgba(46, 44, 28, 0.85)';
      g.beginPath();
      for (let a = 0; a <= 7; a++) {
        const t = (a / 7) * Math.PI * 2, rr = r * (0.82 + hash(x + a, zz) * 0.3);
        a === 0 ? g.moveTo(px + Math.cos(t) * rr, py + Math.sin(t) * rr) : g.lineTo(px + Math.cos(t) * rr, py + Math.sin(t) * rr);
      }
      g.closePath(); g.fill(); g.stroke();
    } else if (kind === 'dead') {
      const r = 1.8 * sc * s;
      g.strokeStyle = 'rgba(60, 44, 30, 0.85)';
      g.beginPath(); g.moveTo(px, py + r); g.lineTo(px, py - r * 0.2); g.lineTo(px - r * 0.6, py - r); g.moveTo(px, py - r * 0.2); g.lineTo(px + r * 0.6, py - r * 0.9); g.stroke();
    } else {
      const r = (kind === 'cliff' ? 4 : 2.2) * sc * s;
      g.fillStyle = 'rgba(150, 144, 130, 0.8)';
      g.strokeStyle = 'rgba(60, 56, 48, 0.9)';
      g.beginPath();
      for (let a = 0; a <= 6; a++) {
        const t = (a / 6) * Math.PI * 2 + jit, rr = r * (0.7 + hash(x, zz + a) * 0.4);
        a === 0 ? g.moveTo(px + Math.cos(t) * rr, py + Math.sin(t) * rr) : g.lineTo(px + Math.cos(t) * rr, py + Math.sin(t) * rr);
      }
      g.closePath(); g.fill(); g.stroke();
    }
  }

  // Age: darker, foxed edges.
  const vg = g.createRadialGradient(W / 2, W / 2, W * 0.3, W / 2, W / 2, W * 0.72);
  vg.addColorStop(0, 'rgba(80, 50, 20, 0)');
  vg.addColorStop(1, 'rgba(70, 40, 14, 0.5)');
  g.fillStyle = vg;
  g.fillRect(0, 0, W, W);
  for (let i = 0; i < 40; i++) {
    const x = hash(i, 3) * W, y = hash(i, 7) * W, r = 8 + hash(i, 11) * 40;
    const fg = g.createRadialGradient(x, y, 0, x, y, r);
    fg.addColorStop(0, 'rgba(120, 80, 30, 0.08)');
    fg.addColorStop(1, 'rgba(120, 80, 30, 0)');
    g.fillStyle = fg;
    g.fillRect(x - r, y - r, r * 2, r * 2);
  }
  const out = { url: cv.toDataURL('image/jpeg', 0.9), extent };
  cache.set(z.id, out);
  return out;
}

/** The fog over what has not been walked: paper, with holes where you went. */
export function fogImage(seen: string, n: number, W = 900): string {
  const cv = document.createElement('canvas');
  cv.width = W; cv.height = W;
  const g = cv.getContext('2d')!;
  g.fillStyle = '#d9cba8';
  g.fillRect(0, 0, W, W);
  // Blank parchment has its own faint grain.
  for (let i = 0; i < 900; i++) {
    g.fillStyle = `rgba(120, 90, 50, ${0.03 + hash(i, 1) * 0.05})`;
    g.fillRect(hash(i, 2) * W, hash(i, 3) * W, 1 + hash(i, 4) * 3, 1 + hash(i, 5) * 3);
  }
  g.globalCompositeOperation = 'destination-out';
  const c = W / n;
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    if (seen[j * n + i] !== '1') continue;
    const x = (i + 0.5) * c, y = (j + 0.5) * c, r = c * 1.35;
    const rg = g.createRadialGradient(x, y, r * 0.3, x, y, r);
    rg.addColorStop(0, 'rgba(0,0,0,1)');
    rg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = rg;
    g.fillRect(x - r, y - r, r * 2, r * 2);
  }
  return cv.toDataURL('image/png');
}
