"""Weights v1 on OUR topology (P1 B2b): primary weights read off our topology's own structure (seeds by rule where one
bone owns the skin, a bounded biharmonic fill across each joint's band: F, G below), then weights.py's rules 2, 4 and
5-10 (4b is not run: BANDS). v0 (B2a) blended by smoothsteps over the joint parts' loops.

    body(P, topo, sk) -> (J [n,8], W [n,8], rep)      P: our vertices (glTF), topo: out/topo/<tier>.npz's arrays,
                                                      sk: build_topo's skeleton (names, parents, worlds, ends)
    head(PH, TH, ring_ids, ring_W, names, sk) -> W     the head mesh's weights (welded points, dense)

Primary weights (each a partition of one; smooth01 = smoothstep):
 T trunk    (every part; the limbs blend from it) the spine chain pelvis, spine_01..05, neck_01, neck_02, Head by
            HEIGHT: at each chain joint the bone above takes over by smoothstep across +-h about the joint's height,
            h = HMAX (4 cm) at every joint, each piece the difference of its two steps (a partition of one where steps
            overlap too: the steps keep their joints' order). (v6, P1 R1 rig root: B's trunk joints are A's, and A's
            spine_01 and spine_02 joints stand 47 mm apart, so v5's h = min(half the height to either neighbouring
            joint, 4 cm) narrowed the bends there to +-23.6 mm against B's own +-37-40; where no two steps overlap
            the pieces are v5's, value for value);
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
            the calf); foot -> ball along the foot bone (t 0.85 -> 1.15). A spec's "weights" "leg" (P1 R1 round 30, her
            body: B's ankle and foot ARE A's, her_a a_foot) sets the two ramps instead: "ankle_m" [lo, span] (all foot
            at lo, all calf at lo + span, along the calf from the ankle joint) and "ball_t" [t0, span].
 F hinge    (elbow, knee: hinge_fill) seeds by the rest bisector plane, the band's width by the angle a round the joint
            from the crease, w_c at the crease (the crease skins' crossing distance at the design flexion), w_o on the
            outer side (the joint part's designed loops), (1 +- ASYM) up / down; the fill between.
 G girdle   (shoulder, hip: girdle_fill) the limb's share 0 on the trunk's seeds, 1 on the limb's, the fill on the band
            GIRDLE names (the deltoid loops and the cap; the glute lobe, the crease's rows up the belly).
 fill       min sum M (L x)^2 (L the edge Laplacian weighted 1 / length^2, M the points' areas) with the seeds fixed:
            C1 into the seeds round the band (no kink where a band ends), even in arc length, clipped to [0, 1].
Then weights.py: 4 chains (twists), 5 shares, 6 points, 7 muscles, 8 breast tip,
9 islands (on our quads; the spine chain's cut-off front band held: SPINE_FRONT), 10 cap; and 2 mirror exactly, by OUR topology's mirror_of (each right point the left's,
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

VERSION = "v6"  # (v2: P1 R2 girdle skin CLAV, BLADE; v3: P1 R1b SPINE_FRONT; v4: P1 R1b BREAST clav_fade_m; v5: P1 A shape CLAV front_below; v6: P1 R1 rig root, T's steps +-HMAX at every joint, overlapping) written into each built glb's extras (build_topo.py stage_export); bump with the rules

SPINE = ["pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "neck_01", "neck_02", "Head"]
FINGERS = ["index", "middle", "ring", "pinky"]
HMAX = 0.04
HAND_SMOOTH = 12
# the girdle's skin (P1 R2: B's own girdle law moves the clavicle and the blade with the arm, so their skin must ride
# them; v1 held the trapezius with spine_05 and a clip's dropped shoulder left it standing: the dome). Anatomy: the
# trapezius runs from the neck's side to the acromion, above the clavicle at the front and over the scapular spine at
# the back; the deltoid's cap sits on the acromion.
#   CLAV  the trunk's clavicle share k = s01((t - t[0]) / (t[1] - t[0])) * fade(dy) * s01((d_seam - neck[0]) / neck[1]):
#         t along the clavicle (head 0, tail 1); dy off its line: above it full to above[0], gone by +above[1]
#         (the trapezius' top, 9-10 cm over the line at the neck's side), below it the v1 5 + 6 cm (the pec line and the
#         breasts keep the trunk's); d_seam the distance to the neck's open ring: within neck[0] the spine's (the
#         neck's own skin holds), all the clavicle's past neck[0] + neck[1]. (v1: t 0.25..0.75, |dy| 5 + 6 cm, no neck.)
#   CAP   (off: cap_deg 0) the shoulder's girdle fill may take as trunk seeds (the limb's share 0) the band's points above
#         the joint within cap_deg of up from it (medial: only those medial of the joint + lateral_m). Measured raw LBS on
#         the R2 law, her left: cap 35 the shoulder top follows a hanging arm (top drop / joint drop at 5 deg -0.54 ->
#         0.88) but abduction 90's outer outline 8.5/39.6 -> 13.9/57.8 mm (mean/max) and its d0.25 girth 1.00 -> 0.79;
#         cap 10 / 20, medial 35 / 50, medial 45 past -15 mm: the same 0.88 at 0.84-0.92 girth and 12-15 mm outlines;
#         the cap on the scapula (BLADE cap_amount 1): 16.3 mm. The share's cap is what lifts the top over a raised arm
#   BLADE the scapula takes `amount` of the clavicle's weight behind the clavicle head's coronal plane (eased over
#         `ease` m): the trapezius over the scapular spine and the blade ride the blade (the scap muscle's ball, kept,
#         is its own); cap_amount (off) the same share over CAP's cone (cap_deg, fading) lateral of the scap's head
#   front (v5, P1 A shape round 11): in front of the clavicle head's coronal plane (eased over front_ease m) the share below
#         the line fades over front_below instead (full to 1 cm, gone 5 cm under the line): under the clavicle at the front
#         lies the pectoralis' clavicular head's narrow strip, then the sternocostal head and the breast on the ribcage.
#         v4's 5 + 6 cm held 0.56-0.65 of the clavicle 2-6 cm under the line at the front (0.36 at 8 cm, into the breast),
#         and the clip's clavicle (11.7 deg off rest at her idle, A's line) dragged the upper chest and the breasts' tops
#         with it: the posed breasts p95 23 mm from A's at the Look (A, read as a check, not a source: 0.17 / 0.10 / 0.07
#         at 2 / 4 / 6 cm). The back keeps the v4 band (BLADE hands most of it to the scapula).
CLAV = {"t": (0.1, 0.6), "above": (0.11, 0.05), "below": (0.05, 0.06), "neck": (0.03, 0.03),
        "front_below": (0.01, 0.04), "front_ease": 0.03}
CAP = {"cap_deg": 0.0, "medial": False, "lateral_m": 0.0}
BLADE = {"amount": 0.6, "ease": 0.03, "cap_amount": 0.0, "cap_deg": (35.0, 65.0)}
# SPINE_FRONT (v3, P1 R1b round 2): the spine chain's height band (T) is the trunk's own skin all round the torso. CLAV
#   and the breasts cut spine_05's band at the sides, so its front part (the sternum and the breasts' top inner edge, 378
#   points on her) was a second component, and the island step (weights.py 9) handed it point by point to the largest
#   OTHER bone: neck_01 / spine_04 / clavicle / breast / pec patches a centimetre apart (clavicle 0.93 beside breast
#   0.97 8 mm away). A hanging arm turns the clavicle 2.7 deg about its head and its patch slid 5.6 mm: the crease at
#   the top of the cleavage (edges 1-9 -> 50-100 deg). Such a component (every point of it in these parts) is the
#   island step's keep_fixed: it keeps the smooth weights rules 1-8 gave it. Every other point's weights are unchanged.
SPINE_FRONT = {"parts": ("trunk", "breast")}
# BREAST (v3): the breast part takes the breast bone's share b = s01(d / fade_m), d its distance from the part's rim (the
#   trunk's weights fade out under it). v2's 5 cm held the clavicle's 0.9 share at the outer upper rim and dropped it in
#   3 cm into the breast: a hanging arm (the clavicle turns 2.7 deg) slid that rim 7 mm in against a still breast, a fold
#   (+30-47 deg) at armpit height. The longer fade spreads the slide over the whole outer breast (a soft mass).
#   v4 (round 3): the CLAVICLE's share fades over its own clav_fade_m (the rest of the trunk's over fade_m, so the
#   breast bone keeps its hold). A hanging arm swings the clavicle 2.8 deg and its skin 7-12 mm toward the midline:
#   on the outer flank (facing the arm) that is a push along the normal, largest where the share was largest, at the
#   upper outer rim (-7 mm against -3..-5 round it): a dent, a cloud on the cel terminator. Spread over 15 cm the
#   share is nearly even across the upper outer breast, which then slides as one piece (terminator turning at 3/4
#   743 -> 304 deg). Shorter fades made it worse (6 cm; a cut-off 7 cm from the armpit fold creased the upper pole).
BREAST = {"fade_m": 0.09, "clav_fade_m": 0.15}


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


def steps(u, knots, h):
    """Partition of one over len(knots)+1 pieces: piece i from knot i-1 to knot i, smoothstep +-h at each knot (one h,
    so the steps keep their knots' order and each piece, the difference of its two steps, is never negative). Where no
    two steps overlap it is hats' value for value (one of each piece's steps is 0 or 1 there)."""
    c = [np.ones(len(u))] + [s01((u - (k - h)) / (2 * h)) for k in knots] + [np.zeros(len(u))]
    return np.stack([c[i] - c[i + 1] for i in range(len(knots) + 1)], 1)


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
    knots = ys[1:]                       # (spine_01's head is the pelvis's: the pelvis owns all below it)
    assert all(b > a for a, b in zip(knots, knots[1:])), ("the spine chain's joints do not rise", knots)
    Hs = steps(y, knots, HMAX)
    for i, b in enumerate(SPINE):
        W[:, c.idx[b]] = Hs[:, i]
    # the girdle's skin (P1 R2, CLAV above): the clavicle owns the trapezius from the neck's side out to the acromion
    # and the skin just above the clavicle at the front; the neck's own skin by the seam holds the spine's
    E = np.sort(np.concatenate([c.Q[:, [0, 1]], c.Q[:, [1, 2]], c.Q[:, [2, 3]], c.Q[:, [3, 0]]]), 1)
    u, cnt = np.unique(E, axis=0, return_counts=True)
    from scipy.spatial import cKDTree
    seam = np.unique(u[cnt == 1].ravel())
    seam = seam[P[seam, 1] > c.head("spine_05")[1]]            # the neck's open ring (the body's only boundary up there)
    dn, _ = cKDTree(P[seam]).query(P)
    t0, t1 = CLAV["t"]
    for s, sx in (("l", 1.0), ("r", -1.0)):
        a, b = c.head(f"clavicle_{s}"), c.tail(f"clavicle_{s}")
        t = wt.seg_t(P, a, b)
        line = a[None] + np.clip(t, 0, 1)[:, None] * (b - a)[None]
        dy = P[:, 1] - line[:, 1]
        own = (P[:, 0] * sx > 0).astype(float)
        below = 1 - s01((-dy - CLAV["below"][0]) / CLAV["below"][1])
        if CLAV.get("front_below"):
            fr = s01((P[:, 2] - a[2]) / CLAV["front_ease"])
            below = (1 - fr) * below + fr * (1 - s01((-dy - CLAV["front_below"][0]) / CLAV["front_below"][1]))
        fade = np.where(dy > 0, 1 - s01((dy - CLAV["above"][0]) / CLAV["above"][1]), below)
        k = s01((t - t0) / (t1 - t0)) * fade * s01((dn - CLAV["neck"][0]) / CLAV["neck"][1]) * own
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
    b = s01(d / BREAST["fade_m"])
    ids = np.where(inb)[0]
    if BREAST.get("clav_fade_m"):
        # v4: the clavicle's share fades over its own (longer) distance, the rest of the trunk's over fade_m
        cl = [c.idx["clavicle_l"], c.idx["clavicle_r"]]
        bc = s01(d / BREAST["clav_fade_m"])
        Wc = W[np.ix_(ids, cl)]
        W[ids] *= (1 - b)[:, None]
        W[np.ix_(ids, cl)] = Wc * (1 - bc)[:, None]
        b = b * (1 - Wc.sum(1)) + bc * Wc.sum(1)          # the breast bone takes what the two fades give up
    else:
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
# hip pin (P1 hip, 5 Nov; the D verdict's fix 3 "pin the midline and perineum seeds to the pelvis"): own-side points
#   under the joint within pin_m of the crotch strip are trunk seeds (the crotch strip itself already was, the midline
#   too), and the fill's band reaches reach_m further (pin_m + reach_m from the strip) so the inner thigh's blend is not
#   squeezed into the 2 cm the medial rings leave (the root curve's rings crowd at the crotch: th1-th13 span 5 cm there
#   against 9.5 cm at the side). Measured raw LBS, hip 90 (her left): no pin 413 inside / 96 mm (51 at the perineum,
#   the cleft's bottom and the inner thigh's first rings swung forward into it); pin 2/3/4 cm, no reach: 263/142/90,
#   inner pits 13-21 mm; pin 4 + reach 6 cm: 30 at 17 mm; pin 4 + reach 10 cm: 0 inside, pits F7.3 S1.9 B6.9 M7.5.
#   Cost: the thigh's girth at d0.25 1.061 -> 1.096 at 90 on the baseline's selection (check.py's own selection, the
#   thigh chain >= 0.5, moves with the weights: it reads 1.24 there, see the P1 hip report)
# hip pin's back (P1 hip r2): reach_back_m, the reach off the crease side (behind the thigh's coronal plane, as the
#   limbs' `front`). Swept raw LBS hip 90 (her left; outline on the geometric strip, bends.py): back 0.10 outer
#   21.2/58.6 mm (mean/max), pit back 6.9; 0.09 19.8/54.3, 8.5; 0.08 18.5/49.8, 11.0 (112: 11.4); 0.07 17.2/44.1, 15.0;
#   0.05 14.9/41.5, 21.1; 0 12.4/41.3, 21.2 (no pin: 10.8/39.3, 7.0, but 413 inside): a shorter back reach trades the
#   outline for a pit at the back of the hip, so it stays 0.10 (the pit is what the judge sees; the key pulls the
#   outline). Most of round 1's outline loss (83 mm) was the check's other leg chosen by weights (bends.py, fixed).
# trunk_side (P1 hip r2): off the crease side, where the hip's blend r (the thigh chain's share of pelvis + thigh
#   chain) is under 1/2, the thigh chain's weight left after weights.py's shares goes to the share bone. Derivation:
#   (c) the shares rule's own split (its share bone holds the blend's middle, f = 4r(1 - r) = 1 at r = 1/2, so the
#   thigh chain's twist weight there is 0 and the trunk side's remainder, 0.02-0.07, was cut off from the thigh's own:
#   thigh_twist_01 islands of 341 points with the pin's reach); (a) a thigh's twist must not drag a stray patch of
#   the buttock. Raw LBS hip 90 unchanged to 0.01 mm (inside 0, pits F7.3 S1.9 B6.9 M7.5), 112 pits F 10.4 -> 7.3,
#   M 8.1 -> 6.1; islands 2 bones -> 0.
GIRDLE = {"shoulder": {"limb_m": 0.05, "trunk_m": 0.15},
          "hip": {"limb_m": 0.07, "trunk_rows": 10, "front_rows": 24, "pin_m": 0.04, "reach_m": 0.10,
                  "reach_back_m": 0.10, "trunk_side": True}}
# 4b's narrow crease band (weights.py RULES "bands") is NOT run here: on our loops under linear blend skinning it puts
# the crease back inside (elbow 90: 0 -> 133 points, 10 mm; knee 90: 0 -> 185, 21 mm); it is the corrective stage's
BANDS = False

def perineum_pin(c, s, own):
    """The hip pin (GIRDLE above): (pin, reach) masks, own side, under the joint; pin = within pin_m of the crotch
    strip (trunk seeds of the hip's fill), reach = within pin_m + reach_m (added to the fill's free band)."""
    Gh = GIRDLE["hip"]
    pin = np.zeros(c.n, bool)
    if not Gh.get("pin_m"):
        return pin, pin
    from scipy.spatial import cKDTree
    cr = c.part == c.pid("crotch")[0]
    d, _ = cKDTree(c.P[cr]).query(c.P)
    O = c.head(f"thigh_{s}")
    low = c.P[:, 1] < O[1] - Gh.get("pin_below_m", 0.0)
    pin = own & (d < Gh["pin_m"]) & low
    front = (c.P - O) @ (-c.world(f"thigh_{s}")[:3, 2]) > 0                  # the crease side (as limbs' `front`)
    rm = np.where(front, Gh.get("reach_m", 0.0), Gh.get("reach_back_m", Gh.get("reach_m", 0.0)))
    reach = own & (d < Gh["pin_m"] + rm) & low
    c.rep[f"hip_pin_{s}"] = int(pin.sum())
    return pin, reach


def hip_ratio(W, names, s):
    """The thigh chain's share r of (pelvis + thigh chain) before the shares (weights.py step 5's own r)."""
    th = [names.index(f"{n}_{s}") for n in ("thigh", "thigh_twist_01", "thigh_twist_02") if f"{n}_{s}" in names]
    a, b = W[:, names.index("pelvis")], W[:, th].sum(1)
    return np.where(a + b > 1e-9, b / np.maximum(a + b, 1e-12), 0.0)


def hip_trunk_side(W, names, s, r, P, frames):
    """The hip's trunk side (r < 1/2, own side): what the thigh chain keeps there after the shares goes to the
    share bone (rule below GIRDLE)."""
    th = [names.index(f"{n}_{s}") for n in ("thigh", "thigh_twist_01", "thigh_twist_02") if f"{n}_{s}" in names]
    G = frames[f"thigh_{s}"]
    back = (P - G[:3, 3]) @ (-G[:3, 2]) <= 0           # off the crease side (weights.py's shares: the full share)
    m = (r < 0.5) & back & (P[:, 0] * (1 if s == "l" else -1) > 0)
    W = W.copy()
    W[m, names.index(f"thigh_share_{s}")] += W[np.ix_(m, th)].sum(1)
    W[np.ix_(m, th)] = 0.0
    return W


def girdle_fill(c, s, joint, own, limb, free):
    """The limb's share g of a girdle: 1 on the limb's points (`limb`) outside `free`, 0 on every other point
    (the trunk's, the other side's), the bounded biharmonic fill on `free`."""
    x = (limb & ~free).astype(float)[:, None]
    fr = np.where(free & own)[0]
    g = fill(c.K, x, fr)[:, 0]
    c.rep[f"{joint}_{s}"] = {"band_points": int(len(fr)), **GIRDLE[joint]}
    return g


def limbs(c, W, rules=None):
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
        r = P - c.head(f"upperarm_{s}")
        cap = free & (r[:, 1] > np.cos(np.radians(CAP["cap_deg"])) * np.linalg.norm(r, axis=1))
        if CAP.get("medial"):
            cap &= r[:, 0] * sx < CAP.get("lateral_m", 0.0)
        free &= ~cap
        g = girdle_fill(c, s, "shoulder", own, m & ~cap, free)
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
        leg = (rules or {}).get("leg") or {}
        a0, aw = leg.get("ankle_m", (-0.02, 0.05))
        ca = 1 - s01((dz - a0) / aw)
        tf = wt.seg_t(P[m], c.head(f"foot_{s}"), c.tail(f"foot_{s}"))
        b0, bw = leg.get("ball_t", (0.85, 0.3))
        cb = s01((tf - b0) / bw)
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
        pin, reach = perineum_pin(c, s, own)
        free |= own & np.isin(c.part, [th, tr]) & reach
        free &= ~pin
        g = girdle_fill(c, s, "hip", own, m & ~pin, free)
        Af = np.zeros((c.n, len(c.names)))
        Af[:, c.idx[f"thigh_{s}"]] = 1.0
        Af[m] = Lg
        ids = np.where(m | (g > 0))[0]
        W[ids] = (1 - g[ids])[:, None] * W[ids] + g[ids, None] * Af[ids]
        rep[f"knee_blend_{s}_m"] = [round(float(lo), 4), round(float(hi), 4)]
    return W, rep


def blade(W, P, c, s):
    """BLADE: the scapula's share of the clavicle's weight at the back."""
    sx = 1.0 if s == "l" else -1.0
    cl, sc = c.idx[f"clavicle_{s}"], c.idx[f"scap_{s}"]
    back = s01((c.head(f"clavicle_{s}")[2] - P[:, 2]) / BLADE["ease"])
    r = P - c.head(f"upperarm_{s}")
    ang = np.degrees(np.arccos(np.clip(r[:, 1] / np.maximum(np.linalg.norm(r, axis=1), 1e-9), -1, 1)))
    a0, a1 = BLADE["cap_deg"]
    cap = (1 - s01((ang - a0) / (a1 - a0))) * s01((P[:, 0] * sx - c.head(f"scap_{s}")[0] * sx) / BLADE["ease"])
    share = np.maximum(BLADE["amount"] * back, BLADE["cap_amount"] * cap)
    t = share * (P[:, 0] * sx > 0) * W[:, cl]
    W[:, cl] -= t
    W[:, sc] += t
    return W


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


def spine_front(W, c, thr):
    """SPINE_FRONT: the points of each spine chain bone's components past its largest (W > thr, joined by quad edges as
    weights.py's island step joins them) that lie wholly in SPINE_FRONT's parts: held (keep_fixed) by the island step."""
    from scipy.sparse.csgraph import connected_components
    e = np.concatenate([c.Q[:, [i, (i + 1) % 4]] for i in range(4)])
    ok = np.isin(c.part, c.pid(*SPINE_FRONT["parts"]))
    keep = np.zeros(c.n, bool)
    for b in SPINE:
        on = W[:, c.idx[b]] > thr
        if on.sum() < 2:
            continue
        m = on[e[:, 0]] & on[e[:, 1]]
        G = sp.coo_matrix((np.ones(int(m.sum())), (e[m, 0], e[m, 1])), shape=(c.n, c.n))
        _, lab = connected_components(G, directed=False)
        ids, cnt = np.unique(lab[on], return_counts=True)
        big = ids[np.argmax(cnt)]
        for i in ids:
            pts = on & (lab == i)
            if i != big and ok[pts].all():
                keep |= pts
    c.rep["spine_front_held"] = int(keep.sum())
    return keep


def a_lower_breast(W, P, topo, sk, A, cfg):
    """A spec's "weights" "a_lower_breast" (P1 R1 round 30, her body: her breasts and the trunk round them ARE A's surface,
    her_a): A's own skin weights over the breasts' lower half and the skirt under and beside them, mapped onto B's bones
    by role (cfg "map", A bone: B bone; the breast's share split onto breast_tip by B's own rule, weights.breast), eased
    out over the trunk by the distance from the breast part (1 - s01(d / fade_m), front only: z > front_z) and up the
    breast by height (1 - s01((y - y_frac's height) / y_ease_m)); only where A's mapped bones hold cover_min of A's
    weight. Her left's taken, mirrored. Why (gate judge 2 fault 4, the right breast's lower curve to a point at the
    close-up and in idle_close): B's height steps hand the lower pole to the spine under the breast (B spine_03, A's
    spine_02: 0.55 at the bottom eighth, A 0.20) and its skirt's upper-chest share falls 0.44 -> 0 within 40 mm (A's 0.72
    -> 0.14 over 70 mm), so where the chest turns on the waist B's lower pole lags: posed bottom-middle vs A p95 4.8 mm
    at the close (round_29), 1.6 with A's weights. A: the game's own heroine.glb skin (its bind, B's points' closest
    points there, barycentric)."""
    from scipy.spatial import cKDTree
    import topo_uv as tu
    from surfdist import Surface
    names = sk["names"]
    m = A.mesh("Heroine")
    na = A.skeleton(0).names
    PA = m.P.astype(float)
    WA = np.zeros((len(PA), len(na)))
    np.put_along_axis(WA, m.J.astype(int), m.W.astype(float), 1)
    parts = list(map(str, topo["parts"]))
    part = topo["part"]
    br, tr = part == parts.index("breast"), part == parts.index("trunk")
    left = P[:, 0] > 0
    dB, _ = cKDTree(P[br]).query(P)
    ylo, yhi = P[br, 1].min(), P[br, 1].max()
    yc = ylo + float(cfg["y_frac"]) * (yhi - ylo)
    k = np.where(br, 1.0, np.where(tr & (P[:, 2] > float(cfg.get("front_z", 0.0))), 1 - s01(dB / float(cfg["fade_m"])), 0.0))
    k *= 1 - s01((P[:, 1] - yc) / float(cfg["y_ease_m"]))
    ids = np.where((k > 1e-4) & left)[0]
    q, _, tri, d = Surface(PA, m.T).closest(P[ids], k=16)
    a, b, c = (PA[m.T[tri, i]] for i in range(3))
    w = np.clip(tu.bary(q, a, b, c), 0, None)
    w /= w.sum(1, keepdims=True)
    Wq = sum(w[:, i:i + 1] * WA[m.T[tri, i]] for i in range(3))
    Wt = np.zeros((len(ids), len(names)))
    for an, bn in cfg["map"].items():
        Wt[:, names.index(bn)] += Wq[:, na.index(an)]
    cover = Wt.sum(1)
    Wt /= np.maximum(cover[:, None], 1e-12)
    for s in ("l", "r"):
        ib, it = names.index(f"breast_{s}"), names.index(f"breast_tip_{s}")
        h, tip = sk["ends"][f"breast_{s}"][0], sk["ends"][f"breast_tip_{s}"][1]
        lo, hi = wt.RULES["breast_tip"]
        kt = s01((wt.seg_t(P[ids], h, tip) - lo) / (hi - lo))
        Wt[:, it] += Wt[:, ib] * kt
        Wt[:, ib] *= 1 - kt
    kk = k[ids] * (cover >= float(cfg["cover_min"]))
    W = W.copy()
    W[ids] = (1 - kk[:, None]) * W[ids] + kk[:, None] * Wt
    W = mirror(W, topo, names)
    return W, {"points_left": int((kk > 1e-4).sum()), "A_dist_mm_p95": round(float(np.percentile(d[kk > 1e-4] * 1e3, 95)), 2),
               "cover_p5": round(float(np.percentile(cover[k[ids] > 1e-4], 5)), 3)}


def mirror(W, topo, names):
    sw = np.array([names.index(wt.swap_side(n)) for n in names])
    mo = topo["mirror_of"]
    r = mo >= 0
    W = W.copy()
    W[r] = W[mo[r]][:, sw]
    mid = topo["side"] == 0
    W[mid] = 0.5 * (W[mid] + W[mid][:, sw])
    return W


def body(P, topo, sk, rules=None):
    c = Ctx(P, topo, sk)
    names, par = sk["names"], sk["parents"]
    W = trunk(c)
    W, rep = limbs(c, W, rules)
    W = smooth_part(W, c.Q, np.isin(c.part, c.pid("hand")), HAND_SMOOTH)
    frames = {n: sk["worlds"][i] for i, n in enumerate(names)}
    tails = {n: sk["ends"][n][1] for n in names}
    Pg = c.P
    for side in ("l", "r"):
        W = wt.chain_split(W, Pg, names, sk["ends"], side)
        if BANDS:
            W = wt.bands(W, Pg, names, frames, side)
        r_hip = hip_ratio(W, names, side) if GIRDLE["hip"].get("trunk_side") else None
        W = wt.shares(W, Pg, names, frames, side)
        if r_hip is not None:
            W = hip_trunk_side(W, names, side, r_hip, Pg, frames)
        W = wt.points(W, Pg, names, frames, side)
        W = wt.muscles(W, Pg, names, par, tails, side)
        W = blade(W, Pg, c, side)
        W = wt.breast(W, Pg, names, sk["ends"], side)
    W = np.maximum(W, 0)
    W /= np.maximum(W.sum(1, keepdims=True), 1e-12)
    W = mirror(W, topo, names)
    moved_all = {}
    J, Wk = wt.cap(W, wt.RULES["cap"])
    Wd = np.zeros_like(W)
    np.put_along_axis(Wd, J, Wk, 1)
    fixed = spine_front(Wd, c, wt.RULES["island"])       # SPINE_FRONT (v3): the spine's own cut-off band is no stray
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
