"""Stage 6's two-sided contact for the hip (correctives.json joint "fold": "field"; correctives.run picks it). P1 hip r3.

Why not contact_pair (r2, kept as the hip's pair_trial): it moved only the trunk's nodes found inside, onto the nearest
thigh face, and each march angle restarted from raw skinning. At 105 the thigh's patch inside the trunk stayed enclosed
by trunk skin (the belly nodes on the thigh's surface still tested inside), and past the thigh's half-thickness the
nearest face is the thigh's far side. Here (judge D's contact, D2's offset rule):

  start    each march angle (`step` deg from the first key) starts from the last angle's result, carried as its
           rest-space delta re-skinned by this pose (correctives.rest_delta's inverse), so every node is at most one
           step's sweep inside: the nearest face is the right one
  inside   the check's own test (ray parity on the whole posed body, the node pushed 0.3 mm out along its normal) on the
           strip's test nodes, BOTH sides: the trunk's nodes in the thigh and the thigh's nodes in the trunk
  target   q, n the nearest point and normal on the OTHER side's posed triangles (the check's split, bends.Strip.seg_d);
           a trunk node moves `share_trunk` (the belly gives) of its way to q, a thigh node the rest (the thigh firm);
           both `margin` past it along n, so the two skins meet at one contact surface with a margin's gap (judge D:
           zero-gap contact; the check reads a node ON the other skin as inside at 0.3 mm). A contact node stays one
           while it is less than `release` outside (never pulled in) and within `reach` of the other skin
  smooth   U = Y - X, an offset on the skinned surface X (D2: free smoothing drifts off the pivot), min |L U|^2 (the
           welded uniform Laplacian: the contact's rim fades C1 into the skin, no kink) + (data (1-f)^2 + anchor)|U|^2
           + contact |U - t|^2; `rounds` re-tests per angle
  volume   contact_pair's band: the trunk's crease side within rim_in .. vol_r of the contact nodes takes the belly's
           smooth response to a normal load, scaled (secant) to the skinned volume: what is pushed in rolls up above
           the crease
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
from contact_pair import nearest_face, vol_grad
from correctives import key_pose, rest_delta, smooth01, volume


def carried(mesh, D, M):
    """The rest-space delta D (per body poser vertex, rest_delta's output) skinned by this pose's blended matrices M:
    each welded node's posed offset (its first poser vertex)."""
    U = np.zeros((mesh.n, 3))
    if D is None:
        return U
    p = mesh.p
    body = np.nonzero(p.piece == "body")[0]
    Ub = np.einsum("vij,vj->vi", M[body][:, :3, :3], D)
    pos = np.full(len(p.piece), -1)
    pos[body] = np.arange(len(body))
    fb = pos[mesh.first]
    m = fb >= 0
    U[m] = Ub[fb[m]]
    return U


def node_len(mesh):
    """Each welded node's mean rest edge length (m): the local mesh scale h, so the solve's weights are physical
    lengths, the same on close and play (a per-node weight w reads as w / h^2 per area)."""
    e = mesh.E
    ln = np.linalg.norm(mesh.P0[e[:, 0]] - mesh.P0[e[:, 1]], axis=1)
    s, c = np.zeros(mesh.n), np.zeros(mesh.n)
    for k in (0, 1):
        np.add.at(s, e[:, k], ln)
        np.add.at(c, e[:, k], 1.0)
    return s / np.maximum(c, 1.0)


def partner(Y, Tc, Q, P0, Q0, far_m, k=64):
    """Closest points on the other side's posed triangles Tc (welded ids into Y) to Q, among the triangles whose rest
    centre is over far_m from the node's rest place Q0 (the skin it is joined to across the crease is the same sheet
    folding, not the other body: r4). Returns q, unit face normal, the face's row in Tc, found."""
    A, B, C = Y[Tc[:, 0]], Y[Tc[:, 1]], Y[Tc[:, 2]]
    c0 = P0[Tc].mean(1)
    _, cand = cKDTree((A + B + C) / 3).query(Q, k=min(k, len(Tc)))
    cand = cand.reshape(len(Q), -1)
    best = np.full(len(Q), np.inf)
    qb = np.zeros_like(Q)
    fb = np.zeros(len(Q), np.int64)
    for j in range(cand.shape[1]):
        t = cand[:, j]
        q, _ = closest_on_tris(Q, A[t], B[t], C[t])
        d = np.linalg.norm(Q - q, axis=1)
        m = (d < best) & (np.linalg.norm(c0[t] - Q0, axis=1) > far_m)
        best[m], qb[m], fb[m] = d[m], q[m], t[m]
    n = np.cross(B[fb] - A[fb], C[fb] - A[fb])
    return qb, n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12), fb, np.isfinite(best)


