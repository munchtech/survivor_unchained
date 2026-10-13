"""Her boots made as a bootmaker makes them, not her skin lifted off her
(WIP: the Ranger's are built by boot(); what is still to come is at the
end). The shaft and foot of each boot are one surface laid out
as horizontal rings: each ring is the convex outline of her leg's cross
section at that height (no hollow between muscles is followed), stood off
by a clearance, and eased up and down the leg with a rising envelope, so no
calf muscle, ankle bone or toe shows through, and her skin stays inside.
The toe gets room ahead of her toes; below `wall` the boot is one upright
outline, where the welt and sole go on.

heroine_outfits.py calls bind(globals()) once its helpers exist."""
import numpy as np
from scipy import sparse
from scipy.ndimage import gaussian_filter1d, maximum_filter1d, minimum_filter1d
from scipy.spatial import ConvexHull, cKDTree

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


def rings(leg, st, z_top, s_min, n=144, step=0.003, dz_most=0.006, fit=None):
    """The boot's inner surface as rings, top down to the floor: chosen from
    cuts 1 mm apart so no ring moves more than `step` from the last (close
    over the instep and toe, far apart up the plain shaft). `fit(zs, H, Hs)`
    may change the shaped supports (a fitted top). Returns the rings'
    heights and points (n each, round from the back), and their supports
    and middles."""
    zs, H, inner, _ = sections(leg, 0.0015, z_top, s_min)
    Hs = shaped(leg, st, zs, H)
    if fit is not None:
        Hs = fit(zs, H, Hs)
    R = [ring(outline(Hs[k], inner[k]), -leg.f, n) for k in range(len(zs))]
    pick, last = [len(zs) - 1], len(zs) - 1
    for k in range(len(zs) - 2, -1, -1):
        if np.abs(R[k] - R[last]).max() > step or zs[last] - zs[k] >= dz_most or k == 0:
            pick.append(k)
            last = k
    return zs[pick], np.array([R[k] for k in pick]), Hs[pick], inner[pick]


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


# ------------------------------------------------------------ the boot --
# Measured on her: ball on the floor, heel pad 4 mm up, arch 8-10 mm up
# outside and 13-21 mm inside, toe tip 27 mm tall, foot 27 cm. Her foot
# stays flat, so a sole under her would be under the floor: the sole is a
# solid cup round the bottom of her foot instead, its edge above the floor.

# The Ranger's: a plain riding boot. Clearances (c_*) and envelopes (w_*) as
# shaped() takes them; `wall`, the height the foot is one upright outline
# below; the sole sunk `sink` under the floor, `t_fore` thick ahead (so its
# top edge, the welt line, stands t_fore - sink up), the heel block's top
# `heel` up and the sole `t_heel` thick over it; the breast `breast` of the
# foot's length from the back of her heel; toe spring `spring` at the tip;
# the shank kept `margin` under her skin; the welt `welt_out` proud of the
# upper and `welt_h` tall.
RANGER = dict(wall=0.025, c_foot=0.003, c_ankle=0.0035, c_shaft=0.004, c_top=0.0035, toe=0.012, toe_point=0.003,
              w_foot=0.012, w_ankle=0.03, w_shaft=0.05,
              sink=0.002, t_fore=0.0065, heel=0.0095, t_heel=0.0055, breast=0.27, spring=0.004, margin=0.0015,
              welt_out=0.0035, welt_h=0.0025)
SHELL = {}       # each leg's upper as cut (its inner sheet: points, triangles), for what is fixed on it


def top_heights(leg, top_s, dip):
    """The boot's top edge: its height in each of the M directions round her
    leg, seen from the edge's middle (in plan), and that middle. The edge
    runs `top_s` down her leg (metres from the hip) in front, `dip` further
    down behind."""
    P, S = G["P"], G["LEG_S"][leg.sd]
    at = top_s + dip * (1 - G["FRONT"])
    Q = P[(G["LEGW"][leg.sd] > 0.5) & (np.abs(S - at) < 0.004)]
    c = Q[:, :2].mean(0)
    j = np.round(np.arctan2(Q[:, 1] - c[1], Q[:, 0] - c[0]) / (2 * np.pi / M)).astype(int) % M
    w = np.bincount(j, minlength=M)
    z = np.bincount(j, Q[:, 2], minlength=M) / np.maximum(w, 1)
    k, have = np.arange(M), np.where(w > 0)[0]
    z = np.interp(k, np.r_[have - M, have, have + M], np.tile(z[have], 3))
    return gaussian_filter1d(z, 4, mode="wrap"), c


