"""P1 R1 breast numbers on the rest body (formview.body: build_topo stages 1-2 on the close tier, the final frame).
    python tools/body/sculpt/breast_measure.py SPEC[,SPEC...] --bare BARE_SPEC [--wall WALL_SPEC] [--json OUT]
Per spec, the left breast (the right is its mirror): the volume added over the bare chest (mL, front region, per
side), the apex (the footprint point farthest from the footprint base centroid) and its normal (yaw out / pitch up
deg), the sagittal profile through the apex (plane x = apex x): the upper-pole slope (root to apex, deg from
vertical), the curvature sign changes along the upper pole (1 = the root fillet only: no ledge) and its least
curvature past the root fillet, the lower pole radius (circle fit over its convex arc), the fold (its least radius and
its depth: the notch under the profile hull from 50 mm under the fold to the apex), the cleavage at apex height, and
the points inside the body at rest (ray.inside, V + 0.3 mm N). The root and fold are where the profile leaves the
reference (the wall spec when given: the smooth chest wall; else the bare) by 3 mm.
"""
import os
import sys
import json
import math
import argparse
import numpy as np

WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(WT, "tools", "body"))


def tet_vol(V, T):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    return np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0


def vnormals(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def section(V, T, ax, val):
    """The mesh cut by the plane V[:, ax] = val: a list of polylines (ordered 3D points)."""
    s = V[:, ax] - val
    st = s[T]
    cross = (st.min(1) < 0) & (st.max(1) >= 0)
    segs = []
    pts = {}
    def ept(i, j):
        k = (min(i, j), max(i, j))
        if k not in pts:
            t = s[k[0]] / (s[k[0]] - s[k[1]])
            pts[k] = V[k[0]] + t * (V[k[1]] - V[k[0]])
        return k
    for tri in T[cross]:
        e = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            i, j = tri[a], tri[b]
            if (s[i] < 0) != (s[j] < 0):
                e.append(ept(i, j))
        if len(e) == 2:
            segs.append(e)
    nb = {}
    for a, b in segs:
        nb.setdefault(a, []).append(b)
        nb.setdefault(b, []).append(a)
    seen = set()
    lines = []
    for k0 in nb:
        if k0 in seen:
            continue
        chain = [k0]
        seen.add(k0)
        for direction in (0, 1):
            cur = k0
            while True:
                nxt = [n for n in nb[cur] if n not in seen]
                if not nxt:
                    break
                cur = nxt[0]
                seen.add(cur)
                if direction == 0:
                    chain.append(cur)
                else:
                    chain.insert(0, cur)
        lines.append(np.array([pts[k] for k in chain]))
    return lines


def resample(P, step=0.001):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.arange(0, d[-1], step)
    return np.stack([np.interp(s, d, P[:, k]) for k in range(P.shape[1])], 1)


def gsmooth(P, sig):
    if sig <= 0:
        return P
    r = int(3 * sig) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2)
    k /= k.sum()
    Pp = np.concatenate([np.repeat(P[:1], r, 0), P, np.repeat(P[-1:], r, 0)])
    return np.stack([np.convolve(Pp[:, j], k, mode="valid") for j in range(P.shape[1])], 1)


def curvature2(P):
    """Signed curvature (1/m) of a 2D polyline (y, z) ordered top -> bottom at 1 mm: + where it bulges to the front."""
    d1 = np.gradient(P, axis=0)
    d2 = np.gradient(d1, axis=0)
    num = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    return num / np.maximum(np.linalg.norm(d1, axis=1) ** 3, 1e-12)


def profile_at(V, T, x, apex, ylo, yhi):
    """The front sagittal profile at plane x through the apex: (y, z) points ordered top -> bottom, apex index."""
    best = None
    for L in section(V, T, 0, x):
        dd = np.linalg.norm(L - apex, axis=1)
        if best is None or dd.min() < best[0]:
            best = (dd.min(), L)
    L = best[1]
    n = len(L)
    i0 = int(np.argmin(np.linalg.norm(L - apex, axis=1)))
    def walk(step):
        out = []
        i = i0
        for _ in range(n):
            q = L[i % n]
            if not (ylo <= q[1] <= yhi) or q[2] < -0.03:
                break
            out.append(q)
            i += step
        return out
    a, b = walk(-1), walk(1)
    if len(a) > 3 and len(b) > 3 and a[3][1] < b[3][1]:
        a, b = b, a
    P = np.array(a[::-1] + b[1:])
    return P[:, 1:3], len(a) - 1


