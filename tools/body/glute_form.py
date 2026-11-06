"""P1 R1 form library: her hourglass (waist, hips, the thighs' tops) and her glutes, OUR designed fields, evaluated in
numpy on every build, every body and both tiers (sliders.OurSliders rule "py:glute_form.<func>": f(sl, c, v, V, values)
-> the new V; the numbers live in tools/body/designed/glutes.json). They replace MakeHuman's measure targets (waist,
hips) and its buttock target plus our glute_lift (catalogue.json): those folded the cleft (178 deg at 1.0, 12-14 points
inside at rest), sat low, and stacked one target on another.

Landmark-anchored: each body's own hip joints (base/landmarks.json's MakeHuman joint cubes, the skeleton's own rule)
on the body the earlier sliders made, so an NPC with other proportions gets the same design on its own frame. C2
throughout (the cubic smooth max, quintic/Wendland windows and bumps): no mask edge or ledge for a cel terminator to
kink on. Linear in v (v = 1 the design, 0.5 a smaller version of it, 0 the body untouched).

hourglass: a horizontal scale per height (x about the midline, z about the trunk's centre line), its profile a sum of
C2 bumps on the height above the hip joints: the waist pinched above the navel, the hips out to their widest at the
joints' level, the thighs' outer tops eased in so the line runs clean from the hip into the thigh.

glutes: each cheek a designed solid (a superellipsoid per half-axis, tilted in the side plane, placed from the hip
joint), smooth-unioned with the body IN EACH SIDE (SAGITTAL) PLANE: a point moves only in y and z, radially from the
solid's axis (r -> smax(r, rho)). So no point ever crosses the midline or passes another (the move is monotone along
each ray and keeps x): the cleft cannot fold. The two cheeks' solids meet in a smooth max (kc): the cleft is a designed
soft valley, not MakeHuman's crease; the body's fillet (k) is the lumbar curve above and the soft gluteal fold below."""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_LM = {}
_PARTS = {}


