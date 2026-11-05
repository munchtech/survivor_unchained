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
    LtL = (Lrf.T @ Lrf).tocsc()
    base_w = cf["data"] * (1 - f[fi]) ** 2 + cf["anchor"]
    share = np.where(sd_n, 1.0 - cf["share_trunk"], cf["share_trunk"])
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
            for side_d, Tc in ((False, T_thigh), (True, T_trunk)):
                c_ = cn[sd_n[cn] == side_d]
                if not len(c_) or not len(Tc):
                    continue
                if cf.get("upright") is not None:
                    Tc = Tc[upright(Y, Tc, not side_d)]
                q, nq = nearest_face(Y, Tc, Y[c_])
                s = np.einsum("ij,ij->i", Y[c_] - q, nq)
                dist = np.linalg.norm(Y[c_] - q, axis=1)
                act = (s < cf["release"]) & (dist < cf["reach"])
                far += int(((s < cf["release"]) & (dist >= cf["reach"])).sum())
                contacts[c_[~act]] = False
                c_, q, nq, s = c_[act], q[act], nq[act], s[act]
                n_act += len(c_)
                k = pos[c_]
                # inside (s < 0): its share of the way to q, then the margin out; touching: held at the margin
                mv = np.where(s < 0, share[c_], 1.0)[:, None] * (q - Y[c_]) + cf["margin"] * nq
                wc[k] = cf["contact"]
                tgt[k] = Y[c_] + mv - X[c_]
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
