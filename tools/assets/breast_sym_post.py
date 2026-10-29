"""Her breasts' inner slopes made mirror-alike (armor 12, dent d1, 21 October 2026: the owner's soft hollow on her
LEFT breast's inner slope above the gold gore boss, "its in all" outfits). DRAFT: not installed.

What it fixes (measured, d1): her body mesh at rest is mirror-symmetric to 0.46 mm rms over her torso (about a
plane 2.0 mm to her left of x = 0), but her left breast's inner lower slope, from the cleavage's foot up the inner
wall (5-70 mm left of her midline, 1.335-1.415 m), stands up to 3.0 mm proud of her right's mirror along its normal:
her left breast's inner fold sits about 5 mm nearer her midline than her right's, so its crease's shadow lies just
above-right of the gore boss, medial of the cup's inner rim (her right's lies under the rim). It is in her body since
63bdbf0f (2 October, "a head of her own"), unchanged through every build since; no weight, tuck colour, paint or
normal step adds to it.

The step: her left patch moved along its normal onto her right side's skin mirrored (about the fitted plane), by a
window of 1 over the patch easing to 0 over FADE (smoothstep), never at her midline or behind her front; three
passes, the offset field lightly smoothed. Her right side, her graft, head and every other point unmoved.
Normals carried as heroine_neck.fair_seam does (each point's own, turned by its surface's change). Her shape keys
are deltas on the basis, so each key's shape moves with the basis (none of hers has a delta in the patch: checked).

Followers (as nape_post's match_pieces): every record file keyed by her body's bind points (armor_tuck/*.bin,
armor_cover/*.bin: i32 x, y, z of the bind point x 1e5, f32 value) re-keyed for the moved points (remap_records),
and any piece's points over the patch carried by the move of the skin under them (follow_piece).

    python tools/assets/breast_sym_post.py <heroine.glb in> <heroine.glb out> [--report]
    python tools/assets/breast_sym_post.py --art <art dir copy> [--no-follow]  (body, then outfits' records [and pieces], in place)
"""
import json
import os
import shutil
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heroine_neck import _Gl, _mark  # noqa: E402

MARK = "breast_sym"
# the patch, from her mirror plane (m): x' left of her midline, y up (glTF rest)
CORE_X = (0.004, 0.075)
CORE_Y = (1.335, 1.415)
FADE = 0.018            # the window's ease outside the core (>= 15 mm)
MID_GUARD = 0.004       # nothing moves within this of her midline
FRONT_Z = (0.04, 0.06)  # eased in from z 4 cm to 6 cm: her front only
PASSES, SMOOTH = 6, 6
NSMOOTH = 6            # the direction of the move: her normals smoothed this many rings (so a crease's points move as one)
UNDER = None  #      # (or (-0.55, -0.25): eased out where her skin faces down)
VECTOR = True
UNTANGLE = 85          # deg: no face of hers turned more than this by the move
UNDER_ = (-0.55, -0.25)  # the window eased out where her skin faces down (her breast's underside, its fold: thin folded faces)
FOLLOW = (0.01, 0.03)   # a piece's point follows the skin under it in full within 1 cm, none past 3
# (d4: her skin mirrored in x = 0 itself, not about the fitted plane. The fit's plane (x = 2 mm) is a 4 mm shift of the
# mirrored skin, more than the whole fault, and turned it round: round 1 read her left wall as 3 mm proud and moved it
# 1.1 mm deeper; the ray-cast along her normal onto the x = 0 mirror (d3) finds it 3 mm inside, a hollow, as seen)
FIT_PLANE = False
NORMALS_MIRROR = True
CARRY_RINGS = 2
MIRROR_AGREE = (25.0, 40.0)
WELD_DEG = 10.0         # her split copies' normals (a UV seam's) shared where they part by more than this, in the window
WELD_BOX = ((0.004, 0.075), (1.335, 1.415), 0.04)  # x' left of her midline, y, z above: her left inner breast only


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _closest_tri(p, A):
    a, b, c = A[:, 0], A[:, 1], A[:, 2]
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    den = va + vb + vc
    den[den == 0] = 1e-30
    v, w = vb / den, vc / den
    r = a + ab * v[:, None] + ac * w[:, None]
    m = (d1 <= 0) & (d2 <= 0); r[m] = a[m]
    m = (d3 >= 0) & (d4 <= d3); r[m] = b[m]
    m = (d6 >= 0) & (d5 <= d6); r[m] = c[m]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); t = d1 / (d1 - d3 + 1e-30); r[m] = (a + ab * t[:, None])[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); t = d2 / (d2 - d6 + 1e-30); r[m] = (a + ac * t[:, None])[m]
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = (d4 - d3) / ((d4 - d3) + (d5 - d6) + 1e-30); r[m] = (b + (c - b) * t[:, None])[m]
    return r


