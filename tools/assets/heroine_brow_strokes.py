"""Her own face's brows painted again as grown hairs (face 40, 22 October 2026).

A max judge at the creation Look (face 39 eyes j1): on fair skin her screen-left brow's strokes crossed each other in a
lattice, evenly spaced and hard-edged, and read as hatching, painted on (the owner's "read as drawn on"). Her brows are
not cards: they are painted in her face's paint (head_tex/heroine_head.jpg, which the game lays over heroine.glb's own
older copy: People.HeadPaintFile), and the dye pass (heroine_paint.gdshader, paint/brows.png) recolours whatever is
painted darker than her skin there.

Per brow (the two big pieces of brows.png's mask over her face, at the paint's size):
  1. its shape: the old hairs (texels darker than the skin round them, dense, closed), so the brow keeps its outline,
     place, thickness;
  2. its frame: the shape's long axis, a bent spine along it, the head (the inner end: the two brows' nearest ends),
     the up side (the arch's bulge), the lower and upper edge along it;
  3. the old hairs taken out: inside the shape (and its stray hairs), the paint's broad colour filled smoothly from
     the skin round it, and the skin's pores and grain carried over from the skin just above the brow;
  4. a faint soft tint under the hairs, densest in the middle;
  5. hairs, each a streamline of one smooth field (so none cross): rising RISE[0] deg off the spine at the head, about
     RISE[3]-RISE[4] through the middle, falling at the tail, the lower ones a little steeper than the upper; dense in
     the middle, sparse at both ends; roots at an irregular spacing; each tapered from root to tip, its width and
     darkness its own (some fine); a seed per brow, so they mirror in shape, not stroke for stroke;
  6. their darkness over the brow matched to the old hairs' (the dye pass's mask measures texels darker than the
     skin), by one gain on every hair.
The paint is written again at the chain's 95, 4:4:4, with a JPEG comment MARK as its done-mark: a marked paint is
skipped. After it: python tools/assets/heroine_browdye.py (Own's brows.png's core and skin from the new paint).

    python tools/assets/heroine_brow_strokes.py [art dir]                 (in place; skips a marked paint)
    python tools/assets/heroine_brow_strokes.py --out PATH [--tex PATH]   (to another file; --tex a 2x crop of the
                                                                            brows before | after, to look at)
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage, sparse
from scipy.sparse.linalg import spsolve

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MARK = "brow_strokes"
SEED = 4040
PAD = 70                  # (texels round each brow's mask: the work's crop)
HAIR = (15, 75, 0.045)    # (an old hair: this share darker than the skin, the skin the 75th percentile of a 15 window)
SHAPE = (0.1, 3.0, 0.35, 2)  # (the brow's shape: old hairs this share darker, their density blur, its floor, closing)
FILL = (1.5, 3, 2.5)      # (the fill: broad colour's blur, the hole widened by, the grain's high-pass)
RISE = (84, 74, 52, 32, 24, 17, 4, -14)  # (deg off the spine, toward up, at t = KNOTS: head to tail)
KNOTS = (0.0, 0.08, 0.18, 0.3, 0.48, 0.7, 0.86, 1.0)
ROW = 7.0                 # (deg: the lower hairs this much steeper, the upper this much flatter)
WOBBLE = (4.0, 9.0)       # (deg, texels: a smooth noise on the field's angle, its scale: never crossing)
LEN = (0.6, 1.15)        # (a hair's length, of the brow's middle thickness: head, middle; the tail between)
WIDTH = (0.8, 2.0, 0.3)   # (root width texels: fine, full; the share of fine hairs)
SPACE = (3.7, 7.5)        # (texels between roots: middle, ends)
TINT = 0.17               # (the soft tint under the hairs at the middle)


def luma(p):
    return p @ np.array([0.3, 0.59, 0.11], np.float32)


def comment(path):
    try:
        return (Image.open(path).info.get("comment") or b"").decode("latin-1")
    except OSError:
        return ""


def brows_boxes(alpha, size):
    """The two brows in brows.png's mask (over her face: below row 1400 of 2048 is her body's paint), at size."""
    k = size / alpha.shape[0]
    a = alpha > 128
    a[int(1400 * alpha.shape[0] / 2048):] = False
    lab, n = ndimage.label(a)
    sz = ndimage.sum(a, lab, range(1, n + 1))
    keep = [i + 1 for i in np.argsort(sz)[::-1][:2]]
    out = []
    for i in keep:
        ys, xs = np.where(lab == i)
        y0, y1 = int(ys.min() * k) - PAD, int((ys.max() + 1) * k) + PAD
        x0, x1 = int(xs.min() * k) - PAD, int((xs.max() + 1) * k) + PAD
        zone = np.asarray(Image.fromarray(((lab == i) * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR))
        out.append(((y0, y1, x0, x1), zone[y0:y1, x0:x1] > 64))
    return out


def old_hairs(L, zone):
    """Old hairs (0/1) and their darkness against the skin round them (0-1)."""
    sk = ndimage.gaussian_filter(ndimage.percentile_filter(L, HAIR[1], size=HAIR[0]), 2)
    d = np.clip((sk - L) / np.maximum(sk, 1), 0, 1)
    near = ndimage.binary_dilation(zone, iterations=12)
    return (d > HAIR[2]) & near, d


def shape_of(d, zone):
    hh = (d > SHAPE[0]) & ndimage.binary_dilation(zone, iterations=4)
    den = ndimage.gaussian_filter(hh.astype(np.float32), SHAPE[1])
    m = den > SHAPE[2]
    lab, n = ndimage.label(m)
    m = lab == (1 + np.argmax(ndimage.sum(m, lab, range(1, n + 1))))
    m = ndimage.binary_closing(m, iterations=SHAPE[3])
    return ndimage.binary_fill_holes(m)


class Frame:
    """A brow's frame in its crop: u along its long axis, w across; spine w = c(u); t 0 head .. 1 tail; v up."""

    def __init__(self, S):
        ys, xs = np.where(S)
        P = np.stack([xs, ys], 1).astype(np.float64)
        self.m = P.mean(0)
        _, _, vt = np.linalg.svd(P - self.m, full_matrices=False)
        self.e1, self.e2 = vt[0], np.array([-vt[0][1], vt[0][0]])
        u, w = (P - self.m) @ self.e1, (P - self.m) @ self.e2
        self.c = np.polyfit(u, w, 2)
        self.u0, self.u1 = np.percentile(u, 0.3), np.percentile(u, 99.7)
        mid = np.polyval(self.c, (self.u0 + self.u1) / 2) - (np.polyval(self.c, self.u0) + np.polyval(self.c, self.u1)) / 2
        self.up = 1.0 if mid > 0 else -1.0          # (the arch bulges up)
        self.tail = 1.0                              # (set by the caller: +1 the tail at u1)
        # its lower and upper edge (v) along u
        v = self.up * (w - np.polyval(self.c, u))
        self.ub = np.linspace(self.u0, self.u1, 25)
        lo, hi = [], []
        for a, b in zip(self.ub[:-1], self.ub[1:]):
            s = v[(u >= a) & (u < b)]
            lo.append(np.percentile(s, 4) if len(s) > 5 else 0)
            hi.append(np.percentile(s, 96) if len(s) > 5 else 0)
        self.ubc = (self.ub[:-1] + self.ub[1:]) / 2
        self.lo = ndimage.gaussian_filter1d(np.array(lo), 1.2, mode="nearest")
        self.hi = ndimage.gaussian_filter1d(np.array(hi), 1.2, mode="nearest")

    def ends(self, off):
        return [off + self.m + u * self.e1 + np.polyval(self.c, u) * self.e2 for u in (self.u0, self.u1)]

    def t(self, u):
        t = (u - self.u0) / (self.u1 - self.u0)
        return t if self.tail > 0 else 1 - t

    def edges(self, u):
        return np.interp(u, self.ubc, self.lo), np.interp(u, self.ubc, self.hi)

    def xy(self, u, v):
        w = np.polyval(self.c, u) + self.up * v
        return self.m + np.outer(u, self.e1) + np.outer(w, self.e2) if np.ndim(u) else self.m + u * self.e1 + w * self.e2

    def uv(self, x, y):
        d = np.stack([x, y], -1) - self.m
        u = d @ self.e1
        return u, self.up * (d @ self.e2 - np.polyval(self.c, u))


