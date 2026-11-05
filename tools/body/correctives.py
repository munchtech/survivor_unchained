"""Stage 7: the correctives, computed (never sculpted), as a build step for any slider body.

    python tools/body/correctives.py <out_dir> [--only elbow,knee] [--tier close|play]
           (build.py and build_topo.py run it after the export, each tier on its own mesh)

Reads <out>/stage/body_lbs.glb (the export without shapes; made from <out>/body.glb the first time) and <out>/rig.json;
writes <out>/body.glb with the shapes on the body mesh, rig.json "correctives" (each shape's weight law,
tools/body/rig_drive.py), and <out>/stage/correctives.json (per key: iterations, contacts, outline pull, sizes).
Data: tools/body/correctives.json (the joints, their keys, regions and the solve's weights).

Per joint and key pose (the left side; the right is its mirror), with the pose posed exactly as the check poses it
(bends.Strip on the lbs poser with the rig's drivers, no shapes):
  X  the LBS + drivers posed surface (welded by place: seams move as one; the head and the neck ring held);
  region  f = 1 - smoothstep((|p0 - c0| - r_in) / (r_out - r_in)) round the joint's rest head (none outside r_out);
  solve   Y = argmin  sum |(L Y)_i - R_i (L P0)_i|^2           a smooth-skin energy: the rest surface's uniform
                                                                Laplacian, each point's turned by its skinning
                                                                rotation (the polar part of its blended matrix):
                                                                the rest shape's detail, no LBS collapse
                    + sum a (1 - f_i)^2 |Y_i - X_i|^2           falloff to the posed surface at the region's edge
                    + sum w_c |Y_i - t_i|^2                     contact: points found inside the posed surface
                                                                (ray parity) and the opposing points they went into
                                                                (the nearest posed points over 20 mm away at rest)
                                                                each pushed half the gap + margin along the
                                                                opposing normal: the crease folds, never crosses
                    + sum w_o f_i |Y_i - o_i|^2                 outline: points on the side view's outline (the
                                                                check's view) moved in the view plane to the
                                                                reference profile's nearest point (the joint's
                                                                listed curves, within `cap`)
          iterated (targets refreshed from each solve; contacts kept once found);
  shape   d_i = M_i^-1 Y_i - p0_i (M_i the vertex's blended skin matrix: shapes add before skinning), 0 outside.
Weight laws (rig.json "correctives", rig_drive.py): elbow and knee "flex" (smoothstep hats over the absolute
flexion, rest = no shape), shoulder and hip "rbf" over the bone's direction in its parent's frame.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import sys
import time

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

import bends  # noqa: E402
import glbwrite  # noqa: E402
import ray  # noqa: E402
from gl import weld  # noqa: E402
from posers import LbsPoser  # noqa: E402
from tools.body import rig_drive  # noqa: E402

CONF = os.path.join(HERE, "correctives.json")


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ the mesh --
class Mesh:
    """The poser's points welded by place; the uniform Laplacian; the head's nodes held."""

    def __init__(self, poser):
        self.p = poser
        rep = weld(poser.P0, 1e-6)
        self.rep = rep
        n = rep.max() + 1
        self.n = n
        first = np.full(n, -1)
        first[rep[::-1]] = np.arange(len(rep))[::-1]
        self.first = first
        self.P0 = poser.P0[first]
        T = rep[poser.T]
        e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
        e = e[e[:, 0] != e[:, 1]]
        e = np.unique(np.sort(e, 1), axis=0)
        A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
        deg = np.asarray(A.sum(1)).ravel()
        self.E = e
        self.Tw = T
        self.Lg = (sp.diags(deg) - A).tocsr()
        self.held = np.zeros(n, bool)
        self.held[rep[poser.piece == "head"]] = True

    def skin_mats(self, G):
        """Each poser vertex's blended skin matrix [V,4,4]."""
        S = G @ self.p.skel.ibm
        M = np.zeros((len(self.p.Pb), 4, 4))
        for k in range(self.p.J.shape[1]):
            M += self.p.W[:, k, None, None] * S[self.p.J[:, k]]
        return M


def polar(M3):
    U, _, Vt = np.linalg.svd(M3)
    R = U @ Vt
    bad = np.linalg.det(R) < 0
    U[bad, :, 2] *= -1
    return U @ Vt