class _Surf:
    """Closest points on a triangle mesh (candidates: the faces round the k nearest points)."""

    def __init__(s, V, F, k=12):
        s.V, s.F, s.k, s.tree = V, F, k, cKDTree(V)
        s.vt = [[] for _ in range(len(V))]
        for t, f in enumerate(F):
            for v in f:
                s.vt[v].append(t)

    def near(s, Q):
        _, nn = s.tree.query(Q, s.k)
        out, tri = np.zeros_like(Q), np.zeros(len(Q), int)
        for i, q in enumerate(Q):
            ts = np.array(sorted({t for v in nn[i] for t in s.vt[v]}))
            cp = _closest_tri(q, s.V[s.F[ts]])
            j = np.linalg.norm(cp - q, axis=1).argmin()
            out[i], tri[i] = cp[j], ts[j]
        return out, tri


def _vn(X, F):
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    n = np.zeros_like(X)
    for k in range(3):
        np.add.at(n, F[:, k], q)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def _body(G):
    """Her body's skin primitive (node Heroine, the first skinned primitive: not the graft), welded by place."""
    g = G.g
    hb = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    p = [p for p in g["meshes"][hb["mesh"]]["primitives"]
         if g["materials"][p["material"]].get("name") not in ("skin_graft", "skin_head")][0]
    P = G.get(p["attributes"]["POSITION"]).astype(float)
    F0 = G.get(p["indices"]).reshape(-1, 3).astype(int)
    _, first, wid = np.unique(np.round(P / 1e-6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    wid = wid.ravel()
    U = P[first]
    F = wid[F0]
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 2] != F[:, 0])]
    return p, P, wid, U, F


def mirror_fit(U, F, iters=6):
    """(R, t): her skin mirrored in x = 0, then turned and moved onto her own skin (point to plane, her torso less
    her breasts). The plane of her symmetry is x = t_x / 2 (R is within a tenth of a degree of none)."""
    Nv = _vn(U, F)
    torso = (U[:, 1] > 1.05) & (U[:, 1] < 1.47) & (np.abs(U[:, 0]) < 0.17)
    breast = (np.hypot(np.abs(U[:, 0]) - 0.09, U[:, 1] - 1.39) < 0.08) & (U[:, 2] > 0)
    sel = np.nonzero(torso & ~breast)[0][::3]
    S = np.diag([-1.0, 1, 1])
    R, t = np.eye(3), np.zeros(3)
    surf = _Surf(U, F)
    Q0 = U[sel] @ S.T
    rms = 0
    for _ in range(iters):
        Q = Q0 @ R.T + t
        cp, _ = surf.near(Q)
        n = Nv[surf.tree.query(cp)[1]]
        r = ((cp - Q) * n).sum(1)
        x = np.linalg.lstsq(np.hstack([np.cross(Q, n), n]), r, rcond=None)[0]
        w = x[:3]
        dR = np.array([[1, -w[2], w[1]], [w[2], 1, -w[0]], [-w[1], w[0], 1]])
        u, _, vt = np.linalg.svd(dR)
        dR = u @ vt
        R, t = dR @ R, dR @ t + x[3:]
        rms = float(np.sqrt((r ** 2).mean()))
    return R, t, rms


