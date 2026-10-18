"""Her throat bends as a woman's, not round an Adam's apple (the owner, 18 October 2026, C01 by the fire: "a giant
atoms apple ... it looks bad").

    import heroine_throat; heroine_throat.ease(<heroine.glb>)     (after heroine_neck.match_graft, before shorten_glb)

What it was. Her shape at rest is smooth (no laryngeal bump on her midline, measured to 0.5 mm over a cubic). The bump
is her skinning: down the front of her throat her weights went from spine_03 (0.84) to Head (0.75) within 4 cm, from
1.553 to 1.593 m (rest, glTF), with neck_01 at 0.1 throughout. So with her head back the skin below 1.55 stayed with
her chest, the skin above 1.59 swung with her head, and the 4 cm between bent at two corners: a dip, then a ridge
that the firelight grazed (her midline 4-6 mm off a smooth curve with the head back 40-50 deg). Same in every body
since the base was rigged, which is why the neck seam fix did not change it.

What it does. Over the front and sides of her neck, between her chest (where no point has Head or neck_01) and the
2 cm of her neck skin under her head (heroine_neck.match_graft gives that skin her head's weights, so the seam holds),
her weights are refilled smoothly (each bone's weight biharmonic over her skin, held at the points round the area):
the bend spreads from her sternal notch to under her jaw and her throat stays one long smooth line as her head goes
back or turns. Her shape is not moved (her pieces fit her as they were); only weights change. The pieces and hair
that took her neck skin's weights take the same change (heroine_neck.match_pieces, through its field).
Off: THROAT_SOFT=0.
"""
import os

TH_FREE = 120.0       # (deg round her neck from her front within which her weights are refilled)
HEAD_HOLD = 0.02      # (m: her skin this near her head keeps match_graft's weights, as heroine_neck.FULL)
UP_MIN = 0.005        # (Head + neck_01 below this: her chest and shoulders, held ...)
DH_LO = float(os.environ.get("THROAT_DH", "0.13"))   # (... unless this near her head: the refill reaches down her neck to
#                       her sternal notch and the tops of her shoulders, so her head's share ramps over her whole neck)
ARM_IN, ARM_OUT = 0.075, 0.12   # (m from her head: her clavicles' and upper arms' weight leaves her neck's column within
#                       ARM_IN, eased back by ARM_OUT, for her spine's ...)
ARM_TH = (110.0, 135.0)          # (... round her neck's front and sides, eased out round her nape)
SOLVE = os.environ.get("THROAT_SOLVE", "bi")   # (bi: biharmonic; harm: harmonic)
Y_LO, Y_HI, R_MAX = 1.40, 1.70, 0.18   # (the box, rest glTF metres, round her neck's axis, that the area lies in)


