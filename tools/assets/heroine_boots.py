"""Her boots made as a bootmaker makes them, not her skin lifted off her
(WIP, not yet wired into heroine_outfits.py and never yet run: see the
plan at the end). The shaft and foot of each boot are one surface laid out
as horizontal rings: each ring is the convex outline of her leg's cross
section at that height (no hollow between muscles is followed), stood off
by a clearance, and eased up and down the leg with a rising envelope, so no
calf muscle, ankle bone or toe shows through, and her skin stays inside.
The toe gets room ahead of her toes; below `wall` the boot is one upright
outline, where the welt and sole go on.

heroine_outfits.py calls bind(globals()) once its helpers exist."""
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from scipy.spatial import ConvexHull

G = None
M = 180                                    # directions each outline is held in
U = np.c_[np.cos(np.arange(M) * 2 * np.pi / M), np.sin(np.arange(M) * 2 * np.pi / M)]


def bind(g):
    global G
    G = g


def ramp(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


class Leg:
    """A leg's frame: its foot's way (`f` forward, `out` to her outside, in
    plan), its ankle and ball, and where its heel and toes end."""
    def __init__(self, sd):
        self.sd = sd
        self.ankle, self.ball = G["head"](f"foot_{sd}"), G["head"](f"ball_{sd}")
        f = (self.ball - self.ankle)[:2]
        self.f = f / np.linalg.norm(f)
        self.out = (1.0 if sd == "l" else -1.0) * np.array([-self.f[1], self.f[0]])
        P = G["P"]
        foot = P[(G["LEGW"][sd] > 0.5) & (P[:, 2] < 0.06)]
        yf = self.yf(foot)
        self.heel_yf, self.toe_yf, self.ball_yf = yf.min(), yf.max(), float(self.yf(self.ball[None])[0])

    def yf(self, p):
        """How far forward of her ankle, along her foot."""
        return (np.asarray(p)[:, :2] - self.ankle[:2]) @ self.f


def sections(leg, z_lo, z_hi, s_min, dz=0.001):
    """Her leg cut level every `dz` from z_lo to z_hi (its skin's triangles
    cut exactly): each cut's support (how far it reaches in each of the M
    directions), a point inside it, and its points."""
    P, TRI = G["P"], G["TRI"]
    keep = (G["LEGW"][leg.sd][TRI].min(1) > 0.3) & (G["LEG_S"][leg.sd][TRI].max(1) > s_min)
    T = TRI[keep]
    E = np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1), axis=0)
    a, b = P[E[:, 0]], P[E[:, 1]]
    zs = np.arange(z_lo, z_hi + dz / 2, dz)
    H = np.full((len(zs), M), np.nan)
    inner = np.zeros((len(zs), 2))
    pts = []
    for k, z in enumerate(zs):
        m = (a[:, 2] - z) * (b[:, 2] - z) < 0
        t = (z - a[m, 2]) / (b[m, 2] - a[m, 2])
        q = a[m, :2] + (b[m, :2] - a[m, :2]) * t[:, None]
        pts.append(q)
        if len(q) >= 3:
            H[k], inner[k] = (q @ U.T).max(0), q.mean(0)
    ok = np.where(~np.isnan(H[:, 0]))[0]
    for k in np.where(np.isnan(H[:, 0]))[0]:   # (a cut with nothing in it takes the nearest that has)
        j = ok[np.argmin(np.abs(ok - k))]
        H[k], inner[k] = H[j], inner[j]
    return zs, H, inner, pts


def shaped(leg, st, zs, H):
    """The supports made a boot's: one upright outline below st['wall'],
    stood off by a clearance (st['c_foot'], ['c_ankle'], ['c_shaft']), room
    ahead of her toes (st['toe'], and st['toe_point'] for a narrower toe),
    then a rising envelope up and down her leg, wide on the shaft
    (st['w_shaft'], ['w_ankle']) and narrow over her foot and the front of
    her ankle (st['w_foot']), so the instep stays fitted. Every value
    only grows: whatever the envelope does, her skin stays inside by the
    clearance at least."""
    dz = zs[1] - zs[0]
    za = leg.ankle[2]
    H = H.copy()
    low = zs <= st["wall"]
    H[low] = H[low].max(0)
    H += np.interp(zs, [0, za - 0.03, za - 0.005, za + 0.06, za + 0.12],
                   [st["c_foot"], st["c_foot"], st["c_ankle"], st["c_ankle"], st["c_shaft"]])[:, None]
    fw = np.clip(U @ leg.f, 0, None)
    H += (st["toe"] * fw[None, :] + st.get("toe_point", 0.0) * fw[None, :] ** 6) * (1 - ramp(zs, 0.035, 0.075))[:, None]
    win = np.interp(zs, [0, 0.05, za, za + 0.05, za + 0.12],
                    [st["w_foot"], st["w_foot"], st["w_ankle"], st["w_ankle"], st["w_shaft"]])
    inst = (1 - ramp(zs, za + 0.02, za + 0.08))[:, None] * ramp(U @ leg.f, 0.2, 0.7)[None, :]
    wk = win[:, None] * (1 - inst) + st["w_foot"] * inst
    L = np.array(sorted({st["w_foot"], st["w_ankle"], st["w_shaft"]}))
    env = []
    for w in L:
        n = max(int(round(w / dz)), 1)
        e = maximum_filter1d(H, size=2 * n + 1, axis=0, mode="nearest")
        env.append(gaussian_filter1d(e, sigma=n / 2.5, axis=0, mode="nearest", truncate=2.5))
    if len(L) == 1:
        return env[0]
    E = np.stack(env)
    i = np.clip(np.searchsorted(L, wk), 1, len(L) - 1)
    t = np.clip((wk - L[i - 1]) / (L[i] - L[i - 1]), 0, 1)
    kk, jj = np.indices(H.shape)
    return E[i - 1, kk, jj] * (1 - t) + E[i, kk, jj] * t


