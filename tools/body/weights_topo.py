"""Weights v1 on OUR topology (P1 B2b): primary weights read off our topology's own structure (seeds by rule where one
bone owns the skin, a bounded biharmonic fill across each joint's band: F, G below), then weights.py's rules 2, 4 and
5-10 (4b is not run: BANDS). v0 (B2a) blended by smoothsteps over the joint parts' loops.

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
            forearm by the hinge fill F, forearm -> hand over +-1.5 cm about the wrist; the trunk into the arm by the
            girdle fill G.
 H hand     (where the wrist blend gives the hand any) per finger, the polyline hand -> metacarpal -> 01 -> 02 -> 03
            (thumb: hand -> 01 -> 02 -> 03); a point's fingers by a soft minimum of its distance to each finger's
            polyline (exp(-(d - dmin) / 2 mm), shares under 1% dropped: webbing blends, fingers stay their own);
            along a finger, smooth hats at each joint over +-min(8 mm, 0.3 x the shorter neighbouring bone); then
            HAND_SMOOTH Jacobi steps of the umbrella operator over the hand part (the soft minimum's switches, e.g.
            the thumb's root against the index metacarpal, made a blend a few edges wide).
 L leg      (thigh, knee, shin, foot; the crotch strip is the trunk's) the station along thigh -> calf: trunk -> thigh by
            the girdle fill G, thigh -> calf by the hinge fill F;
            calf -> foot by height over the ankle (all foot 2 cm under the ankle joint, all calf 3 cm over it, along
            the calf); foot -> ball along the foot bone (t 0.85 -> 1.15).
 F hinge    (elbow, knee: hinge_fill) seeds by the rest bisector plane, the band's width by the angle a round the joint
            from the crease, w_c at the crease (the crease skins' crossing distance at the design flexion), w_o on the
            outer side (the joint part's designed loops), (1 +- ASYM) up / down; the fill between.
 G girdle   (shoulder, hip: girdle_fill) the limb's share 0 on the trunk's seeds, 1 on the limb's, the fill on the band
            GIRDLE names (the deltoid loops and the cap; the glute lobe, the crease's rows up the belly).
 fill       min sum M (L x)^2 (L the edge Laplacian weighted 1 / length^2, M the points' areas) with the seeds fixed:
            C1 into the seeds round the band (no kink where a band ends), even in arc length, clipped to [0, 1].
Then weights.py: 4 chains (twists), 5 shares, 6 points, 7 muscles, 8 breast tip,
9 islands (on our quads), 10 cap; and 2 mirror exactly, by OUR topology's mirror_of (each right point the left's,
sides swapped; the midline the mean of itself and its swap).
Head (the approved undo (ii)): its open ring's points take the body ring's final weights exactly (a seam with no
step); points over 3.5 cm from the ring are Head; between, harmonic on the head's own mesh (the face is rigid on
Head: A's face has no bones of its own, its blend shapes are inherited unchanged).
Derivation: (a) the game's need (bones move skin by our loops, nothing keyed to MakeHuman ids; linear blend skinning
with no correctives passing the check's bends); (b) MakeHuman's CC0 crease and cap profiles, MEASURED on corr_a (no
weight or vertex id read), for ASYM and the girdle bands; each number named at its constant (the sweep that set it).
"""
import numpy as np
import scipy.sparse as sp

import weights as wt
from stages import harmonic, laplacian

VERSION = "v1"  # written into each built glb's extras (build_topo.py stage_export); bump with the rules

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


def U(v):
    v = np.asarray(v, float)
    return v / max(float(np.linalg.norm(v)), 1e-12)


