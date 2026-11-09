"""The painted ground (L1 C1): every zone's and arena's ground layers painted from nothing, no photo or scan.

    python tools/look/ground_paint.py build SET|all [--twice]   -> each set's albedo.png, normal.png, arh.png (+ its manifest)
    python tools/look/ground_paint.py atlas                       -> the grass cards' atlas (godot/art/world/flora/grass_meadow_atlas.png)
    python tools/look/ground_paint.py check [SET|all] [--old]    -> the rule-9 numbers, the version stamp, the inputs hash

Reads godot/data/look/ground.json (sets: which surface each of a set's seven layers is, at how many metres a tile;
surfaces: each FROM its board or target). A surface is drawn at 2x and box-reduced to one 1K layer, tileable:
  masses   two or three value masses at three sizes (rule 10, big-medium-small; ground.json "mass_sizes"): big ones from a
           periodic noise at the surface's world scale (scale_m x big), islands a value up or down at the medium and
           small sizes, each one color with a slow +-0.02 L drift inside it (rule 9: one color varied inside its range);
  cells    chunky planes (setts, slabs, stones, rock): a periodic jittered Voronoi, each cell one color, a lit bevel on the
           light's side and a cool, darker bevel on the other, joints in a deeper tone (rule 9: warm tops, cool joints);
  stamps   big flat shapes: grass clumps (blade-cluster silhouettes, a cool dark underside, blades facing the light lit),
           needle tufts, leaves (two values, the lit half a step up), stones (a shade plane and a lit top plane), strokes
           (roots, ruts, cracks; an optional lit edge) and chips.
Each shape's color is one of its list, varied by at most spread_L (0.05 Oklab L, inside rule 9's +-0.06); nothing is drawn
under min_cm (3 cm). Heights (arh.b) are the shapes' (raised clumps, low ruts), so the shaders' height blend cuts layer
edges along the shapes; the normal map is the heights blurred at 2.5 cm (big forms only; the band sees none of it: cel_nmap 0).
Deterministic (seeded by set, layer and surface name); the manifest (ground.json for the terrain, layers.json for an arena)
carries VERSION and the inputs' hash, and `check` refuses a stale or hand-touched output.
"""
import hashlib, json, math, os, shutil, sys, tempfile, zlib

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from paint_core import srgb_to_lin, lin_to_srgb, lin_to_oklab, oklab_to_lin  # noqa: E402

DATA = os.path.join(ROOT, "godot", "data", "look", "ground.json")
VERSION = 2  # (bumped on any change to the painting: the manifests carry it, and the check refuses a stale one)
N = 1024     # a layer's side in the output
S = 2        # drawn at S x, box-reduced (the shapes' edges anti-aliased, never blurred)
FILES = ("albedo.png", "normal.png", "arh.png")


def seed_of(*k): return zlib.crc32(repr(k).encode()) & 0x7fffffff


def lab(h): return lin_to_oklab(srgb_to_lin(np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])))


def rgb8(o): return tuple(int(round(v * 255)) for v in lin_to_srgb(oklab_to_lin(np.asarray(o, float))))


def shift(h, dL, dh=0.0):
    """A color moved dL in Oklab L and turned dh radians, as an 8-bit sRGB tuple."""
    o = lab(h)
    a, b = o[1], o[2]
    c, s = math.cos(dh), math.sin(dh)
    return rgb8([o[0] + dL, a * c - b * s, a * s + b * c])


# ---- periodic fields -------------------------------------------------------------------------------------------------
def pnoise(n, f_lo, f_hi, rng):
    """A tileable noise (zero mean, unit spread) with frequencies f_lo..f_hi cycles per tile."""
    k = np.fft.fftfreq(n) * n
    K = np.sqrt(k[None, :] ** 2 + k[:, None] ** 2)
    band = (K >= f_lo) & (K <= f_hi)
    spec = (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))) * band / np.maximum(K, 1.0)
    f = np.fft.ifft2(spec).real
    return ((f - f.mean()) / (f.std() + 1e-9)).astype(np.float32)


def blur(x, sig):
    """A periodic Gaussian blur (sigma in px), by FFT."""
    n = x.shape[0]
    k = np.fft.fftfreq(n)
    g = np.exp(-2 * (math.pi * sig) ** 2 * (k[None, :] ** 2 + k[:, None] ** 2))
    return np.fft.ifft2(np.fft.fft2(x) * g).real.astype(np.float32)