def at_angle(zt, c, p):
    """The top edge's height over points p (round its middle c)."""
    a = np.mod(np.arctan2(p[:, 1] - c[1], p[:, 0] - c[0]), 2 * np.pi)
    return np.interp(a, np.arange(M + 1) * 2 * np.pi / M, np.r_[zt, zt[:1]])


class Sole:
    """The sole's lines along her foot (by yf): the welt line `zw` (its top
    edge, where the welt sits) and its bottom `zb`: sunk `sink` under the
    floor ahead, toe spring ahead of the ball, the shank rising behind it to
    the heel block's top at the breast `br`, but never within `margin` of
    her skin above (her arch is low outside)."""
    def __init__(self, leg, st):
        self.leg = leg
        yb, yh, yt = leg.ball_yf, leg.heel_yf, leg.toe_yf
        self.br = yh + st["breast"] * (yt - yh)
        ys = self.ys = np.arange(yh - 0.04, yt + 0.06, 0.001)
        fore = ramp(ys, self.br + 0.005, yb - 0.03)
        zw = st["heel"] + st["t_heel"] + (st["t_fore"] - st["sink"] - st["heel"] - st["t_heel"]) * fore
        zb = st["heel"] + (-st["sink"] - st["heel"]) * fore
        end = yt + st["toe"] + 0.009
        spring = st["spring"] * np.clip((ys - yb - 0.01) / (end - yb - 0.01), 0, 1) ** 2
        zw, zb = zw + spring, zb + spring
        P = G["P"]
        Q = P[(G["LEGW"][leg.sd] > 0.5) & (P[:, 2] < 0.06)]
        yq, zq = leg.yf(Q), Q[:, 2]
        low = np.full(len(ys), np.inf)
        for i, y in enumerate(ys):
            m = np.abs(yq - y) < 0.005
            if m.any():
                low[i] = zq[m].min()
        zb = np.where(ys < self.br - 0.004, zb, np.minimum(zb, low - st["margin"]))
        zb = gaussian_filter1d(minimum_filter1d(zb, 9, mode="nearest"), 2.5, mode="nearest")
        self.zb, self.zw = np.maximum(zb, -st["sink"]), zw

    def w(self, p):
        return np.interp(self.leg.yf(p), self.ys, self.zw)

    def b(self, p):
        return np.interp(self.leg.yf(p), self.ys, self.zb)


def rim(O):
    """A closed outline's outward normals and its way round (in plan)."""
    t = np.roll(O, -1, 0) - np.roll(O, 1, 0)
    t /= np.linalg.norm(t, axis=1)[:, None] + 1e-12
    n = np.c_[t[:, 1], -t[:, 0]]
    if ((O - O.mean(0)) * n).sum() < 0:
        n = -n
    return n, t


def behind(O, leg, y):
    """The part of a convex outline behind yf = y, closed by the straight
    line there (a heel's breast)."""
    v = leg.yf(O) - y
    out = []
    for i in range(len(O)):
        j = (i + 1) % len(O)
        if v[i] <= 0:
            out.append(O[i])
        if v[i] * v[j] < 0:
            out.append(O[i] + (O[j] - O[i]) * (v[i] / (v[i] - v[j])))
    return np.array(out)