def biharmonic_ops(P, Q):
    """K = L^T M L on our quads: L the edge Laplacian weighted 1 / length^2 (on a rectangular grid the finite-difference
    Laplacian, so a fill runs even in arc length, not in ring count: our bend zones' loops are denser), M each point's
    area (a quarter of each of its quads'). The energy sum M (L x)^2 is the discrete integral of the squared Laplacian."""
    n = len(P)
    e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
    e = np.unique(np.sort(e, 1), axis=0)
    w = 1.0 / np.maximum(((P[e[:, 0]] - P[e[:, 1]]) ** 2).sum(1), 1e-10)
    A = sp.coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    L = (sp.diags(np.asarray(A.sum(1)).ravel()) - A).tocsr()
    qa = 0.5 * np.linalg.norm(np.cross(P[Q[:, 2]] - P[Q[:, 0]], P[Q[:, 3]] - P[Q[:, 1]]), axis=1)
    M = np.zeros(n)
    for k in range(4):
        np.add.at(M, Q[:, k], 0.25 * qa)
    return (L.T @ sp.diags(M) @ L).tocsr()


def fill(K, x, free):
    """x [n, k] with the known values set; the `free` points' values replaced by the bounded fill: the biharmonic
    (min sum M (L x)^2, C1 into the known values round them), clipped to [0, 1]."""
    import scipy.sparse.linalg as spl
    x = np.array(x, float)
    if not len(free):
        return x
    isf = np.zeros(len(x), bool)
    isf[free] = True
    Kff = K[free][:, free].tocsc()
    rhs = -(K[free][:, ~isf] @ x[~isf])
    solve = spl.factorized(Kff)
    x[free] = np.stack([solve(np.ascontiguousarray(rhs[:, k])) for k in range(x.shape[1])], 1)
    return np.clip(x, 0, 1)


class Ctx:
    def __init__(self, P, topo, sk):
        self.P = np.asarray(P, float)
        self.part, self.ring, self.side = topo["part"], topo["ring"], topo["side"]
        self.parts = [str(p) for p in topo["parts"]]
        self.Q = topo["Q"]
        self.names = sk["names"]
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.ends = sk["ends"]
        self.worlds = sk["worlds"]
        self.n = len(P)
        self._K = None
        self.rep = {}

    @property
    def K(self):
        if self._K is None:
            self._K = biharmonic_ops(self.P, self.Q)
        return self._K

    def world(self, b):
        return np.asarray(self.worlds[self.idx[b]], float)

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


# hinge joints: upper bone, lower bone, the joint's part, the crease's sign on the lower bone's Z (weights.py's bands)
HINGES = {"elbow": ("upperarm", "lowerarm", "elbow", 1.0), "knee": ("thigh", "calf", "knee", 1.0)}
# (a) the check's deepest test (135): F_d 130 is the design flexion; the sweep (F_d 80-145, the asymmetry 0-0.95, the
# outer width 1-2x) on base_woman: the elbow is fold-free at 135 from here, 115 leaves 231 points inside at 135
F_DESIGN = {"elbow": 130.0, "knee": 130.0}
# (b) MakeHuman's CC0 crease profile, measured on corr_a (0.5 at the plane, 0.9 by 10 mm distal, the ramp 40+ mm into
# the upper arm) and (a) the same sweep: the crease band reaches (1 + ASYM) w_c up the proximal bone and
# (1 - ASYM) w_c down the distal: the distal limb's skin stays its own to the plane (0.6: 277 points at 135, 0.9: 28)
ASYM = {"elbow": 0.9, "knee": 0.9}
WO_SCALE = {"elbow": 1.0, "knee": 1.0}  # 2x (the part's whole span) doubled the outer outline's error (1.8 -> 4.4 mm)
CREASE_SAMPLE = (0.006, 15.0)        # the crease radius: our points within 6 mm of the bisector plane, 15 deg of the crease