# ------------------------------------------------------------------ key poses --
def key_strip(poser, rig, frame, motion, s):
    """A bends.Strip, or for hip_abd a hip strip turned about her front (outward)."""
    if motion != "hip_abd":
        return bends.Strip(poser, rig, frame, motion, s)
    st = bends.Strip(poser, rig, frame, "hip_flex", s)
    out = frame.lat * (1 if s == "l" else -1)
    st.axis = bends.unit(np.cross(out, frame.up))
    st.meas = lambda d: math.degrees(math.atan2(d @ out, -(d @ frame.up)))
    st.rest_deg = st.meas(st.u_d0)
    st.solved = {}
    st.motion = "hip_abd"
    return st


def key_pose(st, deg):
    """The pose at absolute `deg` as Strip.posed makes it (deg 0 is a real angle here, not the rest)."""
    p = st.poser
    aim = deg
    for _ in range(9):
        V, G, info = p.pose([(st.bone, bends.rot(st.axis, st.turn(aim)))])
        err = st.achieved(G) - deg
        if abs(err) < 0.1:
            break
        aim -= err
    return V, G


# --------------------------------------------------------------------- solve --
def parts(mesh, jc, s):
    """The joint's two rigid parts at rest: distal weight per node, proximal and distal surface nodes, rest normals."""
    p = mesh.p
    I = p.index
    sub = lambda x: x.replace("{s}", s)
    wd = p.D[:, p.subtree(I[sub(jc["distal"])])].sum(1)[mesh.first]
    helpers = [I[sub(h)] for h in jc.get("helpers", []) if sub(h) in I]
    wh = p.D[:, helpers].sum(1)[mesh.first] if helpers else np.zeros(mesh.n)
    N0 = bends.normals(p.P0, p.T)[mesh.first]
    lo, hi = jc.get("part_cut", [0.1, 0.9])
    return wd, np.nonzero((wd < lo) & (wh < 1 - hi))[0], np.nonzero(wd > hi)[0], N0


def signed(surf_, Q):
    """Signed distance of points Q to a rigid part's surface (its nearest node and that node's normal): sd, the
    lateral offset from the normal line, and the normal."""
    tr, Pr, Nr = surf_
    _, k = tr.query(Q)
    rel = Q - Pr[k]
    sd = np.einsum("ij,ij->i", rel, Nr[k])
    return sd, np.linalg.norm(rel - sd[:, None] * Nr[k], axis=1), Nr[k]


def prox_dir(st, G):
    """From the joint toward the proximal side: up the proximal bone (elbow, knee), else the torso's (the strip's
    rest p3, the trunk held)."""
    if st.prox is not None:
        return G[st.poser.index[st.prox]][:3, 3] - G[st.j][:3, 3]
    return st.p3