# ---- the painter -----------------------------------------------------------------------------------------------------
class Canvas:
    def __init__(self, metres, light, spread):
        self.W = N * S
        self.ppm = self.W / metres
        self.metres = metres
        self.light = np.array(light, float) / np.linalg.norm(light)
        self.spread = spread
        self.col = np.zeros((self.W, self.W, 3), np.float32)
        self.hgt = np.zeros((self.W, self.W), np.float32)
        self.rough = np.full((self.W, self.W), 0.92, np.float32)

    def px(self, cm): return cm / 100.0 * self.ppm

    def begin_stamps(self):
        self.im = Image.fromarray(np.clip(self.col * 255 + 0.5, 0, 255).astype(np.uint8))
        self.hm = Image.fromarray(np.clip(self.hgt * 255 + 0.5, 0, 255).astype(np.uint8))
        self.dc, self.dh = ImageDraw.Draw(self.im), ImageDraw.Draw(self.hm)

    def end_stamps(self):
        self.col = np.asarray(self.im, np.float32) / 255
        self.hgt = np.asarray(self.hm, np.float32) / 255

    def _wrapped(self, pts):
        W = self.W
        lo, hi = pts.min(0), pts.max(0)
        for ox in (-W, 0, W):
            for oy in (-W, 0, W):
                if hi[0] + ox < 0 or lo[0] + ox > W or hi[1] + oy < 0 or lo[1] + oy > W:
                    continue
                yield [tuple(p) for p in (pts + (ox, oy))]

    def poly(self, pts, color, h):
        for q in self._wrapped(np.asarray(pts, float)):
            self.dc.polygon(q, fill=color)
            self.dh.polygon(q, fill=int(h * 255))

    def line(self, pts, width, color, h):
        for q in self._wrapped(np.asarray(pts, float)):
            self.dc.line(q, fill=color, width=max(int(round(width)), 1), joint="curve")
            self.dh.line(q, fill=int(h * 255), width=max(int(round(width)), 1), joint="curve")


def masses(cv, m, rng, sizes):
    """Big, medium and small masses (rule 10): the big ones a periodic noise at sizes' big x the surface's scale_m, cut at
    its split into the surface's colors; then islands of the next value up or down at the medium and the small size,
    each over its share of the tile (half up, half down), so a surface is never one size of camo blob (wave 2, 04/05)."""
    W, T = cv.W, cv.metres
    n = len(m["colors"])
    s0 = m["scale_m"]
    fb = max(T / (s0 * sizes["big"]), 1.0)
    field = pnoise(W, max(1.0, 0.7 * fb), 1.3 * fb, rng) + 0.15 * pnoise(W, 3 * fb, 6 * fb, rng)
    lvl = np.digitize(field, np.quantile(field, m["split"]))
    for k in ("medium", "small"):
        f = max(T / (s0 * sizes[k]), 1.0)
        g = pnoise(W, max(1.0, 0.7 * f), 1.3 * f, rng) + 0.15 * pnoise(W, 3 * f, 6 * f, rng)
        sh = sizes[k + "_share"] * 0.5
        up, dn = g > np.quantile(g, 1.0 - sh), g < np.quantile(g, sh)
        lvl = np.where(up, np.minimum(lvl + 1, n - 1), np.where(dn, np.maximum(lvl - 1, 0), lvl))
    drift = pnoise(W, max(1.0, 0.5 * fb), fb, rng) * 0.02 / 2.5  # (+-0.02 L inside a mass, at the big scale)
    labs = np.array([lab(c) for c in m["colors"]])
    o = labs[lvl]
    o[..., 0] += np.clip(drift, -0.02, 0.02)
    cv.col = lin_to_srgb(oklab_to_lin(o.reshape(-1, 3))).reshape(W, W, 3).astype(np.float32)
    cv.hgt = (0.3 + 0.12 * lvl / max(n - 1, 1)).astype(np.float32)


