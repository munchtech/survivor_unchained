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


def corner_shift(st, G, deg, nb):
    """How far (m, along nb) the reference's inner corner (tools/body/ref/<motion>_<deg>.json, its "corner" point:
    where the two limbs' inner lines, each offset by the body's own rest half-width from its bone, meet) sits off
    the bisector plane through the joint. Equal half-widths put it on that plane; the knee's (a thin back of the
    thigh against a full calf) put it 24 mm toward the thigh at 90, and a fold held on the joint's plane dents the
    crease there. The hinge is the view's axis, so nb lies in the view plane and the 2D offset is exact."""
    spec = bends.load_ref(st.motion, int(round(deg)))
    pts = [c for c in spec["curves"]["inner"] if "corner" in c]
    if not pts:
        return 0.0
    vw = st.view(2 * bends.PX_CLOSE)
    V0, G0, _ = st.posed(0)
    R = bends.radii(st, ray.mask(V0, st.T_rend, vw), vw, bends.Plane2(st, G0))
    pl = bends.Plane2(st, G)
    q = bends.build_ref({"curves": {"c": [pts[0], pts[0]]}}, pl, R).get("c")
    if q is None:
        return 0.0
    off = q[0] - pl.O
    return float((off[0] * vw.ex + off[1] * vw.ey) @ nb)


