"""Her ears set closer to her head, the ear's front join with her cheek rounded, and the pink band at that join taken
out of her paints (face 41, 26 October 2026: the owner, on the pixie's ear at the Look turned 40, "feel like lobe
might stick too far away from head and this part here looks off", his crop the tragus and the notch where the ear
meets the cheek).

What it fixes (face 41's measure, her bind pose, each side alike):
  * stand-off: each ear's outer surface stood 20 mm off her skull (a thin-plate fit of the skin round the ear, 3.9-6.5
    cm from its middle) at the lobe and the lower third, 17-19 at the middle, 14 above it and 10 at the top: the lobe a
    solid wedge flaring out from her cheek, and the ear wide from the front. Each ear point now goes in toward the skull
    (along the fitted skull's normal) by (1 - K(t)) of its own stand-off, t its height up the ear (0 the lobe's foot, 1
    the helix top): what lies on the skull stays, the rim moves most, so the root keeps its line and nothing kinks; the
    move eased out by the ear's reach (EAR_R) and smoothed in space (SIGMA) so the rim's front and back move alike.
  * the join: the ear's lower front (the tragus, the notch under it, the pretragal skin) a few rings of Taubin
    smoothing (no shrink), weighted over that zone (JOIN_T, JOIN_Z), so the crease where the dense ear meets her
    coarser cheek and the tragus's faceted front edge round off.
  * the pink band (paint, proven: flat paint took it out, the ear's own shade (ear_amount 0) and stored normals
    (--geom-normals) did not): her ear's paint was styled to her cheek as it renders, her paint times her face's tone
    (heroine_ears.py, heroine_ear_chroma.py), but the face's tone is laid by the features' blue, which fades out over
    the tragus and the lobe's front (0.98 in front of the ear, 0.4 at the join, 0.2 on the tragus): there the ear's
    already warmed paint took the face's tone again, Oklab chroma 0.108 at the Look against her cheek's 0.058 and her
    helix's 0.073. paint_join lays, where that blue is between 0 and 1 near her ears, the paint that renders as the
    blend of the two sides, ((1 - b) ear + b face tone x cheek) / (1 + (face tone - 1) b), from each side's own paint
    smoothed in 3D (normalized convolution over her surface, so no UV seam shows), the texel's own lightness and fine
    detail kept. In play (her face's tone ~1) the same paint runs monotonically from cheek to ear, as the ear's paint
    is about the cheek's times the face tone. Every face's paint, with its own tone (heroine_ears.tones).
Her shape keys are deltas and keep their shapes (ears_out and the faces' keys act on the new ear). Positions and
normals only (normals turned with their surface); her head's vertex count and order kept.

Followers (heroine_neck_shape's helpers): every record keyed by her bind points re-keyed; outfit, hair and armor
points near the moved skin carried by its move (FOLLOW).

    python tools/assets/heroine_ear_shape.py --art godot/art/people [--no-follow] [--keep NAME ...] [--dry]
    python tools/assets/heroine_ear_shape.py --paint godot/art/people [face ...]   (no faces: every head paint)
    python tools/assets/heroine_ear_shape.py --shade godot/art/people [SRC]        (no scalp shade on her ears: body post 7c)
    python tools/assets/heroine_ear_shape.py --follow-only godot/art/people BEFORE_GLB FILE ...   (a late-built piece)
    python tools/assets/heroine_ear_shape.py --measure GLB                       (the numbers, nothing written)
Run after heroine_arm_shape (heroine_body_post.py); --paint after the brow strokes (step 7). Done-marks: the glb's
heroine_ear_shape, each paint's JPEG comment ear_join. Then heroine_ear_ao.py again (the ear's shade from its new
shape), the LODs, and a reimport.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_neck_shape as ns  # noqa: E402
from heroine_neck import _Gl, _mark  # noqa: E402

MARK = "heroine_ear_shape"
PAINT_MARK = "ear_join"
EAR_Y = (0.02, 0.14)               # m over her Head joint: where her ears are looked for
EAR_TOP = 0.008                    # m: the ear's middle from her points this close to the side's widest
RING = (0.039, 0.065)              # m from the ear's middle (side on): the skin the skull is fitted to
EAR_R = (0.040, 0.047)             # m: the ear's reach (moved in full within the first, none past the second)
H_GATE = (0.0005, 0.003)           # m of stand-off: none moved under the first, whole from the second
# K(t): the share of its stand-off each point keeps, by its height up the ear (t 0 the lobe's foot, 1 the helix top)
K_T = (0.00, 0.20, 0.42, 0.62, 0.85, 1.00)
K_V = (0.58, 0.60, 0.78, 0.80, 0.78, 0.80)
SIGMA = 0.0015                     # m, the move's smoothing in space (Gaussian)
JOIN_T = ((0.05, 0.15), (0.55, 0.68))   # the join's window up the ear (t)
JOIN_Z = (0.012, 0.007, 0.006, 0.010)   # m: behind the ear's front (none past the first, whole from the second), and in
#                                         front of it onto her cheek (whole to the third, none past the fourth)
JOIN_ITERS, JOIN_LAM, JOIN_MU = 6, 0.45, -0.47
FOLLOW = (0.004, 0.012)


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _head_y(G):
    names = G.names()
    ibm = G.get(G.g["skins"][0]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    return float(np.linalg.inv(ibm[names.index("Head")])[1, 3])


def ear_frame(X, sx, head_y):
    """One side's ear: its middle (y, z) side on, the skull fit (a callable on (n, 2) y, z -> |x|), each point's
    stand-off h and distance r from the middle, its height t up the ear, and the ear's front z."""
    from scipy.interpolate import RBFInterpolator
    ax = np.abs(X[:, 0])
    side = (np.sign(X[:, 0]) == sx) & (X[:, 1] > head_y + EAR_Y[0]) & (X[:, 1] < head_y + EAR_Y[1])
    top = side & (ax > ax[side].max() - EAR_TOP)
    c = np.array([X[top, 1].mean(), X[top, 2].mean()])
    r = np.hypot(X[:, 1] - c[0], X[:, 2] - c[1])
    side = np.sign(X[:, 0]) == sx
    ring = side & (r > RING[0]) & (r < RING[1]) & (ax > 0.035)
    sk = RBFInterpolator(X[ring][:, 1:3], ax[ring], kernel="thin_plate_spline", smoothing=1e-4, degree=1)
    near = side & (r < EAR_R[1] + 0.004) & (ax > 0.03)
    h = np.zeros(len(X))
    h[near] = ax[near] - sk(X[near][:, 1:3])
    ear = near & (h > 0.003) & (r < EAR_R[0])
    y0, y1 = X[ear, 1].min(), X[ear, 1].max()
    t = (X[:, 1] - y0) / (y1 - y0)
    zf = X[ear, 2].max()
    return dict(c=c, sk=sk, h=h, r=r, t=t, near=near, ear=ear, zf=zf, y=(y0, y1), side=side)