def _weld(P, T, np):
    _, inv = np.unique(np.round(P / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    inv = inv.ravel()
    U = np.zeros((inv.max() + 1, 3))
    U[inv] = P
    Tw = inv[T]
    Tw = Tw[(Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])]
    return U, inv, Tw


def ease(path, save=True):
    import numpy as np
    from scipy import sparse
    from scipy.sparse.linalg import splu
    from scipy.spatial import cKDTree
    import heroine_neck as hn
    G = hn._Gl(path)
    g = G.g
    N = g["nodes"]
    hb = [n for n in N if n.get("name") == "Heroine"][0]
    hh = [n for n in N if n.get("name") == "HeroineHead"][0]
    prims = [p for p in g["meshes"][hb["mesh"]]["primitives"] if "JOINTS_0" in p["attributes"]]
    gp = [p for p in prims if g["materials"][p["material"]].get("name") == "skin_graft"]
    assert len(gp) == 1, "one skin_graft"
    hp = [p for p in g["meshes"][hh["mesh"]]["primitives"] if g["materials"][p["material"]].get("name") == "skin_head"][0]
    names = G.names()
    nj = len(names)
    hj, nk = names.index("Head"), names.index("neck_01")
    # her neck's axis: neck_01's place in the world (rest), up her body
    par = {c: i for i, n in enumerate(N) for c in n.get("children", [])}

    def wm(i):
        n = N[i]
        x, y, z, w = n.get("rotation", [0, 0, 0, 1])
        M = np.eye(4)
        M[:3, :3] = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                              [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                              [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) * np.array(n.get("scale", [1, 1, 1]))
        M[:3, 3] = n.get("translation", [0, 0, 0])
        return M if i not in par else wm(par[i]) @ M
    c = wm([i for i, n in enumerate(N) if n.get("name") == "neck_01"][0])[:3, 3]
    # her body's skin, welded by place (the graft's seam copies and its edge with her body move as one)
    Ps, Ts, Js, Ws, o = [], [], [], [], 0
    for p in prims:
        x = G.get(p["attributes"]["POSITION"]).astype(float)
        Ps.append(x)
        Ts.append(G.get(p["indices"]).reshape(-1, 3).astype(int) + o)
        Js.append(G.get(p["attributes"]["JOINTS_0"]))
        Ws.append(G.get(p["attributes"]["WEIGHTS_0"]).astype(float))
        o += len(x)
    P, T = np.concatenate(Ps), np.concatenate(Ts)
    U, inv, Tw = _weld(P, T, np)
    D0 = hn._dense(np.concatenate(Js), np.concatenate(Ws), nj)
    W0 = np.zeros((len(U), nj))
    first = np.unique(inv, return_index=True)[1]
    W0[inv[first]] = D0[first]
    th = np.degrees(np.arctan2(U[:, 0] - c[0], U[:, 2] - c[2]))
    r = np.hypot(U[:, 0] - c[0], U[:, 2] - c[2])
    dh = cKDTree(G.get(hp["attributes"]["POSITION"]).astype(float)).query(U)[0]
    up = W0[:, hj] + W0[:, nk]
    free = (np.abs(th) < TH_FREE) & (U[:, 1] > Y_LO) & (U[:, 1] < Y_HI) & (r < R_MAX) & (dh > HEAD_HOLD) & ((up > UP_MIN) | (dh < DH_LO))
    # biharmonic fill (uniform Laplacian squared), held at every point round the area
    n = len(U)
    e = np.r_[Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]
    e = np.r_[e, e[:, ::-1]]
    A = sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    L = (sparse.diags(np.asarray(A.sum(1)).ravel()) - A).tocsr()
    L2 = (L @ L).tocsr() if SOLVE == "bi" else L
    fi, bi = np.nonzero(free)[0], np.nonzero(~free)[0]
    lu = splu(L2[fi][:, fi].tocsc())
    rhs = -(L2[fi][:, bi] @ W0[bi])
    X = W0.copy()
    used = np.nonzero(np.abs(W0[fi]).sum(0) + np.abs(rhs).sum(0) > 0)[0]
    for k in used:
        X[fi, k] = lu.solve(rhs[:, k])
    X = np.clip(X, 0, None)
    X /= np.maximum(X.sum(1, keepdims=True), 1e-12)
    # her clavicles and upper arms out of her neck's column (a shoulder or arm that moves no longer drags a cord up her
    # neck's side): their weight goes to her spine, all of it within ARM_IN of her head, none beyond ARM_OUT
    def ss(x):
        x = np.clip(x, 0, 1)
        return x * x * (3 - 2 * x)
    arm = [k for k, nm in enumerate(names) if nm.startswith(("clavicle", "upperarm"))]
    m = ss((ARM_OUT - dh) / (ARM_OUT - ARM_IN)) * ss((ARM_TH[1] - np.abs(th)) / (ARM_TH[1] - ARM_TH[0])) * \
        (r < R_MAX) * (U[:, 1] > Y_LO) * (U[:, 1] < Y_HI) * (dh > HEAD_HOLD)
    if arm and ARM_OUT > 0:
        sj = names.index("spine_03")
        a = X[:, arm] * m[:, None]
        X[:, arm] -= a
        X[:, sj] += a.sum(1)
        free = free | ((m > 0) & (W0[:, arm].sum(1) > 1e-4))
    # written back to her primitives (top four), the change kept for her pieces
    o, moved = 0, 0
    keepD = []
    for p, x in zip(prims, Ps):
        ix = inv[o:o + len(x)]
        o += len(x)
        f = free[ix]
        if not f.any():
            continue
        J, Wt = G.get(p["attributes"]["JOINTS_0"]), G.get(p["attributes"]["WEIGHTS_0"]).astype(np.float32)
        old = hn._dense(J[f], Wt[f].astype(float), nj)
        top, tw = hn._top4(X[ix[f]])
        J[f], Wt[f] = top, tw
        G.put(p["attributes"]["JOINTS_0"], J)
        G.put(p["attributes"]["WEIGHTS_0"], Wt)
        keepD.append((x[f], hn._dense(top, tw, nj) - old))
        moved += int(f.sum())
    if save:
        G.save()
    # (the graft's change for her pieces: match_graft's and this, summed where a point has both)
    fld = hn._FIELD[0] if hn._FIELD else None
    if keepD and fld is not None and list(fld["names"]) == list(names):
        Pn = np.concatenate([k[0] for k in keepD])
        Dn = np.concatenate([k[1] for k in keepD])
        Fp, Fd = fld["P"].copy(), fld["D"].copy()
        d, j = cKDTree(Fp).query(Pn)
        same = d < 1e-6
        np.add.at(Fd, j[same], Dn[same])
        fld["P"] = np.concatenate([Fp, Pn[~same]])
        fld["D"] = np.concatenate([Fd, Dn[~same]])
        if save:
            np.savez_compressed(hn.FIELD_FILE, P=fld["P"].astype(np.float32), D=fld["D"].astype(np.float32),
                                names=np.array(names), body=fld["body"].astype(np.float32), head=fld["head"].astype(np.float32))
    print("THROAT: %d points of her neck's front and sides given smooth weights (biharmonic between her chest and the "
          "skin under her head) in %s" % (moved, path))
    return X, free, U


# ---------------------------------------------------------------------------------------------------------------
# Her throat's shape as the game shows it (round 2, 18 October). The neck cut (heroine_neck.shorten_glb) drops each
# point 30 mm x its Head weight, so her throat between her sternal notch and her jaw is squashed by a third in the
# game: the sculpt's faint swell at her larynx (2.6 mm over a 3 cm fit, unposed) came out 4-5 mm, and the side of
# her neck (where it meets her shoulder) the same. Here her neck's front and sides are faired as the game shows them
# (cut, at rest): every point that stands out of a smooth fit (MLS, 3.5 cm) is taken in, inward only, faded to nothing
# at the edges, the skin within SOFT_DH[0] of her head (the graft's weld) unmoved. Her normals there are the faired
# surface's as the game shows it (the cut only moves points, so the game uses these normals unturned at rest).
# Off: THROAT_SOFT=0 (with ease).
SOFT_SIG = 0.03       # (m: the broadest fit's reach, a Gaussian's sigma; a fit takes points within 2.4 sigma)
SOFT_TH = (115.0, 140.0)   # (deg round her neck: whole within the first, none past the second)
SOFT_DH = (0.004, 0.018, 0.11, 0.14)   # (m from her head: none within the first, whole from the second to the
#                       third, none past the fourth: her neck's column, from under her jaw to her sternal notch)
SOFT_PASSES = ((1.0, 0.03),) * 5 + ((1.0, 0.015),) * 3   # (each pass: its share, its fit's sigma: the broad swells, then
#                       the finer folds the cut leaves round her neck)
SOFT_MAX = 0.008      # (m: no point taken in further)
SOFT_POS = (0.004, 0.005)   # (m from her head: her points not moved within the first (the weld), wholly from the second)
_C01 = [("neck_01", 1, 6), ("neck_01", 2, 16), ("Head", 1, 8), ("Head", 2, 14)]   # (C01 shot 3, story.py _side)
SOFT_POSES = [(2.0, [])] + [(1.0, [(j, a, s * d) for j, a, d in _C01 if a == 1] + [(j, a, t * d) for j, a, d in _C01 if a == 2])
                            for s in (1, -1) for t in (1, -1)] + [(1.0, [("neck_01", 0, -20), ("Head", 0, -20)])]
#                       (the looks the fit weighs: at rest twice, her head tilted and turned each way, back 40 deg)


def _ss(x, np):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _vn(U, T, np):
    f = np.cross(U[T[:, 1]] - U[T[:, 0]], U[T[:, 2]] - U[T[:, 0]])
    n = np.zeros_like(U)
    for k in range(3):
        np.add.at(n, T[:, k], f)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def _mls_out(S, Nn, idx, near, sig, np, tree):
    """How far each of S[idx] stands out (+) of a weighted quadric fitted round it over S[near] (the tree's)."""
    out = np.zeros(len(idx))
    Sn, Nnn = S[near], Nn[near]
    for k, i in enumerate(idx):
        nb = tree.query_ball_point(S[i], 2.4 * sig)
        Q = Sn[nb] - S[i]
        n = Nnn[nb].mean(0)
        n /= np.linalg.norm(n)
        a = np.cross(n, [1.0, 0, 0])
        if np.linalg.norm(a) < 0.3:
            a = np.cross(n, [0, 1.0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(n, a)
        u, v, h = Q @ a, Q @ b, Q @ n
        sw = np.sqrt(np.exp(-(u * u + v * v) / (2 * sig * sig)))
        A = np.c_[np.ones_like(u), u, v, u * u, u * v, v * v]
        cf = np.linalg.lstsq(A * sw[:, None], h * sw, rcond=None)[0]
        out[k] = -cf[0]
    return out


def soften(path, delta, save=True):
    """Her neck's front and sides faired as the game shows them (after the neck cut of `delta` m still to come;
    0 if the glb's Head joint is cut already); inward only. After ease, before heroine_neck.shorten_glb."""
    import numpy as np
    from scipy.spatial import cKDTree
    import heroine_neck as hn
    G = hn._Gl(path)
    g = G.g
    N = g["nodes"]
    hb = [n for n in N if n.get("name") == "Heroine"][0]
    hh = [n for n in N if n.get("name") == "HeroineHead"][0]
    prims = [p for p in g["meshes"][hb["mesh"]]["primitives"] if "JOINTS_0" in p["attributes"]]
    hp = [p for p in g["meshes"][hh["mesh"]]["primitives"] if g["materials"][p["material"]].get("name") == "skin_head"][0]
    names = G.names()
    nj = len(names)
    par = {c: i for i, n in enumerate(N) for c in n.get("children", [])}
    hi = [i for i, n in enumerate(N) if n.get("name") == "Head"][0]

    def wm(i, cut, rot=None):
        n = N[i]
        x, y, z, w = n.get("rotation", [0, 0, 0, 1])
        M = np.eye(4)
        M[:3, :3] = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                              [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                              [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) * np.array(n.get("scale", [1, 1, 1]))
        t = np.array(n.get("translation", [0, 0, 0]), float)
        if i == hi and cut:
            t = t * (np.linalg.norm(t) - cut) / np.linalg.norm(t)
        if rot and i in rot:
            M[:3, :3] = M[:3, :3] @ rot[i]
        M[:3, 3] = t
        return M if i not in par else wm(par[i], cut, rot) @ M
    sk = g["skins"][hb.get("skin", 0)]
    ibm = G.get(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    Jm = np.array([wm(j, delta) @ ibm[k] for k, j in enumerate(sk["joints"])])
    # (and as she turns her head: each pose's joints, for the fit's other looks)
    ni = {n.get("name"): i for i, n in enumerate(N)}

    def axrot(ax, deg):
        a = np.radians(deg)
        R = np.eye(3)
        b, e = [(1, 2), (0, 2), (0, 1)][ax]
        R[b, b] = R[e, e] = np.cos(a)
        R[b, e], R[e, b] = (-np.sin(a), np.sin(a)) if ax != 1 else (np.sin(a), -np.sin(a))
        return R
    Jp = []
    for wgt, ops in SOFT_POSES:
        rot = {}
        for jn, ax, dg in ops:
            rot[ni[jn]] = rot.get(ni[jn], np.eye(3)) @ axrot(ax, dg)
        Jp.append((wgt, np.array([wm(j, delta, rot) @ ibm[k] for k, j in enumerate(sk["joints"])])))
    c = wm([i for i, n in enumerate(N) if n.get("name") == "neck_01"][0], 0)[:3, 3]
    Ps, Ts, Js, Ws, o = [], [], [], [], 0
    for p in prims:
        x = G.get(p["attributes"]["POSITION"]).astype(float)
        Ps.append(x)
        Ts.append(G.get(p["indices"]).reshape(-1, 3).astype(int) + o)
        Js.append(G.get(p["attributes"]["JOINTS_0"]))
        Ws.append(G.get(p["attributes"]["WEIGHTS_0"]).astype(float))
        o += len(x)
    P, T = np.concatenate(Ps), np.concatenate(Ts)
    U, inv, Tw = _weld(P, T, np)
    D0 = hn._dense(np.concatenate(Js), np.concatenate(Ws), nj)
    W0 = np.zeros((len(U), nj))
    first = np.unique(inv, return_index=True)[1]
    W0[inv[first]] = D0[first]
    # (as the game shows her at rest: the cut drops her head's joint, her points by their weights)
    M = np.einsum("vj,jab->vab", W0, Jm)
    S = np.einsum("vab,vb->va", M, np.c_[U, np.ones(len(U))])[:, :3]
    th = np.degrees(np.arctan2(U[:, 0] - c[0], U[:, 2] - c[2]))
    r = np.hypot(U[:, 0] - c[0], U[:, 2] - c[2])
    dh = cKDTree(G.get(hp["attributes"]["POSITION"]).astype(float)).query(U)[0]
    box = (U[:, 1] > Y_LO) & (U[:, 1] < Y_HI) & (r < R_MAX)
    f = _ss((SOFT_TH[1] - np.abs(th)) / (SOFT_TH[1] - SOFT_TH[0]), np) * box * \
        _ss((dh - SOFT_DH[0]) / (SOFT_DH[1] - SOFT_DH[0]), np) * _ss((SOFT_DH[3] - dh) / (SOFT_DH[3] - SOFT_DH[2]), np)
    idx = np.nonzero(f > 1e-3)[0]
    near = np.nonzero(box & (dh < SOFT_DH[3] + 3 * SOFT_SIG))[0]
    tot = np.zeros(len(U))
    S2 = S.copy()
    for k, sg in SOFT_PASSES:
        Nn = _vn(S2, Tw, np)
        # (how far each point stands out, as the game shows her at rest and as she turns her head, weighed)
        res, wsum = np.zeros(len(idx)), 0.0
        U2 = U + (S2 - S)
        for wgt, J in Jp:
            Q = np.einsum("vab,vb->va", np.einsum("vj,jab->vab", W0, J), np.c_[U2, np.ones(len(U))])[:, :3]
            res += wgt * np.maximum(_mls_out(Q, _vn(Q, Tw, np), idx, near, sg, np, cKDTree(Q[near])), 0)
            wsum += wgt
        res /= wsum
        d = np.clip(res * f[idx] * k, 0, SOFT_MAX - tot[idx])
        S2[idx] -= Nn[idx] * d[:, None]
        tot[idx] += d
    # (the cut moves points only: the same move at rest; within SOFT_POS of her head only her normals are faired,
    # her points taken in less and less, so no step opens round her neck under her jaw)
    U2 = U + (S2 - S) * _ss((dh - SOFT_POS[0]) / (SOFT_POS[1] - SOFT_POS[0]), np)[:, None]
    # her normals over the faired area (and a ring round it): the faired surface's as the game shows it
    gN = _ss((SOFT_TH[1] + 10 - np.abs(th)) / (SOFT_TH[1] - SOFT_TH[0]), np) * box * \
        _ss((dh - 0.004) / 0.01, np) * _ss((SOFT_DH[3] + 0.02 - dh) / 0.03, np)
    Nc = _vn(S2, Tw, np)
    mv = np.linalg.norm(U2 - U, axis=1)
    o, moved = 0, int((mv > 1e-5).sum())
    for p, x in zip(prims, Ps):
        ix = inv[o:o + len(x)]
        o += len(x)
        G.put(p["attributes"]["POSITION"], U2[ix].astype(np.float32))
        Nr = G.get(p["attributes"]["NORMAL"]).astype(float)
        wv = gN[ix][:, None]
        Nb = Nr * (1 - wv) + Nc[ix] * wv
        Nb /= np.maximum(np.linalg.norm(Nb, axis=1, keepdims=True), 1e-12)
        G.put(p["attributes"]["NORMAL"], Nb.astype(np.float32))
    if save:
        G.save()
    print("THROAT soften: %d points of her neck taken in (inward only, as the game shows her after the %.0f mm cut), "
          "%.2f mm at most, %.2f mm mean of those; none within %.0f mm of her head (the graft's weld) in %s"
          % (moved, delta * 1000, mv.max() * 1000, mv[mv > 1e-5].mean() * 1000 if moved else 0, SOFT_POS[0] * 1000, path))
    return S2 - S, tot, U
