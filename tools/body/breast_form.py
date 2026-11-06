"""P1 R1 form library: HER BREASTS as our designed form (tools/body/designed/breast.json), the rules code.

The MakeHuman cup sliders (bust_size/firmness/set/point/spacing, our bust_lift on top) grow the breast downward and
leave a ledge across the upper pole, a deep flat shelf under it and faceted points. These rules replace them:

  py:breast_form.chest_wall  the base: the MakeHuman base mesh mound and nipple (8.8 mm tip over its smoothed chest)
                             refilled as a smooth chest wall (a biharmonic fill of the region, rim held, blended in
                             by a C2 mask). Linear in v on a given body. Every designed breast sits on it, so the
                             breast sliders are pure added volumes, clean at any value (v = 0.5 has no half nipple).
  py:breast_form.dome        ROUTE (a): the breast as a height field over that wall, set by profile curves: per
                             side a base point (landmark: the breast part centroid + an offset), an axis (yaw out,
                             pitch), four footprint radii (up, low, medial, lateral; blended smoothly) and four 1D
                             profiles (the upper pole slope, the lower pole round curve, the inner and outer
                             flanks), each its slope law sigma(t) = t / sqrt(t^2 + s^2) * (1 + beta t^2) times a C2
                             fold window over its last "fold" of the radius, so every profile meets the wall tangent
                             with zero curvature (C2: no crease) and all share one rounded cap at the apex.
                             The move is h(u, w) along the axis: linear in v (a blend target on any body).
                             P1 R1b: a profile may use the ROUND law instead ("law": "arc", arc_table: a circle
                             of radius R_m from the apex into a solved C2 fold; her lower pole), the cap may keep
                             each pole's own curvature ("cap": "axes", a C-inf switched quadratic form, so a
                             round lower pole and a soft upper turn meet at a C2 apex), and the lower pole's move
                             may turn down with the receding chest wall (axis "pitch_low_deg", C2 ramp from 0 at
                             the apex). The JSON's "relax" (sliders.relax) evens the medial column the midline
                             fade stretches.
  (route (b) is a stored target: tools/body/sculpt/breast_b.py; the support fields are rule "field" in the JSON)

Coordinates: glTF metres, x her left (+), y up, z front (+); the right side is the left side mirrored (topology
mirror_of), so both are exactly symmetric.
"""
import os
import json
import numpy as np
from sliders import smoother, HERE

_C = {}


def extra(sl):
    """Per bake: the topology part labels, mirror map and edge graph."""
    key = ("extra", sl.path)
    if key not in _C:
        import scipy.sparse as sp
        t = sl.topo()
        tier = t["tier"]
        z = np.load(os.path.join(HERE, "out", "topo", tier + ".npz"))
        Q = t["Q"]
        n = len(sl.V0)
        e = np.unique(np.sort(np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]]), 1), axis=0)
        A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
        _C[key] = {"part": z["part"].astype(int), "mirror": z["mirror_of"].astype(np.int64), "A": A, "e": e, "Q": Q,
                   "parts": [str(p) for p in z["parts"]], "tier": tier}
    return _C[key]


def mirror_left(sl, D, eps=1e-4):
    """D computed on the left (x >= 0) carried to the right by the topology mirror map; x-move 0 on the midline."""
    X = extra(sl)
    mi = X["mirror"]
    x0 = sl.V0[:, 0]
    R = x0 < -eps
    D = D.copy()
    D[R] = D[mi[R]] * np.array([-1.0, 1.0, 1.0])
    mid = np.abs(x0) <= eps
    D[mid, 0] = 0.0
    return D