def _normal(sk, YZ, sx, e=2e-4):
    """The fitted skull's outward normal at (y, z)."""
    dy = (sk(YZ + [e, 0]) - sk(YZ - [e, 0])) / (2 * e)
    dz = (sk(YZ + [0, e]) - sk(YZ - [0, e])) / (2 * e)
    n = np.c_[np.full(len(YZ), float(sx)), -dy, -dz]
    return n / np.linalg.norm(n, axis=1, keepdims=True)


def _vol_smooth(X, D, sigma):
    """D smoothed over points close in space (normalized by every point's neighbours, moved or not)."""
    from scipy.spatial import cKDTree
    import scipy.sparse as sp
    src = np.where(np.linalg.norm(D, axis=1) > 1e-8)[0]
    if not len(src):
        return D
    lo, hi = X[src].min(0) - 3 * sigma, X[src].max(0) + 3 * sigma
    act = np.where(((X > lo) & (X < hi)).all(1))[0]
    Ta = cKDTree(X[act])
    M = Ta.sparse_distance_matrix(cKDTree(X[src]), 3 * sigma, output_type="coo_matrix")
    Wg = sp.coo_matrix((np.exp(-0.5 * (M.data / sigma) ** 2), (M.row, M.col)), shape=(len(act), len(src))).tocsr()
    Ma = Ta.sparse_distance_matrix(Ta, 3 * sigma, output_type="coo_matrix")
    den = np.bincount(Ma.row, weights=np.exp(-0.5 * (Ma.data / sigma) ** 2), minlength=len(act))
    out = np.zeros_like(D)
    out[act] = (Wg @ D[src]) / np.maximum(den, 1e-12)[:, None]
    return out


def field(S, head_y, report=True):
    """The bind move of each welded point (n, 3): the setback, then the join's smoothing on top."""
    X = S.B
    D = np.zeros_like(X)
    Wj = np.zeros(len(X))
    for sx in (-1, 1):
        f = ear_frame(X, sx, head_y)
        k = np.interp(f["t"], K_T, K_V)
        m = (1 - k) * f["h"] * _ss((f["h"] - H_GATE[0]) / (H_GATE[1] - H_GATE[0]))
        m *= _ss((EAR_R[1] - f["r"]) / (EAR_R[1] - EAR_R[0])) * f["near"]
        ix = np.where(m > 1e-7)[0]
        D[ix] -= m[ix, None] * _normal(f["sk"], X[ix][:, 1:3], sx)
        # (the join: the ear's lower front and the cheek just in front of it)
        (a0, a1), (b0, b1) = JOIN_T
        wt = _ss((f["t"] - a0) / (a1 - a0)) * _ss((b1 - f["t"]) / (b1 - b0))
        dz = X[:, 2] - f["zf"]
        wz = _ss((dz + JOIN_Z[0]) / (JOIN_Z[0] - JOIN_Z[1])) * _ss((JOIN_Z[3] - dz) / (JOIN_Z[3] - JOIN_Z[2]))
        wj = wt * wz * f["side"] * _ss((EAR_R[1] - f["r"]) / (EAR_R[1] - EAR_R[0])) * (f["h"] > -0.003)
        Wj = np.maximum(Wj, wj)
        if report:
            rim = f["ear"]
            for nm, (t0, t1) in (("lobe", (0.0, 0.25)), ("lower", (0.25, 0.45)), ("middle", (0.45, 0.7)), ("upper", (0.7, 0.88)), ("top", (0.88, 1.01))):
                q = rim & (f["t"] >= t0) & (f["t"] < t1)
                if q.any():
                    i = np.where(q)[0][np.argmax(f["h"][q])]
                    print("EAR_SHAPE: side %+d %-6s stand-off %.1f mm -> %.1f" % (sx, nm, f["h"][i] * 1000, (f["h"][i] - m[i]) * 1000))
    D = _vol_smooth(X, D, SIGMA)
    # (the join: Taubin smoothing of the moved shape, weighted by the zone)
    if Wj.max() > 0:
        X1 = X + D
        for _ in range(JOIN_ITERS):
            for lam in (JOIN_LAM, JOIN_MU):
                X1 = X1 + (lam * Wj)[:, None] * (S.Wn @ X1 - X1)
        D = X1 - X
    return D


