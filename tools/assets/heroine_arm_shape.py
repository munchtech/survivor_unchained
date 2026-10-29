"""Her upper arms sculpted slimmer and shaped (armor 15, 22 October 2026: the owner, "the upper-arm sculpt after the
bust MR (inner arm slimmer, armpit join lower, a small deltoid), with sleeves and armor following").

What it fixes (face 38's measure, bind pose = her A-pose, arms ~52 deg below horizontal): her upper arm read as a
straight, thick tube, about 15% heavy for the slim/athletic target: girth 33.5 / 32.1 / 32.5 / 31.6 cm at 10 / 25 /
40 / 50% shoulder to elbow (barely tapering), the inner (armpit) side 1.6x the outer at 25-40%, no deltoid swell (the
outer radius dipping to 3.8-4.3 cm), and a high, filled-in web between arm and torso.

The step, in bind space, one smooth field per side (each side from its own joints: left = right by construction):
  1. inner side in: each point toward the bone (radially, round the upperarm_* axis) by INNER x a window in t (the
     fraction shoulder -> elbow: none before INNER_T[0][0], whole INNER_T[0][1]..INNER_T[1][0], none past
     INNER_T[1][1]) x ((1 - cos)/2)^INNER_POW of the angle from the arm's outer side (its 'top': world up made normal
     to the bone), so mostly the armpit side and a little into front and back (the section stays round);
  2. the armpit web slimmer: the same move, WEB x its own window near the shoulder (WEB_T), so the web between arm
     and chest/back draws up and in toward the arm: the arm reads as separate from the torso lower down. Both moves
     are taken by the arm's share of each point's skinning (upperarm/lowerarm/hand of that side: ARM_W), so her
     torso (no arm weight) stays and the pec and lat folds keep their line; the web's torso side (a little arm
     weight: TORSO_W) goes WEB_TORSO in toward her midline, so the web slims from both sides;
  3. deltoid: an outward swell DELT on the outer side (DELT_POW), window DELT_T over the shoulder cap, only on the
     arm's own skin (radius under DELT_R), so the shoulder rounds without moving the joint;
  4. nothing within BREAST_KEEP[0] of her breast (her breast-weighted skin), easing in to whole by BREAST_KEEP[1];
     the field smoothed SMOOTH rings over her welded skin (no steps), the breast mask after.
Her body, graft and head move as one (each welded point once: the seam cannot open). Positions and normals only
(normals turned by their surface's turn), on the basis: her shape keys are deltas and keep their shapes.

Followers (heroine_neck_shape's helpers): every record keyed by her bind points (armor_tuck/*.bin, armor_cover/*.bin
in godot/art/people and godot/art/armor) re-keyed; every outfit, hair and armor piece point near the moved skin carried
by the move of the skin under it (in full within FOLLOW[0], none past FOLLOW[1]: the puff sleeves stand off her).

    python tools/assets/heroine_arm_shape.py --art godot/art/people [--no-follow] [--dry]
Run after heroine_neck_shape and before worn_reaver_post (heroine_body_post.py step 5); then the LODs and reimport.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_neck_shape as ns  # noqa: E402
from heroine_neck import _Gl, _mark  # noqa: E402

MARK = "heroine_arm_shape"
INNER = 0.0165                     # m, the inner side's move at its peak (before smoothing)
INNER_T = ((0.04, 0.26), (0.48, 0.68))
INNER_POW = 2.0
WEB = 0.008                        # m, the armpit web's extra draw near the shoulder
WEB_T = ((-0.04, 0.04), (0.14, 0.26))
ARM_W = (0.30, 0.70)               # the arm's skinning share: none under the first, whole over the second
WEB_TORSO = 0.004                  # m, the web's torso side in toward her midline
TORSO_W = (0.06, 0.15, 0.40)       # (its arm share: whole from the first to the second, none past the third)
DELT = 0.0045                      # m, the deltoid's swell
DELT_T = ((-0.08, 0.06), (0.24, 0.40))
DELT_POW = 2.0
DELT_R = (0.065, 0.085)            # (the arm's own skin: whole within the first radius, none past the second)
BREAST_KEEP = (0.030, 0.050)       # m from her breast-weighted skin
SMOOTH = 0                         # (rings over her skin after: none, her mesh is irregular there)
SIGMA = 0.014                     # m, the volume smoothing's reach (Gaussian)
FOLLOW = (0.015, 0.045)


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _win(t, w):
    (a0, a1), (b0, b1) = w
    return _ss((t - a0) / (a1 - a0)) * _ss((b1 - t) / (b1 - b0))


def _joints(G):
    names = G.names()
    ibm = G.get(G.g["skins"][0]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    return names, {n: np.linalg.inv(ibm[i])[:3, 3] for i, n in enumerate(names)}


def _shares(G, S, names):
    """Each welded point's skinning share on each arm (l, r) and on her breasts."""
    nw = len(S.B)
    out = {k: np.zeros(nw) for k in ("l", "r", "breast")}
    cnt = np.zeros(nw)
    sets = {s: [i for i, n in enumerate(names) if n.endswith("_" + s) and any(k in n for k in ("upperarm", "lowerarm", "hand"))]
            for s in "lr"}
    sets["breast"] = [i for i, n in enumerate(names) if n in ("breast_l", "breast_r")]
    for k, p in enumerate(S.prims):
        a = p["attributes"]
        J = G.get(a["JOINTS_0"]).astype(int)
        W = G.get(a["WEIGHTS_0"]).astype(float)
        W /= np.maximum(W.sum(1, keepdims=True), 1e-12)
        ix = S.wid[S.off[k]:S.off[k + 1]]
        for key, js in sets.items():
            np.add.at(out[key], ix, (W * np.isin(J, js)).sum(1))
        np.add.at(cnt, ix, 1)
    return {k: v / np.maximum(cnt, 1) for k, v in out.items()}