def offsets(U, F, R, t, idx, Nv=None):
    """Each point's signed offset (m) along its normal from her other side's skin mirrored onto it (positive:
    standing proud of it), and whether the match is sound (the mirrored skin there facing the same way)."""
    S = np.diag([-1.0, 1, 1])
    Q = (U @ S.T) @ R.T + t
    Nv = _vn(U, F) if Nv is None else Nv
    NQ = _vn(Q, F) * -1  # (mirroring turns her faces' winding: outward again)
    cp, tri = _Surf(Q, F).near(U[idx])
    nq = NQ[F[tri]].mean(1)
    nq /= np.maximum(np.linalg.norm(nq, axis=1, keepdims=True), 1e-12)
    d = ((U[idx] - cp) * Nv[idx]).sum(1)
    ok = ((Nv[idx] * nq).sum(1) > 0.3) & (np.linalg.norm(U[idx] - cp, axis=1) < 0.008)
    return d, ok, cp


def window(U, mid):
    x, y, z = U[:, 0] - mid, U[:, 1], U[:, 2]
    fx = _ss((x - CORE_X[0] + FADE) / FADE) * _ss((CORE_X[1] + FADE - x) / FADE)
    fy = _ss((y - CORE_Y[0] + FADE) / FADE) * _ss((CORE_Y[1] + FADE - y) / FADE)
    return fx * fy * _ss((z - FRONT_Z[0]) / (FRONT_Z[1] - FRONT_Z[0])) * _ss(x / MID_GUARD)