def loft(loops, bottom, top):
    """A closed solid from loops of points (n each, in order from its bottom
    pole to its top pole): quads between loops, fans at the poles, faces
    out."""
    L = np.asarray(loops)
    K, n = L.shape[:2]
    pos = np.vstack([bottom[None], L.reshape(-1, 3), top[None]])
    i = np.arange(n)
    j = (i + 1) % n
    tris = [np.c_[np.zeros(n, int), 1 + j, 1 + i]]
    for k in range(K - 1):
        a, b = 1 + k * n + i, 1 + k * n + j
        tris += [np.c_[a, b, b + n], np.c_[a, b + n, a + n]]
    e = len(pos) - 1
    tris.append(np.c_[np.full(n, e), 1 + (K - 1) * n + i, 1 + (K - 1) * n + j])
    tris = np.vstack(tris)
    if np.einsum("ij,ij->i", pos[tris[:, 0]], np.cross(pos[tris[:, 1]], pos[tris[:, 2]])).sum() < 0:
        tris = tris[:, ::-1]
    return pos, tris


def rigid(leg, p):
    """Weights that hold a part rigid on her foot, bending only across the
    ball (the toe break)."""
    B = G["BONES"]
    w = np.zeros((len(p), len(B)))
    wb = ramp(leg.yf(p), leg.ball_yf - 0.012, leg.ball_yf + 0.012)
    w[:, B.index(f"foot_{leg.sd}")] = 1 - wb
    w[:, B.index(f"ball_{leg.sd}")] = wb
    return w


def skin_weights(sd, pos, sigma=0.008, k=24):
    """Her leg's skin weights under each point, weighed by nearness."""
    P, W = G["P"], G["W"]
    legv = np.where(G["LEGW"][sd] > 0.3)[0]
    d, j = cKDTree(P[legv]).query(pos, k=k)
    g = np.exp(-0.5 * (d / sigma) ** 2) + 1e-12
    A = sparse.csr_matrix((g.ravel(), (np.repeat(np.arange(len(pos)), k), j.ravel())), shape=(len(pos), len(legv)))
    return (A @ np.asarray(W[legv], float)) / g.sum(1)[:, None]


