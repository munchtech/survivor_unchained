"""Her arms rebuilt from ANATOMY (Body 21, 27 Oct 2026; the owner on the town close-up's bent arm: "that bend still just
dosn't look feminine OR athletic - it just looks clunky", and on the front 3/4 with the arm hanging: "armpit problems
there too, and elbow"). Three rounds nudged the old even tube by 3-10 mm and blind judges came out at chance: the
source was wrong (a ball deltoid on a cylinder, a round elbow, a tube forearm). This step builds the arm's FORM and puts
her skin on it.

THE FORM: a smooth implicit (signed distance, mm, negative inside) of bone and muscle volumes in her bone frames
(left-canonical; the right arm is the left's mirror image by construction):
  U  the upper arm: origin her shoulder joint (upperarm_l), s down the line to her elbow joint (lowerarm_l), x lateral,
     y front (her +Z made square to it);
  F  the forearm: origin her elbow joint, s2 down the line to her wrist (hand_l), x2 lateral (dorsal at the wrist: her
     rest forearm is mid-pronated, thumb forward), y2 front (radial / the thumb's side at the wrist).
Volumes (each a loft of an elliptical or quarter-elliptical cross-section along a segment, its radii from a profile;
FORM below holds every number):
  core      each segment's deep mass (humerus, brachialis, the deep heads; radius, ulna, the deep forearm), a loft whose
            four quarter-radii (out, in, front, back) follow profiles: slim where the arm is narrow (above the elbow,
            the wrist: flat, depth ~0.65 of its width);
  deltoid   three heads (clavicular, acromial, spinal) converging on a V on the outer arm ~45% down: a teardrop, its
            volume down and forward, never out past her shoulder line;
  biceps    a fusiform belly at the front peaking ~57% down, thinning into its tendon at the crease;
  triceps   long and lateral heads at the back, upper and middle, then a FLAT tendon plate down to the olecranon;
  brachialis showing low on the outer side between biceps and triceps;
  elbow     bone: the olecranon (a point behind the joint), the medial and lateral epicondyles, small blend radii;
  forearm   the brachioradialis / wrist-extensor wad high on the thumb's side (peaking 30-50 mm below the joint, rising
            30-40 mm above it on the outer arm), the flexor mass on the inner side, the ulna's border along the back;
  axilla    the pectoral's lower edge as the front fold (a soft rounded wedge from her chest wall into the front of her
            arm), unioned on her own surface (it only adds).
Blended with smooth-min (polynomial, radii 6-15 mm), then the skin offset (SKIN mm).

THE SKIN ON IT: each of her arm's vertices moves along its rest normal to the form's surface (the root of the implicit
along that line nearest to it), feathered by her arm's share of the skinning and into her shoulder's top, her armpit
and her hand (FEATHER); the move field smoothed over her surface. Same vertices and order, UVs untouched. Rest normals
recomputed (her stored normal + the surface's change). Her shoulder pose-space shapes (shoulder_*) kept as approved
(arm_contour_post.psd_keep); elbow_point_{l,r} and the rest are deltas and ride on the new shape (worn_reaver may go
stale: the outfit chain re-keys it).

    python tools/assets/arm_anatomy_post.py <in heroine.glb> <out heroine.glb> [--report] [--amt K]
Idempotent: done-mark arm_anatomy (a marked body is copied unchanged). Built on the git body (godot/art/people).
"""
import json
import os
import shutil
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MARK = "arm_anatomy"
XM = 0.0010          # her midline x (m): the mirror plane