def hinge_fill(c, s, joint, dom):
    """The lower bone's share r of a hinge joint's two bones on the points `dom` (bool), by the fill: seeds by rule,
    biharmonic between. The rest bisector plane through the joint (normal nb toward the upper bone, sd a point's
    signed distance); round the joint the angle a from the crease direction (the lower bone's Z times the sign, in
    the plane). The upper bone owns sd > h(a), the lower sd < -h(a), the band between is filled:
      h(a) = w_c + (w_o - w_c) (1 - cos a) / 2
      w_c (the crease) = r_c tan((F_d - F_rest) / 2): under linear blend skinning the crease skins of two rigid
            segments first cross r_c tan(phi / 2) from the plane (phi the turn from rest, r_c the crease skin's
            distance from the joint): a band this wide keeps them apart up to the design flexion F_d;
      w_o (the outer side, the share and point bones' room) = half the joint part's span along nb: its designed loops.
    """
    up, lo, part, sign = HINGES[joint]
    P = c.P
    O = c.head(f"{lo}_{s}")
    u = U(c.head(f"{up}_{s}") - O)
    d = U(c.tail(f"{lo}_{s}") - O)
    nb = U(u - d)
    cz = sign * c.world(f"{lo}_{s}")[:3, 2]
    cz = U(cz - nb * (cz @ nb))
    rel = P - O
    sd = rel @ nb
    rad = rel - sd[:, None] * nb
    R = np.linalg.norm(rad, axis=1)
    ca = (rad @ cz) / np.maximum(R, 1e-9)
    ang = np.degrees(np.arccos(np.clip(ca, -1, 1)))
    jp = dom & (c.part == c.pid(part)[0])
    f_rest = float(np.degrees(np.arccos(np.clip(-u @ d, -1, 1))))
    near = jp & (np.abs(sd) < CREASE_SAMPLE[0]) & (ang < CREASE_SAMPLE[1])
    r_c = float(np.median(R[near]))
    w_c = r_c * np.tan(np.radians(max(F_DESIGN[joint] - f_rest, 0.0)) / 2)
    w_o = WO_SCALE[joint] * 0.5 * float(sd[jp].max() - sd[jp].min())
    h = w_c + (w_o - w_c) * (1 - ca) / 2
    a_ = ASYM[joint] * (1 + ca) / 2
    h_up, h_lo = h * (1 + a_), h * (1 - a_)
    x = (sd < 0).astype(float)[:, None]
    free = np.where(dom & (sd <= h_up) & (sd >= -h_lo))[0]
    x = fill(c.K, x, free)[:, 0]
    c.rep[f"{joint}_{s}"] = {"rest_flexion_deg": round(f_rest, 1), "crease_r_mm": round(r_c * 1e3, 1),
                             "w_crease_mm": round(float(w_c) * 1e3, 1), "w_outer_mm": round(w_o * 1e3, 1),
                             "band_points": int(len(free))}
    return x


# girdles (the fill's free band; the trunk's seeds hold the trunk's own weights T, the limb's the limb chain's):
# shoulder: the shoulder part (its concentric deltoid loops), the arm's rings within limb_m of the arm root, the trunk
#   within trunk_m of the shoulder joint (corr_a's cap is the share's up to 96 mm from the joint: the arm's turn shared
#   over the trapezius and the back of the shoulder); the sweep (trunk_m 0-0.15, limb_m 0.03-0.08): 0.15 / 0.05 the
#   only pair with abduction and flexion 135 both <= 3 points, no depth (0.13 / 0.03: 11; 0.09: 6 at 40 mm)
# hip: the glute lobe (the trunk's rows under row 0, the hip curve root), the trunk's rows 0..trunk_rows behind the
#   thigh's coronal plane and 0..front_rows in front of it (the crease's band reaches up the belly: ASYM's rule), the
#   thigh's rings within limb_m of its root (0.09: hip 90 7 points but the thigh's girth 1.34; 0.07: 1.077); trunk_rows
#   10 (4: girth 1.081 on her right, 2: 1.12, 16: 1.080)
GIRDLE = {"shoulder": {"limb_m": 0.05, "trunk_m": 0.15}, "hip": {"limb_m": 0.07, "trunk_rows": 10, "front_rows": 24}}
# 4b's narrow crease band (weights.py RULES "bands") is NOT run here: on our loops under linear blend skinning it puts
# the crease back inside (elbow 90: 0 -> 133 points, 10 mm; knee 90: 0 -> 185, 21 mm); it is the corrective stage's
BANDS = False

