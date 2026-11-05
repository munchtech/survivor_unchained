#!/usr/bin/env python
"""check.py's `topology` section: the topology gates (topo_gates.py's body-general ones) measured on a BUILT body.

Derivation: (a) game need: a body that bends and shades well needs no folds, thin quads, tiny edges or poles in a
bend zone, whatever its sliders or outfit; (b) named reference: topo_gates.py (fold 60 deg, aspect 4, edge 2 mm,
pole margin 40 mm, imported not copied) and loopplan.json's bend widths (elbow 40/25 mm, knee 50/30 mm);
(c) inheritance: the quads come from the topology npz the glb names (extras.body_base.topology; --topo overrides),
the glb body mesh being that npz's vertices in the same order (build_topo/glbwrite write identity order).
Bend zones come from the glb's OWN skeleton (not a reference mesh): each zone is the built body's own vertices of the
limb parts (npz `parts`) inside the zone's slab, left side (the right is folded onto it), as topo_gates.zone_points.
Hip: within 60 mm of the thigh root seam's front/back curve; shoulder: the arm side to 110 mm below the armpit
(the armpit = the lowest arm vertex that shares an edge with the trunk); neck base: neck + upper trunk above the
clavicle line out to 75 mm.  Nothing is keyed to a MakeHuman vertex id.
"""
from __future__ import annotations

import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree

import topo_gates as G

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BEND = {"elbow": (0.04, 0.025), "knee": (0.05, 0.03)}          # (b) loopplan.json: (bend, end_bend)
PLANE = 3                                                      # topo_build.py's flag for a plane-fit ring


def topo_path(glb, override=None):
    if override:
        return Path(override)
    bb = (glb.js.get("extras") or {}).get("body_base") or {}
    p = bb.get("topology")
    return (REPO / p) if p else None


def _edges(Q):
    return np.unique(np.sort(np.concatenate([Q[:, [k, (k + 1) % 4]] for k in range(4)]), 1), axis=0)