def correct(path_in, path_out, report=True):
    """Her ears set in and their front joins rounded in path_in, written to path_out. Returns the field dict for the
    followers (P0/P1 per moved vertex, SB/SD the welded bind and bind move), or None when the glb has had it."""
    import shutil
    if os.path.abspath(path_in) != os.path.abspath(path_out):
        shutil.copyfile(path_in, path_out)
    G = _Gl(path_out)
    if G.g.get("asset", {}).get("extras", {}).get(MARK):
        print("EAR_SHAPE: %s has had it" % path_out)
        return None
    S = ns._Skin(G)
    Db = field(S, _head_y(G), report)
    mv = np.linalg.norm(Db, axis=1)
    moved = mv > 1e-7
    B1 = S.B + Db
    nb0, nb1 = S.vn(S.B), S.vn(B1)
    fq0 = np.cross(S.B[S.F[:, 1]] - S.B[S.F[:, 0]], S.B[S.F[:, 2]] - S.B[S.F[:, 0]])
    fq1 = np.cross(B1[S.F[:, 1]] - B1[S.F[:, 0]], B1[S.F[:, 2]] - B1[S.F[:, 0]])
    fturn = np.degrees(np.arccos(np.clip((fq0 * fq1).sum(1) / np.maximum(
        np.linalg.norm(fq0, axis=1) * np.linalg.norm(fq1, axis=1), 1e-30), -1, 1)))
    flips = int(((fq0 * fq1).sum(1) < 0).sum())
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
            Nr[m] = ns._rot_normals(Nr[m], nb0[ix][m], nb1[ix][m])
            G.put(a["NORMAL"], Nr.astype(np.float32))
        P0s.append(P[moved[ix]].astype(np.float32))
        P1s.append(Pn[moved[ix]])
    G.save()
    ns._rewrite_json(path_out, G.g)
    _mark(path_out, MARK, {"k": list(K_V), "join_iters": JOIN_ITERS, "max_mm": round(float(mv.max()) * 1000, 3)})
    if report:
        print("EAR_SHAPE: %d welded points moved, largest %.2f mm, mean %.2f; largest face turn %.1f deg, %d flipped"
              % (int(moved.sum()), mv.max() * 1000, mv[moved].mean() * 1000, fturn.max(), flips))
    return dict(P0=np.concatenate(P0s) if P0s else np.zeros((0, 3), np.float32),
                P1=np.concatenate(P1s) if P1s else np.zeros((0, 3), np.float32), SB=S.B, SD=Db)


def run_art(art, follow=True, dry=False, keep=()):
    hp = os.path.join(art, "heroine.glb")
    fld = correct(hp, hp if not dry else hp + ".dry.glb")
    if fld is None or dry:
        return
    root = os.path.dirname(os.path.abspath(art).rstrip("/\\"))
    ad = os.path.join(root, "armor")
    for base in (art, ad):
        for sub in ("armor_tuck", "armor_cover"):
            dd = os.path.join(base, sub)
            for fn in sorted(os.listdir(dd)) if os.path.isdir(dd) else []:
                if fn.endswith(".bin"):
                    h = ns.remap_records(os.path.join(dd, fn), fld)
                    if h:
                        print("EAR_SHAPE: %s/%s re-keyed %d" % (os.path.basename(base), sub + "/" + fn, h))
    if not follow:
        return
    files = [os.path.join(art, f) for f in sorted(os.listdir(art))
             if f.endswith(".gltf") and (f.startswith("heroine_outfit_") or f.startswith("heroine_hair_")) and not f.endswith("_lod.gltf")]
    files += [os.path.join(ad, f) for f in sorted(os.listdir(ad)) if f.endswith(".gltf")] if os.path.isdir(ad) else []
    old = ns.FOLLOW
    ns.FOLLOW = FOLLOW
    try:
        for fp in files:
            if any(k in os.path.basename(fp) for k in keep):
                print("EAR_SHAPE: %s kept (--keep): run its follow when it is built" % os.path.basename(fp))
                continue
            big = ns.follow_piece(fp, fld)
            if big > 0:
                print("EAR_SHAPE: %s followed, largest %.2f mm" % (os.path.relpath(fp, root), big * 1000))
    finally:
        ns.FOLLOW = old


# ---- the paint: the band at the ear's join taken out ----

