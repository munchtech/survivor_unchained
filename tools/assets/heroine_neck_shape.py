"""Her neck and collar given a female form, mirror-alike (face 36, 21 October 2026: the owner, "close out her body";
her neck "just looks... weird", "the neck is bad in the day" too, "this area is hecked" on her left neck, a step on
her left outline with her head turned right; "clavicles absent at the Look").

What it fixes (measured on the built heroine.glb, rest pose): her neck was a straight-sided tube nearly her jaw's
width (front view 105 mm at its narrowest, under a 125 mm jaw: 0.84), with no form on it: no sternocleidomastoid
(SCM) cords, the throat a keel (10 mm proud of its sides 15 mm below her chin), no notch between cords, no clavicle
or the hollow above it (her chest ran up to her trapezius as one plane). And her left and right differed: 1.6 mm
rms over her neck, 4.0 mm at most (her left throat 4 mm proud of her right's mirror at x 24 mm, her left side's
lower neck 3.5 mm sunken), 1.7 / 4.4 mm over her collar.

The step, on her rest positions (the skin as the game draws her at rest), one smooth field:
  1. her two sides made mirror-alike about her midline (x = XM: her face's and torso's fitted mirror plane):
     each point along its normal onto the other side's skin mirrored, her left taking SHARE_NECK of the
     difference over her neck (the owner's faults are her left's), the two halfway over her collar and upper back;
  2. her neck's sides drawn in (TAPER, horizontal, by |sin| of the angle round her neck to a power, so her throat
     and nape keep their depth), most at mid-neck, none at her jaw line or her shoulders: a taper to a narrower
     mid-neck that flares into her trapezius;
  3. form along each point's (smoothed) normal: her SCM cords from under each ear down and forward to the sternal
     notch, a soft hollow behind each, the notch between their heads, her throat's keel eased, her clavicles as a
     gentle ridge with the supraclavicular hollow above (every bump a smooth falloff round a path or point on her
     skin, mirror-alike by construction).
Nothing moves above her gonion line (rest y GONION_Y) or on her jaw's underside (a cap round her neck's own
radius). Her head's lower neck, her graft and her body move as one (each welded point once: the seam cannot open).
Positions and normals only (normals turned by their surface's turn), on the basis: her shape keys are deltas and
keep their shapes. Moves are made in rest space and written to her bind positions through each point's skinning.

Followers: every record keyed by her bind points (armor_tuck/*.bin, armor_cover/*.bin) re-keyed; every piece and
hair point near the moved skin carried by the move of the skin under it (in full within FOLLOW[0], none past
FOLLOW[1]). Disjoint from breast_sym_post.py's patch (y 1.335-1.433 bind), so the two commute.

    python tools/assets/heroine_neck_shape.py <heroine.glb in> <heroine.glb out>
    python tools/assets/heroine_neck_shape.py --art godot/art/people [--no-follow] [--dry]
Then rebuild her play LOD (heroine_lod.py) and reimport.
"""
import json
import os
import shutil
import struct
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heroine_neck import _Gl, _mark  # noqa: E402

MARK = "heroine_neck_shape"
XM = 0.0010                       # her midline (m): her face's fitted mirror plane (torso's 1.5 mm)
CZ = (-0.030, 0.18, 1.55, 1.66)   # her neck's axis: z = CZ0 + CZ1 (clip(y, CZ2, CZ3) - 1.60)
GONION_Y = 1.672                  # rest y of her jaw's angle: nothing moves above
TOP_FADE = 0.010                  # the neck's moves eased out over this below GONION_Y
CAP = (0.006, 0.014)              # over her neck's own radius by: whole within the first, none past the second
CAP_Y = (1.600, 1.612)            # (the cap acts above this: her jaw's underside; below, her shoulders are free)
# 1. left = right
SYM_BOX = ((1.47, 1.50), (0.15, 0.18))   # rest y: none below the first, whole above the second; |x - XM|: whole, none
SHARE_NECK = 1.0                  # her left's share of the difference over her neck (her collar: 0.5)
SYM_PASSES = 3
SYM_SMOOTH = 8                    # rings the side-to-side difference is smoothed over (first passes)
SYM_SMOOTH_LAST = 2               # (and in the last, after the fairing: the local differences out)
FAIR_ITERS = 30                   # (lambda/mu pairs over her neck, before the form)
FAIR_LM = (0.5, -0.53)
FAIR_BOX = ((1.555, 1.575), 0.080, 0.095)  # rest y: none below the first, whole above the second; radius whole, none
# 2. taper
TAPER = 0.0045                    # (m, at her sides, mid-neck)
TAPER_POW = 1.5
TAPER_Y = ((1.560, 0.0), (1.580, 0.25), (1.600, 0.6), (1.622, 1.0), (1.645, 1.0), (1.660, 0.45), (GONION_Y, 0.0))
# 3. form (mm): paths of (theta deg round her neck from her front, + her left; rest y; height; sigma), her left
SCM = ((100, 1.672, 0.0, 15.0), (88, 1.655, 1.6, 15.0), (70, 1.638, 2.4, 15.0), (50, 1.620, 2.6, 14.0),
       (32, 1.603, 2.5, 13.0), (18, 1.590, 2.2, 11.0), (12, 1.582, 1.4, 9.0))
