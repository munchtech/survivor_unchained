"""One subdivision of a quad mesh as her shipped head was made (tools/assets/heroine_head.py `subdivide`, the same
rules, vectorised): every face quartered (a point at its middle and at each edge's), then smoothed as Catmull and
Clark smooth, each original point and edge point by its own amount (`smooth`, 0..1; none on the mesh's open edge),
all of it one sparse matrix linear in the base points, so shape keys and weights go through it alike.

    Sub, F2, U2 = subdivide(nV, F, U, smooth)      # Sub [n2, nV] csr; points2 = Sub @ points
The new points' order (heroine_head.py's): the used original points (sorted), then per face its middle followed by
the new edge points it is the first to meet, in its corners' order.
"""
import numpy as np
import scipy.sparse as sp


def subdivide(nV, F, U, smooth=None):
    F = np.asarray(F, np.int64)
    nF, k = F.shape
    assert k == 4, "quads"
    used = np.unique(F)
    nu = len(used)
    idx = -np.ones(nV, np.int64)
    idx[used] = np.arange(nu)
    a, b = F, np.roll(F, -1, 1)                                   # edge i: corner i -> i+1
    key = np.minimum(a, b) * nV + np.maximum(a, b)
    flat = key.ravel()
    ukeys, first, inv = np.unique(flat, return_index=True, return_inverse=True)
    order = np.argsort(first, kind="stable")                      # edges by first meeting
    rank = np.empty(len(ukeys), np.int64)
    rank[order] = np.arange(len(ukeys))
    eid = rank[inv.ravel()].reshape(nF, 4)                        # each face edge's edge number (first-meet order)
    # numbering: per face its middle, then the edges it meets first (in corner order)
    newe = np.zeros((nF, 4), bool)
    fl = np.arange(nF * 4).reshape(nF, 4)
    newe.ravel()[first] = True
    cnt = 1 + newe.sum(1)
    start = nu + np.concatenate([[0], np.cumsum(cnt)[:-1]])
    cpt = start                                                   # face middle's number
    pos = np.cumsum(newe, 1) * newe                               # 1.. for new edges within the face
    enum = np.zeros(len(ukeys), np.int64)
    sel = newe
    enum[eid[sel]] = (start[:, None] + pos)[sel]
    n2 = nu + nF + len(ukeys)
    emid = enum[eid]                                              # [nF,4] edge point numbers
    ek = ukeys[order]                                             # edge keys in edge-number order
    ea, eb = ek // nV, ek % nV
    # linear rows
    rows = [np.arange(nu), np.repeat(cpt, 4), np.repeat(enum[np.arange(len(ukeys))], 2)]
    cols = [used, F.ravel(), np.stack([ea, eb], 1).ravel()]
    vals = [np.ones(nu), np.full(nF * 4, 0.25), np.full(2 * len(ukeys), 0.5)]
    Sub = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n2, nV))
    F2 = np.stack([idx[F], emid, np.repeat(cpt[:, None], 4, 1), np.roll(emid, 1, 1)], 2).reshape(-1, 4)
    U = np.asarray(U, float)
    cuv = U.mean(1, keepdims=True)
    U2 = np.stack([U, (U + np.roll(U, -1, 1)) / 2, np.repeat(cuv, 4, 1), (np.roll(U, 1, 1) + U) / 2], 2).reshape(-1, 4, 2)
    if smooth is None:
        return Sub, F2, U2
    smooth = np.asarray(smooth, float)
    # incidence
    nfe = np.bincount(eid.ravel(), minlength=len(ukeys))          # faces per edge (by edge number)
    bnd = np.zeros(nV, bool)
    be = nfe < 2
    bnd[ea[be]] = True
    bnd[eb[be]] = True
    FP = sp.csr_matrix((np.full(nF * 4, 0.25), (np.repeat(np.arange(nF), 4), F.ravel())), shape=(nF, nV))
    VF = sp.csr_matrix((np.ones(nF * 4), (F.ravel(), np.repeat(np.arange(nF), 4))), shape=(nV, nF))
    nf = np.asarray(VF.sum(1)).ravel()
    Adj = sp.csr_matrix((np.ones(2 * len(ek)), (np.concatenate([ea, eb]), np.concatenate([eb, ea]))), shape=(nV, nV))
    nn = np.asarray(Adj.sum(1)).ravel()
    nn_ = np.maximum(nn, 1)
    # Catmull-Clark vertex point: mean of face points / n + 2 * mean of edge midpoints / n + (n - 3) / n * self
    Vfac = sp.diags(1.0 / np.maximum(nf, 1) / nn_) @ VF @ FP
    Vedg = sp.diags(1.0 / nn_ ** 2) @ (sp.diags(nn) + Adj)
    Vown = sp.diags((nn - 3.0) / nn_)
    CCv = (Vfac + Vedg + Vown).tocsr()
    w = np.where(bnd, 0.0, smooth)
    w = np.where(np.isin(np.arange(nV), used), w, 0.0)
    # edge point: (a + b) / 4 + the two face points / 4
    two = np.where(nfe == 2)[0]
    fe = np.argsort(eid.ravel(), kind="stable")                   # face-corner slots by edge number
    se = eid.ravel()[fe]
    startp = np.searchsorted(se, two)
    f0, f1 = fe[startp] // 4, fe[startp + 1] // 4
    we = np.minimum(smooth[ea[two]], smooth[eb[two]])
    keep = we > 0
    two, f0, f1, we = two[keep], f0[keep], f1[keep], we[keep]
    E2 = sp.csr_matrix((np.full(len(two) * 2, 0.25), (np.repeat(np.arange(len(two)), 2),
                        np.stack([ea[two], eb[two]], 1).ravel())), shape=(len(two), nV))
    sel0 = sp.csr_matrix((np.full(len(two), 0.25), (np.arange(len(two)), f0)), shape=(len(two), nF))
    sel1 = sp.csr_matrix((np.full(len(two), 0.25), (np.arange(len(two)), f1)), shape=(len(two), nF))
    CCe = (E2 + (sel0 + sel1) @ FP).tocsr()
    # blend the rows
    D = np.ones(n2)
    vr = idx[used]
    D[vr] = 1 - w[used]
    er = enum[two]
    D[er] = 1 - we
    Out = sp.diags(D) @ Sub
    Rv = sp.csr_matrix((np.ones(nu), (vr, np.arange(nu))), shape=(n2, nu)) @ (sp.diags(w[used]) @ CCv[used])
    Re = sp.csr_matrix((np.ones(len(two)), (er, np.arange(len(two)))), shape=(n2, len(two))) @ (sp.diags(we) @ CCe)
    Out = (Out + Rv + Re).tocsr()
    Out.eliminate_zeros()
    Out.sort_indices()
    return Out, F2, U2