def field(G, S):
    """The bind move of each welded point (n, 3)."""
    names, J = _joints(G)
    sh = _shares(G, S, names)
    X = S.B
    D = np.zeros_like(X)
    up = np.array([0.0, 1.0, 0.0])
    for s in "lr":
        A, E = J["upperarm_" + s], J["lowerarm_" + s]
        ax = E - A
        L = np.linalg.norm(ax)
        n = ax / L
        top = up - (up @ n) * n
        top /= np.linalg.norm(top)
        d = X - A
        t = d @ n / L
        rv = d - np.outer(d @ n, n)
        r = np.linalg.norm(rv, axis=1)
        e = rv / np.maximum(r, 1e-9)[:, None]
        ct = e @ top
        side = np.sign(X[:, 0] - 0.001) == np.sign(A[0])
        wa = _ss((sh[s] - ARM_W[0]) / (ARM_W[1] - ARM_W[0])) * side
        inner = ((1 - ct) / 2) ** INNER_POW
        amt = (INNER * _win(t, INNER_T) + WEB * _win(t, WEB_T)) * inner * wa
        # (the web's torso side, little arm weight: in toward her midline, so the web slims from both sides)
        wt = _ss(sh[s] / TORSO_W[0]) * _ss((TORSO_W[2] - sh[s]) / (TORSO_W[2] - TORSO_W[1])) * side
        D[:, 0] -= np.sign(A[0]) * WEB_TORSO * _win(t, WEB_T) * inner * wt
        outer = ((1 + ct) / 2) ** DELT_POW
        delt = DELT * _win(t, DELT_T) * outer * wa * _ss((DELT_R[1] - r) / (DELT_R[1] - DELT_R[0]))
        D += e * (delt - amt)[:, None]
    # (a volume smoothing: points close in space move alike, so the two sides of her armpit's crease move as one
    # and no small face there folds; then a few rings over the skin)
    from scipy.spatial import cKDTree
    src = np.where(np.linalg.norm(D, axis=1) > 1e-7)[0]
    if len(src):
        lo, hi = X[src].min(0) - 3 * SIGMA, X[src].max(0) + 3 * SIGMA
        act = np.where(((X > lo) & (X < hi)).all(1))[0]
        M = cKDTree(X[act]).sparse_distance_matrix(cKDTree(X[src]), 3 * SIGMA, output_type="coo_matrix")
        import scipy.sparse as sp
        Wg = sp.coo_matrix((np.exp(-0.5 * (M.data / SIGMA) ** 2), (M.row, M.col)), shape=(len(act), len(src))).tocsr()
        # (normalised by every point's neighbours, moved or not: the field eases off where the moved skin ends)
        Ma = cKDTree(X[act]).sparse_distance_matrix(cKDTree(X[act]), 3 * SIGMA, output_type="coo_matrix")
        den = np.bincount(Ma.row, weights=np.exp(-0.5 * (Ma.data / SIGMA) ** 2), minlength=len(act))
        Dn = np.zeros_like(D)
        Dn[act] = (Wg @ D[src]) / np.maximum(den, 1e-12)[:, None]
        D = Dn
    for _ in range(SMOOTH):
        D = S.Wn @ D
    br = sh["breast"] > 0.05
    if br.any():
        from scipy.spatial import cKDTree
        db, _ = cKDTree(X[br]).query(X)
        D *= _ss((db - BREAST_KEEP[0]) / (BREAST_KEEP[1] - BREAST_KEEP[0]))[:, None]
    return D