def skins_surface(mesh, st, G, X, sk):
    """r5 (P1 ek): the contact surface from the two skins, not the bisector plane. In the plane's frame (e1 into the
    crease, e2 the hinge, s along nb toward the proximal limb) the strip's skinned nodes X are binned on a `cell` grid
    over (e1, e2): per cell the proximal skin's lower envelope s_p (its facing side) and the distal's upper s_d; where
    they overlap (s_d > s_p: the skinning drove one limb into the other) the contact is the CORE, and its surface
    h = s_p + share (s_d - s_p): each skin gives its share of the overlap (share 0.5: the like tissues of the two
    limbs, biceps on the forearm's flexors, the hamstrings on the gastrocnemius, give alike). h is smoothed (a normalised
    Gaussian, `sigma`) and held flat outward past the overlap by its nearest value; the footprint weight fp is 1 in
    the core and fades over `rim` (a smoothstep of the distance outside it), so the contact's edge eases out (the
    judge's knee kink: the flattening stopped short at the solve's sphere, 15 cm along a contact that runs 22 cm).
    Returns the lookups and the contact's reach (the farthest core-or-rim point from the joint, m)."""
    from scipy.ndimage import distance_transform_edt, gaussian_filter, map_coordinates
    a_ = bends.unit(prox_dir(st, G))
    b_ = st.d3(G)
    nb = bends.unit(a_ - b_)
    wv = bends.unit(a_ + b_)
    hv = np.cross(nb, wv)
    Oj = G[st.j][:3, 3]
    gd = np.zeros(mesh.n, bool)
    gd[mesh.rep[st.seg_d]] = True
    gr = np.zeros(mesh.n, bool)
    gr[mesh.rep[st.rend]] = True
    rel = X - Oj
    e1, e2, s = rel @ wv, rel @ hv, rel @ nb
    c = sk.get("cell", 0.004)
    m = gr & (e1 > 0) & (e1 < sk.get("e1_max", 0.4))
    lo2 = float(e2[m].min())
    n1 = int(np.ceil(e1[m].max() / c)) + 1
    n2 = int(np.ceil((e2[m].max() - lo2) / c)) + 1
    # each skin's facing envelope by rays square to the plane over the grid's cell centres: the proximal triangles
    # hit from the distal side (its lower envelope s_p), the distal ones from the proximal side (s_d); exact where a
    # node binning read a column's far skin when the facing one's nodes fell in the next column
    Tr = mesh.rep[st.T_rend]
    tri_d = gd[Tr].sum(1) >= 2
    g1, g2 = np.meshgrid((np.arange(n1) + 0.5) * c, lo2 + (np.arange(n2) + 0.5) * c, indexing="ij")
    base = Oj + g1.reshape(-1, 1) * wv + g2.reshape(-1, 1) * hv
    far = 1.0
    env = {}
    for nm, Tc, sg in (("p", Tr[~tri_d], -1.0), ("d", Tr[tri_d], 1.0)):
        sc = ray.scene(X, Tc)
        org = base + sg * far * nb
        pid, tf = ray.hits(sc, org, np.tile(-sg * nb, (len(org), 1)))
        E = np.where(pid >= 0, sg * (far - tf), np.nan).reshape(n1, n2)
        env[nm] = E
    sp_ = np.where(np.isfinite(env["p"]), env["p"], np.inf)
    sd_ = np.where(np.isfinite(env["d"]), env["d"], -np.inf)
    both = np.isfinite(sp_) & np.isfinite(sd_)
    ov = np.where(both, sd_ - sp_, -np.inf)
    # the core from the smoothed overlap (the envelopes are one mesh row apart: a raw cell test left holes in the
    # contact, and a node over a hole was let through by its partner), its holes filled
    from scipy.ndimage import binary_fill_holes
    wo = both.astype(float)
    ovs = gaussian_filter(np.where(both, ov, 0.0), sk.get("sigma", 0.006) / c) / np.maximum(
        gaussian_filter(wo, sk.get("sigma", 0.006) / c), 1e-12)
    core = binary_fill_holes(both & (ovs > 0))
    hc = np.where(both, sp_ + sk.get("share", 0.5) * np.where(both, ov, 0.0), 0.0)
    sg = sk.get("sigma", 0.006) / c
    wgt = (both & (ov > -sk.get("gap_data", 0.01))).astype(float)
    num, den = gaussian_filter(hc * wgt, sg), gaussian_filter(wgt, sg)
    ok = den > 1e-3
    h = np.where(ok, num / np.maximum(den, 1e-12), 0.0)
    if ok.any() and not ok.all():
        _, (a1, a2) = distance_transform_edt(~ok, return_indices=True)
        h = h[a1, a2]
    dout = distance_transform_edt(~core) * c if core.any() else np.full(core.shape, np.inf)
    fp = 1.0 - smooth01(dout / sk.get("rim", 0.02))
    reach = 0.0
    k = np.argwhere(fp > 0)
    if len(k):
        E1, E2 = (k[:, 0] + 0.5) * c, lo2 + (k[:, 1] + 0.5) * c
        reach = float(np.sqrt(E1 ** 2 + E2 ** 2 + h[k[:, 0], k[:, 1]] ** 2).max())

    def look(Yc, grid, mode, cval=0.0):
        r_ = Yc - Oj
        q = np.stack([(r_ @ wv) / c - 0.5, (r_ @ hv - lo2) / c - 0.5])
        return map_coordinates(grid, q, order=1, mode=mode, cval=cval)
    return {"h": lambda Yc: look(Yc, h, "nearest"), "fp": lambda Yc: look(Yc, fp, "constant"), "reach": reach,
            "core_cells": int(core.sum()), "rim_cells": int(((fp > 0) & ~core).sum()),
            "ov_max_mm": round(float(ov[core].max() * 1000) if core.any() else 0.0, 1)}