PAINT_R = (0.040, 0.050)           # m from each ear's middle (3D): laid in full within the first, none past the second
EAR_NEAR = (0.004, 0.010)          # m from the ear's own points (stand-off over 3 mm): the same
B_EDGE = (0.004, 0.03)             # the features' blue: none laid under the first or over 1 - it, whole past the second
LP_SIGMA = (0.003, 0.009)          # m: each side's paint smoothed in 3D (the near and the wide pass, for reach)
TRIM = 0.22                        # the join's chroma eased down at its middle (see paint_join)
DETAIL_SIGMA = 0.0008             # m: finer than this, a texel's own colour over its neighbours' is kept
VOX = 0.0005                       # m, the smoothing's grid


def _lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def _raster(UV, T, V, size):
    """The covered texels (iy, ix) of triangles T and V (per point, (n, k)) at each, barycentric."""
    ys, xs, vs = [], [], []
    U = UV * size
    for t in T:
        q = U[t]
        x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        pq = np.stack([gx.ravel() + 0.5, gy.ravel() + 0.5], 1)
        a, b, c = q
        v0, v1, v2 = b - a, c - a, pq - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-14:
            continue
        vv = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        ww = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        bb = np.stack([1 - vv - ww, vv, ww], 1)
        m = (bb > -1e-4).all(1)
        if not m.any():
            continue
        ys.append(gy.ravel()[m])
        xs.append(gx.ravel()[m])
        vs.append(bb[m] @ V[t])
    iy, ix, v = np.concatenate(ys), np.concatenate(xs), np.concatenate(vs)
    key = iy * size + ix
    _, first = np.unique(key, return_index=True)
    return iy[first], ix[first], v[first]


def _lowpass(X, V, w, sigma, lo, shape):
    """Normalized convolution of V (weights w) over points X on a 3D grid: (smoothed V, its weight) at each point."""
    from scipy import ndimage
    g = np.floor((X - lo) / VOX).astype(int)
    g = np.clip(g, 0, np.array(shape) - 1)
    out = []
    acc = np.zeros(shape, np.float32)
    np.add.at(acc, tuple(g.T), w)
    acc = ndimage.gaussian_filter(acc, sigma / VOX, mode="constant")
    den = ndimage.map_coordinates(acc, ((X - lo) / VOX - 0.5).T, order=1)
    for c in range(V.shape[1]):
        acc[:] = 0
        np.add.at(acc, tuple(g.T), w * V[:, c])
        acc = ndimage.gaussian_filter(acc, sigma / VOX, mode="constant")
        out.append(ndimage.map_coordinates(acc, ((X - lo) / VOX - 0.5).T, order=1))
    return np.stack(out, 1) / np.maximum(den, 1e-12)[:, None], den


def _head(glb):
    G = _Gl(glb)
    g = G.g
    hh = [n for n in g["nodes"] if n.get("name") == "HeroineHead"][0]
    p = [q for q in g["meshes"][hh["mesh"]]["primitives"] if g["materials"][q["material"]].get("name") == "skin_head"][0]
    a = p["attributes"]
    return (G.get(a["POSITION"]).astype(float), G.get(a["TEXCOORD_0"]).astype(float),
            G.get(p["indices"]).reshape(-1, 3).astype(int), _head_y(G))


