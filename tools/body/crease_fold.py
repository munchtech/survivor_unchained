"""Stage 7's "flatten" fold (correctives.json joint "fold": "flatten"; correctives.run picks it): solve_key's
smooth-skin solve with the crease's contact as a frictionless plane. Made for the narrow crease bands (weights.py 4b):
  plane    the bisector of the posed proximal and distal directions through the joint (e3 = its normal, toward the
           proximal limb; e1 into the crease; e2 the hinge); the solve runs in that frame, so a contact is a penalty on
           e3 only (the skin slides on the plane, never pinned in it);
  contact  in the crease's wedge, a proximal node (distal weight < 0.5) at s < margin, a distal one at s > -margin,
           becomes active: its e3 held at +-margin (both limbs flattened onto the plane: the fold);
  release  after each round, an active node the plane holds back (it pulls it toward the plane: adhesion) goes free;
  rest     as solve_key: ARAP over the joint's sphere, falloff to LBS, the outline pull, the section swell (not on the
           crease or the contact). cf "rot_prior" (0) ties the local turns to the skin's; "local" 0 freezes them.
v1 (4 Nov): the elbow only; the knee breaks under it (see the P1 crease report)."""
import numpy as np, scipy.sparse as sp
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree
import bends, ray
from correctives import smooth01, polar, parts, prox_dir