def smoother(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


def smax(a, b, k):
    """Cubic polynomial smooth maximum (C2): max(a, b) where they differ by more than k, a round blend within it."""
    h = np.clip(1.0 - np.abs(a - b) / k, 0.0, None)
    return np.maximum(a, b) + h ** 3 * (k / 6.0)


def bump(u):
    """Wendland-like compact bump (1 - u^2)^3 on |u| < 1: C2, 1 at 0, 0 (with two derivatives) at |u| = 1."""
    u = np.clip(np.abs(u), 0.0, 1.0)
    return (1.0 - u * u) ** 3


def switch(lo, hi, t, eps):
    """lo for t < -eps, hi for t > eps, a quintic (C2) blend between."""
    return lo + (hi - lo) * smoother((t + eps) / (2.0 * eps))


def window(x, a, b, f_lo, f_hi):
    """1 on [a, b], easing (quintic, C2) to 0 at a - f_lo and b + f_hi; a or b None: open."""
    m = np.ones_like(x)
    if a is not None:
        m = m * smoother((x - (a - f_lo)) / f_lo)
    if b is not None:
        m = m * smoother(((b + f_hi) - x) / f_hi)
    return m


def landmark(sl, V, name):
    tier = sl.topo()["tier"]
    if tier not in _LM:
        with open(os.path.join(HERE, "base", "landmarks.json")) as f:
            _LM[tier] = json.load(f)["tiers"][tier]
    e = _LM[tier][json.dumps({"cube": name}, separators=(",", ":"))]
    return (V[np.asarray(e["ids"])] * np.asarray(e["w"], float)[:, None]).sum(0)


def hip_frame(sl, V):
    """The hip joints' frame on this body: [x (each joint's |x|, mean of the two), y, z] (glTF m)."""
    l, r = landmark(sl, V, "joint-l-upper-leg"), landmark(sl, V, "joint-r-upper-leg")
    return np.array([0.5 * (l[0] - r[0]), 0.5 * (l[1] + r[1]), 0.5 * (l[2] + r[2])])


def parts_mask(sl, names):
    tier = sl.topo()["tier"]
    key = (tier, tuple(names))
    if key not in _PARTS:
        z = np.load(os.path.join(HERE, "out", "topo", f"{tier}.npz"))
        P = [str(p) for p in z["parts"]]
        _PARTS[key] = np.isin(z["part"], [P.index(n) for n in names]).astype(float)
    return _PARTS[key]


def half_widths(V, T, ys):
    """The body's half-width (max |x|) at each height: the exact plane sections of triangles T (no vertex noise)."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    lo = np.minimum(np.minimum(a[:, 1], b[:, 1]), c[:, 1])
    hi = np.maximum(np.maximum(a[:, 1], b[:, 1]), c[:, 1])
    out = np.full(len(ys), np.nan)
    for i, y in enumerate(ys):
        m = (lo < y) & (hi > y)
        best = 0.0
        for p, q in ((a[m], b[m]), (b[m], c[m]), (c[m], a[m])):
            dp, dq = p[:, 1] - y, q[:, 1] - y
            k = (dp * dq) < 0
            if k.any():
                t = dp[k] / (dp[k] - dq[k])
                best = max(best, float(np.abs(p[k, 0] + t * (q[k, 0] - p[k, 0])).max()))
        out[i] = best
    return out


def hourglass_delta(sl, c, V):
    from scipy.interpolate import CubicSpline
    H = hip_frame(sl, V)
    h = V[:, 1] - H[1]
    parts = c.get("parts", ["trunk", "crotch", "thigh"])
    on = parts_mask(sl, parts)
    sx = np.zeros(len(V))
    L = c.get("line")
    if L:
        # the designed outer line (front view): target half-widths (units of the hip joints' |x|) at heights over
        # the joints, a natural cubic spline (C2); the x scale per height is target / the body's own (its exact
        # sections, lightly smoothed), eased (quintic) to 0 outside the line's span
        unit = H[0] if L.get("unit", "hip_x") == "hip_x" else 1.0
        f = L["fade"]
        hg = np.arange(L["full"][0] - f[0] - 0.01, L["full"][1] + f[1] + 0.01, 0.004)
        Q = sl.topo()["Q"]
        qm = on[Q].min(1) > 0
        T = np.concatenate([Q[qm][:, [0, 1, 2]], Q[qm][:, [0, 2, 3]]])
        wb = half_widths(V, T, H[1] + hg)
        k = np.exp(-0.5 * (np.arange(-6, 7) * 0.004 / float(L.get("smooth_m", 0.008))) ** 2)
        wb = np.convolve(np.pad(wb, 6, mode="edge"), k / k.sum(), "valid")
        wt = CubicSpline(np.asarray(L["h"], float)[::-1], np.asarray(L["w"], float)[::-1] * unit, bc_type="natural")(hg)
        g = (wt / wb - 1.0) * window(hg, L["full"][0], L["full"][1], f[0], f[1])
        sx = CubicSpline(hg, g, bc_type="natural")(np.clip(h, hg[0], hg[-1]))
        sx = sx * window(h, L["full"][0], L["full"][1], f[0], f[1])
    sz = np.zeros(len(V))
    for b in c.get("bands", []):
        w = b["w"] if isinstance(b["w"], (list, tuple)) else [b["w"], b["w"]]
        d = h - b["h"]
        g = bump(np.where(d < 0, d / w[0], d / w[1]))
        sx += float(b.get("sx", 0.0)) * g
        sz += float(b.get("sz", 0.0)) * g
    zc = H[2] + float(c.get("zc", 0.0))
    D = np.zeros_like(V)
    D[:, 0] = V[:, 0] * sx
    D[:, 2] = (V[:, 2] - zc) * sz
    return D * on[:, None]


def hourglass(sl, c, v, V, values):
    """The waist-hip-thigh line: x scaled about the midline per height so the body's outer line (front view) meets
    the designed one ("line": half-widths in units of the hip joints' |x| at heights h over the joints, a C2 spline;
    eased out past its span), and z scaled about the trunk's centre line (zc over the joints' z) by C2 bumps
    ("bands": h, w (or [below, above]), sz; sx adds to the line's scale). Trunk, crotch and thighs only (the
    hanging hands and the arms keep)."""
    return V + v * hourglass_delta(sl, c, V)


def bump_on(q, b):
    """A C2 profile on one coordinate: {"full": [a, b], "fade": [f_lo, f_hi]} 1 on [a, b] easing (quintic) to 0 at
    a - f_lo and b + f_hi; or {"c": c, "w": [below, above]} an asymmetric Wendland bump, 1 at c and 0 past c - w[0]
    and c + w[1], with "mid" (on |x|): the value held toward the midline (mid + (1 - mid) * bump below c, flat at 0
    so the midline stays smooth)."""
    if "tent" in b:                                         # (1 - q/w)^3 on q >= 0 (|x|): a kink AT the midline
        return (1.0 - np.clip(q / float(b["tent"]), 0.0, 1.0)) ** 3   # by design (it rounds the cleft's V), C2 at w
    if "full" in b:
        f = b["fade"] if isinstance(b["fade"], (list, tuple)) else [b["fade"], b["fade"]]
        return window(q, b["full"][0], b["full"][1], float(f[0]), float(f[1]))
    w = b["w"] if isinstance(b["w"], (list, tuple)) else [b["w"], b["w"]]
    d = q - float(b["c"])
    g = bump(np.where(d < 0, d / float(w[0]), d / float(w[1])))
    if "mid" in b:
        g = np.where(d < 0, float(b["mid"]) + (1.0 - float(b["mid"])) * g, g)
    return g


def smile_y(qy, ax, b, sm):
    """The y profile of a move whose LOWER side follows a smile (back view): from |x| sm["x"][0] to sm["x"][1] (a
    quintic, C2 ramp s) the lower foot rises by sm["dy"] * s and its fade lengthens upward by (1 + (fade_k - 1) * s) (a
    "c" bump: its centre rises, its lower width lengthens), so the
    under-curve lifts toward the outer hip and its fold eases out there (fade_k > 1: the fold flattens); the upper
    side is untouched. b: {"full": [a, b], "fade": [lo, hi]} or {"c": c, "w": [below, above]} as bump_on."""
    s = smoother((ax - float(sm["x"][0])) / (float(sm["x"][1]) - float(sm["x"][0])))
    k = 1.0 + (float(sm.get("fade_k", 1.0)) - 1.0) * s
    lift = float(sm["dy"]) * s
    if "full" in b:
        f = b["fade"] if isinstance(b["fade"], (list, tuple)) else [b["fade"], b["fade"]]
        a, hi = b["full"]
        lo = None if a is None else float(a) + lift
        m = np.ones_like(qy)
        if lo is not None:
            m = m * smoother((qy - (lo - float(f[0]))) / (float(f[0]) * k))   # its foot lifts, its fade grows up
        if hi is not None:
            m = m * smoother(((float(hi) + float(f[1])) - qy) / float(f[1]))
        return m
    w = b["w"] if isinstance(b["w"], (list, tuple)) else [b["w"], b["w"]]
    d = qy - (float(b["c"]) + lift)
    return bump(np.where(d < 0, d / (float(w[0]) * k), d / float(w[1])))


def glute_delta(sl, c, V):
    """The cheeks' move at v = 1 (see glutes): a sum of moves in each side plane (dx = 0)."""
    H = hip_frame(sl, V)
    ax = np.abs(V[:, 0])
    q = {"ax": ax - H[0], "axa": ax, "y": V[:, 1] - H[1], "z": V[:, 2] - H[2]}
    A = np.array([H[1] + float(c["axis"][0]), H[2] + float(c["axis"][1])])
    dy, dz = V[:, 1] - A[0], V[:, 2] - A[1]
    r = np.maximum(np.hypot(dy, dz), 1e-9)
    D = np.zeros_like(V)
    for mv in c["moves"]:
        g = np.ones(len(V))
        for on in ("ax", "axa", "y", "z"):
            if on in mv:
                if on == "y" and "smile" in mv:
                    g = g * smile_y(q["y"], ax, mv["y"], mv["smile"])
                else:
                    g = g * bump_on(q[on], mv[on])
        d = mv["dir"]
        if d == "radial":                                   # away from the solid's axis in the side plane
            vy, vz = dy / r, dz / r
        else:                                               # [dy, dz] (normalised)
            n = np.hypot(d[0], d[1])
            vy, vz = d[0] / n, d[1] / n
        D[:, 1] += float(mv["m"]) * g * vy
        D[:, 2] += float(mv["m"]) * g * vz
    return D * parts_mask(sl, c.get("parts", ["trunk", "crotch", "thigh"]))[:, None]