def solve_key(mesh, st, V, G, jc, cf, ref):
    p = mesh.p
    I = p.index
    sub = lambda x: x.replace("{s}", st.s)
    c0 = p.rest[I[sub(jc["center"])]][:3, 3]
    d = np.linalg.norm(mesh.P0 - c0, axis=1)
    sk = None
    r_in, r_out = jc["r_in"], jc["r_out"]
    if jc.get("surface") == "skins":
        # the solve holds the whole contact: its sphere grows to the contact's reach (+ the hold), the fade beyond
        sk = skins_surface(mesh, st, G, V[mesh.first], jc.get("skins", {}))
        r_in = max(r_in, sk["reach"] + jc.get("skins", {}).get("hold", 0.01))
        r_out = r_in + (jc["r_out"] - jc["r_in"])
    f = 1 - smooth01((d - r_in) / (r_out - r_in))
    free = (d < r_out) & ~mesh.held
    if jc.get("free_rend") or sk is not None:   # a girdle's sphere, or the skins' grown one, reaches the other limbs: solve only this strip's body
        rn = np.zeros(mesh.n, bool)
        rn[mesh.rep[st.rend]] = True
        free &= rn
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
    if jc.get("plane_at") == "corner":     # the plane through the inner corner, not the joint (see corner_shift)
        shift = corner_shift(st, G, jc["_deg"], nb)
    else:
        shift = 0.0
    ramp = jc.get("corner_ramp", 0.0)       # the shift eased in from the joint's axis into the crease (m along e1)
    bow = jc.get("bow", 0.0)                 # the contact surface's sag across the limb (1/m): a flesh contact, not a plane
    hv0 = np.cross(bends.unit(a_ - b_), bends.unit(a_ + b_))
    offn = lambda Yc: (shift * (smooth01(((Yc - Oj) @ wv) / ramp) if ramp > 0 else np.ones(len(Yc)))
                       + bow * ((Yc - Oj) @ hv0) ** 2)
    fpn = lambda Yc: np.ones(len(Yc))
    if sk is not None:                       # the skins' contact surface and its footprint (skins_surface)
        offn, fpn = sk["h"], sk["fp"]
        log_sk = {k: sk[k] for k in ("reach", "core_cells", "rim_cells", "ov_max_mm")}
        log_sk["reach"] = round(log_sk["reach"], 4)
    # rest-space sideways: the swell's room (the sides, not the crease or the outer)
    je, jd = I[sub(jc["distal_end"])], I[sub(jc["distal"])]
    d_rest = bends.unit(p.rest[je][:3, 3] - p.rest[jd][:3, 3])
    d_key = bends.unit(G[je][:3, 3] - G[jd][:3, 3])
    bdir = bends.unit(d_key - d_rest)
    crease_side = smooth01(((mesh.P0 - c0) @ bdir + cf["band_in"]) / cf["band_w"])
    Y = X.copy()
    side = np.where(wd >= 0.5, -1.0, 1.0)          # +1 proximal (stays at s >= margin), -1 distal
    if jc.get("side") == "geom":                  # by the rest bisector plane (the check's seg_d), not the 0.5 weight
        gd = np.zeros(mesh.n, bool)
        gd[mesh.rep[st.seg_d]] = True
        gr = np.zeros(mesh.n, bool)
        gr[mesh.rep[st.rend]] = True
        side = np.where(gr, np.where(gd, -1.0, 1.0), side)
    active = np.zeros(mesh.n, bool)
    log = {"free": int(len(fi)), "iters": []}
    if sk is not None:
        log["skins"] = log_sk
    close = jc.get("skins", {}).get("close", 0.0)
    vw = st.view(2 * bends.PX_CLOSE) if ref else None
    dense = (np.concatenate([bends.resample(ref[k]) for k in jc.get("pull", []) if k in ref])
             if ref and jc.get("pull") else None)
    rend_nodes = np.zeros(mesh.n, bool)
    rend_nodes[mesh.rep[st.rend]] = True
    slabs = []
    O0 = p.rest[st.j][:3, 3]
    for sd_, ts in (jc.get("area") or {}).items():
        if sk is not None and jc.get("skins", {}).get("area_step"):
            # the tissue's section kept wherever the contact presses it: stations on to the contact's reach
            stp = jc["skins"]["area_step"]
            ts = sorted(set(list(ts) + [round(float(t), 4) for t in np.arange(max(ts) + stp, sk["reach"] + 1e-6, stp)]))
        sel = st.seg_p if sd_ == "p" else st.seg_d
        ax0 = st.p3 if sd_ == "p" else st.u_d0
        on = np.zeros(mesh.n, bool)
        on[mesh.rep[sel]] = True
        A0 = [bends.section(p.P0, p.T, sel, O0 + t * ax0, ax0, rend=st.rend)[1] for t in ts]
        slabs.append({"side": sd_, "ts": np.asarray(ts, float), "sel": sel, "on": on & free,
                      "tn": (mesh.P0 - O0) @ ax0, "A0": np.asarray(A0), "k": np.ones(len(ts))})
    sc_n = np.ones(mesh.n)
    # mitre: the crease filled to where the two limbs, each rigid with its own bone, meet on the plane
    m_ = cf["margin"]
    mi_w = jc.get("mitre", 0.0)
    mi_t = None
    if mi_w:
        Xr = np.zeros_like(X)
        for sg, bn in ((1.0, sub(jc["proximal"])), (-1.0, sub(jc["distal"]))):
            Sb = G[I[bn]] @ p.skel.ibm[I[bn]]
            k_ = side == sg
            Xr[k_] = mesh.P0[k_] @ Sb[:3, :3].T + Sb[:3, 3]
        relr = Xr - Oj
        sr = relr @ nb - offn(Xr)
        Xr = Xr + np.maximum(side * m_ - side * sr, 0.0)[:, None] * side[:, None] * nb[None, :]
        band = jc.get("mitre_band", 0.04)          # the crease's reach off the plane (m), eased out
        on_m = free & (relr @ wv > cf["wedge"]) & (np.abs(sr) < band)
        wm = mi_w * f * (1 - smooth01(np.abs(sr) / band))
        mi_t = (np.nonzero(on_m)[0], Xr, wm)
    pr_w = jc.get("pressure", 0.0)
    pr_t = {}
    pto = jc.get("pressure_to", {"p": 1.0, "d": 1.0})      # the area the push restores, per side (of the rest's)
    cw = cf["contact"]
    m_ = cf["margin"]
    def across(rel, inwedge, cand, r):
        """Candidates with the other side's skin within r (m) of them in the plane's own coordinates (e1, e2)."""
        P2 = np.stack([rel @ wv, rel @ hv], 1)
        keep = np.zeros(mesh.n, bool)
        for sg in (1.0, -1.0):
            opp = np.nonzero(inwedge & (side == -sg))[0]
            mine = np.nonzero(cand & (side == sg))[0]
            if len(opp) and len(mine):
                d_, _ = cKDTree(P2[opp]).query(P2[mine])
                keep[mine[d_ < r]] = True
        return keep

    for rnd in range(cf["iters"] + 1):
        Vall = Y[mesh.rep]
        N = bends.normals(Vall, p.T)[mesh.first]
        rel = Y - Oj
        s = rel @ nb - offn(Y)
        inwedge = (rel @ wv > cf["wedge"]) & free & (f > 0.02)
        if sk is not None:                    # in the footprint: past the surface, or within `close` of it in the rim
            fpY = fpn(Y)
            viol = inwedge & (fpY > 0) & (side * s < m_ + close * (fpY < 1))
        else:
            viol = inwedge & (side * s < m_)
        if jc.get("footprint"):                # a girdle's plane is wide: contact only where the other part is across
            viol = viol & across(rel, inwedge, viol, jc["footprint"])
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
            if pr_w:                                   # pressure: the swell as a push along the skin's normal
                s_area[:] = 1.0
            sc_n = s_area
        if slabs and rnd > 0 and pr_w:
            O = G[st.j][:3, 3]
            push = np.zeros(mesh.n)
            for sl in slabs:
                ax = st.p3 if sl["side"] == "p" else st.d3(G)
                inc = np.zeros(len(sl["ts"]))
                for k_, t in enumerate(sl["ts"]):
                    per, A = bends.section(Vall, p.T, sl["sel"], O + t * ax, ax, rend=st.rend)
                    if np.isfinite(A) and np.isfinite(per) and per > 0:
                        inc[k_] = np.clip(cf.get("pressure_gain", 0.7) * (pto[sl["side"]] * sl["A0"][k_] - A) / per,
                                          -cf.get("pressure_step", 0.002), cf.get("pressure_step", 0.002))
                ts = sl["ts"]
                ii = np.interp(sl["tn"], np.r_[ts[0] - cf["area_fade"], ts, ts[-1] + cf["area_fade"]],
                               np.r_[0.0, inc, 0.0], left=0.0, right=0.0)
                push = np.where(sl["on"] & (np.abs(ii) > np.abs(push)), ii, push)
            push[active] = np.minimum(push[active], 0.0)
            if cf.get("pressure_band", 0) > 0:          # none at the contact's edge: the corner's normals converge
                sw = side * ((Y - Oj) @ nb - offn(Y)) - m_
                fade = np.where((Y - Oj) @ wv > cf["wedge"], smooth01(sw / cf["pressure_band"]), 1.0)
                push = np.where(push > 0, push * fade, push)
            pr_t = {i: Y[i] + push[i] * N[i] for i in np.nonzero(np.abs(push) > 1e-7)[0]}
            log.setdefault("push_mm", []).append(round(float(np.abs(push).max() * 1000), 2))
            log.setdefault("area_k", []).append([np.round(sl["k"], 3).tolist() for sl in slabs])
        if rnd == cf["iters"]:
            if jc.get("clamp"):                    # the plane as a hard wall at the end: no node in the wedge past it
                rel = Y - Oj
                s = rel @ nb - offn(Y)
                bad = (rel @ wv > cf["wedge"]) & free & (f > 0.02) & (side * s < m_)
                if sk is not None:            # the wall over the footprint, its rim too: no skin crosses the surface
                    bad &= fpn(Y) > 0
                if jc.get("footprint"):
                    bad = bad & across(rel, (rel @ wv > cf["wedge"]) & free & (f > 0.02), bad, jc["footprint"])
                Y[bad] += ((side[bad] * m_ - s[bad]))[:, None] * nb
                Vall = Y[mesh.rep]
                N = bends.normals(Vall, p.T)[mesh.first]
                log["clamped"] = int(bad.sum())
            sc = ray.scene(Vall, p.T)
            near = fi[f[fi] > 0.02]
            log["iters"].append({"inside_parity": int(ray.inside(sc, Y[near] + 3e-4 * N[near]).sum()),
                                 "contact_pts": int(active.sum()), "outline_pts": len(out_t)})
            break
        Wi = a_data.copy()
        tgt = a_data[:, None] * X[fi]
        if mi_t is not None:
            nodes_m, Xr_, wm_ = mi_t
            np.add.at(Wi, pos[nodes_m], wm_[nodes_m])
            np.add.at(tgt, pos[nodes_m], wm_[nodes_m, None] * Xr_[nodes_m])
        for node, t in pr_t.items():
            Wi[pos[node]] += pr_w
            tgt[pos[node]] += pr_w * t
        for node, t in out_t.items():
            wo = cf["outline"] * f[node]
            Wi[pos[node]] += wo
            tgt[pos[node]] += wo * t
        tgtF = tgt @ Fr.T                                   # in the plane's frame
        Wn = np.zeros(len(fi))
        ai = pos[np.nonzero(active & free)[0]]
        Wn[ai] = cw * (fpn(Y[fi[ai]]) if sk is not None else 1.0)
        tgtF[ai, 2] += Wn[ai] * (side[fi[ai]] * m_ + (Oj @ nb) + offn(Y)[fi[ai]])
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
            sa = side * ((Y - Oj) @ nb - offn(Y)) - m_
            rel_ = active & (sa > cf.get("release_tol", 2e-5))
            if sk is not None:                # two skins pressed together are not let go inside the footprint
                rel_ &= fpn(Y) <= 0
            active &= ~rel_
        else:
            rel_ = np.zeros(mesh.n, bool)
        log["iters"].append({"contact_pts": int(active.sum()), "released": int(rel_.sum()), "outline_pts": len(out_t), "move_mm": round(float(np.linalg.norm(Y - X, axis=1).max() * 1000), 1)})
    return Y, f, free, M, log