def circle_fit(P):
    A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
    b = (P ** 2).sum(1)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy, cc = sol
    return math.sqrt(max(cc + cx * cx + cy * cy, 0.0)), (cx, cy)


def hull_notch(P):
    """Max distance (m) of 2D points P (y, z) inside the front side (z+) of their convex hull."""
    from scipy.spatial import ConvexHull
    h = ConvexHull(P)
    best = 0.0
    for simplex, eq in zip(h.simplices, h.equations):
        nrm = eq[:2]
        if nrm[1] <= 0.2:
            continue
        a, b = P[simplex[0]], P[simplex[1]]
        lo, hi = min(a[0], b[0]), max(a[0], b[0])
        sel = (P[:, 0] > lo) & (P[:, 0] < hi)
        if sel.any():
            best = max(best, float((-(P[sel] @ nrm + eq[2])).max()))
    return best


def measure(V, T, Vb, Vref, H=None, HT=None, label=""):
    out = {"label": label}
    C = Vb[T].mean(1)
    front = (C[:, 2] > -0.02) & (np.abs(C[:, 0]) < 0.25) & (C[:, 1] > 1.15) & (C[:, 1] < 1.62)
    dv = tet_vol(V, T) - tet_vol(Vb, T)
    out["vol_added_mL_per_side"] = round(float(dv[front & (C[:, 0] > 0)].sum()) * 1e6, 1)
    out["vol_added_mL_total_over_2"] = round(float(dv.sum()) * 0.5e6, 1)
    d = np.linalg.norm(V - Vb, axis=1)
    fp = (d > 0.003) & (V[:, 0] > 0.005) & (Vb[:, 2] > -0.02) & (Vb[:, 1] > 1.15) & (Vb[:, 1] < 1.62) & (np.abs(Vb[:, 0]) < 0.25)
    b = Vb[fp].mean(0)
    # the apex: the footprint point standing farthest off the reference (the smooth chest wall for a designed
    # breast, the bare chest for her_r1); the axis: from the footprint base centroid to it
    i = int(np.argmax(np.where(fp, np.linalg.norm(V - Vref, axis=1), -9)))
    dirn = (V[i] - b) / np.linalg.norm(V[i] - b)
    N = vnormals(V, T)
    nrm = N[i]
    p = V[i]
    out["apex_mm"] = [round(float(x) * 1000, 1) for x in p]
    out["apex_normal_yaw_out_deg"] = round(math.degrees(math.atan2(nrm[0], nrm[2])), 1)
    out["apex_normal_pitch_up_deg"] = round(math.degrees(math.asin(np.clip(nrm[1], -1, 1))), 1)
    out["apex_axis_yaw_out_deg"] = round(math.degrees(math.atan2(dirn[0], dirn[2])), 1)
    out["apex_axis_pitch_up_deg"] = round(math.degrees(math.asin(dirn[1])), 1)
    out["footprint_y_mm"] = [round(float(Vb[fp, 1].min()) * 1000), round(float(Vb[fp, 1].max()) * 1000)]
    out["footprint_x_mm"] = [round(float(Vb[fp, 0].min()) * 1000), round(float(Vb[fp, 0].max()) * 1000)]
    P, _ = profile_at(V, T, p[0], p, p[1] - 0.16, p[1] + 0.22)
    R, _ = profile_at(Vref, T, p[0], Vref[i], p[1] - 0.20, p[1] + 0.26)
    Ps = resample(P)
    ia = int(np.argmin(np.linalg.norm(Ps - p[1:3], axis=1)))
    from scipy.spatial import cKDTree
    dref = cKDTree(resample(R)).query(Ps)[0]
    root = next((j for j in range(ia, -1, -1) if dref[j] < 0.003), 0)
    fold = next((j for j in range(ia, len(Ps)) if dref[j] < 0.003), len(Ps) - 1)
    pr, pf = Ps[root], Ps[fold]
    out["root_yz_mm"] = [round(float(x) * 1000, 1) for x in pr]
    out["fold_yz_mm"] = [round(float(x) * 1000, 1) for x in pf]
    out["upper_pole_slope_deg_from_vertical"] = round(math.degrees(math.atan2(p[2] - pr[1], pr[0] - p[1])), 1)
    out["apex_height_fraction_from_fold"] = round(float((p[1] - pf[0]) / max(pr[0] - pf[0], 1e-6)), 3)
    k = curvature2(gsmooth(Ps, 5.0))
    ku = k[root:ia + 1]
    sgn = np.sign(np.where(np.abs(ku) < 2.0, 0, ku))
    nz = sgn[sgn != 0]
    out["upper_pole_curv_sign_changes"] = int((np.diff(nz) != 0).sum()) if len(nz) > 1 else 0
    n = len(ku)
    past = ku[int(0.3 * n):] if n > 4 else ku
    out["upper_pole_min_curv_past_root_per_m"] = round(float(past.min()), 2) if len(past) else None
    out["upper_pole_concave_mm_past_root"] = int((past < -2.0).sum())
    kl = k[ia:fold + 1]
    j = 0
    while j < len(kl) and kl[j] > -2.0:
        j += 1
    arc = Ps[ia:ia + max(j, 3)]
    out["lower_pole_arc_len_mm"] = int(j)
    if len(arc) > 8:
        out["lower_pole_radius_mm"] = round(circle_fit(arc[len(arc) // 8:])[0] * 1000, 1)
    fk = k[ia + j:min(fold + 15, len(k))]
    out["fold_min_radius_mm"] = round(1000.0 / max(-fk.min(), 1e-6), 1) if len(fk) and fk.min() < 0 else None
    seg = Ps[ia:min(len(Ps), fold + 50)]
    out["fold_notch_depth_mm"] = round(hull_notch(seg) * 1000, 1) if len(seg) > 5 else None
    secs = section(V, T, 1, p[1])
    pts = np.concatenate(secs) if secs else np.zeros((0, 3))
    pts = pts[(np.abs(pts[:, 0]) < 0.2) & (pts[:, 2] > 0)]
    mid = pts[np.abs(pts[:, 0]) < 0.004]
    zs = float(mid[:, 2].max()) if len(mid) else float("nan")
    out["cleavage_sternum_z_mm"] = round(zs * 1000, 1)
    out["cleavage_depth_mm"] = round((p[2] - zs) * 1000, 1)
    for dz in (0.02, 0.04, 0.06):
        zz = p[2] - dz
        sel = pts[(np.abs(pts[:, 2] - zz) < 0.003) & (pts[:, 0] > 0) & (pts[:, 0] < p[0])]
        out["gap_at_apex_z_minus_%dmm" % int(dz * 1000)] = round(float(2 * sel[:, 0].min()) * 1000, 1) if len(sel) and zz > zs else None
    import ray
    if H is not None:
        VV, TT = np.concatenate([V, H]), np.concatenate([T, HT + len(V)])
    else:
        VV, TT = V, T
    ins = ray.inside(ray.scene(VV, TT), V + 3e-4 * N)
    reg = (np.abs(V[:, 0]) < 0.25) & (V[:, 1] > 1.15) & (V[:, 1] < 1.62) & (V[:, 2] > -0.05)
    out["inside_at_rest_all"] = int(ins.sum())
    out["inside_at_rest_chest"] = int((ins & reg).sum())
    out["_profile"] = {"P": Ps.round(5).tolist(), "apex": ia, "root": root, "fold": fold}
    return out


def main():
    import formview
    ap = argparse.ArgumentParser()
    ap.add_argument("specs")
    ap.add_argument("--bare", required=True)
    ap.add_argument("--wall")
    ap.add_argument("--json")
    a = ap.parse_args()
    os.chdir(WT)
    Vb, T, *_ = formview.body(a.bare)
    Vw = formview.body(a.wall)[0] if a.wall else None
    res = []
    for sp in a.specs.split(","):
        V, T, H, HT, z, rep = formview.body(sp)
        ref = Vb if ("her_r1" in sp or Vw is None) else Vw
        m = measure(V, T, Vb, ref, H, HT, os.path.basename(sp))
        res.append(m)
        print(json.dumps({k: v for k, v in m.items() if not k.startswith("_")}))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f)


if __name__ == "__main__":
    main()