def paint_join(art, faces=None, report=True):
    from PIL import Image
    import heroine_ears as he
    import heroine_brow_strokes as bs
    tex = os.path.join(art, "head_tex")
    tones = he.tones()
    P, UV, F, head_y = _head(os.path.join(art, "heroine.glb"))
    fe = np.asarray(Image.open(os.path.join(tex, "heroine_features.png")).convert("RGB"), np.float32)[:, :, 2] / 255
    paints = {}
    for fn in sorted(os.listdir(tex)):
        if fn == "heroine_head.jpg":
            paints["own"] = fn
        elif fn.startswith("heroine_head_") and fn.endswith(".jpg"):
            paints[fn[len("heroine_head_"):-4]] = fn
    todo = [f for f in (faces or sorted(paints)) if f in paints and f in tones]
    sides = []
    for sx in (-1, 1):
        f = ear_frame(P, sx, head_y)
        cen = np.array([sx * float(np.abs(P[f["ear"], 0]).mean()), f["c"][0], f["c"][1]])
        d3 = np.linalg.norm(P - cen, axis=1)
        T = F[(d3[F] < PAINT_R[1] + 0.006).all(1)]
        from scipy.spatial import cKDTree
        sides.append((cen, T, cKDTree(P[f["ear"]])))
    for face in todo:
        path = os.path.join(tex, paints[face])
        if PAINT_MARK in bs.comment(path):
            print("EAR_JOIN: %s has had it" % paints[face])
            continue
        img = Image.open(path).convert("RGB")
        size = img.size[0]
        A = np.asarray(img, np.float32) / 255
        out = A.copy()
        FT = np.asarray(tones[face], np.float64)
        for cen, T, ear_t in sides:
            iy, ix, X = _raster(UV, T, P, size)
            u = (ix + 0.5) / size
            v = (iy + 0.5) / size
            from scipy import ndimage
            b = ndimage.map_coordinates(fe, [v * fe.shape[0] - 0.5, u * fe.shape[1] - 0.5], order=1, mode="nearest")
            b = np.clip(b, 0, 1)
            p = _lin(A[iy, ix].astype(np.float64))
            lo = X.min(0) - 0.02
            shape = tuple(np.ceil((X.max(0) + 0.02 - lo) / VOX).astype(int) + 1)
            we = (b < B_EDGE[0]).astype(np.float32)
            wc = (b > 1 - B_EDGE[0]).astype(np.float32)
            pe, de = _lowpass(X, p, we, LP_SIGMA[0], lo, shape)
            pc, dc = _lowpass(X, p, wc, LP_SIGMA[0], lo, shape)
            pe2, _ = _lowpass(X, p, we, LP_SIGMA[1], lo, shape)
            pc2, _ = _lowpass(X, p, wc, LP_SIGMA[1], lo, shape)
            # (the near pass where it has its side's paint close, the wide one where it has not)
            ce = _ss(de / 0.08)[:, None]
            cc = _ss(dc / 0.08)[:, None]
            pe = ce * pe + (1 - ce) * pe2
            pc = cc * pc + (1 - cc) * pc2
            tone = 1 + (FT - 1) * b[:, None]
            eff = p * tone                                           # (as it renders at the Look, before her lamps)
            blend = (1 - b)[:, None] * pe + b[:, None] * FT * pc     # (the two sides' blend by the blue)
            fine, _ = _lowpass(X, eff, np.ones(len(p), np.float32), DETAIL_SIGMA, lo, shape)
            Lt, Lb, Lf = he.oklab(eff), he.oklab(blend), he.oklab(fine)
            # (the texel's own lightness at every scale; its colour the blend's, at that lightness, with its own fine
            # colour over its smoothed colour kept)
            ab = Lb[:, 1:] * (Lt[:, :1] / np.maximum(Lb[:, :1], 1e-4)) + (Lt[:, 1:] - Lf[:, 1:])
            # (and the join's colour eased down by TRIM at its middle (b 0.5): measured at the Look after the blend alone,
            # the join still ran 1.35x her cheek's chroma, the lamps' own tones also following the blue)
            ab *= (1 - TRIM * np.clip(4 * b * (1 - b), 0, 1))[:, None]
            new = np.clip(he.unoklab(np.c_[Lt[:, :1], ab]), 0, 1) / tone
            w = _ss((b - B_EDGE[0]) / (B_EDGE[1] - B_EDGE[0])) * _ss((1 - B_EDGE[0] - b) / (B_EDGE[1] - B_EDGE[0]))
            w *= _ss((PAINT_R[1] - np.linalg.norm(X - cen, axis=1)) / (PAINT_R[1] - PAINT_R[0]))
            w *= _ss((EAR_NEAR[1] - ear_t.query(X)[0]) / (EAR_NEAR[1] - EAR_NEAR[0]))    # (her ear, not her jaw's blend)
            res = p + w[:, None] * (new - p)
            out[iy, ix] = _srgb(res).astype(np.float32)
            if report:
                q = w > 0.5
                print("EAR_JOIN: %s side %+d: %d texels laid (%d over half), largest change %.3f (linear)" % (
                    face, int(np.sign(cen[0])), int((w > 0.01).sum()), int(q.sum()), float(np.abs(res - p).max())))
        Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)).save(
            path, quality=95, subsampling=0, comment=(bs.comment(path) + " " + PAINT_MARK).strip().encode("latin-1"))


# ---- the tick: the painted crease at her ear's lower front, eased ----
TICK_MARK = "ear_tick"
TICK_T = (0.05, 0.12, 0.36, 0.44)    # the ear's height (t): none under the first, whole from the second to the third
TICK_Z = (-0.006, -0.004, 0.0045, 0.0065)  # m from the ear's front (z): the same (the crease runs 2-3 mm before it)
TICK_SIGMA = 0.0015                  # m: the low-pass a texel is held against
TICK_L = (0.015, 0.05)               # its darkness (OKLab L) under the low-pass: eased from the first, in full from the second
TICK_A = (0.0, 0.006)                # and its redness (OKLab a) over it: the same (pores and freckles, browner, keep theirs)
TICK_CUT = 0.5                       # of its excess (redness, darkness, yellow) taken off


def _band(x, e):
    return _ss((x - e[0]) / (e[1] - e[0])) * _ss((e[3] - x) / (e[3] - e[2]))


