"""Neck + head stump skin weights fitted to Her's per-pose target (carried_target.Her.compose). Nothing is published.

fit:    per welded point of the free set (the neck region's points + head vertices with Head < 0.999; the head's ring copies
        share the body ring's point, so the seam steps 0), weights w >= 0, sum 1, over the bones spine_04 spine_05 neck_01
        neck_02 Head + any bone already over 0.01 there (no spine_04 above the ring: y > ABOVE_Y, |x| < ABOVE_X). LBS is
        linear in w: with sum 1, a point's posed position minus its target is sum_b w_b (S_b p - y), so each point brings
        the quadratic w^T H w over the 141 poses (all its copies, correctives included). Plus lam * sum over welded edges of
        |w_i - w_j|^2 / l_mm (held neighbours enter as constants: head points with Head >= 0.999 and everything outside).
        One bounded sparse LSQ (scipy lsq_linear), the sum by a stiff row, renormalised. Writes out/neck_fit/fit.npz.
check:  the six tables (module neck_fit.md). neck20: the A1 neck measures (out/neck20) under the fitted weights.
skin(V0, weights, G): LBS + the rig's correctives with any (J, W).
"""
import sys, json, time, hashlib, argparse
from pathlib import Path
import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE / "out" / "neck_fit"
POSES = HERE / "out" / "shoulder" / "poses.npz"
BONES = ["spine_04", "spine_05", "neck_01", "neck_02", "Head"]
ABOVE_Y, ABOVE_X = 1.495, 0.09            # "above the ring" (neck_diag section 7's proxy: F 0.9 at y 1482-1491)
RIGID = 0.999
MAXB = 8
FILL = ["neck_01", "spine_05", "neck_02", "Head", "spine_04"]   # added in this order
REUSE = False                             # --reuse: the cached targets whatever carried_target's bytes


def dense(J, W, nb):
    Wd = np.zeros((len(J), nb))
    np.add.at(Wd, (np.arange(len(J))[:, None], J), W)
    return Wd


def sparse_top(Wd, k=8):
    J = np.argsort(-Wd, 1)[:, :k]
    W = np.take_along_axis(Wd, J, 1)
    return J.astype(np.int64), W / W.sum(1, keepdims=True)


def skin(V0, weights, G, bd=None):
    """[n, 3] LBS of rest V0 (+ the rig's correctives of G, when V0 is B's rest) with weights (J, W) or dense [n, bones]."""
    import deform_audit as da
    bd = da.body("B") if bd is None else bd
    p = bd.p
    J, W = sparse_top(weights, max(8, int((weights > 0).sum(1).max()))) if not isinstance(weights, tuple) else weights
    P = np.array(V0, float)
    if P.shape == p.Pb.shape:
        for k, w in bd.rd.corrective_weights(p, G, bd.rig).items():
            if k in p.targets and w:
                P = P + w * p.targets[k]
    S = G @ p.skel.ibm
    Ph = np.concatenate([P, np.ones((len(P), 1))], 1)
    out = np.zeros((len(P), 3))
    for k in range(J.shape[1]):
        out += W[:, k:k + 1] * np.einsum("nij,nj->ni", S[J[:, k]][:, :3, :], Ph)
    return out


