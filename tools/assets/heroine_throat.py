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
UP_MIN = 0.005        # (Head + neck_01 below this: her chest and shoulders, held)
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
    free = (np.abs(th) < TH_FREE) & (U[:, 1] > Y_LO) & (U[:, 1] < Y_HI) & (r < R_MAX) & (dh > HEAD_HOLD) & (up > UP_MIN)
    # biharmonic fill (uniform Laplacian squared), held at every point round the area
    n = len(U)
    e = np.r_[Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]
    e = np.r_[e, e[:, ::-1]]
    A = sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    L = (sparse.diags(np.asarray(A.sum(1)).ravel()) - A).tocsr()
    L2 = (L @ L).tocsr()
    fi, bi = np.nonzero(free)[0], np.nonzero(~free)[0]
    lu = splu(L2[fi][:, fi].tocsc())
    rhs = -(L2[fi][:, bi] @ W0[bi])
    X = W0.copy()
    used = np.nonzero(np.abs(W0[fi]).sum(0) + np.abs(rhs).sum(0) > 0)[0]
    for k in used:
        X[fi, k] = lu.solve(rhs[:, k])
    X = np.clip(X, 0, None)
    X /= np.maximum(X.sum(1, keepdims=True), 1e-12)
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
