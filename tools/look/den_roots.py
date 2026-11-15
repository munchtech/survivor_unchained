"""The den dungeon's root tangle, painted: the root bank's tileable maps and root-cluster decals, ours from nothing (no
photo, scan or outside source; numpy + PIL only, deterministic).

    python tools/look/den_roots.py build   -> godot/art/dungeon/den/bank_{albedo,normal,arh}.png + bank.json,
                                              bank_decals.png + bank_decals.json, roots_preview.jpg, and the floor set
    python tools/look/den_roots.py build floor -> floor_decals.png + floor_decals.json (128 px/m: long floor roots off
                                              the bank, dark frame masses for the camera-side wall, whole pits in
                                              plan), floor_preview.jpg; nothing else rewritten
    python tools/look/den_roots.py build pits -> pit_decals.png + pit_decals.json (128 px/m: big pits painted at the
                                              game holes' size, shallow walkable hollows), pit_preview.jpg; nothing
                                              else rewritten
    python tools/look/den_roots.py check   -> per variant root coverage, median values (lit roots, all roots, gaps),
                                              the seam error at the tile edges, decal count by kind (reads the outputs)

FROM the owner-approved den targets (den_room.png's root walls, den_boss.png's roots over the pit rims; "Yes, build",
15 Nov), painted cel (Marvel Rivals kind): thick interwoven roots with three flat value bands (lit, mid, a purple-brown
shade), a thin lit edge on the light side, a dark ink outline (thicker on the shade side), long broken bark grooves,
ring cracks, painted dabs along the length, olive moss flecks on lit tops, and dark earth that falls to black in the
hollows between them. The palette is sampled from den_room.png's root walls (PAL below, with the numbers).

METHOD: a 2.5D height-field tube compositor at S = 2 x, box-reduced. A root is a smooth path (Catmull-Rom over a
low-curvature random walk, or a closed sine-sum loop round the torus for the bank's long roots), a radius profile (knots
+-15%, a taper over the last 30-60%), forks (25-50 degrees, 0.4-0.7 of the parent's radius, two generations) and a base
height z0 that rises and falls along it (the weave). Each segment is stamped as a tapered capsule: across a = d / r,
height h = z0 + 0.7 r sqrt(1 - a^2), z-buffer max; the winner's id, signed across, along, radius and the direction of
its distance vector are kept. Shading reads those (the light from the image's upper left, toward the light (-0.5, -0.85)
in image x-right / y-down, elevation 60 degrees), plus a hard cast shadow marched over the height field and the hollows'
depth (blur(h) - h). The bank wraps (every stamp, blur and shadow is periodic), so it tiles exactly.
"""
import json, math, os, sys, time, zlib

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "godot", "art", "dungeon", "den")
VERSION = 1
S = 2                       # drawn at S x, box-reduced
BANK_M = 5.0                # a variant covers 5 x 5 m
BANK_PX = 2048
BANK_VARIANTS = 2
COVER = 0.75                # the bank's root coverage (the down-roots stop at it)
DEC_PPM = 256               # the decal atlas, px per metre
ATLAS_W = 2048
PAD = 10
PREVIEW_PPM = 73            # (the game at 1080p)
TUBE = 0.7                  # a root's section: half an ellipse 0.7 r high
HMAX = 0.8                  # arh.b = height / HMAX metres

L2 = np.array([-0.5, -0.85]); L2 /= np.linalg.norm(L2)     # toward the light, image x right, y down
ELEV = math.radians(60.0)
CE, SE = math.cos(ELEV), math.sin(ELEV)

# ---- the palette (sRGB albedo), sampled from den_room.png's root walls (screen values, median of 7 x 7 px) ------------
# lit root top #865439 (the lit arc, Y 92) / #744e3b (p95-99 of the bottom wall); mid #553a2f / #48302c; purple-brown
# shade #322425 / #2b2124; deep underside #201b1f; earth between the roots #2a2222; the deep gaps #0e1014 / #0d0e11;
# the ink a near-black warm #140f10 (the wall's p0-5 is #0d0e11).
PAL = {
    "lit_hi": "#94613f",    # the painted dabs on the lit tops
    "lit":    "#805338",
    "mid":    "#583c2f",
    "shade":  "#352529",    # purple-brown
    "deep":   "#221a1e",
    "edge":   "#a46d48",    # the thin lit edge on the light side
    "ink":    "#140f10",
    "earth":  "#2c2322",
    "earth_dk": "#1b1718",
    "gap":    "#0e0f13",
    "moss":   "#5f5c2c",
    "moss_dk": "#46441f",
    "shadow": "#1a1210",    # the decals' contact shadow (rgb under alpha 0.2-0.55)
}


def seed_of(*k): return zlib.crc32(repr(k).encode()) & 0x7fffffff


def rgbf(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255.0


TONES = np.stack([rgbf(PAL[k]) for k in ("lit_hi", "lit", "mid", "shade", "deep")])  # t = 0..4


def smooth(x): x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


# ---- periodic fields ---------------------------------------------------------------------------------------------------
def pnoise(n, f_lo, f_hi, rng):
    """A tileable noise (zero mean, unit spread), frequencies f_lo..f_hi cycles per side."""
    k = np.fft.fftfreq(n) * n
    K = np.sqrt(k[None, :] ** 2 + k[:, None] ** 2)
    band = (K >= f_lo) & (K <= f_hi)
    spec = (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))) * band / np.maximum(K, 1.0)
    f = np.fft.ifft2(spec).real
    return ((f - f.mean()) / (f.std() + 1e-9)).astype(np.float32)


def blur(x, sig, wrap):
    """A Gaussian blur (sigma px) by FFT: periodic, or zero-padded when not wrap."""
    if not wrap:
        p = int(3 * sig) + 2
        y = blur(np.pad(x, p), sig, True)
        return y[p:-p, p:-p]
    h, w = x.shape
    ky, kx = np.fft.fftfreq(h)[:, None], np.fft.rfftfreq(w)[None, :]
    g = np.exp(-2 * (math.pi * sig) ** 2 * (kx ** 2 + ky ** 2))
    return np.fft.irfft2(np.fft.rfft2(x) * g, s=x.shape).astype(np.float32)


def tex(T, u, v):
    """Bilinear lookup in a periodic texture T at texel coordinates (u across columns, v down rows)."""
    n = T.shape[0]
    u0, v0 = np.floor(u), np.floor(v)
    fu, fv = (u - u0).astype(np.float32), (v - v0).astype(np.float32)
    i0, j0 = u0.astype(np.int64) % n, v0.astype(np.int64) % n
    i1, j1 = (i0 + 1) % n, (j0 + 1) % n
    return (T[j0, i0] * (1 - fu) + T[j0, i1] * fu) * (1 - fv) + (T[j1, i0] * (1 - fu) + T[j1, i1] * fu) * fv


# ---- the height field --------------------------------------------------------------------------------------------------
class Field:
    def __init__(self, w, h, ppm, wrap):
        self.w, self.h, self.ppm, self.wrap = w, h, ppm, wrap
        n = w * h
        self.H = np.zeros(n, np.float32)           # px; the earth / floor at 0
        self.ID = np.full(n, -1, np.int32)
        self.A = np.zeros(n, np.float32)           # signed across, -1..1
        self.S = np.zeros(n, np.float32)           # along, px
        self.R = np.zeros(n, np.float32)           # radius, px
        self.QX = np.zeros(n, np.float32)          # the distance vector's direction (the section's outward normal, flat)
        self.QY = np.zeros(n, np.float32)

    def stamp(self, P, R, Z, SS, rid):
        """A root's polyline P (N, 2) px, radius R, base height Z, arc length SS (px): tapered capsules, z-buffered."""
        W, Hh = self.w, self.h
        for i in range(len(P) - 1):
            ax, ay = P[i]
            bx, by = P[i + 1]
            ra, rb = R[i], R[i + 1]
            rm = max(ra, rb)
            if rm < 0.6:
                continue
            xs = np.arange(int(math.floor(min(ax, bx) - rm)), int(math.ceil(max(ax, bx) + rm)) + 1)
            ys = np.arange(int(math.floor(min(ay, by) - rm)), int(math.ceil(max(ay, by) + rm)) + 1)
            if self.wrap:
                xi, yi = xs % W, ys % Hh
            else:
                xs, ys = xs[(xs >= 0) & (xs < W)], ys[(ys >= 0) & (ys < Hh)]
                if not len(xs) or not len(ys):
                    continue
                xi, yi = xs, ys
            X = xs[None, :].astype(np.float32) + 0.5
            Y = ys[:, None].astype(np.float32) + 0.5
            dx, dy = bx - ax, by - ay
            l2 = dx * dx + dy * dy
            ur = ((X - ax) * dx + (Y - ay) * dy) / l2 if l2 > 1e-6 else np.zeros((len(ys), len(xs)), np.float32)
            u = np.clip(ur, 0, 1)
            qx = X - ax - u * dx
            qy = Y - ay - u * dy
            r = ra + u * (rb - ra)
            a2 = (qx * qx + qy * qy) / (r * r)
            jj, ii = np.nonzero(a2 < 1.0)
            if not len(jj):
                continue
            a2s, us, rs = a2[jj, ii], u[jj, ii], r[jj, ii]
            ov = np.abs(ur[jj, ii] - us) * math.sqrt(l2)      # (in a cap: lowered, so a cap never rides over the next
            hh = Z[i] + us * (Z[i + 1] - Z[i]) + TUBE * rs * np.sqrt(1.0 - a2s) - ov   # segment's body: no ribs)
            flat = yi[jj] * W + xi[ii]
            up = hh > self.H[flat]
            if not up.any():
                continue
            f = flat[up]
            qxs, qys = qx[jj, ii][up], qy[jj, ii][up]
            d = np.sqrt(qxs * qxs + qys * qys) + 1e-6
            sgn = np.where(dx * qys - dy * qxs >= 0, 1.0, -1.0)
            self.H[f] = hh[up]
            self.ID[f] = rid
            self.A[f] = sgn * np.sqrt(a2s[up])
            self.S[f] = SS[i] + us[up] * (SS[i + 1] - SS[i])
            self.R[f] = rs[up]
            self.QX[f] = qxs / d
            self.QY[f] = qys / d


# ---- root paths --------------------------------------------------------------------------------------------------------
def catmull(C, n_per=20):
    """An open uniform Catmull-Rom through the control rows C (K, D), sampled n_per per span."""
    C = np.asarray(C, float)
    E = np.concatenate([2 * C[:1] - C[1:2], C, 2 * C[-1:] - C[-2:-1]])
    t = np.linspace(0, 1, n_per, endpoint=False)[:, None]
    out = []
    for k in range(len(C) - 1):
        p0, p1, p2, p3 = E[k], E[k + 1], E[k + 2], E[k + 3]
        out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(C[-1:])
    return np.concatenate(out)


def resample(D, ppm):
    """Dense rows (x, y, z, r) px -> the stamp's samples, spaced by 0.3 r (2..36 px); returns P, R, Z, SS."""
    seg = np.hypot(np.diff(D[:, 0]), np.diff(D[:, 1]))
    s = np.concatenate([[0.0], np.cumsum(seg)])
    out, x = [], 0.0
    while x < s[-1]:
        out.append(x)
        x += float(np.clip(0.3 * np.interp(x, s, D[:, 3]), 2.0, 36.0))
    out.append(s[-1])
    q = np.array(out)
    cols = [np.interp(q, s, D[:, j]) for j in range(4)]
    return np.stack(cols[:2], 1), cols[3], cols[2], q


class Roots:
    """The roots of one canvas: generation helpers (metres in, px out) and the per-id tables shading needs."""

    def __init__(self, F, rng):
        self.F, self.rng, self.ppm = F, rng, F.ppm
        self.send, self.ng, self.rnom, self.paths = [], [], [], []

    def add(self, D, closed=False):
        """Stamp dense rows D (x, y, z, r) px as a new root; returns its id and its (P, R, Z, SS)."""
        rid = len(self.send)
        P, R, Z, SS = resample(D, self.ppm)
        self.F.stamp(P, R, Z, SS, rid)
        rn = float(np.median(D[:, 3])) / self.ppm
        self.send.append(float(SS[-1]) if closed else 0.0)
        self.rnom.append(rn)
        self.ng.append(int(np.clip(round(rn / 0.045), 3, 9)))
        self.paths.append((P, R, Z, SS))
        return rid

    def walk(self, start, heading, length_m, step=(0.4, 0.65), wig=8.0, pull=0.18):
        """Control points of a low-curvature walk: the turn rate itself wanders (long S curves), pulled to the heading."""
        rng, ppm = self.rng, self.ppm
        pts, th, om, L = [np.array(start, float)], heading, 0.0, 0.0
        while L < length_m * ppm:
            st = min(rng.uniform(*step) * ppm, length_m * ppm - L + 1.0)
            om = 0.65 * om + rng.normal(0, math.radians(wig))
            th += om + pull * math.atan2(math.sin(heading - th), math.cos(heading - th))
            pts.append(pts[-1] + st * np.array([math.cos(th), math.sin(th)]))
            L += st
        return np.array(pts)

    def open_root(self, ctrl, r_m, zbase_m, zamp_m, tip=(0.3, 0.6), emerge=True, zdive=0.8, tip_r=0.3):
        """Dense rows for an open root along ctrl px: knots +-15%, the weave, the base emerging from the earth (or not,
        for a fork) and the tip tapering over its last tip fraction (zdive: the tip sinks to zdive x r below 0)."""
        rng, ppm = self.rng, self.ppm
        K = len(ctrl)
        z = (zbase_m + zamp_m * np.clip(rng.normal(0, 1, K), -1.6, 1.6)) * ppm
        r = r_m * ppm * np.clip(1 + 0.09 * rng.normal(0, 1, K), 0.85, 1.15)
        D = catmull(np.column_stack([ctrl, z, r]))
        s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(D[:, 0]), np.diff(D[:, 1])))])
        Ls = s[-1]
        tf = rng.uniform(*tip)
        st = (1 - tf) * Ls
        w = np.clip((s - st) / max(Ls - st, 1.0), 0, 1)
        D[:, 3] *= 1 - (1 - tip_r) * w ** 1.5
        D[:, 3] *= 1 + 0.06 * np.sin(s / (rng.uniform(0.35, 0.6) * ppm) * 2 * math.pi + rng.uniform(0, 6.3))
        if emerge:
            e = smooth(s / (0.45 * ppm))
            D[:, 2] = D[:, 2] * e - (1 - e) * 1.0 * D[:, 3]
        if zdive is not None:
            D[:, 2] = D[:, 2] * (1 - smooth(w * 1.4)) - smooth(w * 1.4) * zdive * D[:, 3]
        return D

    def fork(self, D, gen, ang=(25, 50), ratio=(0.4, 0.7), length=(0.7, 1.6), zbase=None, zamp=0.08, zdive=None,
             tip=(0.3, 0.6), tip_r=0.3, **kw):
        """A child from a dense parent D at 25-75% of its length, 25-50 degrees off, 0.4-0.7 of its radius."""
        rng, ppm = self.rng, self.ppm
        n = len(D)
        i = int(rng.uniform(0.22, 0.72) * (n - 1))
        tx, ty = D[min(i + 3, n - 1), :2] - D[max(i - 3, 0), :2]
        th = math.atan2(ty, tx) + math.radians(rng.uniform(*ang)) * rng.choice([-1, 1])
        rc = D[i, 3] / ppm * rng.uniform(*ratio)
        L = rng.uniform(*length) * max(1.0, rc / 0.1)
        ctrl = self.walk(D[i, :2], th, L, step=(0.3, 0.5), **kw)
        zb = D[i, 2] / ppm if zbase is None else zbase
        C = self.open_root(ctrl, rc, zb, zamp, tip=tip, emerge=False, zdive=zdive, tip_r=tip_r)
        k = smooth(np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(C[:, 0]), np.diff(C[:, 1])))]) / (0.5 * ppm))
        C[:, 2] = (1 - k) * D[i, 2] + k * C[:, 2]          # (it leaves its parent at the parent's base height)
        return C


def loop_root(rng, W, ppm, y0, r_m, zbase_m, zamp_m, vertical=False, sweep=1.0, zk=((2, 4), (4, 6), (6, 9))):
    """Dense rows of a closed root round the torus: x runs 0..W, y, z, r are sine sums periodic over it (sweep scales
    the run's side-to-side curve; zk the z wave numbers, low = long stretches over or under)."""
    n = 1600
    t = np.linspace(0, 1, n + 1)
    def ssum(amps, ks):
        return sum(a * np.sin(2 * math.pi * k * t + rng.uniform(0, 2 * math.pi)) for a, k in zip(amps, ks))
    x = rng.uniform(0, W) + t * W
    y = y0 + sweep * ssum([rng.uniform(0.22, 0.36), rng.uniform(0.08, 0.16), rng.uniform(0.02, 0.05)], [1, 2, 3]) * ppm
    z = (zbase_m + zamp_m * ssum([0.75, 0.5, 0.3], [rng.integers(*k) for k in zk])) * ppm
    r = r_m * ppm * (1 + ssum([0.07, 0.05, 0.03], [rng.integers(3, 6), rng.integers(6, 10), rng.integers(10, 15)]))
    D = np.column_stack([x, y, z, r])
    if vertical:
        D[:, [0, 1]] = D[:, [1, 0]]
    return D