BEHIND = ((118, 1.652, 0.0, 14.0), (104, 1.632, -1.5, 14.0), (92, 1.612, -1.9, 14.0), (84, 1.596, -1.5, 14.0))
# clavicle: (x mm from her midline, rest y, height, sigma) on her front skin (round 2: about 3 mm, sigma widened
# laterally where her collar's edges run 12-15 mm, so the mesh carries it as a broad form, not a beaded line)
CLAV = ((15, 1.577, 1.4, 8.0), (25, 1.572, 2.7, 9.0), (40, 1.566, 3.0, 10.0), (60, 1.560, 3.0, 12.0),
        (80, 1.557, 2.8, 14.0), (100, 1.555, 2.6, 15.0), (120, 1.555, 2.0, 15.0), (140, 1.556, 1.0, 15.0),
        (155, 1.558, 0.0, 15.0))
# blobs: (x mm, rest y, depth mm, sigma x mm, sigma y mm) on her front skin
BLOBS = (("notch", 0, 1.585, -4.0, 10.0, 8.0), ("keel", 0, 1.607, -3.0, 12.0, 10.0),
         ("fossa", 62, 1.574, -4.5, 17.0, 11.0))
# her nape drawn in (m, radially, by max(0, -cos theta) ** NAPE_POW: her neck's front-to-back depth was 1.1-1.15 of
# its width at mid-neck): a gentle hollow (her neck's lordosis) under her skull, none at her trapezius or her jaw line
NAPE = 0.0030
NAPE_POW = 1.5
NAPE_Y = ((1.585, 0.0), (1.605, 0.6), (1.625, 1.0), (1.645, 1.0), (1.660, 0.45), (GONION_Y, 0.0))
NSMOOTH = 4                       # rings her normals are smoothed over for the form's direction
FOLLOW = (0.01, 0.03)             # a piece's point follows the skin under it in full within 1 cm, none past 3


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _q2m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def _skin_mats(G):
    """Each joint's skinning matrix at her rest pose (world rest x inverse bind)."""
    g = G.g
    N = g["nodes"]
    par = {c: i for i, n in enumerate(N) for c in n.get("children", [])}
    W = {}

    def w(i):
        if i not in W:
            n = N[i]
            M = np.eye(4)
            M[:3, :3] = _q2m(n.get("rotation", [0, 0, 0, 1])) * np.array(n.get("scale", [1, 1, 1]))
            M[:3, 3] = n.get("translation", [0, 0, 0])
            W[i] = (w(par[i]) @ M) if i in par else M
        return W[i]
    sk = g["skins"][0]
    ibm = G.get(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    return np.array([w(j) @ ibm[k] for k, j in enumerate(sk["joints"])])


class _Skin:
    """Her body's, graft's and head's skin: bind, rest, each vertex's skinning (linear part), welded by bind place."""

    def __init__(s, G):
        g = G.g
        N = g["nodes"]
        hb = [n for n in N if n.get("name") == "Heroine"][0]
        hh = [n for n in N if n.get("name") == "HeroineHead"][0]
        s.prims = [p for p in g["meshes"][hb["mesh"]]["primitives"] if "JOINTS_0" in p["attributes"]]
        s.prims += [p for p in g["meshes"][hh["mesh"]]["primitives"]
                    if g["materials"][p["material"]].get("name") == "skin_head"]
        s.kind = [g["materials"][p["material"]].get("name") for p in s.prims]
        M = _skin_mats(G)
        Bs, Rs, As, Fs = [], [], [], []
        for p in s.prims:
            a = p["attributes"]
            P = G.get(a["POSITION"]).astype(float)
            J = G.get(a["JOINTS_0"]).astype(int)
            Wt = G.get(a["WEIGHTS_0"]).astype(float)
            Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-12)
            A = np.einsum("nc,ncij->nij", Wt, M[J])          # (n, 4, 4) blended
            Bs.append(P)
            Rs.append(np.einsum("nij,nj->ni", A[:, :3, :3], P) + A[:, :3, 3])
            As.append(A[:, :3, :3])
            Fs.append(G.get(p["indices"]).reshape(-1, 3).astype(int))
        s.off = np.cumsum([0] + [len(x) for x in Bs])
        Bv, Rv, Av = np.concatenate(Bs), np.concatenate(Rs), np.concatenate(As)
        F = np.concatenate([f + s.off[k] for k, f in enumerate(Fs)])
        _, first, wid = np.unique(np.round(Bv / 1e-5).astype(np.int64), axis=0, return_index=True, return_inverse=True)
        s.wid = wid.ravel()
        nw = s.wid.max() + 1
        cnt = np.bincount(s.wid, minlength=nw)[:, None]
        s.B = Bv[first]
        s.R = np.zeros((nw, 3))
        np.add.at(s.R, s.wid, Rv)
        s.R /= cnt
        s.A = np.zeros((nw, 3, 3))
        np.add.at(s.A, s.wid, Av)
        s.A /= cnt[:, :, None]
        Fw = s.wid[F]
        s.F = Fw[(Fw[:, 0] != Fw[:, 1]) & (Fw[:, 1] != Fw[:, 2]) & (Fw[:, 2] != Fw[:, 0])]
        E = np.unique(np.sort(np.r_[s.F[:, [0, 1]], s.F[:, [1, 2]], s.F[:, [2, 0]]], 1), axis=0)
        s.E = E
        import scipy.sparse as sp
        Ad = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(nw, nw)).tocsr()
        s.Wn = (sp.diags(1 / np.maximum(np.asarray(Ad.sum(1)).ravel(), 1)) @ Ad).tocsr()

    def vn(s, X):
        q = np.cross(X[s.F[:, 1]] - X[s.F[:, 0]], X[s.F[:, 2]] - X[s.F[:, 0]])
        n = np.zeros_like(X)
        for k in range(3):
            np.add.at(n, s.F[:, k], q)
        return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def _cz(y):
    return CZ[0] + CZ[1] * (np.clip(y, CZ[2], CZ[3]) - 1.60)


