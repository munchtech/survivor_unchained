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
                             fade stretches. R1b round 2: r["lat_up"] (optional) gives the upper outer quadrant
                             its own lateral radius above a height w0 (C-inf switch): the outer side at armpit
                             height comes in where the hanging arm meets it, the side below keeps its reach.
                             R1b round 3: lat_up {"psi_deg": [p0, p1]} switches that radius by the direction from
                             the apex instead (each ray keeps its profile: no concave band, convex contours).
                             P1 R1c (the owner, 6 Nov: round): c["globe"] makes the breast a GLOBE (globe_delta):
                             an ellipsoid round a centre behind the wall, unioned with the chest wall by radial moves
                             and C2 fillets by direction, pressed at the midline; the profile dome becomes its soft base.
  (route (b) is a stored target: tools/body/sculpt/breast_b.py; the support fields are rule "field" in the JSON)

Coordinates: glTF metres, x her left (+), y up, z front (+); the right side is the left side mirrored (topology
mirror_of), so both are exactly symmetric.
"""
import os
import json
import math
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
def cot_weights(V, Q):
    """P1 R1c round 5b: the cotangent edge weights of the quad mesh (each quad split both ways, half weight each),
    computed on the body V itself: a GEOMETRIC Laplacian (linear precision), so a fill follows the surface, not the
    graph. Negative weights (obtuse corners) are clamped to a small positive share. Returns a sparse symmetric W."""
    import scipy.sparse as sp
    n = len(V)
    rows, cols, vals = [], [], []
    for tri in ((0, 1, 2), (0, 2, 3), (0, 1, 3), (1, 2, 3)):
        I = Q[:, tri]
        for a, b, o in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
            ea, eb = V[I[:, a]] - V[I[:, o]], V[I[:, b]] - V[I[:, o]]
            cr = np.linalg.norm(np.cross(ea, eb), axis=1)
            ct = (ea * eb).sum(1) / np.maximum(cr, 1e-12)
            rows += [I[:, a], I[:, b]]
            cols += [I[:, b], I[:, a]]
            vals += [0.25 * ct, 0.25 * ct]
    W = sp.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
    W.sum_duplicates()
    floor = 0.02 * float(np.abs(W.data).mean())
    W.data = np.maximum(W.data, floor)
    return W


def wall_delta(sl, c, V):
    """The chest wall move on body V (v = 1): the region (mask c["region"] on V0, both sides) refilled by the
    biharmonic (thin-plate) surface of the uniform graph Laplacian with everything outside held (two rings: C1 at
    the rim), times the C2 blend mask c["blend"] (1 over the mound, 0 well inside the region rim).
    P1 R1c round 5b: c["lap"] = "cot" uses the GEOMETRIC (cotangent) Laplacian of V instead (cot_weights): the
    uniform one has no linear precision, so where our quad rows bunch (the upper chest under the clavicle, ~10-20 mm
    over the breast's root) its fill rebuilt the base mesh's own 12-15 mm band facing ~10 deg more upward (a ridge
    the Look's high key and back lamps draw as a shade line over each breast top)."""
    import scipy.sparse as sp
    from scipy.sparse.linalg import splu
    X = extra(sl)
    free = sl.mask(c["region"], sl.V0) > 1e-9
    cot = c.get("lap") == "cot"
    key = ("wall", sl.path, json.dumps(c["region"], sort_keys=True)) + ((float(np.round(V[free].sum(), 9)),) if cot else ())
    if key not in _C:
        n = len(sl.V0)
        if cot:
            # only the free region and its two held rings enter the solve: the weights of that patch
            A = cot_weights(V, X["Q"])
        else:
            A = X["A"]
        deg = np.asarray(A.sum(1)).ravel()
        L = sp.identity(n, format="csr") - sp.diags(1.0 / np.maximum(deg, 1e-12)) @ A
        M = (L.T @ L).tocsr()
        f, k = np.nonzero(free)[0], np.nonzero(~free)[0]
        _C.clear() if len(_C) > 64 else None
        _C[key] = (f, k, splu(M[f][:, f].tocsc()), M[f][:, k].tocsr())
    f, k, lu, Mfk = _C[key]
    W = V.copy()
    W[f] = lu.solve(-(Mfk @ V[k]))
    w = sl.mask(c["blend"], sl.V0)
    return mirror_left(sl, (W - V) * w[:, None])


def chest_wall(sl, c, v, V, values):
    """The wall: the first fill (c["region"] / c["blend"]), then each later pass in c["passes"] (P1 R1c round 5b:
    a fill of its own region on the result: the upper chest band between the clavicle and the breast's root, so
    the slope from the collarbone runs into the root as one smooth turn), all with the same Laplacian."""
    D = wall_delta(sl, c, V)
    for p in c.get("passes", []):
        D = D + wall_delta(sl, dict(p, lap=c.get("lap")), V + D)
    return V + v * D


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
    r_lat = r["lat"]
    if "lat_up" in r and "psi_deg" in r["lat_up"]:
        # P1 R1b round 3: the upper outer quadrant's own lateral radius switched by the DIRECTION from the apex, not by
        # height: psi = the polar angle of (|u| / lat, w / up) (0 lateral, 90 up), r["lat"] below psi0 -> lat_up["r"]
        # above psi1 by a quintic ramp (C2). Along every ray from the apex the radius is one number, so each ray keeps
        # the profile's own shape (round 2's switch by height compressed the rays crossing it: a concave band between
        # the apex and the armpit, a pleat at the outer edge); a wide psi0..psi1 keeps every contour convex (the
        # footprint r(psi) has r^2 + 2 r'^2 - r r'' > 0). (Optional "ease_rho": eased in from the apex; off by default,
        # an ease is itself a squeeze along the rays.)
        lu = r["lat_up"]
        p0, p1 = lu["psi_deg"]
        psi = np.degrees(np.arctan2(w / r["up"], np.abs(u) / r["lat"]))
        g = smoother((psi - p0) / (p1 - p0))
        if lu.get("ease_rho"):
            g = g * smoother(np.hypot(u / r["lat"], w / r["up"]) / lu["ease_rho"])
        r_lat = r["lat"] + (lu["r"] - r["lat"]) * g
    elif "lat_up" in r:
        # P1 R1b round 2: the upper outer quadrant (armpit height) has its own lateral radius, switched smoothly (C-inf,
        # like the radii) from r["lat"] below to r["lat_up"] above the height w0 over +-bw: the outer side at armpit
        # height comes in (the hanging arm's inner side meets a clean gap) and the side below the armpit keeps its reach
        lu = r["lat_up"]
        r_lat = smooth_r(w - lu.get("w0_m", 0.0), r["lat"], lu["r"], lu.get("bw_m", bw))
    r_med = r["med"]
    if "med_up" in r:
        # P1 R1c (milestone judge: the cleavage opened into a V notch at its top): the upper INNER quadrant's own medial
        # radius, switched by the direction from the apex like lat_up (psi 0 medial, 90 up; quintic ramp, C2): the
        # inner flank reaches further toward the midline on the rays that climb toward the sternum, so the two inner
        # walls stay full (the midline fade still holds the floor) and the cleavage line starts higher; pure medial
        # rays (psi <= p0) keep r["med"], so the apex and the gap at apex height are unchanged by it
        mu = r["med_up"]
        p0, p1 = mu["psi_deg"]
        psi_m = np.degrees(np.arctan2(w / r["up"], np.abs(u) / r["med"]))
        g = smoother((psi_m - p0) / (p1 - p0))
        if mu.get("ease_rho"):
            # eased in from the apex (C2): the cap keeps its own shape, so the apex normal does not tip up and in
            g = g * smoother(np.hypot(u / r["med"], w / r["up"]) / mu["ease_rho"])
        r_med = r["med"] + (mu["r"] - r["med"]) * g
    xi = u / smooth_r(u, r_med, r_lat, bw)
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


def ramp(s):
    """C2 soft ramp: 0 for s <= -1, s for s >= 1, between the integral of smoother((s + 1) / 2) (a soft max(s, 0))."""
    s = np.asarray(s, float)
    x = np.clip((s + 1.0) / 2.0, 0.0, 1.0)
    inner = 2.0 * (x ** 6 - 3.0 * x ** 5 + 2.5 * x ** 4)      # 2 * int_0^x smoother
    return np.where(s >= 1.0, s, inner)


def shear_up(g, w, bw):
    """P1 R1c round 3: the globe's UPPER half leaned back into the chest: the ellipsoid's axis coordinate d is read as
    d + shear_up * w for w > 0 (switched in C-inf over +-bw like the radii; 0 at and below the apex height, so the
    apex and the lower curve keep their places): the upper half becomes a sheared (still elliptic) arc whose top, the
    place where it faces straight up, sits back inside the receding upper chest instead of standing in front of it
    as a level shelf (round 2: a 20-40 mm shelf at the top of each globe whose front edge read as a lit rim, the root
    behind it as a dark crease). The pole rolls from the chest straight into the curve."""
    s = float(g.get("shear_up", 0.0))
    return s * w * 0.5 * (1.0 + np.tanh(w / bw)) if s else 0.0


def globe_delta(sl, c, V, Va=None):
    """P1 R1c (the owner, 6 Nov: "our tests so far are not round"): the breast as a ROUND GLOBE, a soft union of an
    ellipsoid with the chest wall. Each candidate wall point moves RADIALLY from the globe's centre O (behind the
    wall) out to the ellipsoid where the wall lies inside it: the union is exactly the ellipsoid there (every section
    a circle / ellipse: round seen front, 3/4 and side, the upper pole full and rolling into the curve, the lower curve
    tucking under, the outer side wrapping past the chest wall: a radial move can pass the wall's side line, which a
    height field along one axis cannot), and blends into the wall over a C2 fillet of half-width k_m in radial
    distance (the root, the fold, the outer side: soft, no crease). g = c["globe"]:
      "o_off": O from the base point (anchor) in the base frame [lateral, up, along the axis] (m; the axis part
               negative: O behind the wall);
      "R": the ellipsoid's semi-axes from O {"lat", "med", "up", "low", "a"} (m), switched smoothly (C-inf, like the
               footprint radii, over r_blend_m) across O's planes: one smooth convex surface;
      "k_m": the fillet half-width; "press": {"x_m", ...}: the pressed inner face (see below).
    The two globes may overlap across the midline (pressed together): the move's inward x part saturates smoothly
    (tanh) at press.x_m from the midline, so the inner side flattens against its mirror into a narrow cleavage line
    and nothing crosses; the midline fade (midline_fade_m on V0) holds the cleavage floor. Linear in v."""
    X = extra(sl)
    g = c["globe"]
    a, up, lat = frame(c, 1.0)
    c0 = anchor(sl, c, V if Va is None else Va)          # the base point on the wall (not on the mound under it)
    o = np.asarray(g.get("o_off", [0.0, 0.0, -0.05]), float)
    O = c0 + o[0] * lat + o[1] * up + o[2] * a
    keep = [X["parts"].index(p) for p in ("trunk", "breast", "shoulder")]
    cand = np.isin(X["part"], keep) & (sl.V0[:, 0] >= 0)
    q = V - O
    R = g["R"]
    bw = c.get("r_blend_m", 0.03)
    u, w, d = q @ lat, q @ up, q @ a
    cand &= (d > -float(g.get("back_m", 0.08))) & (np.linalg.norm(q, axis=1) < 0.3)
    u, w, d, qc = u[cand], w[cand], d[cand], q[cand]
    d = d + shear_up(g, w, bw)
    Ru = smooth_r(u, R["med"], R["lat"], bw)
    Rw = smooth_r(w, R["low"], R["up"], bw)
    Ra = smooth_r(d, R.get("a_back", R["a"]), R["a"], bw)
    rho = np.sqrt((u / Ru) ** 2 + (w / Rw) ** 2 + (d / Ra) ** 2)          # 1 on the ellipsoid
    lv = np.linalg.norm(qc, axis=1)
    ls = lv / np.maximum(rho, 1e-9)                                       # the ellipsoid's radius on this ray
    k = g.get("k_m", 0.015)
    if isinstance(k, dict):
        # the fillet's half-width by direction from O (C-inf: the vertical pair switched across w = 0, the horizontal
        # pair across u = 0, mixed by the direction's share): a long soft root up, a softer side, a tighter fold
        sv, sh = (w / Rw) ** 2, (u / Ru) ** 2
        wv = sv / (sv + sh + 1e-4)
        k = wv * smooth_r(w, k["low"], k["up"], bw) + (1.0 - wv) * smooth_r(u, k["med"], k["lat"], bw)
    else:
        k = float(k)
    ln = lv + k * ramp((ls - lv) / k)
    D = np.zeros_like(V)
    mv = (ln - lv)[:, None] * qc / np.maximum(lv, 1e-9)[:, None]
    if c.get("midline_fade_m"):
        # the cleavage floor: held within midline_hold_m of the midline, then the C2 fade (the floor's first quads
        # stay low, so the pressed walls turn up off the floor over three quads, each fold under 60 deg)
        hold = float(g.get("midline_hold_m", 0.0))
        fade_m = c["midline_fade_m"]
        fu = g.get("midline_fade_up")
        if fu:
            # P1 R1c round 7: a narrower fade from fu.y up (V0, C2): the walls close to a line at and over the apex, the
            # slot's foot keeps its width (a floor there has no room to turn in)
            fade_m = fade_m + (float(fu["m"]) - fade_m) * smoother((sl.V0[cand, 1] - fu["y"][0]) / (fu["y"][1] - fu["y"][0]))
        mv *= smoother((np.abs(sl.V0[cand, 0]) - hold) / (fade_m - hold))[:, None]
    pr = g.get("press")
    if pr:
        # the pressed inner face: the inward x move saturates (C-inf) at x_m from the midline (room = how far a point
        # may still go in), so points flatten against the midline plane instead of crossing it
        xc = V[cand, 0]
        room = np.maximum(xc - float(pr.get("x_m", 0.003)), 0.0)
        dx = mv[:, 0]
        inw = dx < 0
        cl = pr.get("close")
        if cl:
            # P1 R1c round 7: the wall in front of the floor closes on its mirror (the visible line) while the floor's own
            # columns keep their fade (no new fold on the floor): the inward move is scaled by gain from column x0[0] to
            # x0[1] on V0 (C2), the walls lean in over a floor kept wide enough to turn up in folds under 60 deg
            x0 = np.abs(sl.V0[cand, 0])
            dxi = dx * (1.0 + (float(cl["gain"]) - 1.0) * smoother((x0 - cl["x0"][0]) / (cl["x0"][1] - cl["x0"][0])))
        else:
            dxi = dx
        sat = -room * np.tanh(-dxi / np.maximum(room, 1e-6))
        mv[:, 0] = np.where(inw, sat, dx)
        ve = pr.get("vee")
        if ve:
            # P1 R1c round 7: the slot's floor as a soft V: the floor's first columns rise along the axis so a narrow slot
            # turns up over them in folds under 60 deg (a flat floor between walls 6 mm apart turns 90 deg in one quad):
            # x0, z, x = columns on V0 and their offsets (m, C2 cubic), over the slot's height band y (V0: full y[1]..y[2])
            from scipy.interpolate import CubicSpline
            cs = CubicSpline(ve["x0"], ve["z"], bc_type="clamped")
            x0 = np.abs(sl.V0[cand, 0])
            y0 = sl.V0[cand, 1]
            yb = ve["y"]
            ybd = smoother((y0 - yb[0]) / (yb[1] - yb[0])) * (1.0 - smoother((y0 - yb[2]) / (yb[3] - yb[2])))
            mv[:, 2] += np.where(x0 < ve["x0"][-1], cs(np.minimum(x0, ve["x0"][-1])), 0.0) * ybd
            if ve.get("x"):
                cx = CubicSpline(ve["x0"], ve["x"], bc_type="clamped")
                mv[:, 0] += np.where(x0 < ve["x0"][-1], cx(np.minimum(x0, ve["x0"][-1])), 0.0) * ybd
    D[cand] = mv
    return mirror_left(sl, D)


def globe_coords(sl, c, P, Va):
    """Points P in the globe's frame: (u, w, d) from its centre O (lateral, up, along the axis; left side) and the
    ellipsoid's switched semi-axes there (Ru, Rw, Ra)."""
    g = c["globe"]
    a, up, lat = frame(c, 1.0)
    c0 = anchor(sl, c, Va)
    o = np.asarray(g.get("o_off", [0.0, 0.0, -0.05]), float)
    O = c0 + o[0] * lat + o[1] * up + o[2] * a
    R = g["R"]
    bw = c.get("r_blend_m", 0.03)
    q = P - O
    u, w, d = q @ lat, q @ up, q @ a
    d = d + shear_up(g, w, bw)
    return u, w, d, smooth_r(u, R["med"], R["lat"], bw), smooth_r(w, R["low"], R["up"], bw), \
        smooth_r(d, R.get("a_back", R["a"]), R["a"], bw), O, (a, up, lat)


def root_band(sl, c, P, Va, rf):
    """P1 R1c round 3: the weight (0..1, left side, C2) of the globe's ROOT band on the globed body P: in the globe's
    frame, the footprint coordinate f = |(u / Ru, w / Rw)| (1 on the rim where the globe meets the chest) and the
    elevation e = (d / Ra) / |(u / Ru, w / Rw, d / Ra)| (0 at the wall, 1 at the front pole). Full for f in
    rf["f"][1..2], easing to 0 at f[0] (on the globe) and f[3] (up the chest); full below e[0], 0 above e[1] (the
    globe's front never moves); the directions above the horizontal through O only (in-plane elevation sin, full
    above rf["dir"][1], 0 below dir[0]: the upper root, from the cleavage top over the top to the armpit side); the
    midline held (V0 |x| under mid[0], easing in to mid[1]: the pressed cleavage keeps its walls)."""
    u, w, d, Ru, Rw, Ra = globe_coords(sl, c, P, Va)[:6]
    xu, xw, xd = u / Ru, w / Rw, d / Ra
    f = np.sqrt(xu * xu + xw * xw)
    e = xd / np.maximum(np.sqrt(f * f + xd * xd), 1e-9)
    f0, f1, f2, f3 = rf.get("f", [0.75, 0.95, 1.2, 1.7])
    e0, e1 = rf.get("e", [0.25, 0.6])
    s0, s1 = rf.get("dir", [-0.1, 0.45])
    m0, m1 = rf.get("mid", [0.008, 0.03])
    sn = xw / np.maximum(f, 1e-9)
    W = smoother((f - f0) / (f1 - f0)) * smoother((f3 - f) / (f3 - f2)) * smoother((e1 - e) / (e1 - e0)) \
        * smoother((sn - s0) / (s1 - s0)) * smoother((np.abs(sl.V0[:, 0]) - m0) / (m1 - m0))
    return np.where(sl.V0[:, 0] >= 0, W, 0.0)


def root_delta(sl, c, P, Va):
    """P1 R1c round 3 (milestone judge 2: "two spheres stuck onto a flat chest": a crisp line over each breast top,
    the profile turning 35-40 deg concave within ~12 mm where the globe meets the chest): the upper ROOT made one body
    with the chest, on the globed body P, in the root band (root_band): "fill_m" a bell along the axis (the chest
    under the root and up toward the collarbone brought forward: the slope rolls into the pole), then "fair": a masked
    umbrella fairing (iters x lam x band; each step a point goes that share of the way to its neighbours' mean):
    the concave turn spread over 25-35 mm (curvature continuous from the chest into the globe), the globe's front
    untouched. Left side computed, both sides faired together, the move mirrored (exactly symmetric)."""
    rf = c["globe"]["root"]
    X = extra(sl)
    a = frame(c, 1.0)[0]
    W = root_band(sl, c, P, Va, rf)
    Wm = W.copy()
    mi = X["mirror"]
    R = sl.V0[:, 0] < -1e-4
    Wm[R] = W[mi[R]]
    P1 = P.copy()
    if rf.get("bridge"):
        # the BRIDGE: the band (weight > cut) refilled by the biharmonic (thin-plate) surface of the uniform graph
        # Laplacian with everything outside held (two rings: C1 at its edge; as wall_delta), blended in by the band's
        # own C2 weight raised to rf["bridge"]["pow"]: the least-bending surface from the globe's upper side to the
        # chest replaces the corner (the concave turn spread over the band, the chest under the root brought forward)
        import scipy.sparse as sp
        from scipy.sparse.linalg import splu
        bc = rf["bridge"]
        free = W > float(bc.get("cut", 0.02))
        key = ("bridge", sl.path, np.packbits(free).tobytes())
        if key not in _C:
            n = len(P)
            A = X["A"]
            dg = np.asarray(A.sum(1)).ravel()
            L = sp.identity(n, format="csr") - sp.diags(1.0 / dg) @ A
            M = (L.T @ L).tocsr()
            f, k = np.nonzero(free)[0], np.nonzero(~free)[0]
            _C[key] = (f, k, splu(M[f][:, f].tocsc()), M[f][:, k].tocsr())
        f, k, lu, Mfk = _C[key]
        Wb = P1.copy()
        Wb[f] = lu.solve(-(Mfk @ P1[k]))
        m = np.clip(W, 0.0, 1.0) ** float(bc.get("pow", 1.0))
        P1 = P1 + mirror_left(sl, (Wb - P1) * m[:, None])
    tl = rf.get("tail")
    if tl:
        # the AXILLARY TAIL (judge 2: the outer base dies in a pocket at the armpit): the upper outer quarter carried
        # toward the front armpit fold as a tapering ridge along the axis: h_m at the rim (footprint f = f[1]),
        # tapering (C2) to 0 at f[2] up the side (40-50 mm past the rim) and eased in from the globe (f[0]); across,
        # a C2 window round the in-plane direction psi_deg (lateral 0, up 90) of half-width half_deg; laid on the
        # bridged body (inside the band the bridge would erase it), itself a C2 bell
        u, w, d, Ru, Rw, Ra = globe_coords(sl, c, P, Va)[:6]
        xu, xw = u / Ru, w / Rw
        f = np.sqrt(xu * xu + xw * xw)
        psi = np.degrees(np.arctan2(xw, xu))
        g0, g1, g2 = tl["f"]
        hf = smoother((f - g0) / (g1 - g0)) * smoother((g2 - f) / (g2 - g1))
        ha = smoother(1.0 - np.abs(psi - float(tl["psi_deg"])) / float(tl["half_deg"]))
        e = (d / Ra) / np.maximum(np.sqrt(f * f + (d / Ra) ** 2), 1e-9)
        he = smoother((float(tl.get("e_max", 0.5)) - e) / float(tl.get("e_ease", 0.3)))
        Ht = float(tl["h_m"]) * hf * ha * he * (sl.V0[:, 0] >= 0)
        if tl.get("along") == "normal":
            # along the bridged body's own normals (umbrella-averaged 8 steps): the side wall rises off itself, no
            # sideways slide of the outer face
            Nn = vnormals(P1, X["Q"])
            A = X["A"]
            dg = np.asarray(A.sum(1)).ravel()
            for _ in range(8):
                Nn = 0.5 * Nn + 0.5 * (A @ Nn) / dg[:, None]
                Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
            P1 = P1 + mirror_left(sl, Ht[:, None] * Nn)
        else:
            P1 = P1 + mirror_left(sl, Ht[:, None] * a)
    if rf.get("fill_m"):
        # the fill: a bell over the band's outer half (f2..f3, the chest above the rim), along the axis (left;
        # mirrored below with the fairing's move)
        Pf = float(rf["fill_m"]) * root_band(sl, c, P, Va, dict(rf, **rf.get("fill_band", {})))[:, None] * a
        P1 = P1 + mirror_left(sl, Pf)
    fr = rf.get("fair")
    if fr:
        A = X["A"]
        deg = np.asarray(A.sum(1)).ravel()
        lam = float(fr.get("lam", 0.5)) * Wm
        for _ in range(int(fr.get("iters", 20))):
            P1 = P1 + lam[:, None] * ((A @ P1) / deg[:, None] - P1)
    return mirror_left(sl, P1 - P)


# ------------------------------------------------------------------------- P1 R1c round 4: the soft union --
def smin_c2(a, b, k):
    """The C2 smooth minimum (the cubic polynomial one): min(a, b) - k h^3 / 6, h = max(k - |a - b|, 0) / k, k per
    point. Exactly min(a, b) where |a - b| >= k (the globe's front and the chest away from it are untouched); the
    curvature is continuous through the blend and at its ends (the quadratic smin is only C1: its curvature jumps where
    the blend ends, which a cel terminator draws as a kink)."""
    k = np.maximum(np.asarray(k, float), 1e-9)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - k * h * h * h / 6.0


def periodic_c2(psi_deg, ctrl):
    """A periodic C2 function of a direction psi (deg): the periodic cubic spline through ctrl = [[psi_deg...],
    [value...]] (increasing psi, one turn)."""
    from scipy.interpolate import CubicSpline
    xs, ys = np.asarray(ctrl[0], float), np.asarray(ctrl[1], float)
    key = ("pc2", tuple(xs), tuple(ys))
    if key not in _C:
        _C[key] = CubicSpline(np.r_[xs, xs[0] + 360.0], np.r_[ys, ys[0]], bc_type="periodic")
    return _C[key]((np.asarray(psi_deg, float) - xs[0]) % 360.0 + xs[0])


def ell_sdf(u, w, d, Ru, Rw, Ra):
    """The signed distance (m, + outside) to the ellipsoid (u / Ru)^2 + (w / Rw)^2 + (d / Ra)^2 = 1 (Quilez's bound
    k0 (k0 - 1) / k1: exact for a sphere, first-order exact at the surface, smooth away from the centre)."""
    k0 = np.sqrt((u / Ru) ** 2 + (w / Rw) ** 2 + (d / Ra) ** 2)
    k1 = np.sqrt((u / Ru ** 2) ** 2 + (w / Rw ** 2) ** 2 + (d / Ra ** 2) ** 2)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-12)


def chest_field(sl, Vb, hm, key):
    """The chest's signed distance (m, + outside) as an implicit moving-least-squares surface of the base body Vb
    (the body under the globe; trunk, breast, shoulder and neck parts, the front half): d(x) = sum_i w_i (x - p_i) . n_i
    / sum_i w_i, w_i = exp(-|x - p_i|^2 / h^2) over the 16 nearest points (h ~ the quad size: C-inf, and on our
    smooth chest within ~0.2 mm of the mesh). Returns a function X -> d."""
    if key in _C:
        return _C[key]
    from scipy.spatial import cKDTree
    X = extra(sl)
    keep = [X["parts"].index(p) for p in ("trunk", "breast", "shoulder", "neck")]
    N = vnormals(Vb, X["Q"])
    sel = np.isin(X["part"], keep) & (Vb[:, 2] > -0.06) & (Vb[:, 1] > 1.05) & (Vb[:, 1] < 1.75) & (np.abs(Vb[:, 0]) < 0.3)
    Pp, Np = Vb[sel], N[sel]
    tree = cKDTree(Pp)

    def d(Xq):
        dist, idx = tree.query(Xq, k=16)
        wq = np.exp(-(dist * dist - dist[:, :1] ** 2) / (hm * hm))
        pd = np.einsum("ijk,ijk->ij", Xq[:, None, :] - Pp[idx], Np[idx])
        return (wq * pd).sum(1) / wq.sum(1)
    _C.clear() if len(_C) > 64 else None
    _C[key] = d
    return d


def union_field(sl, c, Va, chest, bias):
    """F(X, i) for the candidate points: the breast region as ONE implicit form (P1 R1c round 4, the lead: build the
    junction into the form). F = smin(chest - bias_i, smin(globe_L, globe_R, k_mid), tail; k(psi)): the chest field
    (chest_field, shifted per point by its own value at the point's base position, so a point the union does not
    reach stays exactly where it was), the left globe (globe_delta's ellipsoid: same centre, radii, yaw, pitch) and
    its mirror (the pressed midline, small k_mid), the axillary tail (an ellipsoid from the globe's upper outer quarter
    toward the front armpit fold, its own blend k_tail into the globe), all joined by smin_c2 with the chest blend
    radius k by the direction psi from the globe's centre (periodic C2: large over the upper pole so the collarbone's
    slope rolls into the pole, small at the fold, medium at the side)."""
    g = c["globe"]
    un = g["union"]
    a, up, lat = frame(c, 1.0)
    c0 = anchor(sl, c, Va)
    o = np.asarray(g.get("o_off", [0.0, 0.0, -0.05]), float)
    O = c0 + o[0] * lat + o[1] * up + o[2] * a
    R = g["R"]
    bw = c.get("r_blend_m", 0.03)
    tl = un.get("tail")
    if tl:
        tc = O + np.asarray(tl["c"], float) @ np.stack([lat, up, a])
        ax = np.asarray(tl["axis"], float) @ np.stack([lat, up, a])
        ax /= np.linalg.norm(ax)
        e2 = np.cross(a, ax)
        e2 /= np.linalg.norm(e2)
        e3 = np.cross(ax, e2)
        TR = np.asarray(tl["R"], float)
    pl = un.get("pole")
    if pl:
        # P1 R1c round 6: the upper pole's hull (see globe)
        Pq = np.asarray(pl["P"], float)
        Pn = Pq / np.array([float(smooth_r(Pq[0], R["med"], R["lat"], bw)), float(smooth_r(Pq[1], R["low"], R["up"], bw)), float(R["a"])])
        PL = float(np.linalg.norm(Pn))
        Pn = Pn / PL
        th_c, x0 = math.acos(1.0 / PL), math.radians(float(pl.get("x0_deg", 12.0)))
        tip, pl_s = math.radians(float(pl.get("tip_deg", 0.0))), np.array([float(pl.get("lat_s", 1.0)), 1.0, 1.0])

    def globe(Xq):
        q = Xq - O
        u, w, d = q @ lat, q @ up, q @ a
        d = d + shear_up(g, w, bw)
        Ru = smooth_r(u, R["med"], R["lat"], bw)
        Rw = smooth_r(w, R["low"], R["up"], bw)
        Ra = smooth_r(d, R.get("a_back", R["a"]), R["a"], bw)
        if pl:
            # The upper pole's thin mass (the Look's lit rim: the ellipsoid's top faces 87 deg up, a shelf no blend width
            # can turn): the HULL of the ellipsoid and a point P on the upper chest (pole.P from O, m; lateral, up, axis):
            # affine, so in the ellipsoid's unit coordinates it is the unit sphere's tangent cone from P: at an angle
            # theta from P's direction the radius is 1 / cos(theta_c - theta), cos theta_c = 1 / |P| (1 past the contact
            # circle). Tangent to the globe all round the contact circle (no seam, no shelf at its sides), the top rolls
            # off at the generator's elevation, and theta_c - theta goes through the C2 ramp (+-x0_deg) so the curvature
            # eases from the globe's to the generator's: a cel terminator draws no line there.
            nq = np.stack([u / Ru, w / Rw, d / Ra], 1)
            r0 = np.maximum(np.linalg.norm(nq, axis=1), 1e-9)
            # the hull's own unit coordinates: one radius along the axis (R.a), so the generators stay straight across
            # the ellipsoid's front / back switch (a_back at d < 0 would bend them over the top: a band still facing 80 deg)
            nf = np.stack([u / Ru, w / Rw, d / float(R["a"])], 1)
            rf = np.maximum(np.linalg.norm(nf, axis=1), 1e-9)
            nw = nf * pl_s                                 # a lateral squeeze: the cone's axis a soft ridge, not a point
            th = np.arccos(np.clip(nw @ Pn / np.maximum(np.linalg.norm(nw, axis=1), 1e-9), -1.0, 1.0))
            th = np.sqrt(th * th + tip * tip)              # the tip rounded (r flat at the axis, no point in the chest)
            xs = x0 * ramp((th_c - th) / x0)
            rp = 1.0 / np.cos(xs)
            mix = smoother((th_c - th + x0) / (2.0 * x0))  # the ellipsoid past the contact circle, the hull inside it
            k0 = (r0 ** (1.0 - mix)) * (rf ** mix) / rp
            k1 = np.sqrt((nq[:, 0] / Ru) ** 2 + (nq[:, 1] / Rw) ** 2 + (nq[:, 2] / Ra) ** 2) / rp
            return k0 * (k0 - 1.0) / np.maximum(k1, 1e-12), np.degrees(np.arctan2(w / Rw, u / Ru))
        return ell_sdf(u, w, d, Ru, Rw, Ra), np.degrees(np.arctan2(w / Rw, u / Ru))

    def F(Xq, bi):
        gl, psi = globe(Xq)
        Xm = Xq * np.array([-1.0, 1.0, 1.0])
        gr = globe(Xm)[0]
        gg = smin_c2(gl, gr, float(un.get("k_mid_m", 0.006)))
        if tl:
            q = Xq - tc
            dt = ell_sdf(q @ ax, q @ e2, q @ e3, TR[0], TR[1], TR[2])
            qm = Xm - tc
            dtm = ell_sdf(qm @ ax, qm @ e2, qm @ e3, TR[0], TR[1], TR[2])
            gg = smin_c2(gg, np.minimum(dt, dtm), float(tl.get("k_m", 0.03)))
        k = np.maximum(periodic_c2(psi, un["k"]), 1e-3)
        return smin_c2(chest(Xq) - bi, gg, k), psi
    return F, O


def union_delta(sl, c, P, Vb, Va):
    """P1 R1c round 4: the breast region's vertices (left side, on the globed body P) moved onto the union's iso-surface
    F = 0 (union_field) by a few Newton projection steps along grad F (central differences): each point goes the
    shortest way onto the one blended form, so the root's corner is filled by the union's own fillet (the radial globe
    slid the chest's points along rays that graze the upper chest, so no radial fillet could fill it). The move is
    weighted by w(psi) (periodic C2 on the point's direction from the globe's centre, through smoother: 0 keeps the
    radial globe, the pressed cleavage slot) and held at the midline; mirrored, so both sides are exactly symmetric."""
    un = c["globe"]["union"]
    X = extra(sl)
    hm = float(un.get("imls_h_m", 0.007))
    chest = chest_field(sl, Vb, hm, ("chest", sl.path, hm, float(np.round(Vb[::97].sum(), 9))))
    F, O = union_field(sl, c, Va, chest, None)
    keep = [X["parts"].index(p) for p in ("trunk", "breast", "shoulder")]
    q = P - O
    cand = np.isin(X["part"], keep) & (sl.V0[:, 0] >= 0) & (np.linalg.norm(q, axis=1) < float(un.get("reach_m", 0.22)))
    cand &= (q @ frame(c, 1.0)[0]) > -float(un.get("back_m", 0.06))
    idx = np.nonzero(cand)[0]
    x = P[idx].copy()
    bias = chest(Vb[idx])
    hstep = 2e-4
    E = np.eye(3) * hstep
    for _ in range(int(un.get("steps", 6))):
        f = F(x, bias)[0]
        gr = np.stack([(F(x + E[j], bias)[0] - F(x - E[j], bias)[0]) / (2 * hstep) for j in range(3)], 1)
        g2 = np.maximum((gr * gr).sum(1), 1e-6)
        st = -(f / g2)[:, None] * gr
        sn = np.linalg.norm(st, axis=1, keepdims=True)
        x = x + st * np.minimum(1.0, 0.02 / np.maximum(sn, 1e-12))
    psi = F(x, bias)[1]
    wv = smoother(periodic_c2(psi, un["w"])) if un.get("w") else np.ones(len(idx))
    m0, m1 = un.get("mid", [0.0, 0.0])
    if m1 > m0:
        wv = wv * smoother((np.abs(sl.V0[idx, 0]) - m0) / (m1 - m0))
    D = np.zeros_like(P)
    D[idx] = (x - P[idx]) * wv[:, None]
    return mirror_left(sl, D)


def dome(sl, c, v, V, values):
    if c.get("globe"):
        # P1 R1c: the profile dome (h_m > 0) is the globe's soft BASE (a mound on the chest wall: the wide base that
        # reaches up the chest and round the side), the globe is unioned onto it (the round mass; where the mound
        # rises toward the globe's rim the two meet at a shallow angle: a soft fillet, no ball-on-a-wall crease)
        D = dome_delta(sl, c, V) if c.get("h_m") else np.zeros_like(V)
        G = D + globe_delta(sl, c, V + D, V)
        if c["globe"].get("root"):
            G = G + root_delta(sl, c, V + G, V)
        if c["globe"].get("union"):
            base = V + D if c["globe"]["union"].get("chest", "base") == "base" else V
            G = G + union_delta(sl, c, V + G, base, V)
        return V + v * G
    return V + v * dome_delta(sl, c, V)