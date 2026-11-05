#!/usr/bin/env python
"""P1 pass 3: the topology gates (measured on a built tier; topo_build.measure() calls gates()).

  fold      neighbour dihedral (the angle between two quads' normals across their shared edge) <= 60 deg everywhere
            outside the hand and foot templates and the one named cleft (the gluteal cleft: the reference's own
            crease, b); quad aspect (longest edge / shortest) <= 4; every edge >= 2 mm                    (a: the judge)
  zones     every pole >= 40 mm outside every bend zone (a): elbow and knee (+-bend about the crease plane), wrist
            and ankle (+-end_bend about the template rim's plane), shoulder (the armpit + 110 mm down the arm: the
            arm side of the root ring to 110 mm below the armpit along the upper arm, and the armpit's hollow),
            hip (the groin crease and the gluteal fold +-60 mm: the leg root curve's front and back), neck base
            (the neck above its base line, the clavicle heads to C7, b: our skeleton). The joints' own termination
            poles at the epicondyles (fix 1: on the hinge axis, where the skin moves least) are listed apart.
  shoulder  the rim-to-root gap ratio (max / min) <= 1.5; (pass 3c) the 8 chain-end 5-poles designed, >= 10 mm (close) /
            one edge (play) off the armpit crease (the arm / trunk seam)
  fold      (pass 3c) the play crotch's thigh-gap edges a named exception <= 65 deg; the cleft's edges over 60 deg
            all on its midline floor loop, one unbroken chain from the sacrum to the crotch strip's back corner
  breast    breast edge p95 <= 7.5 mm, quad aspect p95 <= 2.0; (pass 3b) the cap's 4 corners (its 3-poles) <= 20 mm
            from the apex or >= 60 mm out (on the chest wall, past the mound)                          (a: the judge)
  ankle     (pass 3b) the shin's last ring (the foot template's rim) 26-28 points                     (a: the judge)
  hip       (pass 3b item 4, the curve root) the 4 named hip poles a side and no others in the hip zone (the crotch
            strip's front and back outer corners, 5-poles where strip, trunk and thigh meet; the lobe's miter, 3, at
            the fold's lateral end; the rise's top, 5, over the hip); the fold row (the lobe's row 0) at y 930-965 for
            x 40-120 and the miter within 12 mm of x 120 (b: the fold's kink 945-950, faded by x 120); the strip's
            outer line within 0.8 x the tier's limb spacing of the reference's crease edges (b: hm08) where it runs on them; the lobe's
            rise 90-130 mm (b: fold to hip side, ~108)                                                 (a: the judge)
"""
import numpy as np
from scipy.spatial import cKDTree

FOLD_DEG, ASPECT_MAX, EDGE_MIN, POLE_MARGIN = 60.0, 4.0, 0.002, 0.040
# (pass 3b) the tier-dependent gates, set at close (a: the judge) and scaled by the tier's spacing over close's (a: the
# play camera: the same counts of quads, so a pole's pinch and a mound's facets read alike at each tier's distance)
BREAST_P95, KITE_CLEAR = 0.0075, 0.060
CROTCH_FOLD_CAP = 65.0      # (pass 3c fix 4) the play crotch's named exception (a: the judge, ruling (d))
CREASE_CLEAR = 0.010        # (pass 3c fix 4) the shoulder's designed corner poles off the armpit crease, close (a: the judge)


def U(v):
    v = np.asarray(v, float)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def quad_normals(V, Q):
    return U(np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]]))


def edge_pairs(Q):
    """Interior edges: (a, b) and their two quads."""
    e = np.concatenate([np.stack([Q[:, k], Q[:, (k + 1) % 4]], 1) for k in range(4)])
    qi = np.tile(np.arange(len(Q)), 4)
    es = np.sort(e, 1)
    key = es[:, 0] * (int(es.max()) + 1) + es[:, 1]
    o = np.argsort(key, kind="stable")
    key, es, qi = key[o], es[o], qi[o]
    i = np.where(key[1:] == key[:-1])[0]
    return es[i], qi[i], qi[i + 1]