def correct(path_in, path_out, report=True):
    """Her body in path_in corrected into path_out (a copy). Returns the field: her moved bind points' old and new
    places (P0, P1), for remap_records and follow_piece; None when the glb has had it."""
    if os.path.abspath(path_in) != os.path.abspath(path_out):
        shutil.copyfile(path_in, path_out)
    G = _Gl(path_out)
    if G.g.get("asset", {}).get("extras", {}).get(MARK):
        print("BREAST_SYM: %s has had it" % path_out)
        return None
    p, P, wid, U, F = _body(G)
    R, t, rms = mirror_fit(U, F)
    fit_mid = t[0] / 2
    if not FIT_PLANE:
        R, t = np.eye(3), np.zeros(3)
    mid = t[0] / 2
    f = window(U, mid)
    ix = np.nonzero(f > 0)[0]
    # (the welded neighbours, for the smoothing)
    E = np.unique(np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1), axis=0)
    import scipy.sparse as sp
    A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(len(U),) * 2).tocsr()
    Wn = (sp.diags(1 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)) @ A).tocsr()
    X = U.copy()
    Ns = _vn(U, F)
    for _ in range(NSMOOTH):
        Ns = Wn @ Ns
        Ns /= np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
    if UNDER:
        f = f * _ss((Ns[:, 1] - UNDER[0]) / (UNDER[1] - UNDER[0]))
    ix = np.nonzero(f > 0)[0]
    for _ in range(PASSES):
        Nv = _vn(X, F)
        d, ok, cp = offsets(X, F, R, t, ix, Nv)
        V = np.zeros_like(U)
        if VECTOR:
            # (each point onto the mirrored skin's nearest point: in her fold the line itself moves, not only out)
            V[ix] = np.where(ok[:, None], cp - X[ix], 0)
        else:
            V[ix] = -np.where(ok, d, 0)[:, None] * Ns[ix] / np.maximum((Nv[ix] * Ns[ix]).sum(1), 0.5)[:, None]
        for _ in range(SMOOTH):
            V = np.where(f[:, None] > 0, 0.5 * V + 0.5 * (Wn @ V), 0)
        X = X + f[:, None] * V
    # (untangled: where the move set her breast's fold over itself, a face turned past UNTANGLE from its rest, the
    # move backed off on its points and their ring, then eased among them, until no face is: never more than asked)
    fn0 = np.cross(U[F[:, 1]] - U[F[:, 0]], U[F[:, 2]] - U[F[:, 0]])
    Dsp = X - U
    for it in range(200):
        X = U + Dsp
        fn1 = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
        cs = (fn0 * fn1).sum(1) / np.maximum(np.linalg.norm(fn0, axis=1) * np.linalg.norm(fn1, axis=1), 1e-30)
        bad = cs < np.cos(np.radians(UNTANGLE))
        if not bad.any():
            break
        m = np.zeros(len(U), bool)
        m[F[bad].ravel()] = True
        m = m | ((A @ m.astype(float)) > 0)
        Dsp[m] *= 0.8
        Dsp[m] = 0.5 * Dsp[m] + 0.5 * (Wn @ Dsp)[m] * (f[m] > 0)[:, None]
    untangled = it
    mv = np.linalg.norm(X - U, axis=1)
    N0, N1 = _vn(U, F), _vn(X, F)
    # (the carried turn read off her vertex normals smoothed CARRY_RINGS rings: her fold's slivers alone turn wildly)
    N0s, N1s = N0.copy(), N1.copy()
    for _ in range(CARRY_RINGS):
        N0s = Wn @ N0s; N0s /= np.maximum(np.linalg.norm(N0s, axis=1, keepdims=True), 1e-12)
        N1s = Wn @ N1s; N1s /= np.maximum(np.linalg.norm(N1s, axis=1, keepdims=True), 1e-12)
    dN = np.where((mv > 1e-7)[:, None], N1s - N0s, 0)
    # (written back per vertex: seam duplicates take their welded point's move)
    P1 = X[wid].astype(np.float32)
    G.put(p["attributes"]["POSITION"], P1)
    Nr = G.get(p["attributes"]["NORMAL"]).astype(float)
    turn = np.linalg.norm(dN, axis=1)[wid] > 1e-7
    Nr[turn] += dN[wid][turn]
    Nr /= np.maximum(np.linalg.norm(Nr, axis=1, keepdims=True), 1e-12)
    if NORMALS_MIRROR:
        # (d4: carried by the change of her own vertex normals, the patch's slivers (faces of 0.01-0.3 mm2 in her fold)
        # turned her stored normals up to 50 deg. Her moved skin now lies on her right's mirror, so it takes her right's
        # stored normals, mirrored and read at the matched point, by the window's weight; a designed crease (a split
        # copy group parting by more than WELD_DEG outside WELD_BOX: her breast's underside fold) keeps its own)
        S = np.diag([-1.0, 1, 1])
        N0r = G.get(p["attributes"]["NORMAL"]).astype(float)
        Nw = np.zeros_like(U)
        np.add.at(Nw, wid, N0r / np.maximum(np.linalg.norm(N0r, axis=1, keepdims=True), 1e-12))
        Nw = (Nw / np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-12)) @ S.T
        Q = (U @ S.T) @ R.T + t
        jx = np.nonzero(f > 0)[0]
        cpm, trm = _Surf(Q, F).near(X[jx])
        a_, b_, c_ = Q[F[trm, 0]], Q[F[trm, 1]], Q[F[trm, 2]]
        v0, v1, v2 = b_ - a_, c_ - a_, cpm - a_
        d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
        d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
        den = np.maximum(d00 * d11 - d01 * d01, 1e-30)
        bv, bw = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
        bu = 1 - bv - bw
        Nm = Nw[F[trm, 0]] * bu[:, None] + Nw[F[trm, 1]] * bv[:, None] + Nw[F[trm, 2]] * bw[:, None]
        Nm /= np.maximum(np.linalg.norm(Nm, axis=1, keepdims=True), 1e-12)
        Ng = _vn(X, F)[jx]
        good = (np.linalg.norm(X[jx] - cpm, axis=1) < 0.002) & ((Nm * Ng).sum(1) > 0.5)
        # (only where her own moved skin agrees with the mirror's normal: eased out from MIRROR_AGREE[0] to [1] deg off
        # her own smoothed normal, so a stretch the move could not match keeps its own shading)
        agree = np.degrees(np.arccos(np.clip((Nm * N1s[jx]).sum(1), -1, 1)))
        fa = _ss((MIRROR_AGREE[1] - agree) / (MIRROR_AGREE[1] - MIRROR_AGREE[0]))
        # (a group's split before, per welded point)
        spl = np.zeros(len(U))
        Nn0 = N0r / np.maximum(np.linalg.norm(N0r, axis=1, keepdims=True), 1e-12)
        np.maximum.at(spl, wid, np.degrees(np.arccos(np.clip((Nn0 * (Nw @ S.T)[wid]).sum(1), -1, 1))))
        wx, wy, wz = WELD_BOX
        inbox0 = ((U[:, 0] - mid > wx[0]) & (U[:, 0] - mid < wx[1]) & (U[:, 1] > wy[0]) & (U[:, 1] < wy[1]) & (U[:, 2] > wz))
        crease = (spl > WELD_DEG / 2) & ~inbox0
        wgt = np.zeros(len(U))
        wgt[jx] = np.where(good & ~crease[jx], f[jx] * fa, 0)
        mirN = np.zeros_like(U)
        mirN[jx] = Nm
        on = wgt[wid] > 0
        Nr[on] = Nr[on] * (1 - wgt[wid][on, None]) + mirN[wid][on] * wgt[wid][on, None]
        Nr /= np.maximum(np.linalg.norm(Nr, axis=1, keepdims=True), 1e-12)
        if report:
            print("BREAST_SYM: normals from her right's mirror on %d welded points (%d unmatched, %d crease points kept)"
                  % (int((wgt > 0).sum()), int((~good).sum()), int(crease[jx].sum())))
    # (the seam's split copies: one normal, their mean, where they part by more than WELD_DEG in the box: the fold line)
    wx, wy, wz = WELD_BOX
    inbox = ((U[:, 0] - mid > wx[0]) & (U[:, 0] - mid < wx[1]) & (U[:, 1] > wy[0]) & (U[:, 1] < wy[1]) & (U[:, 2] > wz))
    welded, split0, before, nb = 0, 0.0, 0.0, 0
    Nb = G.get(p["attributes"]["NORMAL"]).astype(float)
    Nb /= np.maximum(np.linalg.norm(Nb, axis=1, keepdims=True), 1e-12)
    for g in np.unique(wid[inbox[wid]]):
        ii = np.nonzero(wid == g)[0]
        if len(ii) < 2:
            continue
        sb = np.degrees(np.arccos(np.clip(Nb[ii] @ Nb[ii].T, -1, 1))).max()
        before, nb = max(before, sb), nb + (len(ii) if sb > WELD_DEG else 0)
        nn = Nr[ii]
        sp = np.degrees(np.arccos(np.clip(nn @ nn.T, -1, 1))).max()
        if sp > WELD_DEG:
            m = nn.sum(0)
            Nr[ii] = m / np.linalg.norm(m)
            welded += len(ii)
            split0 = max(split0, sp)
    G.put(p["attributes"]["NORMAL"], Nr.astype(np.float32))
    acc = G.g["accessors"][p["attributes"]["POSITION"]]
    lo, hi = P1.min(0).tolist(), P1.max(0).tolist()
    G.save()
    # (the accessor's bounds, and the done-mark, in the json)
    _bounds(path_out, p["attributes"]["POSITION"], lo, hi)
    _mark(path_out, MARK, {"core_x": CORE_X, "core_y": CORE_Y, "fade": FADE, "mid": round(float(mid), 6),
                           "passes": PASSES, "max_mm": round(float(mv.max()) * 1000, 3), "weld_copies": welded})
    moved = mv > 1e-7
    if report:
        keys = G.g["meshes"][[n for n in G.g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]].get("extras", {}).get("targetNames", [])
        kd = []
        for k, tg in enumerate(p.get("targets", [])):
            dd = _dense_acc(G, tg["POSITION"])
            kd.append((keys[k] if k < len(keys) else k, float(np.abs(dd[np.isin(wid, np.nonzero(moved)[0])]).max(initial=0))))
        print("BREAST_SYM: mirror plane x = %.2f mm (torso rms %.2f mm); %d welded points moved (%d vertices), largest "
              "%.2f mm, mean %.2f mm; outside the window: %.3g mm; normals turned on %d vertices (max %.2f deg); "
              "untangle passes %d; shape keys' largest delta on moved points: %s" %
              (mid * 1000, rms * 1000, int(moved.sum()), int(moved[wid].sum()), mv.max() * 1000,
               mv[moved].mean() * 1000 if moved.any() else 0, mv[f == 0].max(initial=0) * 1000, int(turn.sum()),
               np.degrees(np.arccos(np.clip((N0 * N1).sum(1), -1, 1))).max(), untangled, kd))
        print("BREAST_SYM: mirror x = %.2f mm (the fitted plane would be %.2f); seam copies in the box parting > %g deg: "
              "%d before (largest %.1f deg), %d after the mirror's normals (largest %.1f), welded" %
              (mid * 1000, fit_mid * 1000, WELD_DEG, nb, before, welded, split0))
    keep = moved[wid]
    return dict(P0=P[keep].astype(np.float32), P1=P1[keep], mid=mid, R=R, t=t)