def tick_off(art, faces=None, report=True):
    """The AI paint's crease line where her tragus meets her cheek, a dark red tick at the Look turned 40 on fair
    skin (face 41's j5): each texel there darker and redder than its 1.5 mm neighbourhood loses TICK_CUT of its
    excess darkness and colour. Pores and freckles (browner, not redder) keep theirs. Done-mark: each paint's JPEG comment ear_tick."""
    from PIL import Image
    import heroine_ears as he
    import heroine_brow_strokes as bs
    tex = os.path.join(art, "head_tex")
    P, UV, F, head_y = _head(os.path.join(art, "heroine.glb"))
    paints = [fn for fn in sorted(os.listdir(tex)) if fn.startswith("heroine_head") and fn.endswith(".jpg")]
    if faces:
        paints = [fn for fn in paints if fn[len("heroine_head"):-4].lstrip("_") in faces or (fn == "heroine_head.jpg" and "own" in faces)]
    sides = []
    for sx in (-1, 1):
        f = ear_frame(P, sx, head_y)
        y0, y1 = f["y"]
        t = (P[:, 1] - y0) / (y1 - y0)
        dz = P[:, 2] - f["zf"]
        sel = (np.sign(P[:, 0]) == sx) & (t > TICK_T[0] - 0.15) & (t < TICK_T[3] + 0.15) & (dz > TICK_Z[0] - 0.008) & (dz < TICK_Z[3] + 0.008)
        sides.append((sx, f, F[sel[F].all(1)]))
    for fn in paints:
        path = os.path.join(tex, fn)
        if TICK_MARK in bs.comment(path):
            print("EAR_TICK: %s has had it" % fn)
            continue
        img = Image.open(path).convert("RGB")
        size = img.size[0]
        A = np.asarray(img, np.float32) / 255
        out = A.copy()
        for sx, f, T in sides:
            iy, ix, X = _raster(UV, T, P, size)
            lab = he.oklab(_lin(A[iy, ix].astype(np.float64)))
            lo = X.min(0) - 0.01
            shape = tuple(np.ceil((X.max(0) + 0.01 - lo) / VOX).astype(int) + 1)
            lp, _ = _lowpass(X, lab, np.ones(len(X), np.float32), TICK_SIGMA, lo, shape)
            y0, y1 = f["y"]
            w = _band((X[:, 1] - y0) / (y1 - y0), TICK_T) * _band(X[:, 2] - f["zf"], TICK_Z)
            w *= _ss((lp[:, 0] - lab[:, 0] - TICK_L[0]) / (TICK_L[1] - TICK_L[0]))
            w *= _ss((lab[:, 1] - lp[:, 1] - TICK_A[0]) / (TICK_A[1] - TICK_A[0])) * TICK_CUT
            new = lab - w[:, None] * (lab - lp)
            res = np.clip(he.unoklab(new), 0, 1)
            out[iy, ix] = _srgb(res).astype(np.float32)
            if report:
                print("EAR_TICK: %s side %+d: %d texels eased (%d over 0.25), largest L lift %.3f" % (
                    fn, sx, int((w > 0.01).sum()), int((w > 0.25).sum()), float((w * (lp[:, 0] - lab[:, 0])).max())))
        Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)).save(
            path, quality=95, subsampling=0, comment=(bs.comment(path) + " " + TICK_MARK).strip().encode("latin-1"))


# ---- the ear's front: no paler than her cheek as it renders ----
FRONT_MARK = "ear_front"
FRONT_T = (0.20, 0.32, 0.92, 1.02)   # the ear's height (t): its front from the tragus to the helix's top
FRONT_Z = (0.007, 0.004)             # m behind the ear's front (z): in full within the second, none past the first
FRONT_EAR = (0.0007, 0.002)          # m from her ear's own points: in full within the first, none past the second
FRONT_GAP = 0.05                     # OKLab L the ear's front gains over her cheek on its way to the screen (her face's
                                     # tone on the cheek, none on the ear: +0.04; its front facing the key: +0.047), less
                                     # the 0.035 a lit rim may keep (measured face 42, braid copper at the Look turned 40)
FRONT_MAX = 0.06                     # the most L taken off
FRONT_C = 0.35                       # its chroma raised by this share at the full cut (it rendered 0.83x the cheek's)
FRONT_SOFT = 0.001                   # m: the mask's 3D low-pass (its edge eased over her ear's mesh, ~2-3 mm a ring)