# ---- shading -----------------------------------------------------------------------------------------------------------
def cast_shadow(H, ppm, wrap):
    """A hard cast shadow: p is shadowed when the height field, marched toward the light, rises above the light's ray."""
    h, w = H.shape
    step = max(2, int(round(0.005 * ppm)))
    tn = math.tan(ELEV)
    n = int(math.ceil(float(H.max()) / tn / step)) + 1
    p = n * step + 2
    G = H if wrap else np.pad(H, p)
    sh = np.zeros(G.shape, bool)
    bias = 0.006 * ppm
    for k in range(1, n + 1):
        t = k * step
        dx, dy = int(round(t * L2[0])), int(round(t * L2[1]))
        sh |= np.roll(G, (-dy, -dx), (0, 1)) > G + t * tn + bias
    return sh if wrap else sh[p:-p, p:-p]


def shade(F, RT, seed, earth=True):
    """Colour every pixel of the field: (h, w, 3) sRGB float, plus the root mask, the cast shadow and the hollow depth."""
    rng = np.random.default_rng(seed)
    W, Hh, ppm = F.w, F.h, F.ppm
    H2 = F.H.reshape(Hh, W)
    sh = cast_shadow(H2, ppm, F.wrap).ravel()
    deep = np.clip((blur(H2, 0.11 * ppm, F.wrap) - H2) / (0.08 * ppm), 0, 1).ravel()
    T1, T2, T3 = (pnoise(256, 10, 40, rng) for _ in range(3))
    TM = pnoise(512, 30, 90, rng)
    col = np.zeros((Hh * W, 3), np.float32)

    idx = np.nonzero(F.ID >= 0)[0]
    rid = F.ID[idx]
    a = F.A[idx]; aa = np.abs(a)
    sm = F.S[idx] / ppm                 # along, metres
    rp = F.R[idx]; rm = rp / ppm        # radius px, metres
    qx, qy = F.QX[idx], F.QY[idx]
    send = np.array(RT.send, np.float32)[rid] / ppm
    rnom = np.array(RT.rnom, np.float32)[rid]
    ng = np.array(RT.ng, np.float32)[rid]
    th = np.arcsin(np.clip(a, -1, 1))
    closed = send > 0

    def nz(T, along_m, v):
        """A noise along the root (one feature per along_m metres), periodic round a closed root (cross-faded)."""
        u = sm / along_m * 10.0
        n0 = tex(T, u, v)
        if closed.any():
            c = closed
            w_ = sm[c] / send[c]
            n1 = tex(T, (sm[c] - send[c]) / along_m * 10.0, v[c])
            n0[c] = (n0[c] * (1 - w_) + n1 * w_) / np.sqrt((1 - w_) ** 2 + w_ ** 2)
        return n0

    off = rid.astype(np.float32) * 37.3
    # the section's normal and the light
    ac = np.minimum(aa, 0.985)
    k = TUBE * ac / np.sqrt(1 - ac * ac)
    ql = qx * L2[0] + qy * L2[1]                       # > 0: this side faces the light
    lam = (k * ql * CE + SE) / np.sqrt(1 + k * k)
    lam = lam + 0.04 * nz(T1, 0.4, th / math.pi * 6 + off)
    t = np.where(lam > 0.95, 1, np.where(lam > 0.8, 2, 3))
    t = np.where(sh[idx], np.maximum(t, 3), t)
    dp = deep[idx]
    t = t + (dp > 0.45) + (dp > 0.78)
    # painted dabs along the length: a lit fleck up a step, a dark one down
    big = rm > 0.055
    dab = nz(T2, 0.5, (th / math.pi + 0.5) * ng * 5.0 + off + 5.0)
    t = np.where(big & (dab > 1.15) & ((t == 1) | (t == 2)), t - 1, t)
    t = np.where(big & (dab < -1.35) & (t == 3), 4, t)
    t = np.clip(t, 0, 4)
    c = TONES[t]
    # bark: long wobbly broken grooves (even in the section's angle, so they crowd toward the edges), ring cracks
    gw = 0.017 * ppm
    q = (th / math.pi + 0.5) * ng + 0.45 * nz(T3, 0.75, off + 2.0)
    qr = np.round(q)
    f = np.abs(q - qr)
    wq = gw * ng / (math.pi * np.maximum(rp * np.cos(th), 1.0))
    keep = nz(T1, 0.4, qr * 9.7 + off + 11.0) > -0.25
    groove = (rm > 0.07) & (aa < 0.88) & (f < 0.5 * wq) & keep
    rs = 0.9                                          # m between ring cracks (about half kept)
    so = sm + (off % 7.0)
    ri = np.floor(so / rs)
    pos = (so / rs - ri - 0.5) * rs + 0.035 * np.sin(th * 2.5 + ri)
    ring = (rm > 0.06) & (np.abs(pos) < 0.0075) & (np.abs(th) < 0.35 + 0.9 * (tex(T3, ri * 7.3, off) * 0.5 + 0.5)) \
        & (tex(T2, ri * 5.1 + 3, off + 1) > 0.15)
    gk = groove | ring
    c[gk] = c[gk] * 0.45 + rgbf(PAL["ink"]) * 0.55
    # moss flecks on lit upward tops
    pxx, pyy = (idx % W).astype(np.float32), (idx // W).astype(np.float32)
    mn = tex(TM, pxx * 512.0 / W, pyy * 512.0 / Hh) if F.wrap else tex(TM, pxx / ppm * 60.0, pyy / ppm * 60.0)
    top = (rm > 0.08) & (t <= 1) & (aa < 0.55) & ~gk
    c[top & (mn > 1.75)] = rgbf(PAL["moss_dk"])
    c[top & (mn > 2.05)] = rgbf(PAL["moss"])
    # the lit edge and the ink: the root's own silhouette is where it meets anything lower (the z-buffer's depth jump)
    wi = (0.015 + 0.013 * np.clip(-ql, 0, 1)) * ppm
    edge = (aa > 1 - (wi + 0.016 * ppm) / rp) & (ql > 0.3) & (t <= 2) & ~sh[idx] & (rm > 0.05)
    c[edge] = rgbf(PAL["edge"])
    ink = (aa > 1 - wi / rp) | (F.H[idx] < 0.012 * ppm)
    c[ink] = rgbf(PAL["ink"])
    col[idx] = c
    tone = np.full(Hh * W, -1, np.int8)
    tone[idx] = np.where(ink, 9, np.where(edge, 0, t))

    if earth:
        e = np.nonzero(F.ID < 0)[0]
        de = deep[e] + 0.12 * tex(T1, (e % W) / W * 256, (e // W) / Hh * 256)
        b = (de > 0.25).astype(np.int32) + (de > 0.55) + sh[e]
        col[e] = np.stack([rgbf(PAL["earth"]), rgbf(PAL["earth_dk"]), rgbf(PAL["gap"]), rgbf(PAL["gap"])])[np.minimum(b, 3)]
    return col.reshape(Hh, W, 3), (F.ID >= 0).reshape(Hh, W), sh.reshape(Hh, W), deep.reshape(Hh, W), tone.reshape(Hh, W)


def reduce(x):
    h, w = x.shape[:2]
    return x.reshape(h // S, S, w // S, S, *x.shape[2:]).mean((1, 3))


to8 = lambda x: np.clip(x * 255 + 0.5, 0, 255).astype(np.uint8)


# ---- the bank ----------------------------------------------------------------------------------------------------------
def bank_variant(v):
    rng = np.random.default_rng(seed_of("den_roots", "bank", v, VERSION))
    W = BANK_PX * S
    ppm = W / BANK_M
    F = Field(W, W, ppm, True)
    RT = Roots(F, rng)
    tt = np.linspace(0, 1, 1601)
    # the huge roots across the bank: a twisted pair and one more, bands sized by each one's span, laid in a shuffled
    # order with random (Dirichlet) gaps, so the spacing never repeats and the hollows come few and big
    items = [("pair", None), ("huge", rng.uniform(0.42, 0.55))]   # (3 huge: a 4th leaves no room for hollows)
    pr = [rng.uniform(0.40, 0.50), rng.uniform(0.40, 0.47)]
    pA = (pr[0] + pr[1]) * rng.uniform(1.6, 2.0)            # the pair's peak centre separation, m
    span = [pA + pr[0] + pr[1] if k == "pair" else 2 * r for k, r in items]
    order = rng.permutation(len(items))
    gaps = rng.dirichlet(np.full(len(items), 0.8)) * max(BANK_M - sum(span), 0.0)
    yy, y0s = rng.uniform(0, BANK_M), {}
    for j, i in enumerate(order):
        y0s[i] = (yy + 0.5 * span[i]) * ppm
        yy += span[i] + gaps[j]
    huge, hy = [], []
    for i, (kind, r) in enumerate(items):
        if kind == "pair":                                    # two huge roots twisted round each other once a tile
            D1 = loop_root(rng, W, ppm, y0s[i], pr[0], 0.38 * pr[0], 0.3 * pr[0], sweep=1.1, zk=((1, 3), (2, 4), (3, 5)))
            D2 = loop_root(rng, W, ppm, y0s[i], pr[1], 0.38 * pr[1], 0.3 * pr[1], sweep=1.1, zk=((1, 3), (2, 4), (3, 5)))
            ph = rng.uniform(0, 2 * math.pi)
            sw, cw = np.sin(2 * math.pi * tt + ph), np.cos(2 * math.pi * tt + ph)
            yc = D1[:, 1].copy()
            D2[:, 0] = D1[:, 0]
            D1[:, 1] = yc - 0.5 * pA * ppm * sw
            D2[:, 1] = yc + 0.5 * pA * ppm * sw
            c = 0.32 * ppm * 0.5 * (pr[0] + pr[1])
            D1[:, 2] += c * cw
            D2[:, 2] -= c * cw
            for D in (D1, D2):
                RT.add(D, closed=True); huge.append(D)
            hy += [(y0s[i] - 0.5 * pA * ppm, pr[0]), (y0s[i] + 0.5 * pA * ppm, pr[1])]
        else:
            D = loop_root(rng, W, ppm, y0s[i], r, 0.38 * r, 0.35 * r, sweep=rng.uniform(1.0, 1.4), zk=((1, 3), (2, 4), (3, 5)))
            RT.add(D, closed=True); huge.append(D); hy.append((y0s[i], r))
    cov = lambda: float((F.ID >= 0).mean())
    est = lambda r: cov() + 2 * 0.85 * r / BANK_M * (1 - cov())   # (a root's expected new coverage)
    xs = (rng.uniform(0, 1) + np.arange(3) / 3 + rng.uniform(-0.08, 0.08, 3)) * W
    nv = 0
    for x0 in xs[:int(rng.integers(2, 4))]:                   # medium roots running down the bank, over and under
        r = rng.uniform(0.18, 0.25)
        if nv and est(r) > COVER - 0.06:
            break
        D = loop_root(rng, W, ppm, x0, r, 0.32, 0.16, vertical=True, sweep=rng.uniform(1.0, 1.5), zk=((2, 4), (3, 5), (5, 8)))
        RT.add(D, closed=True); nv += 1
    nm = 0
    for k in range(int(rng.integers(4, 7))):                  # medium roots riding a huge one's flank, over and under it
        r = rng.uniform(0.18, 0.25)
        if nm and est(r) > COVER - 0.015:
            break
        yh, rh = hy[int(rng.integers(len(hy)))]
        y0 = yh + rng.choice([-1, 1]) * (rh + rng.uniform(-0.15, 0.25)) * ppm
        D = loop_root(rng, W, ppm, y0, r, 0.3, 0.12, sweep=rng.uniform(1.2, 1.8), zk=((1, 3), (2, 5), (4, 7)))
        RT.add(D, closed=True); nm += 1
    print(f"    (huge + medium coverage {cov():.3f})")
    for D in huge:                                            # at most one long fork a huge root
        if rng.random() < 0.5:
            RT.add(RT.fork(D, 1, ang=(18, 32), ratio=(0.35, 0.5), length=(0.75, 1.05), zamp=0.06, zdive=0.8, tip=(0.4, 0.55)))
    for _ in range(int(rng.integers(4, 7))):                  # rootlets, long, mostly along the bank
        free = np.nonzero(F.ID < 0)[0]
        p0 = free[rng.integers(len(free))]
        h0 = (rng.choice([0, math.pi]) + rng.normal(0, 0.3)) if rng.random() < 0.7 else (math.pi / 2 + rng.normal(0, 0.35))
        D = RT.open_root(RT.walk((p0 % W, p0 // W), h0, rng.uniform(1.5, 2.6), step=(0.35, 0.55), wig=9),
                         rng.uniform(0.05, 0.075), 0.1, 0.08, zdive=0.8)
        RT.add(D)
    ns = nm + nv
    col, mask, sh, deep, tone = shade(F, RT, seed_of("den_roots", "bank_shade", v, VERSION), earth=True)
    Hm = F.H.reshape(W, W) / ppm
    rough = np.where(mask, 0.8, 0.95).astype(np.float32)
    col, Hm, rough, cov = reduce(col), reduce(Hm), reduce(rough), float(mask.mean())
    deep = reduce(deep)
    n = BANK_PX
    ppo = n / BANK_M
    hb = blur(Hm.astype(np.float32), 1.0, True)
    du = (np.roll(hb, -1, 1) - np.roll(hb, 1, 1)) * 0.5 * ppo
    dv = (np.roll(hb, -1, 0) - np.roll(hb, 1, 0)) * 0.5 * ppo
    g = np.sqrt(du * du + dv * dv)
    sc = np.minimum(1.0, 2.5 / np.maximum(g, 1e-6))
    nrm = np.stack([-du * sc, dv * sc, np.ones_like(du)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    ao = np.clip(1.0 - 1.1 * deep, 0.15, 1.0)
    arh = np.stack([ao, rough, np.clip(Hm / HMAX, 0, 1)], -1)
    tt = tone[mask]
    print(f"  bank v{v}: {len(RT.send)} roots ({nm} medium, {nv} down), coverage {cov:.3f}; tones lit_hi/lit/mid/shade/deep/ink % "
          + " ".join(f"{100 * (tt == k).mean():.0f}" for k in (0, 1, 2, 3, 4, 9)))
    return to8(col), to8(nrm * 0.5 + 0.5), to8(arh), cov


def build_bank(out):
    maps = [[], [], []]
    covs = []
    for v in range(BANK_VARIANTS):
        a, n, h, cov = bank_variant(v)
        for m, x in zip(maps, (a, n, h)):
            m.append(x)
        covs.append(round(cov, 4))
    for f, m in zip(("bank_albedo.png", "bank_normal.png", "bank_arh.png"), maps):
        Image.fromarray(np.concatenate(m, 0)).save(os.path.join(out, f), optimize=False, compress_level=6)
    man = {"by": "tools/look/den_roots.py (painted from nothing; no outside source)", "version": VERSION,
           "from": "den_room.png's root walls, den_boss.png's roots over the pit rims (owner-approved den targets, 15 Nov)",
           "metres": BANK_M, "px": BANK_PX, "variants": BANK_VARIANTS,
           "layout": "variants stacked vertically (variant v = rows v*px .. (v+1)*px); each tiles seamlessly",
           "orientation": "image up = up the bank / away from the camera; roots run mostly left-right along the bank",
           "light": [round(float(c), 4) for c in L2], "light_elevation_deg": 60,
           "light_note": "baked into the albedo: toward the light in image x right / y down (the upper left)",
           "normal": "tangent space, nrm = (-dh/dx, dh/dy, 1) (OpenGL, green up), slope clamped at 2.5",
           "arh": "r = ao (the hollows' depth), g = roughness (roots 0.8, earth 0.95), b = height / height_m",
           "height_m": HMAX, "coverage": covs, "palette": PAL}
    with open(os.path.join(out, "bank.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1)


# ---- the decals --------------------------------------------------------------------------------------------------------
WALLS = [(3.0, 1.7), (3.4, 1.8), (3.8, 1.9), (3.2, 1.8), (4.0, 1.8), (3.5, 1.9), (3.6, 1.7), (3.9, 1.8)]   # (along, down) m
RIMS = [(2.6, 1.25), (3.0, 1.3), (3.5, 1.3), (4.0, 1.35)]


def decal_wall(i, wm, hm):
    for attempt in range(200):
        rng = np.random.default_rng(seed_of("den_roots", "wall", i, attempt, VERSION))
        ppm = DEC_PPM * S
        W, Hh = int(round(wm * DEC_PPM)) * S, int(round(hm * DEC_PPM)) * S
        F = Field(W, Hh, ppm, False)
        RT = Roots(F, rng)
        n = int(rng.integers(2, 4))
        same = rng.random() < 0.5
        dirs = np.full(n, rng.choice([1, -1])) if same else rng.permutation([1, -1, rng.choice([1, -1])])[:n]
        ok = True
        dense = []
        for k in range(n):                                    # down out of the bank, then a turn onto the floor
            d = int(dirs[k])
            r0 = rng.uniform(0.15, 0.30)
            down = rng.uniform(1.0, 1.5)                      # from y = -0.3 m: the floor run lies at down - 0.3 m
            run = rng.uniform(1.5, 2.5)
            yf = min(down - 0.3, hm - r0 - 0.12)
            x0 = (rng.uniform(r0 + 0.15, wm - run - r0 - 0.15 - 0.4) if d > 0 else
                  rng.uniform(run + r0 + 0.15 + 0.4, wm - r0 - 0.15)) if wm - run - 2 * r0 - 0.7 > 0 else 0.5 * wm
            tr = rng.uniform(0.35, 0.55)                      # the turn's radius
            pts = [(x0, -0.3), (x0, yf - tr)]
            for a in np.linspace(0, math.pi / 2, 5)[1:]:      # the quarter turn
                pts.append((x0 + d * tr * (1 - math.cos(a)), yf - tr + tr * math.sin(a)))
            pts.append((x0 + d * (tr + run), yf))
            seg = np.array(pts)
            L = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(seg, axis=0).T))])
            q = np.linspace(0, L[-1], max(5, int(L[-1] / 0.38) + 1))
            C = np.column_stack([np.interp(q, L, seg[:, 0]), np.interp(q, L, seg[:, 1])])
            C[1:-1] += rng.normal(0, 0.045, (len(C) - 2, 2))   # (hand jitter, the ends kept)
            C[-1, 1] += rng.normal(0, 0.06)
            D = RT.open_root(C * ppm, r0, 0.0, 0.04, tip=(0.4, 0.4), emerge=False, zdive=0.5, tip_r=0.2)
            sd = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(D[:, 0]), np.diff(D[:, 1])))])
            e = smooth(sd / (((down - tr) + 0.3) * ppm))
            D[:, 2] += (1 - e) * 0.2 * ppm                    # (high where it leaves the bank, down onto the floor)
            dense.append(D)
        xs0 = [D[0, 0] for D in dense]
        if any(dirs[i] > 0 > dirs[j] and xs0[i] < xs0[j] for i in range(n) for j in range(n)):
            continue                                          # (two turning toward each other read as a U)
        def inside(D):                                        # inside the sides and the bottom
            m = D[:, 3] > 0.3
            return not ((D[m, 0] - D[m, 3] < 4).any() or (D[m, 0] + D[m, 3] > W - 4).any() or (D[m, 1] + D[m, 3] > Hh - 4).any())
        if not all(inside(D) for D in dense):
            continue
        for D in list(dense):
            nf, tries = int(rng.integers(1, 3)), 0
            while nf and tries < 12:
                tries += 1
                C = RT.fork(D, 1, ang=(22, 40), ratio=(0.45, 0.65), length=(0.45, 0.7), zbase=0.0, zamp=0.04, zdive=0.5,
                            tip=(0.4, 0.4), tip_r=0.2, wig=9)
                if inside(C) and C[0, 1] > 0.25 * ppm:
                    dense.append(C); nf -= 1
        for D in dense:
            RT.add(D)
        return F, RT, rng
    raise SystemExit("den_roots: no wall decal fits %d" % i)


def decal_rim(i, wm, hm):
    for attempt in range(200):
        rng = np.random.default_rng(seed_of("den_roots", "rim", i, attempt, VERSION))
        ppm = DEC_PPM * S
        W, Hh = int(round(wm * DEC_PPM)) * S, int(round(hm * DEC_PPM)) * S
        F = Field(W, Hh, ppm, False)
        RT = Roots(F, rng)
        dense = []
        nr = int(rng.integers(1, 3))
        n = 9
        t = np.linspace(0, 1, n)
        yc = 0.45 - 0.08 * np.sin(math.pi * t) + 0.05 * np.sin(2 * math.pi * t * rng.uniform(1.2, 1.8) + rng.uniform(0, 6.3))
        tc = rng.uniform(0.35, 0.65)                          # where the second crosses the first
        mg = 0.25 / wm + 0.03
        for k in range(nr):                                   # the roots along the rim (the second crosses the first)
            sg = 1 if k == 0 else -1
            x = (mg + (1 - 2 * mg) * t + rng.normal(0, 0.008, n)) * W
            y = (yc + sg * 0.11 * np.sin(0.5 * math.pi * (t - tc) / max(tc, 1 - tc)) * (nr - 1)) * Hh
            r0 = rng.uniform(0.19, 0.25) if k == 0 else rng.uniform(0.15, 0.2)
            zz = sg * 0.35 * r0 * np.cos(0.5 * math.pi * (t - tc) / max(tc, 1 - tc)) * (nr - 1)   # (out of phase)
            ctrl = np.column_stack([x, y, zz * ppm])
            if k == 1:                                        # (the second runs the other way)
                ctrl = ctrl[::-1].copy()
            dx = 1.0 if ctrl[-1, 0] > ctrl[0, 0] else -1.0
            keep = (ctrl[:, 0] - ctrl[0, 0]) * dx <= abs(ctrl[-1, 0] - ctrl[0, 0]) - (0.42 + r0) * ppm
            ctrl = ctrl[keep]
            xl, yl, zl = ctrl[-1]                             # it pours over the rim at its end, at full thickness
            dy = Hh - yl + 0.25 * ppm
            drop = np.array([[xl + dx * 0.2 * ppm, yl + 0.3 * dy, zl], [xl + dx * 0.32 * ppm, yl + 0.65 * dy, zl],
                             [xl + dx * 0.38 * ppm, Hh + 0.25 * ppm, zl]])
            drop[:, :2] += rng.normal(0, 0.03 * ppm, (3, 2))
            ctrl = np.concatenate([ctrl, drop])
            D = RT.open_root(ctrl[:, :2], r0, 0.32 * r0, 0.08 * r0, tip=(0.0, 0.01), emerge=True, zdive=None, tip_r=1.0)
            K = len(ctrl)
            D[:, 2] += np.interp(np.linspace(0, K - 1, len(D)), np.arange(K), ctrl[:, 2])
            dense.append(D)
        A = dense[0]
        nd = int(rng.integers(2, 4)) if nr == 2 else int(rng.integers(2, 5))
        for j, f in enumerate(np.sort(rng.uniform(0.15, 0.62, nd))):  # short roots dropping over the rim
            q = dense[int(rng.integers(len(dense)))]
            n_ = len(q) - 1
            p = q[int(f * n_)]
            tg = q[min(int(f * n_) + 3, n_), :2] - q[max(int(f * n_) - 3, 0), :2]
            h0 = math.atan2(tg[1], tg[0]) + rng.choice([-1, 1]) * math.radians(rng.uniform(35, 60))
            h0 = math.atan2(max(abs(math.sin(h0)), 0.6), math.cos(h0))   # (always toward the pit, slanted)
            L = (Hh - p[1]) / ppm * 1.5 + 0.3
            ctrl = RT.walk(p[:2], h0, L, step=(0.15, 0.25), wig=10, pull=0.0)
            ctrl = ctrl + np.column_stack([np.zeros(len(ctrl)), np.cumsum(np.full(len(ctrl), 0.06 * ppm))])  # (droop)
            C = RT.open_root(ctrl, min(p[3] / ppm * rng.uniform(0.6, 0.8), 0.17), p[2] / ppm, 0.03, tip=(0.0, 0.01),
                             emerge=False, tip_r=1.0)
            dense.append(C)
        def inside(D):
            m = D[:, 3] > 0.3
            return not ((D[m, 0] - D[m, 3] < 4).any() or (D[m, 0] + D[m, 3] > W - 4).any() or (D[m, 1] - D[m, 3] < 4).any())
        if not all(inside(D) for D in dense):
            continue
        for _ in range(int(rng.integers(1, 3))):              # forks back onto the floor (away from the pit)
            C = RT.fork(A, 1, ang=(25, 40), length=(0.5, 0.8), zbase=0.0, zamp=0.03, zdive=0.5, tip=(0.4, 0.4), tip_r=0.2,
                        wig=9)
            if inside(C) and (C[:, 1] + C[:, 3] < Hh - 4).all() and C[-1, 1] < C[0, 1] - 0.15 * ppm:
                dense.append(C)
        for D in dense:
            RT.add(D)
        return F, RT, rng
    raise SystemExit("den_roots: no rim decal fits %d" % i)


def decal_image(F, RT, seed):
    col, mask, sh, deep, _ = shade(F, RT, seed, earth=False)
    ppm = F.ppm
    cast = blur((sh & ~mask).astype(np.float32), 0.012 * ppm, False)
    ring = smooth(deep / 0.6) * (~mask)
    sa = np.clip(np.maximum(0.47 * cast, 0.4 * ring), 0, 0.5)
    alpha = np.where(mask, 1.0, sa).astype(np.float32)
    rgb = np.where(mask[..., None], col, rgbf(PAL["shadow"])[None, None, :])
    pa = reduce(rgb * alpha[..., None])
    a = reduce(alpha)
    rgb = pa / np.maximum(a[..., None], 1e-6)
    return np.concatenate([to8(rgb), to8(a)[..., None]], -1)


def pack(sizes, aw=ATLAS_W):
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])
    x, y, shelf, rects = PAD, PAD, 0, {}
    for i in order:
        w, h = sizes[i]
        if x + w + PAD > aw:
            x, y, shelf = PAD, y + shelf + PAD, 0
        rects[i] = (x, y, w, h)
        x += w + PAD
        shelf = max(shelf, h)
    hgt = 1 << int(math.ceil(math.log2(y + shelf + PAD)))
    return [rects[i] for i in range(len(sizes))], hgt