def harmonic(img, hole):
    """img with the hole filled smoothly from round it (Laplace, per channel)."""
    idx = -np.ones(hole.shape, np.int64)
    ys, xs = np.where(hole)
    idx[ys, xs] = np.arange(len(ys))
    n = len(ys)
    rows, cols, vals = [], [], []
    b = np.zeros((n, img.shape[2]))
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        y2, x2 = ys + dy, xs + dx
        j = idx[y2, x2]
        inside = j >= 0
        rows += [np.arange(n)[inside]]
        cols += [j[inside]]
        vals += [-np.ones(inside.sum())]
        b[~inside] += img[y2[~inside], x2[~inside]]
    A = sparse.csr_matrix((np.concatenate(vals + [np.full(n, 4.0)]),
                           (np.concatenate(rows + [np.arange(n)]), np.concatenate(cols + [np.arange(n)]))), (n, n))
    out = img.copy()
    out[ys, xs] = spsolve(A.tocsc(), b)
    return out


def field_angle(F, u, v, wob, off):
    t = np.clip(F.t(u), 0, 1)
    lo, hi = F.edges(u)
    vn = np.clip((v - (lo + hi) / 2) / np.maximum((hi - lo) / 2, 1), -1.2, 1.2)
    ang = np.interp(t, KNOTS, RISE) - ROW * vn
    x, y = F.xy(u, v) if np.ndim(u) == 0 else (None, None)
    if x is not None:
        yi, xi = int(np.clip(y, 0, wob.shape[0] - 1)), int(np.clip(x, 0, wob.shape[1] - 1))
        ang = ang + wob[yi, xi]
    return np.radians(ang)


