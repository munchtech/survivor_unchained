"""Stage 6's two-body contact for the hip (correctives.json joint "fold": "pair"; correctives.run picks it). P1 hip r2.

The D verdict's method (judge D, 5 Nov): the thigh's front and the lower belly a zero-gap contact pair, the belly gives,
the thigh stays firm; a volume term rolling the pushed belly up above the crease; solved onward from 90 in steps of
15 deg or less, stored as in-betweens so 90-135 never falls back to raw skinning. D2's findings kept (correctives.json
hip "why"): the correction is a smooth OFFSET U = Y - X on the skinned surface X (free smoothing drifts off the
skeleton's pivot), the volume target is the skinned volume, rigid capped obstacles push the buttock (so the contact
is on the posed surface, by the check's own sides). Per side (the left; the right is its mirror), per march angle:

  X        the skinned (LBS + drivers) posed surface, welded; sides by the check's own split (bends.Strip.seg_d), so
           the solve clears what the check measures (bends.penetration: parity inside, depth to the other side)
  contact  a node inside the posed body (ray parity) or in contact at the last angle or round: q its closest point on
           the OTHER side's posed triangles, n that face's normal, s = (y - q).n; active while s < `release`
           (one-sided: never pulled in), target q + `margin` n (touching: zero gap). The trunk's nodes take the
           move (the belly gives), the thigh's `give_d` of its weight (the thigh firm)
  smooth   min |L U|^2 (the welded body's uniform Laplacian: C1 into the skin round it, no kink at the contact's
           rim) + (data (1 - f)^2 + anchor + firm on the thigh) |U|^2 (f the sphere falloff round the joint)
  volume   the belly's smooth response Z to a normal load on a band above the contact (A Z = m g: g the volume
           gradient, m = 1 within `rim_in` .. `vol_r` of the contact nodes, trunk nodes on the crease side, eased
           to 0 at both ends), added as lam Z with lam solved (secant) for the skinned volume: what the thigh
           pushes back rolls up above the crease instead of vanishing.
  march    `step` degrees from the first key to the last; each angle starts from the last one's contacts (so no
           contact is deep and its side never in doubt).
Output: [(deg, Y, f, free, M, G, log)] per key (correctives.run turns each into a rest-space shape, law "arc").
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

import bends
import ray
from contact_fold import closest_on_tris
from correctives import key_pose, smooth01, volume


def vol_grad(Y, T):
    """dV/dY per node [n,3] (welded triangles T): (1/6) sum over a node's faces of the opposite edge's cross."""
    g = np.zeros_like(Y)
    a, b, c = Y[T[:, 0]], Y[T[:, 1]], Y[T[:, 2]]
    np.add.at(g, T[:, 0], np.cross(b, c))
    np.add.at(g, T[:, 1], np.cross(c, a))
    np.add.at(g, T[:, 2], np.cross(a, b))
    return g / 6.0


def nearest_face(Y, Tc, Q, k=12):
    """Closest points on the triangles Tc (welded ids into Y) to Q: points, face normals (unit)."""
    A, B, C = Y[Tc[:, 0]], Y[Tc[:, 1]], Y[Tc[:, 2]]
    tr = cKDTree((A + B + C) / 3)
    _, cand = tr.query(Q, k=min(k, len(Tc)))
    best = np.full(len(Q), np.inf)
    qb = np.zeros_like(Q)
    fb = np.zeros(len(Q), np.int64)
    for j in range(cand.shape[1]):
        t = cand[:, j]
        q, _ = closest_on_tris(Q, A[t], B[t], C[t])
        d = np.linalg.norm(Q - q, axis=1)
        m = d < best
        best[m], qb[m], fb[m] = d[m], q[m], t[m]
    n = np.cross(B[fb] - A[fb], C[fb] - A[fb])
    return qb, n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def solve_chain(mesh, st, jc, cf):
    p = mesh.p
    I = p.index
    sub = lambda x: x.replace("{s}", st.s)
    c0 = p.rest[I[sub(jc["center"])]][:3, 3]
    d0 = np.linalg.norm(mesh.P0 - c0, axis=1)
    f = 1 - smooth01((d0 - jc["r_in"]) / (jc["r_out"] - jc["r_in"]))
    free = (d0 < jc["r_out"]) & ~mesh.held
    rn = np.zeros(mesh.n, bool)
    rn[mesh.rep[st.rend]] = True
    free &= rn
    fi = np.nonzero(free)[0]
    pos = -np.ones(mesh.n, np.int64)
    pos[fi] = np.arange(len(fi))
    # sides: the check's (seg_d by poser vertex -> welded node), its rend triangles split as bends.penetration does
    sd_n = np.zeros(mesh.n, bool)
    sd_n[mesh.rep[st.seg_d]] = True
    Tr = mesh.rep[st.T_rend]
    tri_d = sd_n[Tr].sum(1) >= 2
    T_thigh, T_trunk = Tr[tri_d], Tr[~tri_d]
    test = np.zeros(mesh.n, bool)
    test[mesh.rep[st.test]] = True
    test &= free
    # the crease side at rest (the thigh's swing: in front of its coronal plane), for the volume's band
    Gr = p.rest[I[sub(jc["distal"])]]
    crease = (mesh.P0 - Gr[:3, 3]) @ (-Gr[:3, 2]) > 0
    # the system's fixed part: |L U|^2 over the rows touching the free nodes (U = 0 off them)
    Lg = mesh.Lg
    rows = np.nonzero(np.asarray(abs(Lg[:, fi]).sum(1)).ravel() > 0)[0]
    Lrf = Lg[rows][:, fi]
    LtL = (Lrf.T @ Lrf).tocsc()
    base_w = cf["data"] * (1 - f[fi]) ** 2 + cf["anchor"] + np.where(sd_n[fi], cf.get("firm", 0.0), 0.0)
    give = np.where(sd_n[fi], cf.get("give_d", 0.2), 1.0)
    keys = [float(k[1]) for k in jc["keys"]]
    step = cf["step"]
    march = sorted(set([round(float(x), 3) for x in np.arange(keys[0], keys[-1], step)] + keys))
    out = {}
    contacts = np.zeros(mesh.n, bool)
    TW = mesh.Tw
    for th in march:
        V, G = key_pose(st, th)
        X = V[mesh.first]
        M = mesh.skin_mats(G)
        volX = volume(X, TW)
        Y = X.copy()
        lg = {"deg": th, "rounds": []}
        lam = 0.0
        for rd in range(cf["rounds"]):
            sc = ray.scene(Y[mesh.rep], p.T)
            N = bends.normals(Y[mesh.rep], p.T)[mesh.first]
            ti = np.nonzero(test)[0]
            ins = ti[ray.inside(sc, Y[ti] + 3e-4 * N[ti])]
            contacts[ins] = True
            cn = np.nonzero(contacts & free)[0]
            tgt = np.zeros((len(fi), 3))
            wc = np.zeros(len(fi))
            n_act = 0
            for side_d, Tc in ((False, T_thigh), (True, T_trunk)):
                c_ = cn[sd_n[cn] == side_d]
                if not len(c_) or not len(Tc):
                    continue
                q, nq = nearest_face(Y, Tc, Y[c_])
                s = np.einsum("ij,ij->i", Y[c_] - q, nq)
                act = s < cf["release"]
                contacts[c_[~act]] = False
                c_, q, nq = c_[act], q[act], nq[act]
                n_act += len(c_)
                k = pos[c_]
                wc[k] = cf["contact"] * give[k]
                tgt[k] = q + cf["margin"] * nq - X[c_]
            A = (LtL + sp.diags(base_w + wc)).tocsc()
            lu = splu(A)
            U = np.stack([lu.solve(wc * tgt[:, c]) for c in range(3)], 1)
            # the volume: a band on the trunk's crease side above the contact, eased; lam for the skinned volume
            Yb = X.copy()
            Yb[fi] += U
            band = np.zeros(mesh.n)
            if (wc > 0).any() and cf.get("volume", 1):
                dc, _ = cKDTree(mesh.P0[fi[wc > 0]]).query(mesh.P0[fi])
                hat = smooth01(dc / cf["rim_in"]) * (1 - smooth01((dc - cf["rim_in"]) / (cf["vol_r"] - cf["rim_in"])))
                band[fi] = hat * (~sd_n[fi]) * crease[fi] * (wc == 0)
            if band.any():
                g = vol_grad(Yb, TW)
                Z = np.stack([lu.solve(band[fi] * g[fi, c]) for c in range(3)], 1)
                v0 = volume(Yb, TW) - volX
                Yz = Yb.copy()
                Yz[fi] += Z
                v1 = volume(Yz, TW) - volX
                lam = max(0.0, -v0 / (v1 - v0)) if abs(v1 - v0) > 1e-15 else 0.0
                for _ in range(2):                      # secant on the cubic (nearly linear) volume
                    Yz = Yb.copy()
                    Yz[fi] += lam * Z
                    vl = volume(Yz, TW) - volX
                    if abs(vl) < 1e-8:
                        break
                    lam = max(0.0, lam - vl * lam / (vl - v0)) if abs(vl - v0) > 1e-15 else lam
                Y = Yz
            else:
                Y = Yb
            lg["rounds"].append({"inside": int(len(ins)), "contacts": int(n_act), "lam": round(float(lam), 3),
                                 "dvol_cm3": round((volume(Y, TW) - volX) * 1e6, 2)})
        sc = ray.scene(Y[mesh.rep], p.T)
        N = bends.normals(Y[mesh.rep], p.T)[mesh.first]
        ti = np.nonzero(test)[0]
        insf = ti[ray.inside(sc, Y[ti] + 3e-4 * N[ti])]
        lg["inside"] = int(len(insf))
        lg["inside_thigh"] = int(sd_n[insf].sum())
        lg["inside_contact"] = int(contacts[insf].sum())
        lg["max_move_mm"] = round(float(np.linalg.norm(Y - X, axis=1).max() * 1000), 1)
        r_ = lg["rounds"][-1]
        print(f"    pair {th:6.1f}: inside {lg['inside']} (thigh {lg['inside_thigh']}, in contact {lg['inside_contact']}) contacts {r_['contacts']} lam {r_['lam']} "
              f"dvol {r_['dvol_cm3']} cm3 max {lg['max_move_mm']} mm", flush=True)
        if any(abs(th - k) < 1e-6 for k in keys):
            out[round(th, 3)] = (Y.copy(), f, free, M, G, {"march": lg})
    return [(k,) + out[round(k, 3)] for k in keys]