def boot(name, sd, top_s, dip, st, mkey, sole_key="darkleather", thick=0.0025, bevel=0.001, budget=16000):
    """A boot: its upper (shaft and foot, one sheet from rings()), cut at
    its top edge (`top_s` down her leg in front, `dip` lower behind) and
    down into the sole; the sole a solid cup round the bottom of her foot,
    its welt on top stitched; the heel block, three lifts, under the back.
    The sole, heel and the upper's foot and toe box ride her foot rigidly
    (bending only at the ball); the shaft takes her skin's weights, eased.
    Each part hides her skin deep under it (its 'deep_*' keys)."""
    g = G
    leg = Leg(sd)
    za, yb = leg.ankle[2], leg.ball_yf
    zt, tc = top_heights(leg, top_s, dip)
    sole = Sole(leg, st)

    # (a fitted top: from 6 cm under the edge up, the shaft closes in to her
    # own outline, `c_top` off it)
    def fit(zs, H, Hs):
        t = 1 - ramp(zt[None, :] - zs[:, None], 0.015, 0.06)
        return Hs * (1 - t) + np.minimum(Hs, H + st["c_top"]) * t
    zr, R, Hr, Ir = rings(leg, st, zt.max() + 0.015, top_s - 0.06, fit=fit)
    pos, tris = grid(zr, R)
    z, yf = pos[:, 2], leg.yf(pos)
    kr = np.maximum(1 - ramp(z, za - 0.035, za - 0.005), ramp(yf, yb - 0.035, yb - 0.01) * (1 - ramp(z, 0.05, 0.08)))
    wt = skin_weights(sd, pos) * (1 - kr)[:, None] + rigid(leg, pos) * kr[:, None]
    f = np.minimum(at_angle(zt, tc, pos) - z, z - (sole.w(pos) - 0.0012))
    pos, wt, tris = g["clip"](f, pos, wt, tris)
    pos, wt, tris = g["weld"](pos, wt, tris)
    SHELL[sd] = (pos.copy(), tris.copy())
    wt = g["four_bones"](g["eased_weights"](pos, tris, wt, over=0.012))
    made = [g["finish"](name, pos, wt, tris, mkey, thick, bevel, budget)]

    # The sole: under the upright foot's outline, `thick` + welt_out out.
    k0 = int(np.argmin(np.abs(zr - 0.012)))
    reach = thick + st["welt_out"]
    O = ring(outline(Hr[k0] + reach, Ir[k0]), -leg.f, 220)
    on, _ = rim(O)
    c = O.mean(0)
    bev = 0.0008
    loops = [np.c_[q, sole.b(q)] for q in (c + (O - on * bev - c) * s for s in np.linspace(0.1, 0.92, 9))]
    loops += [np.c_[O - on * bev, sole.b(O)], np.c_[O, sole.b(O) + bev], np.c_[O, sole.w(O) - bev * 0.6],
              np.c_[O - on * bev * 0.6, sole.w(O)]]
    loops += [np.c_[q, sole.w(q)] for q in (c + (O - on * bev - c) * s for s in np.linspace(0.92, 0.1, 5))]
    spos, stris = loft(loops, np.r_[c, sole.b(c[None])[0]], np.r_[c, sole.w(c[None])[0]])
    swt = rigid(leg, spos)
    made.append(g["finish"](name + "_sole", spos, swt, stris, sole_key, 0.0, 0.0, 10 ** 7))

    # The heel block: three lifts, under the sole behind the breast (its top
    # inside the sole), a hair inside the sole's edge.
    Oh = ring(behind(ring(outline(Hr[k0] + reach - 0.0004, Ir[k0]), -leg.f, 240), leg, sole.br), -leg.f, 180)
    hn, _ = rim(Oh)
    ch = Oh.mean(0)
    z0, z1 = -st["sink"], st["heel"] + 0.0005
    hb = 0.0007
    full = lambda v: np.full(len(Oh), v)
    loops = [np.c_[ch + (Oh - hn * hb - ch) * s, full(z0)] for s in np.linspace(0.12, 0.92, 6)]
    loops += [np.c_[Oh - hn * hb, full(z0)], np.c_[Oh, full(z0 + hb)]]
    for zl in z0 + (st["heel"] - z0) * np.array([1 / 3, 2 / 3]):
        loops += [np.c_[Oh, full(zl - 0.0003)], np.c_[Oh - hn * 0.00035, full(zl)], np.c_[Oh, full(zl + 0.0003)]]
    loops += [np.c_[Oh, full(z1)]]
    loops += [np.c_[ch + (Oh - ch) * s, full(z1)] for s in np.linspace(0.85, 0.12, 4)]
    hpos, htris = loft(loops, np.r_[ch, z0], np.r_[ch, z1])
    made.append(g["finish"](name + "_heel", hpos, rigid(leg, hpos), htris, sole_key, 0.0, 0.0, 10 ** 7))

    # The welt, on the sole's top edge round the upper, and its stitching.
    wl = R[k0]
    wn, _ = rim(wl)
    curve = np.c_[wl, sole.w(wl)]
    up = np.tile([0.0, 0.0, 1.0], (len(wl), 1))
    out3 = np.c_[wn, np.zeros(len(wl))]
    tg = np.roll(curve, -1, 0) - np.roll(curve, 1, 0)
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
    made.append(g["tube"](name + "_welt", curve, up, out3, sole_key, st["welt_out"] + 0.001, 0.0, reach, st["welt_h"],
                          spos, swt, closed=True, nv=12))
    made += g["stitches"](name + "_weltstitch", curve + out3 * (thick + st["welt_out"] * 0.55) + up * (st["welt_h"] - 0.0001),
                          up, tg, spos, swt, step=0.0035, length=0.0024, closed=True)
    for o in made:
        o["hides"] = o is made[0] or o.name.endswith(("_sole", "_heel"))
        if o["hides"]:
            o["deep_zt"] = [float(v) for v in zt]
            o["deep_c"] = [float(v) for v in tc]
            o["deep_side"] = sd
    print("BOOT %s: rings %d, sole sunk %.1f mm, welt line %.1f mm ahead and %.1f mm at the heel, shank %.1f mm up at the breast"
          % (name, len(zr), -1000 * sole.zb.min(), 1000 * float(np.interp(yb, sole.ys, sole.zw)),
             1000 * float(sole.zw[0]), 1000 * float(np.interp(sole.br + 0.002, sole.ys, sole.zb))))
    return made