def _cyl(X):
    """theta (deg, + her left), radius, the horizontal radial unit vector, round her neck's axis."""
    dx, dz = X[:, 0] - XM, X[:, 2] - _cz(X[:, 1])
    r = np.hypot(dx, dz)
    e = np.stack([dx, np.zeros_like(dx), dz], 1) / np.maximum(r, 1e-9)[:, None]
    return np.degrees(np.arctan2(dx, dz)), r, e


def _mesh(X, F):
    import trimesh
    return trimesh.Trimesh(X, F, process=False)


def _neck_radius(X, N):
    """Her neck's own radius by (|theta|, y), from points facing sideways, inner-most (her jaw's underside and ramus
    stand outside it): a lookup (|theta| deg, y) -> r."""
    th, r, _ = _cyl(X)
    ths, ys = np.arange(0, 181, 5.0), np.arange(1.590, 1.700, 0.0025)
    m = (np.abs(N[:, 1]) < 0.6) & (X[:, 1] > ys[0] - 0.003) & (X[:, 1] < ys[-1] + 0.003) & (r < 0.09)
    G = np.full((len(ths), len(ys)), np.nan)
    at, ay, ar = np.abs(th[m]), X[m, 1], r[m]
    for i, t in enumerate(ths):
        mi = np.abs(at - t) < 4.0
        for j, y in enumerate(ys):
            mj = mi & (np.abs(ay - y) < 0.002)
            if mj.any():
                G[i, j] = ar[mj].min()
    for i in range(len(ths)):              # (gaps filled along y, then theta)
        row = G[i]
        ok = ~np.isnan(row)
        if ok.any():
            G[i] = np.interp(ys, ys[ok], row[ok])
    for j in range(len(ys)):
        col = G[:, j]
        ok = ~np.isnan(col)
        G[:, j] = np.interp(ths, ths[ok], col[ok]) if ok.any() else 0.06
    from scipy.ndimage import median_filter
    G = median_filter(G, size=3, mode="nearest")
    from scipy.interpolate import RegularGridInterpolator
    f = RegularGridInterpolator((ths, ys), G, bounds_error=False, fill_value=None)
    return lambda t, y: f(np.stack([np.clip(np.abs(t), 0, 180), np.clip(y, ys[0], ys[-1])], 1))


