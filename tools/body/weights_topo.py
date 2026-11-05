"""Weights v0 on OUR topology (P1 B2a): weights.py's rule 1 (MakeHuman's map) and rule 3 (through the subdivision)
replaced by primary weights read off our topology's own structure; weights.py's rules 2 and 4-10 then run unchanged.
A later solver designs v1; this is the simplest honest rule that passes the check's weight numbers.

    body(P, topo, sk) -> (J [n,8], W [n,8], rep)      P: our vertices (glTF), topo: out/topo/<tier>.npz's arrays,
                                                      sk: build_topo's skeleton (names, parents, worlds, ends)
    head(PH, TH, ring_ids, ring_W, names, sk) -> W     the head mesh's weights (welded points, dense)

Primary weights (each a partition of one; smooth01 = smoothstep):
 T trunk    (every part; the limbs blend from it) the spine chain pelvis, spine_01..05, neck_01, neck_02, Head by
            HEIGHT: at each chain joint the bone above takes over by smoothstep across +-h about the joint's height,
            h = min(half the height to either neighbouring joint, 4 cm) (so the steps never overlap: a partition
            of one; the lowest joint, spine_01's head = the pelvis's, has 8 cm below it);
            clavicle: of that, k = smooth01((t - 0.25) / 0.5) * (1 - smooth01((|dy| - 5 cm) / 6 cm)) on its own side,
            t the point's parameter along the clavicle (head 0, tail 1), dy its height off the clavicle's line;
            breast (the breast part only): b = smooth01(d / 5 cm), d its distance from the breast hole's rim.
 A arm      (shoulder, arm, elbow, forearm, hand) the station s along upper arm -> forearm (arc length; a ring's
            station is its centroid's, so a loop moves as one; the few off-ring kite points their own): upper arm ->
            forearm by smoothstep across the elbow part's designed loops (its first ring's station to its last's),
            forearm -> hand over +-1.5 cm about the wrist. Shoulder: the part's concentric loops blend the trunk into
            the arm, h = smooth01(ring / (rings + 1)) (the rim the trunk's, the arm root ring nearly all the arm's).
 H hand     (where the wrist blend gives the hand any) per finger, the polyline hand -> metacarpal -> 01 -> 02 -> 03
            (thumb: hand -> 01 -> 02 -> 03); a point's fingers by a soft minimum of its distance to each finger's
            polyline (exp(-(d - dmin) / 2 mm), shares under 1% dropped: webbing blends, fingers stay their own);
            along a finger, smooth hats at each joint over +-min(8 mm, 0.3 x the shorter neighbouring bone); then
            HAND_SMOOTH Jacobi steps of the umbrella operator over the hand part (the soft minimum's switches, e.g.
            the thumb's root against the index metacarpal, made a blend a few edges wide).
 L leg      (thigh, knee, shin, foot; the crotch strip is the trunk's) the station along thigh -> calf: the hip blends
            trunk -> thigh over the first 7 cm of the thigh's rings, thigh -> calf across the knee part's designed loops;
            calf -> foot by height over the ankle (all foot 2 cm under the ankle joint, all calf 3 cm over it, along
            the calf); foot -> ball along the foot bone (t 0.85 -> 1.15).
Then weights.py: 4 chains (twists), 4b bands (the elbow's crease), 5 shares, 6 points, 7 muscles, 8 breast tip,
9 islands (on our quads), 10 cap; and 2 mirror exactly, by OUR topology's mirror_of (each right point the left's,
sides swapped; the midline the mean of itself and its swap).
Head (the approved undo (ii)): its open ring's points take the body ring's final weights exactly (a seam with no
step); points over 3.5 cm from the ring are Head; between, harmonic on the head's own mesh (the face is rigid on
Head: A's face has no bones of its own, its blend shapes are inherited unchanged).
Derivation: (a) the game's need (bones move skin by our loops, nothing keyed to MakeHuman ids); (b) no reference
weights; the numbers here are v0 choices, each named above.
"""
import numpy as np
import scipy.sparse as sp

import weights as wt
from stages import harmonic, laplacian