def front_tone(art, faces=None, report=True):
    """Her ear's front (the helix root, the crus, down to the tragus) rendered a pale, grey strip beside her cheek at
    the Look turned 40 (face 42's j1: "a pale near-white band ... on the join the owner flagged"): the cheek takes her
    face's tone and the ear does not, and the front faces the key. Each paint's ear front is laid darker by its own
    gap to its cheek (the paint's L there over the cheek's, + FRONT_GAP, up to FRONT_MAX) and a little richer; a face
    whose ear already paints darker (Sunborn) is left. Done-mark: each paint's JPEG comment ear_front."""
    from PIL import Image
    from scipy.spatial import cKDTree
    import heroine_ears as he
    import heroine_brow_strokes as bs
    tex = os.path.join(art, "head_tex")
    P, UV, F, head_y = _head(os.path.join(art, "heroine.glb"))
    paints = [fn for fn in sorted(os.listdir(tex)) if fn.startswith("heroine_head") and fn.endswith(".jpg")]
    if faces:
        paints = [fn for fn in paints if fn[len("heroine_head"):-4].lstrip("_") in faces or (fn == "heroine_head.jpg" and "own" in faces)]
    sides = []
    for sx in (-1, 1):
        f = ear_frame(P, sx, head_y)
        y0, y1 = f["y"]
        t = (P[:, 1] - y0) / (y1 - y0)
        dz = P[:, 2] - f["zf"]
        sel = (np.sign(P[:, 0]) == sx) & (t > 0.1) & (t < 1.1) & (dz > -0.015) & (dz < 0.02)
        # (each point's distance to her ear's points, laid on the texels barycentric: face 43 found the texel's own
        # distance to those points, spaced 2-3 mm, made the mask a comb, a darkened tooth round each point and the
        # paint between left pale, the "ladder" of 3-4 pale bars at the Look turned 40)
        sides.append((sx, f, F[sel[F].all(1)], cKDTree(P[f["ear"]]).query(P)[0]))
    for fn in paints:
        path = os.path.join(tex, fn)
        if FRONT_MARK in bs.comment(path):
            print("EAR_FRONT: %s has had it" % fn)
            continue
        img = Image.open(path).convert("RGB")
        size = img.size[0]
        A = np.asarray(img, np.float32) / 255
        out = A.copy()
        for sx, f, T, dv in sides:
            iy, ix, XD = _raster(UV, T, np.c_[P, dv], size)
            X, de = XD[:, :3], XD[:, 3]
            lab = he.oklab(_lin(A[iy, ix].astype(np.float64)))
            y0, y1 = f["y"]
            t = (X[:, 1] - y0) / (y1 - y0)
            dz = X[:, 2] - f["zf"]
            ear = (de < 0.0007) & (dz > -0.007) & (t > 0.3) & (t < 0.9)
            cheek = (de > 0.004) & (dz > 0.004) & (dz < 0.012) & (t > 0.3) & (t < 0.9)
            cut = float(np.clip(lab[ear, 0].mean() - lab[cheek, 0].mean() + FRONT_GAP, 0, FRONT_MAX))
            w = _band(t, FRONT_T) * _ss((dz + FRONT_Z[0]) / (FRONT_Z[0] - FRONT_Z[1])) * _ss((FRONT_EAR[1] - de) / (FRONT_EAR[1] - FRONT_EAR[0]))
            lo = X.min(0) - 0.01
            w = _lowpass(X, w[:, None], np.ones(len(X), np.float32), FRONT_SOFT, lo,
                         tuple(np.ceil((X.max(0) + 0.01 - lo) / VOX).astype(int) + 1))[0][:, 0]
            new = lab.copy()
            new[:, 0] -= w * cut
            new[:, 1:] *= (1 + FRONT_C * w * cut / FRONT_MAX)[:, None]
            out[iy, ix] = _srgb(np.clip(he.unoklab(new), 0, 1)).astype(np.float32)
            if os.environ.get("FRONT_DBG"):                  # (the mask itself, green, to see its shape in a shot)
                out[iy, ix, 1] = np.maximum(out[iy, ix, 1], w.astype(np.float32))
            if report:
                print("EAR_FRONT: %s side %+d: ear front L %.3f, cheek %.3f: cut %.3f over %d texels" % (
                    fn, sx, lab[ear, 0].mean(), lab[cheek, 0].mean(), cut, int((w > 0.5).sum())))
        Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)).save(
            path, quality=95, subsampling=0, comment=(bs.comment(path) + " " + FRONT_MARK).strip().encode("latin-1"))


# ---- the scalp shade: none on her ear ----

SHADE_MARK = "ear_shade"
SHADE_H = 0.002                    # m of stand-off: her ear (the skull fit's), within EAR_R[0] of its middle
SHADE_FADE = (0.0005, 0.003)       # m from that ear (3D): no shade within the first, the shade as it was past the second
SHADE_GUTTER = 4                   # texels: uncovered texels this near a changed one take its share (mipmaps)
SHADE_FLOOR = 0.35                 # of the shade kept on her scalp's skin round the ear (stand-off under SHADE_FLOOR_H)
SHADE_FLOOR_H = (0.0008, 0.0016)   # m: the floor in full under the first, none (her ear's root) past the second


