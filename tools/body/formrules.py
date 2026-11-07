"""P1 R1: the design sheet's rules, measured (tools/body/form_rules.json). The judge reads rules, not a copy of A:
every rule is a number on the built body at rest with a band, and A's number is information only.

    python tools/body/formrules.py BODY.glb [--spec SPEC.json] [--out DIR]   (also check.py --only forms)

Sections: "neck" (the trapezius line under the chin, the neck's girth, the slope), "seam" (the throat seam as one
surface), and, given the build's spec (--spec, else build.json beside the glb), "breast" (sculpt/breast_measure.py)
and "glutes" (sculpt/glute_measure.py), measured on formview.body(spec) and the spec with the breast sliders at 0.
Each rule: {"value", "band": [lo, hi], "ok"}; summary "forms: N of M rules in band" plus the misses.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gl import Glb, weld  # noqa: E402

RULES = HERE / "form_rules.json"


def rest(B: Glb, name):
    from headbake import rest_world
    m = B.mesh(name)
    return rest_world(m, B.skeleton())[0], m.T


def vnormals(V, T):
    w = np.asarray(weld(V, 2e-5))
    Vw = np.zeros((w.max() + 1, 3))
    Vw[w] = V
    Tw = w[T]
    fn = np.cross(Vw[Tw[:, 1]] - Vw[Tw[:, 0]], Vw[Tw[:, 2]] - Vw[Tw[:, 0]])
    N = np.zeros_like(Vw)
    for k in range(3):
        np.add.at(N, Tw[:, k], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return N[w]


def chin(H):
    hz = H[(np.abs(H[:, 0]) < 0.02) & (H[:, 2] > H[:, 2].mean())]
    return float(hz[:, 1].min())


def neck(V, H):
    """The shoulder top under the chin at 7..17 cm out (both sides averaged, mm, negative below), the neck's width
    2-4 cm under the chin, the trapezius' slope 7 -> 13 cm, and the profile's worst rise outward (a knob or shelf)."""
    c = chin(H)
    xs = [0.07, 0.09, 0.11, 0.13, 0.15, 0.17]
    prof = []
    for x in xs:
        ys = []
        for s in (1, -1):
            sel = V[(np.abs(V[:, 0] * s - x) < 0.004) & (V[:, 1] < c)]
            ys.append(sel[:, 1].max())
        prof.append((float(np.mean(ys)) - c) * 1e3)

    def width(y):
        nb = V[(np.abs(V[:, 1] - y) < 0.003) & (np.abs(V[:, 0]) < 0.12)]
        return float(nb[:, 0].max() - nb[:, 0].min()) * 1e3 if len(nb) else float("nan")
    w = [width(c - k / 100) for k in (2, 3, 4)]
    rise = max(prof[i + 1] - prof[i] for i in range(len(prof) - 1))
    return {"top_under_chin_mm": [round(p, 1) for p in prof], "at_x_cm": [7, 9, 11, 13, 15, 17],
            "top_7cm_mm": round(prof[0], 1), "top_9cm_mm": round(prof[1], 1), "top_17cm_mm": round(prof[-1], 1),
            "width_2_4cm_mm": [round(x, 1) for x in w], "width_max_2_4cm_mm": round(max(w), 1),
            "trap_slope_7_13_deg": round(math.degrees(math.atan2(prof[0] - prof[3], 60.0)), 1),
            "profile_worst_rise_mm": round(rise, 1)}


def seam(V, T, H, HT):
    """Each point of the body's open ring (its boundary at the head) against the head there: the angle between the
    body's normal and the head's (one surface: near 0)."""
    from scipy.spatial import cKDTree
    from gl import boundary_edges
    w = np.asarray(weld(V, 1e-7))
    bv = np.unique(boundary_edges(w[T]))
    first = {}
    for i, r in enumerate(w):
        first.setdefault(int(r), i)
    idx = np.array([first[int(k)] for k in bv])
    d, hi = cKDTree(H).query(V[idx])
    ring = idx[d < 1e-4]
    NB, NH = vnormals(V, T), vnormals(H, HT)
    _, hi = cKDTree(H).query(V[ring])
    ang = np.degrees(np.arccos(np.clip((NB[ring] * NH[hi]).sum(1), -1, 1)))
    return {"ring_points": int(len(ring)), "angle_mean_deg": round(float(ang.mean()), 1),
            "angle_p90_deg": round(float(np.percentile(ang, 90)), 1), "angle_max_deg": round(float(ang.max()), 1)}


MEASURES = {"hanging": lambda ctx: hanging(ctx), "neck": lambda ctx: neck(ctx["V"], ctx["H"]), "seam": lambda ctx: seam(ctx["V"], ctx["T"], ctx["H"], ctx["HT"])}


BREAST_SLIDERS = ["bust_firmness", "bust_lift", "bust_point", "bust_set", "bust_size", "bust_spacing", "chest_wall",
                  "breast_a", "breast_b", "breast_settle", "support_lift", "support_press", "support_fill"]


def _derived(spec_path, zero, keep, tmp):
    """A flat copy of the spec (base merged, as sliders.load_spec) with the `zero` sliders at 0 (the `keep` ones
    restored to the spec's value), written to tmp."""
    from sliders import load_spec
    sp = load_spec(spec_path)
    sl = dict(sp.get("sliders", {}))
    for k in zero:
        sl[k] = sp.get("sliders", {}).get(k, 0.0) if k in keep else 0.0
    sp["sliders"] = sl
    p = Path(tmp) / f"derived_{abs(hash((tuple(sorted(sl.items())), spec_path)))}.json"
    p.write_text(json.dumps(sp))
    return str(p)


def _circle(P):
    """Least-squares circle through 2D points P: algebraic (Kasa) start, Gauss-Newton on the geometric residual.
    Returns centre, radius, RMS residual (all in P's units)."""
    A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
    s = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    c, R = s[:2].copy(), math.sqrt(max(s[2] + s[0] ** 2 + s[1] ** 2, 1e-12))
    for _ in range(30):
        d = P - c
        r = np.maximum(np.linalg.norm(d, axis=1), 1e-12)
        J = np.c_[-d / r[:, None], -np.ones(len(P))]
        st = np.linalg.lstsq(J, -(r - R), rcond=None)[0]
        c, R = c + st[:2], R + st[2]
        if np.abs(st).max() < 1e-9:
            break
    res = np.linalg.norm(P - c, axis=1) - R
    return c, abs(R), float(np.sqrt(np.mean(res ** 2)))


def _arc_deg(P, c):
    a = np.unwrap(np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0]))
    return float(abs(math.degrees(a[-1] - a[0])))