class Setup:
    def __init__(self, h):
        import carried_target as ct
        self.h, bd = h, h.bd
        self.bd, p = bd, bd.p
        self.p, I = p, p.index
        V0 = self.V0 = bd.V0
        nv, nb = len(V0), len(p.names)
        self.group, self.first = ct.weld_points(V0)
        self.group, self.first = np.asarray(self.group), np.asarray(self.first)
        self.Wd = dense(bd.J, bd.W, nb)
        self.HD = I["Head"]
        hs = self.Wd[:, sorted(set(p.subtree(self.HD)) | {self.HD})].sum(1)
        rg = h.regions["neck"]
        self.region_v = np.isin(self.group, self.group[rg.pts])
        self.head_v = p.piece == "head"
        cand = (self.region_v | self.head_v) & (hs < RIGID)
        held_pt = np.zeros(len(self.first), bool)
        np.logical_or.at(held_pt, self.group, ~cand)                     # a point is free only if every copy is
        self.free_pt = np.nonzero(~held_pt)[0]
        self.free_v = np.isin(self.group, self.free_pt)
        self.fv = np.nonzero(self.free_v)[0]
        self.loc = -np.ones(len(self.first), np.int64)
        self.loc[self.free_pt] = np.arange(len(self.free_pt))
        self.pl = self.loc[self.group[self.fv]]
        Wp = np.zeros((len(self.free_pt), nb))
        np.maximum.at(Wp, self.pl, self.Wd[self.fv])
        act = Wp > 0.01                                                  # every bone it has keeps its place
        for b in [I[x] for x in FILL]:                                   # then the neck bones while the GLB's 8 allow
            act[:, b] |= act.sum(1) < MAXB
        Vp = V0[self.first[self.free_pt]]
        self.above = (Vp[:, 1] > ABOVE_Y) & (np.abs(Vp[:, 0]) < ABOVE_X)
        act[self.above, I["spine_04"]] = False
        self.BU = np.nonzero(act.any(0))[0]
        self.act = act[:, self.BU]
        self.check_set = self.region_v | self.head_v                     # check 2's vertices: neck set + head piece
        self.cv = np.nonzero(self.check_set)[0]
        z = np.load(POSES, allow_pickle=True)
        self.G, self.names = z["G"], [str(x) for x in z["name"]]

    def key(self):
        src = (HERE / "carried_target.py").read_bytes() + POSES.read_bytes()
        return hashlib.sha1(src).hexdigest()[:16]

    def targets(self):
        """(full, neck) [poses, check-set vertices, 3] m: Her.compose(G) (every region) and compose(G, ["neck"]) (published +
        the neck's delta) on the neck set + head piece, cached by carried_target's bytes. The fit takes the neck's: the
        girdle regions' deltas (up to 80 mm on the shoulder tops the neck region reaches, x +-205 mm) are the girdle's job,
        added over the skin as compose adds them, not neck-bone weight."""
        f = OUT / "target.npz"
        k = self.key()
        if f.exists():
            z = np.load(f)
            if (str(z["key"]) == k or REUSE) and np.array_equal(z["cv"], self.cv) and "Xn" in z.files:
                return z["X"].astype(float), z["Xn"].astype(float)
        t = time.time()
        X = np.array([self.h.compose(G)[self.cv] for G in self.G], np.float32)
        Xn = np.array([self.h.compose(G, regions=["neck"])[self.cv] for G in self.G], np.float32)
        OUT.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(f, X=X, Xn=Xn, cv=self.cv, key=k)
        print(f"targets: {len(X)} poses composed in {time.time() - t:.0f}s")
        return X.astype(float), Xn.astype(float)

    def posed_rest(self, G, ids):
        P = self.p.Pb[ids].copy()
        for k, w in self.bd.rd.corrective_weights(self.p, G, self.bd.rig).items():
            if k in self.p.targets and w:
                P += w * self.p.targets[k][ids]
        return P

    def edges(self):
        """Welded edges (point ids) touching a free point, rest length mm."""
        T = self.bd.T
        e = np.unique(np.sort(self.group[np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])], 1), axis=0)
        e = e[e[:, 0] != e[:, 1]]
        e = e[(self.loc[e] >= 0).any(1)]
        l = np.linalg.norm(self.V0[self.first[e[:, 0]]] - self.V0[self.first[e[:, 1]]], axis=1) * 1000
        return e[l > 1e-3], l[l > 1e-3]