def correct(path_in, path_out, report=True):
    """Her arms shaped in path_in written to path_out. Returns the field dict for the followers (P0/P1 per moved
    vertex, SB/SD the welded bind and bind move), or None when the glb has had it."""
    import shutil
    if os.path.abspath(path_in) != os.path.abspath(path_out):
        shutil.copyfile(path_in, path_out)
    G = _Gl(path_out)
    if G.g.get("asset", {}).get("extras", {}).get(MARK):
        print("ARM_SHAPE: %s has had it" % path_out)
        return None
    S = ns._Skin(G)
    Db = field(G, S)
    mv = np.linalg.norm(Db, axis=1)
    moved = mv > 1e-7
    B1 = S.B + Db
    nb0, nb1 = S.vn(S.B), S.vn(B1)
    fq0 = np.cross(S.B[S.F[:, 1]] - S.B[S.F[:, 0]], S.B[S.F[:, 2]] - S.B[S.F[:, 0]])
    fq1 = np.cross(B1[S.F[:, 1]] - B1[S.F[:, 0]], B1[S.F[:, 2]] - B1[S.F[:, 0]])
    fturn = np.degrees(np.arccos(np.clip((fq0 * fq1).sum(1) / np.maximum(
        np.linalg.norm(fq0, axis=1) * np.linalg.norm(fq1, axis=1), 1e-30), -1, 1)))
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
    _mark(path_out, MARK, {"inner_mm": INNER * 1000, "web_mm": WEB * 1000, "delt_mm": DELT * 1000, "smooth": SMOOTH,
                           "max_mm": round(float(mv.max()) * 1000, 3)})
    if report:
        print("ARM_SHAPE: %d welded points moved, largest %.2f mm, mean %.2f; largest face turn %.1f deg"
              % (int(moved.sum()), mv.max() * 1000, mv[moved].mean() * 1000, fturn.max()))
    return dict(P0=np.concatenate(P0s) if P0s else np.zeros((0, 3), np.float32),
                P1=np.concatenate(P1s) if P1s else np.zeros((0, 3), np.float32), SB=S.B, SD=Db)


def run_art(art, follow=True, dry=False):
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
                        print("ARM_SHAPE: %s/%s re-keyed %d" % (os.path.basename(base), sub + "/" + fn, h))
    if not follow:
        return
    files = [os.path.join(art, f) for f in sorted(os.listdir(art))
             if f.endswith(".gltf") and (f.startswith("heroine_outfit_") or f.startswith("heroine_hair_")) and not f.endswith("_lod.gltf")]
    files += [os.path.join(ad, f) for f in sorted(os.listdir(ad)) if f.endswith(".gltf")] if os.path.isdir(ad) else []
    keep = ns.FOLLOW
    ns.FOLLOW = FOLLOW
    try:
        for fp in files:
            big = ns.follow_piece(fp, fld)
            if big > 0:
                print("ARM_SHAPE: %s followed, largest %.2f mm" % (os.path.relpath(fp, root), big * 1000))
    finally:
        ns.FOLLOW = keep


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--art":
        run_art(a[1], follow="--no-follow" not in a, dry="--dry" in a)
    else:
        correct(a[0], a[1])