def hair_path(F, u, v, length, wob):
    """A hair from its root (u, v): a streamline of the field, 1 texel a step, in the crop's x, y."""
    pts = []
    for _ in range(int(length) + 1):
        x, y = F.xy(u, v)
        pts.append((x, y))
        a = field_angle(F, u, v, wob, None)
        # the spine's own slope at u (the field is off the spine, in u, v; v is across, not bent)
        du = F.tail * np.cos(a)
        dv = np.sin(a)
        slope = np.polyval(np.polyder(F.c), u)
        k = 1 / np.sqrt(1 + slope * slope)
        u, v = u + du * k, v + dv
    return np.array(pts)


def draw(shape, path, w0, alpha):
    """A tapered hair's coverage (0-1) over the crop, antialiased; the root softly in."""
    out = np.zeros(shape, np.float32)
    x0, y0 = np.floor(path.min(0) - 3).astype(int)
    x1, y1 = np.ceil(path.max(0) + 3).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, shape[1]), min(y1, shape[0])
    if x1 <= x0 or y1 <= y0:
        return out
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32) + 0.5
    n = len(path)
    s = np.linspace(0, 1, n)
    wid = w0 * (1 - 0.85 * s ** 1.4)
    op = alpha * np.clip(s / 0.12, 0.35, 1) * (1 - 0.35 * s ** 2)
    best = np.zeros(gx.shape, np.float32)
    for i in range(n - 1):
        a, b = path[i], path[i + 1]
        d = b - a
        L2 = max(d @ d, 1e-6)
        h = np.clip(((gx - a[0]) * d[0] + (gy - a[1]) * d[1]) / L2, 0, 1)
        dist = np.hypot(gx - a[0] - h * d[0], gy - a[1] - h * d[1])
        w = wid[i] + h * (wid[i + 1] - wid[i])
        o = op[i] + h * (op[i + 1] - op[i])
        cov = np.minimum(w, 1) * np.clip(np.maximum(w, 1) / 2 + 0.5 - dist, 0, 1) * o
        best = np.maximum(best, cov)
    out[y0:y1, x0:x1] = best
    return out