def nnls_active(A, b, rounds=60, tol=1e-9):
    """min |A x - b|^2, x >= 0, on the sparse normal equations: block active set (clamp the negatives, solve, release the
    clamped with a negative gradient, the worst first), exact solves by SuperLU. Returns x, rounds, worst KKT violation."""
    from scipy.sparse.linalg import splu
    N = (A.T @ A).tocsc()
    q = A.T @ b
    n = N.shape[0]
    F = np.ones(n, bool)
    x = np.zeros(n)
    for it in range(1, rounds + 1):
        f = np.nonzero(F)[0]
        y = splu(N[f][:, f].tocsc()).solve(q[f])
        if (y < -tol).any():
            F[f[y < -tol]] = False
            x[:] = 0
            x[f] = np.maximum(y, 0)
            continue
        x[:] = 0
        x[f] = y
        g = N @ x - q
        bad = ~F & (g < -tol * max(1.0, np.abs(q).max()))
        if not bad.any():
            return x, it, 0.0
        o = np.nonzero(bad)[0]
        F[o[np.argsort(g[o])[:max(1, len(o) // 4)]]] = True
    g = N @ x - q
    return x, rounds, float(max(0.0, -g[~F].min() if (~F).any() else 0.0, -x.min()))


def fit(S, lam=100.0, mu=1e6, verbose=True):
    _, X = S.targets()
    ci = np.searchsorted(S.cv, S.fv)                                     # free vertices inside the check set
    assert np.array_equal(S.cv[ci], S.fv), "free vertex outside the check set"
    npf, nbu = len(S.free_pt), len(S.BU)
    agg = sp.csr_matrix((np.ones(len(S.fv)), (S.pl, np.arange(len(S.fv)))), (npf, len(S.fv)))
    H = np.zeros((npf, nbu * nbu))
    t = time.time()
    for k, G in enumerate(S.G):
        Sm = (G @ S.p.skel.ibm)[S.BU]
        P = S.posed_rest(G, S.fv)
        Q = np.einsum("bij,vj->vbi", Sm[:, :3, :3], P) + Sm[:, :3, 3][None]
        D = (Q - X[k][ci][:, None, :]) * 1000                            # mm
        H += agg @ np.einsum("vbi,vci->vbc", D, D).reshape(len(D), -1)
    H = H.reshape(npf, nbu, nbu) / len(S.G)                              # mean squared mm per pose
    vid = -np.ones((npf, nbu), np.int64)
    vid[S.act] = np.arange(S.act.sum())
    nx = int(S.act.sum())
    rows, cols, vals, rhs = [], [], [], []
    r = 0
    for i in range(npf):                                                 # data: H_i = R^T R
        a = np.nonzero(S.act[i])[0]
        e, U = np.linalg.eigh(H[i][np.ix_(a, a)])
        keep = e > 1e-10 * max(e.max(), 1e-12)
        R = (np.sqrt(e[keep])[:, None] * U[:, keep].T)
        m = R.shape[0]
        rows.append(np.repeat(np.arange(r, r + m), len(a)))
        cols.append(np.tile(vid[i, a], m))
        vals.append(R.ravel())
        rhs.append(np.zeros(m))
        r += m
    E, L = S.edges()
    WpH = S.Wd[S.first][:, S.BU]                                         # held points' weights (point order)
    li, lj = S.loc[E[:, 0]], S.loc[E[:, 1]]
    c = np.sqrt(lam / L)
    for b in range(nbu):                                                 # smoothness, bone by bone
        xi = np.where(li >= 0, vid[np.maximum(li, 0), b], -2)
        xj = np.where(lj >= 0, vid[np.maximum(lj, 0), b], -2)
        ki = np.where(li >= 0, 0.0, WpH[E[:, 0], b])                    # constants: held weight; inactive free = 0
        kj = np.where(lj >= 0, 0.0, WpH[E[:, 1], b])
        use = (xi >= 0) | (xj >= 0)
        for x, s_ in ((xi, 1.0), (xj, -1.0)):
            u = use & (x >= 0)
            rr = r + np.cumsum(use)[u] - 1
            rows.append(rr), cols.append(x[u]), vals.append(s_ * c[u])
        rhs.append((-(ki - kj) * c)[use])
        r += int(use.sum())
    rows.append(np.repeat(np.arange(r, r + npf), S.act.sum(1)))           # sum to 1
    cols.append(vid[S.act]), vals.append(np.full(nx, np.sqrt(mu)))
    rhs.append(np.full(npf, np.sqrt(mu)))
    r += npf
    A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), (r, nx))
    b = np.concatenate(rhs)
    t1 = time.time()
    x, nit, kkt = nnls_active(A, b)
    Wp = np.zeros((npf, nbu))
    Wp[S.act] = x
    sdev = float(np.abs(Wp.sum(1) - 1).max())
    Wp = np.maximum(Wp, 0)
    Wp /= Wp.sum(1, keepdims=True)
    Wfull = S.Wd.copy()
    Wfull[S.fv] = 0
    Wfull[np.ix_(S.fv, S.BU)] = Wp[S.pl]
    J, W = sparse_top(Wfull[S.fv], S.bd.J.shape[1])
    lost = float((1 - np.take_along_axis(Wfull[S.fv], J, 1).sum(1)).max())
    if verbose:
        print(f"fit: {npf} free points ({len(S.fv)} vertices; {int(S.head_v[S.fv].sum())} on the head), {nx} unknowns, "
              f"bones {' '.join(S.p.names[k] for k in S.BU)}; H in {t1 - t:.0f}s, lsq {time.time() - t1:.0f}s "
              f"(active set {nit} rounds, KKT {kkt:.1e}); sum dev before renorm {sdev:.1e}; weight past top {J.shape[1]} {lost:.4f}")
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "fit.npz", ids=S.fv, J=J, W=W, points=S.free_pt, lam=lam, mu=mu, key=S.key(),
                        bones=np.array([S.p.names[k] for k in S.BU]))
    return J, W


def load_fit(bd):
    """Full (J, W) for B: today's weights with the fitted free set written in."""
    z = np.load(OUT / "fit.npz")
    nb = len(bd.p.names)
    Wd = dense(bd.J, bd.W, nb)
    Wd[z["ids"]] = dense(z["J"], z["W"], nb)
    return Wd, z


# ---------------------------------------------------------------- checks

def zones_E(V0, T):
    e = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [0, 2]]]), 1)
    E = np.unique(e, axis=0)
    E = E[(V0[E][:, :, 1] > 1.40).all(1) & (V0[E][:, :, 1] < 1.62).all(1)]
    E = E[np.linalg.norm(V0[E[:, 0]] - V0[E[:, 1]], axis=1) > 1e-5]
    m = (V0[E[:, 0]] + V0[E[:, 1]]) / 2
    x, y, zz = np.abs(m[:, 0]), m[:, 1], m[:, 2]
    Z = {"pit": (x < .025) & (y > 1.525) & (y < 1.56) & (zz > 0),
         "trap": (x >= .025) & (x <= .08) & (y > 1.50) & (y < 1.56) & (zz > .02),
         "nape": (x < .04) & (y > 1.50) & (y < 1.56) & (zz < -.08),
         "neck": (x < .12) & (y > 1.42) & (y < 1.60)}
    return E, Z