def _surf_point(M, origin, direction):
    loc, ri, _ = M.ray.intersects_location(origin[None], direction[None], multiple_hits=True)
    if not len(loc):
        return None
    d = np.linalg.norm(loc - origin, axis=1)
    return loc[d.argmin()]


def _path(M, pts, kind):
    """A path on her skin, densified to 1 mm: (points (n,3), height mm, sigma mm), her left and her right."""
    out = []
    for side in (1, -1):
        P, H, S = [], [], []
        for k in range(len(pts) - 1):
            a, b = np.array(pts[k], float), np.array(pts[k + 1], float)
            for t in np.linspace(0, 1, 12, endpoint=False):
                P.append(a + (b - a) * t)
        P.append(np.array(pts[-1], float))
        Q = []
        for u, y, h, sg in P:
            if kind == "neck":
                th = np.radians(u) * side
                o = np.array([XM, y, _cz(y)])
                d = np.array([np.sin(th), 0, np.cos(th)])
                q = _surf_point(M, o, d)
            else:
                q = _surf_point(M, np.array([XM + side * u / 1000, y, 0.4]), np.array([0, 0, -1.0]))
            if q is not None:
                Q.append(q)
                H.append(h)
                S.append(sg)
        Q, H, S = np.array(Q), np.array(H), np.array(S)
        # (densified to about 1 mm along the path)
        L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
        n = max(int(L[-1] / 0.001), 2)
        t = np.linspace(0, L[-1], n)
        out.append((np.stack([np.interp(t, L, Q[:, k]) for k in range(3)], 1), np.interp(t, L, H), np.interp(t, L, S)))
    return out


def form_field(X, N, M):
    """The form's scalar (m, along the smoothed normal) at points X, from her skin M (rest, mirror-alike)."""
    s = np.zeros(len(X))
    for pts, kind in ((SCM, "neck"), (BEHIND, "neck"), (CLAV, "front")):
        for Q, H, S in _path(M, pts, kind):
            d, j = cKDTree(Q).query(X)
            s += H[j] / 1000 * np.exp(-(d / (S[j] / 1000)) ** 2)
    for name, x, y, h, sx, sy in BLOBS:
        for side in ((1,) if x == 0 else (1, -1)):
            c = _surf_point(M, np.array([XM + side * x / 1000, y, 0.4]), np.array([0, 0, -1.0]))
            d = X - c
            s += h / 1000 * np.exp(-((d[:, 0] / (sx / 1000)) ** 2 + (d[:, 1] / (sy / 1000)) ** 2 + (d[:, 2] / (sx / 1000)) ** 2))
    return s


def taper_field(X):
    th, r, e = _cyl(X)
    g = PchipInterpolator([a for a, _ in TAPER_Y], [b for _, b in TAPER_Y])(np.clip(X[:, 1], TAPER_Y[0][0], TAPER_Y[-1][0]))
    gn = PchipInterpolator([a for a, _ in NAPE_Y], [b for _, b in NAPE_Y])(np.clip(X[:, 1], NAPE_Y[0][0], NAPE_Y[-1][0]))
    nape = NAPE * np.clip(gn, 0, 1) * np.maximum(0, -np.cos(np.radians(th))) ** NAPE_POW
    return -(TAPER * np.clip(g, 0, 1) * np.abs(np.sin(np.radians(th))) ** TAPER_POW + nape)[:, None] * e


def windows(X, nrad):
    """(the neck's window: 0 above her gonion line and on her jaw's underside; the left = right window)"""
    th, r, _ = _cyl(X)
    top = _ss((GONION_Y - X[:, 1]) / TOP_FADE)
    cap = _ss((nrad(th, X[:, 1]) + CAP[1] - r) / (CAP[1] - CAP[0]))
    capw = _ss((X[:, 1] - CAP_Y[0]) / (CAP_Y[1] - CAP_Y[0]))
    neck = top * (1 - capw + capw * cap)
    sym = _ss((X[:, 1] - SYM_BOX[0][0]) / (SYM_BOX[0][1] - SYM_BOX[0][0])) * \
        _ss((SYM_BOX[1][1] - np.abs(X[:, 0] - XM)) / (SYM_BOX[1][1] - SYM_BOX[1][0])) * neck
    return neck, sym