def cells(cv, c, rng, patches=None):
    """Chunky planes: a periodic jittered Voronoi, one color a cell, a lit and a cool bevel, joints deeper."""
    W = cv.W
    g = max(int(round(cv.metres * 100 / c["size_cm"])), 2)
    cs = W / g
    jit = rng.uniform(0.18, 0.82, (g, g, 2))
    cid_h = rng.random((g, g))
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float32)
    gx, gy = (xx // cs).astype(int), (yy // cs).astype(int)
    F1 = np.full((W, W), 1e9, np.float32); F2 = F1.copy()
    best = np.zeros((W, W, 2), np.float32); bid = np.zeros((W, W), np.int64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx, cy = gx + dx, gy + dy
            ix, iy = cx % g, cy % g
            px_ = (cx + jit[iy, ix, 0]) * cs
            py_ = (cy + jit[iy, ix, 1]) * cs
            d = np.hypot(xx - px_, yy - py_)
            closer = d < F1
            F2 = np.where(closer, F1, np.minimum(F2, d))
            F1 = np.where(closer, d, F1)
            best[..., 0] = np.where(closer, xx - px_, best[..., 0])
            best[..., 1] = np.where(closer, yy - py_, best[..., 1])
            bid = np.where(closer, iy * g + ix, bid)
    edge = (F2 - F1) * 0.5
    joint = cv.px(c["joint_cm"]) * 0.5
    stone = edge > joint
    if c.get("round", 0) > 0:
        stone &= F1 < cs * (0.78 - 0.3 * c["round"])
    bevel = max(cv.px(3.0), 0.16 * cs)
    rim = stone & (edge < joint + bevel)
    rad = F1 < cs * (0.78 - 0.3 * c.get("round", 0)) - bevel if c.get("round", 0) > 0 else np.zeros_like(stone)
    if c.get("round", 0) > 0:
        rim = stone & ((edge < joint + bevel) | ~rad)
    dirn = best / np.maximum(F1[..., None], 1e-3)
    facing = dirn[..., 0] * cv.light[0] + dirn[..., 1] * cv.light[1]
    labs = np.array([lab(h) for h in c["colors"]])
    ncol = len(c["colors"])
    hsh = cid_h.reshape(-1)[bid]
    pick = np.minimum((hsh * ncol).astype(int), ncol - 1)
    o = labs[pick].copy()
    o[..., 0] += (np.modf(hsh * 7.31)[0] - 0.5) * 2 * cv.spread * 0.8
    lit = c.get("lit", 0.05)
    o[..., 0] += np.where(rim & (facing > 0.25), lit, 0.0)
    cool = rim & (facing < -0.25)
    o[..., 0] -= np.where(cool, lit * 0.8, 0.0)
    o[..., 2] -= np.where(cool, 0.008, 0.0)  # (the cool side a touch bluer: rule 9's cool cavity)
    if patches:
        pf = pnoise(W, max(1.0, 0.6 * cv.metres / patches["scale_m"]), 1.5 * cv.metres / patches["scale_m"], rng)
        moss = stone & (pf > np.quantile(pf, 1 - patches["share"])) & (facing > -0.5)
        plab = np.array([lab(h) for h in patches["colors"]])
        o = np.where(moss[..., None], plab[(hsh > 0.5).astype(int)], o)
    rgb = lin_to_srgb(oklab_to_lin(o.reshape(-1, 3))).reshape(W, W, 3).astype(np.float32)
    jcol = np.array(rgb8(lab(c["joint"])), np.float32) / 255
    isjoint = (edge <= joint) & (c.get("round", 0) == 0)
    cv.col = np.where(stone[..., None], rgb, np.where(isjoint[..., None], jcol, cv.col))
    h = 0.5 + 0.5 * np.clip((edge - joint) / bevel, 0, 1)
    cv.hgt = np.where(stone, h, np.where(isjoint, 0.15, cv.hgt)).astype(np.float32)
    cv.rough = np.where(stone, 0.85, cv.rough).astype(np.float32)


def courses(cv, c, rng):
    """(L1 W2 town) Coursed setts: rows of rounded-rectangle stones in a running bond (MB3 SETTS: chunky planes, warm
    tops, cool joints; rule 10: big-medium-small as the stones, their bevels and the joints), wrapped so the tile repeats.
    Each stone one color of its list (+-spread), its top a slightly tilted plane (+-tilt of the spread across it), a lit
    bevel on the light's side and a cool, darker one on the other, the joints one deep cool tone; every size >= 3 cm."""
    W = cv.W
    nr = max(int(round(cv.metres * 100 / c["row_cm"])), 1)
    rh = rng.uniform(1 - c["row_jit"], 1 + c["row_jit"], nr); rb = np.concatenate([[0], np.cumsum(rh / rh.sum() * W)])
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float32)
    row = np.clip(np.searchsorted(rb, yy, side="right") - 1, 0, nr - 1)
    y0, y1 = rb[row], rb[row + 1]
    nst = max(int(round(cv.metres * 100 / c["len_cm"])), 1)
    sid = np.zeros((W, W), np.int64); x0 = np.zeros((W, W), np.float32); x1 = np.zeros((W, W), np.float32)
    for r in range(nr):
        ln = rng.uniform(1 - c["len_jit"], 1 + c["len_jit"], nst); cb = np.concatenate([[0], np.cumsum(ln / ln.sum() * W)])
        off = (0.5 * (r % 2) + rng.uniform(-0.2, 0.2)) * W / nst
        k = row == r
        lx = (xx[k] - off) % W
        j = np.clip(np.searchsorted(cb, lx, side="right") - 1, 0, nst - 1)
        sid[k] = r * nst + j; x0[k] = cb[j] + off; x1[k] = cb[j + 1] + off
        xx_k = xx[k]; xx_k = np.where(xx_k < x0[k], xx_k + W, xx_k); xx_k = np.where(xx_k >= x1[k], xx_k - W, xx_k)
        xx[k] = xx_k
    cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    hx, hy = (x1 - x0) * 0.5, (y1 - y0) * 0.5
    px, py = xx - cx, yy - cy
    jh, rad = cv.px(c["joint_cm"]) * 0.5, cv.px(c["corner_cm"])
    # (each stone's outline wobbles a little, at the stone's own scale: a periodic noise, +-wobble_cm)
    wob = pnoise(W, max(1.0, cv.metres * 100 / c["len_cm"] * 0.7), cv.metres * 100 / c["len_cm"] * 2.0, rng)
    wob = (wob - wob.mean()) / (wob.std() + 1e-6) * cv.px(c["wobble_cm"]) * 0.5
    qx, qy = np.abs(px) - (hx - jh - rad), np.abs(py) - (hy - jh - rad)
    d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rad + wob
    stone = d < 0
    e = -d
    bevel = cv.px(c["bevel_cm"])
    gy, gx = np.gradient(d)
    gl = np.maximum(np.hypot(gx, gy), 1e-6)
    facing = -(gx / gl * cv.light[0] + gy / gl * cv.light[1])  # (the bevel's outward normal toward the light: lit)
    labs = np.array([lab(h) for h in c["colors"]])
    h = rng.random(nr * nst)
    pick = np.minimum((h * len(labs)).astype(int), len(labs) - 1)
    o = labs[pick][sid].copy()
    # ('spread' (L1 l9 kit): the class's own +-L between stones, over ground.json's spread_L: MB3's setts are quiet)
    sp = c.get("spread", cv.spread)
    o[..., 0] += ((np.modf(h * 7.31)[0] - 0.5) * 2 * sp * 0.9)[sid]
    tilt = rng.uniform(-1, 1, (nr * nst, 2))
    o[..., 0] += (tilt[sid, 0] * px / np.maximum(hx, 1) + tilt[sid, 1] * py / np.maximum(hy, 1)) * sp * c["tilt"]
    rim = stone & (e < bevel)
    lit = c["lit"]
    w = 1 - np.clip(e / bevel, 0, 1)
    o[..., 0] += np.where(rim & (facing > 0.2), lit * smoothstep01(facing) * np.sqrt(w), 0.0)
    cool = rim & (facing < -0.2)
    o[..., 0] -= np.where(cool, lit * 0.8 * smoothstep01(-facing) * np.sqrt(w), 0.0)
    o[..., 2] -= np.where(cool, 0.012, 0.0)
    rgb = lin_to_srgb(oklab_to_lin(o.reshape(-1, 3))).reshape(W, W, 3).astype(np.float32)
    jcol = np.array(rgb8(lab(c["joint"])), np.float32) / 255
    cv.col = np.where(stone[..., None], rgb, jcol)
    cv.hgt = np.where(stone, 0.55 + 0.45 * (1 - w ** 2), 0.12).astype(np.float32)
    cv.rough = np.where(stone, 0.85, 0.95).astype(np.float32)


def smoothstep01(x):
    t = np.clip((x - 0.2) / 0.6, 0, 1); return t * t * (3 - 2 * t)


def rot(pts, a, c):
    ca, sa = math.cos(a), math.sin(a)
    p = np.asarray(pts, float)
    return np.stack([p[:, 0] * ca - p[:, 1] * sa, p[:, 0] * sa + p[:, 1] * ca], 1) + c


def stamp_colors(cv, st, rng):
    h = st["colors"][rng.integers(len(st["colors"]))]
    return h, rng.uniform(-1, 1) * cv.spread * 0.8


def fan_leaf(c, ang, ln, w, L, perp, curl):
    """A broad pointed leaf on the ground, from c, at ang radians off the light's direction (L, the picture's up)."""
    d = L * math.cos(ang) + perp * math.sin(ang)
    n_ = np.array([-d[1], d[0]])
    t = np.linspace(0, 1, 9)[:, None]
    spine = c + d * ln * t + n_ * curl * ln * t ** 2
    wd = w * np.sin(np.clip(t * 0.9 + 0.1, 0, 1) * math.pi) ** 0.7 * (1 - t) ** 0.25
    return np.concatenate([spine + n_ * wd, (spine - n_ * wd)[::-1]])


def mound_fan(cv, c, r, rng, L, nl, spread, reach, wide, color, h):
    """A fan of nl broad pointed leaves from c toward the light, over a rounded foot, as one flat color."""
    perp = np.array([-L[1], L[0]])
    k = 16
    ang = np.linspace(0, 2 * math.pi, k, endpoint=False)
    jit = rng.uniform(0.85, 1.1, k)
    foot = [c + perp * math.cos(a_) * r * 0.62 * j + L * math.sin(a_) * r * 0.42 * j for a_, j in zip(ang, jit)]
    cv.poly(foot, color, h)
    for i in range(nl):
        u = (i + rng.uniform(0.25, 0.75)) / nl * 2 - 1
        a_ = u * spread + rng.uniform(-0.08, 0.08)
        ln = r * reach * rng.uniform(0.75, 1.0) * (1 - 0.3 * u * u)
        root = c + perp * u * r * 0.35
        cv.poly(fan_leaf(root, a_, ln, r * wide * rng.uniform(0.85, 1.15), L, perp, rng.uniform(-0.15, 0.15)), color, h)


def mounds(cv, st, rng):
    """Grass as big flat clumps (bible rule 9, MB4 grass, target 07's lawn): each mound three flat values, a cool dark
    under-mass dropped away from the light, the body, and a lit spiky crown toward the light, overlapping like scales
    (the ones toward the light drawn first, so a nearer mound's lit crown covers the dark foot of the one behind)."""
    T = cv.metres
    count = int(round(st["per_m2"] * T * T))
    lo, hi = st["size_cm"]
    L = cv.light
    cols = st["colors"]  # [under, body, lit]
    ms = []
    for _ in range(count):
        c = rng.uniform(0, cv.W, 2)
        r = cv.px(max(rng.uniform(lo, hi), 3.0)) * 0.5
        ms.append((float(c @ L) % (cv.W * abs(L[1]) + 1e-6), c, r, rng.uniform(-1, 1) * cv.spread * 0.8, rng.integers(1 << 30)))
    for _, c, r, dL, sd in sorted(ms, key=lambda m: -m[0]):
        g = np.random.default_rng(int(sd))
        nl = int(st.get("leaves", 7))
        # the dark under-mass, wider and dropped away from the light; the body; the lit crown toward the light
        mound_fan(cv, c - L * r * 0.22, r * 1.05, g, L, nl + 2, 1.6, 0.95, 0.2, shift(cols[0], dL * 0.5), st["height"] * 0.7)
        mound_fan(cv, c, r * 0.9, g, L, nl, 1.45, 1.0, 0.2, shift(cols[1], dL), st["height"] * 0.85)
        mound_fan(cv, c + L * r * 0.2, r * 0.7, g, L, max(nl - 2, 3), 1.2, 1.0, 0.2, shift(cols[2], dL), st["height"])


def stamps(cv, st, rng):
    if st["shape"] == "mound":
        return mounds(cv, st, rng)
    T = cv.metres
    count = int(round(st["per_m2"] * T * T))
    lo, hi = st["size_cm"]
    mn = cv.px(3.0)
    L = cv.light
    for _ in range(count):
        c = rng.uniform(0, cv.W, 2)
        size = cv.px(max(rng.uniform(lo, hi), 3.0))
        a = rng.uniform(0, 2 * math.pi)
        hx, dL = stamp_colors(cv, st, rng)
        sh = st["shape"]
        if sh in ("clump", "tuft"):
            r = size * 0.5
            nb = int(rng.integers(st["blades"][0], st["blades"][1] + 1))
            if "under" in st:
                cv.poly(rot([(math.cos(t) * r * 0.42, math.sin(t) * r * 0.42) for t in np.linspace(0, 2 * math.pi, 12, endpoint=False)], 0, c),
                        shift(st["under"], dL * 0.5), st["height"] * 0.6)
            curl = rng.choice([-1, 1]) * (0.18 if sh == "clump" else 0.04)
            blades = []
            for i in range(nb):
                ang = a + i * 2 * math.pi / nb + rng.uniform(-0.35, 0.35)
                ln = r * rng.uniform(0.6, 1.0)
                bw = max(mn * 0.5, (0.16 if sh == "clump" else 0.09) * r)
                d = np.array([math.cos(ang), math.sin(ang)]); n_ = np.array([-d[1], d[0]])
                face = float(d @ L)
                tip = d * ln + n_ * curl * ln
                mid = d * ln * 0.5 + n_ * curl * ln * 0.3
                pts = [n_ * bw, mid + n_ * bw * 0.7, tip, mid - n_ * bw * 0.7, -n_ * bw]
                blades.append((face, np.asarray(pts) + c))
            for face, pts in sorted(blades, key=lambda b: b[0]):
                lit = face > 0.15
                col = st["colors"][1 if lit and len(st["colors"]) > 1 else 0]
                cv.poly(pts, shift(col, dL + (0.02 if lit else -0.015)), st["height"] * (1.0 if lit else 0.9))
        elif sh == "leaf":
            ln, wd = size, size * 0.5
            t = np.linspace(0, 1, 10)
            up = np.stack([(t - 0.5) * ln, 0.5 * wd * np.sin(math.pi * t) ** 0.75], 1)
            dn = up[::-1] * (1, -1)
            pts = rot(np.concatenate([up, dn[1:-1]]), a, c)
            cv.poly(pts, shift(hx, dL), st["height"])
            n_ = np.array([-math.sin(a), math.cos(a)])
            half = up if float(n_ @ L) > 0 else up * (1, -1)
            mid = np.stack([(t[::-1] - 0.5) * ln, np.zeros_like(t)], 1)
            cv.poly(rot(np.concatenate([half, mid[1:-1]]), a, c), shift(hx, dL + 0.035), st["height"])
        elif sh == "stone":
            r = size * 0.5
            k = 14
            jit = rng.uniform(0.85, 1.12, k)
            jit = (jit + np.roll(jit, 1) + np.roll(jit, -1)) / 3
            ang = np.linspace(0, 2 * math.pi, k, endpoint=False)
            blob = np.stack([np.cos(ang) * jit * r, np.sin(ang) * jit * r * 0.8], 1)
            cv.poly(rot(blob, a, c), shift(hx, dL - 0.035, -0.05), st["height"] * 0.85)
            if r * 0.7 >= mn * 0.5:
                cv.poly(rot(blob * 0.68, a, c + L * r * 0.2), shift(hx, dL + 0.03), st["height"])
        elif sh == "stroke":
            w = size
            ln = cv.px(rng.uniform(*st["length_cm"]))
            ang = rng.uniform(-0.15, 0.15) if st.get("along") else a
            p = c.copy(); pts = [p.copy()]
            step = max(cv.px(10.0), w)
            for _ in range(max(int(ln / step), 2)):
                ang += rng.uniform(-0.2, 0.2)
                p = p + step * np.array([math.cos(ang), math.sin(ang)])
                pts.append(p.copy())
            cv.line(pts, w, shift(hx, dL), st["height"])
            if st.get("lit_edge"):
                lw = min(max(w * 0.45, mn), w * 0.8)
                off = L * (w - lw) * 0.5
                cv.line(np.asarray(pts) + off, lw, shift(hx, dL + st["lit_edge"]), st["height"])
        elif sh == "chip":
            ln, wd = size, max(size * 0.4, mn)
            pts = rot([(-ln / 2, -wd / 2), (ln / 2, -wd / 2 * 0.8), (ln / 2, wd / 2 * 0.8), (-ln / 2, wd / 2)], a, c)
            cv.poly(pts, shift(hx, dL), st["height"])
        else:
            raise ValueError(f"unknown shape {sh}")


def paint_surface(name, surf, metres, data, salt, variant=None):
    rng = np.random.default_rng(seed_of(salt, name, metres, VERSION) if variant is None else seed_of(salt, name, metres, VERSION, variant))
    cv = Canvas(metres, data["light"], data["spread_L"])
    if "masses" in surf:
        masses(cv, surf["masses"], rng, data["mass_sizes"])
    if "cells" in surf:
        cells(cv, surf["cells"], rng, surf.get("patches"))
    if "courses" in surf:
        courses(cv, surf["courses"], rng)
    if surf.get("stamps"):
        cv.begin_stamps()
        for st in surf["stamps"]:
            assert st["size_cm"][0] >= data["min_cm"], (name, "a shape under min_cm")
            stamps(cv, st, rng)
        cv.end_stamps()
    # (box-reduced: S x S pixels to one)
    col = cv.col.reshape(N, S, N, S, 3).mean((1, 3))
    hgt = cv.hgt.reshape(N, S, N, S).mean((1, 3))
    rough = cv.rough.reshape(N, S, N, S).mean((1, 3))
    ppm = N / metres
    hb = blur(hgt, 0.025 * ppm)
    amp = 0.03  # (height 1 = 3 cm: the clumps' and stones' relief, for the normal's big forms)
    du = (np.roll(hb, -1, 1) - np.roll(hb, 1, 1)) * 0.5 * amp * ppm
    dv = (np.roll(hb, -1, 0) - np.roll(hb, 1, 0)) * 0.5 * amp * ppm
    nrm = np.stack([-du, dv, np.ones_like(du)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    ao = np.clip(1.0 - 1.5 * np.maximum(blur(hgt, 0.06 * ppm) - hgt, 0), 0.75, 1.0)
    arh = np.stack([ao, rough, hgt], -1)
    to8 = lambda x: np.clip(x * 255 + 0.5, 0, 255).astype(np.uint8)
    return to8(col), to8(nrm * 0.5 + 0.5), to8(arh)


def inputs_hash(data, set_name):
    s = data["sets"][set_name]
    used = {l["surface"]: data["surfaces"][l["surface"]] for l in s["layers"]}
    blob = json.dumps([VERSION, data["light"], data["spread_L"], data["min_cm"], data["mass_sizes"], s["layers"], used, s.get("moss")],
                      sort_keys=True)
    blob += open(__file__, "rb").read().decode("utf-8")
    return hashlib.sha1(blob.encode()).hexdigest()[:12]


def manifest_path(set_name, out, data=None):
    pre = ((data or {}).get("sets", {}).get(set_name) or {}).get("prefix", "")  # (L1 W2 town: the setts' arrays beside the terrain's)
    return os.path.join(out, pre + ("ground.json" if set_name == "terrain" else "layers.json"))


def build_set(data, set_name, out=None):
    s = data["sets"][set_name]
    out = out or os.path.join(ROOT, s["dir"])
    os.makedirs(out, exist_ok=True)
    maps = [[], [], []]
    layers = []
    for l in s["layers"]:
        surf = data["surfaces"][l["surface"]]
        a, n, h = paint_surface(l["surface"], surf, l["metres"], data, set_name, l.get("variant"))
        for m, x in zip(maps, (a, n, h)):
            m.append(x)
        mean = srgb_to_lin(a.reshape(-1, 3) / 255.0).mean(0)
        layers.append({"name": l["name"], "surface": l["surface"], "metres": l["metres"], "source": "painted (tools/look/ground_paint.py)",
                       "from": surf["from"], "mean": [round(float(v), 5) for v in mean]})
    for f, m in zip(FILES, maps):
        Image.fromarray(np.concatenate(m, 0)).save(os.path.join(out, s.get("prefix", "") + f), optimize=False, compress_level=6)
    man = {"by": "tools/look/ground_paint.py (L1 C1: painted from nothing; godot/data/look/ground.json)", "painted": VERSION,
           "inputs": inputs_hash(data, set_name), "from": s["from"], "layers": layers}
    if s.get("moss"):  # (the arena's moss cushions, drawn by arena_ground.gdshader: ArenaGround.cs reads them here)
        man["moss"] = {k: s["moss"][k] for k in ("lit", "shade", "from")}
    if set_name == "terrain":  # (the setts' own maps are wave 2's; Ground.cs reads their size here)
        man["setts"] = {"metres": 4.0, "variants": 3, "px": 1024}
    with open(manifest_path(set_name, out, data), "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1)
    print(f"{set_name}: {len(layers)} layers -> {out}")
    return out


# ---- the grass cards' atlas ------------------------------------------------------------------------------------------
GC = 256  # (a clump cell; 4 x 2 cells, the last flower_cells with heads: grass_own.gdshader's layout)


def atlas_clump(rng, col, flowers, nfl):
    """One clump, side-on (the card faces the camera), drawn at 2x: a cool dark mound at the root (the underside), then
    5-8 broad blades tapering to a point, the back ones in the cool shade, the front ones in the body with their half
    toward the light lit (MB4: 'grass as big flat clumps', a lit top and a cool underside; three flat values, no fine
    blades: a blade is 7-11 cm across at its root on a 0.62 m card)."""
    W = GC * S
    im = Image.new("RGBA", (W, W), rgb8(lab(col["body"])) + (0,))
    d = ImageDraw.Draw(im)
    base = np.array([W * 0.5 + rng.uniform(-0.05, 0.05) * W, W * 0.985])
    lean = rng.uniform(-0.35, 0.35)
    under, body, lit = col["under"], col["body"], col["lit"]
    mound = [(base[0] + math.cos(t) * W * 0.2, base[1] - abs(math.sin(t)) * W * 0.11) for t in np.linspace(0, math.pi, 12)]
    d.polygon(mound + [(base[0] - W * 0.2, base[1])], fill=shift(under, 0) + (255,))
    nb = int(rng.integers(7, 12))
    order = sorted(range(nb), key=lambda i: rng.random())
    for rank, i in enumerate(order):
        front = rank >= nb // 2
        a = (i / max(nb - 1, 1) - 0.5) * 1.5 + lean + rng.uniform(-0.12, 0.12)
        ln = W * rng.uniform(0.55, 0.92) * (0.75 if abs(a) > 0.6 else 1.0)
        w0 = W * rng.uniform(0.055, 0.085)
        p0 = base + np.array([rng.uniform(-0.08, 0.08) * W, 0])
        tip = p0 + np.array([math.sin(a) * ln, -math.cos(a) * ln * 0.95])
        p1 = p0 + np.array([math.sin(a) * ln * 0.25, -ln * 0.6])
        s_ = np.linspace(0, 1, 14)[:, None]
        cl = (1 - s_) ** 2 * p0 + 2 * (1 - s_) * s_ * p1 + s_ ** 2 * tip
        tg = np.gradient(cl, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-9
        nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
        wd = w0 * (1 - s_[:, 0]) ** 0.85
        left, right = cl + nr * wd[:, None], cl - nr * wd[:, None]
        dL = rng.uniform(-1, 1) * 0.03
        d.polygon([tuple(p) for p in np.concatenate([left, right[::-1]])], fill=shift(body if front else under, dL) + (255,))
        if front:  # (the half toward the light, up-left on the card: lit)
            side = left if nr[len(nr) // 2] @ np.array([-0.6, -0.8]) > 0 else right
            d.polygon([tuple(p) for p in np.concatenate([side, cl[::-1]])], fill=shift(lit, dL) + (255,))
    for _ in range(nfl):
        hx = base[0] + rng.uniform(-0.25, 0.25) * W
        hy = W * rng.uniform(0.12, 0.3)
        d.line([(hx, hy), (base[0] + (hx - base[0]) * 0.4, base[1] - W * 0.2)], fill=shift(under, 0.04) + (255,), width=int(W * 0.022))
        r = W * rng.uniform(0.03, 0.04)
        fc = flowers[int(rng.integers(len(flowers)))]
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=shift(fc, 0) + (255,))
    a = np.asarray(im, np.float32) / 255
    return a.reshape(GC, S, GC, S, 4).mean((1, 3))


def atlas_tuft(rng, col, flowers, nfl, ah):
    """One clump as a low wide tuft (L1 l9 grass, FROM target 07's tufts and MB4 grass), side-on on a GC x ah cell, at 2x:
    three flat values by depth, never blades: a cool dark mass behind (the underside, leaves in 'under'), the body's
    leaves before it, and a crown of short broad pointed leaves in front lit ('lit'), fanned wide (a tuft is about twice
    as wide as it is tall); the root's last part darkens into the ground in the shader (grass_own.gdshader's base)."""
    W, H = GC * S, ah * S
    im = Image.new("RGBA", (W, H), rgb8(lab(col["body"])) + (0,))
    d = ImageDraw.Draw(im)
    cx = W * 0.5 + rng.uniform(-0.04, 0.04) * W
    lean = rng.uniform(-0.2, 0.2)

    def leaf(x0, ang, ln, w0, color):
        p0 = np.array([x0, H * 0.995])
        tip = p0 + np.array([math.sin(ang) * ln, -math.cos(ang) * ln])
        p1 = p0 + np.array([math.sin(ang) * ln * 0.2, -math.cos(ang) * ln * 0.62])
        s_ = np.linspace(0, 1, 12)[:, None]
        cl = (1 - s_) ** 2 * p0 + 2 * (1 - s_) * s_ * p1 + s_ ** 2 * tip
        tg = np.gradient(cl, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-9
        nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
        wd = w0 * np.sin(np.clip(s_[:, 0] * 0.85 + 0.15, 0, 1) * math.pi) ** 0.6 * (1 - s_[:, 0]) ** 0.35
        d.polygon([tuple(p) for p in np.concatenate([cl + nr * wd[:, None], (cl - nr * wd[:, None])[::-1]])], fill=color + (255,))

    # (a dark mound at the root, so the tuft sits on a mass, not a fan of stalks)
    d.ellipse([cx - W * 0.36, H * 0.62, cx + W * 0.36, H * 1.3], fill=shift(col["under"], 0) + (255,))
    layers = ((col["under"], 9, 12, 0.6, 1.0, 1.3), (col["body"], 7, 9, 0.48, 0.85, 1.15), (col["lit"], 5, 7, 0.36, 0.72, 1.0))
    for li, (cc, n0, n1, hl, hh, spread) in enumerate(layers):
        nb = int(rng.integers(n0, n1 + 1))
        for i in range(nb):
            u = (i + rng.uniform(0.2, 0.8)) / nb * 2 - 1
            ang = u * spread + lean + rng.uniform(-0.1, 0.1)
            ln = H * rng.uniform(hl, hh) * (1.0 - 0.35 * abs(u) ** 2)
            leaf(cx + u * W * (0.3 - 0.06 * li), ang, ln, W * rng.uniform(0.06, 0.08), shift(cc, rng.uniform(-1, 1) * 0.02))
    for _ in range(nfl):
        hx = cx + rng.uniform(-0.25, 0.25) * W
        hy = H * rng.uniform(0.1, 0.25)
        d.line([(hx, hy), (cx + (hx - cx) * 0.5, H * 0.7)], fill=shift(col["under"], 0.04) + (255,), width=int(W * 0.014))
        r = W * rng.uniform(0.02, 0.026)
        fc = flowers[int(rng.integers(len(flowers)))]
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=shift(fc, 0) + (255,))
    a = np.asarray(im, np.float32) / 255
    return a.reshape(ah, S, GC, S, 4).mean((1, 3))


def build_atlas(data, out=None):
    g = data["grass_atlas"]
    rng = np.random.default_rng(seed_of("grass_atlas", g["kind"], VERSION))
    ah = int(GC * g.get("aspect", 1.0))  # (a cell's height to its width: 0.5 for the tufts, twice as wide as tall)
    atlas = np.zeros((ah * 2, GC * 4, 4), np.float32)
    for j in range(8):
        nfl = 3 if j >= 8 - g["flower_cells"] else 0
        c = atlas_tuft(rng, g["colors"], g["flowers"], nfl, ah) if g.get("form") == "tuft" else atlas_clump(rng, g["colors"], g["flowers"], nfl)
        r, k = j // 4, j % 4
        atlas[r * ah:(r + 1) * ah, k * GC:(k + 1) * GC] = c
    # (the edges' color carried into the clear, so the mips never darken a clump's outline)
    body = np.array(rgb8(lab(g["colors"]["body"])), np.float32) / 255
    al = atlas[..., 3:4]
    atlas[..., :3] = np.where(al > 0.01, atlas[..., :3] / np.maximum(al, 1e-3), body)
    path = out or os.path.join(ROOT, g["out"])
    Image.fromarray(np.clip(atlas * 255 + 0.5, 0, 255).astype(np.uint8), "RGBA").save(path)
    print("grass atlas ->", path)
    return path


# ---- the check -------------------------------------------------------------------------------------------------------
def layer_numbers(rgb, metres):
    """fine: mean |L - median(L, 3 cm)| (photo grain scores high, flat shapes near 0); values90: how many 0.03-wide L
    bins hold 90% of the pixels (two or three masses plus their shapes: few)."""
    from scipy.ndimage import median_filter
    o = lin_to_oklab(srgb_to_lin(rgb.reshape(-1, 3) / 255.0))
    L = o[:, 0].reshape(rgb.shape[:2])
    k = max(int(round(0.03 * rgb.shape[0] / metres)) | 1, 3)
    fine = float(np.abs(L - median_filter(L, size=k, mode="wrap")).mean())
    hist = np.bincount(np.clip((L.reshape(-1) / 0.03).astype(int), 0, 40), minlength=41)
    cs = np.cumsum(np.sort(hist)[::-1]) / hist.sum()
    return fine, int(np.searchsorted(cs, 0.9) + 1)


def check_set(data, set_name, old=False):
    s = data["sets"][set_name]
    out = os.path.join(ROOT, s["dir"])
    ok = True
    if not old:
        man = json.load(open(manifest_path(set_name, out, data), encoding="utf-8"))
        if man.get("painted") != VERSION or man.get("inputs") != inputs_hash(data, set_name):
            print(f"{set_name}: STALE (version {man.get('painted')} inputs {man.get('inputs')}; rebuild)"); ok = False
        if any(not os.path.exists(os.path.join(out, s.get("prefix", "") + f)) for f in FILES):
            print(f"{set_name}: missing maps"); return False
    src = os.path.join(out, "albedo_paint.jpg" if old else s.get("prefix", "") + "albedo.png")
    if not os.path.exists(src):
        print(f"{set_name}: no {src}"); return ok
    a = np.asarray(Image.open(src).convert("RGB"))
    rows = []
    for i, l in enumerate(s["layers"]):
        fine, v90 = layer_numbers(a[i * N:(i + 1) * N], l["metres"])
        rows.append(f"{l['name']}:{fine:.4f}/{v90}")
        if not old and (fine > 0.012 or v90 > 9):
            ok = False
    print(f"{set_name}{' (old)' if old else ''}: fine/values90 " + "  ".join(rows) + ("" if old else ("  PASS" if ok else "  FAIL")))
    return ok


def main(a):
    data = json.load(open(DATA, encoding="utf-8"))
    cmd = a[0] if a else "check"
    which = [x for x in a[1:] if not x.startswith("--")]
    names = list(data["sets"]) if not which or which[0] == "all" else which
    if cmd == "build":
        if "--twice" in a:
            same = True
            for n_ in names:
                d1, d2 = tempfile.mkdtemp(), tempfile.mkdtemp()
                build_set(data, n_, d1); build_set(data, n_, d2)
                for f in tuple(data["sets"][n_].get("prefix", "") + f_ for f_ in FILES) + (os.path.basename(manifest_path(n_, d1, data)),):
                    eq = open(os.path.join(d1, f), "rb").read() == open(os.path.join(d2, f), "rb").read()
                    same &= eq
                    print(f"  {n_}/{f}: {'same' if eq else 'DIFFERENT'}")
                for d_ in (d1, d2):
                    shutil.rmtree(d_, ignore_errors=True)
            print("twice:", "byte-identical" if same else "NOT identical")
            return 0 if same else 1
        for n_ in names:
            build_set(data, n_)
        if not which or which[0] == "all":
            build_atlas(data)
        return 0
    if cmd == "atlas":
        build_atlas(data)
        return 0
    if cmd == "check":
        ok = all([check_set(data, n_, "--old" in a) for n_ in names])
        return 0 if ok else 1
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
