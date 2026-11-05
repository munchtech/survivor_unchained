"""Stage 6's stepped contact fold (correctives.json joint "fold": "stepped"; correctives.run picks it).

Made for the hip (P1 D2, from the max judge's D verdict: "a contact pair with zero gap, the belly gives, the thigh
stays firm; a volume term rolling the pushed belly up above the crease; solved onward from 90 in steps of 15 deg or
less, stored as in-between shapes so 90-135 never falls back to raw skinning; the rest curvature kept over the hip
band; the midline and perineum against the inner thigh and the other thigh"). The method, per side (the left; the
right is its mirror):

  march    the pose is walked from `start` to the last key in `step` degree substeps (bends.Strip's pose at each
           absolute angle, the rig's drivers, no shapes); each substep starts from the last one's result carried
           to the new pose (its rest-space delta re-skinned), so a contact is never deep and its side never in
           doubt (from raw skinning at 135 the thigh is 75 mm inside the belly: no nearest surface is the right one);
  solve    the smooth-skin energy of correctives.solve_key (ARAP over the joint's sphere: each node's rest edges,
           turned by its best rotation, scaled by the volume field; falloff to the skinned surface at the sphere's
           edge), with
  contact  a persistent, two-sided, zero-gap contact on the POSED surface: a node found inside the posed body (ray
           parity: robust at any depth) or already in contact is matched to the nearest posed triangle that was
           over `far_m` away at rest (the other side of the fold); its signed distance s to it is driven to
           `margin` (0.3 mm: touching), the move shared by softness: the node takes give = soft_i / (soft_i +
           soft_t) of it, the triangle's nodes the rest by their barycentrics (a node off the sphere: soft 0, an
           obstacle: the other thigh); a contact stays while s < `release` (the surfaces meet and stay met: no slit)
           and its weight eases out from s = margin to s = release (no edge at the contact's rim: no kink);
  soft     trunk 1 (the belly gives), the limb `soft_d` (the thigh firm), the midline within `mid_m` of x = 0 below
           the joint's height + `mid_dy` `soft_mid` (the perineum held: the inner thigh gives there);
  volume   the rest edges scaled by 1 + kap g on the soft side round the contact (g a hat over the distance to the
           nearest contact node: 0 on it, 1 at `rim_in`, 0 again at `vol_r`): the belly the thigh pushed back rolls
           up beside the crease; kap solved (secant) for the rest volume, at most `kap_max`.
Output: per key in jc["keys"] (absolute degrees, in the march), the welded Y, f, free, the skin matrices, the bone
worlds and a log; correctives.run turns each into a shape (rest-space delta) and the "arc" weight law (rig_drive.py).
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

import bends
import ray
from correctives import key_pose, polar, smooth01, volume


def closest_on_tris(p, a, b, c):
    """Closest points on triangles (a, b, c) to points p (all [k,3]): the points and their barycentrics [k,3]
    (Ericson's Voronoi regions, vectorized)."""
    dot = lambda x, y: np.einsum("ij,ij->i", x, y)
    ab, ac, ap = b - a, c - a, p - a
    bp, cp = p - b, p - c
    d1, d2, d3, d4, d5, d6 = dot(ab, ap), dot(ac, ap), dot(ab, bp), dot(ac, bp), dot(ab, cp), dot(ac, cp)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    den = va + vb + vc
    den = np.where(np.abs(den) < 1e-30, 1e-30, den)
    v, w = vb / den, vc / den
    bc = np.stack([1 - v - w, v, w], 1)
    sdiv = lambda x, y: x / np.where(np.abs(y) < 1e-30, 1e-30, y)
    m = (va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0)
    t = sdiv(d4 - d3, (d4 - d3) + (d5 - d6))
    bc[m] = np.stack([0 * t, 1 - t, t], 1)[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    t = sdiv(d2, d2 - d6)
    bc[m] = np.stack([1 - t, 0 * t, t], 1)[m]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    t = sdiv(d1, d1 - d3)
    bc[m] = np.stack([1 - t, t, 0 * t], 1)[m]
    for m, k in (((d6 >= 0) & (d5 <= d6), 2), ((d3 >= 0) & (d4 <= d3), 1), ((d1 <= 0) & (d2 <= 0), 0)):
        e = np.zeros(3)
        e[k] = 1
        bc[m] = e
    q = bc[:, :1] * a + bc[:, 1:2] * b + bc[:, 2:] * c
    return q, bc


def far_match(Y, P0, Tw, nodes, far_m, k=64):
    """Each node's nearest posed triangle over far_m away at rest (every corner): signed distance (+ outside, along
    the triangle's normal), the triangle, its barycentrics and normal; nan where none is in reach."""
    C = Y[Tw].mean(1)
    kk = min(k, len(Tw))
    _, ti = cKDTree(C).query(Y[nodes], k=kk)
    best = np.full(len(nodes), np.inf)
    out_s = np.full(len(nodes), np.nan)
    out_t = np.full(len(nodes), -1)
    out_b = np.zeros((len(nodes), 3))
    out_n = np.zeros((len(nodes), 3))
    for c in range(kk):
        t = ti[:, c]
        tri = Tw[t]
        rest_far = (np.linalg.norm(P0[tri] - P0[nodes][:, None], axis=2) > far_m).all(1)
        a, b, cc = Y[tri[:, 0]], Y[tri[:, 1]], Y[tri[:, 2]]
        q, bc = closest_on_tris(Y[nodes], a, b, cc)
        dist = np.linalg.norm(Y[nodes] - q, axis=1)
        nrm = np.cross(b - a, cc - a)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-15)
        ok = rest_far & (dist < best)
        best[ok] = dist[ok]
        out_s[ok] = np.einsum("ij,ij->i", Y[nodes][ok] - q[ok], nrm[ok])
        out_t[ok], out_b[ok], out_n[ok] = t[ok], bc[ok], nrm[ok]
    return out_s, out_t, out_b, out_n


def limb_solid(mesh, wd):
    """The limb as a closed solid at rest: the welded triangles whose corners all carry the limb's chain at >= 0.5,
    each open loop (the limb's root, where its weight crosses 0.5) closed by a fan from its centroid. Returns the
    skin triangles, the cap triangles (centre index mesh.n + loop number) and the loops."""
    Tw = mesh.Tw
    sk = Tw[(wd[Tw] >= 0.5).all(1)]
    e = np.concatenate([sk[:, [0, 1]], sk[:, [1, 2]], sk[:, [2, 0]]])
    key = np.sort(e, 1)
    _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    bnd = e[cnt[inv.ravel()] == 1]          # directed boundary edges (each skin triangle's own winding)
    nxt = {int(a): int(b) for a, b in bnd}
    caps, loops, seen = [], [], set()
    for a0 in list(nxt):
        if a0 in seen:
            continue
        loop, a = [], a0
        while a not in seen and a in nxt:
            seen.add(a)
            loop.append(a)
            a = nxt[a]
        if len(loop) < 3:
            continue
        c = mesh.n + len(loops)
        loops.append(loop)
        for i in range(len(loop)):          # the cap wound against the loop's skin: outward
            caps.append([loop[(i + 1) % len(loop)], loop[i], c])
    return sk, np.asarray(caps, np.int64).reshape(-1, 3), loops


def solid_points(Pn, loops):
    return np.concatenate([Pn] + [Pn[l].mean(0, keepdims=True) for l in loops]) if loops else Pn


def nearest_on(Ps, Tsk, tr, Q, k=16):
    """Nearest point on the skin triangles Tsk (over points Ps; tr a cKDTree of their centroids) to points Q: the
    point, the triangle's outward normal and the distance."""
    kk = min(k, len(Tsk))
    _, ti = tr.query(Q, k=kk)
    best = np.full(len(Q), np.inf)
    qb, nb = np.zeros_like(Q), np.zeros_like(Q)
    for c in range(kk):
        tri = Tsk[ti[:, c]]
        a, b, cc = Ps[tri[:, 0]], Ps[tri[:, 1]], Ps[tri[:, 2]]
        q, _ = closest_on_tris(Q, a, b, cc)
        dist = np.linalg.norm(Q - q, axis=1)
        nrm = np.cross(b - a, cc - a)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-15)
        ok = dist < best
        best[ok], qb[ok], nb[ok] = dist[ok], q[ok], nrm[ok]
    return qb, nb, best