def vnormals(V, Q):
    fn = np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]])
    N = np.zeros_like(V)
    for k in range(4):
        np.add.at(N, Q[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


# ------------------------------------------------------------------------------------------------ the wall --
def wall_delta(sl, c, V):
    """The chest wall move on body V (v = 1): the region (mask c["region"] on V0, both sides) refilled by the
    biharmonic (thin-plate) surface of the uniform graph Laplacian with everything outside held (two rings: C1 at
    the rim), times the C2 blend mask c["blend"] (1 over the mound, 0 well inside the region rim)."""
    import scipy.sparse as sp
    from scipy.sparse.linalg import splu
    X = extra(sl)
    key = ("wall", sl.path, json.dumps(c["region"], sort_keys=True))
    if key not in _C:
        n = len(sl.V0)
        free = sl.mask(c["region"], sl.V0) > 1e-9
        A = X["A"]
        deg = np.asarray(A.sum(1)).ravel()
        L = sp.identity(n, format="csr") - sp.diags(1.0 / deg) @ A
        M = (L.T @ L).tocsr()
        f, k = np.nonzero(free)[0], np.nonzero(~free)[0]
        _C[key] = (f, k, splu(M[f][:, f].tocsc()), M[f][:, k].tocsr())
    f, k, lu, Mfk = _C[key]
    W = V.copy()
    W[f] = lu.solve(-(Mfk @ V[k]))
    w = sl.mask(c["blend"], sl.V0)
    return mirror_left(sl, (W - V) * w[:, None])


def chest_wall(sl, c, v, V, values):
    return V + v * wall_delta(sl, c, V)


# ------------------------------------------------------------------------------------------ route (a) dome --
def profile_table(p, n=4001):
    """A 1D profile P(t), t = 0 (apex) .. 1 (the root on the wall): P = 1 - int sigma / int_0^1 sigma with the slope
    law sigma(t) = t / sqrt(t^2 + s^2) * (1 + beta t^2) * smoother((1 - t) / fold): a rounded cap of size s, a slope
    that settles straight (beta 0) or keeps growing (beta > 0: a round, full curve), and a C2 fold over the last
    "fold" of the radius (the slope eases to 0 with zero curvature at t = 1: the profile meets the wall tangent)."""
    t = np.linspace(0.0, 1.0, n)
    s, b, f = float(p["s"]), float(p.get("beta", 0.0)), float(p["fold"])
    sig = t / np.sqrt(t * t + s * s) * (1.0 + b * t * t) * smoother((1.0 - t) / f)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (sig[1:] + sig[:-1]) * np.diff(t))])
    return t, 1.0 - cum / cum[-1]


def arc_table(p, H, r, n=4001):
    """The ROUND law (p["law"] = "arc", P1 R1b: the lower pole): a profile whose tangent turns by phi with
    sin(phi) = t / k * smoother((1 - t) / f), k = R / r. On a profile h(w) the curvature is exactly d sin(phi) / dw,
    so over the arc it is 1 / R (p["R_m"]: a circle from the apex down, the round full lower pole that carries the
    weight); in the window over the last f of the radius it turns negative (the soft fold) and eases to 0 at t = 1
    (the profile meets the wall tangent with zero curvature: C2). f is solved (bisection) so the profile drops exactly
    the projection H over the footprint radius r: the arc and the fold share the footprint, so a rounder arc (smaller
    R) gets a longer, softer fold and a larger R a tighter one. Returns t, P (P = h / H) like profile_table."""
    key = ("arc", float(p["R_m"]), float(H), float(r), n)
    if key in _C:
        return _C[key]
    t = np.linspace(0.0, 1.0, n)
    k = float(p["R_m"]) / float(r)

    def drop(f):
        S = t / k * smoother((1.0 - t) / f)
        if S.max() >= 0.995:                              # the arc would turn past ~84 deg: no height field
            return np.inf, None
        tp = S / np.sqrt(1.0 - S * S)
        cum = np.concatenate([[0.0], np.cumsum(0.5 * (tp[1:] + tp[:-1]) * np.diff(t))])
        return cum[-1] * r, cum                           # metres dropped over the radius
    lo, hi = 0.02, 0.95                                   # the drop falls as the fold window f grows
    assert drop(hi)[0] <= H <= drop(lo)[0], ("arc law: no fold fits R_m %.3f with h %.3f over r %.3f" % (k * r, H, r))
    for _ in range(60):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if drop(m)[0] > H else (lo, m)
    d, cum = drop(hi)
    out = (t, 1.0 - cum / cum[-1], hi)
    _C[key] = out
    return out


def frame(c, side=1.0):
    """The breast axis a (unit, glTF) and the base plane up / lateral directions for a side (+1 left)."""
    yaw, pit = np.radians(c["axis"]["yaw_deg"]), np.radians(c["axis"].get("pitch_deg", 0.0))
    a = np.array([side * np.sin(yaw) * np.cos(pit), np.sin(pit), np.cos(yaw) * np.cos(pit)])
    up = np.array([0.0, 1.0, 0.0]) - a[1] * a
    up /= np.linalg.norm(up)
    lat = np.cross(up, a)
    if lat[0] * side < 0:
        lat = -lat
    return a, up, lat / np.linalg.norm(lat)


def anchor(sl, c, V):
    """The base point (left side): the breast part centroid on body V plus the design offset c["c_off"]."""
    X = extra(sl)
    bp = (X["part"] == X["parts"].index("breast")) & (sl.V0[:, 0] > 0)
    return V[bp].mean(0) + np.asarray(c.get("c_off", [0, 0, 0]), float)


def smooth_r(x, r_neg, r_pos, width):
    """A footprint radius that switches smoothly (C-infinity) from r_neg (x < 0) to r_pos (x > 0) over +-width."""
    g = 0.5 * (1.0 + np.tanh(x / width))
    return r_neg + (r_pos - r_neg) * g


