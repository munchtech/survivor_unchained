"""The Long Cut's seam: one 24 m crack strip baked to maps (godot/art/fx/longcut/), a natural fracture, not a tube.

    python tools/fxsim/longcut_crack.py [--seed 7] [--out godot/art/fx/longcut] [--px 4096x512] [--preview OUT.jpg]

U runs along the line (0 = her end, 1 = the tip), V across a 2.4 m band (0.5 = the line). Everything is built in
metres (the strip's texels are not square), so the same seed gives the same crack at any resolution.
Writes crack_albedo.png (RGBA, alpha = coverage), crack_normal.png (OpenGL, Y+), crack_emis.png (the hot core),
crack_height.png (16-bit; 0..1 = H_LO..H_HI metres), the same cut into 12 tiles crack_<map>_00..11.png (2 m each,
384x512), and crack.json (the numbers the shader needs).

The crack: a fracture path of straight-ish runs with angular jogs (a random walk pulled back to the line), opening
from ~0.40 m at her end to ~0.10 m near the tip and closing to a hairline; both walls follow the same jagged edge (the
two sides of a split fit). 2-4 side forks near her end. Raised lips of broken plates (Voronoi slabs, each tilted
up toward the gap), hairline cracks between them; char black-brown near the gap fading out into the ground; rubble
lying in the gap shadows the light in places, so the glow never runs as an even tube.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

L_M, B_M = 24.0, 2.4          # strip length and band width, metres
H_LO, H_HI = -0.30, 0.10      # the height map's range, metres


def opt(k, d, t=str):
    a = sys.argv
    return t(a[a.index(k) + 1]) if k in a else d


# ---------------------------------------------------------------- noise (metric, seeded, never periodic)
class Noise:
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.tabs = {}

    def vnoise(self, x, y, f, key):
        """Value noise (quintic), frequency f per metre, -1..1, its own random lattice per key, rotated/offset."""
        if key not in self.tabs:
            r = self.rng
            ang = r.uniform(0, math.pi)
            off = r.uniform(0, 50, 2)
            n = min(int((L_M + B_M + 4) * f * 1.5) + 8, 2048)  # (wraps only for fine grain, metres apart)
            self.tabs[key] = (ang, off, r.random((n, n), dtype=np.float32) * 2 - 1)
        ang, off, tab = self.tabs[key]
        c, s = math.cos(ang), math.sin(ang)
        X = (x * c - y * s) * f + off[0] + (B_M + 2) * f
        Y = (x * s + y * c) * f + off[1] + (B_M + 2) * f
        xi = np.floor(X).astype(np.int64); yi = np.floor(Y).astype(np.int64)
        tx = (X - xi).astype(np.float32); ty = (Y - yi).astype(np.float32)
        tx = tx * tx * tx * (tx * (tx * 6 - 15) + 10); ty = ty * ty * ty * (ty * (ty * 6 - 15) + 10)
        n = tab.shape[0]
        xi %= n; yi %= n; x1 = (xi + 1) % n; y1 = (yi + 1) % n
        a = tab[xi, yi] + (tab[x1, yi] - tab[xi, yi]) * tx
        b = tab[xi, y1] + (tab[x1, y1] - tab[xi, y1]) * tx
        return a + (b - a) * ty

    def fbm(self, x, y, f, key, oct=5, gain=0.5, lac=2.03):
        s, a, norm = 0.0, 1.0, 0.0
        for i in range(oct):
            s = s + a * self.vnoise(x, y, f * lac ** i, f"{key}{i}")
            norm += a; a *= gain
        return s / norm


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- the fracture path
def swing(rng, x):
    """The split's slow swing (r3c: the judge's "lightning-fine zigzag on a straight path"): 0.6-1 m side to side over
    every 4-6 m, its own length and size each time, starting on the line at her end."""
    knots_x, knots_y = [0.0], [0.0]
    side = 1 if rng.random() < 0.5 else -1
    xx = rng.uniform(2.0, 3.0)
    while xx < L_M + 6:
        knots_x.append(xx); knots_y.append(side * rng.uniform(0.30, 0.50))
        side = -side; xx += rng.uniform(4.0, 6.0)
    kx, ky = np.array(knots_x), np.array(knots_y)
    # cosine-eased between knots: a bend, never a corner
    i = np.clip(np.searchsorted(kx, x) - 1, 0, len(kx) - 2)
    t = np.clip((x - kx[i]) / (kx[i + 1] - kx[i]), 0, 1)
    t = 0.5 - 0.5 * np.cos(np.pi * t)
    return ky[i] + (ky[i + 1] - ky[i]) * t


def path(rng, nx, xs):
    """The crack's centreline y(x): the slow swing, and about it straight-ish runs of 0.25-1.1 m with angular jogs
    (half the r3b zigzag), then a fine jagged jitter both walls share."""
    rs = np.random.default_rng(int(rng.integers(1 << 30)))
    pts = [(0.0, 0.0)]
    x, y = 0.0, 0.0
    drift, zig = 0.0, 1
    while x < L_M + 1:
        # a fracture zigzags: short straight runs at alternating-ish angles about a slow drift, now and then a long
        # straight run or a hard jog sideways; the drift is pulled back so it never leaves the band
        drift = float(np.clip(0.85 * drift + rng.normal(0, 0.06) - 0.25 * y, -0.3, 0.3))
        r = rng.random()
        if r < 0.12:
            run, ang = rng.uniform(0.5, 1.0), drift + rng.normal(0, 0.05)          # a long clean run
        elif r < 0.22:
            run, ang = rng.uniform(0.05, 0.12), drift + zig * rng.uniform(0.4, 0.55)  # a hard step
        else:
            zig = -zig if rng.random() < 0.75 else zig
            run, ang = rng.uniform(0.08, 0.40), drift + zig * rng.uniform(0.06, 0.28)
        x += run * math.cos(ang); y += run * math.sin(ang)
        y = float(np.clip(y, -0.15, 0.15))
        pts.append((x, y))
    px, py = np.array(pts).T
    yc = np.interp(xs, px, py) + swing(rs, xs) * np.clip(xs / 1.5, 0, 1)
    # soften the corners a touch (a real split rounds its jogs over a centimetre or two), keep the angles
    yc = ndimage.gaussian_filter1d(yc, 0.012 / (L_M / nx))
    return yc


def main():
    seed = opt("--seed", 7, int)
    out = opt("--out", "godot/art/fx/longcut")
    W, H = [int(v) for v in opt("--px", "4096x512").split("x")]
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(seed)
    N = Noise(seed + 1000)
    xs = (np.arange(W) + 0.5) * L_M / W                     # metres along
    ys = (np.arange(H) + 0.5) * B_M / H - B_M / 2           # metres across (row 0 = V 0 = -1.2)
    X, Y = np.meshgrid(xs.astype(np.float32), ys.astype(np.float32))
    u = X / L_M
    dx, dy = L_M / W, B_M / H

    # ---- centreline + shared jagged edge (fine fracture teeth: both walls follow it)
    yc = path(rng, W, xs)
    teeth = 0.011 * N.fbm(xs, np.zeros_like(xs), 9.0, "teeth", oct=4, gain=0.55)
    teeth += 0.004 * N.fbm(xs, np.zeros_like(xs), 40.0, "teeth2", oct=2)
    ycj = (yc + teeth).astype(np.float32)
    # true distance to the path (a hard jog runs nearly across the band: a vertical-only measure spikes there), the
    # path sampled every 2.5 mm; the teeth bend only the walls (fading out a few cm away)
    fx = np.arange(0, L_M, 0.0025)
    q = np.stack([X.ravel(), Y.ravel()], -1)

    def pdist(yy):
        dd, ii = cKDTree(np.stack([fx, np.interp(fx, xs, yy)], -1)).query(q, workers=-1)
        return dd.reshape(X.shape).astype(np.float32)
    d_s = pdist(yc); d_t = pdist(ycj)
    near = np.exp(-d_s / 0.06)
    d = d_s + (d_t - d_s) * near
    sd = d * np.sign(Y - yc[None, :] + 1e-6)

    # ---- width: 0.40 m at her end to 0.10 m at u 0.93, then closing to a hairline at the tip (u 0.985)
    uu = xs / L_M
    w = np.interp(uu, [0.0, 0.015, 0.06, 0.5, 0.93, 0.975, 0.985], [0.0, 0.30, 0.42, 0.24, 0.10, 0.035, 0.0])
    w *= 1 + 0.22 * N.fbm(xs, np.zeros_like(xs), 0.9, "wmod", oct=3)        # pinches and bellies
    w = np.maximum(w, 0).astype(np.float32)
    hw = w[None, :] / 2
    # the two walls are not exact: each side its own small give
    zx0 = np.zeros_like(xs)
    side_t = smooth(-0.6, 0.6, sd / np.maximum(hw, 1e-3))
    give = 0.010 * (N.fbm(xs, zx0, 22.0, "giveL", oct=2)[None, :] * (1 - side_t) + N.fbm(xs, zx0, 22.0, "giveR", oct=2)[None, :] * side_t)
    hw_s = np.maximum(hw + give * (hw > 0.004), 0)

    # ---- forks: 2-4 near her end, angled forward, tapering to nothing
    fork_d = np.full_like(X, 9.0); fork_hw = np.zeros_like(X)
    nf = int(rng.integers(3, 7))
    for i in range(nf):
        x0 = rng.uniform(0.8, 6.0) if i else rng.uniform(0.7, 2.0)
        side = 1 if (i % 2 == 0) ^ (rng.random() < 0.3) else -1
        i0 = int(x0 / dx)
        p = [(x0, float(ycj[i0]) + side * w[i0] * 0.35)]
        base = side * rng.uniform(0.4, 0.8)
        Lf = rng.uniform(0.35, 1.0); s = 0.0; zig = 1
        while s < Lf:
            # the same zigzag as the main split, about a heading that bends back toward the line's own direction
            run = rng.uniform(0.05, 0.22)
            zig = -zig if rng.random() < 0.7 else zig
            base *= 0.93
            ang = base + zig * rng.uniform(0.12, 0.4)
            px_, py_ = p[-1]
            nx_, ny_ = px_ + run * math.cos(ang), py_ + run * math.sin(ang)
            ny_ = float(np.clip(ny_, -0.9, 0.9))
            p.append((nx_, ny_)); s += run
        P = np.array(p)
        seg_s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        # bbox pixels only
        bx0, bx1 = max(0, int((P[:, 0].min() - 0.2) / dx)), min(W, int((P[:, 0].max() + 0.2) / dx) + 1)
        by0, by1 = max(0, int((P[:, 1].min() + B_M / 2 - 0.2) / dy)), min(H, int((P[:, 1].max() + B_M / 2 + 0.2) / dy) + 1)
        sx, sy = X[by0:by1, bx0:bx1], Y[by0:by1, bx0:bx1]
        best = np.full(sx.shape, 9.0, np.float32); bs = np.zeros(sx.shape, np.float32)
        for k in range(len(P) - 1):
            a, b = P[k], P[k + 1]
            ab = b - a; l2 = ab @ ab
            t_ = np.clip(((sx - a[0]) * ab[0] + (sy - a[1]) * ab[1]) / l2, 0, 1)
            dd = np.hypot(sx - a[0] - t_ * ab[0], sy - a[1] - t_ * ab[1])
            m = dd < best
            best[m] = dd[m]; bs[m] = (seg_s[k] + t_ * np.sqrt(l2))[m]
        f0 = min(0.13, w[i0] * 0.45) * rng.uniform(0.75, 1.0)
        fh = f0 / 2 * np.clip(1 - bs / Lf, 0, 1) ** 0.8
        sub_d = fork_d[by0:by1, bx0:bx1]; sub_h = fork_hw[by0:by1, bx0:bx1]
        # keep the nearer / wider (by margin) of the forks
        better = (best - fh) < (sub_d - sub_h)
        sub_d[better] = best[better]; sub_h[better] = fh[better]

    # ---- combined "inside the gap" depth fraction g (1 at the deepest, 0 at the wall's top)
    ragged = 1 + 0.18 * N.fbm(X, Y, 14.0, "rag", oct=3)
    g_main = np.clip(1 - d / np.maximum(hw_s * ragged, 1e-4), 0, 1) * (hw_s > 0.002)
    g_fork = np.clip(1 - fork_d / np.maximum(fork_hw * ragged, 1e-4), 0, 1) * (fork_hw > 0.002)
    g = np.maximum(g_main, g_fork * 0.8)
    # the floor's bright slit wanders between the walls and swells and thins (the gap is never lit as an even tube)
    zx = np.zeros_like(xs)
    off = (0.38 * N.fbm(xs, zx, 2.2, "slit", oct=3))[None, :]
    kf = (0.42 + 0.18 * N.fbm(xs, zx, 3.1, "slitw", oct=2))[None, :]
    gf = np.clip(1 - np.abs(sd / np.maximum(hw_s, 1e-4) - off) / kf, 0, 1) * (g_main > 0)
    gf = np.maximum(gf, smooth(0.3, 1.0, g_fork) * 0.8)
    edge = np.minimum(d - hw_s, np.where(fork_hw > 0.002, fork_d - fork_hw, 9.0))   # metres outside the nearest wall
    edge = np.maximum(edge, 0)

    # ---- the lips: Voronoi plates, each a flat slab tilted up toward the gap
    # (r3c: the broken lips and the scorch stay within the crack's own width each side, so the whole mark is at most
    # twice the opening: at 0.2-0.45 m of lips and 0.55-0.9 m of char it read as a 90 px black ribbon at night)
    lipw = (0.015 + 0.30 * w[None, :]) * (1 + 0.25 * N.fbm(X, Y, 1.4, "lipw", oct=3))       # how far the break runs
    rngp = np.random.default_rng(seed + 7)
    pts = []
    for cell in (0.13, 0.24):
        nxp, nyp = int(L_M / cell), int(B_M / cell)
        gx, gy = np.meshgrid((np.arange(nxp) + 0.5) * cell, (np.arange(nyp) + 0.5) * cell - B_M / 2)
        jit = rngp.uniform(-0.45, 0.45, (2,) + gx.shape) * cell
        pp = np.stack([gx + jit[0], gy + jit[1]], -1).reshape(-1, 2)
        # small plates near the gap, big ones farther out
        di = np.abs(pp[:, 1] - np.interp(pp[:, 0], xs, ycj))
        keep = (di < 0.30) if cell < 0.2 else (di >= 0.26)
        pts.append(pp[keep])
    pts = np.concatenate(pts)
    # warp the lookup so the plates are not convex-perfect
    wx = X + 0.018 * N.fbm(X, Y, 18.0, "pw1", oct=2); wy = Y + 0.018 * N.fbm(X, Y, 18.0, "pw2", oct=2)
    tree = cKDTree(pts)
    q = np.stack([wx.ravel(), wy.ravel()], -1)
    dist, idx = tree.query(q, k=2, workers=-1)
    f1 = dist[:, 0].reshape(X.shape).astype(np.float32); f2 = dist[:, 1].reshape(X.shape).astype(np.float32)
    cid = idx[:, 0].reshape(X.shape)
    border = (f2 - f1)                                       # ~0 on a plate's border
    seed_pts = pts[cid]
    seed_d = np.abs(seed_pts[..., 1] - np.interp(seed_pts[..., 0], xs, ycj))
    seed_edge = np.maximum(seed_d - np.interp(seed_pts[..., 0], xs, w) / 2, 0)
    crand = np.random.default_rng(seed + 9).random((len(pts), 3)).astype(np.float32)[cid]
    lipzone = 1 - smooth(0.0, 1.0, edge / lipw)              # 1 at the wall, 0 where the break ends
    seed_zone = 1 - smooth(0.0, 1.0, seed_edge / lipw)
    # lift: a plate near the wall is shoved up and tipped toward the gap
    lift_amt = (0.045 + 0.04 * (1 - u)) * (0.6 + 0.8 * crand[..., 0])
    plate_h = lift_amt * seed_zone ** 1.4 + (seed_edge - edge) * 0.35 * seed_zone * (0.5 + crand[..., 1])
    plate_h += 0.010 * (crand[..., 2] - 0.5) * seed_zone
    gap_cracks = smooth(0.0, 0.006, border)                  # 0 on a crack between plates
    crack_depth = (1 - gap_cracks) * seed_zone * 0.02
    # fine grain on every surface
    grain = 0.004 * N.fbm(X, Y, 60.0, "grain", oct=3) + 0.010 * N.fbm(X, Y, 7.0, "lump", oct=3)

    # hairline cracks out across the char (ridged noise), fewer far out
    rid = np.abs(N.fbm(X, Y, 3.2, "rid", oct=4, gain=0.55))
    hair = (1 - smooth(0.0, 0.025, rid)) * (1 - smooth(0.15, 0.9, edge)) * (edge > 0)

    # ---- height (metres)
    depth = (0.10 + 0.22 * (w[None, :] / 0.42))             # a wide gap is a deep one
    depth = np.where(g_main >= g_fork * 0.8, depth, 0.03 + 0.22 * (2 * fork_hw / 0.42))   # and a fork as deep as it is wide
    wall = g ** 0.55                                       # steep walls, deep floor
    h_gap = -depth * wall
    # rubble lying in the gap: blocks that sit up out of the dark floor
    # (angular: Voronoi pieces, about one in four a block, wedged at the walls' height or fallen deeper)
    rr = np.random.default_rng(seed + 11)
    nrub = int(L_M / 0.05)
    rpts = np.stack([rr.uniform(0, L_M, nrub * 3), np.zeros(nrub * 3)], -1)
    rpts[:, 1] = np.interp(rpts[:, 0], xs, yc) + rr.normal(0, 0.06, len(rpts))
    rd, ri = cKDTree(rpts).query(np.stack([wx.ravel(), wy.ravel()], -1), k=2, workers=-1)
    rb = (rd[:, 1] - rd[:, 0]).reshape(X.shape)
    rsel = rr.random((len(rpts), 2)).astype(np.float32)[ri[:, 0].reshape(X.shape)]
    rclump = N.vnoise(X, Y, 1.3, "rclump") * 0.5 + 0.5
    rub = (rsel[..., 0] < 0.25 * rclump ** 1.5) * smooth(0.0, 0.004, rb) * (g > 0.08)
    rub_h = 0.25 + 0.55 * rsel[..., 1]                      # how high the block sits (fraction of the depth)
    h_gap = np.where(rub > 0.5, -depth * rub_h * wall ** 0.3 + 0.01 * N.vnoise(X, Y, 50, "rubg"), h_gap)
    h = np.where(g > 0, h_gap, plate_h * lipzone ** 0.3 - crack_depth - hair * 0.006) + grain
    h = np.clip(h, H_LO, H_HI).astype(np.float32)

    # ---- coverage (alpha): the scorch, wider at her end, ragged, fully out by the band's edges
    reach = (0.02 + 0.48 * w[None, :]) * (1 + 0.45 * N.fbm(X, Y, 2.3, "reach", oct=4))   # noisy, never parallel
    char = 1 - smooth(0.0, 1.0, edge / np.maximum(reach, 0.015))
    char = np.clip(char + 0.35 * N.fbm(X, Y, 9.0, "charn", oct=3) * char * (1 - char) * 4, 0, 1)
    # the scorch only half-paints (darkening the ground at most ~40%); the gap and the lips are the crack itself
    alpha = np.maximum(char ** 0.8 * 0.45, (g > 0) * 1.0)
    alpha = np.maximum(alpha, lipzone * 0.98)
    endfade = smooth(0.0, 0.25, X) * (1 - smooth(L_M - 0.6, L_M - 0.15, X))
    # past the tip the whole mark thins out to nothing (the scorch follows the crack's own reach)
    tipfade = 1 - smooth(0.955, 0.995, u)
    bandfade = 1 - smooth(0.95, 1.17, np.abs(Y))
    alpha = alpha * endfade * bandfade * (0.25 + 0.75 * tipfade) * np.where(u > 0.985, tipfade * 2, 1).clip(0, 1)
    alpha = np.clip(alpha, 0, 1).astype(np.float32)

    # ---- albedo (linear), then sRGB
    rock = np.array([0.050, 0.043, 0.036], np.float32)
    charc = np.array([0.020, 0.016, 0.013], np.float32)
    soot = np.array([0.030, 0.024, 0.019], np.float32)
    var = (0.75 + 0.5 * crand[..., 0])[..., None]
    plate_col = rock * var * (0.85 + 0.3 * crand[..., 1:2])
    # the plates near the wall are charred; farther ones only sooted
    burn = (1 - smooth(0.0, 0.7, edge / np.maximum(lipw, 0.1)))[..., None]
    col = plate_col * (1 - burn) + charc * burn * (0.8 + 0.4 * crand[..., 2:3])
    # out on the scorch: soot fading off
    col = np.where((lipzone > 0.02)[..., None], col, soot[None, None] * (0.8 + 0.5 * (0.5 + 0.5 * N.fbm(X, Y, 4.0, "sootv", oct=3)))[..., None])
    # broken faces: the fresh rock on a plate's raised edge is a shade lighter and warmer
    fresh = (smooth(0.006, 0.0, edge) * (g == 0))[..., None]
    col = col * (1 - fresh * 0.6) + np.array([0.11, 0.075, 0.05], np.float32) * fresh * 0.6
    # the cracks between plates and the hairlines: black
    col *= 0.35 + 0.65 * gap_cracks[..., None] ** 0.5
    col *= (1 - 0.6 * hair[..., None])
    # inside the gap: dark heat-tempered rock (a little rust), the rubble darker
    gapc = np.array([0.026, 0.016, 0.011], np.float32) * (1 - 0.5 * rub[..., None])
    col = np.where((g > 0)[..., None], gapc * (0.8 + 0.4 * (0.5 + 0.5 * N.fbm(X, Y, 20.0, "gapv", oct=2)))[..., None], col)
    # ash: a few pale grey flecks out on the scorch (where the heat blew the char to ash)
    ash = 0.6 * smooth(0.70, 0.85, N.fbm(X, Y, 28.0, "ash", oct=3) * 0.5 + 0.5) * (1 - lipzone) * char
    col = col * (1 - ash[..., None] * 0.7) + np.array([0.20, 0.19, 0.18], np.float32) * ash[..., None] * 0.7
    col *= (1 + 0.12 * N.fbm(X, Y, 30.0, "colgrain", oct=2))[..., None]
    col = np.clip(col, 0, 1)

    # ---- emission: 1 deep in the gap, falling off up the walls; a thin rim on the lips; hot fissures nearby
    along = 0.78 + 0.22 * N.fbm(xs, np.zeros_like(xs), 0.6, "along", oct=3)         # irregular hot knots, no rhythm
    along = along * np.interp(uu, [0, 0.6, 0.97, 1.0], [1.0, 0.9, 0.7, 0.0])
    # the floor is the light; the walls catch it faintly, rising to it
    e = (0.92 * smooth(0.15, 1.0, gf) ** 1.5 + 0.08 * smooth(0.0, 0.6, g)) * along[None, :]
    e *= 1 - 0.85 * rub                                    # rubble blocks the light
    e += rub * smooth(0.004, 0.0, rb) * 0.5 * (g > 0.2)    # ...with its cracks shining through
    # (r3c: no glow on the lips or their seams: the embers live inside the crack)
    e = np.clip(e, 0, 1) * endfade

    # ---- normal from height (OpenGL: green = up the image)
    hs = ndimage.gaussian_filter(h, (0.6, 0.6))
    gy_, gx_ = np.gradient(hs, dy, dx)                     # per metre: rows (down the image), columns
    nx_, ny_ = -gx_, gy_                                    # n ∝ (-dh/dx, -dh/dy_up, 1), y_up = -row
    nz = np.ones_like(nx_)
    ln = np.sqrt(nx_ ** 2 + ny_ ** 2 + nz ** 2)
    nrm = np.stack([nx_ / ln, ny_ / ln, nz / ln], -1)

    def srgb8(a):
        a = np.clip(a, 0, 1)
        return (np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055) * 255 + 0.5).astype(np.uint8)

    maps = {
        "albedo": Image.fromarray(np.dstack([srgb8(col), (alpha * 255 + 0.5).astype(np.uint8)]), "RGBA"),
        "normal": Image.fromarray(((nrm * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), "RGB"),
        "emis": Image.fromarray((e * 255 + 0.5).astype(np.uint8), "L"),
        "height": Image.fromarray(((h - H_LO) / (H_HI - H_LO) * 65535 + 0.5).astype(np.uint16), "I;16"),
    }
    for k, im in maps.items():
        im.save(os.path.join(out, f"crack_{k}.png"), optimize=True)
        # 12 tiles of 2 m: resampled from the strip (4096/12 is not whole), 384x512 each
        big = im if k != "height" else Image.fromarray(np.array(im).astype(np.float32), "F")
        big = big.resize((384 * 12, H), Image.LANCZOS)
        for i in range(12):
            tile = big.crop((384 * i, 0, 384 * (i + 1), H))
            if k == "height":
                tile = Image.fromarray(np.clip(np.array(tile), 0, 65535).astype(np.uint16), "I;16")
            elif k == "normal":
                a = np.array(tile).astype(np.float32) / 127.5 - 1
                a /= np.linalg.norm(a, axis=-1, keepdims=True) + 1e-6
                tile = Image.fromarray(((a * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), "RGB")
            tile.save(os.path.join(out, f"crack_{k}_{i:02d}.png"), optimize=True)
    gw = [float(np.interp(v, uu, w)) for v in (0.0, 0.05, 0.25, 0.5, 0.75, 0.93, 0.98)]
    json.dump({"length_m": L_M, "band_m": B_M, "u": "along the line, 0 = her end", "v": "across, 0.5 = the line",
               "height_range_m": [H_LO, H_HI], "normal": "OpenGL (Y+)", "seed": seed, "tiles": 12, "tile_m": 2.0,
               "centre_m": [round(float(v), 4) for v in np.interp((np.arange(256) + 0.5) / 256 * L_M, xs, yc)],
               "gap_width_m_at_u": dict(zip(["0", "0.05", "0.25", "0.5", "0.75", "0.93", "0.98"], [round(v, 3) for v in gw])),
               "source": "tools/fxsim/longcut_crack.py"},
              open(os.path.join(out, "crack.json"), "w"), indent=1)
    print("gap widths", [round(v, 3) for v in gw], "forks", nf)

    pv = opt("--preview", "")
    if pv:
        # a quick lit look: a low raking moon + soft sky over a dark dirt ground, the core glowing gold
        Ld = np.array([0.55, 0.35, 0.76]); Ld /= np.linalg.norm(Ld)
        lam = np.clip((nrm * Ld).sum(-1), 0, 1)[..., None]
        ground = np.array([0.10, 0.085, 0.065], np.float32)
        lit = col * (0.25 + 1.1 * lam)
        img = ground * (0.25 + 1.1 * lam[..., :]) * 0 + ground * 0.6
        img = img * (1 - alpha[..., None]) + lit * alpha[..., None]
        img = img + e[..., None] * np.array([1.6, 0.85, 0.30], np.float32) * 1.0
        img = img / (1 + img)  # soft rolloff
        Image.fromarray(srgb8(img * 1.6)).save(pv, quality=92)


main()