def cleft_mask(X):
    """(b) the gluteal cleft on the reference: the midline crease between the buttocks (its top: hm08's midline
    edges stay over 60 deg up to the one at y 1.098 (65.3 deg); the next, at 1.109, is 40.7 deg)."""
    return (np.abs(X[:, 0]) < 0.035) & (X[:, 2] < -0.07) & (X[:, 1] > 0.88) & (X[:, 1] < 1.109)


def mesh_quality(V, Q, tmpl_q):
    """Fold, aspect and edge-length measures on the body (template quads apart)."""
    n = quad_normals(V, Q)
    E, qa, qb = edge_pairs(Q)
    dih = np.degrees(np.arccos(np.clip((n[qa] * n[qb]).sum(1), -1, 1)))
    body_e = ~(tmpl_q[qa] | tmpl_q[qb])
    mid = 0.5 * (V[E[:, 0]] + V[E[:, 1]])
    cl = cleft_mask(mid)
    bad = body_e & ~cl & (dih > FOLD_DEG)
    Lq = np.stack([np.linalg.norm(V[Q[:, k]] - V[Q[:, (k + 1) % 4]], axis=1) for k in range(4)], 1)
    asp = Lq.max(1) / np.maximum(Lq.min(1), 1e-12)
    bq = ~tmpl_q
    el = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    worst = np.argsort(-np.where(bad, dih, 0))[:12]
    short = np.where(body_e & (el < EDGE_MIN))[0][:8]
    return {
        "fold_edges_over_60": int(bad.sum()),
        "fold_deg_p99_max_body": [round(float(np.percentile(dih[body_e & ~cl], 99)), 1),
                                  round(float(dih[body_e & ~cl].max()), 1)],
        "fold_worst": [{"pos_mm": [int(round(c * 1000)) for c in mid[k]], "deg": round(float(dih[k]), 1)}
                       for k in worst if bad[k]],
        "cleft_edges_over_60": int((body_e & cl & (dih > FOLD_DEG)).sum()),
        "aspect_over_4": int((asp[bq] > ASPECT_MAX).sum()),
        "aspect_p95_max": [round(float(np.percentile(asp[bq], 95)), 2), round(float(asp[bq].max()), 2)],
        "aspect_worst": [{"pos_mm": [int(round(c * 1000)) for c in V[Q[k]].mean(0)], "aspect": round(float(asp[k]), 2)}
                         for k in np.where(bq)[0][np.argsort(-asp[bq])][:8] if asp[k] > ASPECT_MAX],
        "edges_under_2mm": int((el[body_e] < EDGE_MIN).sum()),
        "edge_min_mm_body": round(float(el[body_e].min()) * 1000, 2),
        "short_edges": [{"pos_mm": [int(round(c * 1000)) for c in mid[k]], "mm": round(float(el[k]) * 1000, 2)}
                        for k in short],
        "_asp": asp, "_dih": dih, "_E": E, "_qa": qa, "_qb": qb, "_bad": bad, "_cl": cl & body_e,
    }


def vertex_labels(ref):
    lab = np.zeros(len(ref.P), np.int64)
    for k in range(3):
        lab[ref.T[:, k]] = ref.lab
    return np.where(lab >= 5, lab - 5, lab)