def shade_off(art, src=None, report=True):
    """heroine_shadow.png's green (her scalp's shade, multiplied by her hair's colour in the game) taken off her whole
    ear, front, tragus and helix with it, faded back in over SHADE_FADE into her scalp; red, blue, alpha and every texel
    past the fade kept byte for byte. (face 41, 26 Oct: heroine_features.py's ear rule leaves her ear's front to her
    face's side, "in front and below, her face's", and its blur and her ear's top-front keep the shade: at the Look
    turned 40 the ear's front third, helix top to tragus, read hair-coloured with no hair on.) Done-mark: the PNG's
    text chunk ear_shade; heroine_features.py writes a new one without it, so run this after it (body post 7c)."""
    from PIL import Image, PngImagePlugin
    from scipy import ndimage
    from scipy.spatial import cKDTree
    path = os.path.join(art, "head_tex", "heroine_shadow.png")
    im = Image.open(src or path)
    if SHADE_MARK in im.info:
        print("EAR_SHADE: %s has had it" % os.path.basename(path))
        return None
    A = np.array(im.convert("RGBA"))
    size = A.shape[0]
    P, UV, F, head_y = _head(os.path.join(art, "heroine.glb"))
    cov = np.zeros((size, size), bool)
    ci, cj, _ = _raster(UV, F, np.zeros((len(P), 1)), size)
    cov[ci, cj] = True
    M = np.ones((size, size), np.float32)
    touched = np.zeros((size, size), bool)
    for sx in (-1, 1):
        f = ear_frame(P, sx, head_y)
        core = f["near"] & (f["h"] > SHADE_H) & (f["r"] < EAR_R[0])
        d = cKDTree(P[core]).query(P)[0]
        T = F[(d[F] < SHADE_FADE[1] + 0.004).all(1)]
        iy, ix, dt = _raster(UV, T, np.c_[d, f["h"]], size)
        m = _ss((dt[:, 0] - SHADE_FADE[0]) / (SHADE_FADE[1] - SHADE_FADE[0]))
        # (face 41 pixie3: not to none on her scalp's skin just round her ear: there, under the pixie's edge drawn
        # back off the helix, the bare 3 mm band read a pale patch, a hole in the shade; kept at SHADE_FLOOR, her
        # sideburn tapering into skin as the shade itself fades to her cheek)
        m = np.maximum(m, SHADE_FLOOR * _ss((SHADE_FLOOR_H[1] - dt[:, 1]) / (SHADE_FLOOR_H[1] - SHADE_FLOOR_H[0])))
        M[iy, ix] = np.minimum(M[iy, ix], m)
        touched[iy, ix] |= m < 1
        if report:
            g = A[iy, ix, 1] / 255.0
            q = dt[:, 0] < SHADE_FADE[0]
            print("EAR_SHADE: side %+d: %d ear points, %d texels on her ear (shade mean %.3f, max %.3f, over 0.1: %d) -> 0"
                  % (sx, int(core.sum()), int(q.sum()), g[q].mean(), g[q].max(), int((g[q] > 0.1).sum())))
    # (the texels round her UV islands, unrendered but in their mipmaps, take their nearest covered texel's share)
    dist, (ny, nx) = ndimage.distance_transform_edt(~cov, return_indices=True)
    gut = ~cov & (dist <= SHADE_GUTTER) & touched[ny, nx]
    M[gut] = M[ny[gut], nx[gut]]
    g0 = A[..., 1].astype(np.float32)
    A[..., 1] = np.clip(np.floor(g0 * M + 0.5), 0, 255).astype(np.uint8)
    info = PngImagePlugin.PngInfo()
    info.add_text(SHADE_MARK, "fade %.1f-%.1f mm, h %.1f mm, floor %.2f" % (SHADE_FADE[0] * 1000, SHADE_FADE[1] * 1000, SHADE_H * 1000, SHADE_FLOOR))
    Image.fromarray(A, "RGBA").save(path, pnginfo=info)
    if report:
        print("EAR_SHADE: %s: %d texels changed (%d gutter)" % (path, int((A[..., 1] != g0).sum()), int(gut.sum())))
    return M


def follow_only(art, files, before):
    """The followers alone, for a piece built after the glb had its ear shape (the glb is marked, so --art skips): the
    move field computed again from the glb as it was before (before: that glb, e.g. from git), checked against the
    installed one, then each named file followed. Only for files built on the old ear (heroine_hair.py builds from
    the built blend, which has the old ear) and not yet followed."""
    import tempfile
    hp = os.path.join(art, "heroine.glb")
    tmp = os.path.join(tempfile.mkdtemp(prefix="ear_follow_"), "heroine.glb")
    fld = correct(before, tmp, report=False)
    if fld is None:
        raise SystemExit("EAR_SHAPE: %s is already marked; give the glb from before the ear shape" % before)
    a, b = ns._Skin(_Gl(tmp)).B, ns._Skin(_Gl(hp)).B
    err = float(np.abs(a - b).max()) if a.shape == b.shape else float("inf")
    if err > 1e-5:
        raise SystemExit("EAR_SHAPE: the field from %s does not give the installed glb (off by %.3g m)" % (before, err))
    old = ns.FOLLOW
    ns.FOLLOW = FOLLOW
    try:
        for fp in files:
            big = ns.follow_piece(fp, fld)
            print("EAR_SHAPE: %s followed, largest %.2f mm" % (os.path.basename(fp), big * 1000))
    finally:
        ns.FOLLOW = old


def measure(glb):
    G = _Gl(glb)
    S = ns._Skin(G)
    hy = _head_y(G)
    for sx in (-1, 1):
        f = ear_frame(S.B, sx, hy)
        rim = f["ear"]
        row = []
        for nm, (t0, t1) in (("lobe", (0.0, 0.25)), ("lower", (0.25, 0.45)), ("middle", (0.45, 0.7)), ("upper", (0.7, 0.88)), ("top", (0.88, 1.01))):
            q = rim & (f["t"] >= t0) & (f["t"] < t1)
            row.append("%s %.1f" % (nm, f["h"][q].max() * 1000 if q.any() else 0))
        print("EAR: side %+d stand-off (mm): %s" % (sx, ", ".join(row)))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--art":
        keep = [a[i + 1] for i, x in enumerate(a) if x == "--keep"]
        run_art(a[1], follow="--no-follow" not in a, dry="--dry" in a, keep=keep)
    elif a and a[0] == "--paint":
        paint_join(a[1], [x for x in a[2:] if not x.startswith("--")] or None)
    elif a and a[0] == "--front":
        front_tone(a[1], [x for x in a[2:] if not x.startswith("--")] or None)
    elif a and a[0] == "--tick":
        tick_off(a[1], [x for x in a[2:] if not x.startswith("--")] or None)
    elif a and a[0] == "--shade":
        # (--shade ART [SRC]: SRC, the shade as heroine_features.py wrote it (unmarked), to lay it again)
        shade_off(a[1], a[2] if len(a) > 2 else None)
    elif a and a[0] == "--follow-only":
        # (--follow-only ART BEFORE_GLB FILE ...)
        follow_only(a[1], a[3:], a[2])
    elif a and a[0] == "--measure":
        measure(a[1])
    else:
        correct(a[0], a[1])