def build_decals(out):
    items = []
    for i, (wm, hm) in enumerate(WALLS):
        F, RT, _ = decal_wall(i, wm, hm)
        items.append(("wall", i, wm, hm, decal_image(F, RT, seed_of("den_roots", "wall_shade", i, VERSION)), [0.5, 0.0]))
    for i, (wm, hm) in enumerate(RIMS):
        F, RT, _ = decal_rim(i, wm, hm)
        items.append(("rim", i, wm, hm, decal_image(F, RT, seed_of("den_roots", "rim_shade", i, VERSION)), [0.5, 1.0]))
    rects, ah = pack([(it[4].shape[1], it[4].shape[0]) for it in items])
    atlas = np.zeros((ah, ATLAS_W, 4), np.uint8)
    dec = []
    for (kind, v, wm, hm, img, anc), (x, y, w, h) in zip(items, rects):
        atlas[y:y + h, x:x + w] = img
        dec.append({"kind": kind, "variant": v, "rect": [x, y, w, h], "metres": [wm, hm], "anchor": anc})
    Image.fromarray(atlas, "RGBA").save(os.path.join(out, "bank_decals.png"), optimize=False, compress_level=9)
    man = {"by": "tools/look/den_roots.py (painted from nothing; no outside source)", "version": VERSION,
           "size": [ATLAS_W, ah], "px_per_m": DEC_PPM, "light": [round(float(c), 4) for c in L2],
           "light_note": "painted from the rect's upper left (toward the light, image x right / y down); keep a decal's "
                         "turn within about +-60 degrees",
           "alpha": "straight; roots and their ink >= 0.6 (alpha scissor 0.6), the soft contact shadow 0.2-0.55 "
                    "(rgb = palette shadow), 0 elsewhere",
           "kinds": {"wall": "roots enter at the rect's TOP edge at full thickness (they continue into the bank) come "
                             "down and turn to lie along the floor; anchor = the top edge's middle",
                     "rim": "roots draped along a pit's rim near the top, short roots run off the BOTTOM edge at full "
                            "thickness (into the pit); anchor = the bottom edge's middle"},
           "anchor": "[fx, fy] in the rect (0..1, x right, y down)", "decals": dec}
    with open(os.path.join(out, "bank_decals.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1)


# ---- the floor decals (floor_decals.png): long floor roots, the camera-side frame masses, whole pits --------------------
# FROM den_boss.png (the two pits on the right half: a lit earth lip, a dark slate far wall falling to black, roots
# pouring over the rims; the long roots crossing the floor) and den_room.png (the dark root masses along the frame's
# bottom). The pit is painted in plan for the play camera (looking image-up, 62 degrees down).
FL_PPM = 128                # the floor atlas, px per metre (fields drawn at FL_PPM * S)
FL_ATLAS_W = 4096
FLOORS = [(2.4, 3.8), (3.1, 4.9), (2.8, 4.4), (3.1, 6.2), (3.0, 4.6), (3.1, 6.0)]   # (across, along) m
FLOORS_S = [(2.4, 3.8), (3.1, 4.9), (3.0, 4.4)]   # the same lit for the camera-side banks (image light from below)
FRAMES = [(4.0, 2.0), (4.8, 2.3), (3.4, 1.8), (4.4, 2.4)]                          # (along the wall, out) m
PITS = 3
PIT_M = 8.4                 # a pit's square rect, the mouth centred (room for the lip, its shadow and the root starts)
MOUTH_R = 2.6
COT = 1.0 / math.tan(math.radians(62.0))      # a point d m down the far wall shows COT d (0.53 d) lower in plan
WALL_D = 2.4                # m of far wall seen before the black
FPAL = {
    "lip_lit":  "#7b583c",  # the pit lip facing the light (upper left)
    "lip":      "#5a4030",
    "lip_dk":   "#33261f",  # the lip turned from the light, and its inner roll
    "slate_hi": "#4d4d55",  # the far wall's ledges
    "slate":    "#34343c",
    "slate_dk": "#202027",
    "crack":    "#0e0d11",
    "void":     "#030303",
    "frame_gap": "#0a0909", # the frame masses' gaps against the bank
}


def arc(D): return np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(D[:, 0]), np.diff(D[:, 1])))])


def wrapa(a): return (a + math.pi) % (2 * math.pi) - math.pi


def inside_rect(D, W, Hh, top=False, bottom=True):
    """A root's dense rows stay off the rect's sides (and its top unless it enters there, its bottom unless allowed)."""
    m = D[:, 3] > 0.3
    bad = (D[m, 0] - D[m, 3] < 4).any() or (D[m, 0] + D[m, 3] > W - 4).any()
    if bottom:
        bad = bad or (D[m, 1] + D[m, 3] > Hh - 4).any()
    if not top:
        bad = bad or (D[m, 1] - D[m, 3] < 4).any()
    return not bad


def tip_sink(D, frac=0.18, zd=0.8):
    """The tip sinks into the earth over its last frac of the length only (to zd x r below 0)."""
    s = arc(D)
    w = smooth((s - (1 - frac) * s[-1]) / max(frac * s[-1], 1.0))
    D[:, 2] = D[:, 2] * (1 - w) - w * zd * D[:, 3]
    return D


def decal_floor(i, wm, hm, tag="floor"):
    """The bank spilling onto the floor, in the wall decals' language at floor length: 2-4 thick roots enter the TOP
    edge together (out of the bank's foot, 0.4-0.6 m across, high where they leave it), fan out down the rect for 3-6 m
    crossing over and under one another (a braid, not a comb), lying ON the earth (not sunk), tapering to about 0.15 m
    and sinking at the tip; about half shed one fork the way a wall root does."""
    ppm = FL_PPM * S
    W, Hh = int(round(wm * FL_PPM)) * S, int(round(hm * FL_PPM)) * S
    for attempt in range(400):
        rng = np.random.default_rng(seed_of("den_roots", tag, i, attempt, VERSION, 3))
        F = Field(W, Hh, ppm, False)
        RT = Roots(F, rng)
        n = 2 if wm < 2.6 else int(rng.integers(2, 4))
        x0s = wm / 2 + np.sort(rng.uniform(-1, 1, n)) * min(0.55, 0.18 * n)        # (a mass at the bank's foot)
        xe = np.linspace(-1, 1, n) * (wm / 2 - 0.45) + rng.normal(0, 0.12, n)
        if n > 2 and rng.random() < 0.8:                       # (one pair swaps sides on the way: they cross)
            k = int(rng.integers(n - 1)); xe[k], xe[k + 1] = xe[k + 1], xe[k]
        xe += wm / 2
        rr = rng.uniform(0.2, 0.3, n); rr[int(rng.integers(n))] = rng.uniform(0.26, 0.3)
        dense, ok = [], True
        for k in range(n):
            r0 = float(rr[k])
            ly = rng.uniform(0.72, 0.96) * hm - 0.12              # the tip's y
            m = max(7, int((ly + 0.3) / 0.42) + 1)
            u = np.linspace(0, 1, m)
            fan = smooth(np.clip(u / 0.7, 0, 1))
            x = x0s[k] + (xe[k] - x0s[k]) * fan + 0.3 * np.sin(2 * math.pi * rng.uniform(0.6, 1.1) * u + rng.uniform(0, 6.3)) * u
            C = np.column_stack([x, -0.3 + u * (ly + 0.3)])
            C[1:-1] += rng.normal(0, 0.045, (m - 2, 2))           # (hand jitter, the ends kept)
            D = RT.open_root(C * ppm, r0, 0.0, 0.05, tip=(0.01, 0.02), emerge=False, zdive=None, tip_r=1.0)
            s = arc(D)
            uu = s / s[-1]
            D[:, 3] *= 1.0 - (1.0 - 0.075 / r0) * uu ** 0.85      # (0.4-0.6 m at the bank to ~0.15 m at the end)
            D[:, 2] += (1 - smooth(s / (1.0 * ppm))) * 0.2 * ppm  # (high where it leaves the bank, down onto the floor)
            D = tip_sink(D, frac=0.14, zd=0.5)
            if not inside_rect(D, W, Hh, top=True):
                ok = False; break
            dense.append(D)
        if not ok:
            continue
        for D in list(dense):
            nf, tries = int(rng.random() < 0.55), 0           # (a fork or none: more read as a claw)
            while nf and tries < 16:
                tries += 1
                C = RT.fork(D, 1, ang=(18, 32), ratio=(0.45, 0.6), length=(0.9, 1.6), zbase=0.0, zamp=0.04, zdive=0.5,
                            tip=(0.4, 0.4), tip_r=0.2, wig=9)
                if inside_rect(C, W, Hh) and C[0, 1] > 0.6 * ppm:
                    dense.append(C); nf -= 1
        for D in dense:
            RT.add(D)
        return F, RT
    raise SystemExit("den_roots: no floor decal fits %d" % i)