def solve_key(mesh, st, V, G, jc, cf, ref):
    """The desired posed surface Y (welded) for one key pose, and its log."""
    p = mesh.p
    I = p.index
    sub = lambda x: x.replace("{s}", st.s)
    c0 = p.rest[I[sub(jc["center"])]][:3, 3]
    d = np.linalg.norm(mesh.P0 - c0, axis=1)
    f = 1 - smooth01((d - jc["r_in"]) / (jc["r_out"] - jc["r_in"]))
    free = (d < jc["r_out"]) & ~mesh.held
    rn = np.zeros(mesh.n, bool)
    rn[mesh.rep[st.rend]] = True
    if jc.get("free_rend"):                 # a girdle's sphere reaches the other limbs: they stay as posed (obstacles)
        free &= rn
    fi = np.nonzero(free)[0]
    pos = -np.ones(mesh.n, np.int64)
    pos[fi] = np.arange(len(fi))
    X = V[mesh.first]
    M = mesh.skin_mats(G)
    R = polar(M[mesh.first][:, :3, :3])
    E = mesh.E
    eP = mesh.P0[E[:, 0]] - mesh.P0[E[:, 1]]
    a_data = cf["data"] * (1 - f[fi]) ** 2 + cf["floor"]
    Lg = mesh.Lg[fi][:, fi]
    Lfx = mesh.Lg[fi][:, ~free]
    Xfix = X[~free]
    # the two rigid parts, posed with their bones: the static surfaces a fold presses against
    wd, ps, ds, N0 = parts(mesh, jc, st.s)
    surf = {}
    for side, nodes, bone in (("p", ps, sub(jc["proximal"])), ("d", ds, sub(jc["distal"]))):
        nodes = nodes[d[nodes] < jc["r_out"] + 0.05]
        Sb = G[I[bone]] @ p.skel.ibm[I[bone]]
        Pr = mesh.P0[nodes] @ Sb[:3, :3].T + Sb[:3, 3]
        Nr = N0[nodes] @ polar(Sb[None, :3, :3])[0].T
        surf[side] = (cKDTree(Pr), Pr, Nr)
    test = {"d": fi[(wd[fi] >= 0.5) & (f[fi] > 0.02)], "p": fi[(wd[fi] < 0.5) & (f[fi] > 0.02)]}
    if jc.get("obstacles"):                 # the other limbs near the joint (the other thigh at the crotch), as posed
        oth = "r" if st.s == "l" else "l"
        ob = np.zeros(mesh.n, bool)
        for b in jc["obstacles"]:
            ob |= p.D[:, p.subtree(I[b.replace("{o}", oth)])].sum(1)[mesh.first] >= 0.5
        ob &= ~free & (d < jc["r_out"] + 0.05)
        No = bends.normals(X[mesh.rep], p.T)[mesh.first]
        on_ = np.nonzero(ob)[0]
        surf["o"] = (cKDTree(X[on_]), X[on_], No[on_])
    # the crease side (rest space): toward where the distal bone turned
    je, jd = I[sub(jc["distal_end"])], I[sub(jc["distal"])]
    d_rest = bends.unit(p.rest[je][:3, 3] - p.rest[jd][:3, 3])
    d_key = bends.unit(G[je][:3, 3] - G[jd][:3, 3])
    bdir = bends.unit(d_key - d_rest)
    br = jc.get("band_r", cf["band_r"])
    band = (1 - smooth01((d - br[0]) / (br[1] - br[0]))) * smooth01(((mesh.P0 - c0) @ bdir + cf["band_in"]) / cf["band_w"])
    band[~free] = 0.0
    crease_side = smooth01(((mesh.P0 - c0) @ bdir + cf["band_in"]) / cf["band_w"])
    Y = X.copy()
    cons = {}
    log = {"free": int(len(fi)), "iters": []}
    vw = st.view(2 * bends.PX_CLOSE) if ref else None
    dense = (np.concatenate([bends.resample(ref[k]) for k in jc.get("pull", []) if k in ref])
             if ref and jc.get("pull") else None)
    rend_nodes = np.zeros(mesh.n, bool)
    rend_nodes[mesh.rep[st.rend]] = True
    vol0 = volume(mesh.P0, mesh.Tw)
    # section areas near the joint (the check's cuts): each slab's rings swell (rest edges scaled) to their rest area
    slabs = []
    O0 = p.rest[st.j][:3, 3]
    for side, ts in (jc.get("area") or {}).items():
        sel = st.seg_p if side == "p" else st.seg_d
        if not sel.any():
            continue
        ax0 = st.p3 if side == "p" else st.u_d0
        on = np.zeros(mesh.n, bool)
        on[mesh.rep[sel]] = True
        A0 = [bends.section(p.P0, p.T, sel, O0 + t * ax0, ax0, rend=st.rend)[1] for t in ts]
        slabs.append({"side": side, "ts": np.asarray(ts, float), "sel": sel, "on": on & free,
                      "tn": (mesh.P0 - O0) @ ax0, "A0": np.asarray(A0), "k": np.ones(len(ts))})
    kap, hist = 0.0, []
    hm = None
    if jc.get("hold_mid"):                  # [band m, weight, bone]: nodes within band of x = 0 pulled to that bone's rigid pose
        band_m, w_m, hb = jc["hold_mid"]
        Sh = G[I[hb]] @ p.skel.ibm[I[hb]]
        Xh = mesh.P0 @ Sh[:3, :3].T + Sh[:3, 3]
        hm = w_m * (1 - smooth01(np.abs(mesh.P0[:, 0]) / band_m)) * (f > 0.02)
    sc_n = np.ones(mesh.n)
    for rnd in range(cf["iters"] + 1):
        Vall = Y[mesh.rep]
        N = bends.normals(Vall, p.T)[mesh.first]
        # contacts: the fold is where the two rigid parts' signed distances meet (s_other = s_own); a part's
        # point past it (s_other - s_own < margin) is moved along their gradient (n_other - n_own) back to it
        n_hit = 0
        if jc.get("fold") == "plane":
            # the fold is the plane through the joint between the two limbs (the bisector of the proximal and the
            # distal directions): on the crease side, proximal points stay on its proximal side, distal ones on theirs
            a_ = bends.unit(prox_dir(st, G))
            b_ = st.d3(G)
            nb = bends.unit(a_ - b_)
            Oj = G[st.j][:3, 3]
            for nodes, sgn in ((test["p"], 1.0), (test["d"], -1.0)):
                nodes = nodes[(Y[nodes] - Oj) @ bends.unit(a_ + b_) > cf["wedge"]]    # in the wedge between the limbs
                sd = sgn * ((Y[nodes] - Oj) @ nb)
                bad = sd < cf["margin"]
                n_hit += int(bad.sum())
                for node, s_ in zip(nodes[bad], sd[bad]):
                    cons[node] = Y[node] + sgn * (cf["margin"] - s_) * nb
            # the crease's own skin (between the parts' weights) in the wedge: onto the plane, the fold's floor
            cr = fi[(np.abs(wd[fi] - 0.5) < cf["crease_wd"]) & ((Y[fi] - Oj) @ bends.unit(a_ + b_) > cf["wedge"])]
            for node in cr:
                cons[node] = Y[node] - ((Y[node] - Oj) @ nb) * nb
        for side, other in ((("d", "p"), ("p", "d")) if jc.get("fold") != "plane" else ()):
            nodes = test[side]
            sd_o, lat_o, n_o = signed(surf[other], Y[nodes])
            sd_w, lat_w, n_w = signed(surf[side], Y[nodes])
            sd_w = np.where(lat_w < cf["lat_max"], sd_w, 0.0)
            n_w = np.where((lat_w < cf["lat_max"])[:, None], n_w, 0.0)
            gap = sd_o - sd_w
            bad = (gap < cf["margin"]) & (sd_o > -cf["depth_max"]) & (lat_o < cf["lat_max"])
            n_hit += int(bad.sum())
            gdir = n_o[bad] - n_w[bad]
            g2 = np.maximum(np.einsum("ij,ij->i", gdir, gdir), 0.25)
            step = ((cf["margin"] - gap[bad]) / g2)[:, None] * gdir
            for node, st_ in zip(nodes[bad], step):
                cons[node] = Y[node] + st_
        if "o" in surf:                     # out of the obstacles, along their normal
            nodes = np.concatenate([test["p"], test["d"]])
            sd_o, lat_o, n_o = signed(surf["o"], Y[nodes])
            bad = (sd_o < cf["margin"]) & (sd_o > -cf.get("depth_max_o", 0.06)) & (lat_o < cf["lat_max"])
            n_hit += int(bad.sum())
            for node, s_, n_ in zip(nodes[bad], sd_o[bad], n_o[bad]):
                cons[node] = cons.get(node, Y[node]) + (cf["margin"] - s_) * n_
        # what the parts miss (the crease's own skin, between the parts): points inside the posed surface (ray
        # parity), pushed out half the way along the nearest posed point over 20 mm away at rest (and it back)
        if cf.get("parity", 0) and rnd < cf["iters"]:
            sc = ray.scene(Vall, p.T)
            near = fi[f[fi] > 0.02]
            hit = near[ray.inside(sc, Y[near] + 3e-4 * N[near])]
            if len(hit):
                dd, ii = cKDTree(Y).query(Y[hit], k=min(64, mesh.n))
                far = np.linalg.norm(mesh.P0[ii] - mesh.P0[hit][:, None], axis=2) > 0.02
                dd = np.where(far, dd, np.inf)
                kq = np.argmin(dd, 1)
                q = ii[np.arange(len(hit)), kq]
                ok = np.isfinite(dd[np.arange(len(hit)), kq])
                for i_, q_ in zip(hit[ok], q[ok]):
                    nq = N[q_]
                    gap = max(0.0, float((Y[q_] - Y[i_]) @ nq)) + cf["margin"]
                    for node, sgn in ((i_, 1.0), (q_, -cf["parity_give"])):
                        if free[node] and sgn:
                            cons[node] = cons.get(node, Y[node]) + sgn * 0.5 * gap * nq
        # outline: points on the side view's outline moved in the view's plane to the reference's nearest point
        out_t = {}
        if dense is not None and cf["outline"] > 0:
            mk = ray.mask(Vall, st.T_rend, vw)
            Ed = bends.edge_points(mk, vw)
            xy = vw.xy(Y)
            cand = np.nonzero(free & rend_nodes & (np.abs(N @ vw.cam) < 0.5))[0]
            de, _ = cKDTree(Ed).query(xy[cand])
            sil = cand[de < 0.7e-3]
            dr, ir = cKDTree(dense).query(xy[sil])
            for node, r_i, dd_ in zip(sil, ir, dr):
                if dd_ < jc.get("cap", 0.015):
                    dv = dense[r_i] - xy[node]
                    out_t[node] = Y[node] + dv[0] * vw.ex + dv[1] * vw.ey
        # volume: the crease band's rest edges scaled by 1 + kap band, kap solved (secant) for the rest volume
        if cf.get("volume", 0) and rnd > 0:
            dv = volume(Y, mesh.Tw) - vol0
            hist.append((kap, dv))
            if len(hist) == 1 or abs(hist[-1][1] - hist[-2][1]) < 1e-12:
                kap = kap + (cf["kap_step"] if dv < 0 else -cf["kap_step"])
            else:
                (k0, v0), (k1, v1) = hist[-2], hist[-1]
                kap = float(np.clip(k1 - v1 * (k1 - k0) / (v1 - v0), -0.2, cf["kap_max"]))
            g = band
            if cons:
                dc, _ = cKDTree(Y[np.array(sorted(cons))]).query(Y)
                g = band * smooth01(dc / cf["rim"])          # around the contact patch, not on it
            sc_n = 1.0 + kap * g
            log.setdefault("volume", []).append([round(kap, 4), round(dv * 1e6, 2)])
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
            s_area = 1.0 + (s_area - 1.0) * (1.0 - crease_side)    # the swell on the sides and back, not the crease
            if cons:
                s_area[np.array(sorted(cons))] = 1.0
            sc_n = (1.0 + kap * g if cf.get("volume", 0) else np.ones(mesh.n)) * s_area
            log.setdefault("area_k", []).append([np.round(sl["k"], 3).tolist() for sl in slabs])
        if rnd == cf["iters"]:
            sc = ray.scene(Vall, p.T)
            near = fi[f[fi] > 0.02]
            log["iters"].append({"inside_parity": int(ray.inside(sc, Y[near] + 3e-4 * N[near]).sum()),
                                 "contact_hits": n_hit, "outline_pts": len(out_t)})
            break
        W = a_data.copy()
        tgt = a_data[:, None] * X[fi]
        if hm is not None:                  # the midline held where its own bone puts it (the perineum)
            W += hm[fi]
            tgt += hm[fi, None] * Xh[fi]
        for node, t in cons.items():
            W[pos[node]] += cf["contact"]
            tgt[pos[node]] += cf["contact"] * t
        for node, t in out_t.items():
            wo = cf["outline"] * f[node]
            W[pos[node]] += wo
            tgt[pos[node]] += wo * t
        lu = splu((Lg + sp.diags(W)).tocsc())
        for _ in range(cf["arap"]):
            # global: sum_j (y_i - y_j) = sum_j (R_i + R_j) / 2 (s_i + s_j) / 2 (p_i - p_j), plus the soft targets
            Re = 0.5 * (R[E[:, 0]] + R[E[:, 1]]) * (0.5 * (sc_n[E[:, 0]] + sc_n[E[:, 1]]))[:, None, None]
            r = np.einsum("nij,nj->ni", Re, eP)
            b = np.zeros((mesh.n, 3))
            np.add.at(b, E[:, 0], r)
            np.add.at(b, E[:, 1], -r)
            rhs = b[fi] - Lfx @ Xfix + tgt
            Y = X.copy()
            Y[fi] = np.stack([lu.solve(rhs[:, c]) for c in range(3)], 1)
            # local: each node's best turn of its rest edges onto its posed ones
            eY = Y[E[:, 0]] - Y[E[:, 1]]
            Sm = np.einsum("ni,nj->nij", eP, eY)
            Cv = np.zeros((mesh.n, 3, 3))
            np.add.at(Cv, E[:, 0], Sm)
            np.add.at(Cv, E[:, 1], Sm)
            U, _, Vt = np.linalg.svd(Cv[fi])
            Rn = np.einsum("nji,nkj->nik", Vt, U)
            bad = np.linalg.det(Rn) < 0
            if bad.any():
                U2 = U.copy()
                U2[bad, :, 2] *= -1
                Rn[bad] = np.einsum("nji,nkj->nik", Vt[bad], U2[bad])
            R[fi] = Rn
        log["iters"].append({"contact_hits": n_hit, "contact_pts": len(cons), "outline_pts": len(out_t)})
    return Y, f, free, M, log