def partner_any(Y, Tc, Q, P0, Q0, hq, ratio=0.5, k=64):
    """Closest points on ANY of the strip's posed triangles Tc to Q, among those the pose brought together with the
    node: rest distance (the triangle's rest centre to the node's rest place) over 2 h (beyond its own 1-ring) and
    the posed distance under `ratio` of it. r4: the crease folds within one weight side (the front of the hip at
    112: trunk nodes 1 mm inside the trunk's own folded skin, 10-16 mm from the thigh's), so the other skin is the
    one that came to it, whichever side. Returns q, unit face normal, the face's row in Tc, found."""
    A, B, C = Y[Tc[:, 0]], Y[Tc[:, 1]], Y[Tc[:, 2]]
    c0 = P0[Tc].mean(1)
    _, cand = cKDTree((A + B + C) / 3).query(Q, k=min(k, len(Tc)))
    cand = cand.reshape(len(Q), -1)
    best = np.full(len(Q), np.inf)
    qb = np.zeros_like(Q)
    fb = np.zeros(len(Q), np.int64)
    for j in range(cand.shape[1]):
        t = cand[:, j]
        q, _ = closest_on_tris(Q, A[t], B[t], C[t])
        d = np.linalg.norm(Q - q, axis=1)
        r0 = np.linalg.norm(c0[t] - Q0, axis=1)
        m = (d < best) & (r0 > 2 * hq) & (d < ratio * r0)
        best[m], qb[m], fb[m] = d[m], q[m], t[m]
    n = np.cross(B[fb] - A[fb], C[fb] - A[fb])
    return qb, n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12), fb, np.isfinite(best)


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
    sd_n = np.zeros(mesh.n, bool)
    sd_n[mesh.rep[st.seg_d]] = True
    Tr = mesh.rep[st.T_rend]
    tri_d = sd_n[Tr].sum(1) >= 2
    T_thigh, T_trunk = Tr[tri_d], Tr[~tri_d]
    test = np.zeros(mesh.n, bool)
    test[mesh.rep[st.test]] = True
    test &= free
    Gr = p.rest[I[sub(jc["distal"])]]
    crease = (mesh.P0 - Gr[:3, 3]) @ (-Gr[:3, 2]) > 0
    # the roll's band above the crease only: the belly over the joint's transverse plane (b: judge D, "rolled up
    # above the crease"); below it the band reached the perineum and pushed it into the other leg (99 mm, r3 trial 1)
    crease &= (mesh.P0 - c0) @ st.fr.up > cf.get("band_above", 0.0)
    Lg = mesh.Lg
    rows = np.nonzero(np.asarray(abs(Lg[:, fi]).sum(1)).ravel() > 0)[0]
    Lrf = Lg[rows][:, fi]
    if cf.get("op", "bilap") == "membrane":
        # r4: the offset's energy is the membrane's (Dirichlet: the sum over edges of |U_i - U_j|^2, harmonic off
        # the contacts) + a bending length's |LU|^2 + an anchor length's |U|^2, each in metres over the local mesh
        # scale h (node_len), so close and play solve the same surface. Derivation: (c) the check's pit is the change
        # of the 25 mm curvature, ~ (r^2/4) lap(u_n): a harmonic offset reads 0 off the contacts, where the
        # bi-Laplacian alone (|LU|^2, r3) rings concave round every push (the flank's rim, F16 S15 at 135); (a) soft
        # tissue under a contact: the free skin round it stays convex (the membrane's obstacle problem: C^1,1, it
        # leaves the other skin tangentially, the soft fold)
        h = node_len(mesh)
        lb = cf.get("bend_m", 0.0)
        K = Lg[fi][:, fi]
        if lb > 0:
            K = K + Lrf.T @ sp.diags((lb / h[rows]) ** 2) @ Lrf
        LtL = sp.csc_matrix(K)
        base_w = cf["data"] * (1 - f[fi]) ** 2 + (h[fi] / cf["anchor_m"]) ** 2
    else:
        LtL = (Lrf.T @ Lrf).tocsc()
        base_w = cf["data"] * (1 - f[fi]) ** 2 + cf["anchor"]
    h_n = node_len(mesh)
    give = None
    sh_t = np.full(mesh.n, float(cf["share_trunk"]))
    if "share_trunk_low" in cf:
        # r4: the trunk's give by what lies under it: below the joint's transverse plane the mons and the groin are
        # on the pubic bone (the pubic tubercle at the level of the hip joint centre), above it the abdominal wall
        # (no bone): share_trunk_low below, share_trunk above, a smoothstep over +-share_w. A thigh node takes the
        # rest of its trunk partner's (the firmness of what it presses on).
        hw = cf.get("share_w", 0.02)
        lo, hi = cf["share_trunk_low"], cf["share_trunk"]
        give = lambda P: lo + (hi - lo) * smooth01(((P - c0) @ st.fr.up + hw) / (2 * hw))
        sh_t = give(mesh.P0)
    share = np.where(sd_n, 1.0 - sh_t, sh_t)
    TW = mesh.Tw
    n0 = np.cross(mesh.P0[TW[:, 1]] - mesh.P0[TW[:, 0]], mesh.P0[TW[:, 2]] - mesh.P0[TW[:, 0]])
    tid = {tuple(t): i for i, t in enumerate(TW.tolist())}
    rows_of = lambda Tc: np.array([tid[tuple(t)] for t in Tc.tolist()])
    rid = {False: rows_of(T_trunk), True: rows_of(T_thigh)}
    jb = I[sub(jc["distal"])]
    Rc = {}

    def upright(Y, Tc, thigh):
        """The other side's faces that are not folded over by the skinning (the posed normal within 72 deg of the rest
        normal carried by the side's own bone: the thigh's, or the pelvis held): a trunk node beside a folded crease
        face read 'outside' it while the ray parity, and the check, found it inside the thigh (r3 trial C: 191 of
        the 201 left inside at 135 sat within 1 mm of such a face). Off by default: at 0.3 it moved nothing (135: 183
        inside, 6.0 mm), so the faces they sit by are not folded; the parity's crossings are the other skin's own.)"""
        R = Rc["thigh"] if thigh else np.eye(3)
        n1 = np.cross(Y[Tc[:, 1]] - Y[Tc[:, 0]], Y[Tc[:, 2]] - Y[Tc[:, 0]])
        r0 = n0[rid[thigh]] @ R.T
        c = np.einsum("ij,ij->i", n1, r0) / np.maximum(np.linalg.norm(n1, axis=1) * np.linalg.norm(r0, axis=1), 1e-18)
        return c > cf["upright"]

    keys = [float(k[1]) for k in jc["keys"]]
    march = sorted(set([round(float(x), 3) for x in np.arange(keys[0], keys[-1], cf["step"])] + keys))
    out, D = {}, None
    contacts = np.zeros(mesh.n, bool)
    for th in march:
        V, G = key_pose(st, th)
        X = V[mesh.first]
        M = mesh.skin_mats(G)
        Rc["thigh"] = (G[jb] @ p.skel.ibm[jb])[:3, :3]
        volX = volume(X, TW)
        Y = X + carried(mesh, D, M) * free[:, None]
        lg = {"deg": th, "rounds": []}
        lam = 0.0
        if cf.get("seam"):
            # the seam's contacts: the strip's test nodes inside the other part's skinned skin (the check's test on X)
            scx = ray.scene(X[mesh.rep], p.T)
            Nx = bends.normals(X[mesh.rep], p.T)[mesh.first]
            tix = np.nonzero(test)[0]
            contacts[tix[ray.inside(scx, X[tix] + 3e-4 * Nx[tix])]] = True
        for rd in range(cf["rounds"]):
            sc = ray.scene(Y[mesh.rep], p.T)
            N = bends.normals(Y[mesh.rep], p.T)[mesh.first]
            ti = np.nonzero(test)[0]
            ins = ti[ray.inside(sc, Y[ti] + 3e-4 * N[ti])]
            contacts[ins] = True
            cn = np.nonzero(contacts & free)[0]
            wc = np.zeros(len(fi))
            tgt = np.zeros((len(fi), 3))
            n_act, far = 0, 0
            if cf.get("partners") == "any":
                # r4: every contact node against whichever skin the pose brought to it (partner_any); who gives:
                # a trunk node on the thigh by the trunk's give, a thigh node on the trunk the rest of its partner's,
                # a skin on its own side (the crease folding onto itself) half each
                pairs = ((None, Tr),)
            else:
                pairs = ((False, T_thigh), (True, T_trunk))
            for side_d, Tc in pairs:
                c_ = cn if side_d is None else cn[sd_n[cn] == side_d]
                if not len(c_) or not len(Tc):
                    continue
                if side_d is None:
                    q, nq, fb, ok = partner_any(Y, Tc, Y[c_], mesh.P0, mesh.P0[c_], h_n[c_], cf.get("pair_ratio", 0.5))
                    s = np.einsum("ij,ij->i", Y[c_] - q, nq)
                    dist = np.linalg.norm(Y[c_] - q, axis=1)
                    act = ok & (s < cf["release"]) & (dist < cf["reach"])
                    far += int((ok & (s < cf["release"]) & (dist >= cf["reach"])).sum())
                    contacts[c_[~act]] = False
                    c_, q, nq, s, fb = c_[act], q[act], nq[act], s[act], fb[act]
                    n_act += len(c_)
                    k = pos[c_]
                    th_n, th_p = sd_n[c_], tri_d[fb]
                    giv_n = give(mesh.P0[c_]) if give is not None else np.full(len(c_), cf["share_trunk"])
                    giv_p = give(mesh.P0[Tc[fb]].mean(1)) if give is not None else np.full(len(c_), cf["share_trunk"])
                    shr = np.where(th_n == th_p, 0.5, np.where(th_n, 1.0 - giv_p, giv_n))
                    mv = np.where(s < 0, shr, 1.0)[:, None] * (q - Y[c_]) + cf["margin"] * nq
                    wc[k] = cf["contact"]
                    tgt[k] = Y[c_] + mv - X[c_]
                    continue
                if cf.get("upright") is not None:
                    Tc = Tc[upright(Y, Tc, not side_d)]
                if cf.get("far_m") is not None:
                    q, nq, fb, ok = partner(Y, Tc, Y[c_], mesh.P0, mesh.P0[c_], cf["far_m"])
                else:
                    (q, nq), fb, ok = nearest_face(Y, Tc, Y[c_]), None, np.ones(len(c_), bool)
                s = np.einsum("ij,ij->i", Y[c_] - q, nq)
                dist = np.linalg.norm(Y[c_] - q, axis=1)
                act = ok & (s < cf["release"]) & (dist < cf["reach"])
                sm = np.zeros(len(c_), bool)
                if cf.get("seam") and bool(side_d) == (cf["seam"] == 1):   # 1: the thigh's give fixed, 2: the trunk's
                    # R5 lead 4, the seam (implicit skinning's contact, Vaillant 2013: each part's field from its own
                    # skinned skin; the contact where they meet). r4 moved each node its share of the way to the
                    # other part's SOLVED skin Y, so the share compounded round on round (half, then half the rest)
                    # until the belly lay on an uncompressed thigh (share 0.5 or 0.75: sink -45 vs -49 mm). Here a
                    # thigh node inside the trunk's SKINNED skin X gives its fixed share of that overlap (the trunk's
                    # give at its partner face), measured on X, so per angle it never compounds; the trunk then
                    # lies on the compressed thigh as before: the two parts meet at the seam, each compressed by its
                    # share (both sides fixed on X disagree node to node: 135 680 inside)
                    qx, nx, fx, okx = partner(X, Tc, X[c_], mesh.P0, mesh.P0[c_], cf.get("far_m", 0.0))
                    sx = np.einsum("ij,ij->i", X[c_] - qx, nx)
                    sm = okx & (sx < 0)
                    act |= sm
                    if side_d:
                        gx = (1.0 - give(mesh.P0[Tc[fx]].mean(1))) if give is not None else 1.0 - share[c_]
                    else:
                        gx = share[c_]
                    seam_t = gx[:, None] * (qx - X[c_])
                far += int((ok & (s < cf["release"]) & (dist >= cf["reach"])).sum())
                contacts[c_[~act]] = False
                c_, q, nq, s = c_[act], q[act], nq[act], s[act]
                n_act += len(c_)
                k = pos[c_]
                shr = share[c_]
                if give is not None and side_d and fb is not None:
                    shr = 1.0 - give(mesh.P0[Tc[fb[act]]].mean(1))
                # inside (s < 0): its share of the way to q, then the margin out; touching: held at the margin
                mv = np.where(s < 0, shr, 1.0)[:, None] * (q - Y[c_]) + cf["margin"] * nq
                wc[k] = cf["contact"]
                tgt[k] = Y[c_] + mv - X[c_]
                if sm.any():
                    sm, seam_t = sm[act], seam_t[act]
                    tgt[k[sm]] = seam_t[sm]
            A = (LtL + sp.diags(base_w + wc)).tocsc()
            lu = splu(A)
            U = np.stack([lu.solve(wc * tgt[:, c]) for c in range(3)], 1)
            Yb = X.copy()
            Yb[fi] += U
            band = np.zeros(mesh.n)
            if (wc > 0).any() and cf.get("volume", 1):
                dc, _ = cKDTree(mesh.P0[fi[wc > 0]]).query(mesh.P0[fi])
                hat = smooth01(dc / cf["rim_in"]) * (1 - smooth01((dc - cf["rim_in"]) / (cf["vol_r"] - cf["rim_in"])))
                band[fi] = hat * (~sd_n[fi]) * crease[fi] * (wc == 0)
            if band.any():
                g = vol_grad(Yb, TW)
                # the roll's response with the contact nodes held where the contact put them (a stiff contact only
                # resisted it: lam ~250 pushed them back in, 4-5 mm deep at 112-135, r3 trial 2)
                luz = splu((LtL + sp.diags(base_w + np.where(wc > 0, 1e6, 0.0))).tocsc())
                Z = np.stack([luz.solve(band[fi] * g[fi, c]) for c in range(3)], 1)
                v0 = volume(Yb, TW) - volX
                Yz = Yb.copy()
                Yz[fi] += Z
                v1 = volume(Yz, TW) - volX
                lam = max(0.0, -v0 / (v1 - v0)) if abs(v1 - v0) > 1e-15 else 0.0
                for _ in range(2):
                    Yz = Yb.copy()
                    Yz[fi] += lam * Z
                    vl = volume(Yz, TW) - volX
                    if abs(vl) < 1e-8:
                        break
                    lam = max(0.0, lam - vl * lam / (vl - v0)) if abs(vl - v0) > 1e-15 else lam
                Y = Yz
            else:
                Y = Yb
            lg["rounds"].append({"inside": int(len(ins)), "contacts": int(n_act), "far": far, "lam": round(float(lam), 3),
                                 "dvol_cm3": round((volume(Y, TW) - volX) * 1e6, 2)})
        sc = ray.scene(Y[mesh.rep], p.T)
        N = bends.normals(Y[mesh.rep], p.T)[mesh.first]
        ti = np.nonzero(test)[0]
        insf = ti[ray.inside(sc, Y[ti] + 3e-4 * N[ti])]
        lg["inside"] = int(len(insf))
        if cf.get("debug"):
            for side_d, Tc in ((False, T_thigh), (True, T_trunk)):
                c_ = insf[sd_n[insf] == side_d]
                if not len(c_):
                    continue
                q, nq = nearest_face(Y, Tc, Y[c_])
                s_ = np.einsum("ij,ij->i", Y[c_] - q, nq) * 1000
                r_ = (mesh.P0[c_] - c0) * 1000
                print(f"      dbg {th} {'thigh' if side_d else 'trunk'} n {len(c_)} s mm p5 {np.percentile(s_, 5):.1f} "
                      f"p50 {np.median(s_):.1f} p95 {np.percentile(s_, 95):.1f}; s>0: {(s_ > 0).sum()} contacts {contacts[c_].sum()} "
                      f"band {(band[c_] > 0).sum()} | rest y {r_[:, 1].min():.0f}..{r_[:, 1].max():.0f} z {r_[:, 2].min():.0f}..{r_[:, 2].max():.0f}")
                o = np.argsort(s_)[:3].tolist() + np.argsort(-s_)[:3].tolist()
                for k in o:
                    print(f"        s {s_[k]:7.1f} rest ({r_[k, 0]:.0f},{r_[k, 1]:.0f},{r_[k, 2]:.0f}) dist {1000*np.linalg.norm(Y[c_[k]] - q[k]):.1f}")
        lg["inside_thigh"] = int(sd_n[insf].sum())
        lg["max_move_mm"] = round(float(np.linalg.norm(Y - X, axis=1).max() * 1000), 1)
        r_ = lg["rounds"][-1]
        print(f"    field {th:6.1f}: inside {lg['inside']} (thigh {lg['inside_thigh']}) contacts {r_['contacts']} "
              f"far {r_['far']} lam {r_['lam']} dvol {r_['dvol_cm3']} cm3 max {lg['max_move_mm']} mm", flush=True)
        D = rest_delta(mesh, Y, f, free, M)
        if any(abs(th - k) < 1e-6 for k in keys):
            out[round(th, 3)] = (Y.copy(), f, free, M, G, {"march": lg})
    return [(k,) + out[round(k, 3)] for k in keys]