def decal_frame(i, wm, hm):
    """The camera-side frame: a dark tangle of open roots in the top metre, 2-3 entering at the top edge (the bank),
    2-4 reaching down 1-1.5 m into the room; then darkened by depth and the top gaps filled near black."""
    ppm = FL_PPM * S
    W, Hh = int(round(wm * FL_PPM)) * S, int(round(hm * FL_PPM)) * S
    rng = np.random.default_rng(seed_of("den_roots", "frame", i, VERSION))
    F = Field(W, Hh, ppm, False)
    RT = Roots(F, rng)
    dense = []
    n, tries = int(rng.integers(10, 17)), 0
    while len(dense) < n and tries < 600:                     # the open roots along x: arches out of the bank's
        tries += 1                                            # foot and back into it (both ends under the dark band)
        r = rng.uniform(0.08, 0.22)
        span = rng.uniform(1.2, 2.8)
        x0 = rng.uniform(0.15, wm - 0.15 - span)
        dep = rng.uniform(0.45, 1.0)
        u = np.linspace(0, 1, 9)
        y = 0.12 + (dep - 0.12) * np.sin(math.pi * u) ** rng.uniform(0.6, 1.0)
        x = x0 + span * (u + rng.uniform(-0.1, 0.1) * np.sin(2 * math.pi * u))
        if rng.random() < 0.5:
            x = x[::-1]
        ctrl = np.column_stack([x, y]) * ppm
        ctrl[1:-1] += rng.normal(0, 0.04 * ppm, (7, 2))
        D = tip_sink(RT.open_root(ctrl, r, rng.uniform(0.0, 0.25), 0.06, tip=(0.15, 0.25), emerge=True, zdive=None,
                                  tip_r=0.6), 0.12, 1.2)
        if inside_rect(D, W, Hh) and D[:, 1].max() < 1.25 * ppm:
            dense.append(D)
    m, tries = int(rng.integers(2, 4)), 0
    while m and tries < 200:                                  # entering at the top edge (out of the bank)
        tries += 1
        ctrl = RT.walk((rng.uniform(0.4, wm - 0.4) * ppm, -0.3 * ppm), math.pi / 2 + rng.normal(0, 0.35),
                       rng.uniform(1.3, 1.9), step=(0.3, 0.5), wig=9, pull=0.2)
        D = RT.open_root(ctrl, rng.uniform(0.2, 0.3), 0.25, 0.05, tip=(0.4, 0.6), emerge=False, zdive=0.8, tip_r=0.2)
        if inside_rect(D, W, Hh, top=True):
            dense.append(D); m -= 1
    m, tries = int(rng.integers(2, 5)), 0
    while m and tries < 300:                                  # reaching down into the room
        tries += 1
        ctrl = RT.walk((rng.uniform(0.3, wm - 0.3) * ppm, rng.uniform(0.45, 0.9) * ppm),
                       math.pi / 2 + rng.uniform(-0.5, 0.5), rng.uniform(1.0, 1.5), step=(0.25, 0.4), wig=10, pull=0.15)
        D = tip_sink(RT.open_root(ctrl, rng.uniform(0.09, 0.16), 0.08, 0.04, tip=(0.35, 0.5), emerge=True, zdive=None,
                                  tip_r=0.25), 0.15)
        if inside_rect(D, W, Hh):
            dense.append(D); m -= 1
    for D in dense:
        RT.add(D)
    img = decal_image(F, RT, seed_of("den_roots", "frame_shade", i, VERSION)).astype(np.float32) / 255.0
    rgb, a = img[..., :3], img[..., 3]
    h, w = a.shape
    y_m = (np.arange(h) + 0.5) / FL_PPM
    x_m = (np.arange(w) + 0.5) / FL_PPM
    rgb = rgb * (0.12 + 0.24 * smooth(y_m / 0.9))[:, None, None]
    ph = rng.uniform(0, 2 * math.pi, 3)
    yg = 0.275 + 0.075 * (0.55 * np.sin(x_m * 1.7 + ph[0]) + 0.3 * np.sin(x_m * 4.1 + ph[1]) + 0.15 * np.sin(x_m * 9.3 + ph[2]))
    f = np.clip((yg[None, :] - y_m[:, None]) * FL_PPM + 0.5, 0, 1)
    an = a + (1 - a) * f
    rgb = (rgb * a[..., None] + rgbf(FPAL["frame_gap"]) * ((1 - a) * f)[..., None]) / np.maximum(an, 1e-6)[..., None]
    return np.concatenate([to8(rgb), to8(an)[..., None]], -1)


def fnz(T, x_m, y_m, per_m, off=0.0):
    """Noise over metres, about per_m features per metre (T = pnoise(1024, 24, 40): 32 texels a feature)."""
    return tex(T, x_m * per_m * 32.0 + off, y_m * per_m * 32.0 + 0.7 * off)


def pit_mouth(i):
    rng = np.random.default_rng(seed_of("den_roots", "pit_mouth", i, VERSION))
    amp = {2: (0.04, 0.06), 3: (0.025, 0.04), 5: (0.012, 0.02), 9: (0.005, 0.008)}
    harm = [[k, round(float(rng.uniform(*amp[k])), 4), round(float(rng.uniform(0, 2 * math.pi)), 4)] for k in (2, 3, 5, 9)]
    lw = [round(float(rng.uniform(0, 2 * math.pi)), 4) for _ in range(2)]
    return harm, lw


def mouth_r(harm, th):
    return MOUTH_R * (1 + sum(a * np.sin(k * th + p) for k, a, p in harm))


def lip_w(lw, th):
    return 0.4 + 0.1 * (0.6 * np.sin(3 * th + lw[0]) + 0.4 * np.sin(7 * th + lw[1]))


def decal_pit(i):
    """A whole pit in plan: the lit earth lip, the far wall (slate bands falling to black, seen 62 degrees down), the
    void, a soft contact shadow, and 3-6 roots from the earth outside the lip pouring over it into the dark."""
    ppm = FL_PPM * S
    N = int(round(PIT_M * FL_PPM)) * S
    half = N / 2 / ppm
    harm, lw = pit_mouth(i)
    rng = np.random.default_rng(seed_of("den_roots", "pit", i, VERSION))
    T = [pnoise(1024, 24, 40, rng) for _ in range(6)]
    c = (np.arange(N, dtype=np.float32) + 0.5) / ppm - half
    X, Y = np.meshgrid(c, c)
    R = np.hypot(X, Y) + 1e-6
    TH = np.arctan2(Y, X)
    nx, ny = X / R, Y / R
    L0 = nx * L2[0] + ny * L2[1]                              # the outward direction toward the light
    sd = R - mouth_r(harm, TH) + 0.035 * fnz(T[0], X, Y, 2.5)
    lwv = lip_w(lw, TH) + 0.04 * fnz(T[1], X, Y, 2.0, 50.0)
    M = sd < 0
    # the lip: toned by its outward face to the light, flecked, a dark inner roll, ink at the mouth's edge
    l = L0 + 0.14 * fnz(T[2], X, Y, 4.0)
    lip = np.where((l > 0.25)[..., None], rgbf(FPAL["lip_lit"]), np.where((l < -0.3)[..., None], rgbf(FPAL["lip_dk"]),
                                                                          rgbf(FPAL["lip"])))
    fl = fnz(T[3], X, Y, 9.0)
    lip = np.where(((fl > 1.7) & (l > -0.3))[..., None], np.where((l > 0.25)[..., None], rgbf(PAL["edge"]) * 0.82,
                                                                  rgbf(FPAL["lip_lit"])), lip)
    roll = sd < 0.09 + 0.03 * fnz(T[4], X, Y, 3.0)
    lip = np.where(roll[..., None], rgbf(FPAL["lip_dk"]), lip)
    lip = np.where((sd < 0.022)[..., None], rgbf(PAL["ink"]), lip)
    a_lip = np.clip((lwv - sd) / 0.04 + 0.5, 0, 1)
    # the far wall: each column's first mouth row is the far edge; d m down shows COT d lower
    Ms = R < mouth_r(harm, TH)
    has = Ms.any(0)
    yn = np.where(has, np.argmax(Ms, 0), N)
    d = (np.arange(N)[:, None] - yn[None, :]) / ppm / COT
    v = 1 - d / WALL_D + 0.16 * fnz(T[5], X / 3.0, d, 2.0, 20.0) + 0.08 * fnz(T[4], X / 2.0, d, 5.0, 40.0)
    wall = np.where((v > 0.72)[..., None], rgbf(FPAL["slate_hi"]), np.where((v > 0.42)[..., None], rgbf(FPAL["slate"]),
                    np.where((v > 0.16)[..., None], rgbf(FPAL["slate_dk"]), rgbf(FPAL["void"]))))
    crack = (np.abs(fnz(T[2], X / 1.6, d, 2.2, 90.0)) < 0.04) & (v > 0.16)
    wall = np.where((crack | (d < 0.07))[..., None], np.where((d < 0.07)[..., None], rgbf(FPAL["slate_dk"]),
                                                               rgbf(FPAL["crack"])), wall)
    wall = np.where((sd > -0.012)[..., None], rgbf(PAL["ink"]), wall)
    # the contact shadow outside the lip, stronger lower right, gone before the rect's edge
    e = sd - lwv
    sa = 0.5 * (1 - smooth(e / 0.75)) * (0.85 + 0.35 * np.clip(-L0, 0, 1))
    em = half - np.maximum(np.abs(X), np.abs(Y))
    sa = np.clip(sa, 0, 0.55) * smooth((em - 0.05) / 0.3)
    shc = rgbf(PAL["shadow"])
    A = np.where(M, 1.0, a_lip + sa * (1 - a_lip)).astype(np.float32)
    P = np.where(M[..., None], wall, lip * a_lip[..., None] + shc * (sa * (1 - a_lip))[..., None]).astype(np.float32)
    # the roots (their own field): out of the earth 0.4-1 m outside the lip, over the rim, drooping into the dark
    F = Field(N, N, ppm, False)
    RT = Roots(F, rng)
    def rmo(th): return float(mouth_r(harm, th))
    def path(p0, h, Lin):
        pts, lin = [np.array(p0, float)], 0.0
        for _ in range(200):
            p = pts[-1]
            st = rng.uniform(0.2, 0.3)
            if math.hypot(*p) < rmo(math.atan2(p[1], p[0])):
                dd = wrapa(math.pi / 2 - h)
                if abs(dd) < 2.2:                            # (into the hole and down the far wall; the near side
                    h += float(np.clip(dd, -0.3, 0.3))       # hides behind its lip)
                lin += st
                if lin > Lin:
                    break
            else:
                h += 0.13 * wrapa(math.atan2(-p[1], -p[0]) - h)
            h += rng.normal(0, math.radians(5))
            pts.append(p + st * np.array([math.cos(h), math.sin(h)]))
        return np.array(pts)
    nr = int(rng.integers(4, 7))
    ths = rng.uniform(0, 2 * math.pi) + np.arange(nr) * 2 * math.pi / nr + rng.normal(0, 0.25, nr)
    dense = []
    for th in ths:
        for _ in range(20):
            r = rng.uniform(0.12, 0.24)
            rim = rmo(th) + float(lip_w(lw, th))
            dmax = min(1.0, (half - 0.15 - r) / max(abs(math.cos(th)), abs(math.sin(th))) - rim)
            if dmax < 0.4:
                th += 0.3; continue
            rho = rim + rng.uniform(0.4, dmax)
            p0 = rho * np.array([math.cos(th), math.sin(th)]) + half
            near = math.sin(th) > 0.5
            ctrl = path(p0 - half, th + math.pi + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9), rng.uniform(0.45, 0.6) if near else
                        rng.uniform(0.9, 1.4)) + half
            D = RT.open_root(ctrl * ppm, r, -0.1 * r, 0.03, tip=(0.35, 0.5), emerge=True, zdive=None, tip_r=0.35)
            s = arc(D)
            D[:, 2] -= (1 - smooth(s / (0.9 * ppm))) * 0.6 * D[:, 3]     # (a long rise out of the earth)
            if not inside_rect(D, N, N):
                continue
            dense.append(D)
            if rng.random() < 0.6:                            # a thinner strand split off before the rim
                s = arc(D)
                ins = np.nonzero(np.hypot(D[:, 0] / ppm - half, D[:, 1] / ppm - half) <
                                 np.array([rmo(math.atan2(q[1] / ppm - half, q[0] / ppm - half)) for q in D]) + 0.1)[0]
                if len(ins) and s[ins[0]] > 0.7 * ppm:
                    j = int(np.searchsorted(s, rng.uniform(0.5 * ppm, s[ins[0]] - 0.15 * ppm)))
                    tg = D[min(j + 4, len(D) - 1), :2] - D[max(j - 4, 0), :2]
                    hf = math.atan2(tg[1], tg[0]) + rng.choice([-1, 1]) * math.radians(rng.uniform(30, 45))
                    C = path(D[j, :2] / ppm - half, hf, rng.uniform(0.4, 0.5) if near else rng.uniform(0.7, 1.1)) + half
                    C = RT.open_root(C * ppm, D[j, 3] / ppm * rng.uniform(0.5, 0.65), 0.03, 0.02, tip=(0.4, 0.5),
                                     emerge=False, zdive=None, tip_r=0.3)
                    kk = smooth(arc(C) / (0.4 * ppm))
                    C[:, 2] = (1 - kk) * D[j, 2] + kk * C[:, 2]
                    if inside_rect(C, N, N):
                        dense.append(C)
            break
    for D in dense:
        RT.add(D)
    col, mask, sh, deep, _ = shade(F, RT, seed_of("den_roots", "pit_shade", i, VERSION), earth=False)
    cast = blur((sh & ~mask).astype(np.float32), 0.012 * ppm, False)
    rs = np.clip(np.maximum(0.47 * cast, 0.4 * smooth(deep / 0.6) * (~mask)), 0, 0.5) * smooth((em - 0.05) / 0.3)
    P = P * (1 - rs[..., None]) + shc * rs[..., None]
    A = A + rs * (1 - A)
    sv = 0.55 - 0.25 * ny                                     # the fade into the dark: 0.8 m far side, 0.3 m near
    fade = 1 - smooth(np.clip(-sd, 0, None) / sv)
    P = np.where(mask[..., None], col * fade[..., None], P)
    A = np.where(mask, 1.0, A)
    pa, a = reduce(P), reduce(A)
    rgb = pa / np.maximum(a[..., None], 1e-6)
    rlo, rhi = float(mouth_r(harm, np.linspace(0, 2 * math.pi, 3600)).min()), float(mouth_r(harm, np.linspace(0, 2 * math.pi, 3600)).max())
    return np.concatenate([to8(rgb), to8(a)[..., None]], -1), harm, (rlo, rhi), float(lip_w(lw, np.linspace(0, 6.3, 999)).max())