SPINE = ["pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "neck_01", "neck_02", "Head"]
FINGERS = ["index", "middle", "ring", "pinky"]
HMAX = 0.04
HAND_SMOOTH = 12


def s01(x):
    return wt.smooth01(x)


def poly_station(X, pts):
    """Arc length along the polyline pts of each point's closest point (before the first segment and past the last
    extrapolated along them), and the distance to it."""
    pts = np.asarray(pts, float)
    best_d = np.full(len(X), np.inf)
    best_s = np.zeros(len(X))
    acc = 0.0
    nseg = len(pts) - 1
    for i in range(nseg):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        L = float(np.linalg.norm(ab))
        t = ((X - a) @ ab) / max(L * L, 1e-12)
        tc = np.clip(t, 0 if i > 0 else -np.inf, 1 if i < nseg - 1 else np.inf)
        tq = np.clip(t, 0, 1)
        d = np.linalg.norm(X - (a + tq[:, None] * ab), axis=1)
        m = d < best_d
        best_d[m], best_s[m] = d[m], acc + tc[m] * L
        acc += L
    return best_s, best_d


def hats(u, knots, h):
    """Partition of one over len(knots)+1 pieces: piece i from knot i-1 to knot i, smoothstep +-h[i] at knot i."""
    c = [np.ones(len(u))] + [s01((u - (k - hh)) / (2 * hh)) for k, hh in zip(knots, h)] + [np.zeros(len(u))]
    return np.stack([c[i] * (1 - c[i + 1]) for i in range(len(knots) + 1)], 1)


def ring_station(X, part, ring, side, pts, parts_sel):
    """Station per point: its ring's centroid's (ring >= 0 in the selected parts), else its own."""
    s, _ = poly_station(X, pts)
    sel = np.isin(part, parts_sel) & (ring >= 0)
    key = np.stack([part[sel], ring[sel], side[sel]], 1)
    u, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    C = np.zeros((len(u), 3))
    np.add.at(C, inv, X[sel])
    C /= np.bincount(inv)[:, None]
    sc, _ = poly_station(C, pts)
    s[sel] = sc[inv]
    return s


class Ctx:
    def __init__(self, P, topo, sk):
        self.P = np.asarray(P, float)
        self.part, self.ring, self.side = topo["part"], topo["ring"], topo["side"]
        self.parts = [str(p) for p in topo["parts"]]
        self.Q = topo["Q"]
        self.names = sk["names"]
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.ends = sk["ends"]
        self.n = len(P)

    def pid(self, *names):
        return [self.parts.index(x) for x in names]

    def head(self, b):
        return np.asarray(self.ends[b][0], float)

    def tail(self, b):
        return np.asarray(self.ends[b][1], float)


def trunk(c):
    P, n = c.P, c.n
    W = np.zeros((n, len(c.names)))
    y = P[:, 1]
    ys = [c.head(b)[1] for b in SPINE]
    lens = [np.linalg.norm(c.tail(b) - c.head(b)) for b in SPINE]
    knots = ys[1:]                       # (spine_01's head is the pelvis's: the pelvis owns all below it)
    h = []
    for k in range(len(knots)):
        below = knots[k] - knots[k - 1] if k > 0 else 2 * HMAX
        above = knots[k + 1] - knots[k] if k + 1 < len(knots) else lens[-1]
        h.append(min(0.5 * below, 0.5 * above, HMAX))
    Hs = hats(y, knots, h)
    for i, b in enumerate(SPINE):
        W[:, c.idx[b]] = Hs[:, i]
    for s, sx in (("l", 1.0), ("r", -1.0)):
        a, b = c.head(f"clavicle_{s}"), c.tail(f"clavicle_{s}")
        t = wt.seg_t(P, a, b)
        line = a[None] + np.clip(t, 0, 1)[:, None] * (b - a)[None]
        dy = P[:, 1] - line[:, 1]
        own = (P[:, 0] * sx > 0).astype(float)
        k = s01((t - 0.25) / 0.5) * (1 - s01((np.abs(dy) - 0.05) / 0.06)) * own
        W *= (1 - k)[:, None]
        W[:, c.idx[f"clavicle_{s}"]] += k
    # breast: its part only, by distance from the hole's rim (trunk points on a quad with a breast point)
    br, tr = c.pid("breast", "trunk")
    inb = c.part == br
    qb = inb[c.Q].any(1)
    rim = np.unique(c.Q[qb].ravel())
    rim = rim[c.part[rim] == tr]
    from scipy.spatial import cKDTree
    d, _ = cKDTree(P[rim]).query(P[inb])
    b = s01(d / 0.05)
    ids = np.where(inb)[0]
    W[ids] *= (1 - b)[:, None]
    for s, sx in (("l", 1.0), ("r", -1.0)):
        m = P[ids, 0] * sx > 0
        W[ids[m], c.idx[f"breast_{s}"]] += b[m]
    return W


def hand_chain(c, s, X):
    """Weights [len(X), bones] of the hand's chains (H above)."""
    out = np.zeros((len(X), len(c.names)))
    chains = []
    for f in FINGERS:
        bones = [f"hand_{s}", f"{f}_metacarpal_{s}", f"{f}_01_{s}", f"{f}_02_{s}", f"{f}_03_{s}"]
        chains.append(bones)
    chains.append([f"hand_{s}", f"thumb_01_{s}", f"thumb_02_{s}", f"thumb_03_{s}"])
    D, U, KN = [], [], []
    for bones in chains:
        pts = [c.head(b) for b in bones] + [c.tail(bones[-1])]
        u, d = poly_station(X, pts)
        L = np.linalg.norm(np.diff(np.asarray(pts), axis=0), axis=1)
        kn = np.cumsum(L)[:-1]
        h = [min(0.008, 0.3 * min(L[i], L[i + 1])) for i in range(len(kn))]
        D.append(d), U.append(u), KN.append((kn, h))
    D = np.stack(D, 1)
    a = np.exp(-(D - D.min(1, keepdims=True)) / 0.002)
    a /= a.sum(1, keepdims=True)
    a = np.where(a < 0.01, 0.0, a)
    a /= a.sum(1, keepdims=True)
    for f, bones in enumerate(chains):
        Hs = hats(U[f], *KN[f])
        for i, b in enumerate(bones):
            out[:, c.idx[b]] += a[:, f] * Hs[:, i]
    return out


def limbs(c, W):
    P = c.P
    arm_parts = c.pid("shoulder", "arm", "elbow", "forearm", "hand")
    leg_parts = c.pid("thigh", "knee", "shin", "foot")
    sh, el, kn, th = c.pid("shoulder", "elbow", "knee", "thigh")
    rep = {}
    for s, sx in (("l", 1.0), ("r", -1.0)):
        own = P[:, 0] * sx > 0
        # the arm
        m = own & np.isin(c.part, arm_parts)
        pts = [c.head(f"upperarm_{s}"), c.head(f"lowerarm_{s}"), c.head(f"hand_{s}")]
        st = ring_station(P[m], c.part[m], c.ring[m], c.side[m], pts, c.pid("shoulder", "arm", "elbow", "forearm"))
        L1, L2 = np.linalg.norm(pts[1] - pts[0]), np.linalg.norm(pts[2] - pts[1])
        ie = (c.part[m] == el) & (c.ring[m] >= 0)
        lo, hi = st[ie].min(), st[ie].max()
        ce = s01((st - lo) / (hi - lo))
        cw = s01((st - (L1 + L2 - 0.015)) / 0.03)
        A = np.zeros((m.sum(), len(c.names)))
        A[:, c.idx[f"upperarm_{s}"]] = 1 - ce
        A[:, c.idx[f"lowerarm_{s}"]] = ce * (1 - cw)
        hm_ = cw > 0
        A[hm_] += cw[hm_, None] * hand_chain(c, s, P[m][hm_])
        rsh = c.ring[m]
        R = c.ring[c.part == sh].max()
        h = np.where(c.part[m] == sh, s01(rsh / (R + 1.0)), 1.0)
        ids = np.where(m)[0]
        W[ids] = (1 - h)[:, None] * W[ids] + h[:, None] * A
        rep[f"elbow_blend_{s}_m"] = [round(float(lo), 4), round(float(hi), 4), round(float(L1), 4)]
        # the leg
        m = own & np.isin(c.part, leg_parts)
        pts = [c.head(f"thigh_{s}"), c.head(f"calf_{s}"), c.head(f"foot_{s}")]
        st = ring_station(P[m], c.part[m], c.ring[m], c.side[m], pts, c.pid("thigh", "knee", "shin"))
        ik = (c.part[m] == kn) & (c.ring[m] >= 0)
        lo, hi = st[ik].min(), st[ik].max()
        ck = s01((st - lo) / (hi - lo))
        ank = c.head(f"foot_{s}")
        up = c.head(f"calf_{s}") - ank
        up /= np.linalg.norm(up)
        dz = (P[m] - ank) @ up
        ca = 1 - s01((dz + 0.02) / 0.05)
        tf = wt.seg_t(P[m], c.head(f"foot_{s}"), c.tail(f"foot_{s}"))
        cb = s01((tf - 0.85) / 0.3)
        Lg = np.zeros((m.sum(), len(c.names)))
        Lg[:, c.idx[f"thigh_{s}"]] = 1 - ck
        Lg[:, c.idx[f"calf_{s}"]] = ck * (1 - ca)
        Lg[:, c.idx[f"foot_{s}"]] = ck * ca * (1 - cb)
        Lg[:, c.idx[f"ball_{s}"]] = ck * ca * cb
        it = (c.part[m] == th) & (c.ring[m] >= 0)
        s0 = st[it].min()
        h = np.where(c.part[m] == th, s01((st - s0) / 0.07), 1.0)
        ids = np.where(m)[0]
        W[ids] = (1 - h)[:, None] * W[ids] + h[:, None] * Lg
        rep[f"knee_blend_{s}_m"] = [round(float(lo), 4), round(float(hi), 4)]
    return W, rep


def smooth_part(W, Q, sel, iters):
    """`iters` Jacobi steps of the umbrella operator (each point half itself, half its neighbours' mean) on the points
    in `sel`; the rest held (they are the boundary)."""
    e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
    n = len(W)
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A = ((A + A.T) > 0).astype(float)
    deg = np.asarray(A.sum(1)).ravel()
    ids = np.where(sel)[0]
    As = A[ids]
    for _ in range(iters):
        W[ids] = 0.5 * W[ids] + 0.5 * (As @ W) / deg[ids, None]
    return W


def mirror(W, topo, names):
    sw = np.array([names.index(wt.swap_side(n)) for n in names])
    mo = topo["mirror_of"]
    r = mo >= 0
    W = W.copy()
    W[r] = W[mo[r]][:, sw]
    mid = topo["side"] == 0
    W[mid] = 0.5 * (W[mid] + W[mid][:, sw])
    return W


def body(P, topo, sk):
    c = Ctx(P, topo, sk)
    names, par = sk["names"], sk["parents"]
    W = trunk(c)
    W, rep = limbs(c, W)
    W = smooth_part(W, c.Q, np.isin(c.part, c.pid("hand")), HAND_SMOOTH)
    frames = {n: sk["worlds"][i] for i, n in enumerate(names)}
    tails = {n: sk["ends"][n][1] for n in names}
    Pg = c.P
    for side in ("l", "r"):
        W = wt.chain_split(W, Pg, names, sk["ends"], side)
        W = wt.bands(W, Pg, names, frames, side)
        W = wt.shares(W, Pg, names, frames, side)
        W = wt.points(W, Pg, names, frames, side)
        W = wt.muscles(W, Pg, names, par, tails, side)
        W = wt.breast(W, Pg, names, sk["ends"], side)
    W = np.maximum(W, 0)
    W /= np.maximum(W.sum(1, keepdims=True), 1e-12)
    W = mirror(W, topo, names)
    fixed = np.zeros(len(W), bool)
    moved_all = {}
    J, Wk = wt.cap(W, wt.RULES["cap"])
    for _ in range(6):
        Wd = np.zeros_like(W)
        np.put_along_axis(Wd, J, Wk, 1)
        Wd, moved = wt.islands(Wd, topo["Q"], fixed, wt.RULES["island"])
        for j, cnt in moved.items():
            moved_all[names[j]] = moved_all.get(names[j], 0) + cnt
        Wd = mirror(Wd, topo, names)
        J, Wk = wt.cap(Wd, wt.RULES["cap"])
        if not moved:
            break
    Wd = np.zeros_like(W)
    np.put_along_axis(Wd, J, Wk, 1)
    Wd = mirror(Wd, topo, names)
    J, Wk = wt.cap(Wd, wt.RULES["cap"])
    rep.update({"max_influences": int((Wk > 0).sum(1).max()), "island_points_moved": moved_all,
                "rules": "tools/body/weights_topo.py (primary) + tools/body/weights.py RULES 2, 4-10"})
    return J, Wk, rep


def head(PH, TH, ring_ids, ring_W, names, reach=0.035):
    """Dense head weights on the head's welded points: the ring's fixed to ring_W, Head past `reach` m from the ring,
    harmonic between (clipped >= 0, normalised)."""
    from scipy.spatial import cKDTree
    n = len(PH)
    d, _ = cKDTree(PH[ring_ids]).query(PH)
    zone = d > reach
    zone[ring_ids] = False
    known = np.concatenate([ring_ids, np.where(zone)[0]])
    vals = np.zeros((len(known), len(names)))
    vals[:len(ring_ids)] = ring_W
    vals[len(ring_ids):, names.index("Head")] = 1.0
    isk = np.zeros(n, bool)
    isk[known] = True
    L = laplacian(TH, n)
    used = np.zeros(n, bool)
    used[np.unique(TH)] = True
    free = np.where(~isk & used)[0]
    cols = np.where(vals.any(0))[0]
    x = np.zeros((n, len(names)))
    x[:, cols] = harmonic(L, known, vals[:, cols], free)
    x[~used, names.index("Head")] = 1.0
    x = np.maximum(x, 0)
    x /= np.maximum(x.sum(1, keepdims=True), 1e-12)
    return x, {"ring_points": int(len(ring_ids)), "head_zone_points": int(zone.sum()), "blend_points": int(len(free)),
               "reach_m": reach}