def outline(h, o):
    """The convex outline whose supports are h (the half-planes x.u <= h
    met), from a point o inside it; counter-clockwise from above."""
    d = h - U @ o
    hull = ConvexHull(U / d[:, None])
    A, da = U[hull.vertices], d[hull.vertices]
    B, db = np.roll(A, -1, 0), np.roll(da, -1)
    det = A[:, 0] * B[:, 1] - A[:, 1] * B[:, 0]
    return np.c_[(da * B[:, 1] - db * A[:, 1]) / det, (A[:, 0] * db - B[:, 0] * da) / det] + o


def ring(poly, back, n):
    """An outline laid out as n points evenly round it, the first straight
    behind its middle (where the back seam runs)."""
    c = poly.mean(0)
    a, e = poly, np.roll(poly, -1, 0) - poly
    # (the ray c + t*back against each edge a + s*e)
    den = back[0] * (-e[:, 1]) - back[1] * (-e[:, 0])
    rx, ry = a[:, 0] - c[0], a[:, 1] - c[1]
    t = (rx * (-e[:, 1]) - ry * (-e[:, 0])) / np.where(np.abs(den) > 1e-12, den, 1e-12)
    s = (back[0] * ry - back[1] * rx) / np.where(np.abs(den) > 1e-12, den, 1e-12)
    hit = np.where((t > 0) & (s >= 0) & (s <= 1))[0][0]
    start = a[hit] + e[hit] * s[hit]
    loop = np.vstack([start, np.roll(poly, -(hit + 1), 0), start])
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(loop, axis=0), axis=1))]
    q = np.arange(n) * L[-1] / n
    return np.c_[np.interp(q, L, loop[:, 0]), np.interp(q, L, loop[:, 1])]


def rings(leg, st, z_top, s_min, n=144, step=0.003, dz_most=0.006):
    """The boot's inner surface as rings, top down to the floor: chosen from
    cuts 1 mm apart so no ring moves more than `step` from the last (close
    over the instep and toe, far apart up the plain shaft). Returns the
    rings' heights and points (n each, round from the back)."""
    zs, H, inner, _ = sections(leg, 0.0015, z_top, s_min)
    Hs = shaped(leg, st, zs, H)
    R = [ring(outline(Hs[k], inner[k]), -leg.f, n) for k in range(len(zs))]
    pick, last = [len(zs) - 1], len(zs) - 1
    for k in range(len(zs) - 2, -1, -1):
        if np.abs(R[k] - R[last]).max() > step or zs[last] - zs[k] >= dz_most or k == 0:
            pick.append(k)
            last = k
    return zs[pick], np.array([R[k] for k in pick])


def grid(zr, R):
    """Rings made a sheet (normals out, away from her)."""
    K, n = R.shape[:2]
    pos = np.c_[R.reshape(-1, 2), np.repeat(zr, n)]
    k, i = np.meshgrid(np.arange(K - 1), np.arange(n), indexing="ij")
    a, b = k * n + i, k * n + (i + 1) % n
    c, d = b + n, a + n
    tris = np.vstack([np.c_[a.ravel(), b.ravel(), c.ravel()], np.c_[a.ravel(), c.ravel(), d.ravel()]])
    nrm = G["vertex_normals"](pos, tris)
    cen = np.repeat(R.mean(1), n, 0)
    if (((pos[:, :2] - cen) * nrm[:, :2]).sum(1)).mean() < 0:
        tris = tris[:, ::-1]
    return pos, tris


# ---------------------------------------------------------------- the plan --
# Still to build (measured on her: ball on the floor, heel pad 4 mm up, arch
# 8-10 mm up outside and 13-21 mm inside, toe tip 27 mm tall, foot 27 cm):
#  - clip the grid with clip(): its top by the leg's S (front dip per outfit),
#    its foot at the welt line z_w(yf) - 1.2 mm; within ~6 cm of the top blend
#    each ring toward her skin's own cut + 2.5 mm (a fitted top, skin weights).
#  - the sole as a cup (her foot stays flat, so a sole under her would be under
#    the floor): outline = bottom ring's supports + thick + 3 mm; bottom z_b(yf)
#    = -sink, toe spring rising ahead of the ball, shank rising to the breast;
#    top z_w = z_b + t_sole. Heel block under it behind the breast, 3 lifts.
#    Welt: tube() on the welt line, stitches() on its top.
#  - weights: shaft from her skin's, smoothed along her (ADJ) wider at the
#    ankle; the foot, sole and heel only foot/ball by yf; heel block foot.
#  - creases as outward ridges (ankle stacking, toe break), back seam tube +
#    stitches, toe cap and heel counter overlays, cuffs (turned down, a fold
#    tube along the top), ranger laces (grommets + cords on the shaft),
#    reaver garters (helical straps, hide bulging between).
#  - her skin inside tucked whole: the tuck rule today stops at 4.5 mm off a
#    piece; boots need a "deep" rule (ray 30 mm, eased in below the top).
#  - grime from the floor up in the vertex colour's alpha (1 everywhere today)
#    and wear/polish/flat from outfit_materials.json into the shader.