def _mirror_sd(X, F, Q):
    """Signed distance (m) of points Q to the skin X mirrored about XM (+ = Q stands out of it), and its normal."""
    import trimesh
    sel = np.abs(X[:, 0] - XM) < 0.25
    Fm = F[sel[F].all(1)]
    Xm = X.copy()
    Xm[:, 0] = 2 * XM - Xm[:, 0]
    M = trimesh.Trimesh(Xm, Fm[:, ::-1], process=False)
    cp, d, tri = trimesh.proximity.closest_point(M, Q)
    n = M.face_normals[tri]
    return d * np.sign(((Q - cp) * n).sum(1)), n


def symmetrize(S, X, w, report=True, passes=SYM_PASSES, smooth=None):
    """Her two sides onto each other's mirror inside w (rest positions in, out): each point along its (smoothed)
    normal by its share of its distance from the other side mirrored, that distance smoothed over SYM_SMOOTH rings
    first (the difference is broad; the coarse graft's closest points jitter point to point)."""
    X = X.copy()
    th, r, _ = _cyl(X)
    a = 0.5 + (SHARE_NECK - 0.5) * _ss((0.075 - r) / 0.01) * _ss((X[:, 1] - 1.555) / 0.01)
    share = np.where(X[:, 0] > XM, a, 1 - a)
    ix = np.nonzero(w > 0)[0]
    if not len(ix):
        return X
    for k in range(passes):
        N = S.vn(X)
        for _ in range(NSMOOTH):
            N = S.Wn @ N
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        sd = np.zeros(len(X))
        sd[ix], _ = _mirror_sd(X, S.F, X[ix])
        sd *= share * w
        for _ in range(SYM_SMOOTH if smooth is None else smooth):
            sd = (S.Wn @ sd) * (w > 0)
        X -= sd[:, None] * N
        if report:
            print("NECK_SHAPE: left = right pass %d, largest move %.2f mm" % (k + 1, np.abs(sd).max() * 1000))
    return X


def fair(S, X, w, report=True):
    """Her neck faired (Taubin lambda/mu, along each point's normal) inside w: the high-frequency lumps (her left's
    and the facets mirrored onto it) out before the form goes on."""
    N0 = S.vn(X)
    Y = X.copy()
    for _ in range(FAIR_ITERS):
        for lm in FAIR_LM:
            Y = Y + lm * w[:, None] * (S.Wn @ Y - Y)
    V = X + np.einsum("ij,ij->i", Y - X, N0)[:, None] * N0
    if report:
        print("NECK_SHAPE: faired, largest move %.2f mm" % (np.linalg.norm(V - X, axis=1).max() * 1000))
    return V


def _rot_normals(Nr, n0, n1):
    """Each normal turned by the turn taking n0 to n1 (Rodrigues)."""
    v = np.cross(n0, n1)
    c = np.clip((n0 * n1).sum(1), -1, 1)
    k = 1 / (1 + c + 1e-12)
    vx = np.cross(v, Nr)
    out = Nr + vx + np.cross(v, vx) * k[:, None]
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)