def verdict2(W, V0, T, I, SUB):
    """neck_diag VERDICT 2 on a dense W, as neck20/proxy.stats + run2 measure it."""
    E, Z = zones_E(V0, T)
    above = (V0[:, 1] > ABOVE_Y) & (np.abs(V0[:, 0]) < ABOVE_X)
    F = W[:, SUB].sum(1)
    ez = E[Z["pit"] | Z["trap"] | Z["nape"] | Z["neck"]]
    l = np.linalg.norm(V0[ez[:, 0]] - V0[ez[:, 1]], axis=1) * 1000
    g = {nm: float((np.abs(W[ez[:, 0], I[nm]] - W[ez[:, 1], I[nm]]) / l).max()) for nm in ("neck_01", "neck_02", "Head")}
    en = E[Z["neck"]]
    en = en[(np.abs(V0[en, 0]) < .07).all(1)]
    up = np.sign(V0[en[:, 1], 1] - V0[en[:, 0], 1])
    dF = (F[en[:, 1]] - F[en[:, 0]]) * up
    return {"spine_04 above ring": float(W[above, I["spine_04"]].max()), "F drop up an edge |x|<70": max(0.0, float(-dF.min())), **{f"dw/mm {k}": v for k, v in g.items()}}


def cmd_check(S):
    bd, p = S.bd, S.p
    X, Xn = S.targets()
    Wf, z = load_fit(bd)
    Jf, Wfs = sparse_top(Wf, max(8, int((Wf > 0).sum(1).max())))
    ci = np.searchsorted(S.cv, S.fv)
    T = bd.T
    e = np.unique(np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1), axis=0)
    e = e[S.check_set[e].all(1)]
    e = e[np.linalg.norm(S.V0[e[:, 0]] - S.V0[e[:, 1]], axis=1) > 1e-6]
    loc = -np.ones(len(S.V0), np.int64)
    loc[S.cv] = np.arange(len(S.cv))
    el = loc[e]
    L0 = np.linalg.norm(S.V0[e[:, 0]] - S.V0[e[:, 1]], axis=1)
    gid = S.group
    gv = np.nonzero(np.bincount(gid[S.head_v], minlength=len(S.first))[gid] & ~S.head_v)[0]   # body ring: welded to the head
    hv_of = {}
    for v in np.nonzero(S.head_v)[0]:
        hv_of.setdefault(gid[v], v)
    ring = np.array([(v, hv_of[gid[v]]) for v in gv])
    dist = {"fitted vs neck target": [], "published vs neck target": [], "fitted+deltas vs target": [], "published vs target": []}
    ed = {k: [] for k in ("fitted", "fitted+deltas", "published", "target")}
    seam = {"fitted": 0.0, "published": 0.0}
    for k, G in enumerate(S.G):
        Vp = S.h.rt.published(bd, G)
        Vf = skin(S.p.Pb, (Jf, Wfs), G, bd)
        Y = X[k]
        Vd = Vf[S.cv] + Y - Xn[k]                                         # the fitted skin + the other regions' deltas
        for nm, V, T_ in (("fitted vs neck target", Vf[S.fv], Xn[k][ci]), ("published vs neck target", Vp[S.fv], Xn[k][ci]),
                          ("fitted+deltas vs target", Vd[ci], Y[ci]), ("published vs target", Vp[S.fv], Y[ci])):
            dist[nm].append(np.linalg.norm(V - T_, axis=1) * 1000)
        for nm, V in (("fitted", Vf), ("published", Vp)):
            seam[nm] = max(seam[nm], float(np.linalg.norm(V[ring[:, 0]] - V[ring[:, 1]], axis=1).max() * 1000))
        for nm, C in (("fitted", Vf[S.cv]), ("fitted+deltas", Vd), ("published", Vp[S.cv]), ("target", Y)):
            ed[nm].append(np.linalg.norm(C[el[:, 0]] - C[el[:, 1]], axis=1) / L0)
    print(f"free set: {len(S.free_pt)} points, {len(S.fv)} vertices; check set {len(S.cv)} vertices, {len(e)} edges; "
          f"lam {float(z['lam'])}; fit key {str(z['key'])} (now {S.key()})")
    print("\n1. skin vs target on the free set, mm (mean of pose means / p95 all / max; worst 5 poses by max)")
    for nm, d in dist.items():
        d = np.array(d)
        w = np.argsort(-d.max(1))[:5]
        print(f"  {nm:24s}: {d.mean():.2f} / {np.percentile(d, 95):.2f} / {d.max():.2f} | " + ", ".join(f"{S.names[i]} {d[i].max():.1f}" for i in w))
    print("\n2. edges over 2.5x rest, neck set + head piece, 141 poses (edge-poses over; max; worst 10 edge / pose)")
    for nm, r in ed.items():
        r = np.array(r)
        o = np.argsort(-r.max(0))[:10]
        print(f"  {nm:13s}: {int((r > 2.5).sum())} over, max {r.max():.2f} | " + ", ".join(
            f"{r[:, j].max():.2f} e{e[j, 0]}-{e[j, 1]} y{S.V0[e[j], 1].mean() * 1000:.0f} {S.names[int(r[:, j].argmax())]}" for j in o))
    print(f"\n3. seam gap, max over poses (body ring {len(ring)} vertices vs their head copies), mm: fitted {seam['fitted']:.2e}, published {seam['published']:.2e}")
    hsel = S.Wd[:, S.HD] >= RIGID
    same = np.array_equal(Wf[hsel], S.Wd[hsel]) and np.array_equal(np.delete(Wf, S.fv, 0), np.delete(S.Wd, S.fv, 0))
    import deform_audit as da
    bd2 = da.Body("B") if hasattr(da, "Body") else bd
    rest_ok = np.array_equal(bd2.V0, S.V0) and np.array_equal(bd2.T, S.bd.T)
    print(f"\n4. weights array_equal where Head >= 0.999 and off the free set: {'yes' if same else 'no'}; "
          f"head rest / order unchanged (fresh load vs in memory; nothing written to the GLB): {'yes' if rest_ok else 'no'}")
    I = p.index
    SUB = sorted(set(p.subtree(I["neck_01"])) | {I["neck_01"]})
    print("\n5. VERDICT 2 (target: spine_04 0 above the ring; no F drop; dw/mm < 0.03)")
    rows = {"published": S.Wd, "fitted": Wf}
    px = HERE / "out" / "neck20" / "proxy_w.npz"
    if px.exists():
        rows["proxy n=4"] = np.load(px)["w4"].astype(float)
    for nm, W in rows.items():
        print(f"  {nm:9s}: " + " | ".join(f"{k} {v:.3f}" for k, v in verdict2(W, S.V0, S.bd.T, I, SUB).items()))
    print("\n6. A1 neck measures under the fitted weights: python tools/body/neck_fit.py neck20 (out/neck20 scripts, use(W))")