def relax_region(sl, V, mask, iters, step):
    """Tangential Laplacian evening of the quads (the normal part of each step taken off: the surface keeps its
    shape, the points slide) weighted by a 0..1 mask; as sliders.relax, for a py rule's own region."""
    import scipy.sparse as sp
    t = sl.topo()
    Q = t["Q"]
    n = len(V)
    e = np.unique(np.sort(np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]]), 1), axis=0)
    A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    w = mask * step
    w[t["ring"]] = 0.0
    act = w > 1e-4
    V = V.copy()
    for _ in range(int(iters)):
        fn = np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]])
        N = np.zeros_like(V)
        for k in range(4):
            np.add.at(N, Q[:, k], fn)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        L = (A @ V) / deg[:, None] - V
        L -= (L * N).sum(1, keepdims=True) * N
        V[act] += w[act, None] * L[act]
    return V


def _graph(sl):
    import scipy.sparse as sp
    t = sl.topo()
    if "_A" not in t:
        Q = t["Q"]
        n = len(sl.V0)
        e = np.unique(np.sort(np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]]), 1), axis=0)
        A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
        t["_A"], t["_deg"] = A, np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    return t["_A"], t["_deg"]


def region(sl, c_terms, V, H):
    """A C2 region weight from bump_on terms on ax (|x| over the joints' |x|), axa (|x|), y and z (over the joints)."""
    q = {"ax": np.abs(V[:, 0]) - H[0], "axa": np.abs(V[:, 0]), "y": V[:, 1] - H[1], "z": V[:, 2] - H[2]}
    g = np.ones(len(V))
    for on, b in c_terms.items():
        g = g * bump_on(q[on], b)
    return g