def dome_height(c, u, w):
    """h(u, w) (m) over the base plane: the four profiles blended by direction, one shared cap near the apex."""
    r = c["r"]
    bw = c.get("r_blend_m", 0.03)
    xi = u / smooth_r(u, r["med"], r["lat"], bw)
    eta = w / smooth_r(w, r["low"], r["up"], bw)
    rho = np.sqrt(xi * xi + eta * eta)
    reg = c.get("dir_reg", 0.15)
    dn = np.sqrt(rho * rho + reg * reg)
    dx, dy = xi / dn, eta / dn
    cw = {"lat": np.maximum(dx, 0) ** 3, "med": np.maximum(-dx, 0) ** 3, "up": np.maximum(dy, 0) ** 3,
          "low": np.maximum(-dy, 0) ** 3}
    tot = sum(cw.values()) + 1e-12
    iso = reg * reg / (rho * rho + reg * reg)            # at the apex the direction is undefined: an even mix
    h = np.zeros_like(u)
    caps, tabs = {}, {}
    for k in ("up", "low", "med", "lat"):
        p = c["profiles"][k]
        t, P = arc_table(p, c["h_m"], r[k])[:2] if p.get("law") == "arc" else profile_table(p)
        tabs[k] = (t, P)
        caps[k] = (1.0 - P[40]) / t[40] ** 2             # the profile own cap curvature (1 - P ~ kappa t^2)
    if c.get("cap") == "axes":
        # P1 R1b: the cap keeps each pole's own curvature (the lower pole's round arc starts AT the apex, the upper
        # pole turns into its straight slope sooner): a quadratic form whose two coefficients switch smoothly (C-inf,
        # like the radii) from medial to lateral and from low to up, so the apex stays C2
        cap = 1.0 - smooth_r(u, caps["med"], caps["lat"], bw) * xi * xi - smooth_r(w, caps["low"], caps["up"], bw) * eta * eta
    else:
        cap = 1.0 - float(np.mean(list(caps.values()))) * rho * rho     # one shared cap 1 - kappa rho^2 (C2 there)
    rc = c.get("cap_rho", 0.25)
    blend = 1.0 - smoother(rho / rc)                     # the cap near the apex, eased into the four profiles
    for k in ("up", "low", "med", "lat"):
        t, P = tabs[k]
        Pk = np.interp(np.minimum(rho, 1.0), t, P) * (rho < 1.0)
        Pk = blend * cap + (1.0 - blend) * Pk
        wk = (1.0 - iso) * cw[k] / tot + iso * 0.25
        h += wk * Pk
    return float(c["h_m"]) * np.clip(h, 0.0, None), rho


def dome_delta(sl, c, V):
    """Route (a) move on body V (v = 1): for the left side candidate points (trunk / breast / shoulder parts, in
    front of the base point), u, w = their coordinates in the base plane, the move h(u, w) along the axis a; the right
    side mirrored."""
    X = extra(sl)
    a, up, lat = frame(c, 1.0)
    c0 = anchor(sl, c, V)
    keep = [X["parts"].index(p) for p in ("trunk", "breast", "shoulder")]
    cand = np.isin(X["part"], keep) & (sl.V0[:, 0] >= 0)
    q = V - c0
    cand &= (q @ a > -c.get("depth_m", 0.08)) & (np.linalg.norm(q, axis=1) < 0.25)
    u, w = q[cand] @ lat, q[cand] @ up
    h, rho = dome_height(c, u, w)
    if c.get("midline_fade_m"):
        # the two breasts never share the midline: the height eases to 0 (C2) within this of it on V0, so the
        # cleavage floor stays one smooth valley (without it the medial flanks met in a crease: 13 quads > 60 deg)
        h = h * smoother(np.abs(sl.V0[cand, 0]) / c["midline_fade_m"])
    # the move direction fans across the breast: the axis yaw at the base point, turning in toward the cleavage on
    # the medial flank and out on the lateral (c["axis"]["fan_deg_per_m"] per metre of u): the apex points out
    # while the inner flank rises straight forward (a natural cleavage, no splay)
    yaw = np.radians(c["axis"]["yaw_deg"] + c["axis"].get("fan_deg_per_m", 0.0) * u)
    # P1 R1b: under the apex the chest wall recedes (her rib cage, ~15 deg); a level move shears the lower pole's
    # round arc flat against it, so the lower pole's move turns down with the wall: c["axis"]["pitch_low_deg"]
    # reached at the bottom of the footprint, eased in from 0 at the apex (smoother: C2; the upper pole unchanged)
    pit = np.radians(c["axis"].get("pitch_deg", 0.0)
                     + c["axis"].get("pitch_low_deg", 0.0) * smoother(-w / c["r"]["low"]))
    av = np.stack([np.sin(yaw) * np.cos(pit), np.sin(pit) * np.ones_like(yaw), np.cos(yaw) * np.cos(pit)], 1)
    D = np.zeros_like(V)
    D[cand] = h[:, None] * av
    return mirror_left(sl, D)


def dome(sl, c, v, V, values):
    return V + v * dome_delta(sl, c, V)