def _loop(V, T, y, near=None, lim=0.2):
    """The transverse section of the mesh at height y: the closed polyline nearest the 3D point `near` (default the
    body's axis at that height: the torso, not an arm), or None."""
    import breast_measure as bm
    near = np.array([0.0, y, 0.0]) if near is None else near
    best = None
    for L in bm.section(V, T, 1, y):
        d = float(np.linalg.norm(L - near, axis=1).min())
        if best is None or d < best[0]:
            best = (d, L)
    return None if best is None or best[0] > lim else best[1]


def _walk(L, i0, step, stop):
    """Points of the closed polyline L from index i0 in direction step until stop(point) (exclusive)."""
    n, out, i = len(L), [], i0
    for _ in range(n):
        q = L[i % n]
        if stop(q):
            break
        out.append(q)
        i += step
    return np.array(out)


def _inner_wall(L, xa):
    """The left inner wall of a transverse loop: from the front midline crossing (the cleavage floor) toward +x up to
    the breast's front (x <= xa), as (x, z) points; and the floor's z."""
    x = L[:, 0]
    n = len(L)
    best = None
    for k in range(n):
        a, b = L[k], L[(k + 1) % n]
        if (a[0] <= 0.0 < b[0]) or (b[0] <= 0.0 < a[0]):
            t = -a[0] / (b[0] - a[0])
            z = a[2] + t * (b[2] - a[2])
            if best is None or z > best[0]:
                best = (z, k, 1 if b[0] > a[0] else -1)
    if best is None:
        return None, None
    zs, k, st = best
    i0 = (k + 1) % n if st == 1 else k
    W = _walk(L, i0, st, lambda q: q[0] > xa or q[0] < 0.0)
    if len(W) < 2:
        return None, zs
    W = W[:int(np.argmax(W[:, 2])) + 1]                 # up to the front-most point of the wall
    return np.r_[[[0.0, zs]], W[:, [0, 2]]], zs