# ---------------------------------------------------------------------------------------------------------- FORM --
# Frames: "U" upper arm (x lateral, y front, s down from the shoulder joint), "F" forearm (x2, y2, s2 from the elbow
# joint). All mm. Lofts: (frame, profile rows (s, out, in, front, back)) quarter-ellipse sections round the frame's
# own line. Spindles: (frame, A (x, y, s), B (x, y, s), outward hint (x, y), ra rows (u, mm), rb rows (u, mm), k):
# an elliptical section ra (outward) by rb (round the arm) along A->B. Ellipsoids: (frame, centre, radii x y s, k).
FORM = {
    "skin": 1.5,
    "core_U": [  # s: out, in, front, back (the deep mass round the humerus line)
        (-10, 26, 36, 34, 36), (20, 28, 40, 37, 38), (60, 29, 41, 39, 39), (100, 29.5, 40, 39, 38.5),
        (130, 30, 38.5, 39, 37.5), (160, 31, 36.5, 38.5, 35), (190, 32.5, 33.5, 36.5, 30.5),
        (215, 33, 30.5, 33.5, 26.5), (240, 32, 28.5, 29.5, 23.5), (262, 31, 28.5, 27, 22.5)],
    "core_F": [  # s2: out (dorsal), in (palmar), front (radial), back (ulnar)
        (-12, 32, 28, 27.5, 22.5), (15, 34, 29.5, 30, 23), (50, 35.5, 30, 31, 23.5), (90, 33, 28, 30, 23.5),
        (130, 29, 24, 28.5, 23), (170, 24.5, 19.5, 26.5, 23), (210, 20, 15.5, 25.5, 23.5),
        (240, 17.5, 14, 25, 24), (262, 17, 14, 24.5, 24.5)],
    "spindles": {
        # the deltoid's three heads to the V (U: x 24, y 4, s 118); outward hints point away from the humerus line
        "delt_mid": ("U", (12, 1, -22), (24, 4, 118), (1, 0), [(0, 13.5), (.086, 15.5), (.26, 14.5), (.44, 13.5), (.66, 11.5), (.84, 7.5), (1, 2.5)],
                     [(0, 17), (.2, 21), (.45, 19), (.75, 12), (1, 4)], 12),
        "delt_ant": ("U", (-6, 42, -16), (25, 10, 116), (0.2, 1), [(0, 12), (.25, 15), (.45, 14), (.7, 9), (1, 2.5)],
                     [(0, 16), (.25, 20), (.5, 16), (.8, 9), (1, 3)], 12),
        "delt_post": ("U", (0, -46, -12), (23, -2, 117), (0.1, -1), [(0, 11), (.25, 12.5), (.45, 12), (.7, 8), (1, 2.5)],
                      [(0, 16), (.25, 20), (.5, 16), (.8, 9), (1, 3)], 12),
        # biceps: belly at the front, peak ~57% of the humerus, tendon into the crease
        "biceps": ("U", (-6, 39, 45), (0, 23, 240), (0, 1), [(0, 5), (.25, 11), (.45, 18), (.55, 19), (.7, 15.5), (.85, 8), (1, 3)],
                   [(0, 10), (.25, 17), (.5, 21), (.7, 16), (.88, 8), (1, 4)], 13),
        # triceps: long head (back-inner), lateral head (back-outer), then the flat tendon plate
        "tri_long": ("U", (-16, -36, 30), (-4, -27, 180), (-0.35, -1), [(0, 7), (.3, 13.5), (.55, 15), (.75, 11), (1, 4)],
                     [(0, 12), (.35, 17), (.6, 15.5), (1, 7)], 13),
        "tri_lat": ("U", (11, -31, 40), (3, -26, 174), (0.3, -1), [(0, 5), (.35, 10.5), (.55, 11.5), (.8, 7), (1, 3)],
                    [(0, 11), (.4, 15), (.7, 12), (1, 6)], 12),
        "tri_plate": ("U", (0, -31.5, 172), (0, -24.5, 244), (0, -1), [(0, 4.5), (.5, 3.5), (1, 2.5)],
                      [(0, 24), (.5, 20), (1, 16)], 7),
        # brachialis: low on the outer side, between biceps and triceps
        "brachialis": ("U", (12, 6, 128), (12, 9, 246), (1, 0.3), [(0, 4), (.35, 9), (.6, 10), (.85, 6), (1, 3)],
                       [(0, 10), (.4, 15), (.75, 14), (1, 9)], 11),
        # the brachioradialis / wrist extensors' origin rising on the outer arm above the joint (U), its belly (F)
        "br_origin": ("U", (21, 6, 192), (27, 10, 262), (1, 0.4), [(0, 2.5), (.5, 6.5), (1, 10)],
                      [(0, 7), (.5, 11), (1, 15)], 9),
        "br_belly": ("F", (31, 10, -22), (12, 22, 175), (0.55, 0.85), [(0, 5), (.12, 9.5), (.3, 15.5), (.45, 13.5), (.7, 6), (1, 2.5)],
                     [(0, 9), (.15, 13), (.3, 18), (.5, 14), (.8, 8), (1, 5)], 12),
        "extensors": ("F", (24, -8, 0), (14, -6, 200), (1, -0.25), [(0, 7), (.2, 11), (.4, 10), (.7, 5), (1, 2)],
                      [(0, 13), (.3, 16), (.6, 12), (1, 7)], 13),
        "flexors": ("F", (-21, 3, -10), (-8, 12, 185), (-0.8, 0.6), [(0, 6), (.12, 10), (.28, 14), (.45, 12), (.65, 7.5), (.85, 4), (1, 2)],
                    [(0, 11), (.25, 18), (.5, 14), (1, 8)], 12),
        "ulna": ("F", (0, -20.5, 6), (-2, -20.5, 248), (0, -1), [(0, 4.5), (1, 4)], [(0, 7), (1, 6)], 8),
    },
    "ellipsoids": {
        "olecranon": ("F", (0, -19.5, -4), (9.5, 7.5, 12), 6),
        "epi_med": ("U", (-26, -3, 249), (7.5, 8, 10), 6),
        "epi_lat": ("U", (25, -1, 251), (6, 7.5, 9), 6),
    },
    # the front axillary fold (a round cone from her chest wall into her arm's front, unioned on her skin): OFF. Tried
    # chest (-72, 95, 25) -> arm (-30, 42, 95), r 14/10, k 12: it read as a nub on the breast's side, not a wedge.
    "fold": None,
}
FEATHER = {"arm_w": (0.35, 0.75), "top_s": (-28.0, 12.0), "pit_s": (48.0, 98.0), "pit_x": (-18.0, -38.0),
           "hand_s2": (238.0, 266.0)}