def correct(path_in, path_out, report=True):
    """Her neck shaped in path_in written to path_out. Returns the field (her moved bind points' old and new places,
    P0 and P1, and the welded skin's bind and bind move for follow_piece), or None when the glb has had it."""
    if os.path.abspath(path_in) != os.path.abspath(path_out):
        shutil.copyfile(path_in, path_out)
    G = _Gl(path_out)
    if G.g.get("asset", {}).get("extras", {}).get(MARK):
        print("NECK_SHAPE: %s has had it" % path_out)
        return None
    S = _Skin(G)
    X0 = S.R
    N0 = S.vn(X0)
    nrad = _neck_radius(X0, N0)
    wn, ws = windows(X0, nrad)
    # 1. left = right
    X1 = symmetrize(S, X0, ws, report)
    th0, r0, _ = _cyl(X1)
    wf = ws * _ss((X1[:, 1] - FAIR_BOX[0][0]) / (FAIR_BOX[0][1] - FAIR_BOX[0][0])) * _ss((FAIR_BOX[2] - r0) / (FAIR_BOX[2] - FAIR_BOX[1]))
    X1 = fair(S, X1, wf, report)
    X1 = symmetrize(S, X1, ws, report, passes=3, smooth=SYM_SMOOTH_LAST)
    # 2 + 3. taper and form, on the mirror-alike skin
    N1 = S.vn(X1)
    Ns = N1.copy()
    for _ in range(NSMOOTH):
        Ns = S.Wn @ Ns
    Ns /= np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
    M1 = _mesh(X1, S.F)
    sc = form_field(X1, Ns, M1)
    D = taper_field(X1) + sc[:, None] * Ns
    X2 = X1 + D * wn[:, None]
    Dr = X2 - X0
    # (rest move to bind move through each point's skinning)
    Db = np.linalg.solve(S.A, Dr[:, :, None])[:, :, 0]
    mv = np.linalg.norm(Db, axis=1)
    moved = mv > 1e-7
    B1 = S.B + Db
    nb0, nb1 = S.vn(S.B), S.vn(B1)
    turn = np.degrees(np.arccos(np.clip((nb0 * nb1).sum(1), -1, 1)))
    # (no face turned past 60 degrees by the move: a fold)
    fq0 = np.cross(S.B[S.F[:, 1]] - S.B[S.F[:, 0]], S.B[S.F[:, 2]] - S.B[S.F[:, 0]])
    fq1 = np.cross(B1[S.F[:, 1]] - B1[S.F[:, 0]], B1[S.F[:, 2]] - B1[S.F[:, 0]])
    fturn = np.degrees(np.arccos(np.clip((fq0 * fq1).sum(1) / np.maximum(np.linalg.norm(fq0, axis=1) * np.linalg.norm(fq1, axis=1), 1e-30), -1, 1)))
    P0s, P1s = [], []
    for k, p in enumerate(S.prims):
        ix = S.wid[S.off[k]:S.off[k + 1]]
        if not moved[ix].any():
            continue
        a = p["attributes"]
        P = G.get(a["POSITION"]).astype(float)
        Pn = (P + Db[ix]).astype(np.float32)
        G.put(a["POSITION"], Pn)
        acc = G.g["accessors"][a["POSITION"]]
        acc["min"], acc["max"] = Pn.min(0).tolist(), Pn.max(0).tolist()
        if "NORMAL" in a:
            Nr = G.get(a["NORMAL"]).astype(float)
            m = moved[ix]
            Nr[m] = _rot_normals(Nr[m], nb0[ix][m], nb1[ix][m])
            G.put(a["NORMAL"], Nr.astype(np.float32))
        P0s.append(P[moved[ix]].astype(np.float32))
        P1s.append(Pn[moved[ix]])
    G.save()
    _rewrite_json(path_out, G.g)
    hy = S.R[:, 1]
    above = (hy > GONION_Y)
    _mark(path_out, MARK, {"xm": XM, "taper_mm": TAPER * 1000, "nape_mm": NAPE * 1000, "round": 2, "gonion_y": GONION_Y, "share_neck": SHARE_NECK,
                           "max_mm": round(float(mv.max()) * 1000, 3)})
    if report:
        print("NECK_SHAPE: %d welded points moved, largest %.2f mm (rest %.2f), mean %.2f; above her gonion line "
              "(rest y > %.3f) %.4f mm; normals turned on %d (max %.1f deg); largest face turn %.1f deg"
              % (int(moved.sum()), mv.max() * 1000, np.linalg.norm(Dr, axis=1).max() * 1000,
                 mv[moved].mean() * 1000, GONION_Y, np.linalg.norm(Dr[above], axis=1).max(initial=0) * 1000,
                 int((turn > 0.01).sum()), turn.max(), fturn.max()))
    return dict(P0=np.concatenate(P0s) if P0s else np.zeros((0, 3), np.float32),
                P1=np.concatenate(P1s) if P1s else np.zeros((0, 3), np.float32), SB=S.B, SD=Db)


def _rewrite_json(path, g):
    """The glb's json chunk replaced by g (accessor bounds), its binary kept."""
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    out = d[:12] + struct.pack("<I", len(js)) + d[16:20] + js + d[20 + jl:]
    open(path, "wb").write(out[:8] + struct.pack("<I", len(out)) + out[12:])