def breast_round(V, T, Vref, b):
    """P1 R1c (the owner, 6 Nov: "our tests so far are not round"): the breast's ROUNDNESS as numbers, left breast,
    rest body. b is breast_measure.measure's output (apex, the sagittal profile with its root / fold).
      side: the sagittal outline through the apex from the upper root to the inframammary fold (where it leaves the
        chest-wall reference by 3 mm): circle fit, RMS residual / radius, the arc angle the fit covers;
      upper-pole fill: between the root and the apex, the area between the outline and the straight chord over the
        circular segment of the fitted radius on that chord (0 = a straight slope, 1 = round); its concave mm past
        the root fillet (after the first convex mm going up from the root to the apex);
      front: the transverse outline at apex height from the cleavage (the inner wall within 6 mm of the midline, or
        the reference) to the lateral root: circle fit residual / radius, arc angle; the lateral wrap: in front view
        how far the breast moves the torso's side line out past the chest wall's (max over the breast's heights);
      cleavage bare: at apex height and 30 / 60 mm above, the gap between the inner walls 10 mm in front of the
        cleavage floor; the cleavage line's depth: from the floor forward while the gap stays <= 20 mm (a slot: on our
        topology a floor turning in under 60 deg a quad is ~15 mm wide);
      contrast: the torso's front-view width 15 mm under the fold (underbust) and its least width down to y 0.95
        (the waist): waist / underbust."""
    import breast_measure as bm
    from scipy.spatial import cKDTree
    out = {}
    pr = b["_profile"]
    Ps, ia, root, fold = np.asarray(pr["P"]), pr["apex"], pr["root"], pr["fold"]
    p = np.asarray(b["apex_mm"]) / 1000.0
    # -- side
    S = Ps[root:fold + 1]
    c, R, rms = _circle(S)
    out["side_radius_mm"] = round(R * 1000, 1)
    out["side_round_resid_over_R"] = round(rms / R, 4)
    out["side_arc_deg"] = round(_arc_deg(S, c), 1)
    # P1 R1c round 6: the same fit over the globe proper: from where the outline's normal falls to 60 deg above level
    # to the fold (the upper pole's thin hull above it is straight by design)
    Pg = bm.gsmooth(Ps, 3.0)
    d1 = np.gradient(Pg, axis=0)
    el = np.degrees(np.arctan2(d1[:, 1], -d1[:, 0]))
    up60 = [j for j in range(root, ia) if el[j] >= 60.0]
    _, Rg, rg = _circle(Ps[(up60[-1] if up60 else root):fold + 1])
    out["side_round_globe_resid_over_R"] = round(rg / Rg, 4)
    # P1 R1 round 8 (breast_settle): the weight's numbers. lower_third_off_mm: the lower third of the apex-to-fold outline
    # against the circle fitted on the upper globe alone (normal 60 deg above level to the apex): how far the lower curve
    # sits outside the circle the upper pole promises (+: the mass has settled; a balloon reads near 0 or under).
    # fold_lean_deg: the outline's tilt from vertical 12 mm above the fold, at the rib contact (the lower curve lies down
    # on the ribs as it comes in: a floating globe keeps turning).
    i0 = up60[-1] if up60 else root
    cu, Ru, _ = _circle(Ps[i0:ia + 1])
    n3 = max(1, (fold - ia) // 3)
    lo3 = Ps[fold - 2 * n3:fold - n3 + 1]
    out["lower_third_off_mm"] = round(float(np.mean(np.linalg.norm(lo3 - cu, axis=1) - Ru)) * 1000, 1)
    j12 = max(ia, fold - 12)
    out["fold_lean_deg"] = round(float(abs(math.degrees(math.atan2(d1[j12, 1], d1[j12, 0])))), 1)
    # -- upper-pole fill
    U = Ps[root:ia + 1]
    a0, a1 = U[0], U[-1]
    ch = a1 - a0
    L = float(np.linalg.norm(ch))
    e = ch / max(L, 1e-9)
    nrm = np.array([-e[1], e[0]])
    if nrm[1] < 0:                                      # toward the front (+z)
        nrm = -nrm
    s = (U - a0) @ e
    d = (U - a0) @ nrm
    area = float(np.sum(0.5 * (d[1:] + d[:-1]) * np.diff(s)))
    th = 2 * math.asin(min(1.0, L / (2 * R)))
    seg = R * R * (th - math.sin(th)) / 2
    out["upper_pole_fill"] = round(area / max(seg, 1e-12), 3)
    k = bm.curvature2(bm.gsmooth(Ps, 5.0))[root:ia + 1]
    cv = np.nonzero(k > 2.0)[0]
    out["upper_pole_concave_mm_past_fillet"] = int((k[cv[0]:] < -2.0).sum()) if len(cv) else len(k)
    # P1 R1c round 7: the root's own concave stretch (from 60 mm above the root to the first convex run)
    k0 = bm.curvature2(bm.gsmooth(Ps, 5.0))[max(0, root - 60):ia + 1]
    cv0 = np.nonzero(k0[60 if root >= 60 else root:] > 2.0)[0]
    end = (60 if root >= 60 else root) + (int(cv0[0]) if len(cv0) else 0)
    out["upper_pole_root_concave_mm"] = int((k0[:end] < -2.0).sum())
    # -- front (transverse at apex height)
    Lb, Lr = _loop(V, T, p[1]), _loop(Vref, T, p[1])
    if Lb is not None and Lr is not None:
        tr = cKDTree(bm.resample(Lr))
        i0 = int(np.argmin(np.linalg.norm(Lb - p, axis=1)))
        nb = len(Lb)
        stp = 1 if Lb[(i0 + 3) % nb, 0] > Lb[i0, 0] else -1   # +1 walks lateral
        off = lambda q: tr.query(q)[0] < 0.003
        lat = _walk(Lb, i0, stp, off)
        med = _walk(Lb, i0, -stp, lambda q: off(q) or q[0] < 0.006)
        F = bm.resample(np.r_[med[::-1], lat[1:]][:, [0, 2]])
        cf, Rf, rf = _circle(F)
        out["front_radius_mm"] = round(Rf * 1000, 1)
        out["front_round_resid_over_R"] = round(rf / Rf, 4)
        out["front_arc_deg"] = round(_arc_deg(F, cf), 1)
    wraps = []
    for y in np.arange(Ps[fold][0] + 0.01, p[1] + 0.0301, 0.005):
        lb, lr = _loop(V, T, y), _loop(Vref, T, y)
        if lb is None or lr is None or lb[:, 0].max() > 0.25:
            continue
        wraps.append(float(lb[:, 0].max() - lr[:, 0].max()))
    out["lateral_wrap_mm"] = round(max(wraps) * 1000, 1) if wraps else None
    # -- cleavage, bare
    depth = []
    for dy in (0, 30, 60):
        Lc = _loop(V, T, p[1] + dy / 1000.0)
        W, zs = _inner_wall(Lc, p[0]) if Lc is not None else (None, None)
        key = "cleavage_gap_mm_at_apex" if dy == 0 else "cleavage_gap_mm_apex_plus%d" % dy
        if W is None:
            out[key] = None
            continue
        zz = zs + 0.010
        j = np.nonzero(W[:, 1] >= zz)[0]
        out[key] = round(float(2 * np.interp(zz, W[j[0] - 1:j[0] + 1, 1], W[j[0] - 1:j[0] + 1, 0])) * 1000, 1) if len(j) and j[0] > 0 else None
        wide = np.nonzero(W[:, 0] > 0.010)[0]
        depth.append(float((W[wide[0], 1] if len(wide) else W[-1, 1]) - zs) * 1000)
    out["cleavage_line_depth_mm"] = round(max(depth), 1) if depth else None
    out["cleavage_line_depth_mm_by_height"] = [round(x, 1) for x in depth]
    # -- the waist under it
    def width(y):
        lw = _loop(V, T, y)
        return float(lw[:, 0].max() - lw[:, 0].min()) if lw is not None and lw[:, 0].max() < 0.25 else None
    yf = Ps[fold][0]
    ub, bw = width(yf), width(p[1])
    ys = np.arange(0.95, yf, 0.0025)
    ws = [(w, y) for w, y in ((width(y), y) for y in ys) if w]
    if ub and ws:
        w, y = min(ws)
        out["underbust_w_mm"] = round(ub * 1000, 1)
        out["waist_w_mm"] = round(w * 1000, 1)
        out["waist_over_underbust_w"] = round(w / ub, 3)
        out["fold_to_waist_mm"] = round((yf - y) * 1000, 1)
        if bw:
            out["bust_over_waist_w"] = round(bw / w, 3)
    return out


def _path(V, T, p, psi_deg, up=0.17):
    """The profile up a path from the apex p: the mesh cut by the plane through p that holds the forward axis (z) and
    the direction d = (sin psi, cos psi, 0) (psi 0 straight up, + toward the left breast's outer side), from p up to
    `up` along d: (s along d, z) points ordered top -> apex (m)."""
    import breast_measure as bm
    ps = math.radians(psi_deg)
    d = np.array([math.sin(ps), math.cos(ps), 0.0])
    n = np.array([math.cos(ps), -math.sin(ps), 0.0])
    M = np.stack([n, d, [0.0, 0.0, 1.0]], 1)
    Vr, pr = V @ M, p @ M
    best = None
    for L in bm.section(Vr, T, 0, pr[0]):
        dd = float(np.linalg.norm(L - pr, axis=1).min())
        if best is None or dd < best[0]:
            best = (dd, L)
    L = best[1]
    nL = len(L)
    i0 = int(np.argmin(np.linalg.norm(L - pr, axis=1)))
    st = 1 if L[(i0 + 2) % nL, 1] > L[i0, 1] else -1
    out, i = [], i0
    for _ in range(nL):
        q = L[i % nL]
        if q[1] - pr[1] > up or q[2] < -0.02:
            break
        out.append(q)
        i += st
    P = np.array(out)[::-1]
    return np.c_[P[:, 1] - pr[1], P[:, 2]]


def root_blend(V, T, Vref, b):
    """P1 R1c round 3 (milestone judge 2: "two spheres stuck onto a flat chest": a crisp line, a dark crease over a
    lit rim, arcs over each breast top): the UPPER ROOT's blend as numbers, left breast, rest body, on three paths up
    from the apex (_path: psi -28 inner, 0 centre, +28 outer third of the upper root; the clavicle side). On each
    (1 mm, light smoothing) the root is where the outline leaves the chest-wall reference by 3 mm; from 25 mm above it to 45 mm below
    the CONCAVE turn (curvature under -3/m, the mesh's facet noise below that):
      width_mm: the arc over which the central 80 % of that turn happens (a fillet: small; a blend: wide);
      depth_mm: the outline's deepest point behind the chord across the turn (5..95 %): how deep the concave part is;
      turn_deg: the whole concave turn;
      crease_deg_per_mm: the most the outline turns concave within any 6 mm (/ 6): the crease detector (a cel band
        and the baked cavity draw a line where it is high).
    Reported per path and as the worst (least width over the paths turning 15 deg or more, most depth, most
    crease) over the three. The upper-pole fill
    below the blend (upper_pole_fill_below_blend): breast_round's fill from the centre path's blend end (95 %) to
    the apex instead of the 3 mm root (a wide blend is not the pole's slope).
"""
    import breast_measure as bm
    from scipy.spatial import cKDTree
    out = {}
    p = np.asarray(b["apex_mm"]) / 1000.0
    worst = {"width_mm": 1e9, "depth_mm": 0.0, "crease_deg_per_mm": 0.0}
    for name, psi in (("inner", -28.0), ("centre", 0.0), ("outer", 28.0)):
        Ps = bm.resample(_path(V, T, p, psi))
        dref = cKDTree(bm.resample(_path(Vref, T, p, psi))).query(Ps)[0]
        ia = len(Ps) - 1
        root = next((j for j in range(ia, -1, -1) if dref[j] < 0.003), 0)
        k2 = bm.curvature2(bm.gsmooth(Ps, 2.0))
        k1 = bm.curvature2(bm.gsmooth(Ps, 1.0))
        w0, w1 = max(root - 25, 2), min(root + 45, ia - 2)
        jp = w0 + int(np.argmax(-k2[w0:w1]))                  # the main concave lobe's peak
        j0, j1 = max(jp - 25, w0), min(jp + 26, w1)
        cc = np.maximum(-k2[j0:j1] - 3.0, 0.0) * 1e-3          # rad per mm
        C = np.cumsum(cc)
        r = {"root_s_mm": round(float(Ps[root, 0]) * 1000, 1)}
        if C[-1] > 1e-6:
            q = lambda f: j0 + int(np.searchsorted(C, f * C[-1]))
            a5, a95 = q(0.05), q(0.95)
            r["width_mm"] = round(float(C[-1]) / max(float(cc.max()), 1e-9), 1)   # the lobe's equivalent width
            ch = Ps[a95] - Ps[a5]
            e = ch / max(float(np.linalg.norm(ch)), 1e-9)
            nrm = np.array([e[1], -e[0]])                    # the chord's front side (+z for a top -> down chord)
            if nrm[1] < 0:
                nrm = -nrm
            r["depth_mm"] = round(float(max(0.0, -((Ps[a5:a95 + 1] - Ps[a5]) @ nrm).min())) * 1000, 1)
            r["turn_deg"] = round(math.degrees(float(C[-1])), 1)
            if name == "centre":
                out["_blend_end"] = a95
        else:
            r.update(width_mm=0.0, depth_mm=0.0, turn_deg=0.0)
        c1 = np.maximum(-k1[w0:w1], 0.0) * 1e-3
        w6 = np.convolve(c1, np.ones(6), "valid") if len(c1) >= 6 else c1
        r["crease_deg_per_mm"] = round(math.degrees(float(w6.max())) / 6.0, 2)
        out["root_blend_" + name] = r
        if r["turn_deg"] >= 15.0:                              # a path that hardly turns has no blend to spread
            worst["width_mm"] = min(worst["width_mm"], r["width_mm"])
        worst["depth_mm"] = max(worst["depth_mm"], r["depth_mm"])
        worst["crease_deg_per_mm"] = max(worst["crease_deg_per_mm"], r["crease_deg_per_mm"])
    out["root_blend_width_mm"] = worst["width_mm"] if worst["width_mm"] < 1e8 else None
    out["root_blend_width_mm_centre"] = out["root_blend_centre"]["width_mm"]
    # P1 R1c round 6: the width alone punishes a smaller turn (width = turn / peak; a pole that hardly turns has a short
    # lobe): what a cel band reads is how fast it turns, the lobe's peak (turn / width, 2 mm smoothing)
    rc = out["root_blend_centre"]
    out["root_blend_peak_deg_per_mm_centre"] = round(rc["turn_deg"] / max(rc["width_mm"], 1e-6), 2) if rc["width_mm"] else 0.0
    out["root_blend_depth_mm"] = worst["depth_mm"]
    out["root_crease_deg_per_mm"] = worst["crease_deg_per_mm"]
    # the upper-pole fill below the blend (as breast_round's, from the blend's end on the centre path)
    pr = b["_profile"]
    Pc = np.asarray(pr["P"])
    if "_blend_end" in out:
        Pa = bm.resample(_path(V, T, p, 0.0))
        top = Pa[out.pop("_blend_end")]
        y_top = p[1] + top[0]
        j = int(np.argmin(np.abs(Pc[:pr["apex"] + 1, 0] - y_top)))
        U = Pc[max(j, pr["root"]):pr["apex"] + 1]
        c, R, _ = _circle(Pc[pr["root"]:pr["fold"] + 1])
        a0, a1 = U[0], U[-1]
        ch = a1 - a0
        L = float(np.linalg.norm(ch))
        e = ch / max(L, 1e-9)
        nrm = np.array([-e[1], e[0]])
        if nrm[1] < 0:
            nrm = -nrm
        s, d = (U - a0) @ e, (U - a0) @ nrm
        area = float(np.sum(0.5 * (d[1:] + d[:-1]) * np.diff(s)))
        th = 2 * math.asin(min(1.0, L / (2 * R)))
        out["upper_pole_fill_below_blend"] = round(area / max(R * R * (th - math.sin(th)) / 2, 1e-12), 3)
    return out


def upper_turn(V, T, Vref, b, rnd, sig=3.0, above=0.040, band_deg=10.0):
    """P1 R1c round 5 (the game's Look camera: a thin LIT RIM arcs over each breast top, the shade just above it): how
    the UPPER POLE turns, left breast, rest body, on root_blend's three paths (psi -28 inner, 0 centre, +28 outer), from
    `above` (40 mm) over the root (3 mm off the chest-wall reference) down to the apex, 1 mm steps, smoothed sig mm
    (3 mm: under half our ~8 mm quads, the facet ripple ~10 % of the globe's 1/R). Per path:
      turn_max_deg_per_mm: the most the outline turns, either sign (deg/mm), over the path's upper part (down to where
        the normal is 30 deg above level: the globe's front below it is an ellipsoid's, a / b^2, tighter than its side
        circle and no part of the rim); turn_max_over_globe: that / the globe's own 1/R (breast_round's side circle);
      convex_peak_mm: the main convex peak's width at half its height (mm along the path; a broad crest: wide);
      summit_deg: the normal's highest elevation above level (90 = a shelf facing straight up);
      crest_band_mm: how tall the band within band_deg of the summit stands seen from the front (level camera:
        sum of cos(elevation) ds): the lit rim's height in the picture (the key and the lamps behind her light what
        faces up; a summit that faces up, foreshortened to a few mm, is the thin bright line).
    Reported per path and as the worst over the three."""
    import breast_measure as bm
    from scipy.spatial import cKDTree
    out = {}
    p = np.asarray(b["apex_mm"]) / 1000.0
    invR = math.degrees(1.0 / max(float(rnd["side_radius_mm"]), 1.0))       # deg per mm
    worst = {"turn_max_over_globe": 0.0, "convex_peak_mm": 1e9, "summit_deg": 0.0, "crest_band_mm": 1e9}
    for name, psi in (("inner", -28.0), ("centre", 0.0), ("outer", 28.0)):
        Ps = bm.resample(_path(V, T, p, psi))
        dref = cKDTree(bm.resample(_path(Vref, T, p, psi))).query(Ps)[0]
        ia = len(Ps) - 1
        root = next((j for j in range(ia, -1, -1) if dref[j] < 0.003), 0)
        Pg = bm.gsmooth(Ps, sig)
        k = np.degrees(bm.curvature2(Pg)) / 1000.0
        d1 = np.gradient(Pg, axis=0)
        el = np.degrees(np.arctan2(d1[:, 1], -d1[:, 0]))      # (s down, z forward): the normal's elevation above level
        j0 = max(root - int(round(above * 1000)), int(3 * sig))
        j1 = ia - int(3 * sig)
        low = np.nonzero(el[root:j1] < 30.0)[0]
        jt = root + int(low[0]) if len(low) else j1                # the upper part: down to elevation 30 deg
        kk = k[j0:jt]
        r = {"root_s_mm": round(float(Ps[root, 0]) * 1000, 1)}
        jm = int(np.argmax(np.abs(kk)))
        r["turn_max_deg_per_mm"] = round(float(abs(kk[jm])), 2)
        r["turn_max_at_mm"] = j0 + jm - root
        r["turn_max_over_globe"] = round(float(abs(kk[jm])) / invR, 2)
        jc = int(np.argmax(kk))
        h = kk[jc] / 2.0
        a, e = jc, jc
        while a > 0 and kk[a - 1] >= h:
            a -= 1
        while e < len(kk) - 1 and kk[e + 1] >= h:
            e += 1
        r["convex_peak_mm"] = int(e - a + 1)
        r["convex_peak_at_mm"] = j0 + jc - root
        ew = el[j0:j1]
        js = int(np.argmax(ew))
        r["summit_deg"] = round(float(ew[js]), 1)
        r["summit_at_mm"] = j0 + js - root
        cb = ew >= ew[js] - band_deg
        lo, hi = js, js
        while lo > 0 and cb[lo - 1]:
            lo -= 1
        while hi < len(cb) - 1 and cb[hi + 1]:
            hi += 1
        r["crest_band_mm"] = round(float(np.cos(np.radians(ew[lo:hi + 1])).sum()), 1)
        out["upper_turn_" + name] = r
        worst["turn_max_over_globe"] = max(worst["turn_max_over_globe"], r["turn_max_over_globe"])
        worst["convex_peak_mm"] = min(worst["convex_peak_mm"], r["convex_peak_mm"])
        worst["summit_deg"] = max(worst["summit_deg"], r["summit_deg"])
        worst["crest_band_mm"] = min(worst["crest_band_mm"], r["crest_band_mm"])
    out["upper_turn_max_over_globe"] = worst["turn_max_over_globe"]
    out["upper_turn_convex_peak_mm"] = worst["convex_peak_mm"]
    out["upper_summit_deg"] = worst["summit_deg"]
    out["upper_crest_band_mm"] = worst["crest_band_mm"]
    return out


def spec_measures(spec_path, body_glb):
    """Breast and glute numbers on the spec's own body (formview.body): sections "breast" and "glutes"."""
    import tempfile
    sys.path.insert(0, str(HERE / "sculpt"))
    import formview
    import breast_measure as bm
    import glute_measure as gm
    from sliders import load_spec
    V, T, H, HT, z, rep = formview.body(spec_path)
    sl = load_spec(spec_path).get("sliders", {})
    with tempfile.TemporaryDirectory() as tmp:
        bare = _derived(spec_path, BREAST_SLIDERS, (), tmp)
        Vb = formview.body(bare)[0]
        if sl.get("breast_a", 0) > 0 or sl.get("breast_b", 0) > 0:
            Vref = formview.body(_derived(spec_path, BREAST_SLIDERS, ("chest_wall",), tmp))[0]
        else:
            Vref = Vb
    b = bm.measure(V, T, Vb, Vref, H, HT, "spec")
    b.update(breast_round(V, T, Vref, b))
    b.update(root_blend(V, T, Vref, b))
    b.update(upper_turn(V, T, Vref, b, b))
    b = {k: v for k, v in b.items() if not k.startswith("_")}
    g = gm.measure(spec_path, V=V, z=z, skel_glb=body_glb)
    g = {k: v for k, v in g.items() if not k.startswith("_")}
    for k in ("apex_y_mm", "apex_z_mm"):
        b[k] = None
    b["apex_y_mm"], b["apex_z_mm"] = b["apex_mm"][1], b["apex_mm"][2]
    b["cleavage_floor_over60"] = g.get("cleavage_floor_over60")
    return {"breast": b, "glutes": g}


def hanging(ctx):
    """P1 R1c round 7, on the build's own rig (lbs + its correctives) with the arms hanging 8 deg (the Look): the pocket
    on the breast's outer base and the shoulder line. pocket_slot_depth_mm: the front envelope z(x) at y from the apex's
    height up, x from 13 to 22 cm: the deepest drop between a crest on the breast side and one on the arm side, worst
    height (the pit); shoulder_line_concave_per_m and _sign_changes: the front silhouette's top from 12.5 to 20.5 cm out,
    10 mm smoothed: its largest concave curvature and its sign changes past +-4 /m."""
    import check, rig_drive as rd
    glb = ctx["glb"]
    P = check.make_poser("lbs", str(glb), json.loads((Path(glb).parent / "rig.json").read_text()))
    h = lambda G, n: G[P.index[n]][:3, 3]
    _, G, _ = P.pose([])
    t = []
    for s, sg in (("l", 1), ("r", -1)):
        d = rd._n(h(G, "lowerarm_" + s) - h(G, "upperarm_" + s))
        e = math.radians(8.0)
        t.append(("upperarm_" + s, rd._arc(d, rd._n(np.array([sg * math.sin(e), -math.cos(e), 0.03])))))
    V = P.pose(t)[0][P.piece == "body"]
    Tb = P.T[np.all(P.piece[P.T] == "body", axis=1)]
    gs = lambda a, sd: np.convolve(np.pad(a, 3 * sd, mode="edge"), np.exp(-0.5 * (np.arange(-3 * sd, 3 * sd + 1) / sd) ** 2) / (sd * math.sqrt(2 * math.pi)), "valid")
    xs = np.arange(0.13, 0.22, 0.001)
    worst = 0.0
    E = V[np.concatenate([Tb[:, [0, 1]], Tb[:, [1, 2]], Tb[:, [2, 0]]])]
    for y in np.arange(1.40, 1.45, 0.005):
        Vt = V[Tb]
        sg_ = np.sign(Vt[:, :, 1] - y)
        Vt = Vt[(sg_.max(1) > 0) & (sg_.min(1) < 0)]
        ed = []
        for u, v in ((0, 1), (1, 2), (2, 0)):
            du, dv = Vt[:, u, 1] - y, Vt[:, v, 1] - y
            cr = du * dv < 0
            pt = np.full((len(Vt), 3), np.nan)
            pt[cr] = Vt[cr, u] + (Vt[cr, v] - Vt[cr, u]) * (du[cr] / (du[cr] - dv[cr]))[:, None]
            ed.append(pt)
        ed = np.stack(ed, 1)                                 # each triangle's cut segment, sampled along it
        ok_ = ~np.isnan(ed[:, :, 0])
        s0 = ed[np.arange(len(ed)), ok_.argmax(1)]
        s1 = ed[np.arange(len(ed)), 2 - ok_[:, ::-1].argmax(1)]
        q = np.concatenate([s0 + (s1 - s0) * f_ for f_ in np.linspace(0, 1, 9)])
        zf = np.full(len(xs), -9.0)
        i = np.round((q[:, 0] - xs[0]) / 0.001).astype(int)
        ok = (i >= 0) & (i < len(xs))
        np.maximum.at(zf, i[ok], q[ok, 2])
        g = zf > -5
        if g.sum() < 20:
            continue
        zs = gs(np.interp(xs, xs[g], zf[g]), 1)
        for j in range(5, len(xs) - 5):
            worst = max(worst, min(zs[:j].max() - zs[j], zs[j + 1:].max() - zs[j]))
    xt = np.arange(0.10, 0.22, 0.002)
    top = np.full(len(xt), -9.0)
    m = E[:, :, 1].min(1) > 1.3
    for a, b in E[m]:
        n = max(2, int(np.linalg.norm(a - b) / 0.001))
        pp = a + (b - a) * np.linspace(0, 1, n)[:, None]
        i = np.round((pp[:, 0] - xt[0]) / 0.002).astype(int)
        ok = (i >= 0) & (i < len(xt))
        np.maximum.at(top, i[ok], pp[ok, 1])
    ys = gs(top, 3)
    d1 = np.gradient(ys, xt)
    k = np.gradient(d1, xt) / (1 + d1 * d1) ** 1.5
    kk = k[(xt >= 0.125) & (xt <= 0.205)]
    sg = np.sign(kk) * (np.abs(kk) > 4)
    sg = sg[sg != 0]
    return {"pocket_slot_depth_mm": round(float(worst) * 1000, 1), "shoulder_line_concave_per_m": round(float(kk.max()), 1),
            "shoulder_line_sign_changes": int((sg[1:] != sg[:-1]).sum())}


def measure(body_glb, rules=None, spec=None):
    rules = rules or json.loads(RULES.read_text())
    if spec is None and (Path(body_glb).parent / "build.json").exists():
        sp = json.loads((Path(body_glb).parent / "build.json").read_text()).get("spec")
        if sp:
            spec = str(HERE.parents[1] / sp)
    B = Glb(body_glb)
    from posers import guess_body
    V, T = rest(B, guess_body(B))
    H, HT = rest(B, "HeroineHead")
    ctx = {"V": V, "T": T, "H": H, "HT": HT, "B": B, "glb": body_glb}
    out, miss, n, skipped = {}, [], 0, []
    extra = spec_measures(spec, body_glb) if spec else {}
    for sec, rs in rules["sections"].items():
        if sec in ("breast", "glutes") and not spec:
            skipped.append(sec)
            continue
        if sec == "hanging" and not (Path(body_glb).parent / "rig.json").exists():
            skipped.append(sec)
            continue
        if sec not in MEASURES and sec not in extra:
            continue
        m = MEASURES[sec](ctx) if sec in MEASURES else extra[sec]
        out[sec] = {"measured": m, "rules": {}}
        for key, r in rs["rules"].items():
            v = m.get(key)
            if v is None:
                miss.append(f"{sec}.{key} not measured")
                out[sec]["rules"][key] = {"value": None, "band": r["band"], "ok": False}
                n += 1
                continue
            lo, hi = r["band"]
            ok = (lo is None or v >= lo) and (hi is None or v <= hi)
            out[sec]["rules"][key] = {"value": v, "band": r["band"], "ok": bool(ok)}
            n += 1
            if not ok:
                miss.append(f"{sec}.{key} {v} not in {r['band']}")
    out["summary"] = f"forms: {n - len(miss)} of {n} rules in band" + (f"; MISS {'; '.join(miss)}" if miss else "") + (f" (skipped {','.join(skipped)}: no spec)" if skipped else "")
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("body")
    ap.add_argument("--spec", help="the body's spec (default: build.json's, beside the glb)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    r = measure(a.body, spec=a.spec)
    print(r["summary"])
    for sec in ("breast", "glutes"):
        if sec in r:
            print(sec, json.dumps(r[sec]["measured"]))
    if a.out:
        Path(a.out).mkdir(parents=True, exist_ok=True)
        (Path(a.out) / "forms.json").write_text(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