def cmd_neck20():
    """neck20's neck_01-alone sweep and seven-clip table, published vs fitted (proxy.use(W) takes dense weights)."""
    import time as _t
    sys.argv = [sys.argv[0], str(HERE / "out" / "neck20")]
    sys.path.insert(0, sys.argv[1])
    import os
    os.chdir(HERE.parent.parent)
    import proxy as px
    from scipy.spatial.transform import Rotation as Rot
    Wf, _ = load_fit(px.B)
    WS = {"published": None, "fitted": Wf}
    bm2 = {**dict(px.ct.HER["bone_map"]), "neck_01": "neck_02"}
    order2 = px.ct.transfer_order(list(px.A.p.names), px.A.p.parent, px.I, bm2, only=set(px.ct.HER["pose_bones"]) | {"Head"})[0]
    ZK = ("pit", "trap", "nape")

    def rA(G):
        Va = px.A.pose_turns(px.ct.transfer_turns(G, px.rest, px.I, px.AI, px.A.p.parent, bm2, order2))[0]
        r = np.linalg.norm(Va[px.EA[:, 0]] - Va[px.EA[:, 1]], axis=1) / px.LA0
        return np.array([r[px.ZA[k]].max() for k in ZK])

    def zb(G):
        r = px.ratio(px.pub(G))
        return np.array([r[px.Z[k]].max() for k in ZK])

    def setw(W):
        px.use_orig() if W is None else px.use(W)
    ax = px.rest[px.N2][:3, 3] - px.rest[px.N1][:3, 3]
    ax /= np.linalg.norm(ax)
    AX = {"flex": np.array([1., 0, 0]), "extend": np.array([-1., 0, 0]), "side": np.array([0, 0, 1.]), "twist": ax}
    print("neck_01 alone, pit/trap/nape: published | fitted | A (bar max(2.5, A+0.15)); largest passing angle")
    best = {}
    for an, a in AX.items():
        for d in (10, 20, 30, 40, 50, 60):
            G = px.B.p.driver.drive(px.p, px.turn_about(px.rest, px.N1, Rot.from_rotvec(a * np.radians(d)).as_matrix()), px.B.rig)[0]
            o = []
            for W in WS.values():
                setw(W)
                o.append(zb(G))
            px.use_orig()
            aa = rA(G)
            ok = bool((o[1] <= np.maximum(2.5, aa + .15)).all())
            if ok and best.get(an, -1) == d - 10 or (d == 10 and ok):
                best[an] = d
            print(f"  {an:6s} {d}: " + " | ".join("/".join(f"{x:.2f}" for x in v) for v in o + [aa]) + f" | {ok}", flush=True)
    print("  largest passing (fitted):", best)
    SS = set(px.SUB)

    def shared(G, fr):
        Ws = px.ct.world_turn(G, px.rest, px.S5)
        rv = Rot.from_matrix(px.ct.world_turn(G, px.rest, px.HD) @ Ws.T).as_rotvec()
        G2 = G.copy()
        c = 0
        for b, f in zip((px.N1, px.N2, px.HD), fr):
            c += f
            G2[b][:3, :3] = Rot.from_rotvec(rv * c).as_matrix() @ Ws @ px.rest[b][:3, :3]
            G2[b][:3, 3] = (G2[px.par[b]] @ np.linalg.inv(px.rest[px.par[b]]) @ px.rest[b])[:3, 3]
        for k in px.B.order:
            if k in SS and k not in (px.N1, px.N2, px.HD):
                G2[k] = G2[px.par[k]] @ np.linalg.inv(G[px.par[k]]) @ G[k]
        return G2
    SPL = {"keyed": None, "20/30/50": (.2, .3, .5)}
    CL = ["idle_warden_town", "iron_vow", "bladestorm_loop", "heroic_leap", "shield_charge", "run_warden", "run_warden_town"]
    print("\nseven clips, worst pit/trap/nape (frames over the bar)")
    for cn in CL:
        t = _t.time()
        d = px.da.load_clip("p4:" + cn)
        px.use_orig()
        fr = [(f, G) for f, _, G in px.B.clip_frames(d, 1)]
        bar = np.maximum(2.5, np.array([rA(G) for f, G in fr]) + .15)
        line = []
        for sn, s in SPL.items():
            Gs = [G if s is None else shared(G, s) for f, G in fr]
            for wn, W in WS.items():
                setw(W)
                R = np.array([zb(G) for G in Gs])
                line.append(f"{sn} {wn} " + "/".join(f"{x:.2f}" for x in R.max(0)) + f" ({int((R > bar).any(1).sum())})")
        px.use_orig()
        print(f"  {cn} ({len(fr)}f, {_t.time() - t:.0f}s): " + " | ".join(line), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fit", "check", "neck20"])
    ap.add_argument("--lam", type=float, default=100.0)
    ap.add_argument("--reuse", action="store_true")
    a = ap.parse_args()
    global REUSE
    REUSE = a.reuse
    if a.cmd == "neck20":
        return cmd_neck20()
    import carried_target as ct
    S = Setup(ct.Her(verbose=False))
    if a.cmd == "fit":
        fit(S, a.lam)
        cmd_check(S)
    else:
        cmd_check(S)


if __name__ == "__main__":
    main()