# ------------------------------------------------------------ the sabaton --
# The Warden's: plate over her foot, matching her greaves, not a shoe. On the
# boot's shell (rings(): her foot's hull, clear of every toe), cut into steel
# plates as an armourer makes a sabaton: an instep plate wrapped round her heel
# as its cup, its top tucked up under the greave's foot; `lames` lames across
# her instep, each sliding under the one behind it (its front stood out
# `flare`, its back tucked in `tuck`, over `over`), each gold-edged along the
# edge that shows, a gold rivet each side; a rounded toe cap under the last.
# Under the greave, a thin dark lining runs up from under the plates to the
# top edge (it takes her skin's weights there as the boot's shaft did), so
# nothing opens at the ankle as she moves. Each plate is rigid on her foot
# (one blend, stepped from her foot to her toes across the ball), so none
# bends like leather. Under them a thin dark sole, flat (no welt, no
# stitching, no heel block), its edge `sole_out` proud of the plates.
# Clearances as the Ranger's (the shell is that boot's); `plate` thick,
# `lift` off the shell (the lining's room under them), `tuck_up` up under
# the greave's foot; the lames' front edges from `first` ahead of the
# greave's foot (along hers, on top) to `last` ahead of her ball, leaning
# back down her sides `lean` (degrees, the first; the last half that).
SABATON = dict(RANGER, toe=0.013, toe_point=0.0, sink=0.002, t_fore=0.0055, heel=-0.002, t_heel=0.0055, spring=0.004,
               plate=0.0015, lift=0.0013, tuck=0.0011, flare=0.0011, over=0.009, lames=4, tuck_up=0.012, lining=0.001,
               first=0.032, last=0.010, lean=18.0, sole_out=0.001, gold=(0.0045, 0.0005, 0.0012), rivet=0.0024)


def _fair(c, closed, step=0.0015, sigma=0.003):
    """A line resampled evenly and eased (an open one keeps its ends)."""
    if closed:
        return G["smooth_closed"](c, sigma, step)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    n = max(int(d[-1] / step), 4)
    t = np.linspace(0, d[-1], n + 1)
    r = np.stack([np.interp(t, d, c[:, k]) for k in range(3)], 1)
    return gaussian_filter1d(r, max(sigma / (d[-1] / n), 0.5), axis=0, mode="nearest")


def _runs(pos, tris, mark, least=0.02):
    """The stretches of a sheet's edge where `mark` holds, each in order
    along the edge (and whether it is the whole loop)."""
    out = []
    for loop in G["edge_loops"](tris):
        loop = np.asarray(loop)
        m = mark[loop]
        if m.all():
            out.append((pos[loop], True))
            continue
        if not m.any():
            continue
        s = int(np.argmin(m))
        loop, m = np.roll(loop, -s), np.roll(m, -s)
        i = 0
        while i < len(loop):
            if not m[i]:
                i += 1
                continue
            j = i
            while j < len(loop) and m[j]:
                j += 1
            seg = pos[loop[max(i - 1, 0):min(j + 1, len(loop))]]
            if np.linalg.norm(np.diff(seg, axis=0), axis=1).sum() >= least:
                out.append((seg, False))
            i = j
    return out