def volume(P, T):
    return float(np.einsum("ij,ij->i", P[T[:, 0]], np.cross(P[T[:, 1]], P[T[:, 2]])).sum() / 6)


def rest_delta(mesh, Y, f, free, M):
    """Per poser vertex (the body's), the rest-space delta that skins to Y: M^-1 Y - p0, 0 off the region."""
    p = mesh.p
    body = np.nonzero(p.piece == "body")[0]
    sel = body[free[mesh.rep[body]]]
    Yh = np.concatenate([Y[mesh.rep[sel]], np.ones((len(sel), 1))], 1)
    q = np.linalg.solve(M[sel], Yh[..., None])[..., 0][:, :3]
    D = np.zeros((len(body), 3))
    D[np.searchsorted(body, sel)] = q - p.Pb[sel]
    return D


def mirror_map(P, tol=1e-5):
    tr = cKDTree(P)
    d, i = tr.query(P * np.array([-1.0, 1, 1]))
    return np.where(d < tol, i, -1)


def normal_delta(P, T, D):
    n0 = bends.normals(P, T)
    n1 = bends.normals(P + D, T)
    return n1 - n0


def topo_mirror(mo, Pb, stage_npz=None):
    """The body points' mirror by OUR topology: mo[i] (topology vertex i's mirror, -1 on one side's listing) both
    ways, the midline (no pair: |x| <= 5 mm on her) its own mirror (it was -1: 212 points, the right shapes lost
    the perineum's and the spine's share). When the export appends seam copies after our n vertices (the UV split),
    each maps through its source vertex: mir[k] = mirror(src[k]) (src from the stage npz's "src" if it has one,
    else the copy's coincident point among the first n), so the right side never falls back to a position mirror."""
    n = len(mo)
    m = np.full(n, -1)
    r_ = np.nonzero(mo >= 0)[0]
    m[r_] = mo[r_]
    m[mo[r_]] = r_
    m[m < 0] = np.nonzero(m < 0)[0]
    if len(Pb) == n:
        return m
    src = None
    if stage_npz and os.path.exists(stage_npz):
        z = np.load(stage_npz)
        if "src" in z.files and len(z["src"]) == len(Pb):
            src = z["src"].astype(np.int64)
    if src is None:
        src = np.arange(len(Pb))
        _, k = cKDTree(Pb[:n]).query(Pb[n:])
        src[n:] = k
    return m[src]