def _dense_acc(G, ai):
    """An accessor, sparse or not, as a dense array (a shape key's deltas are often sparse)."""
    a = G.g["accessors"][ai]
    if "bufferView" in a:
        return G.get(ai).astype(float)
    out = np.zeros((a["count"], 3))
    sps = a.get("sparse")
    if sps:
        bv = G.g["bufferViews"]
        it = {5121: "u1", 5123: "<u2", 5125: "<u4"}[sps["indices"]["componentType"]]
        o = G.b0 + bv[sps["indices"]["bufferView"]].get("byteOffset", 0) + sps["indices"].get("byteOffset", 0)
        ii = np.frombuffer(bytes(G.buf[o:o + np.dtype(it).itemsize * sps["count"]]), it)
        o = G.b0 + bv[sps["values"]["bufferView"]].get("byteOffset", 0) + sps["values"].get("byteOffset", 0)
        out[ii] = np.frombuffer(bytes(G.buf[o:o + 12 * sps["count"]]), "<f4").reshape(-1, 3)
    return out


def _bounds(path, ai, lo, hi):
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    g = json.loads(d[20:20 + jl])
    g["accessors"][ai]["min"], g["accessors"][ai]["max"] = lo, hi
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


def follow_piece(path, field, mark=None):
    """A piece file's points over the patch carried by the move of her skin under them (the nearest moved bind
    point's move, in full within FOLLOW[0], none past FOLLOW[1]). Returns the largest move (m).
    (armor 14: each moved point's stored normal turned by its surface's change, as correct() carries hers: the moved
    points kept their old normals before, so a garment kept the old hollow's shading. mark: a done-mark written in the
    file's asset extras, and a file that has it is skipped)"""
    if not len(field["P0"]):
        return 0.0
    G = _Gl(path)
    if mark and G.g.get("asset", {}).get("extras", {}).get(mark):
        print("BREAST_SYM: %s has had %s" % (os.path.basename(path), mark))
        return 0.0
    T = cKDTree(field["P0"])
    Dm = field["P1"].astype(float) - field["P0"].astype(float)
    big = 0.0
    for m in G.g["meshes"]:
        for p in m["primitives"]:
            P = G.get(p["attributes"]["POSITION"]).astype(float)
            d, j = T.query(P, k=8)
            w = np.exp(-(d / 0.004) ** 2) + 1e-12
            mv = (Dm[j] * w[:, :, None]).sum(1) / w.sum(1)[:, None]
            mv *= _ss((FOLLOW[1] - d[:, 0]) / (FOLLOW[1] - FOLLOW[0]))[:, None]
            if np.abs(mv).max() < 1e-7:
                continue
            P1 = (P + mv).astype(np.float32)
            G.put(p["attributes"]["POSITION"], P1)
            if "NORMAL" in p["attributes"] and "indices" in p:
                # (welded by place, so a UV seam's split copies turn alike)
                _, wid = np.unique(np.round(P * 1e6).astype(np.int64), axis=0, return_inverse=True)
                wid = wid.ravel()
                F = wid[G.get(p["indices"]).astype(np.int64).reshape(-1, 3)]
                U0 = np.zeros((wid.max() + 1, 3)); U0[wid] = P
                U1 = np.zeros_like(U0); U1[wid] = P1
                dN = _vn(U1, F) - _vn(U0, F)
                N = G.get(p["attributes"]["NORMAL"]).astype(float)
                on = np.linalg.norm(mv, axis=1) > 1e-7
                N[on] += dN[wid][on]
                N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
                G.put(p["attributes"]["NORMAL"], N.astype(np.float32))
            a = G.g["accessors"][p["attributes"]["POSITION"]]
            a["min"], a["max"] = P1.min(0).tolist(), P1.max(0).tolist()
            big = max(big, float(np.linalg.norm(mv, axis=1).max()))
    if mark:
        G.g.setdefault("asset", {}).setdefault("extras", {})[mark] = round(big * 1000, 3)
    if big > 0 or mark:
        G.save()
    return big