def girdle_fill(c, s, joint, own, limb, free):
    """The limb's share g of a girdle: 1 on the limb's points (`limb`) outside `free`, 0 on every other point
    (the trunk's, the other side's), the bounded biharmonic fill on `free`."""
    x = (limb & ~free).astype(float)[:, None]
    fr = np.where(free & own)[0]
    g = fill(c.K, x, fr)[:, 0]
    c.rep[f"{joint}_{s}"] = {"band_points": int(len(fr)), **GIRDLE[joint]}
    return g


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
        ce = hinge_fill(c, s, "elbow", own & np.isin(c.part, c.pid("arm", "elbow", "forearm")))[m]
        ce = np.where(np.isin(c.part[m], c.pid("hand")), 1.0, np.where(c.part[m] == sh, 0.0, ce))
        cw = s01((st - (L1 + L2 - 0.015)) / 0.03)
        A = np.zeros((m.sum(), len(c.names)))
        A[:, c.idx[f"upperarm_{s}"]] = 1 - ce
        A[:, c.idx[f"lowerarm_{s}"]] = ce * (1 - cw)
        hm_ = cw > 0
        A[hm_] += cw[hm_, None] * hand_chain(c, s, P[m][hm_])
        ia = (c.part[m] == c.pid("arm")[0]) & (c.ring[m] >= 0)
        free = np.zeros(c.n, bool)
        free[np.where(m)[0]] = (c.part[m] == sh) | (ia & (st - st[ia].min() < GIRDLE["shoulder"]["limb_m"]))
        Gs = GIRDLE["shoulder"]
        free |= own & (c.part == c.pid("trunk")[0]) & (np.linalg.norm(P - c.head(f"upperarm_{s}"), axis=1) < Gs["trunk_m"])
        g = girdle_fill(c, s, "shoulder", own, m, free)
        Af = np.zeros((c.n, len(c.names)))
        Af[:, c.idx[f"upperarm_{s}"]] = 1.0
        Af[m] = A
        ids = np.where(m | (g > 0))[0]
        W[ids] = (1 - g[ids])[:, None] * W[ids] + g[ids, None] * Af[ids]
        rep[f"elbow_blend_{s}_m"] = [round(float(lo), 4), round(float(hi), 4), round(float(L1), 4)]
        # the leg
        m = own & np.isin(c.part, leg_parts)
        pts = [c.head(f"thigh_{s}"), c.head(f"calf_{s}"), c.head(f"foot_{s}")]
        st = ring_station(P[m], c.part[m], c.ring[m], c.side[m], pts, c.pid("thigh", "knee", "shin"))
        ik = (c.part[m] == kn) & (c.ring[m] >= 0)
        lo, hi = st[ik].min(), st[ik].max()
        ck = hinge_fill(c, s, "knee", own & np.isin(c.part, c.pid("thigh", "knee", "shin")))[m]
        ck = np.where(c.part[m] == c.pid("foot")[0], 1.0, ck)
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
        tr = c.pid("trunk")[0]
        Gh = GIRDLE["hip"]
        front = (P - c.head(f"thigh_{s}")) @ (-c.world(f"thigh_{s}")[:3, 2]) > 0      # the crease side (thigh -Z)
        free = own & (c.part == tr) & (c.ring <= np.where(front, Gh["front_rows"], Gh["trunk_rows"]))
        free[np.where(m)[0]] = (c.part[m] == th) & (st - s0 < GIRDLE["hip"]["limb_m"])
        g = girdle_fill(c, s, "hip", own, m, free)
        Af = np.zeros((c.n, len(c.names)))
        Af[:, c.idx[f"thigh_{s}"]] = 1.0
        Af[m] = Lg
        ids = np.where(m | (g > 0))[0]
        W[ids] = (1 - g[ids])[:, None] * W[ids] + g[ids, None] * Af[ids]
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
        if BANDS:
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
    rep.update(c.rep)
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