def solve_chain(mesh, st, jc, cf):
    """[(deg, Y, f, free, M, G, log)] for each key of jc["keys"] (absolute degrees), marched from cf["start"]."""
    p = mesh.p
    I = p.index
    sub = lambda x: x.replace("{s}", st.s)
    c0 = p.rest[I[sub(jc["center"])]][:3, 3]
    d = np.linalg.norm(mesh.P0 - c0, axis=1)
    f = 1 - smooth01((d - jc["r_in"]) / (jc["r_out"] - jc["r_in"]))
    free = (d < jc["r_out"]) & ~mesh.held
    if jc.get("free_rend"):
        rn = np.zeros(mesh.n, bool)
        rn[mesh.rep[st.rend]] = True
        free &= rn
    fi = np.nonzero(free)[0]
    pos = -np.ones(mesh.n, np.int64)
    pos[fi] = np.arange(len(fi))
    jd = I[sub(jc["distal"])]
    wd = p.D[:, p.subtree(jd)].sum(1)[mesh.first]
    Tsk, Tcap, loops = limb_solid(mesh, wd)
    Tsol = np.concatenate([Tsk, Tcap])
    prox = fi[(wd[fi] < 0.5) & (f[fi] > 0.02)]          # the side that gives (the trunk)
    # the crease side only (toward where the limb swings: the front of the hip); behind, the skin stretches over
    # the limb's rigid shape (the buttock), it is not a contact
    je = I[sub(jc["distal_end"])]
    Vk, Gk = key_pose(st, float(jc["keys"][-1][1]))
    bdir = bends.unit(bends.unit(Gk[je][:3, 3] - Gk[jd][:3, 3]) - bends.unit(p.rest[je][:3, 3] - p.rest[jd][:3, 3]))
    prox = prox[(mesh.P0[prox] - c0) @ bdir > cf.get("side_min", 0.0)]
    if loops and cf.get("root_m", 0):       # not the root's own skin: the cap closes the solid there, not skin
        lp = np.concatenate([np.asarray(l) for l in loops])
        prox = prox[cKDTree(mesh.P0[lp]).query(mesh.P0[prox])[0] > cf["root_m"]]
    dist_ = fi[(wd[fi] >= 0.5) & (f[fi] > 0.02)]        # the firm limb
    sx = 1.0 if st.s == "l" else -1.0
    posed = cf.get("obstacle") == "posed"   # contacts on the posed surface itself (both sides, by softness)
    test = fi[f[fi] > 0.02]
    sj = jc.get("soft", {})
    soft = np.where(wd >= 0.5, sj.get("d", 0.2), sj.get("p", 1.0))
    if "mid" in sj:                         # [soft, half-width m, ease m, height above the joint m]
        s_m, mid_m, mid_w, mid_dy = sj["mid"]
        mm_ = (1 - smooth01((np.abs(mesh.P0[:, 0]) - mid_m) / mid_w)) * (1 - smooth01((mesh.P0[:, 1] - c0[1] - mid_dy) / mid_w))
        soft = soft * (1 - mm_) + s_m * mm_
    soft = np.where(free, soft, 0.0)
    mid = jc.get("mid_wall")                # m: the limb's own nodes kept on its side of x = 0 (the other thigh)
    a_data = cf["data"] * (1 - f[fi]) ** 2 + cf["anchor"]
    Lg = mesh.Lg
    rows = np.nonzero(np.asarray(abs(Lg[:, fi]).sum(1)).ravel() > 0)[0]
    Lr = Lg[rows]
    Lrf, Lrx = Lr[:, fi], Lr[:, ~free]
    LtL = (Lrf.T @ Lrf).tocsc()
    keys = [float(k[1]) for k in jc["keys"]]
    step = cf["step"]
    start = cf.get("start", 0.0)
    march = list(np.arange(start, keys[-1], step)[1:]) + keys
    march = sorted(set(round(float(x), 3) for x in march if x > start))
    out = {}
    Dw = None
    contacts = set()
    kap = 0.0
    hm = None
    for th in march:
        V, G = key_pose(st, th)
        X = V[mesh.first]
        M = mesh.skin_mats(G)
        Mw = M[mesh.first]
        Y = X.copy()
        if Dw is not None:
            ph = np.concatenate([mesh.P0[fi] + Dw, np.ones((len(fi), 1))], 1)
            Y[fi] = np.einsum("nij,nj->ni", Mw[fi], ph)[:, :3]
        Xfix = X[~free]
        volX = volume(X, mesh.Tw)           # the skinned surface's volume (its overlap counted twice: each part's own)
        # the limb's rigid solid at this pose
        Sd = G[jd] @ p.skel.ibm[jd]
        Pr = mesh.P0 @ Sd[:3, :3].T + Sd[:3, 3]
        Ps = solid_points(Pr, loops)
        sc_sol = ray.scene(Ps, Tsol)
        tr_sk = cKDTree(Ps[Tsk].mean(1))
        if jc.get("hold_mid"):
            band_m, w_m, hb = jc["hold_mid"]
            Sh = G[I[hb]] @ p.skel.ibm[I[hb]]
            Xh = mesh.P0 @ Sh[:3, :3].T + Sh[:3, 3]
            hm = w_m * (1 - smooth01(np.abs(mesh.P0[:, 0]) / band_m)) * (f > 0.02)
        hist, gvol = [], None
        lg = {"deg": th, "rounds": []}
        for rnd in range(cf["rounds"] + 1):
            # the giving side: out of the limb's solid (inside by parity: any depth), or still touching it
            if posed:
                Vall = Y[mesh.rep]
                Np = bends.normals(Vall, p.T)[mesh.first]
                insp = test[ray.inside(ray.scene(Vall, p.T), Y[test] + cf["probe"] * Np[test])]
            else:
                insp = prox[ray.inside(sc_sol, Y[prox])]
            if rnd == cf["rounds"]:
                lg["inside_solid"] = int(len(insp))
                break
            contacts |= set(insp.tolist())
            cn = np.array(sorted(contacts), np.int64)
            W = a_data.copy()
            tgt = a_data[:, None] * X[fi]
            if hm is not None:
                W += hm[fi]
                tgt += hm[fi, None] * Xh[fi]
            n_act = 0
            if len(cn) and posed:
                s_, t_, b_, n_ = far_match(Y, mesh.P0, mesh.Tw, cn, cf["far_m"])
                keep = np.isfinite(s_) & (s_ < cf["release"])
                contacts = set(cn[keep].tolist())
                cn, s_, t_, b_, n_ = cn[keep], s_[keep], t_[keep], b_[keep], n_[keep]
                n_act = len(cn)
                tri = mesh.Tw[t_]
                st_ = (b_ * soft[tri]).sum(1)
                give = np.where(soft[cn] + st_ > 0, soft[cn] / np.maximum(soft[cn] + st_, 1e-9), 0.0)
                mv = cf["margin"] - s_
                ease = 1 - smooth01((s_ - cf["margin"]) / max(cf["release"] - cf["margin"], 1e-9))
                wc = cf["contact"] * np.where(s_ <= cf["margin"], 1.0, ease)
                acc_w = np.zeros(mesh.n)
                acc_t = np.zeros((mesh.n, 3))
                np.add.at(acc_w, cn, wc * np.maximum(give, 1e-3))
                np.add.at(acc_t, cn, (wc * np.maximum(give, 1e-3))[:, None] * (Y[cn] + (give * mv)[:, None] * n_))
                for k in range(3):
                    j = tri[:, k]
                    wj = wc * b_[:, k] * (1 - give)
                    np.add.at(acc_w, j, wj)
                    np.add.at(acc_t, j, wj[:, None] * (Y[j] - ((1 - give) * mv)[:, None] * n_))
                on = np.nonzero((acc_w > 0) & free)[0]
                W[pos[on]] += acc_w[on]
                tgt[pos[on]] += acc_t[on]
            elif len(cn):
                q, nq, dist = nearest_on(Ps, Tsk, tr_sk, Y[cn])
                sd = np.einsum("ij,ij->i", Y[cn] - q, nq)
                sd = np.where(np.isin(cn, insp), -dist, sd)
                keep = sd < cf["release"]
                contacts = set(cn[keep].tolist())
                cn, q, nq, sd = cn[keep], q[keep], nq[keep], sd[keep]
                n_act = len(cn)
                ease = 1 - smooth01((sd - cf["margin"]) / (cf["release"] - cf["margin"]))
                wc = cf["contact"] * np.where(sd <= cf["margin"], 1.0, ease)
                W[pos[cn]] += wc
                tgt[pos[cn]] += wc[:, None] * (q + cf["margin"] * nq)
            # the firm limb: its own skin not inside its rigid shape (the lagging blend pushed out to it)
            insd = dist_[:0]
            if cf.get("firm", 0) and len(cn):         # only where the trunk touches (the blend behind stretches)
                near = dist_[cKDTree(Y[cn]).query(Y[dist_])[0] < cf["firm_r"]]
                insd = near[ray.inside(sc_sol, Y[near])] if len(near) else near
            if len(insd):
                q, nq, _ = nearest_on(Ps, Tsk, tr_sk, Y[insd])
                W[pos[insd]] += cf["firm"]
                tgt[pos[insd]] += cf["firm"] * q
            if mid is not None:
                own = dist_[(Y[dist_, 0] * sx) < mid]
                if len(own):
                    W[pos[own]] += cf["contact"]
                    t_ = Y[own].copy()
                    t_[:, 0] = sx * mid
                    tgt[pos[own]] += cf["contact"] * t_
            # volume: the giving side round the contact pushed out along its normals by kap g (m), kap solved
            # (secant) so the corrected surface keeps the skinned one's volume (the overlap was each part's own)
            if cf.get("volume", 0) and rnd > 0 and len(cn):
                dv = volume(Y, mesh.Tw) - volX
                hist.append((kap, dv))
                if len(hist) == 1 or abs(hist[-1][1] - hist[-2][1]) < 1e-12:
                    kap = kap + (cf["kap_step"] if dv < 0 else -cf["kap_step"])
                else:
                    (k0, v0), (k1, v1) = hist[-2], hist[-1]
                    kap = k1 - v1 * (k1 - k0) / (v1 - v0)
                kap = float(np.clip(kap, 0.0, cf["kap_max"]))
                dc, _ = cKDTree(Y[cn]).query(Y)
                gvol = np.where(dc < cf["rim_in"], smooth01(dc / cf["rim_in"]),
                                1 - smooth01((dc - cf["rim_in"]) / (cf["vol_r"] - cf["rim_in"])))
                gvol = gvol * (wd < 0.5) * f
                gvol[cn] = 0.0
            # the correction U = Y - X smooth (min |L U|^2: C1 into the skin round it, no kink at a contact's rim),
            # small (anchor), zero with no contact: the skinned surface stays where nothing touches
            rhs = Lrf.T @ (Lr @ X - Lrx @ Xfix) + tgt
            Wt = W.copy()
            if kap > 0 and gvol is not None:
                Nn = bends.normals(X[mesh.rep], p.T)[mesh.first]
                wv = cf["vol_w"] * gvol[fi]
                Wt += wv
                rhs += wv[:, None] * (X[fi] + kap * gvol[fi, None] * Nn[fi])
            lu = splu((LtL + sp.diags(Wt)).tocsc())
            Y = X.copy()
            Y[fi] = np.stack([lu.solve(rhs[:, c]) for c in range(3)], 1)
            lg["rounds"].append({"inside_solid": int(len(insp)), "contacts": n_act, "firm": int(len(insd)), "kap": round(kap, 4)})
        ph = np.concatenate([Y[fi], np.ones((len(fi), 1))], 1)
        Dw = np.linalg.solve(Mw[fi], ph[..., None])[..., 0][:, :3] - mesh.P0[fi]
        sc = ray.scene(Y[mesh.rep], p.T)
        N = bends.normals(Y[mesh.rep], p.T)[mesh.first]
        t_ = fi[f[fi] > 0.02]
        lg["inside"] = int(ray.inside(sc, Y[t_] + 3e-4 * N[t_]).sum())
        lg["vol_mm3"] = round((volume(Y, mesh.Tw) - volX) * 1e9, 0)
        r_ = lg["rounds"][-1]
        print(f"    march {th:6.1f}: inside {lg['inside']} in-solid {lg['inside_solid']} contacts {r_['contacts']} "
              f"firm {r_['firm']} kap {kap:.4f} dvol {lg['vol_mm3']} mm3", flush=True)
        if any(abs(th - k) < 1e-6 for k in keys):
            out[th] = (Y.copy(), f, free, M, G, {"march": lg})
    return [(k,) + out[round(k, 3)] for k in keys]