# ----------------------------------------------------------------------- run --
def shape_name(jc, motion, deg):
    tag = {"shoulder_abd": "abd", "shoulder_flex": "flex" if deg >= 0 else "ext", "hip_flex": "flex",
           "hip_abd": "abd", "elbow": "flex", "knee": "flex"}[motion]
    return f"{jc['name']}_{tag}{int(round(abs(deg)))}_{{s}}"


TIERS = {"close": ("body.glb", "rig.json", "body_lbs.glb", "shapes.npz", "correctives.json"),
         "play": ("play.glb", "play_rig.json", "play_lbs.glb", "play_shapes.npz", "play_correctives.json")}


def run(out, only=None, tier="close", fresh=False):
    """`fresh`: the export was just written (build_topo's stage 6): it becomes the shapeless base."""
    t0 = time.time()
    conf = json.load(open(CONF))
    cf = conf["solve"]
    f_glb, f_rig, f_base, f_shapes, f_rep = TIERS[tier]
    base = os.path.join(out, "stage", f_base)
    if fresh or not os.path.exists(base):
        shutil.copyfile(os.path.join(out, f_glb), base)
    rig_path = os.path.join(out, f_rig)
    rig = json.load(open(rig_path))
    rig["correctives"] = [c for c in rig.get("correctives", []) if only and c.get("joint") not in only]
    poser = LbsPoser(base, dict(rig, correctives=[]))
    mesh = Mesh(poser)
    frame = bends.Frame(poser, rig)
    body = np.nonzero(poser.piece == "body")[0]
    Pb, Tb = poser.Pb[body], poser.T[(poser.piece[poser.T] == "body").all(1)]
    mir = mirror_map(Pb)
    tp = os.path.join(HERE, "out", "topo", f"{tier}.npz")       # our topology's own mirror (her forms are not symmetric
    if os.path.exists(tp):                                       # to 1e-5 m: 3005 points went unmatched by place)
        mir = topo_mirror(np.load(tp)["mirror_of"], Pb, os.path.join(out, "stage", f"{tier}.npz"))
    old = {}
    if only and os.path.exists(os.path.join(out, "stage", f_shapes)):
        z = np.load(os.path.join(out, "stage", f_shapes))
        old = {k: z[k] for k in z.files}
    shapes, rep = {}, {}
    for jc in conf["joints"]:
        if jc.get("held"):                  # documented in correctives.json, not shipped (its "why")
            continue
        if only and jc["name"] not in only:
            for k, v in old.items():
                if k.startswith(jc["name"] + "_"):
                    shapes[k] = v
            continue
        row = {"joint": jc["name"], "law": jc["law"]}
        names, dirs = [], []
        strips = {}
        chain = {}
        if jc.get("fold") in ("stepped", "pair", "field"):  # the whole arc marched at once (contact_*.py)
            if jc["fold"] == "field":
                import contact_field as chain_mod
            elif jc["fold"] == "pair":
                import contact_pair as chain_mod
            else:
                import contact_fold as chain_mod
            st = key_strip(poser, rig, frame, jc["keys"][0][0], "l")
            strips[jc["keys"][0][0]] = st
            t = time.time()
            for k_, Y, f, free, M, G, lg in chain_mod.solve_chain(mesh, st, jc, {**cf, **jc.get("solve", {})}):
                chain[k_] = (Y, f, free, M, G, lg)
            print(f"  {jc['name']} march {round(time.time() - t, 1)} s", flush=True)
        for motion, deg in jc["keys"]:
            st = strips.get(motion) or key_strip(poser, rig, frame, motion, "l")
            strips[motion] = st
            nm = shape_name(jc, motion, deg)
            V, G = key_pose(st, deg) if not chain else (None, chain[float(deg)][4])
            pk = jc.get("per_key", {}).get(str(int(round(deg))), {})               # a key's own settings
            jk = dict(jc, **pk, _deg=deg)
            spec = bends.load_ref(motion, deg) if motion in bends.MOTIONS and not chain else None
            ref = None
            if spec and jk.get("pull"):
                V0, G0, _ = st.posed(0)
                vw_hi = st.view(2 * bends.PX_CLOSE)
                m0 = ray.mask(V0, st.T_rend, vw_hi)
                pl0 = bends.Plane2(st, G0)
                ref = bends.build_ref(spec, bends.Plane2(st, G), bends.radii(st, m0, vw_hi, pl0), (m0, vw_hi))
            t = time.time()
            cfk = {**cf, **jc.get("solve", {}), **pk.get("solve", {})}
            if chain:
                Y, f, free, M, _, lg = chain[float(deg)]
                lg = dict(lg, iters=[{"inside_parity": lg["march"]["inside"]}])
            elif jk.get("fold") == "flatten":
                import crease_fold
                Y, f, free, M, lg = crease_fold.solve_key(mesh, st, V, G, jk, cfk, ref)
            else:
                Y, f, free, M, lg = solve_key(mesh, st, V, G, jk, cfk, ref)
            D = rest_delta(mesh, Y, f, free, M)
            DL = D.copy()
            if jc.get("one_side", True):               # a limb's shape stays on its side
                DL[Pb[:, 0] < -1e-6] = 0.0
            DR = np.zeros_like(D)
            ok = mir >= 0
            DR[ok] = DL[mir[ok]] * np.array([-1.0, 1, 1])
            shapes[nm.replace("{s}", "l")] = DL
            shapes[nm.replace("{s}", "r")] = DR
            lg.update(deg=deg, motion=motion, max_mm=round(float(np.linalg.norm(DL, axis=1).max() * 1000), 2),
                      moved=int((np.linalg.norm(DL, axis=1) > 1e-4).sum()), s=round(time.time() - t, 1))
            row.setdefault("keys", []).append(lg)
            names.append(nm)
            if jc["law"] in ("rbf", "arc"):
                dirs.append(rig_drive.direction(poser, G, jc["bone"].replace("{s}", "l"), jc["end"].replace("{s}", "l"),
                                                jc["frame"].replace("{s}", "l")))
            print(f"  {nm} {deg}: {lg['iters'][-1]} max {lg['max_mm']} mm, {lg['s']} s", flush=True)
        rep[jc["name"]] = row
        if jc["law"] == "flex":
            bones = jc["bones"]
            rest_F = rig_drive.flexion(poser, poser.rest, *[b.replace("{s}", "l") for b in bones])
            keys = sorted([(float(k[1]), n) for k, n in zip(jc["keys"], names)] + [(rest_F, None)])
            rig["correctives"].append({"joint": jc["name"], "law": "flex", "bones": bones,
                                       "keys": [round(k, 3) for k, _ in keys], "shapes": [n for _, n in keys]})
        elif jc["law"] == "arc":
            d0 = rig_drive.direction(poser, poser.rest, jc["bone"].replace("{s}", "l"), jc["end"].replace("{s}", "l"),
                                     jc["frame"].replace("{s}", "l"))
            K = np.stack([d0] + dirs)
            mx = np.array([-1.0, 1, 1])
            rig["correctives"].append({"joint": jc["name"], "law": "arc", "bone": jc["bone"], "end": jc["end"],
                                       "frame": jc["frame"], "gate_deg": jc["gate_deg"], "shapes": names,
                                       "keys": {"l": np.round(K, 6).tolist(), "r": np.round(K * mx, 6).tolist()}})
        else:
            d0 = rig_drive.direction(poser, poser.rest, jc["bone"].replace("{s}", "l"), jc["end"].replace("{s}", "l"),
                                     jc["frame"].replace("{s}", "l"))
            K = np.stack([d0] + dirs)
            Mm = rig_drive.rbf_solve(K, jc["sigma_deg"])
            mx = np.array([-1.0, 1, 1])
            rig["correctives"].append({"joint": jc["name"], "law": "rbf", "bone": jc["bone"], "end": jc["end"],
                                       "frame": jc["frame"], "sigma_deg": jc["sigma_deg"], "shapes": names,
                                       "keys": {"l": np.round(K, 6).tolist(), "r": np.round(K * mx, 6).tolist()},
                                       "M": {"l": np.round(Mm, 6).tolist(), "r": np.round(Mm, 6).tolist()}})
    # write: the shapes on the body (glTF order: the poser's body points are the mesh's), normals' deltas with them
    order = []
    for c in rig["correctives"]:
        for s in ("l", "r"):
            order += [n.replace("{s}", s) for n in c.get("shapes", []) if n]
    tg = {n: (shapes[n].astype(np.float32), normal_delta(Pb, Tb, shapes[n]).astype(np.float32)) for n in order}
    glbwrite.set_targets(base, rig.get("body_mesh", "Heroine"), tg, os.path.join(out, f_glb))
    np.savez_compressed(os.path.join(out, "stage", f_shapes), **shapes)
    with open(rig_path, "w") as fh:
        json.dump(rig, fh, indent=1)
    rep["shapes"] = len(order)
    rep["mirror_unmatched_body_points"] = int((mir < 0).sum())
    rep["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(out, "stage", f_rep), "w") as fh:
        json.dump(rep, fh, indent=1)
    print("CORRECTIVES", tier, len(order), "shapes", rep["seconds"], "s")
    return rep


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
        a = [x for x in a if x != sys.argv[sys.argv.index("--only") + 1]]
    tier = sys.argv[sys.argv.index("--tier") + 1] if "--tier" in sys.argv else "close"
    a = [x for x in a if x != tier]
    run(os.path.abspath(a[0]), only, tier)