def zone_points(ref, L, joints, hip_ring):
    """Each bend zone as the reference's own vertices (b), left side (x >= 0; the right is its mirror)."""
    P = ref.P * np.where(ref.P[:, :1] < 0, [-1.0, 1, 1], 1.0)
    lab = vertex_labels(ref)
    ARM, LEG, HAND, FOOT = 1, 2, 3, 4
    Z = {}
    for nm, ks in (("elbow", (ARM, HAND)), ("knee", (LEG, FOOT))):
        j = joints[nm]
        near = np.linalg.norm(P - j["J"], axis=1) < j["bend"] + 0.12
        Z[nm] = P[near & np.isin(lab, ks) & (np.abs((P - j["J"]) @ j["bisector"]) <= j["bend"])]
        nm2 = "wrist" if nm == "elbow" else "ankle"
        near = np.linalg.norm(P - j["c_end"], axis=1) < j["end_bend"] + 0.12
        Z[nm2] = P[near & np.isin(lab, ks) & (np.abs((P - j["c_end"]) @ j["n_end"]) <= j["end_bend"])]
    d_up = U(L["elbow"] - L["shoulder"])
    u = (P - L["shoulder"]) @ d_up
    u_ap = float((L["armpit"] - L["shoulder"]) @ d_up)
    Z["shoulder"] = P[((lab == ARM) & (u <= u_ap + 0.110)) | (np.linalg.norm(P - L["armpit"], axis=1) < 0.035)]
    Z["deltoid"] = P[(lab == ARM) & (u <= u_ap + 0.110) & (P[:, 1] > L["armpit"][1])]
    tl = np.where(ref.lab >= 5, ref.lab - 5, ref.lab)
    on_t, on_a = np.zeros(len(P), bool), np.zeros(len(P), bool)
    for k in range(3):
        on_t[ref.T[tl == 0, k]] = True
        on_a[ref.T[tl == ARM, k]] = True
    Z["armpit_crease"] = P[on_t & on_a]               # (pass 3c) the arm / trunk seam, both sides folded to x >= 0
    R = np.asarray(hip_ring)
    Rd = np.concatenate([np.linspace(R[k], R[(k + 1) % len(R)], 6, endpoint=False) for k in range(len(R))])
    lat = Rd[:, 0] - R[:, 0].min()
    Rd = Rd[lat < 0.6 * lat.max()]                     # the groin crease (front, inner) and the gluteal fold (back)
    Z["hip"] = P[cKDTree(Rd).query(P)[0] <= 0.060]
    ring = ref.ring
    zax = 0.5 * (ring[:, 2].max() + ring[:, 2].min())
    th = np.arctan2(np.abs(P[:, 0]), P[:, 2] - zax)
    yb = 1.55 + 0.04 * (1 - np.cos(th)) / 2           # (b) the clavicle heads (1.552) to C7 (neck_01 - 0.04)
    r = np.hypot(P[:, 0], P[:, 2] - zax)
    Z["neck_base"] = P[(lab == 0) & (P[:, 1] >= yb) & (r < 0.075) & (P[:, 1] < ring[:, 1].max() + 0.01)]
    return Z


def pole_zones(V, poles, Z):
    """Each pole's distance (m) to every zone (0 inside); the nearest zone and its distance."""
    X = V[poles] * np.where(V[poles][:, :1] < 0, [-1.0, 1, 1], 1.0)
    D = {}
    for nm, P in Z.items():
        if len(P) == 0 or nm in ("deltoid", "armpit_crease"):
            continue
        d = cKDTree(P).query(X)[0]
        D[nm] = np.where(d < 0.004, 0.0, d)            # within the reference's own vertex spacing: inside
    names = list(D)
    M = np.stack([D[k] for k in names], 1)
    k = M.argmin(1)
    return [(names[k[i]], round(float(M[i, k[i]]) * 1000, 1)) for i in range(len(poles))]