def _bead(name, c, closed, pp, tt, w, key, gold, thick):
    """A gold rolled edge along a line of a plate (its sheet pp, tt)."""
    g = G
    c = _fair(c, closed)
    tree = cKDTree(pp)
    _, j = tree.query(c)
    nr = g["vertex_normals"](pp, tt)[j]
    nr = gaussian_filter1d(nr, 3, axis=0, mode="wrap" if closed else "nearest")
    tg = (np.roll(c, -1, 0) - np.roll(c, 1, 0)) if closed else np.gradient(c, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
    nr = nr - tg * (nr * tg).sum(1)[:, None]
    nr /= np.linalg.norm(nr, axis=1)[:, None] + 1e-12
    ow = np.cross(tg, nr)
    ow /= np.linalg.norm(ow, axis=1)[:, None] + 1e-12
    near = pp[tree.query(c, k=12)[1]].mean(1)
    if ((near - c) * ow).sum(1).mean() > 0:
        ow = -ow
    width, height, over = gold
    return g["tube"](name, c, nr, ow, key, width, height, over, thick, pp, w, closed=closed, nv=10)


def sabaton(name, sd, top_s, dip, st, mkey, trim="gold", studs="gold", lining="darkleather", sole_key="darkleather",
            under=None, bevel=0.0006):
    """The Warden's sabaton (SABATON above): its lining, plates, their gold
    edges and rivets, and its sole. `under`, the piece (its sheet in SHEET)
    whose foot its top tucks up under: nothing of it comes within a hair of
    that piece's inside there."""
    g = G
    leg = Leg(sd)
    za, yb = leg.ankle[2], leg.ball_yf
    zt, tc = top_heights(leg, top_s, dip)
    sole = Sole(leg, st)

    def fit(zs, H, Hs):
        t = 1 - ramp(zt[None, :] - zs[:, None], 0.015, 0.06)
        return Hs * (1 - t) + np.minimum(Hs, H + st["c_top"]) * t
    zr, R, Hr, Ir = rings(leg, st, zt.max() + 0.015, top_s - 0.06, fit=fit)
    pos, tris = grid(zr, R)
    lo = sole.w(pos) - 0.0025          # (every plate runs 2.5 mm down into the sole)
    pos, _, tris = g["clip"](np.minimum(at_angle(zt, tc, pos) - pos[:, 2], pos[:, 2] - lo), pos, np.zeros((len(pos), 1)), tris)
    pos, _, tris = g["weld"](pos, np.zeros((len(pos), 1)), tris)
    nrm = g["vertex_normals"](pos, tris)
    z, yf = pos[:, 2], leg.yf(pos)
    xo = (pos[:, :2] - leg.ankle[:2]) @ leg.out
    t_, p0, a_, b_, ov = st["plate"], st["lift"], st["tuck"], st["flare"], st["over"]

    # Where the greave's foot is: each point's way up under it (s, metres
    # past its edge, negative below it), and how far out its inside is.
    s = np.full(len(pos), -1.0)
    room = np.full(len(pos), np.inf)
    y_g = 0.02
    if under is not None and under in g["SHEET"]:
        gp, gt = g["SHEET"][under][0], g["SHEET"][under][1]
        loops = g["edge_loops"](gt)
        foot = gp[np.asarray(min(loops, key=lambda L: gp[np.asarray(L), 2].mean()))]
        bvh = g["BVHTree"].FromPolygons([tuple(p) for p in gp], gt.tolist())
        V = g["Vector"]
        for i in range(len(pos)):
            hit = bvh.ray_cast(V(pos[i]), V(nrm[i]), 0.03)
            if hit[0] is not None:
                room[i] = hit[3]
            else:
                q = bvh.find_nearest(V(pos[i]), 0.008)
                if q[0] is not None and (np.array(q[0][:]) - pos[i]) @ nrm[i] > 0:
                    room[i] = (np.array(q[0][:]) - pos[i]) @ nrm[i]
        d_e = cKDTree(foot).query(pos)[0]
        covered = np.isfinite(room) & (room < 0.03)
        s = np.where(covered, d_e, -d_e)
        top = foot[np.abs((foot[:, :2] - leg.ankle[:2]) @ leg.out) < 0.01]
        y_g = float(leg.yf(top).max()) if len(top) else 0.02
    # Room under it: the plates (and the bead on their top edge) and the
    # lining kept 1.2 mm inside its inside; where they would not be, the
    # shell is drawn in (eased over the sheet; her skin there is not drawn).
    need = np.where(s < st["tuck_up"] + 0.003, p0 + t_ + 0.0005, st["lining"])
    shift = np.minimum(0.0, room - 0.0012 - need)
    A = g["adjacency"](len(pos), tris)
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    sh = shift.copy()
    for _ in range(12):
        sh = np.minimum(shift, (A @ sh) / deg)
    shift = sh
    pos = pos + nrm * shift[:, None]

    # The plates' front edges: planes across her foot, leaning back down her
    # sides, through her instep's top.
    n = st["lames"]
    e = np.linspace(y_g + st["first"], yb + st["last"], n + 1)
    mid = np.abs(xo) < 0.012
    planes = []
    for k, ek in enumerate(e):
        m = mid & (np.abs(yf - ek) < 0.003)
        ztop = float(z[m].max()) if m.any() else float(np.interp(ek, [y_g, yb], [za - 0.02, 0.045]))
        ph = np.radians(st["lean"] * (1 - 0.5 * k / max(n, 1)))
        planes.append((ek, ztop, ph))

    def d(k, p):
        ek, ztop, ph = planes[k]
        return (leg.yf(p) - ek) * np.cos(ph) - (p[:, 2] - ztop) * np.sin(ph)
    D = [d(k, pos) for k in range(n + 1)]

    foot_i, ball_i = g["BONES"].index(f"foot_{sd}"), g["BONES"].index(f"ball_{sd}")

    def blend(wb):
        w = np.zeros((1, len(g["BONES"])))
        w[0, foot_i], w[0, ball_i] = 1 - wb, wb
        return w

    made = []
    hiders = []
    # The lining: from `over` under the plates' top up to the top edge, her
    # skin's weights above her ankle as the boot's shaft, rigid below.
    keep = s - (st["tuck_up"] - 0.012)
    lp, la, lt = g["clip"](keep, pos, np.c_[nrm], tris)
    if len(lt):
        lp, la, lt = g["weld"](lp, la, lt)
        kr = 1 - ramp(lp[:, 2], za - 0.035, za - 0.005)
        lw = skin_weights(sd, lp) * (1 - kr)[:, None] + rigid(leg, lp) * kr[:, None]
        lw = g["four_bones"](g["eased_weights"](lp, lt, lw, over=0.012))
        o = g["finish"](name + "_lining", lp, lw, lt, lining, st["lining"], 0.0003, 10 ** 7)
        made.append(o)
        hiders.append(o)

    # The plates: 0 the instep plate (round her heel), 1..n the lames, n+1
    # the toe cap.
    sheets = []
    for k in range(n + 2):
        keep = np.full(len(pos), 1.0)
        off = np.full(len(pos), p0)
        if k == 0:
            keep = np.minimum(keep, st["tuck_up"] - s)
        if k >= 1:
            keep = np.minimum(keep, D[k - 1] + ov)
            off -= a_ * (1 - ramp(D[k - 1], 0.0, 0.004))
        if k <= n:
            keep = np.minimum(keep, -D[k])
            off += b_ * ramp(D[k], -ov - 0.004, -ov)
        pp, aa, tt = g["clip"](keep, pos, np.c_[nrm, off, D[min(k, n)], s], tris)
        if not len(tt):
            continue
        pp, aa, tt = g["weld"](pp, aa, tt)
        nn = aa[:, :3] / (np.linalg.norm(aa[:, :3], axis=1)[:, None] + 1e-12)
        pp = pp + nn * aa[:, 3:4]
        # (its blend: from her foot to her toes across the ball, by where it shows)
        yc = (y_g if k == 0 else e[k - 1]) * 0.5 + (e[k] if k <= n else leg.toe_yf) * 0.5
        wb = float(ramp(yc, yb - 0.015, yb + 0.015))
        w = np.repeat(blend(wb), len(pp), 0)
        nm = f"{name}_plate{k}" if k <= n else f"{name}_toe"
        if k == 0:
            nm = f"{name}_instep"
        o = g["finish"](nm, pp, w, tt, mkey, t_, bevel, 10 ** 7)
        made.append(o)
        hiders.append(o)
        sheets.append((k, nm, pp, tt, w, aa))
        print("SABATON %s: plate %d, %d points, blend to her toes %.2f" % (nm, k, len(pp), wb))

    # Gold along each edge that shows: the front of each plate but the toe
    # cap, and the instep plate's top, under the greave; never along the sole.
    for k, nm, pp, tt, w, aa in sheets:
        zb_ = sole.w(pp) + 0.0008
        mark = pp[:, 2] > zb_
        if k <= n:
            front = aa[:, 4] > -0.0012
        else:
            front = np.zeros(len(pp), bool)
        top = (aa[:, 5] > st["tuck_up"] - 0.0015) if k == 0 else np.zeros(len(pp), bool)
        for j, (c, closed) in enumerate(_runs(pp, tt, mark & (front | top))):
            made.append(_bead(f"{nm}_gold{j}" if j else f"{nm}_gold", c, closed, pp, tt, w, trim, st["gold"], t_))
        # A rivet each side, halfway along what shows, 11 mm up from the sole.
        if k <= n:
            dm = aa[:, 4] + (0.5 * (e[k] - (e[k - 1] if k else y_g)) if k else 0.012)
            zr_ = sole.w(pp) + 0.011
            cand = np.where((np.abs(dm) < 0.004) & (np.abs(pp[:, 2] - zr_) < 0.003))[0]
            if len(cand):
                xs = (pp[cand, :2] - leg.ankle[:2]) @ leg.out
                pick = [cand[np.argmax(xs)], cand[np.argmin(xs)]]
                vn = g["vertex_normals"](pp, tt)
                made += g["rivets"](nm, pp, None, tt, t_, studs, r=st["rivet"],
                                    spots=(pp[pick], vn[pick], w[pick]))

    # The sole: thin and flat under her, its edge proud of the plates.
    k0 = int(np.argmin(np.abs(zr - 0.012)))
    reach = p0 + b_ + t_ + st["sole_out"]
    O = ring(outline(Hr[k0] + reach, Ir[k0]), -leg.f, 220)
    on, _ = rim(O)
    c = O.mean(0)
    bev = 0.0008
    loops = [np.c_[q, sole.b(q)] for q in (c + (O - on * bev - c) * s_ for s_ in np.linspace(0.1, 0.92, 9))]
    loops += [np.c_[O - on * bev, sole.b(O)], np.c_[O, sole.b(O) + bev], np.c_[O, sole.w(O) - bev * 0.6],
              np.c_[O - on * bev * 0.6, sole.w(O)]]
    loops += [np.c_[q, sole.w(q)] for q in (c + (O - on * bev - c) * s_ for s_ in np.linspace(0.92, 0.1, 5))]
    spos, stris = loft(loops, np.r_[c, sole.b(c[None])[0]], np.r_[c, sole.w(c[None])[0]])
    o = g["finish"](name + "_sole", spos, rigid(leg, spos), stris, sole_key, 0.0, 0.0, 10 ** 7)
    made.append(o)
    hiders.append(o)
    for o in made:
        o["hides"] = o in hiders
        if o["hides"]:
            o["deep_zt"] = [float(v) for v in zt]
            o["deep_c"] = [float(v) for v in tc]
            o["deep_side"] = sd
    print("SABATON %s: greave's foot %.1f cm ahead of her ankle on top; front edges at %s cm; lean %s deg; "
          "shell drawn in under the greave at %d points, up to %.1f mm; sole edge %.1f mm out, top %.1f mm up"
          % (name, 100 * y_g, ", ".join("%.1f" % (100 * v) for v in e),
             ", ".join("%.0f" % np.degrees(p[2]) for p in planes), int((shift < -1e-5).sum()), -1000 * shift.min(),
             1000 * reach, 1000 * float(sole.zw.mean())))
    return made


# ------------------------------------------------------------ still to come --
#  - creases as outward ridges (ankle stacking, toe break), back seam tube +
#    stitches, toe cap and heel counter overlays; the top edge bound;
#    reaver garters (helical straps, hide bulging between).
#  - grime from the floor up in the vertex colour's alpha (1 everywhere today)
#    and wear/polish/flat from outfit_materials.json into the shader; scuffs.
#  - the Arcanist's and Reaver's boots on boot() (their own specs: a heel,
#    a pointed toe, a softer sole).
