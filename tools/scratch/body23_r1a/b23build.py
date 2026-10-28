"""Body 23 r1a: write a candidate glb from the looped body: rest move dU (welded, m), new vertices' weights refit near the
elbows (fix_weights), shapes appended (elbow_psd*); shoulder_* shapes kept as approved (arm_contour_post.psd_keep)."""
import json, struct, sys
import numpy as np
import k
from heroine_neck import _Gl
import pit_hollow_post as ph
import arm_contour_post as ac
from worn_reaver_post import _sparse
from scipy.optimize import nnls
from scipy.spatial import cKDTree

NOLD = {0: 40816, 1: 3697}     # her prims' vertex counts before arm_loops_post (old ids keep their bytes)
GIT = k.B23 + r"\loops\git.glb"


def fix_weights(radius=0.075, frames=None, log=print):
    """the loops' new points near each elbow: weights refit so that, posed at the frames, each lands where its old
    triangle's posed corners put it (least squares, non-negative, summing to 1, 8 kept). Returns {welded: (J, W)}"""
    bs = k.base()
    frames = frames or k.FRAMES
    g0 = k.h.GlbBody(GIT)
    # old triangles of her body prim 0 (the elbows are there)
    G0 = _Gl(GIT)
    mesh = G0.g["meshes"][[n for n in G0.g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    p0 = mesh["primitives"][bs.kidx[0]]
    F0 = G0.get(p0["indices"]).reshape(-1, 3).astype(int)
    P0 = g0.prims[bs.kidx[0]]["P"]
    Pn = bs.gb.prims[bs.kidx[0]]["P"]
    new = np.arange(NOLD[0], len(Pn))
    E = {sd: bs.J["lowerarm_" + sd] for sd in "lr"}
    near = np.zeros(len(new), bool)
    for sd in "lr":
        near |= np.linalg.norm(Pn[new] - E[sd], axis=1) < radius
    new = new[near]
    # old triangle and barycentrics of each new point
    C = P0[F0].mean(1)
    _, cand = cKDTree(C).query(Pn[new], k=16)
    tri = np.zeros(len(new), int); bar = np.zeros((len(new), 3)); best = np.full(len(new), np.inf)
    for c in range(cand.shape[1]):
        f = F0[cand[:, c]]
        a, b, cc = P0[f[:, 0]], P0[f[:, 1]], P0[f[:, 2]]
        v0, v1, v2 = b - a, cc - a, Pn[new] - a
        d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
        den = d00 * d11 - d01 * d01
        l1 = (d11 * d20 - d01 * d21) / den; l2 = (d00 * d21 - d01 * d20) / den; l0 = 1 - l1 - l2
        L = np.clip(np.c_[l0, l1, l2], 0, 1); L /= L.sum(1, keepdims=True)
        q = L[:, :1] * a + L[:, 1:2] * b + L[:, 2:3] * cc
        d = np.linalg.norm(q - Pn[new], axis=1)
        m = d < best
        best[m], tri[m], bar[m] = d[m], cand[m, c], L[m]
    log("fix_weights: %d new points near the elbows, on their old triangles within %.2e m" % (len(new), best.max()))
    # per frame: bone skin matrices (3x4) and posed old points (dump rows of prim 0)
    G = bs.G
    pn = bs.gb.prims[bs.kidx[0]]
    gp = G.g["meshes"][[n for n in G.g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]["primitives"][bs.kidx[0]]
    Jt = np.hstack([G.get(gp["attributes"]["JOINTS_0"]), G.get(gp["attributes"]["JOINTS_1"])]).astype(int)
    Wt = np.hstack([G.get(gp["attributes"]["WEIGHTS_0"]), G.get(gp["attributes"]["WEIGHTS_1"])]).astype(float)
    if Wt.max() > 1.5:
        Wt = Wt / (255.0 if Wt.max() <= 255 else 65535.0)
    rows = {i: [] for i in range(len(new))}
    for f in frames:
        fr = k.frame(f)
        sf = [i for i, (kk, j, _) in enumerate(fr.mp) if kk == bs.kidx[0]][0]
        A = fr.dump["surfs"][sf]["A"]; j = fr.mp[sf][1]
        posed = np.full((len(Pn), 3), np.nan); posed[j] = A[:, 0:3]
        sh = k.shapes_of(fr, extra=False)
        Xr = Pn.copy()
        for n, w in sh.items():
            if w and n in pn["T"]:
                Xr = Xr + w * pn["T"][n]
        nb = len(fr.bnames)
        # skin matrices S_b = Gs_b @ ibm_b
        S = np.stack([fr.Gs[b] @ bs.ibm[bs.names.index(fr.bnames[b])] for b in range(nb)])
        tgt = (bar[:, :, None] * posed[F0[tri]]).sum(1)
        for i, v in enumerate(new):
            rows[i].append((S, Xr[v], tgt[i]))
    out = {}
    worst0, worst1 = 0.0, 0.0
    for i, v in enumerate(new):
        cb = np.unique(np.r_[Jt[F0[tri[i]]].ravel()])
        cb = cb[(Wt[F0[tri[i]]].ravel()[np.argsort(Jt[F0[tri[i]]].ravel(), kind="stable")] >= 0).any() and slice(None)] if False else cb
        Arows, b = [], []
        for S, x, t in rows[i]:
            if not np.isfinite(t).all():
                continue
            Ab = np.stack([S[j][:3, :3] @ x + S[j][:3, 3] for j in cb], 1)    # 3 x nb
            Arows.append(Ab); b.append(t)
        if not Arows:
            continue
        Am = np.vstack(Arows) * 1000; bb = np.concatenate(b) * 1000
        lam = 200.0
        Am2 = np.vstack([Am, lam * np.ones((1, len(cb)))]); bb2 = np.r_[bb, lam]
        # the current (interpolated) weights, as a prior
        wcur = np.zeros(len(cb))
        jj = Jt[v]; ww = Wt[v]
        for a_, b_ in zip(jj, ww):
            if b_ > 0 and a_ in cb:
                wcur[list(cb).index(a_)] += b_
        r0 = np.abs(Am @ wcur - bb).reshape(-1, 3)
        mu = 0.3
        Am3 = np.vstack([Am2, mu * np.eye(len(cb))]); bb3 = np.r_[bb2, mu * wcur]
        w, _ = nnls(Am3, bb3)
        if (w > 0).sum() > 8:
            keep = np.argsort(-w)[:8]; w2 = np.zeros_like(w); w2[keep] = w[keep]; w = w2
        w /= w.sum()
        r1 = np.abs(Am @ w - bb).reshape(-1, 3)
        e0, e1 = np.linalg.norm(r0, axis=1).max(), np.linalg.norm(r1, axis=1).max()
        worst0, worst1 = max(worst0, e0), max(worst1, e1)
        if e1 < e0:
            out[int(bs.wid[bs.offs[0] + v])] = (cb, w, int(v))
    log("fix_weights: posed drift at the frames (max over points and frames) %.2f -> %.2f mm; %d refit" % (worst0, worst1, len(out)))
    return out


def write(dst, dU=None, shapes=None, weights=None, src=k.LOOPS, extras=None, log=print):
    G = _Gl(src)
    g = G.g
    b = ph.Body(G)
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    dU = np.zeros_like(b.U) if dU is None else dU
    n0 = ph.vn(b.U, b.F)
    n1 = ph.vn(b.U + dU, b.F)
    o = 0
    for pi, p in enumerate(prims):
        ai, ni = p["attributes"]["POSITION"], p["attributes"]["NORMAL"]
        X = G.get(ai).astype(float)
        w = b.wid[o:o + len(X)]
        o += len(X)
        X = X + dU[w]
        Nn = G.get(ni).astype(float) + (n1 - n0)[w]
        Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
        G.put(ai, X.astype(np.float32)); G.put(ni, Nn.astype(np.float32))
        g["accessors"][ai]["min"] = X.min(0).astype(np.float32).tolist()
        g["accessors"][ai]["max"] = X.max(0).astype(np.float32).tolist()
        if weights and pi == 0:
            j0, j1 = p["attributes"]["JOINTS_0"], p["attributes"]["JOINTS_1"]
            w0, w1 = p["attributes"]["WEIGHTS_0"], p["attributes"]["WEIGHTS_1"]
            Jt = np.hstack([G.get(j0), G.get(j1)]); Wt = np.hstack([G.get(w0), G.get(w1)])
            scale = 1.0
            if np.issubdtype(Wt.dtype, np.integer):
                scale = 255.0 if Wt.dtype.itemsize == 1 else 65535.0
            for u, (cb, wv, v) in weights.items():
                order = np.argsort(-wv)[:8]
                jj = np.zeros(8, int); ww = np.zeros(8)
                jj[:len(order)] = cb[order]; ww[:len(order)] = wv[order]
                if scale != 1.0:
                    q = np.round(ww * scale); q[0] += scale - q.sum(); ww = q
                Jt[v] = jj; Wt[v] = ww
            G.put(j0, Jt[:, :4].astype(Jt.dtype)); G.put(j1, Jt[:, 4:].astype(Jt.dtype))
            G.put(w0, Wt[:, :4].astype(Wt.dtype)); G.put(w1, Wt[:, 4:].astype(Wt.dtype))
    rep = {}
    ac.psd_keep(G, prims, b.wid, dU, n1 - n0, rep)
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    names = mesh.setdefault("extras", {}).setdefault("targetNames", [])
    U2 = b.U + dU
    for name, D in (shapes or {}).items():
        dN = ph.vn(U2 + D, b.F) - ph.vn(U2, b.F)
        o = 0
        for p in prims:
            n = g["accessors"][p["attributes"]["POSITION"]]["count"]
            w = b.wid[o:o + n]
            Dp = D[w]
            Ns = G.get(p["attributes"]["NORMAL"]).astype(float)
            Nn = Ns + dN[w]
            Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
            dNp = np.where((np.abs(dN[w]).max(1) > 1e-5)[:, None], Nn - Ns, 0)
            ip = np.nonzero(np.abs(Dp).max(1) > 0)[0]
            inn = np.nonzero(np.abs(dNp).max(1) > 0)[0]
            p.setdefault("targets", []).append({"POSITION": _sparse(g, binb, n, ip, Dp[ip]),
                                                "NORMAL": _sparse(g, binb, n, inn, dNp[inn])})
            o += n
        names.append(name)
        mesh["weights"] = list(mesh.get("weights", [])) + [0]
    g.setdefault("asset", {}).setdefault("extras", {})["body23_r1a"] = extras or {}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    log("written %s (psd kept: %s)" % (dst, ", ".join("%s %d/%.1f" % (kk, v[0], v[1]) for kk, v in rep.items() if v[0])))