def _key(P):
    return np.round(P.astype(np.float32).astype(np.float64) * 1e5).astype(np.int64)


def remap_records(path, field):
    """A tuck or cover record file (u32 count; i32 x, y, z of her bind point x 1e5; f32 value) re-keyed for her
    moved points. Returns the number re-keyed."""
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[:4])[0]
    rec = np.frombuffer(b, np.dtype([("k", "<i4", 3), ("v", "<f4")]), n, 4).copy()
    k0, k1 = _key(field["P0"]), _key(field["P1"])
    lut = {tuple(a): tuple(c) for a, c in zip(k0, k1) if tuple(a) != tuple(c)}
    hit = 0
    for i in range(n):
        c = lut.get(tuple(int(v) for v in rec["k"][i]))
        if c is not None:
            rec["k"][i] = c
            hit += 1
    if hit:
        open(path, "wb").write(b[:4] + rec.tobytes() + b[4 + 16 * n:])
    return hit


def follow_piece(path, field, dry=False):
    """A piece or hair file's points near her moved skin carried by the move of the skin under them (bind space: the
    nearest skin points' moves, in full within FOLLOW[0], none past FOLLOW[1]). Returns the largest move (m)."""
    SB, SD = field["SB"], field["SD"]
    live = np.linalg.norm(SD, axis=1) > 1e-7
    if not live.any():
        return 0.0
    lo, hi = SB[live].min(0) - FOLLOW[1], SB[live].max(0) + FOLLOW[1]
    near = ((SB > lo) & (SB < hi)).all(1)
    T = cKDTree(SB[near])
    Dn = SD[near]
    G = _Gl(path)
    big = 0.0
    done = set()
    for m in G.g["meshes"]:
        for p in m["primitives"]:
            ai = p["attributes"]["POSITION"]
            if ai in done:
                continue
            done.add(ai)
            P = G.get(ai).astype(float)
            inb = ((P > lo) & (P < hi)).all(1)
            if not inb.any():
                continue
            d, j = T.query(P[inb], k=8)
            w = np.exp(-((d - d[:, :1]) / 0.004) ** 2)
            mv = (Dn[j] * w[:, :, None]).sum(1) / w.sum(1)[:, None]
            mv *= _ss((FOLLOW[1] - d[:, 0]) / (FOLLOW[1] - FOLLOW[0]))[:, None]
            if np.abs(mv).max() < 1e-7:
                continue
            P1 = P.copy()
            P1[inb] += mv
            P1 = P1.astype(np.float32)
            G.put(ai, P1)
            a = G.g["accessors"][ai]
            a["min"], a["max"] = P1.min(0).tolist(), P1.max(0).tolist()
            big = max(big, float(np.linalg.norm(mv, axis=1).max()))
    if big > 0 and not dry:
        G.save()
    return big


def run_art(art, follow=True, dry=False):
    hp = os.path.join(art, "heroine.glb")
    fld = correct(hp, hp if not dry else hp + ".dry.glb")
    if fld is None:
        return
    root = os.path.dirname(os.path.abspath(art).rstrip("/\\"))
    ad = os.path.join(root, "armor")
    for base in (art, ad):
        for sub in ("armor_tuck", "armor_cover"):
            dd = os.path.join(base, sub)
            for fn in sorted(os.listdir(dd)) if os.path.isdir(dd) else []:
                if fn.endswith(".bin") and not dry:
                    h = remap_records(os.path.join(dd, fn), fld)
                    if h:
                        print("NECK_SHAPE: %s/%s re-keyed %d" % (os.path.basename(base), sub + "/" + fn, h))
    if not follow:
        return
    files = [os.path.join(art, f) for f in sorted(os.listdir(art))
             if f.endswith(".gltf") and (f.startswith("heroine_outfit_") or f.startswith("heroine_hair_")) and not f.endswith("_lod.gltf")]
    files += [os.path.join(ad, f) for f in sorted(os.listdir(ad)) if f.endswith(".gltf")] if os.path.isdir(ad) else []
    for fp in files:
        big = follow_piece(fp, fld, dry)
        if big > 0:
            print("NECK_SHAPE: %s followed, largest %.2f mm" % (os.path.relpath(fp, root), big * 1000))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--art":
        run_art(a[1], follow="--no-follow" not in a, dry="--dry" in a)
    else:
        correct(a[0], a[1])