def build_floor(out):
    items = []
    for i, (wm, hm) in enumerate(FLOORS):
        F, RT = decal_floor(i, wm, hm)
        items.append(dict(kind="floor", variant=i, metres=[wm, hm], anchor=[0.5, 0.0],
                          img=decal_image(F, RT, seed_of("den_roots", "floor_shade", i, VERSION))))
        print(f"  floor {i}: {len(RT.send)} roots")
    global L2
    keep = L2
    L2 = np.array([keep[0], -keep[1]])                       # (a camera-side bank's roots run image-down = north: their
    try:                                                      # light painted from the image's lower left, mirrored in game)
        for i, (wm, hm) in enumerate(FLOORS_S):
            F, RT = decal_floor(i, wm, hm, "floor_s")
            items.append(dict(kind="floor_s", variant=i, metres=[wm, hm], anchor=[0.5, 0.0],
                              light=[round(float(c), 4) for c in L2],
                              img=decal_image(F, RT, seed_of("den_roots", "floor_s_shade", i, VERSION))))
            print(f"  floor_s {i}: {len(RT.send)} roots")
    finally:
        L2 = keep
    for i, (wm, hm) in enumerate(FRAMES):
        items.append(dict(kind="frame", variant=i, metres=[wm, hm], anchor=[0.5, 0.0], img=decal_frame(i, wm, hm)))
        print(f"  frame {i}")
    for i in range(PITS):
        img, harm, (rlo, rhi), lwm = decal_pit(i)
        items.append(dict(kind="pit", variant=i, metres=[PIT_M, PIT_M], anchor=[0.5, 0.5], img=img, mouth_r=MOUTH_R,
                          mouth_harm=harm, mouth_r_range=[round(rlo, 3), round(rhi, 3)], lip_m=round(lwm, 3)))
        print(f"  pit {i}: mouth r {rlo:.2f}-{rhi:.2f} m")
    rects, ah = pack([(it["img"].shape[1], it["img"].shape[0]) for it in items], FL_ATLAS_W)
    atlas = np.zeros((ah, FL_ATLAS_W, 4), np.uint8)
    dec = []
    for it, (x, y, w, h) in zip(items, rects):
        atlas[y:y + h, x:x + w] = it.pop("img")
        dec.append({"kind": it.pop("kind"), "variant": it.pop("variant"), "rect": [x, y, w, h], **it})
    Image.fromarray(atlas, "RGBA").save(os.path.join(out, "floor_decals.png"), optimize=False, compress_level=9)
    man = {"by": "tools/look/den_roots.py build floor (painted from nothing; no outside source)", "version": VERSION,
           "size": [FL_ATLAS_W, ah], "px_per_m": FL_PPM, "light": [round(float(c), 4) for c in L2],
           "light_note": "painted from the rect's upper left (toward the light, image x right / y down); laid flat on "
                         "the floor, image up = north (the play camera looks north, 62 degrees down); keep a floor "
                         "decal's turn within about +-60 degrees, never turn a pit",
           "alpha": "straight; roots, lip, pit mouth and the frame's gap fill >= 0.6 (alpha scissor 0.6; the whole mouth "
                    "and the frame's top band are 1), the soft contact shadow 0.2-0.55 (rgb = palette shadow), 0 "
                    "elsewhere",
           "kinds": {"floor": "the bank spilling onto the floor: 2-4 thick roots (0.4-0.6 m) enter the rect's TOP edge "
                              "(y = 0) together at full thickness (they continue into the bank: put the top edge on the "
                              "bank's foot), fan out down the rect crossing over and under, lying on the earth, tapering "
                              "to ~0.15 m and sinking at the tip, forking; anchor = the top edge's middle",
                     "floor_s": "the same for the camera-side banks (laid with the top edge south): painted with the "
                                "decal's own light (its 'light', the image's lower left), mirrored in game",
                     "frame": "a dark root mass for the camera-side wall line: the TOP edge (y = 0) sits against the "
                              "bank (the band above an irregular line 0.2-0.35 m down is opaque near black), roots reach "
                              "1-1.5 m toward the rect's bottom; darkened by depth (x 0.12 at the top to x 0.36 below "
                              "0.9 m); anchor = the top edge's middle",
                     "pit": "a whole pit painted in plan for the play camera: anchor = the mouth's centre (the rect's "
                            "centre); the mouth r(theta) = mouth_r * (1 + sum a sin(k theta + p)) over mouth_harm "
                            "[k, a, p] (theta = atan2(y, x), image x right / y down, metres from the centre), alpha 1 "
                            "over all of it (it covers the game's own traced hole: trace it inside mouth_r_range[0]); "
                            "the lip band lies up to lip_m outside the mouth, the contact shadow 0.75 m past that; "
                            "the near half of the mouth is black"},
           "anchor": "[fx, fy] in the rect (0..1, x right, y down)", "decals": dec}
    with open(os.path.join(out, "floor_decals.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1)


def floor_preview(out):
    """The floor kinds at the game's scale on a plain den floor (a scene, then every decal), then 1:1 crops."""
    atl = Image.open(os.path.join(out, "floor_decals.png")).convert("RGBA")
    man = json.load(open(os.path.join(out, "floor_decals.json"), encoding="utf-8"))
    floor = (0x5a, 0x3e, 0x2e)
    k = PREVIEW_PPM / FL_PPM
    def get(d, scale=k):
        x, y, w, h = d["rect"]
        c = atl.crop((x, y, x + w, y + h))
        return c if scale == 1 else c.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    by = {}
    for d in man["decals"]:
        by.setdefault(d["kind"], []).append(d)
    G = 16
    Wd = int(24 * PREVIEW_PPM)
    # the scene: a bank strip on top, floor roots off it, two pits on the right, frame masses along the bottom
    sh_ = int(14 * PREVIEW_PPM)
    sc = Image.new("RGBA", (Wd, sh_), floor + (255,))
    bank_p = os.path.join(out, "bank_albedo.png")
    top = int(1.2 * PREVIEW_PPM)
    if os.path.exists(bank_p):
        b = Image.open(bank_p).convert("RGB")
        t = b.crop((0, 0, BANK_PX, BANK_PX)).resize((int(BANK_M * PREVIEW_PPM),) * 2, Image.LANCZOS)
        for x in range(0, Wd, t.width):
            sc.paste(t.crop((0, t.height - top, t.width, t.height)), (x, 0))
    for j, x in enumerate((1.0, 3.6, 6.4, 9.0)):
        d = by["floor"][j % len(by["floor"])]
        c = get(d)
        sc.alpha_composite(c, (int(x * PREVIEW_PPM), top))
    for d, (x, y) in zip(by["pit"], ((11.5, 1.6), (16.0, 5.2))):
        sc.alpha_composite(get(d), (int(x * PREVIEW_PPM), int(y * PREVIEW_PPM)))
    bot = int(0.8 * PREVIEW_PPM)
    sc.paste((10, 9, 9, 255), (0, sh_ - bot, Wd, sh_))
    x = 0
    for j in range(8):
        c = get(by["frame"][j % len(by["frame"])]).rotate(180)
        sc.alpha_composite(c, (x, sh_ - bot - c.height))
        x += c.width - int(0.4 * PREVIEW_PPM)
        if x > Wd:
            break
    # every decal, shelf-laid
    dims = [get(d) for d in man["decals"]]
    rows, cx, cy, shl = [], G, 0, 0
    for c in dims:
        if cx + c.width + G > Wd:
            cx, cy, shl = G, cy + shl + G, 0
        rows.append((c, cx, cy))
        cx += c.width + G
        shl = max(shl, c.height)
    dh = cy + shl + G
    fl = Image.new("RGBA", (Wd, dh), floor + (255,))
    for c, x, y in rows:
        fl.alpha_composite(c, (x, y + G // 2))
    # 1:1 (128 px/m): a floor root's top 3.5 m, a frame, a pit
    crops = []
    for kind, i in (("floor", 3), ("frame", 1), ("pit", 0)):
        c = get(by[kind][i], 1)
        bg = Image.new("RGBA", c.size, floor + (255,))
        bg.alpha_composite(c)
        crops.append(bg.convert("RGB").crop((0, 0, c.width, min(c.height, int(3.5 * FL_PPM)) if kind == "floor" else c.height)))
    ch = max(c.height for c in crops)
    sheet = Image.new("RGB", (Wd, sh_ + G + dh + ch + G), (24, 22, 22))
    sheet.paste(sc.convert("RGB"), (0, 0))
    sheet.paste(fl.convert("RGB"), (0, sh_ + G))
    x = G
    for c in crops:
        if x + c.width > Wd:
            break
        sheet.paste(c, (x, sh_ + G + dh))
        x += c.width + G
    sheet.save(os.path.join(out, "floor_preview.jpg"), quality=90)


# ---- the pit set (pit_decals.png): big pits and shallow hollows, painted at native size ---------------------------------
# FROM den_boss.png (the two pits on the right half: charcoal slate throats in chunky ledges, never one black disk; roots
# running along the rims and over the mouths; the dark sunken hollows ringed by roots, lower right) in the floor pits'
# language (decal_pit). A big pit is painted at the game holes' own size (mean r 5.2-5.8 m), so the game's angle-by-angle
# fit stretches it about 1; a hollow is a walkable dish, no hole.
PIT_VERSION = 1             # (the pit set's own seeds: VERSION and the floor atlas untouched)
PT_PPM = 128                # px per metre (fields drawn at PT_PPM * S)
PT_ATLAS_W = 4096
BIG_R = 5.5                 # the big pit's mean mouth radius, m
BIG_M = 15.0                # its square rect (the lip, its contact shadow and the root starts)
BIGPITS = 2
BIG_WALL_D = 9.0            # m of far wall (in depth; the shelves add plan width, not depth) before the black
HOLLOWS = [1.4, 1.75, 2.05, 2.4]   # the hollows' mean dish radius, m
HB_BOT, HB_DK, HB_LIT = 0.74, -0.13, 0.035   # a hollow's steps: the dark bottom (depth share), the dark slope, the lit one
PPAL = {
    "ledge_lit": "#6b686c",  # a shelf's front edge catching a little light
    "slate_ddk": "#17171c",  # the first terrace of the fall to black
    "slate_k":  "#0c0c10",   # the second (then the void)
    "dish_lit": "#50392b",   # a hollow's inner slope facing the light (lower right): a step above the rest
    "dish":     "#3d2c22",   # damp earth, the bowl's middle step
    "dish_dk":  "#2c1f18",   # the bottom and the inner slope turned from the light (the darkest step)
    "crest_lit": "#694a35",  # the floor's turn into the bowl on the upper left, a touch lit (the den floor ~ #604432)
    "bone":     "#6e6555",   # a bone in a hollow's bottom (in its shade)
    "bone_lit": "#8f8470",
    "leaf":     "#8b5531",
    "leaf_hi":  "#a66a3b",
    "leaf_dk":  "#5d3820",
}


def pt_mouth(tag, i, amp):
    rng = np.random.default_rng(seed_of("den_roots", tag, i, PIT_VERSION))
    harm = [[k, round(float(rng.uniform(*amp[k])), 4), round(float(rng.uniform(0, 2 * math.pi)), 4)] for k in sorted(amp)]
    lw = [round(float(rng.uniform(0, 2 * math.pi)), 4) for _ in range(3)]
    return harm, lw


def pt_r(r0, harm, th):
    return r0 * (1 + sum(a * np.sin(k * th + p) for k, a, p in harm))


def pt_grid(rect_m, ppm):
    N = int(round(rect_m * PT_PPM)) * S
    half = N / 2 / ppm
    c = ((np.arange(N, dtype=np.float32) + 0.5) / ppm - half).astype(np.float32)
    X, Y = np.meshgrid(c, c)
    return N, half, c, X, Y


def pour_path(rng, p0, h, Lin, rmo, wig=5.0, step=(0.2, 0.3), pull=0.13):
    """Control points (m, centred): in from the earth toward the mouth, over the rim, then down the wall (image-down)
    for Lin m inside (a near-side root keeps on and hides behind its lip)."""
    pts, lin = [np.array(p0, float)], 0.0
    for _ in range(400):
        p = pts[-1]
        st = rng.uniform(*step)
        if math.hypot(*p) < rmo(math.atan2(p[1], p[0])):
            dd = wrapa(math.pi / 2 - h)
            if abs(dd) < 2.2:
                h += float(np.clip(dd, -0.3, 0.3))
            lin += st
            if lin > Lin:
                break
        else:
            h += pull * wrapa(math.atan2(-p[1], -p[0]) - h)
        h += rng.normal(0, math.radians(wig))
        pts.append(p + st * np.array([math.cos(h), math.sin(h)]))
    return np.array(pts)


def lift(D, ppm, run=0.9):
    """A long rise out of the earth over the first run m."""
    D[:, 2] -= (1 - smooth(arc(D) / (run * ppm))) * 0.6 * D[:, 3]
    return D


def no_pop(D, ppm, run=0.6):
    """Over its first run m a root only rises out of the earth: no bit of it pops up and sinks again (a stray stub)."""
    k = min(int(np.searchsorted(arc(D), run * ppm)) + 1, len(D))
    D[:k, 2] = np.minimum.accumulate(D[:k, 2][::-1])[::-1]
    return D


def decal_bigpit(i):
    """A big pit in plan at its own size: the lit earth lip, a far wall in slate risers and shelves (more of it showing,
    ledges catching a little light, cracks, black only in the deepest part), a soft contact shadow, 5-6 roots pouring
    over the rim, 2-3 running along it and 2-3 hanging across the mouth with their shadows on the wall below."""
    ppm = PT_PPM * S
    N, half, c, X, Y = pt_grid(BIG_M, ppm)
    harm, lw = pt_mouth("bigpit_mouth", i, {2: (0.025, 0.04), 3: (0.016, 0.026), 5: (0.008, 0.013), 9: (0.003, 0.005),
                                            14: (0.0015, 0.003)})
    rng = np.random.default_rng(seed_of("den_roots", "bigpit", i, PIT_VERSION))
    T = [pnoise(1024, 24, 40, rng) for _ in range(9)]
    R = np.hypot(X, Y) + 1e-6
    TH = np.arctan2(Y, X)
    MR = pt_r(BIG_R, harm, TH).astype(np.float32)
    nx, ny = X / R, Y / R
    L0 = nx * L2[0] + ny * L2[1]
    del nx
    sd = R - MR + 0.05 * fnz(T[0], X, Y, 0.7) + 0.02 * fnz(T[0], X, Y, 2.6, 30.0)
    def lipw(th): return 0.6 + 0.12 * (0.6 * np.sin(3 * th + lw[0]) + 0.4 * np.sin(5 * th + lw[1]))
    lwv = lipw(TH) + 0.05 * fnz(T[1], X, Y, 0.9, 50.0)
    M = sd < 0
    # the lip: the key side lit, the far side mid, its inner half turning dark into the roll, ink at the mouth's edge
    l = L0 + 0.12 * fnz(T[2], X, Y, 1.6)
    qq = sd / np.maximum(lwv, 0.1)
    lip = np.where((l > 0.22)[..., None], rgbf(FPAL["lip_lit"]),
                   np.where(((l < -0.3) & (qq < 0.5))[..., None], rgbf(FPAL["lip_dk"]), rgbf(FPAL["lip"])))
    fl = fnz(T[3], X, Y, 7.0)
    lip = np.where(((fl > 1.7) & (l > -0.3))[..., None], np.where((l > 0.22)[..., None], rgbf(PAL["edge"]) * 0.82,
                                                                  rgbf(FPAL["lip_lit"])), lip)
    lip = np.where((sd < 0.13 + 0.04 * fnz(T[4], X, Y, 2.0))[..., None], rgbf(FPAL["lip_dk"]), lip)
    lip = np.where((sd < 0.03)[..., None], rgbf(PAL["ink"]), lip)
    a_lip = np.clip((lwv - sd) / 0.05 + 0.5, 0, 1).astype(np.float32)
    del l, qq, fl
    e = sd - lwv
    sa = 0.5 * (1 - smooth(e / 0.9)) * (0.85 + 0.35 * np.clip(-L0, 0, 1))
    em = half - np.maximum(np.abs(X), np.abs(Y))
    sa = (np.clip(sa, 0, 0.55) * smooth((em - 0.05) / 0.35)).astype(np.float32)
    shc = rgbf(PAL["shadow"])
    Cp = (lip * a_lip[..., None] + shc * (sa * (1 - a_lip))[..., None]).astype(np.float32)
    A = (a_lip + sa * (1 - a_lip)).astype(np.float32)
    del lip, e, sa
    # each column's first mouth row is the far edge: t m below it in plan
    has = M.any(0)
    yn = np.where(has, np.argmax(M, 0), N)
    t = ((np.arange(N, dtype=np.float32)[:, None] - yn[None, :]) / ppm).astype(np.float32)

    # ---- the roots (their own field)
    F = Field(N, N, ppm, False)
    RT = Roots(F, rng)
    def rmo(th): return float(pt_r(BIG_R, harm, th))
    def room(th, r): return (half - 0.3 - r) / max(abs(math.cos(th)), abs(math.sin(th))) - (rmo(th) + float(lipw(th)))
    pour, along, spans, tend = [], [], [], []
    taken = []                                                 # (the rim angles used, to spread the kinds)
    def free(th, gap=0.45): return all(abs(wrapa(th - u)) > gap for u in taken)
    nsp = int(rng.integers(2, 4))
    for k in range(nsp):                                       # the spans: a chord over the mouth, sagging into it
        for _ in range(60):
            tha = rng.uniform(0, 2 * math.pi)
            thb = tha + math.pi + rng.choice([-1, 1]) * rng.uniform(0.45, 1.1)
            r = rng.uniform(0.14, 0.19)
            pa = (rmo(tha) + float(lipw(tha)) + rng.uniform(0.45, 0.9)) * np.array([math.cos(tha), math.sin(tha)])
            pb = (rmo(thb) + float(lipw(thb)) + rng.uniform(0.45, 0.9)) * np.array([math.cos(thb), math.sin(thb)])
            mid = 0.5 * (pa + pb)
            if max(np.abs(pa).max(), np.abs(pb).max()) > half - 0.35 - r or not (free(tha, 0.6) and free(thb, 0.6)):
                continue
            if k == 0 and mid[1] > -1.2:                       # (the first over the far wall, its shadow on the slate)
                continue
            if k > 0 and any(abs((mid - m0)[0] * dv0[1] - (mid - m0)[1] * dv0[0]) < 1.4 for _, m0, dv0 in spans):
                continue
            Lc = float(np.linalg.norm(pb - pa))
            n = max(4, int(Lc / 0.7))
            u = np.linspace(0, 1, n + 1)
            dv = (pb - pa) / Lc
            ctrl = pa[None] + u[:, None] * (pb - pa)[None] + np.array([-dv[1], dv[0]])[None] * \
                (rng.normal(0, 0.25, n + 1) * np.sin(math.pi * u))[:, None]
            D = RT.open_root((ctrl + half) * ppm, r, 0.05 * r, 0.02, tip=(0.06, 0.1), emerge=True, zdive=0.8, tip_r=0.75)
            q = D[:, :2] / ppm - half
            ins = np.hypot(q[:, 0], q[:, 1]) < np.array([rmo(math.atan2(b, a)) for a, b in q])
            ii = np.nonzero(ins)[0]
            s = arc(D)
            s0, s1 = s[ii[0]], s[ii[-1]]
            uu = np.clip((s - s0) / max(s1 - s0, 1.0), 0, 1)
            smax = rng.uniform(1.8, 2.6) * (s1 - s0) / ppm / 9.0
            D[:, 1] += COT * smax * np.sin(math.pi * uu) ** 1.1 * ppm
            if not inside_rect(D, N, N):
                continue
            spans.append((D, mid, dv))
            taken += [tha, thb]
            for _ in range(int(rng.integers(2, 4))):           # rootlets hanging off it
                j = int(np.searchsorted(s, s0 + rng.uniform(0.2, 0.8) * (s1 - s0)))
                ln = COT * rng.uniform(0.5, 1.4)
                h = math.pi / 2 + rng.normal(0, 0.18)
                cc = D[j, :2] / ppm + np.outer(np.linspace(0, ln, 4), [math.cos(h), math.sin(h)]) + \
                    np.column_stack([rng.normal(0, 0.04, 4) * np.linspace(0, 1, 4), np.zeros(4)])
                C = RT.open_root(cc * ppm, rng.uniform(0.035, 0.055), D[j, 2] / ppm - 0.06, 0.0, tip=(0.6, 0.8),
                                 emerge=False, zdive=None, tip_r=0.3)
                tend.append(C)
            break
    def along_root(th0, r, sgn, al, out, tail, taper=False):
        """Out in the earth, in onto the lip and along it for al m, then over into the mouth for tail m (> 0) or back
        into the earth (taper: a long taper, thick at the root end and lying low over the near lip)."""
        ss = np.arange(0, al + 1e-6, 0.4)
        ths = th0 + sgn * ss / BIG_R
        w = smooth(ss / 1.2)
        off = (1 - w) * out + w * rng.uniform(0.2, 0.5) * np.array([float(lipw(u_)) for u_ in ths])
        if tail <= 0:
            off = off + smooth((ss - (al - 1.0)) / 1.0) * rng.uniform(0.5, 0.9)
        off = off + rng.normal(0, 0.05, len(ss))
        pts = np.array([(rmo(u_) + o_) * np.array([math.cos(u_), math.sin(u_)]) for u_, o_ in zip(ths, off)])
        if tail > 0:
            tg = pts[-1] - pts[-2]
            h = math.atan2(tg[1], tg[0])
            h += float(np.clip(wrapa(math.atan2(-pts[-1][1], -pts[-1][0]) - h), -0.9, 0.9)) * rng.uniform(0.6, 1.0)
            pts = np.concatenate([pts, pour_path(rng, pts[-1], h, tail, rmo)[1:]])
        D = RT.open_root((pts + half) * ppm, r, -0.1 * r, 0.03, tip=(0.6, 0.8) if taper else (0.3, 0.45), emerge=True,
                         zdive=None, tip_r=0.28 if taper else 0.35)
        D = no_pop(lift(D, ppm), ppm)
        return D if inside_rect(D, N, N) else None
    def fork_of(D, into):
        if rng.random() < 0.6:
            C = RT.fork(D, 1, ratio=(0.45, 0.6), length=(0.9, 1.6), zdive=None, tip=(0.4, 0.6), tip_r=0.25)
            if inside_rect(C, N, N) and C[0, 2] > -0.25 * C[0, 3]:
                into.append(C)
                cover_mark(cov, C, ppm, half, rmo, -0.1, 0.75)
    cov = np.zeros(360, bool)
    for D, _, _ in spans:
        cover_mark(cov, D, ppm, half, rmo, -0.1, 0.75)
    npo = int(rng.integers(5, 7))
    ths = rng.uniform(0, 2 * math.pi) + np.arange(npo) * 2 * math.pi / npo + rng.normal(0, 0.2, npo)
    for th in ths:                                             # over the rim, into the dark
        for _ in range(30):
            r = rng.uniform(0.15, 0.225)
            dmax = min(1.9, room(th, r))
            if dmax < 0.6 or not free(th, 0.25):
                th += 0.27; continue
            near = math.sin(th) > 0.45
            if near:                                           # the near side: lying low along and over the lip
                D = along_root(th, r, rng.choice([-1, 1]), rng.uniform(2.0, 3.4), rng.uniform(0.6, dmax),
                               rng.uniform(0.3, 0.55), taper=True)
                if D is None:
                    th += 0.27; continue
                along.append(D)
                cover_mark(cov, D, ppm, half, rmo, -0.1, 0.75)
                fork_of(D, along)
                taken.append(th)
                break
            rim = rmo(th) + float(lipw(th))
            p0 = (rim + rng.uniform(0.5, dmax)) * np.array([math.cos(th), math.sin(th)])
            ctrl = pour_path(rng, p0, th + math.pi + rng.choice([-1, 1]) * rng.uniform(0.4, 0.85),
                             rng.uniform(2.0, 3.6), rmo) + half
            D = lift(RT.open_root(ctrl * ppm, r, -0.1 * r, 0.03, tip=(0.35, 0.5), emerge=True, zdive=None, tip_r=0.35), ppm)
            D = no_pop(D, ppm)
            if not inside_rect(D, N, N):
                th += 0.27; continue
            pour.append(D)
            taken.append(th)
            cover_mark(cov, D, ppm, half, rmo, -0.1, 0.75)
            if rng.random() < 0.6:                             # a thinner strand split off before the rim
                s = arc(D)
                q = D[:, :2] / ppm - half
                ins = np.nonzero(np.hypot(q[:, 0], q[:, 1]) < np.array([rmo(math.atan2(b, a)) for a, b in q]) + 0.15)[0]
                if len(ins) and s[ins[0]] > 0.8 * ppm:
                    j = int(np.searchsorted(s, rng.uniform(0.5 * ppm, s[ins[0]] - 0.2 * ppm)))
                    tg = D[min(j + 4, len(D) - 1), :2] - D[max(j - 4, 0), :2]
                    hf = math.atan2(tg[1], tg[0]) + rng.choice([-1, 1]) * math.radians(rng.uniform(28, 45))
                    C = pour_path(rng, D[j, :2] / ppm - half, hf, rng.uniform(1.0, 1.8), rmo) + half
                    C = RT.open_root(C * ppm, D[j, 3] / ppm * rng.uniform(0.5, 0.62), 0.03, 0.02, tip=(0.4, 0.5),
                                     emerge=False, zdive=None, tip_r=0.3)
                    kk = smooth(arc(C) / (0.4 * ppm))
                    C[:, 2] = (1 - kk) * D[j, 2] + kk * C[:, 2]
                    if inside_rect(C, N, N) and C[0, 2] > -0.25 * C[0, 3]:
                        pour.append(C)
                        cover_mark(cov, C, ppm, half, rmo, -0.1, 0.75)
            break
    goal = rng.uniform(0.64, 0.7)
    for k in range(9):                                         # along the rim (crossing what is there) until it is wreathed
        if cov.mean() >= goal:
            break
        gc, gl = big_gap(cov)
        for _ in range(40):
            r = rng.uniform(0.13, 0.2)
            sgn = rng.choice([-1, 1])
            al = rng.uniform(2.6, 4.6)
            th0 = gc - sgn * 0.5 * min(gl, al / BIG_R) + rng.normal(0, 0.1)
            if room(th0, r) < 0.7:
                continue
            the = th0 + sgn * al / BIG_R
            if math.sin(the) > 0.45:
                tail, tap = rng.uniform(0.3, 0.55), True
            else:
                tail, tap = (rng.uniform(1.8, 3.0) if rng.random() < 0.5 else 0.0), False
            D = along_root(th0, r, sgn, al, min(room(th0, r), rng.uniform(0.7, 1.3)), tail, taper=tap)
            if D is None:
                continue
            along.append(D)
            cover_mark(cov, D, ppm, half, rmo, -0.1, 0.75)
            fork_of(D, along)
            break
    for D in pour + along:
        RT.add(D)
    sid = [RT.add(D) for D, _, _ in spans]
    tid = [RT.add(C) for C in tend]
    col, mask, sh, deep, _ = shade(F, RT, seed_of("den_roots", "bigpit_shade", i, PIT_VERSION), earth=False)
    cvr = rim_cover(mask, X, Y, MR, -0.05, 0.75)
    ID = F.ID.reshape(N, N)
    hang = np.isin(ID, sid + tid)
    H2 = F.H.reshape(N, N).copy()
    H2[hang] = 0
    sh_in = cast_shadow(H2, ppm, False)                        # (inside the mouth: the rim roots' shadow only)
    del H2
    sh = np.where(M, sh_in, sh)
    del sh_in
    cast = blur((sh & ~mask).astype(np.float32), 0.012 * ppm, False)
    rs = np.clip(np.maximum(0.47 * cast, 0.4 * smooth(deep / 0.6) * (~mask) * (~M)), 0, 0.5) * smooth((em - 0.05) / 0.3)
    del cast, deep
    # the hanging roots' own shadow on the wall below them (down-right, away from the light)
    kk = 1.45
    dx, dy = int(round(-L2[0] * kk * ppm)), int(round(-L2[1] * kk * ppm))
    hs = np.roll(np.roll(hang & M, dy, 0), dx, 1)
    hs = (blur(hs.astype(np.float32), 0.025 * ppm, False) > 0.45) & M & ~mask

    # ---- the far wall: risers and shelves per column, by depth
    def cn(k, per, off): return fnz(T[k], c, np.full_like(c, off), per)
    d1 = 1.45 + 0.35 * cn(4, 0.45, 1.0) + 0.03 * cn(4, 1.5, 2.0)
    e1 = np.clip(0.44 * np.clip(0.8 + 0.8 * cn(5, 0.45, 1.0), 0, 1.3) + 0.03 * cn(5, 3.0, 4.0), 0, None)
    d2 = 3.8 + 0.45 * cn(4, 0.4, 5.0) + 0.04 * cn(4, 1.4, 6.0)
    e2 = np.clip(0.38 * np.clip(0.6 + 0.9 * cn(5, 0.4, 7.0), 0, 1.3) + 0.03 * cn(5, 2.6, 8.0), 0, None)
    d3 = 6.3 + 0.5 * cn(4, 0.35, 9.0) + 0.04 * cn(4, 1.3, 10.0)
    e3 = np.clip(0.32 * np.clip(0.35 + 1.0 * cn(5, 0.35, 11.0), 0, 1.3) + 0.03 * cn(5, 2.2, 12.0), 0, None)
    dB = BIG_WALL_D + 0.7 * cn(6, 0.4, 13.0)
    a1 = COT * d1; b1 = a1 + e1
    a2 = b1 + COT * (d2 - d1); b2 = a2 + e2
    a3 = b2 + COT * (d3 - d2); b3 = a3 + e3
    g = [x[None, :] for x in (d1, e1, d2, e2, d3, e3, dB, a1, b1, a2, b2, a3, b3)]
    d1, e1, d2, e2, d3, e3, dB, a1, b1, a2, b2, a3, b3 = g
    s1, s2, s3 = (t >= a1) & (t < b1), (t >= a2) & (t < b2), (t >= a3) & (t < b3)
    Dp = np.where(t < a1, t / COT, np.where(t < b1, d1, np.where(t < a2, d1 + (t - b1) / COT, np.where(
        t < b2, d2, np.where(t < a3, d2 + (t - b2) / COT, np.where(t < b3, d3, d3 + (t - b3) / COT)))))).astype(np.float32)
    since = Dp - np.where(t < a1, 0.0, np.where(t < a2, d1, np.where(t < a3, d2, d3)))
    shelf = np.where(s1, 1, np.where(s2, 2, np.where(s3, 3, 0))).astype(np.int8)
    fs = np.where(s1, (t - a1) / np.maximum(e1, 1e-3), np.where(s2, (t - a2) / np.maximum(e2, 1e-3),
                                                                 (t - a3) / np.maximum(e3, 1e-3)))
    fsm = np.where(s1, t - a1, np.where(s2, t - a2, t - a3))
    del s1, s2, s3
    WT = np.stack([rgbf(PPAL["ledge_lit"]), rgbf(FPAL["slate_hi"]), rgbf(FPAL["slate"]), rgbf(FPAL["slate_dk"]),
                   rgbf(PPAL["slate_ddk"]), rgbf(FPAL["void"]), rgbf(FPAL["crack"]), rgbf(PPAL["slate_k"])])
    xr = X / BIG_R
    v = 1 - Dp / dB + 0.06 * fnz(T[6], X / 3.0, Dp / 2.0, 0.6, 20.0)
    v = v + (0.16 * np.clip(xr, 0, 1) - 0.05 * np.clip(-xr, 0, 1)) * np.clip(1 - Dp / dB, 0, 1)
    band = np.where(v > 0.8, 1, np.where(v > 0.57, 2, 3)).astype(np.int8)       # (the fall to black: the terraces below)
    facet = fnz(T[7], X * 0.5, Dp * 1.1, 0.9) > 1.0                         # chunky lighter rock faces
    band = np.where(facet & (band >= 2) & (band <= 4), band - 1, band)
    band = np.where((since < 0.32) & (t >= a1) & (band < 5), np.minimum(band + 1, 3), band)   # under a shelf's lip
    # the shelves: lit along the front edge, darker at the back against the riser above, rubble flecks
    sb = np.where(shelf == 1, np.where(fs > 0.62, 0, np.where(fs > 0.2, 1, 2)),
                  np.where(shelf == 2, np.where(fs > 0.62, 1, np.where(fs > 0.22, 2, 3)),
                           np.where(fs > 0.6, 2, np.where(fs > 0.25, 3, 4))))
    peb = fnz(T[3], X, Y, 6.0, 70.0) > 1.45
    sb = np.where(peb, np.maximum(sb - 1, 0), sb)
    band = np.where(shelf > 0, sb, band).astype(np.int8)
    del sb, peb, facet, fs
    # below the last shelf the slate falls to black in three terraces with smooth, gently wavy edges: in plan past the
    # last shelf's front (Dp is linear there, so a terrace edge never frays over a shelf), the key side a little deeper
    xc = c[None, :] / BIG_R
    tilt = 0.9 * np.clip(xc, 0, 1) - 0.3 * np.clip(-xc, 0, 1)
    def terr(Dk, off, lo):
        tk = b3 + COT * np.maximum(Dk + tilt - d3, 0.0) + 0.12 * cn(6, 0.45, off)[None] + 0.035 * cn(6, 1.2, off + 3.0)[None]
        return np.maximum(tk, lo)
    t1 = terr(6.7, 31.0, b3 + 0.06)
    t2 = terr(7.45, 37.0, t1 + 0.16)
    t3 = terr(8.2, 43.0, t2 + 0.16)
    ter = (t >= t1).astype(np.int8) + (t >= t2) + (t >= t3)
    band = np.where(ter == 1, np.maximum(band, 4), np.where(ter == 2, 7, np.where(ter == 3, 5, band))).astype(np.int8)
    del ter, xc, tilt
    crack = (np.abs(fnz(T[8], X, Dp / 4.0, 0.9)) < 0.022) & (band <= 3) & (shelf == 0)
    line = ((shelf == 0) & (t >= a1) & (since < 0.07)) | ((shelf > 0) & (fsm < 0.02))
    band = np.where(crack | (line & (band <= 3)), 6, band)
    band = np.where(t < 0.085, 3, band)                                     # the roll under the far rim
    band = np.where(hs & (band <= 3), np.where(band == 3, 7, band + 2), band)  # a hanging root's shadow (not on the terraces)
    wall = WT[band]
    wall = np.where((sd > -0.018)[..., None], rgbf(PAL["ink"]), wall)
    del band, crack, line, since, Dp, v, hs, xr
    Cp = np.where(M[..., None], wall, Cp)
    A = np.where(M, 1.0, A).astype(np.float32)
    del wall
    Cp = Cp * (1 - rs[..., None]) + shc * rs[..., None]
    A = A + rs * (1 - A)
    # the roots' fade: down the far wall by the depth seen, behind the near lip within 0.5 m; the spans a little
    # darker where they hang deepest, the rootlets to their tips
    wf = smooth((ny + 0.3) / 0.6)
    fade_in = (1 - wf) * (1 - smooth(t / (COT * 7.0))) + wf * (1 - smooth(-sd / 0.5))
    fade = np.where(M, fade_in, 1.0)
    fade = np.where(np.isin(ID, sid), 1 - 0.3 * smooth(-sd / 3.0), fade)
    if tid:
        tl = np.zeros(len(RT.send), np.float32)
        for j in tid:
            tl[j] = RT.paths[j][3][-1]
        Sm = F.S.reshape(N, N)
        it = np.isin(ID, tid)
        fade = np.where(it, 0.85 - 0.6 * smooth(Sm / np.maximum(tl[np.maximum(ID, 0)], 1.0)), fade)
    Cp = np.where(mask[..., None], col * fade[..., None], Cp)
    A = np.where(mask, 1.0, A)
    del col, fade, fade_in
    pa, a = reduce(Cp), reduce(A)
    rgb = pa / np.maximum(a[..., None], 1e-6)
    tt = np.linspace(0, 2 * math.pi, 3600)
    rlo, rhi = float(pt_r(BIG_R, harm, tt).min()), float(pt_r(BIG_R, harm, tt).max())
    print(f"  bigpit {i}: {len(pour)} pour (+strands), {len(along)} along, {len(spans)} spans, {len(tend)} rootlets, "
          f"rim under roots {100 * cvr:.0f}%")
    return np.concatenate([to8(rgb), to8(a)[..., None]], -1), harm, (rlo, rhi), float(lipw(tt).max() + 0.05)


def hollow_rect(r0):
    rimw = 0.3 + 0.05 * r0
    return rimw, round(2 * (r0 * 1.09 + rimw + 1.1) * 10) / 10


def rim_cover(mask, X, Y, MR, lo, hi, nb=360):
    """The share of a mouth's round under roots: the angle bins holding a root pixel lo..hi m past the mouth's edge."""
    R = np.hypot(X, Y)
    z = mask & (R > MR + lo) & (R < MR + hi)
    b = ((np.arctan2(Y[z], X[z]) + math.pi) / (2 * math.pi) * nb).astype(np.int64) % nb
    return float(np.unique(b).size) / nb


def cover_mark(cov, D, ppm, half, rmo, lo, hi):
    """Mark the angle bins a dense root D covers lo..hi m past the mouth's edge (its own radius either side)."""
    q = D[:, :2] / ppm - half
    th = np.arctan2(q[:, 1], q[:, 0])
    m = np.array([rmo(t) for t in th])
    rr, rd = np.hypot(q[:, 0], q[:, 1]), D[:, 3] / ppm
    ok = (rr > m + lo - rd) & (rr < m + hi + rd)
    nb = len(cov)
    for t, w in zip(th[ok], rd[ok] / m[ok]):
        b0, b1 = int(math.floor((t - w + math.pi) / (2 * math.pi) * nb)), int(math.floor((t + w + math.pi) / (2 * math.pi) * nb))
        cov[np.arange(b0, b1 + 1) % nb] = True


def big_gap(cov):
    """The widest run of uncovered bins: (its centre angle, its width in radians)."""
    nb = len(cov)
    if not cov.any():
        return 0.0, 2 * math.pi
    k = int(np.argmax(cov))
    rc = np.roll(cov, -k)
    best, run, st = (0, 0), 0, 0
    for j in range(nb + 1):
        if j < nb and not rc[j]:
            if run == 0:
                st = j
            run += 1
        else:
            if run > best[1]:
                best = (st, run)
            run = 0
    c = (best[0] + k + best[1] / 2.0) % nb
    return c / nb * 2 * math.pi - math.pi, best[1] / nb * 2 * math.pi


def decal_hollow(i):
    """A shallow sunken bowl (walkable, no hole) of dark damp earth: no raised rim (the floor's own colour meets it at a
    thin ink break, a little lit crest on the upper left only), three broad painted steps inside (the bottom and the
    slope turned from the light darkest, the slope facing it, lower right, a step lighter), a few dark leaves (a bone)
    in the bottom; a dense tangle of thick roots running along the rim (about half its round), forking, crossing, and
    draping over it into the bowl, their shadows on the floor and in the bowl."""
    r0 = HOLLOWS[i]
    ppm = PT_PPM * S
    rimw, rect = hollow_rect(r0)
    N, half, c, X, Y = pt_grid(rect, ppm)
    harm, lw = pt_mouth("hollow_mouth", i, {2: (0.05, 0.08), 3: (0.03, 0.05), 5: (0.01, 0.018), 9: (0.004, 0.007)})
    rng = np.random.default_rng(seed_of("den_roots", "hollow", i, PIT_VERSION))
    T = [pnoise(1024, 24, 40, rng) for _ in range(8)]
    R = np.hypot(X, Y) + 1e-6
    TH = np.arctan2(Y, X)
    MR = pt_r(r0, harm, TH).astype(np.float32)
    L0 = (X * L2[0] + Y * L2[1]) / R
    q = R - MR                                               # m outside the bowl's edge (mouth_harm wobbles it)
    s = np.clip(R / MR, 0, 1)
    Dd = 0.3 + 0.12 * r0
    h = (-Dd * (1 - s ** 2.2)).astype(np.float32)             # steepest at the edge, a broad flat bottom
    hy, hx = np.gradient(h, 1.0 / ppm)
    lam = (-hx * L2[0] * CE - hy * L2[1] * CE + SE) / np.sqrt(1 + hx * hx + hy * hy)
    dl = lam - SE + 0.03 * fnz(T[2], X, Y, 0.55)              # (broad, gently wavy steps: low noise only)
    dd = np.clip(-h / Dd, 0, 1) + 0.07 * fnz(T[1], X, Y, 0.5)
    del hx, hy, lam, h
    P = lambda k: rgbf(PPAL[k])
    ins = q < 0
    band = np.where((dd > HB_BOT) | (dl < HB_DK), 2, np.where(dl > HB_LIT, 0, 1)).astype(np.int8)
    C = np.stack([P("dish_lit"), P("dish"), P("dish_dk")])[band]
    del band
    cw = 0.05 * smooth((L0 - 0.25) / 0.35) * (1 + 0.25 * fnz(T[3], X, Y, 0.8))   # the lit crest (upper left)
    C = np.where(ins[..., None], C, P("crest_lit"))
    C = np.where(((q > -0.02 - 0.014 * np.clip(L0, 0, 1)) & (q < 0.008))[..., None], rgbf(PAL["ink"]), C)
    qo = 0.008 + np.maximum(cw, 0)
    a_in = np.clip((qo - q) / 0.015 + 0.5, 0, 1).astype(np.float32)
    em = half - np.maximum(np.abs(X), np.abs(Y))
    shc = rgbf(PAL["shadow"])
    # leaf litter in the bottom (dark: it lies in the bowl's shade), a bone in some
    nl = int(3 + 2 * r0)
    for _ in range(nl):
        rr, a = r0 * 0.62 * math.sqrt(rng.uniform(0, 1)) ** 1.2, rng.uniform(0, 2 * math.pi)
        cx, cy = rr * math.cos(a), rr * math.sin(a)
        ll, wr, ang = rng.uniform(0.08, 0.13), rng.uniform(0.38, 0.48), rng.uniform(0, math.pi)
        tone = P(["leaf", "leaf_hi", "leaf_dk", "leaf"][int(rng.integers(0, 4))]) * 0.66
        ca, sn = math.cos(ang), math.sin(ang)
        for shadow in (True, False):
            ox, oy = (-L2[0] * 0.018, -L2[1] * 0.018) if shadow else (0.0, 0.0)
            j0, j1 = int((cy + oy - ll + half) * ppm), int((cy + oy + ll + half) * ppm) + 1
            k0, k1 = int((cx + ox - ll + half) * ppm), int((cx + ox + ll + half) * ppm) + 1
            u = (X[j0:j1, k0:k1] - cx - ox) * ca + (Y[j0:j1, k0:k1] - cy - oy) * sn
            w = -(X[j0:j1, k0:k1] - cx - ox) * sn + (Y[j0:j1, k0:k1] - cy - oy) * ca
            hw = 0.5 * ll * wr * (1 - (2 * u / ll) ** 2).clip(0) ** 0.6 * (1 - 0.25 * u / ll)
            inl = np.abs(w) < hw
            if shadow:
                C[j0:j1, k0:k1][inl] *= 0.7
                continue
            lc = np.where((w < 0)[..., None], tone, tone * 0.8)
            lc = np.where(((hw - np.abs(w) < 0.007) | (np.abs(w) < 0.0035))[..., None], P("leaf_dk") * 0.5, lc)
            C[j0:j1, k0:k1] = np.where(inl[..., None], lc, C[j0:j1, k0:k1])
    if i % 2 == 1:                                             # a gnawed bone
        bl, ang = rng.uniform(0.3, 0.4), rng.uniform(0, math.pi)
        rr, a = r0 * 0.35 * math.sqrt(rng.uniform(0, 1)), rng.uniform(0, 2 * math.pi)
        cx, cy = rr * math.cos(a), rr * math.sin(a)
        ca, sn = math.cos(ang), math.sin(ang)
        ext = bl / 2 + 0.08
        j0, j1 = int((cy - ext + half) * ppm), int((cy + ext + half) * ppm) + 1
        k0, k1 = int((cx - ext + half) * ppm), int((cx + ext + half) * ppm) + 1
        def bone(ox, oy, grow):
            u = (X[j0:j1, k0:k1] - cx - ox) * ca + (Y[j0:j1, k0:k1] - cy - oy) * sn
            w = -(X[j0:j1, k0:k1] - cx - ox) * sn + (Y[j0:j1, k0:k1] - cy - oy) * ca
            sh_ = (np.abs(u) < bl / 2) & (np.abs(w) < 0.02 + grow)
            for e_ in (-1, 1):
                for f_ in (-1, 1):
                    sh_ |= np.hypot(u - e_ * bl / 2, w - f_ * 0.02) < 0.027 + grow
            return sh_, u, w
        bs, _, _ = bone(-L2[0] * 0.03, -L2[1] * 0.03, 0.0)
        C[j0:j1, k0:k1][bs] *= 0.62
        out_, _, _ = bone(0, 0, 0.011)
        body, u, w = bone(0, 0, 0.0)
        lit, _, _ = bone(L2[0] * 0.012, L2[1] * 0.012, 0.0)
        bc = np.where((body & ~lit)[..., None], P("bone_lit"), P("bone"))
        bc = np.where((out_ & ~body)[..., None], rgbf(PAL["ink"]), bc)
        C[j0:j1, k0:k1] = np.where(out_[..., None], bc, C[j0:j1, k0:k1])
    Cp = (C * a_in[..., None]).astype(np.float32)
    A = a_in.copy()
    del C
    # the roots: thick, along the rim until about half its round is under them, forking, crossing, draping over it
    F = Field(N, N, ppm, False)
    RT = Roots(F, rng)
    def rmo(th): return float(pt_r(r0, harm, th))
    def room(th, r): return (half - 0.2 - r) / max(abs(math.cos(th)), abs(math.sin(th))) - (rmo(th) + 0.05)
    cov = np.zeros(360, bool)
    goal = rng.uniform(0.34, 0.4)            # (the along roots and their forks; the drapes add the rest)
    along, over, forks = [], [], []
    for k in range(9):
        if cov.mean() >= goal:
            break
        gc, gl = big_gap(cov)
        for _ in range(40):
            r = rng.uniform(0.1, 0.17)
            sgn = rng.choice([-1, 1])
            al = rng.uniform(1.6, 2.6)
            th0 = gc - sgn * 0.5 * min(gl, al / r0) + rng.normal(0, 0.12)
            if room(th0, r) < 0.45:
                continue
            ss = np.arange(0, al + 1e-6, 0.25)
            ths = th0 + sgn * ss / r0
            w = smooth(ss / 0.7)
            off = (1 - w) * rng.uniform(0.5, min(1.1, room(th0, r))) + w * rng.uniform(-0.1, 0.06)
            end = rng.random()
            if end < 0.55:                                     # its end turns down into the bowl
                off = off - smooth((ss - (al - 0.6)) / 0.6) * rng.uniform(0.45, 0.8)
            elif end < 0.8:                                    # or back into the earth
                off = off + smooth((ss - (al - 0.6)) / 0.6) * rng.uniform(0.3, 0.6)
            pts = np.array([(rmo(u_) + o_) * np.array([math.cos(u_), math.sin(u_)]) for u_, o_ in zip(ths, off)])
            pts += rng.normal(0, 0.03, pts.shape)
            D = no_pop(RT.open_root((pts + half) * ppm, r, -0.1 * r, 0.02, tip=(0.45, 0.65), emerge=True, zdive=None, tip_r=0.22), ppm)
            if not inside_rect(D, N, N):
                continue
            along.append(D)
            cover_mark(cov, D, ppm, half, rmo, -0.12, 0.12)
            if rng.random() < 0.65:                            # a fork, into the bowl or out over the floor
                Cf = RT.fork(D, 1, ang=(20, 38), ratio=(0.5, 0.62), length=(0.9, 1.5), zdive=None, tip=(0.5, 0.7), tip_r=0.22, wig=6.0)
                if inside_rect(Cf, N, N) and Cf[0, 2] > -0.25 * Cf[0, 3]:   # (not off its parent's buried start)
                    forks.append(Cf)
                    cover_mark(cov, Cf, ppm, half, rmo, -0.12, 0.12)
            break
    ndr = 2 + int(r0 > 1.6) + int(rng.integers(0, 2))
    used = []
    for k in range(ndr):                                       # over the rim and down into the bowl
        for _ in range(60):
            th0 = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(0.09, 0.14)
            if any(abs(wrapa(th0 - u_)) < 0.55 for u_ in used) or room(th0, r) < 0.45:
                continue
            p0 = (rmo(th0) + rng.uniform(0.4, min(1.0, room(th0, r)))) * np.array([math.cos(th0), math.sin(th0)])
            hd_ = th0 + math.pi + rng.uniform(-0.55, 0.55)
            ln = np.linalg.norm(p0) - rmo(th0) + rng.uniform(0.3, 0.6) * r0
            ctrl = RT.walk((p0 + half) * ppm, hd_, ln, step=(0.2, 0.3), wig=6.0, pull=0.2)
            D = no_pop(RT.open_root(ctrl, r, -0.1 * r, 0.02, tip=(0.45, 0.65), emerge=True, zdive=None, tip_r=0.22), ppm)
            if not inside_rect(D, N, N):
                continue
            over.append(D)
            used.append(th0)
            cover_mark(cov, D, ppm, half, rmo, -0.12, 0.12)
            if rng.random() < 0.4:
                Cf = RT.fork(D, 1, ang=(20, 38), ratio=(0.5, 0.62), length=(0.7, 1.2), zdive=None, tip=(0.5, 0.7), tip_r=0.22, wig=6.0)
                if inside_rect(Cf, N, N) and Cf[0, 2] > -0.25 * Cf[0, 3]:   # (not off its parent's buried start)
                    forks.append(Cf)
            break
    for D in along + over + forks:
        RT.add(D)
    col, mask, sh, deep, _ = shade(F, RT, seed_of("den_roots", "hollow_shade", i, PIT_VERSION), earth=False)
    cast = blur((sh & ~mask).astype(np.float32), 0.012 * ppm, False)
    rs = np.clip(np.maximum(0.45 * cast, 0.36 * smooth(deep / 0.6) * (~mask)), 0, 0.5) * smooth((em - 0.05) / 0.3)
    Cp = Cp * (1 - rs[..., None]) + shc * rs[..., None]
    A = A + rs * (1 - A)
    fade = 1 - 0.18 * np.clip(dd, 0, 1)
    Cp = np.where(mask[..., None], col * fade[..., None], Cp)
    A = np.where(mask, 1.0, A)
    cv = rim_cover(mask, X, Y, MR, -0.12, 0.12)
    pa, a = reduce(Cp), reduce(A)
    rgb = pa / np.maximum(a[..., None], 1e-6)
    tt = np.linspace(0, 2 * math.pi, 3600)
    rlo, rhi = float(pt_r(r0, harm, tt).min()), float(pt_r(r0, harm, tt).max())
    print(f"  hollow {i}: r {rlo:.2f}-{rhi:.2f} m, rect {rect} m, {len(along)} along, {len(over)} over, {len(forks)} forks,"
          f" rim under roots {100 * cv:.0f}%, {nl} leaves")
    return np.concatenate([to8(rgb), to8(a)[..., None]], -1), harm, (rlo, rhi), round(0.008 + 0.05 * 1.25 + 0.03, 3), rect


def build_pits(out):
    items = []
    for i in range(BIGPITS):
        img, harm, (rlo, rhi), lwm = decal_bigpit(i)
        items.append(dict(kind="bigpit", variant=i, metres=[BIG_M, BIG_M], anchor=[0.5, 0.5], img=img, mouth_r=BIG_R,
                          mouth_harm=harm, mouth_r_range=[round(rlo, 3), round(rhi, 3)], lip_m=round(lwm, 3)))
    for i, r0 in enumerate(HOLLOWS):
        img, harm, (rlo, rhi), lwm, rect = decal_hollow(i)
        items.append(dict(kind="hollow", variant=i, metres=[rect, rect], anchor=[0.5, 0.5], img=img, mouth_r=r0,
                          mouth_harm=harm, mouth_r_range=[round(rlo, 3), round(rhi, 3)], lip_m=round(lwm, 3)))
    rects, ah = pack([(it["img"].shape[1], it["img"].shape[0]) for it in items], PT_ATLAS_W)
    atlas = np.zeros((ah, PT_ATLAS_W, 4), np.uint8)
    dec = []
    for it, (x, y, w, h) in zip(items, rects):
        atlas[y:y + h, x:x + w] = it.pop("img")
        dec.append({"kind": it.pop("kind"), "variant": it.pop("variant"), "rect": [x, y, w, h], **it})
    Image.fromarray(atlas, "RGBA").save(os.path.join(out, "pit_decals.png"), optimize=False, compress_level=9)
    man = {"by": "tools/look/den_roots.py build pits (painted from nothing; no outside source)", "version": PIT_VERSION,
           "size": [PT_ATLAS_W, ah], "px_per_m": PT_PPM, "light": [round(float(c), 4) for c in L2],
           "light_note": "painted from the rect's upper left (toward the light, image x right / y down); laid flat on "
                         "the floor, image up = north (the play camera looks north, 62 degrees down); never turned",
           "alpha": "straight; the lip, the mouth and the roots (a hollow: its whole dish) >= 0.6 (alpha scissor "
                    "0.6; the mouth and the dish are 1), the soft contact shadow 0.2-0.55 (rgb = palette shadow), 0 at "
                    "the rect's edge",
           "kinds": {"bigpit": "a big pit at its own size (the game's holes, mean r 5.2-5.8 m): anchor = the mouth's "
                               "centre (the rect's centre); the mouth r(theta) = mouth_r * (1 + sum a sin(k theta + p)) "
                               "over mouth_harm [k, a, p] (theta = atan2(y, x), image x right / y down, metres from the "
                               "centre), alpha 1 over all of it; the lip band up to lip_m outside the mouth, the contact "
                               "shadow 0.9 m past that; the far wall in slate risers and shelves, black only past about "
                               "9 m down (the near part of the mouth)",
                     "hollow": "a shallow walkable hollow, no hole: the same mouth fields for the dish's edge; the dish "
                               "opaque out to lip_m past the edge (an ink break, a little lit crest on the upper left "
                               "only, no raised rim: the floor meets it), no contact shadow ring (the roots' shadows "
                               "only); nothing black (the bottom and the shade slope about sRGB (44, 31, 24))"},
           "anchor": "[fx, fy] in the rect (0..1, x right, y down)", "decals": dec}
    with open(os.path.join(out, "pit_decals.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1)


PIT_TARGET = os.path.join(os.path.expanduser("~"), "Desktop", "survivorsunchained_inputs", "scratch_coord12",
                          "dungeon_concepts", "den_boss.png")


def pit_preview(out):
    """At the game's scale (73 px/m) on a flat floor of the game's colour: the two big pits beside 1:1 crops of
    den_boss.png's pit and its hollows; the four hollows; then a 1:1 (128 px/m) crop of a big pit's far rim."""
    atl = Image.open(os.path.join(out, "pit_decals.png")).convert("RGBA")
    man = json.load(open(os.path.join(out, "pit_decals.json"), encoding="utf-8"))
    floor = (96, 68, 50)
    k = PREVIEW_PPM / PT_PPM
    G = 16
    def get(d, scale=k):
        x, y, w, h = d["rect"]
        c = atl.crop((x, y, x + w, y + h))
        c = c if scale == 1 else c.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        bg = Image.new("RGBA", c.size, floor + (255,))
        bg.alpha_composite(c)
        return bg.convert("RGB")
    big = [get(d) for d in man["decals"] if d["kind"] == "bigpit"]
    hol = [get(d) for d in man["decals"] if d["kind"] == "hollow"]
    tim = Image.open(PIT_TARGET).convert("RGB") if os.path.exists(PIT_TARGET) else None
    tgt = [tim.crop((380, 470, 1010, 941)), tim.crop((1000, 150, 1672, 780))] if tim else []   # its pit; its hollows
    row1 = [*big] + tgt
    W = max(sum(c.width for c in row1), sum(c.width for c in hol)) + G * (len(row1) + 1)
    d0 = [d for d in man["decals"] if d["kind"] == "bigpit"][0]
    x, y, w, h = d0["rect"]
    crop = get(d0, 1).crop((int(0.2 * w), int(0.1 * h), int(0.2 * w) + min(W - 2 * G, int(0.6 * w)), int(0.1 * h) + int(0.45 * h)))
    H = G + max(c.height for c in row1) + G + max(c.height for c in hol) + G + crop.height + G
    sheet = Image.new("RGB", (W, H), (24, 22, 22))
    xx, yy = G, G
    for c in row1:
        sheet.paste(c, (xx, yy)); xx += c.width + G
    yy += max(c.height for c in row1) + G
    xx = G
    for c in hol:
        sheet.paste(c, (xx, yy)); xx += c.width + G
    yy += max(c.height for c in hol) + G
    sheet.paste(crop, (G, yy))
    sheet.save(os.path.join(out, "pit_preview.jpg"), quality=90)


def check_pits():
    """pit_decals: the rects, the mouth (a hollow's dish) opaque, nothing opaque at the rect's edge; a big pit's mouth
    at most 55 % pure black (Y < 8); no pixel in a hollow's dish below Y 12."""
    p = os.path.join(OUT, "pit_decals.json")
    if not os.path.exists(p):
        print("pit decals: none built"); return True
    dm = json.load(open(p, encoding="utf-8"))
    atl = np.asarray(Image.open(os.path.join(OUT, "pit_decals.png")).convert("RGBA"))
    ok = atl.shape[1] == dm["size"][0] and atl.shape[0] == dm["size"][1] and max(dm["size"]) <= 4096
    kinds = {}
    for d in dm["decals"]:
        kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
    print("pit decals:", kinds, "atlas", dm["size"], "px/m", dm["px_per_m"])
    rs = [d["rect"] for d in dm["decals"]]
    for i, (x, y, w, h) in enumerate(rs):
        if x < PAD or y < PAD or x + w > dm["size"][0] - PAD or y + h > dm["size"][1] - PAD:
            print("FAIL pit rect outside the padded atlas", i); ok = False
        for j in range(i):
            X, Yy, Ww, Hh = rs[j]
            if x < X + Ww and X < x + w and y < Yy + Hh and Yy < y + h:
                print("FAIL pit rects overlap", i, j); ok = False
    ppm = dm["px_per_m"]
    for d in dm["decals"]:
        x, y, w, h = d["rect"]
        img = atl[y:y + h, x:x + w].astype(np.float32)
        al = img[..., 3]
        c = (np.arange(w, dtype=np.float32) + 0.5) / ppm - w / ppm / 2
        X, Yc = np.meshgrid(c, c[:h])
        th = np.arctan2(Yc, X)
        mr = d["mouth_r"] * (1 + sum(a * np.sin(k * th + p) for k, a, p in d["mouth_harm"]))
        mouth = np.hypot(X, Yc) < mr - 1.5 / ppm
        Y = img[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        edge = max((al[:2] > 12).mean(), (al[-2:] > 12).mean(), (al[:, :2] > 12).mean(), (al[:, -2:] > 12).mean())
        op = (al[mouth] >= 250).mean()
        tag = f"{d['kind']} {d['variant']}"
        if d["kind"] == "bigpit":
            blk = (Y[mouth] < 8).mean()
            print(f"  {tag}: mouth opaque {100 * op:.2f}%, pure black (Y < 8) {100 * blk:.1f}% of the mouth, "
                  f"edge alpha {100 * edge:.2f}%")
            ok = ok and op > 0.999 and blk <= 0.55 and edge == 0
        else:
            lo = int((Y[mouth] < 12).sum())
            print(f"  {tag}: dish opaque {100 * op:.2f}%, dish px below Y 12: {lo}, darkest Y {Y[mouth].min():.0f}, "
                  f"median Y {np.median(Y[mouth]):.0f}, edge alpha {100 * edge:.2f}%")
            ok = ok and op > 0.999 and lo == 0 and edge == 0
    print("pit decals", "OK" if ok else "FAIL")
    return ok


# ---- the preview -------------------------------------------------------------------------------------------------------
def preview(out):
    alb = Image.open(os.path.join(out, "bank_albedo.png")).convert("RGB")
    atl = Image.open(os.path.join(out, "bank_decals.png")).convert("RGBA")
    man = json.load(open(os.path.join(out, "bank_decals.json"), encoding="utf-8"))
    floor = (0x5a, 0x3e, 0x2e)
    tile_px = int(round(BANK_M * PREVIEW_PPM))
    tiles = []
    for v in range(BANK_VARIANTS):
        t = alb.crop((0, v * BANK_PX, BANK_PX, (v + 1) * BANK_PX)).resize((tile_px, tile_px), Image.LANCZOS)
        im = Image.new("RGB", (2 * tile_px, 2 * tile_px))
        for ox in (0, 1):
            for oy in (0, 1):
                im.paste(t, (ox * tile_px, oy * tile_px))
        tiles.append(im)
    G = 16
    Wd = 2 * (2 * tile_px) + 3 * G
    # the decals at 73 px/m on the floor, shelf-laid
    dims = []
    for d in man["decals"]:
        x, y, w, h = d["rect"]
        c = atl.crop((x, y, x + w, y + h))
        dims.append(c.resize((max(1, round(w * PREVIEW_PPM / DEC_PPM)), max(1, round(h * PREVIEW_PPM / DEC_PPM))), Image.LANCZOS))
    rows, cx, cy, sh = [], G, 0, 0
    for c in dims:
        if cx + c.width + G > Wd:
            cx, cy, sh = G, cy + sh + G, 0
        rows.append((c, cx, cy))
        cx += c.width + G
        sh = max(sh, c.height)
    dh = cy + sh + G
    # the 1:1 crops at 256 px/m: 2 x 2 m of each bank variant, a wall and a rim decal
    crop_m = 2.0
    cp = int(crop_m * 256)
    crops = []
    for v in range(BANK_VARIANTS):
        src = int(crop_m * BANK_PX / BANK_M)
        crops.append(alb.crop((300, v * BANK_PX + 600, 300 + src, v * BANK_PX + 600 + src)).resize((cp, cp), Image.LANCZOS))
    for kind in ("wall", "rim"):
        d = [d for d in man["decals"] if d["kind"] == kind][2 if kind == "wall" else 1]
        x, y, w, h = d["rect"]
        bg = Image.new("RGBA", (w, h), floor + (255,))
        bg.alpha_composite(atl.crop((x, y, x + w, y + h)))
        crops.append(bg.convert("RGB").crop((0, 0, min(w, 900), h)))
    ch = max(c.height for c in crops)
    sheet = Image.new("RGB", (Wd, G + 2 * tile_px + G + dh + ch + G), (24, 22, 22))
    sheet.paste(tiles[0], (G, G))
    sheet.paste(tiles[1], (2 * G + 2 * tile_px, G))
    y0 = G + 2 * tile_px + G
    fl = Image.new("RGBA", (Wd, dh), floor + (255,))
    for c, x, y in rows:
        fl.alpha_composite(c, (x, y + G // 2))
    sheet.paste(fl.convert("RGB"), (0, y0))
    y1 = y0 + dh
    x = G
    for c in crops:
        if x + c.width > Wd:
            break
        sheet.paste(c, (x, y1))
        x += c.width + G
    sheet.save(os.path.join(out, "roots_preview.jpg"), quality=90)


# ---- check -------------------------------------------------------------------------------------------------------------
def check():
    bank = json.load(open(os.path.join(OUT, "bank.json"), encoding="utf-8"))
    alb = np.asarray(Image.open(os.path.join(OUT, "bank_albedo.png")).convert("RGB"), np.float32)
    arh = np.asarray(Image.open(os.path.join(OUT, "bank_arh.png")).convert("RGB"), np.float32)
    nrm = np.asarray(Image.open(os.path.join(OUT, "bank_normal.png")).convert("RGB"), np.float32)
    n = bank["px"]
    pal = {k: rgbf(PAL[k]) * 255 for k in PAL}
    root_keys = ["lit_hi", "lit", "mid", "shade", "deep", "edge", "ink", "moss", "moss_dk"]
    ok = True
    for v in range(bank["variants"]):
        a = alb[v * n:(v + 1) * n]
        r = arh[v * n:(v + 1) * n]
        Y = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        root = r[..., 1] < 0.875 * 255
        P = np.stack([pal[k] for k in root_keys])
        near = np.argmin(((a[root][:, None, :] - P[None]) ** 2).sum(-1), 1)
        lit = np.isin(near, [0, 1, 5])
        print(f"variant {v}: root coverage {100 * root.mean():.1f}%  median Y: lit roots {np.median(Y[root][lit]):.0f}, "
              f"all roots {np.median(Y[root]):.0f}, gaps {np.median(Y[~root]):.0f}")
        for name, m in (("albedo", a), ("normal", nrm[v * n:(v + 1) * n]), ("arh", r)):
            edge = 0.5 * (np.abs(m[:, 0] - m[:, -1]).mean() + np.abs(m[0] - m[-1]).mean())
            inner = 0.5 * (np.abs(np.diff(m, axis=1)).mean() + np.abs(np.diff(m, axis=0)).mean())
            print(f"  seam {name}: edge step {edge:.2f}, interior step {inner:.2f}, seam error {edge - inner:+.2f} (0-255)")
            if edge - inner > 1.5:
                ok = False
        if not 0.62 <= root.mean() <= 0.78:
            ok = False
    dm = json.load(open(os.path.join(OUT, "bank_decals.json"), encoding="utf-8"))
    kinds = {}
    for d in dm["decals"]:
        kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
    atl = np.asarray(Image.open(os.path.join(OUT, "bank_decals.png")))
    al = atl[..., 3]
    print("decals:", kinds, "atlas", dm["size"], f"alpha: roots (>=153) {100 * (al >= 153).mean():.1f}%, "
          f"shadow (51-140) {100 * ((al >= 51) & (al <= 140)).mean():.1f}%")
    rs = [d["rect"] for d in dm["decals"]]
    for i, (x, y, w, h) in enumerate(rs):
        if x < PAD or y < PAD or x + w > dm["size"][0] - PAD or y + h > dm["size"][1] - PAD:
            print("FAIL rect outside the padded atlas", i); ok = False
        for j in range(i):
            X, Yy, Ww, Hh = rs[j]
            if x < X + Ww and X < x + w and y < Yy + Hh and Yy < y + h:
                print("FAIL rects overlap", i, j); ok = False
    ok = check_floor() and ok
    ok = check_pits() and ok
    print("OK" if ok else "FAIL")
    return ok


def check_floor():
    """floor_decals: the rects, the cut rules per kind (roots cross only the edge they are meant to), the pit's mouth
    opaque and its near half black, the frames dark; the FPAL colours present."""
    p = os.path.join(OUT, "floor_decals.json")
    if not os.path.exists(p):
        print("floor decals: none built"); return True
    dm = json.load(open(p, encoding="utf-8"))
    atl = np.asarray(Image.open(os.path.join(OUT, "floor_decals.png")).convert("RGBA"))
    ok = atl.shape[1] == dm["size"][0] and atl.shape[0] == dm["size"][1] and max(dm["size"]) <= 4096
    kinds = {}
    for d in dm["decals"]:
        kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
    print("floor decals:", kinds, "atlas", dm["size"], "px/m", dm["px_per_m"])
    rs = [d["rect"] for d in dm["decals"]]
    for i, (x, y, w, h) in enumerate(rs):
        if x < PAD or y < PAD or x + w > dm["size"][0] - PAD or y + h > dm["size"][1] - PAD:
            print("FAIL floor rect outside the padded atlas", i); ok = False
        for j in range(i):
            X, Yy, Ww, Hh = rs[j]
            if x < X + Ww and X < x + w and y < Yy + Hh and Yy < y + h:
                print("FAIL floor rects overlap", i, j); ok = False
    ppm = dm["px_per_m"]
    for d in dm["decals"]:
        x, y, w, h = d["rect"]
        img = atl[y:y + h, x:x + w].astype(np.float32)
        al = img[..., 3]
        tag = f"{d['kind']} {d['variant']}"
        if d["kind"] in ("floor", "floor_s"):
            top = (al[0] >= 153).mean()
            cut = max((al[-2:] >= 153).mean(), (al[:, :2] >= 153).mean(), (al[:, -2:] >= 153).mean())
            print(f"  {tag}: roots across the top edge {100 * top:.0f}% of it, at the other edges {100 * cut:.2f}%, "
                  f"roots {100 * (al >= 153).mean():.0f}% of the rect")
            ok = ok and top > 0.1 and cut == 0
        elif d["kind"] == "frame":
            band = al[:int(0.18 * ppm)]
            low = al[int(0.4 * ppm):]
            cut = max((al[-2:] >= 153).mean(), (low[:, :2] >= 153).mean(), (low[:, -2:] >= 153).mean())
            Y = img[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            print(f"  {tag}: top band opaque {100 * (band >= 250).mean():.1f}%, cut at the other edges "
                  f"{100 * cut:.2f}%, median Y of the roots {np.median(Y[al >= 153]):.0f}")
            ok = ok and (band >= 250).mean() > 0.999 and cut == 0 and np.median(Y[al >= 153]) < 45
        else:
            c = (np.arange(w, dtype=np.float32) + 0.5) / ppm - w / ppm / 2
            X, Yc = np.meshgrid(c, c[:h])
            th = np.arctan2(Yc, X)
            mr = MOUTH_R * (1 + sum(a * np.sin(k * th + p) for k, a, p in d["mouth_harm"]))
            R = np.hypot(X, Yc)
            mouth = R < mr - 1.5 / ppm
            nearh = mouth & (Yc > 0.25 * mr)
            Y = img[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            edge = max((al[:2] > 12).mean(), (al[-2:] > 12).mean(), (al[:, :2] > 12).mean(), (al[:, -2:] > 12).mean())
            ring = (R > mr + 0.1) & (R < mr + 0.3)
            print(f"  {tag}: mouth opaque {100 * (al[mouth] >= 250).mean():.2f}%, near half black (Y < 12) "
                  f"{100 * (Y[nearh] < 12).mean():.1f}%, lip ring opaque {100 * (al[ring] >= 153).mean():.0f}%, "
                  f"edge alpha {100 * edge:.2f}%")
            ok = ok and (al[mouth] >= 250).mean() > 0.999 and (Y[nearh] < 12).mean() > 0.85 and edge == 0
    print("floor decals", "OK" if ok else "FAIL")
    return ok


def main(a):
    if not a or a[0] not in ("build", "check"):
        raise SystemExit(__doc__)
    if a[0] == "check":
        sys.exit(0 if check() else 1)
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    only = a[1] if len(a) > 1 else "all"
    if only == "floor":                                       # (the floor atlas alone: the bank's outputs untouched)
        build_floor(OUT)
        floor_preview(OUT)
        print(f"floor decals done in {time.time() - t0:.0f} s -> {OUT}")
        return
    if only == "pits":                                        # (the pit set alone: nothing else rewritten)
        build_pits(OUT)
        pit_preview(OUT)
        print(f"pit decals done in {time.time() - t0:.0f} s -> {OUT}")
        return
    if only in ("all", "bank"):
        build_bank(OUT)
        print(f"bank: {time.time() - t0:.0f} s")
    if only in ("all", "decals", "dp"):
        build_decals(OUT)
        print(f"decals: {time.time() - t0:.0f} s")
    preview(OUT)
    if only == "all":
        build_floor(OUT)
        floor_preview(OUT)
        build_pits(OUT)
        pit_preview(OUT)
    print(f"done in {time.time() - t0:.0f} s -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