OUTFIT_MARK = "breast_sym_follow"


def follow_outfits(art, field):
    """(armor 14, 22 October: the arcanist bodysuit's dent on her left breast, the owner's crop
    bodysuit_dent_closeup.png.) The outfits are built on her body as Blender exports it, before this step; with
    --no-follow her skin moved out up to 3.2 mm and the garments over it kept the old hollow (the arcanist top's
    plumleather: a 2.1 mm pit at her left lower inner breast against 1.4 on her right). So the four outfits' points over
    the patch now follow her skin, as a piece's do; not a refit (nothing else moves). The slot pieces (armor/*.gltf)
    are fitted after this by build.py --all, so they never need it."""
    for o in ("warden", "arcanist", "ranger", "reaver"):
        pth = os.path.join(art, "heroine_outfit_%s.gltf" % o)
        if os.path.exists(pth):
            print("BREAST_SYM: outfit %s followed, largest %.2f mm" % (o, follow_piece(pth, field, OUTFIT_MARK) * 1000))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--outfits-from":
        # (a one-off on built art whose body has had the step: the field from the body before and after it, e.g.
        # git show d7d35321^:godot/art/people/heroine.glb and d7d35321:..., same build so the same point order)
        def _pts(f):
            G = _Gl(f)
            p = G.g["meshes"][0]["primitives"][0]
            return G.get(p["attributes"]["POSITION"]).astype(float)
        A, B = _pts(a[1]), _pts(a[2])
        mv = np.linalg.norm(B - A, axis=1) > 1e-7
        follow_outfits(a[3], {"P0": A[mv], "P1": B[mv]})
    elif a and a[0] == "--art":
        art = a[1]
        fld = correct(os.path.join(art, "heroine.glb"), os.path.join(art, "heroine.glb"))
        if fld is not None:
            for sub in ("armor_tuck", "armor_cover"):
                for root in (art, os.path.join(os.path.dirname(art.rstrip("/\\")), "armor")):
                    dd = os.path.join(root, sub)
                    for fn in sorted(os.listdir(dd)) if os.path.isdir(dd) else []:
                        if fn.endswith(".bin"):
                            h = remap_records(os.path.join(dd, fn), fld)
                            if h:
                                print("BREAST_SYM: %s/%s re-keyed %d" % (sub, fn, h))
            # (--no-follow: no slot piece touched; the outfits follow unless --no-outfit-follow (armor 14))
            if "--no-outfit-follow" not in a:
                follow_outfits(art, fld)
            # (the slot pieces fitted to her: armor/*.gltf; a piece standing clear of the patch is untouched)
            ad = os.path.join(os.path.dirname(art.rstrip("/\\")), "armor")
            for fn in sorted(os.listdir(ad)) if os.path.isdir(ad) and "--no-follow" not in a else []:
                if fn.endswith(".gltf"):
                    big = follow_piece(os.path.join(ad, fn), fld)
                    if big > 0:
                        print("BREAST_SYM: armor/%s followed, largest %.2f mm" % (fn, big * 1000))
    else:
        correct(a[0], a[1])