RAY = 40.0           # mm: how far along her normal the form's surface is looked for
SMOOTH = 2           # passes of the move field's smoothing (umbrella, 0.5)


# ------------------------------------------------------------------------------------------------------ helpers --
def _ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def _prof(rows, u):
    rows = np.asarray(rows, float)
    return np.interp(u, rows[:, 0], rows[:, 1])


def frames(J):
    """left-canonical bone frames (origin, axis, front, lateral) for U and F, mm-free (metres)"""
    def fr(A, B):
        a = (B - A) / np.linalg.norm(B - A)
        f = np.array([0, 0, 1.0]) - a[2] * a
        f /= np.linalg.norm(f)
        return dict(O=A, a=a, f=f, l=np.cross(f, a), L=float(np.linalg.norm(B - A)) * 1000)
    return {"U": fr(J["upperarm_l"], J["lowerarm_l"]), "F": fr(J["lowerarm_l"], J["hand_l"])}


def local(FR, k, P):
    """points (n, 3) m -> (x, y, s) mm in frame k"""
    d = (P - FR[k]["O"]) * 1000
    return np.stack([d @ FR[k]["l"], d @ FR[k]["f"], d @ FR[k]["a"]], 1)


def loft(Q, rows):
    """quarter-ellipse sections along the frame's line: rows (s, out, in, front, back)"""
    rows = np.asarray(rows, float)
    x, y, s = Q[:, 0], Q[:, 1], Q[:, 2]
    sc = np.clip(s, rows[0, 0], rows[-1, 0])
    rO, rI, rF, rB = (np.interp(sc, rows[:, 0], rows[:, i]) for i in (1, 2, 3, 4))
    rx = np.where(x > 0, rO, rI)
    ry = np.where(y > 0, rF, rB)
    q = np.hypot(x, y)
    rho = np.hypot(x / rx, y / ry)
    ds = q - q / np.maximum(rho, 1e-9)
    e = np.abs(s - sc)
    return np.where(e > 0, np.hypot(np.maximum(ds, 0), e), ds)


def spindle(Q, A, B, hint, ra_rows, rb_rows):
    A, B = np.asarray(A, float), np.asarray(B, float)
    t = B - A
    Ln = np.linalg.norm(t)
    t /= Ln
    h = np.array([hint[0], hint[1], 0.0])
    ea = h - (h @ t) * t
    ea /= np.linalg.norm(ea)
    eb = np.cross(t, ea)
    d = Q - A
    u = (d @ t) / Ln
    uc = np.clip(u, 0, 1)
    q = d - (uc * Ln)[:, None] * t
    qa, qb = q @ ea, q @ eb
    ra, rb = _prof(ra_rows, uc), _prof(rb_rows, uc)
    qn = np.hypot(qa, qb)
    rho = np.hypot(qa / ra, qb / rb)
    ds = qn - qn / np.maximum(rho, 1e-9)
    e = np.abs(u - uc) * Ln
    return np.where(e > 0, np.hypot(np.maximum(ds, 0), e), ds)