def solve_key(mesh, st, V, G, jc, cf, ref):
    p = mesh.p
    I = p.index
    sub = lambda x: x.replace("{s}", st.s)
    c0 = p.rest[I[sub(jc["center"])]][:3, 3]
    d = np.linalg.norm(mesh.P0 - c0, axis=1)
    f = 1 - smooth01((d - jc["r_in"]) / (jc["r_out"] - jc["r_in"]))
    free = (d < jc["r_out"]) & ~mesh.held
    fi = np.nonzero(free)[0]
    pos = -np.ones(mesh.n, np.int64)
    pos[fi] = np.arange(len(fi))
    X = V[mesh.first]
    M = mesh.skin_mats(G)
    R = polar(M[mesh.first][:, :3, :3])
    R_lbs = R.copy()
    E = mesh.E
    eP = mesh.P0[E[:, 0]] - mesh.P0[E[:, 1]]
    l2 = np.zeros(mesh.n)
    np.add.at(l2, E[:, 0], (eP ** 2).sum(1))
    np.add.at(l2, E[:, 1], (eP ** 2).sum(1))
    a_data = cf["data"] * (1 - f[fi]) ** 2 + cf["floor"]
    Lg = mesh.Lg[fi][:, fi]
    Lfx = mesh.Lg[fi][:, ~free]
    Xfix = X[~free]
    wd, _, _, N0 = parts(mesh, jc, st.s)
    # the plane's frame: e3 = nb (toward the proximal limb), e1 = into the crease, e2 = the hinge
    a_ = bends.unit(prox_dir(st, G))
    b_ = st.d3(G)
    nb = bends.unit(a_ - b_)
    wv = bends.unit(a_ + b_)
    hv = np.cross(nb, wv)
    Fr = np.stack([wv, hv, nb])            # rows: world -> plane frame
    Oj = G[st.j][:3, 3]
    # rest-space sideways: the swell's room (the sides, not the crease or the outer)
    je, jd = I[sub(jc["distal_end"])], I[sub(jc["distal"])]
    d_rest = bends.unit(p.rest[je][:3, 3] - p.rest[jd][:3, 3])
    d_key = bends.unit(G[je][:3, 3] - G[jd][:3, 3])
    bdir = bends.unit(d_key - d_rest)
    crease_side = smooth01(((mesh.P0 - c0) @ bdir + cf["band_in"]) / cf["band_w"])
    Y = X.copy()
    side = np.where(wd >= 0.5, -1.0, 1.0)          # +1 proximal (stays at s >= margin), -1 distal
    active = np.zeros(mesh.n, bool)
    log = {"free": int(len(fi)), "iters": []}
    vw = st.view(2 * bends.PX_CLOSE) if ref else None
    dense = (np.concatenate([bends.resample(ref[k]) for k in jc.get("pull", []) if k in ref])
             if ref and jc.get("pull") else None)
    rend_nodes = np.zeros(mesh.n, bool)
    rend_nodes[mesh.rep[st.rend]] = True
    slabs = []
    O0 = p.rest[st.j][:3, 3]
    for sd_, ts in (jc.get("area") or {}).items():
        sel = st.seg_p if sd_ == "p" else st.seg_d
        ax0 = st.p3 if sd_ == "p" else st.u_d0
        on = np.zeros(mesh.n, bool)
        on[mesh.rep[sel]] = True
        A0 = [bends.section(p.P0, p.T, sel, O0 + t * ax0, ax0, rend=st.rend)[1] for t in ts]
        slabs.append({"side": sd_, "ts": np.asarray(ts, float), "sel": sel, "on": on & free,
                      "tn": (mesh.P0 - O0) @ ax0, "A0": np.asarray(A0), "k": np.ones(len(ts))})
    sc_n = np.ones(mesh.n)
    cw = cf["contact"]
    m_ = cf["margin"]
    for rnd in range(cf["iters"] + 1):
        Vall = Y[mesh.rep]
        N = bends.normals(Vall, p.T)[mesh.first]
        rel = Y - Oj
        s = rel @ nb
        inwedge = (rel @ wv > cf["wedge"]) & free & (f > 0.02)
        viol = inwedge & (side * s < m_)
        active |= viol
        out_t = {}
        if dense is not None and cf["outline"] > 0:
            mk = ray.mask(Vall, st.T_rend, vw)
            Ed = bends.edge_points(mk, vw)
            xy = vw.xy(Y)
            cand = np.nonzero(free & rend_nodes & (np.abs(N @ vw.cam) < 0.5) & ~active)[0]
            de, _ = cKDTree(Ed).query(xy[cand])
            sil = cand[de < 0.7e-3]
            dr, ir = cKDTree(dense).query(xy[sil])
            for node, r_i, dd_ in zip(sil, ir, dr):
                if dd_ < jc.get("cap", 0.015):
                    dv = dense[r_i] - xy[node]
                    out_t[node] = Y[node] + dv[0] * vw.ex + dv[1] * vw.ey
        if slabs and rnd > 0:
            O = G[st.j][:3, 3]
            s_area = np.ones(mesh.n)
            for sl in slabs:
                ax = st.p3 if sl["side"] == "p" else st.d3(G)
                for k_, t in enumerate(sl["ts"]):
                    A = bends.section(Vall, p.T, sl["sel"], O + t * ax, ax, rend=st.rend)[1]
                    if np.isfinite(A) and np.isfinite(sl["A0"][k_]) and A > 0:
                        sl["k"][k_] = float(np.clip(sl["k"][k_] * (sl["A0"][k_] / A) ** (0.5 * cf["area_relax"]),
                                                    1.0, cf["area_kmax"]))
                ts = sl["ts"]
                kk = np.interp(sl["tn"], np.r_[ts[0] - cf["area_fade"], ts, ts[-1] + cf["area_fade"]],
                               np.r_[1.0, sl["k"], 1.0], left=1.0, right=1.0)
                s_area = np.where(sl["on"], np.maximum(s_area, kk), s_area)
            s_area = 1.0 + (s_area - 1.0) * (1.0 - crease_side)
            s_area[active] = 1.0
            sc_n = s_area
            log.setdefault("area_k", []).append([np.round(sl["k"], 3).tolist() for sl in slabs])
        if rnd == cf["iters"]:
            sc = ray.scene(Vall, p.T)
            near = fi[f[fi] > 0.02]
            log["iters"].append({"inside_parity": int(ray.inside(sc, Y[near] + 3e-4 * N[near]).sum()),
                                 "contact_pts": int(active.sum()), "outline_pts": len(out_t)})
            break
        Wi = a_data.copy()
        tgt = a_data[:, None] * X[fi]
        for node, t in out_t.items():
            wo = cf["outline"] * f[node]
            Wi[pos[node]] += wo
            tgt[pos[node]] += wo * t
        tgtF = tgt @ Fr.T                                   # in the plane's frame
        Wn = np.zeros(len(fi))
        ai = pos[np.nonzero(active & free)[0]]
        Wn[ai] = cw
        tgtF[ai, 2] += cw * (side[fi[ai]] * m_ + (Oj @ nb))
        lus = [splu((Lg + sp.diags(Wi)).tocsc()), splu((Lg + sp.diags(Wi + Wn)).tocsc())]
        XfixF = Xfix @ Fr.T
        for _ in range(cf["arap"]):
            Re = 0.5 * (R[E[:, 0]] + R[E[:, 1]]) * (0.5 * (sc_n[E[:, 0]] + sc_n[E[:, 1]]))[:, None, None]
            r = np.einsum("nij,nj->ni", Re, eP)
            b = np.zeros((mesh.n, 3))
            np.add.at(b, E[:, 0], r)
            np.add.at(b, E[:, 1], -r)
            rhs = (b[fi] @ Fr.T) - Lfx @ XfixF + tgtF
            YF = np.stack([lus[0].solve(rhs[:, 0]), lus[0].solve(rhs[:, 1]), lus[1].solve(rhs[:, 2])], 1)
            Y = X.copy()
            Y[fi] = YF @ Fr
            if not cf.get("local", 1):
                break
            eY = Y[E[:, 0]] - Y[E[:, 1]]
            Sm = np.einsum("ni,nj->nij", eP, eY)
            Cv = np.zeros((mesh.n, 3, 3))
            np.add.at(Cv, E[:, 0], Sm)
            np.add.at(Cv, E[:, 1], Sm)
            if cf.get("rot_prior", 0):
                Cv += cf["rot_prior"] * l2[:, None, None] * np.transpose(R_lbs, (0, 2, 1))
            U, _, Vt = np.linalg.svd(Cv[fi])
            Rn = np.einsum("nji,nkj->nik", Vt, U)
            bad = np.linalg.det(Rn) < 0
            if bad.any():
                U2 = U.copy()
                U2[bad, :, 2] *= -1
                Rn[bad] = np.einsum("nji,nkj->nik", Vt[bad], U2[bad])
            R[fi] = Rn
        # release: an active node the plane holds back (pulls toward it: adhesion, not contact) goes free
        if cf.get("release", 1):
            sa = side * ((Y - Oj) @ nb) - m_
            rel_ = active & (sa > cf.get("release_tol", 2e-5))
            active &= ~rel_
        else:
            rel_ = np.zeros(mesh.n, bool)
        log["iters"].append({"contact_pts": int(active.sum()), "released": int(rel_.sum()), "outline_pts": len(out_t)})
    return Y, f, free, M, log