def fair(sl, V, w, iters, lam=0.5, mu=-0.53, lock_x=False):
    """Taubin (lambda | mu) fairing weighted by w (0..1): the small lumps of the base go (a cel terminator kinks
    on them), the big forms stay (no shrink); the open neck ring is pinned. lock_x: in the side planes only (a long
    fairing otherwise draws the cleft's walls across the midline)."""
    A, deg = _graph(sl)
    w = w.copy()
    w[sl.topo()["ring"]] = 0.0
    act = w > 1e-4
    V = V.copy()
    for _ in range(int(iters)):
        for k in (lam, mu):
            L = (A @ V) / deg[:, None] - V
            if lock_x:
                L[:, 0] = 0.0
            V[act] += (k * w[act])[:, None] * L[act]
    return V


def glutes(sl, c, v, V, values):
    """The cheeks' designed mass: "moves", each a magnitude m (metres at v = 1) along a side-plane direction ("radial"
    from the axis point "axis" [dy, dz] over the hip joints, or a fixed [dy, dz]) under a product of C2 profiles on
    ax (|x| over the joints' |x|), y and z (over the joints): bump_on. No x move: nothing crosses the midline.
    "even": the moved region's quads evened after the move (tangential; not sliders.relax, which is post-join only)."""
    D = glute_delta(sl, c, V)
    ms = c.get("move_smooth")
    if ms:
        # P1 R1c (milestone judge: vertical ripples on the cheeks from behind, the cleft reading only in its lower
        # third): the move itself low-passed over the mesh graph (Jacobi steps of the umbrella average, the move's
        # own field, not the surface): the 44 mm push carried vertex-scale content (the cheeks' quad columns shaded as
        # vertical streaks: 0.4-0.9 mm high-pass relief vs 0.1 on the base) and its narrow cleft fill flattened the
        # cleft's V; the smoothed move keeps the masses (wavelengths over ~5 edges) and lets the base's own V through
        # (D has no x part, so nothing crosses the midline; the parts mask is laid again after)
        A, deg = _graph(sl)
        a = float(ms.get("step", 0.5))
        for _ in range(int(ms.get("iters", 30))):
            D = (1.0 - a) * D + a * (A @ D) / deg[:, None]
        D = D * parts_mask(sl, c.get("parts", ["trunk", "crotch", "thigh"]))[:, None]
    out = V + v * D
    fa = c.get("fair")
    if fa:
        H = hip_frame(sl, V)
        w = region(sl, fa["mask"], V, H) * parts_mask(sl, c.get("parts", ["trunk", "crotch", "thigh"]))
        out = fair(sl, out, w * min(1.0, v), fa.get("iters", 10), fa.get("lambda", 0.5), fa.get("mu", -0.53))
    rx = c.get("even")
    if rx:
        m = np.clip(np.linalg.norm(D, axis=1) / float(rx.get("full_m", 0.01)), 0.0, 1.0)
        m = smoother(m) * parts_mask(sl, c.get("parts", ["trunk", "crotch", "thigh"]))
        out = relax_region(sl, out, m, rx.get("iters", 10), rx.get("step", 0.5) * min(1.0, v))
    return out