def _boundary_verts(Q, n):
    e = np.sort(np.concatenate([Q[:, [k, (k + 1) % 4]] for k in range(4)]), 1)
    key = e[:, 0].astype(np.int64) * n + e[:, 1]
    u, c = np.unique(key, return_counts=True)
    bd = u[c == 1]
    return np.unique(np.concatenate([bd // n, bd % n]))


def _zones(V, z, sk):
    P = list(z["parts"])
    part = z["part"]

    def ids(*n):
        return np.isin(part, [P.index(k) for k in n])

    arm = ids("arm", "elbow", "forearm")
    leg = ids("thigh", "knee", "shin")
    hand, foot = ids("hand"), ids("foot")
    N = sk.names

    def J(n):
        return np.asarray(sk.rest[N.index(n)][:3, 3], float)

    X = V * np.where(V[:, :1] < 0, [-1.0, 1, 1], 1.0)
    Zs, joints = {}, {}
    for nm, (a, b, c, ks_, ke_) in {"elbow": ("upperarm_l", "lowerarm_l", "hand_l", arm, hand),
                                    "knee": ("thigh_l", "calf_l", "foot_l", leg, foot)}.items():
        bend, eb = BEND[nm]
        j, d_in, d_out = J(b), G.U(J(b) - J(a)), G.U(J(c) - J(b))
        nb = G.U(d_in + d_out)
        joints[nm] = {"J": j, "bisector": nb}
        near = np.linalg.norm(X - j, axis=1) < bend + 0.12
        Zs[nm] = X[near & ks_ & (np.abs((X - j) @ nb) <= bend)]
        nm2 = "wrist" if nm == "elbow" else "ankle"
        ce = J(c)
        near = np.linalg.norm(X - ce, axis=1) < eb + 0.12
        Zs[nm2] = X[near & (ks_ | ke_) & (np.abs((X - ce) @ d_out) <= eb)]
    E = _edges(z["Q"])
    tr = ~(arm | leg | hand | foot | ids("neck"))
    seam = E[(arm[E[:, 0]] & tr[E[:, 1]]) | (arm[E[:, 1]] & tr[E[:, 0]])]
    sv = np.unique(seam)
    sv = sv[V[sv, 0] > 0]
    ap = V[sv[np.argmin(V[sv, 1])]] if len(sv) else J("upperarm_l")
    d_up = G.U(J("lowerarm_l") - J("upperarm_l"))
    u = (X - J("upperarm_l")) @ d_up
    u_ap = float((ap - J("upperarm_l")) @ d_up)
    Zs["shoulder"] = X[(arm & (u <= u_ap + 0.110)) | (np.linalg.norm(X - ap, axis=1) < 0.035)]
    th = ids("thigh")
    other = ~(th | ids("knee", "shin", "foot"))
    hs = np.unique(E[(th[E[:, 0]] & other[E[:, 1]]) | (th[E[:, 1]] & other[E[:, 0]])])
    hs = hs[(V[hs, 0] > 0) & (V[hs, 1] > J("thigh_l")[1] - 0.15)]   # the root ring, not the inner thigh's crotch seam
    if len(hs):
        lat = V[hs, 0] - V[hs, 0].min()
        hs = hs[lat < 0.6 * lat.max()]
        Zs["hip"] = X[cKDTree(V[hs]).query(X)[0] <= 0.060]
    # neck base (b: topo_gates): above the clavicle heads rising 40 mm to C7 at the back, within 75 mm of the neck
    # ring's axis (the open boundary of the topology IS the neck ring), up to 10 mm over the ring
    bd = _boundary_verts(z["Q"], len(V))
    ring = V[bd]
    zax = 0.5 * (ring[:, 2].max() + ring[:, 2].min())
    th_ = np.arctan2(np.abs(X[:, 0]), X[:, 2] - zax)
    yb = float(J("clavicle_l")[1] - 0.005) + 0.04 * (1 - np.cos(th_)) / 2
    r = np.hypot(X[:, 0], X[:, 2] - zax)
    Zs["neck_base"] = X[(ids("neck", "trunk", "shoulder", "breast")) & (X[:, 1] >= yb) & (r < 0.075)
                        & (X[:, 1] < ring[:, 1].max() + 0.01)]
    return Zs, joints


def measure(V, z, sk):
    """V: the built body mesh's rest vertices (topology order); z: the topology npz arrays; sk: the glb skeleton."""
    V = np.asarray(V, float)
    Q = z["Q"]
    P = list(z["parts"])
    qpart, part = z["qpart"], z["part"]
    tmpl_q = np.isin(qpart, [P.index("hand"), P.index("foot")])
    n = G.quad_normals(V, Q)
    E, qa, qb = G.edge_pairs(Q)
    dih = np.degrees(np.arccos(np.clip((n[qa] * n[qb]).sum(1), -1, 1)))
    body_e = ~(tmpl_q[qa] | tmpl_q[qb])
    mid_v = np.abs(V[:, 0]) < 1e-4
    on_floor = mid_v[E[:, 0]] & mid_v[E[:, 1]]
    m = 0.5 * (V[E[:, 0]] + V[E[:, 1]])
    ty = float(sk.rest[sk.names.index("thigh_l")][1, 3])       # (b) topo_gates' thigh-gap box, relative to the thigh joint
    gap = (np.abs(m[:, 0]) <= 0.040) & (m[:, 1] >= ty - 0.092) & (m[:, 1] <= ty - 0.067) & (np.abs(m[:, 2]) <= 0.015)
    bad = body_e & ~on_floor & (dih > G.FOLD_DEG)
    exc = bad & gap & (dih <= G.CROTCH_FOLD_CAP)
    Lq = np.stack([np.linalg.norm(V[Q[:, k]] - V[Q[:, (k + 1) % 4]], axis=1) for k in range(4)], 1)
    asp = Lq.max(1) / np.maximum(Lq.min(1), 1e-12)
    el = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    out = {"vertices": len(V), "quads": len(Q),
           "fold_over_60": int((bad & ~exc).sum()), "fold_over_60_crotch_exception": int(exc.sum()),
           "fold_on_floor_loop_over_60": int((body_e & on_floor & (dih > G.FOLD_DEG)).sum()),
           "fold_max_deg_off_floor": round(float(dih[body_e & ~on_floor].max()), 1),
           "aspect_over_4": int((asp[~tmpl_q] > G.ASPECT_MAX).sum()),
           "aspect_max": round(float(asp[~tmpl_q].max()), 2),
           "edges_under_2mm": int((body_e & (el < G.EDGE_MIN)).sum()),
           "edge_min_mm": round(float(el[body_e].min()) * 1000, 2)}
    # poles: interior (not on the neck's open ring) vertices of valence != 4, designed ones apart
    Ea = _edges(Q)
    val = np.bincount(Ea.ravel(), minlength=len(V))
    e_all = np.sort(np.concatenate([Q[:, [k, (k + 1) % 4]] for k in range(4)]), 1)
    key = e_all[:, 0].astype(np.int64) * len(V) + e_all[:, 1]
    u, c = np.unique(key, return_counts=True)
    bd = u[c == 1]
    bound = np.zeros(len(V), bool)
    bound[bd // len(V)] = bound[bd % len(V)] = True
    poles = np.where((val != 4) & ~bound & (z["flag"] != 4))[0]       # TEMPLATE = 4: the hand / foot templates are hm08's own
    designed = z["designed_pole"][poles] > 0
    Zs, joints = _zones(V, z, sk)
    zn = G.pole_zones(V, poles, Zs)
    near = np.array([d < G.POLE_MARGIN * 1000 for _, d in zn], bool) & ~designed
    by = {}
    for i in np.where(near)[0]:
        by[zn[i][0]] = by.get(zn[i][0], 0) + 1
    out.update({"poles_total": int(len(poles)), "poles_designed": int(designed.sum()),
                "poles_in_bend_zone_40mm": int(near.sum()), "poles_in_bend_zone_by_zone": by,
                "zone_points": {k: int(len(v)) for k, v in Zs.items()}})
    cr = {}
    for nm, j in joints.items():
        sel = np.where((part == P.index(nm)) & (z["flag"] == PLANE) & (V[:, 0] > 0))[0]
        best = None
        for rg in sorted(set(z["ring"][sel].tolist())):
            Xr = V[sel[z["ring"][sel] == rg]]
            c0 = Xr.mean(0)
            off = abs(float((c0 - j["J"]) @ j["bisector"]))
            if best is None or off < best[0]:
                nn = np.linalg.svd(Xr - c0)[2][2]
                best = (off, float(np.degrees(np.arccos(min(1.0, abs(nn @ j["bisector"]))))))
        cr[nm] = None if best is None else {"deg": round(best[1], 2), "ring_offset_from_joint_mm": round(best[0] * 1000, 1)}
    out["crease_plane_vs_bisector"] = cr
    return out