def hairs(F, S, rng, crop_shape):
    """The hairs' roots, lengths, widths and darkness: dense in the middle, sparse at the ends, irregular."""
    lo, hi = F.edges(F.ubc)
    thick = float(np.median((hi - lo)[len(lo) // 3: 2 * len(lo) // 3]))
    wob = ndimage.gaussian_filter(rng.standard_normal(crop_shape), WOBBLE[1])
    wob *= WOBBLE[0] / max(wob.std(), 1e-6)
    cand = []
    for _ in range(9000):
        u = rng.uniform(F.u0, F.u1)
        l, h = F.edges(u)
        cand.append((u, rng.uniform(l - 1, h)))
    cand = np.array(cand)
    t = F.t(cand[:, 0])
    dens = np.interp(t, (0, 0.06, 0.2, 0.4, 0.6, 0.8, 0.95, 1), (0.08, 0.3, 0.75, 1, 1, 0.7, 0.3, 0.1))
    gap = SPACE[0] + (SPACE[1] - SPACE[0]) * (1 - dens)
    keep = []
    pts = []
    for i in rng.permutation(len(cand)):
        if rng.random() > dens[i] ** 0.6:
            continue
        x, y = F.xy(cand[i, 0], cand[i, 1])
        if pts:
            P = np.array(pts)
            if np.min(np.hypot(P[:, 0] - x, P[:, 1] - y)) < gap[i] * rng.uniform(0.8, 1.25):
                continue
        pts.append((x, y))
        keep.append(i)
    out = []
    for i in keep:
        u, v = cand[i]
        ti = float(np.clip(F.t(u), 0, 1))
        lm = LEN[0] + (LEN[1] - LEN[0]) * np.interp(ti, (0, 0.25, 0.6, 1), (0, 1, 1, 0.55))
        length = thick * lm * rng.uniform(0.55, 1.2)
        fine = rng.random() < WIDTH[2] + 0.3 * (1 - np.interp(ti, (0, 0.15, 0.8, 1), (0, 1, 1, 0)))
        w0 = rng.uniform(WIDTH[0], 1.2) if fine else rng.uniform(1.3, WIDTH[1])
        a = (0.5 + 0.5 * rng.beta(3, 1.6)) * (0.75 if fine else 1.0)
        out.append((u, v, length, w0, a, rng.uniform(0.72, 1.15)))
    return out, wob, thick


def brow(P, box, zone, seed, tail_sign, stats):
    y0, y1, x0, x1 = box
    C = P[y0:y1, x0:x1].astype(np.float64)
    L = luma(C)
    hair, d = old_hairs(L, zone)
    S = shape_of(d, zone)
    F = Frame(S)
    F.tail = tail_sign
    # the old hairs out: the brow's shape and its stray hairs, widened
    # (and the light specks the old paint left along its edge)
    near = ndimage.binary_dilation(S, iterations=14)
    specks = near & (L > ndimage.percentile_filter(L, 50, size=11) * 1.035)
    hole = ndimage.binary_dilation(S | ((hair | specks) & near), iterations=FILL[1])
    hole[:2] = hole[-2:] = False
    hole[:, :2] = hole[:, -2:] = False
    broad = np.stack([ndimage.gaussian_filter(C[..., k], FILL[0]) for k in range(3)], -1)
    filled = harmonic(broad, hole)
    hp = C - np.stack([ndimage.gaussian_filter(C[..., k], FILL[2]) for k in range(3)], -1)
    # the skin's grain from just above the brow (its hairs left out)
    lo, hi = F.edges(F.ubc)
    hy, hx = np.where(hole)
    _, hv = F.uv(hx.astype(np.float64), hy.astype(np.float64))
    shift = float(hv.max() - hv.min()) + 8         # (the whole hole's grain from past its upper edge)
    n = (F.xy(F.ubc[len(F.ubc) // 2], 1.0) - F.xy(F.ubc[len(F.ubc) // 2], 0.0))
    n = n / np.linalg.norm(n)
    dy, dx = n[1] * shift, n[0] * shift
    big = P.astype(np.float64)
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    src = np.stack([ndimage.map_coordinates(big[..., k], [gy + dy, gx + dx], order=1) for k in range(3)], -1)
    srcL = luma(src)
    sh, _ = old_hairs(srcL, np.ones_like(zone))
    shp = src - np.stack([ndimage.gaussian_filter(src[..., k], FILL[2]) for k in range(3)], -1)
    shp[ndimage.binary_dilation(sh, iterations=1)] *= 0.2
    lim = 2.5 * np.std(shp[hole])
    shp = np.clip(shp, -lim, lim)
    grain = np.std(hp[~hole & ~hair]) / max(np.std(shp[hole]), 1e-6)
    feather = np.clip(ndimage.gaussian_filter(hole.astype(np.float64), 1.2) * 1.6, 0, 1)[..., None]
    clean = C * (1 - feather) + (filled + shp * min(grain, 1.3)) * feather
    skinL = luma(filled)
    # its hair colour: the old hairs' darkest quarter
    dk = hair & (d > np.percentile(d[hair], 75))
    col = np.median(C[dk], 0)
    rng = np.random.default_rng(seed)
    hs, wob, thick = hairs(F, S, rng, L.shape)
    # (a hair fades out past the brow's outline, so the outline stays the old one's)
    env = np.clip(ndimage.gaussian_filter(ndimage.binary_dilation(S, iterations=2).astype(np.float64), 1.5) * 1.5, 0, 1)
    covs = []
    for u, v, length, w0, a, k in hs:
        covs.append((draw(L.shape, hair_path(F, u, v, length, wob), w0, a) * env, k))
    # the soft tint under them, densest in the middle
    gy2, gx2 = np.mgrid[0:L.shape[0], 0:L.shape[1]].astype(np.float64)
    uu, _ = F.uv(gx2, gy2)
    tt = np.clip(F.t(uu), 0, 1)
    tint = TINT * ndimage.gaussian_filter(S.astype(np.float64), 3.0) * np.interp(tt, (0, 0.2, 0.45, 0.7, 1), (0.25, 0.8, 1, 0.8, 0.3))
    old_dark = float(np.sum(np.clip((skinL - L) / skinL, 0, 1)[hole]))

    def render(g):
        out = clean * (1 - tint[..., None]) + col * tint[..., None]
        for cov, k in covs:
            a = np.clip(cov * g, 0, 0.97)[..., None]
            out = out * (1 - a) + col * k * a
        return out

    g = 1.0
    for _ in range(4):
        out = render(g)
        new_dark = float(np.sum(np.clip((skinL - luma(out)) / skinL, 0, 1)[hole]))
        g *= old_dark / max(new_dark, 1e-6)
        g = float(np.clip(g, 0.4, 2.2))
    out = render(g)
    new_dark = float(np.sum(np.clip((skinL - luma(out)) / skinL, 0, 1)[hole]))
    stats.append("brow box %s: %d hairs, thick %.1f, gain %.2f, darkness old %.0f new %.0f, colour %s"
                 % (box, len(hs), thick, g, old_dark, new_dark, np.round(col).astype(int).tolist()))
    return out


def main(a):
    art = next((x for x in a if not x.startswith("--") and a[a.index(x) - 1] not in ("--out", "--tex")), None) \
        if a else None
    art = art or os.path.join(ROOT, "godot", "art", "people")
    paint = os.path.join(art, "head_tex", "heroine_head.jpg")
    out_path = a[a.index("--out") + 1] if "--out" in a else paint
    if out_path == paint and MARK in comment(paint):
        print("BROW_STROKES: %s already marked, skipped" % paint)
        return
    P = np.asarray(Image.open(paint).convert("RGB")).astype(np.float64)
    alpha = np.asarray(Image.open(os.path.join(art, "paint", "brows.png")))[..., 3]
    boxes = brows_boxes(alpha, P.shape[0])
    # the heads: the two brows' nearest ends
    frames = []
    for box, zone in boxes:
        y0, y1, x0, x1 = box
        L = luma(P[y0:y1, x0:x1])
        _, d = old_hairs(L, zone)
        frames.append(Frame(shape_of(d, zone)).ends(np.array([x0, y0], float)))
    best = min(((i, j) for i in range(2) for j in range(2)),
               key=lambda ij: np.linalg.norm(frames[0][ij[0]] - frames[1][ij[1]]))
    tails = [1.0 if best[0] == 0 else -1.0, 1.0 if best[1] == 0 else -1.0]
    out = P.copy()
    stats = []
    for k, ((box, zone), ts) in enumerate(zip(boxes, tails)):
        y0, y1, x0, x1 = box
        out[y0:y1, x0:x1] = brow(P, box, zone, SEED + 17 * k, ts, stats)
    for s in stats:
        print("BROW_STROKES:", s)
    img = Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))
    img.save(out_path, quality=95, subsampling=0, comment=(comment(paint) + " " + MARK).strip().encode("latin-1"))
    print("BROW_STROKES: wrote", out_path)
    if "--tex" in a:
        rows = []
        for box, _ in boxes:
            y0, y1, x0, x1 = box
            pair = [np.asarray(Image.fromarray(np.clip(X[y0:y1, x0:x1], 0, 255).astype(np.uint8))
                               .resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.LANCZOS)) for X in (P, out)]
            rows.append(np.concatenate([pair[0], np.full((pair[0].shape[0], 8, 3), 255, np.uint8), pair[1]], 1))
        w = max(r.shape[1] for r in rows)
        rows = [np.pad(r, ((0, 8), (0, w - r.shape[1]), (0, 0)), constant_values=255) for r in rows]
        Image.fromarray(np.concatenate(rows, 0)).save(a[a.index("--tex") + 1])


if __name__ == "__main__":
    main(sys.argv[1:])