def ellipsoid(Q, C, R):
    p = (Q - np.asarray(C, float)) / np.asarray(R, float)
    k0 = np.linalg.norm(p, axis=1)
    k1 = np.linalg.norm(p / np.asarray(R, float), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def round_cone(Q, A, B, r):
    A, B = np.asarray(A, float), np.asarray(B, float)
    t = B - A
    Ln = np.linalg.norm(t)
    u = np.clip(((Q - A) @ t) / (Ln * Ln), 0, 1)
    return np.linalg.norm(Q - (A + u[:, None] * t), axis=1) - (r[0] + (r[1] - r[0]) * u)


class Form:
    """the arm's implicit at left-canonical rest points (m): mm, negative inside"""

    def __init__(s, FR, form=FORM):
        s.FR, s.form = FR, form

    def parts(s, P):
        QU, QF = local(s.FR, "U", P), local(s.FR, "F", P)
        Q = {"U": QU, "F": QF}
        fm = s.form
        out = {"core_U": (loft(QU, fm["core_U"]), 14.0), "core_F": (loft(QF, fm["core_F"]), 14.0)}
        for n, (k, A, B, hint, ra, rb, kk) in fm["spindles"].items():
            out[n] = (spindle(Q[k], A, B, hint, ra, rb), kk)
        for n, (k, C, R, kk) in fm["ellipsoids"].items():
            out[n] = (ellipsoid(Q[k], C, R), kk)
        return out

    def __call__(s, P):
        pr = s.parts(P)
        D = None
        for n, (d, k) in pr.items():
            D = d if D is None else smin(D, d, k)
        if s.form.get("fold"):
            D = smin(D, s.fold(P), s.form["fold"]["k"])
        return D - s.form["skin"]

    def fold(s, P):
        f = s.form["fold"]
        return round_cone(local(s.FR, "U", P), f["chest"], f["arm"], f["r"])


# ------------------------------------------------------------------------------------------------- projection --
def _roots(fn, P0, N, ray=RAY, step=2.0):
    """per point: the t (mm) along N nearest 0 where fn(P0 + t N, sel) crosses zero (nan if none); sel = the rows"""
    ts = np.arange(-ray, ray + 1e-6, step)
    allr = np.arange(len(P0))
    V = np.stack([fn(P0 + (t / 1000.0) * N, allr) for t in ts], 1)
    best = np.full(len(P0), np.nan)
    bestabs = np.full(len(P0), np.inf)
    for i in range(len(ts) - 1):
        a, b = V[:, i], V[:, i + 1]
        x = (a <= 0) != (b <= 0)
        tt = ts[i] + step * a / np.where(x, a - b, 1.0)
        better = x & (np.abs(tt) < bestabs)
        best[better] = tt[better]
        bestabs[better] = np.abs(tt[better])
    ok = np.nonzero(np.isfinite(best))[0]
    for _ in range(2):                                   # secant refinement
        t0 = best[ok]
        f0 = fn(P0[ok] + (t0 / 1000.0)[:, None] * N[ok], ok)
        f1 = fn(P0[ok] + ((t0 + 0.25) / 1000.0)[:, None] * N[ok], ok)
        g = (f1 - f0) / 0.25
        best[ok] = t0 - f0 / np.where(np.abs(g) > 1e-3, g, 1.0)
    return best


def feather(b, FR, P, side):
    import arm_contour_post as ac
    fe = FEATHER
    wa = ac._armw(b, side)
    w = _ss(fe["arm_w"][0], fe["arm_w"][1], wa)
    QU, QF = local(FR, "U", P), local(FR, "F", P)
    w *= _ss(fe["top_s"][0], fe["top_s"][1], QU[:, 2])
    pit = _ss(fe["pit_x"][0], fe["pit_x"][1], QU[:, 0]) * (1 - _ss(fe["pit_s"][0], fe["pit_s"][1], QU[:, 2]))
    w *= 1 - pit
    w *= 1 - _ss(fe["hand_s2"][0], fe["hand_s2"][1], QF[:, 2])
    side_ok = (b.U[:, 0] > XM) if side == "l" else (b.U[:, 0] < XM)
    return w * side_ok


def moves(b, form=FORM, amt=1.0, smooth=SMOOTH, report=None):
    """(dU (n, 3) m, info): her arm's skin onto the form, both sides (the right mirrored), feathered and smoothed"""
    import pit_hollow_post as ph
    J = {n: np.linalg.inv(b.ibm[i])[:3, 3] for i, n in enumerate(b.names)}
    FR = frames(J)
    fm = Form(FR, form)
    N0 = ph.vn(b.U, b.F)
    for _ in range(2):                                   # a steadier ray: her normals smoothed a little
        N0 = N0 + b.lap(N0) * 0.5
        N0 /= np.maximum(np.linalg.norm(N0, axis=1, keepdims=True), 1e-12)
    n = len(b.U)
    dU = np.zeros((n, 3))
    info = {}
    for side, sg in (("l", 1), ("r", -1)):
        mir = np.array([sg, 1, 1.0])
        off = np.array([XM * (1 - sg), 0, 0])
        P = b.U * mir + off
        N = N0 * mir
        w = feather(b, FR, P, side)
        on = np.nonzero(w > 1e-3)[0]
        t = _roots(lambda Pq, sel: fm(Pq), P[on], N[on])
        miss = ~np.isfinite(t)
        if miss.any():                                    # no root near: take the neighbours' move (diffused)
            tt = np.zeros(n)
            tt[on] = np.where(miss, 0.0, t)
            have = np.zeros(n)
            have[on[~miss]] = 1.0
            for _ in range(30):
                num, den = b.A @ (tt * have), b.A @ have
                fill = (have == 0) & (den > 0)
                tt[fill] = num[fill] / den[fill]
                have[fill] = 1.0
            t = np.where(miss, tt[on], t)
        D = np.zeros((n, 3))
        D[on] = (t * w[on])[:, None] * N[on] / 1000.0
        # the front axillary fold on her own surface where the arm's form doesn't hold (her chest, the pit): it adds
        f = form.get("fold")
        tf = np.zeros(n)
        if f:
            sd = (b.U[:, 0] > XM) if side == "l" else (b.U[:, 0] < XM)
            cand = np.nonzero(sd & (fm.fold(P) < f["k"] + 20) & (w < 0.999))[0]
            if len(cand):
                P0c, N0c = P[cand], N[cand]

                def u_fn(Pq, sel):
                    tt = ((Pq - P0c[sel]) * 1000 * N0c[sel]).sum(1)
                    return smin(tt, fm.fold(Pq), f["k"])
                tr = _roots(u_fn, P0c, N0c, ray=30.0, step=1.5)
                tf[cand] = np.where(np.isfinite(tr), np.maximum(tr, 0), 0)
            D += ((1 - w) * tf)[:, None] * N / 1000.0
        D = D * mir                                       # back to her side
        dU += D
        info[side] = dict(points=int(len(on)), missed=int(miss.sum()), max_mm=round(float(np.abs(t).max()), 1),
                          fold_max_mm=round(float(tf.max()), 1))
    # smooth the move field over her surface (the stretch between rays), where it moves
    act = np.linalg.norm(dU, axis=1) > 1e-5
    grow = act.copy()
    for _ in range(3):
        grow = grow | (b.A @ grow.astype(float) > 0)
    for _ in range(smooth):
        dU = np.where(grow[:, None], dU + 0.5 * b.lap(dU), dU)
    return dU * amt, info


# ----------------------------------------------------------------------------------------------------- writing --
def run(src, dst, form=FORM, amt=1.0, quiet=False):
    from heroine_neck import _Gl
    import pit_hollow_post as ph
    import arm_contour_post as ac
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    G = _Gl(dst)
    g = G.g
    ex = g.setdefault("asset", {}).setdefault("extras", {})
    if ex.get(MARK):
        print("ARM_ANATOMY: %s has had it" % dst)
        return None
    b = ph.Body(G)
    dU, info = moves(b, form=form, amt=amt)
    n0 = ph.vn(b.U, b.F)
    n1 = ph.vn(b.U + dU, b.F)
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    o = 0
    for p in prims:
        ai, ni = p["attributes"]["POSITION"], p["attributes"]["NORMAL"]
        X = G.get(ai).astype(float)
        w = b.wid[o:o + len(X)]
        o += len(X)
        X = X + dU[w]
        Nn = G.get(ni).astype(float) + (n1 - n0)[w]
        Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
        G.put(ai, X.astype(np.float32))
        G.put(ni, Nn.astype(np.float32))
        g["accessors"][ai]["min"] = X.min(0).astype(np.float32).tolist()
        g["accessors"][ai]["max"] = X.max(0).astype(np.float32).tolist()
    rep = {}
    ac.psd_keep(G, prims, b.wid, dU, n1 - n0, rep)
    mv = np.linalg.norm(dU, axis=1) * 1000
    ex[MARK] = {"amt": amt, "skin": form["skin"], "max_mm": round(float(mv.max()), 2), "info": info}
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binb = bytes(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + binb
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    if not quiet:
        print("ARM_ANATOMY: %d points moved > 0.5 mm, max %.1f mm -> %s" % ((mv > 0.5).sum(), mv.max(), dst))
        print("  " + json.dumps(info))
        print("  psd kept (points, max mm taken back): " + ", ".join("%s %d/%.1f" % (k, v[0], v[1]) for k, v in rep.items()))
    return info


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    amt = 1.0
    if "--amt" in sys.argv:
        amt = float(sys.argv[sys.argv.index("--amt") + 1])
        a = [x for x in a if x != str(sys.argv[sys.argv.index("--amt") + 1])]
    run(a[0], a[1], amt=amt)