def gates(ref, V, Q, info, C, joints, L, poles_out, poles, hip_ring, parts):
    tmpl_q = np.isin(info["qpart"], [parts.index("hand"), parts.index("foot")])
    mq = mesh_quality(V, Q, tmpl_q)
    asp = mq.pop("_asp")
    dih, E, qa, qb, bad, cl = (mq.pop(k) for k in ("_dih", "_E", "_qa", "_qb", "_bad", "_cl"))
    # (pass 3c fix 4) the play crotch's edges over 60 deg inside the thigh gap: a named exception capped at 65 deg
    # (a: the judge, ruling (d): in self-shadow, about a pixel at the play camera); every other fold edge still fails
    m = 0.5 * (V[E[:, 0]] + V[E[:, 1]])              # the thigh gap under the perineum (the judge's (+-25, 986, 3))
    gap = (np.abs(m[:, 0]) <= 0.040) & (m[:, 1] >= 0.975) & (m[:, 1] <= 1.000) & (np.abs(m[:, 2]) <= 0.015)
    exc = bad & gap & (dih <= CROTCH_FOLD_CAP)
    mq["fold_edges_over_60_crotch_exception"] = int(exc.sum())
    mq["fold_edges_over_60"] = int((bad & ~exc).sum())
    # (pass 3c fix 4) the cleft rule: no edge over 60 deg off the cleft's floor loop (the midline), and the floor loop
    # one continuous chain of midline edges from the sacrum (the cleft's top) to the crotch strip's back corner
    mid_v = np.abs(V[:, 0]) < 1e-7
    on_floor = mid_v[E[:, 0]] & mid_v[E[:, 1]]
    hot = cl & (dih > FOLD_DEG)
    mq["cleft_edges_over_60_off_floor"] = int((hot & ~on_floor).sum())
    sb = (C.get("hip_named_mm") or {}).get("strip_back")
    if sb is not None:
        y_lo = sb[1] / 1000.0
        back = np.where(mid_v & (V[:, 2] < -0.05) & (V[:, 1] >= y_lo - 0.012) & (V[:, 1] <= 1.115))[0]
        back = back[np.argsort(V[back, 1])]
        es = set(map(tuple, np.sort(E[on_floor], 1).tolist()))
        gaps = [int(i) for i in range(len(back) - 1) if (min(back[i], back[i + 1]), max(back[i], back[i + 1])) not in es]
        hy = 0.5 * (V[E[hot, 0], 1] + V[E[hot, 1], 1])
        mq["cleft_floor"] = {"verts": int(len(back)), "breaks": len(gaps), "strip_back_y_mm": sb[1],
                             "y_mm": [round(float(V[back[0], 1]) * 1000, 1), round(float(V[back[-1], 1]) * 1000, 1)],
                             "hot_y_mm": [round(float(hy.min()) * 1000, 1), round(float(hy.max()) * 1000, 1)] if len(hy) else []}
    Z = zone_points(ref, L, joints, hip_ring)
    designed = info["designed_pole"].astype(bool) if "designed_pole" in info else np.zeros(len(V), bool)
    for p, (zn, zd), v in zip(poles_out, pole_zones(V, poles, Z), poles):
        p.update({"zone": zn, "zone_dist_mm": zd, "designed": bool(designed[v])})
    fail = [p for p in poles_out if not p["designed"] and p["zone_dist_mm"] < POLE_MARGIN * 1000]
    by_zone = {}
    for p in fail:
        by_zone[p["zone"]] = by_zone.get(p["zone"], 0) + 1
    g = dict(mq)
    g["zone_points"] = {k: int(len(v)) for k, v in Z.items()}
    g["poles_total"] = len(poles_out)
    dv = info["designed_pole"] if "designed_pole" in info else np.zeros(len(V), int)
    g["poles_designed_at_epicondyles"] = int(sum(p["designed"] and dv[v] == 1 for p, v in zip(poles_out, poles)))
    hipn = [p for p, v in zip(poles_out, poles) if dv[v] == 2]
    if hipn or "hip_named_mm" in C:                  # (pass 3b item 4) the curve root's designed poles and rules
        g["hip_named_poles"] = [{"pos_mm": p["pos_mm"], "val": p["valence"]} for p in hipn if p["pos_mm"][0] >= 0]
        g["hip_root"] = {"named_mm": C.get("hip_named_mm"), "lobe": C.get("lobe"), "fold_row_y_mm": C.get("fold_row_y_mm"),
                         "crease_line_dist_mm": C.get("crease_line_dist_mm"), "crease_tol_mm": C.get("crease_tol_mm"), "crotch_m": C.get("crotch_m"),
                         "blend": C.get("root_blend"), "N_leg": C.get("N_leg")}
    g["poles_designed_max_dist_to_hinge_exit_mm"] = C.get("joint_pole_hinge_mm")
    g["poles_within_40mm_of_a_zone"] = len(fail)
    g["poles_within_40mm_by_zone"] = by_zone
    g["poles_within_40mm_left"] = [{"pos_mm": p["pos_mm"], "val": p["valence"], "part": p["part"],
                                    "zone": p["zone"], "mm": p["zone_dist_mm"]} for p in fail if p["pos_mm"][0] >= 0]
    gap = C.get("shoulder_gap_mm")
    if gap:
        g["shoulder_rim_gap_mm"] = gap
        g["shoulder_rim_gap_ratio"] = round(gap[2] / max(gap[0], 1e-6), 2)
    kv = C.get("shoulder_kite_verts")
    if kv:
        dd = cKDTree(Z["deltoid"]).query(V[kv])[0]
        g["shoulder_kites_min_dist_to_deltoid_mm"] = round(float(dd.min()) * 1000, 1)
        # (pass 3c fix 4) the 8 corner poles (4 a side) are designed (ruling (a): the deltoid loop's textbook ends at
        # the armpit folds and the shoulder top); their clearance from the armpit crease: the reference's arm / trunk
        # boundary (b: hm08's arm group, which runs through the armpit's fold)
        g["poles_designed_shoulder"] = int(sum(p["designed"] and dv[v] == 3 for p, v in zip(poles_out, poles)))
        cd = cKDTree(Z["armpit_crease"]).query(V[kv] * np.where(V[kv][:, :1] < 0, [-1.0, 1, 1], 1.0))[0]
        g["shoulder_poles_crease_mm"] = [round(float(x) * 1000, 1) for x in cd]
    bq = info["qpart"] == parts.index("breast")
    if bq.any():
        qb = Q[bq]
        e = np.unique(np.sort(np.concatenate([qb[:, [k, (k + 1) % 4]] for k in range(4)]), 1), axis=0)
        el = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
        g["breast_edge_mm_p95"] = round(float(np.percentile(el, 95)) * 1000, 2)
        g["breast_aspect_p95"] = round(float(np.percentile(asp[bq], 95)), 2)
    bcm = C.get("breast_cap_corner_mm")
    if bcm:
        g["breast_cap_corner_mm"] = bcm
    g["ankle_points"] = C.get("ankle_points")
    gs = C.get("gate_scale") or {"spacing": 0.0078, "close_spacing": 0.0078, "ankle_points": [26, 28]}
    k_s = gs["spacing"] / gs["close_spacing"]        # (a) the play camera: the tier's own spacing over close's
    g["tier_scale"] = {"spacing_ratio": round(k_s, 3), "breast_p95_max_mm": round(BREAST_P95 * k_s * 1000, 2),
                       "kite_clear_min_mm": round(KITE_CLEAR * k_s * 1000, 1), "ankle_points": gs["ankle_points"],
                       # (a: the judge) 10 mm at close, at least one edge at the lighter tiers
                       "crease_clear_min_mm": round(max(CREASE_CLEAR, gs["spacing"] if k_s > 1 else 0) * 1000, 1)}
    g["pass"] = {
        "fold": mq["fold_edges_over_60"] == 0,
        "aspect": mq["aspect_over_4"] == 0,
        "min_edge": mq["edges_under_2mm"] == 0,
        "poles_vs_zones": len(fail) == 0,
        "shoulder_gap_ratio": bool(gap) and g["shoulder_rim_gap_ratio"] <= 1.5,
        "shoulder_poles_designed_8": g.get("poles_designed_shoulder", 0) == 8,
        "shoulder_poles_vs_crease": min(g.get("shoulder_poles_crease_mm") or [0]) >= g["tier_scale"]["crease_clear_min_mm"],
        "cleft_on_floor": mq["cleft_edges_over_60_off_floor"] == 0 and (mq.get("cleft_floor") or {}).get("breaks", 1) == 0,
        "breast": ("breast_edge_mm_p95" in g and g["breast_edge_mm_p95"] <= g["tier_scale"]["breast_p95_max_mm"]
                   and g["breast_aspect_p95"] <= 2.0),
        "breast_cap_corners": bool(bcm) and all(d <= 20 or d >= 60 for d in bcm),
        "ankle_26_28": gs["ankle_points"][0] <= (g["ankle_points"] or 0) <= gs["ankle_points"][1],
    }
    hr = g.get("hip_root")
    if hr:
        nmm, fy, lb = hr["named_mm"] or {}, hr["fold_row_y_mm"] or [0, 0], hr["lobe"] or {}
        g["pass"]["hip_named_poles_4"] = len(g["hip_named_poles"]) == 4 and all(
            any(np.allclose(p["pos_mm"], x, atol=1.0) for x in nmm.values()) for p in g["hip_named_poles"])
        g["pass"]["hip_fold_on_landmarks"] = (930 <= fy[0] and fy[1] <= 965           # (b) the fold y 945-950, x 40-120
                                              and abs(nmm.get("miter", [0, 0, 0])[0] - 120) <= 12)
        g["pass"]["hip_crotch_on_crease"] = (hr["crease_line_dist_mm"] or 99) <= (hr["crease_tol_mm"] or 0)   # 0.8 x spacing
        g["pass"]["hip_lobe_rise"] = 90 <= lb.get("rise_mm", 0) <= 130 and lb.get("rows", 0) >= 3
    return g
