"""The den dungeon's root tangle, painted: the root bank's tileable maps and root-cluster decals, ours from nothing (no
photo, scan or outside source; numpy + PIL only, deterministic).

    python tools/look/den_roots.py build   -> godot/art/dungeon/den/bank_{albedo,normal,arh}.png + bank.json,
                                              bank_decals.png + bank_decals.json, roots_preview.jpg
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


def pack(sizes):
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])
    x, y, shelf, rects = PAD, PAD, 0, {}
    for i in order:
        w, h = sizes[i]
        if x + w + PAD > ATLAS_W:
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
    print("OK" if ok else "FAIL")
    return ok


def main(a):
    if not a or a[0] not in ("build", "check"):
        raise SystemExit(__doc__)
    if a[0] == "check":
        sys.exit(0 if check() else 1)
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    only = a[1] if len(a) > 1 else "all"
    if only in ("all", "bank"):
        build_bank(OUT)
        print(f"bank: {time.time() - t0:.0f} s")
    if only in ("all", "decals", "dp"):
        build_decals(OUT)
        print(f"decals: {time.time() - t0:.0f} s")
    preview(OUT)
    print(f"done in {time.time() - t0:.0f} s -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
