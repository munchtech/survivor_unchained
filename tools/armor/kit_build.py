"""The kit's free meshes (lane D, 16 Nov 2026): a piece authored at the SHIPPED body's rest (body A, heroine.glb).

    python tools/armor/kit_build.py kit_bodice          -> godot/art/armor/src/kit_bodice/{kit_bodice.glb, piece.json}
    python tools/turn.py run blender "armor-D: kit_bodice" -- python tools/armor/piece_ship.py kit_bodice

A piece is data (godot/art/armor/src/<id>/build.json: its recipe and every measure) + a recipe here. The output is the
free-mesh contract (docs/armor/PIECE_SCHEMA.md): glTF axes, metres, unskinned, identity transforms; `*_rigid` objects
ride one blend; material names from godot/art/people/outfit_materials.json.

Charts (each one a ray field from inside her, so a plate follows HER surface, smoothed and lifted):
    her_a()        heroine.glb's body at rest as a native_build.Ref (the builder's primitives run on body A)
    Polar          a cup: rays from a point inside a mound, (phi off its apex, psi round it); outline = a signed
                   field g(hit point) > 0, cut on every spoke (exact boundary, corners kept)
    Wrap           a band round her torso: horizontal rays from a vertical axis, (y, theta); top(theta), bot(theta)
    slab           a plate from a grid of inner points + outward directions: inner, outer, an edge wall
    bead           a rolled gold rim: a half-ellipse tube swept along an edge (its own geometry: reads at play camera)
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "assets"))
from native_build import Part, Ref, U, buckle, grid_tris, rand01, raycast, vertex_normals  # noqa: E402

BODY = os.path.join(REPO, "godot", "art", "people", "heroine.glb")
SRC = os.path.join(REPO, "godot", "art", "armor", "src")
MATS = os.path.join(REPO, "godot", "art", "people", "outfit_materials.json")


def her_a(path=BODY):
    """Body A (the shipped heroine.glb) at rest: Ref over its welded skin, joints from its inverse binds."""
    import body_follow_post as bf
    B = bf.Body(path)
    joints = {}
    for n, m in zip(B.names, B.ibm):
        M = np.linalg.inv(m.reshape(4, 4).T)
        joints[n] = M[:3, 3]
    r = Ref(B.U, B.F, B.N, joints, list(B.names), None, None)
    r.B = B
    c = B.U[B.F].mean(1)
    r.torso = B.F[(c[:, 1] > 0.85) & (c[:, 1] < 1.75) & (np.abs(c[:, 0]) < 0.30)]
    return r


CACHE = os.path.join(REPO, "godot", ".shots", "demo_armor", "kit_cache")


def cast(ref, O, D, tmax=0.5):
    """First hits on her torso; cached by the rays (git-ignored .shots), so a re-tune of an outline is quick."""
    import hashlib
    O, D = np.asarray(O, float), U(D)
    key = hashlib.sha1(O.round(7).tobytes() + D.round(7).tobytes() + str(tmax).encode() + ref.V[:50].tobytes()).hexdigest()
    f = os.path.join(CACHE, key + ".npz")
    if os.path.exists(f):
        z = np.load(f)
        return z["t"], z["i"]
    t, i = raycast(ref.V, ref.torso, O, D, tmax, chunk=64)
    os.makedirs(CACHE, exist_ok=True)
    np.savez(f, t=t, i=i)
    return t, i


def gsmooth(A, sig, wrap_c):
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(A, sig, mode=("nearest", "wrap" if wrap_c else "nearest"))


def fill_rows(A):
    """nan filled along each column from its nearest finite row."""
    A = A.copy()
    for j in range(A.shape[1]):
        c = A[:, j]
        ok = np.isfinite(c)
        if ok.any() and not ok.all():
            idx = np.arange(len(c))
            A[~ok, j] = np.interp(idx[~ok], idx[ok], c[ok])
    return A


# ---------------------------------------------------------------- geometry

def slab(name, mat, Pin, Nout, thick, closed_c=False, fan=None, extra=None, col_w=1.0):
    """A plate from inner points (R, C, 3) and outward unit directions: inner face, outer face (thick + extra), edge
    wall. closed_c: the columns wrap (a band: walls on its first and last rows); fan: row 0 is a small ring
    closed by a strip (a cup: wall on its last row only)."""
    R, C = Pin.shape[:2]
    ex = np.zeros((R, C)) if extra is None else extra
    Pout = Pin + Nout * (thick + ex)[..., None]
    rn = rand01(name)
    parts = []
    for P, sgn in ((Pout, 1), (Pin, -1)):
        V = P.reshape(-1, 3)
        T = grid_tris(R, C, close=closed_c)
        D = Nout.reshape(-1, 3) * sgn
        if fan:  # row 0 is a small ring: closed by a zig-zag strip (no fan: every point keeps a low valence)
            T = np.vstack([T, strip_cap(C)])
        T = orient(V, T, D)
        parts.append(Part(name, mat, V, T, uv0=np.c_[V[:, 0] + V[:, 2], V[:, 1]] * 3.0,
                          col=np.tile([1.0, rn, 0.0, col_w], (len(V), 1))))
    loops = [R - 1] if fan is not None or not closed_c else [0, R - 1]
    if not closed_c and fan is None:
        loops = ["perim"]
    for lp in loops:
        if lp == "perim":
            ij = [(0, j) for j in range(C)] + [(i, C - 1) for i in range(1, R)] + \
                 [(R - 1, j) for j in range(C - 2, -1, -1)] + [(i, 0) for i in range(R - 2, 0, -1)]
            ii, jj = np.array(ij).T
            inner_i = np.clip(ii + np.where(ii == 0, 1, np.where(ii == R - 1, -1, 0)), 0, R - 1)
            inner_j = np.clip(jj + np.where(jj == 0, 1, np.where(jj == C - 1, -1, 0)), 0, C - 1)
        else:
            ii, jj = np.full(C, lp), np.arange(C)
            inner_i, inner_j = np.full(C, lp - 1 if lp else 1), jj
        a, b = Pin[ii, jj], Pout[ii, jj]
        out = U(a - Pin[inner_i, inner_j])
        n = len(a)
        V = np.vstack([a, b])
        T = grid_tris(2, n, close=True)
        T = orient(V, T, np.vstack([out, out]))
        parts.append(Part(name, mat, V, T, uv0=np.c_[V[:, 0] + V[:, 2], V[:, 1]] * 3.0,
                          col=np.tile([1.0, rn, 0.0, 0.0], (len(V), 1))))
    return Part.join(name, mat, parts)


def strip_cap(C):
    """A ring 0..C-1 closed by a zig-zag strip between its two halves."""
    lo, hi, T, k = 0, C - 1, [], 0
    while hi - lo > 1:
        if k % 2 == 0:
            T.append([lo, lo + 1, hi])
            lo += 1
        else:
            T.append([lo, hi - 1, hi])
            hi -= 1
        k += 1
    return np.array(T)


def orient(V, T, D):
    """Each face wound to look along D (per vertex)."""
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    flip = (fn * D[T].mean(1)).sum(1) < 0
    T = T.copy()
    T[flip] = T[flip][:, ::-1]
    return T


def resample(P, step, closed):
    P = np.asarray(P, float)
    Q = np.vstack([P, P[:1]]) if closed else P
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    n = max(int(round(d[-1] / step)), 3)
    s = np.linspace(0, d[-1], n + (0 if closed else 1), endpoint=not closed)
    return np.stack([np.interp(s, d, Q[:, k]) for k in range(3)], 1)


def relax(P, it, closed, keep_ends=True):
    P = P.copy()
    for _ in range(it):
        if closed:
            P = 0.5 * P + 0.25 * (np.roll(P, 1, 0) + np.roll(P, -1, 0))
        else:
            P[1:-1] = 0.5 * P[1:-1] + 0.25 * (P[:-2] + P[2:])
    return P


def bead(ref, name, mat, E, rim, off, closed, relax_it=2, corners=None):
    """A rolled rim: a half-ellipse tube (rim w wide, h proud) swept along E, centred `off` out along her normal."""
    E = resample(E, rim["step"], closed)
    E = relax(E, relax_it, closed)
    q, n, _ = ref.closest(E)
    n = U(relax(n, 3, closed))
    t = U(np.gradient(np.vstack([E[-1:], E, E[:1]]) if closed else E, axis=0))
    t = t[1:-1] if closed else t
    b = U(np.cross(n, t))
    n = U(np.cross(t, b))
    k = rim["sides"]
    a = np.linspace(0, 2 * np.pi, k, endpoint=False)
    hx = np.cos(a) * rim["w"] / 2
    hy = np.sin(a) * np.where(np.sin(a) > 0, rim["h"], rim.get("below", 0.0011))
    C = E + n * off
    P = C[:, None, :] + hx[None, :, None] * b[:, None, :] + hy[None, :, None] * n[:, None, :]
    m = len(E)
    if closed:
        P = np.vstack([P, P[:1]])
        m += 1
    V = P.reshape(-1, 3)
    T = grid_tris(m, k, close=True)
    D = (P - C[np.r_[np.arange(len(E)), [0]] if closed else np.arange(m)][:, None, :]).reshape(-1, 3)
    if not closed:
        caps = []
        for r, c in ((0, C[0]), (m - 1, C[-1])):
            j = len(V) + len(caps)
            caps.append(c)
            T = np.vstack([T, np.c_[np.full(k, j), r * k + np.arange(k), r * k + (np.arange(k) + 1) % k]])
        V = np.vstack([V, caps])
        D = np.vstack([D, -t[0], t[-1]])
    T = orient(V, T, D)
    rn = rand01(name)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V[:m * k:k], axis=0), axis=1))] if m > 1 else np.zeros(1)
    uv = np.zeros((len(V), 2))
    uv[:m * k, 0] = np.repeat(s, k) * 4.0
    uv[:m * k, 1] = np.tile(a / (2 * np.pi), m)
    return Part(name, mat, V, T, uv0=uv, uv1=np.tile([0.0, 0.8], (len(V), 1)),
                col=np.tile([1.0, rn, 0.0, 0.0], (len(V), 1)))


def diamond(c, n, up, w, h, depth, name, mat):
    """A faceted diamond clasp: a flat rhombus base, a raised table, on a point and its normal."""
    n, up = U(n), U(up - U(n) * (U(n) @ up))
    x = np.cross(up, n)
    rim = [c + up * h, c + x * w, c - up * h, c - x * w]
    mid = [c + n * depth * 0.55 + up * h * 0.55, c + n * depth * 0.55 + x * w * 0.55,
           c + n * depth * 0.55 - up * h * 0.55, c + n * depth * 0.55 - x * w * 0.55]
    top = c + n * depth
    back = c - n * 0.0005
    V = np.vstack([rim, mid, [top, back]])
    T = []
    for k in range(4):
        a, b = k, (k + 1) % 4
        T += [[a, b, 4 + b], [a, 4 + b, 4 + a], [4 + a, 4 + b, 8], [a, 9, b]]
    T = np.array(T)
    T = orient(V, T, U(V - (c - n * 0.004)))
    return Part(name, mat, V, T, uv0=(V - c) @ np.c_[x, up] * 2.5, uv1=np.tile([0.0, 0.9], (len(V), 1)),
                col=np.tile([0.95, rand01(name), 0.0, 0.0], (len(V), 1)))


# ---------------------------------------------------------------- charts

class Wrap:
    """Horizontal rays from the vertical axis x = 0, z = z0: rho(y, theta) of her skin; theta 0 front, +90 her left."""

    def __init__(self, ref, z0, y0, y1, dy=0.004, dth=2.0):
        self.z0 = z0
        self.ys = np.arange(y0, y1 + dy / 2, dy)
        self.ths = np.arange(-180.0, 180.0, dth)
        Y, TH = np.meshgrid(self.ys, self.ths, indexing="ij")
        O = np.c_[np.zeros(Y.size), Y.ravel(), np.full(Y.size, z0)]
        t, _ = cast(ref, O, self.dirs(TH.ravel()), 0.45)
        self.rho = t.reshape(Y.shape)

    def dirs(self, th):
        r = np.radians(th)
        return np.stack([np.sin(r), np.zeros_like(r), np.cos(r)], -1)

    def field(self, rho):
        from scipy.interpolate import RegularGridInterpolator
        th = np.r_[self.ths, 180.0]
        A = np.c_[rho, rho[:, :1]]
        f = RegularGridInterpolator((self.ys, th), A, bounds_error=False, fill_value=None)
        return lambda y, t: f(np.stack(np.broadcast_arrays(y, (np.asarray(t) + 180.0) % 360.0 - 180.0), -1))

    def pt(self, y, th, rho):
        y, th, rho = np.broadcast_arrays(np.asarray(y, float), np.asarray(th, float), np.asarray(rho, float))
        return np.stack([np.zeros_like(y), y, np.full(y.shape, self.z0)], -1) + rho[..., None] * self.dirs(th)


class Polar:
    """Rays from a point inside a mound: phi off its apex direction, psi round it (0 up, 90 her outer side)."""

    def __init__(self, ref, c, apex, hand, phis, psis):
        self.c, self.hand = np.asarray(c, float), hand
        self.a = U(np.asarray(apex, float) - self.c)
        e1 = U(np.array([0, 1.0, 0]) - self.a * self.a[1])
        e2 = np.cross(self.a, e1)
        self.e1, self.e2 = e1, (e2 if e2[0] * hand > 0 else -e2)
        self.phis, self.psis = phis, psis
        PH, PS = np.meshgrid(phis, psis, indexing="ij")
        t, _ = cast(ref, np.tile(self.c, (PH.size, 1)), self.dirs(PH.ravel(), PS.ravel()), 0.3)
        self.r = t.reshape(PH.shape)

    def dirs(self, phi, psi):
        p, s = np.radians(phi)[..., None], np.radians(psi)[..., None]
        return np.cos(p) * self.a + np.sin(p) * (np.cos(s) * self.e1 + np.sin(s) * self.e2)


# ---------------------------------------------------------------- the bodice

def bodice(cfg, ref):
    M, rim, cl, th_ = cfg["mat"], cfg["rim"], cfg["clear"], cfg["thick"]
    cu, co = cfg["cup"], cfg["corset"]
    z0 = cfg["axis_z"]
    wrap = Wrap(ref, z0, 0.95, 1.52)
    rho_skin = wrap.rho
    skin_f = wrap.field(fill_rows(rho_skin))
    ts = cu["theta_side"]
    tj = ts + co["step_th"]  # the side panel's top is at the cup's outer corner from here on (one outline)
    bc, by = co["back_corner"]
    sk = co["scoop"]
    plate, trim, straps, rigid = [], [], [], []
    from scipy.interpolate import PchipInterpolator

    def ub(xs):
        return cu["ub"] + (cu["clasp"][1] - cu["ub"]) * np.clip(1 - xs / 0.05, 0, 1)

    # ---- corset outline in (y, theta), theta in [0, 180] mirrored. Front (under the cups): the underbust; past
    # the cup's outer side a step up to its outer corner (cu.arm), then the side panel under her arm (co.side),
    # flat under the shoulder strap's back end, then a square scoop down to the back's floor.
    P_ = np.array([[tj, cu["arm"][1]]] + co["side"] + [[bc - sk["edge"], by], [bc + sk["edge"], by],
                                                       [bc + sk["edge"] + sk["drop"], sk["floor"]], [180.0, sk["mid"]]])
    side_f = PchipInterpolator(P_[:, 0], P_[:, 1])

    def top(th):
        a = np.abs(th)
        x = skin_f(np.full(np.shape(a), cu["ub"]), a) * np.sin(np.radians(a))
        return np.where(a <= ts + 1e-6, ub(x), side_f(np.clip(a, tj, 180.0)))

    def bot(th):
        a = np.abs(th)
        v = co["point"] + (co["hip"] - co["point"]) * np.clip(a / co["v_theta"], 0, 1)
        return np.where(a > co["v_theta"], co["hip"] + (co["back_bot"] - co["hip"]) *
                        smooth01((a - co["v_theta"]) / (180 - co["v_theta"])), v)

    # ---- corset: rows between bot and top; columns round her: dense over the front panel (the ridge) and the
    # scoop's sides (a square corner), exact at the cup's outer side (ts) and the step's top (tj)
    exact = np.array([ts, tj, -ts, -tj])
    dense = [np.arange(-co["front_w"], co["front_w"] + 1e-6, co["front_step"])]
    for h in (1, -1):
        dense.append(h * np.arange(bc - sk["edge"] - 2.0, bc + sk["edge"] + sk["drop"] + 4.0 + 1e-6, co["scoop_step"]))
    dense = np.concatenate(dense)
    dense = dense[np.min(np.abs(dense[:, None] - exact[None, :]), 1) > 0.3]
    base = np.arange(-180.0, 180.0, co["col_step"])
    near = np.abs((base[:, None] - np.r_[dense, exact][None, :] + 180.0) % 360.0 - 180.0).min(1)
    TH = np.unique(np.round(np.r_[dense, exact, base[near > 0.6 * co["col_step"]]], 4))
    Cn = len(TH)
    tt, bb = top(TH), bot(TH)
    w = np.linspace(0, 1, co["rows"])
    w = 0.5 - 0.5 * np.cos(np.pi * w) * 0.35 + (w - 0.5) * 0.65  # a little denser at both edges
    w = (w - w[0]) / (w[-1] - w[0])
    # chevrons: shingled lames on the front panel; each line is two close rows (a crisp step, its upper lame proud)
    ch = co["chevron"]
    b0, t0 = float(np.ravel(bot(0.0))[0]), float(np.ravel(top(np.zeros(1)))[0])
    wk = (np.array(ch["y"]) - b0) / (t0 - b0)
    dw = ch["gap"] / (t0 - b0)
    w = np.unique(np.r_[w[np.min(np.abs(w[:, None] - wk[None, :]), 1) > 0.02], wk - dw / 2, wk + dw / 2])
    Y = bb[None, :] + (tt - bb)[None, :] * w[:, None]
    # her rho there, smoothed over the band only (what lies above its top never pulls it)
    rs = rho_skin.copy()
    above = wrap.ys[:, None] > top(wrap.ths)[None, :] + 0.004
    rs[above] = np.nan
    rs = fill_rows(rs)
    sm = gsmooth(rs, (2.0, 1.2), True)
    shell = np.maximum(sm + cl, fill_rows(rho_skin) + cl * 0)  # never under her skin
    shell = np.maximum(shell, fill_rows(rs) + cfg["clear_min"])
    shell_f = wrap.field(shell)
    TT = np.broadcast_to(TH[None, :], Y.shape)
    rl = co["relief"]

    def rho_at(Yq, Aq):
        """The plate's inner face; its bottom edge relieved: the last few cm stand a little further off her (room
        for her hip and belly in a stride)."""
        a = (np.asarray(Aq, float) + 180.0) % 360.0 - 180.0
        lift = rl["mm"] * (1 - smooth01((np.asarray(Yq, float) - bot(a)) / rl["h"])) * np.interp(np.abs(a), rl["th"], rl["k"])
        return shell_f(Yq, a) + lift

    rho_in = rho_at(Y, TT)
    Pin = wrap.pt(Y, TT, rho_in)
    Nout = wrap.dirs(TT)
    sa0, sy0 = co["seams"][0][0]
    sa1, sy1 = co["seams"][0][1]

    def ex_fn(Yq, Aq, rho):
        """The plate's outer relief: the centre keel (a sharp roof) and the chevron lames between the panel's seams."""
        a = (np.asarray(Aq, float) + 180.0) % 360.0 - 180.0
        Yq = np.asarray(Yq, float)
        bq, tq = bot(a), top(a)
        rg = co["ridge"]
        ridge = rg["h"] * np.clip(1 - np.abs(np.radians(a)) * rho / (rg["w"] / 2), 0, 1) ** rg["p"]
        ridge = ridge * smooth01((Yq - bq) / rg["fade_bot"]) * smooth01((tq - Yq) / rg["fade_top"])
        wv = (Yq - bq) / np.maximum(tq - bq, 1e-6)
        edges = np.r_[0.0, wk, 1.0]
        k = np.clip(np.searchsorted(edges, wv, side="right") - 1, 0, len(edges) - 2)
        lo, hi = edges[k], edges[k + 1]
        chev = ch["h"] * np.clip((hi - wv) / (hi - lo), 0, 1)
        s = np.clip((sy0 - Yq) / (sy0 - sy1), 0, 1)
        a_seam = sa0 + (sa1 - sa0) * s ** 0.8
        chev = chev * smooth01((a_seam - np.abs(a) - ch["inset"]) / ch["fade"]) * smooth01((tq - Yq) / 0.006)
        return ridge + chev

    ex = ex_fn(Y, TT, rho_in)
    plate.append(slab("corset", M["plate"], Pin, Nout, th_, closed_c=True, extra=ex))

    def surf(y, th, up):
        """A point on the corset's outer face (+ up) and its outward direction."""
        y, th = np.asarray(y, float), np.asarray(th, float)
        return wrap.pt(y, th, rho_at(y, th) + th_ + up), wrap.dirs(th)

    # corset rims: bottom all round; top where no cup sits over it
    edge_off = th_ * 0.5 + 0.0003
    trim.append(bead(ref, "trim_corset_bot", M["trim"], Pin[0], rim, edge_off, True, relax_it=1))
    jt = [j for j in range(Cn) if TH[j] >= tj - 1e-6] + [j for j in range(Cn) if TH[j] <= -tj + 1e-6]
    trim.append(bead(ref, "trim_corset_top", M["trim"], Pin[-1][jt], rim, edge_off, False, relax_it=1))
    # seams (proud of the plate): the front panel's, the side panels', the back's centre
    seams = []
    for sm_ in co["seams"]:
        (a0, y0), (a1, y1) = sm_
        for h in (1, -1):
            s = np.linspace(0, 1, 60)
            seams.append((h * (a0 + (a1 - a0) * s ** 0.8), y0 + (y1 - y0) * s))
    for h in (1, -1):
        y = np.linspace(cu["ub"] + 0.002, co["hip"] + 0.004, 60)
        seams.append((np.full(60, h * (ts + co["side_seam"])), y))
    y = np.linspace(sk["mid"] - 0.004, co["back_bot"] + 0.004, 60)
    seams.append((np.full(60, 180.0), y))
    for k, (a, y) in enumerate(seams):
        y = np.clip(y, bot(a) + 0.003, top(a) - 0.003)
        P = wrap.pt(y, a, rho_at(y, a) + th_ + 0.0003)
        trim.append(bead(ref, f"trim_seam{k}", M["trim"], P, dict(rim, w=rim["w"] * 0.7, h=rim["h"] * 0.7,
                                                                       below=0.0003), 0.0, False, relax_it=1))

    # leather straps with gold buckles: two each side, three across the back
    sw = co["strap_w"]
    strap_defs = [(s["y"], h * s["th"][0], h * s["th"][1], h * s["buckle"]) for s in co["straps"] for h in (1, -1)]
    a0, a1 = co["back_th"]
    strap_defs += [(s["y"], a0, a1, 180.0) for s in co["back_straps"]]
    for k, (y, a, b, bk) in enumerate(strap_defs):
        lo, hi = min(a, b), max(a, b)
        A = np.linspace(lo, hi, max(int((hi - lo) / 2.5), 4))
        Ys = np.linspace(y - sw / 2, y + sw / 2, 4)
        YY, AA = np.meshgrid(Ys, A, indexing="ij")
        rr = rho_at(YY, AA) + th_ + 0.0006 + ex_fn(YY, AA, rho_at(YY, AA))
        straps.append(slab(f"strap{k}", M["strap"], wrap.pt(YY, AA, rr), wrap.dirs(AA), 0.0018))
        c, n = (np.reshape(v, 3) for v in surf(y, bk, 0.0045))
        tdir = U(np.reshape(wrap.pt(y, bk + 1.0, rho_at(y, bk + 1.0)) - wrap.pt(y, bk - 1.0, rho_at(y, bk - 1.0)), 3))
        rigid.append(buckle(c, n, tdir, w=sw + 0.006, h=0.019, bar=0.0028, name=f"buckle{k}_rigid", material=M["trim"]))

    # ---- cups (each side on her own skin) and shoulder straps
    sh = cfg["shoulder"]
    for hand in (1, -1):
        ax, ay, az = cu["apex"]
        c = np.array([hand * ax, ay - 0.006, az - cu["base_back"]])
        apex = np.array([hand * (ax + 0.012), ay - 0.004, az])
        phis = np.arange(0.0, 150.0, 0.5)
        psis = np.linspace(0, 360, cu["spokes"], endpoint=False)
        pol = Polar(ref, c, apex, hand, phis, psis)
        r = pol.r.copy()
        H = pol.c + r[..., None] * pol.dirs(*np.meshgrid(phis, psis, indexing="ij"))
        xs, y = hand * H[..., 0], H[..., 1]
        thH = np.degrees(np.arctan2(xs, H[..., 2] - z0))
        rx, ry = cu["root"]
        cx, cy = cu["clasp"]
        wv = cu["root_w"] / 2
        tv = np.clip((y - cy) / (ry - cy), 0, 1)
        xv = cx + (rx - wv - cx) * tv ** cu["bow"]
        arx, ary = cu["arm"]
        yline = ry + (ary - ry) * (xs - (rx + wv)) / (arx - (rx + wv))
        g = np.minimum.reduce([y - ub(xs), xs - xv, ry - y, np.where(xs > rx + wv, yline - y, 1.0),
                               np.radians(ts - thH) * 0.14])
        g[~np.isfinite(r)] = -1
        # the edge on each spoke: the first phi where g turns negative (linear crossing)
        K = cu["rings"]
        edge_phi = np.zeros(len(psis))
        for j in range(len(psis)):
            neg = np.where(g[:, j] <= 0)[0]
            i = neg[0] if len(neg) else len(phis) - 1
            g0, g1 = g[i - 1, j], g[i, j]
            edge_phi[j] = phis[i - 1] + (phis[i] - phis[i - 1]) * g0 / max(g0 - g1, 1e-9)
            if not np.isfinite(r[i, j]) or abs(r[i, j] - r[i - 1, j]) > 0.004:  # the ray jumped (a gap, a fold)
                edge_phi[j] = phis[i - 1]
        # her r along each spoke inside the outline (what lies past it never pulls the cup), smoothed, lifted
        rin = r.copy()
        rin[(g <= 0) & (phis[:, None] > edge_phi[None, :] + 1.0)] = np.nan
        rf = fill_rows(rin)
        rsm = gsmooth(rf, (3.0, 1.0), True)
        shell_r = np.clip(rsm + cl, rf + cfg["clear_min"], rf + cl + 0.003)  # on her own skin's ray, never past it
        shell_r = np.maximum(dome(cu["dome"], pol, phis, psis, edge_phi, r, shell_r), rf + cfg["clear_min"])
        from scipy.interpolate import RegularGridInterpolator
        fr = RegularGridInterpolator((phis, np.r_[psis, 360.0]), np.c_[shell_r, shell_r[:, :1]])
        u = np.linspace(0.07, 1.0, K)
        u = 1 - (1 - u) ** 1.35  # rings denser at the rim; ring 0 a small ring round the apex
        PH = u[:, None] * edge_phi[None, :]
        PS = np.broadcast_to(psis[None, :], PH.shape)
        D = pol.dirs(PH, PS)
        rr = fr(np.stack([PH, PS], -1))
        Pin = pol.c + rr[..., None] * D
        # outward = the shell's normal, from a fine local difference
        Nn = shell_normals(pol, fr, PH, PS)
        nm = "cup_" + ("l" if hand > 0 else "r")
        plate.append(slab(nm, M["plate"], Pin, Nn, th_, closed_c=True, fan=True))
        trim.append(bead(ref, "trim_" + nm, M["trim"], Pin[-1], rim, edge_off, True, relax_it=1))
        if hand > 0:
            clasp_y = cy
        # shoulder strap: from the cup's flat top over her shoulder to the back's corner
        jt = np.argmin(np.abs(((psis + 180) % 360) - 180) + 0 * psis)  # psi 0: up
        top_pts = Pin[-1]
        front = top_pts[np.argmin(np.linalg.norm(top_pts[:, :2] - [hand * rx, ry], axis=1))]
        bc, by = co["back_corner"]
        back = np.reshape(wrap.pt(by, hand * bc, shell_f(by, hand * bc)), 3)
        t0, _ = cast(ref, [[hand * sh["top"][0], 1.9, -0.01]], [[0, -1.0, 0]], 0.6)
        stop = np.array([hand * sh["top"][0], 1.9 - t0[0], -0.01])
        path = catmull([front, front + [0, 0.035, -0.01], stop + [0, 0.004, 0.035], stop,
                        stop + [0, -0.004, -0.04], back + [0, 0.04, 0.0], back], 80)
        q, n, _ = ref.closest(path)
        n = U(relax(n, 4, False))
        tng = U(np.gradient(q, axis=0))
        bn = U(np.cross(n, tng))
        across = np.linspace(-sh["w"] / 2, sh["w"] / 2, 5)
        G = q[None, :, :] + across[:, None, None] * bn[None, :, :]
        qq, nn, _ = ref.closest(G.reshape(-1, 3))
        nn = U(nn).reshape(G.shape)
        Ps = qq.reshape(G.shape) + nn * cl
        plate.append(slab("strap_" + nm[-1], M["plate"], Ps, nn, th_))
        for e in (0, -1):
            trim.append(bead(ref, f"trim_strap_{nm[-1]}{e}", M["trim"], Ps[e], rim, edge_off, False, relax_it=1))
    # the clasp at the V's foot
    t0, _ = cast(ref, [[0.0, cu["clasp"][1], 0.4]], [[0, 0, -1.0]])
    cp = np.array([0.0, cu["clasp"][1], 0.4 - t0[0]])
    rigid.append(diamond(cp + [0, 0, cl + th_ + 0.002], [0, 0, 1.0], [0, 1.0, 0], 0.012, 0.017, 0.006, "clasp_rigid", M["trim"]))
    return plate, trim, straps, rigid


def dome(dm, pol, phis, psis, edge_phi, r, base):
    """A cup's designed dome: an ellipsoid on the cup's axis (axes along a, e1 up, e2 out; its centre on the axis,
    dropped along e1 by dm.drop: a full lower pole), fitted to her skin + clear inside the outline, lifted to clear
    it everywhere there (+ dm.full), eased back to her offset (base) over the outline's last part (u0..1)."""
    from scipy.optimize import least_squares
    PH, PS = np.meshgrid(phis, psis, indexing="ij")
    D = pol.dirs(PH, PS)
    da, d1, d2 = (D * pol.a).sum(-1), (D * pol.e1).sum(-1), (D * pol.e2).sum(-1)
    u = PH / edge_phi[None, :]
    fit = (u <= dm["fit_u"]) & np.isfinite(r)

    def ray(p, m=slice(None)):
        s, A, B1, B2 = p
        t = -dm["drop"]
        Q = da[m] ** 2 / A ** 2 + d1[m] ** 2 / B1 ** 2 + d2[m] ** 2 / B2 ** 2
        L = s * da[m] / A ** 2 + t * d1[m] / B1 ** 2
        K = s * s / A ** 2 + t * t / B1 ** 2 - 1
        return (L + np.sqrt(np.maximum(L * L - Q * K, 0))) / Q

    tgt = base[fit]
    r0 = float(np.nanmedian(tgt))
    p = least_squares(lambda q: ray(q, fit) - tgt, [0.0, r0, r0, r0],
                      bounds=([-0.05, 0.03, 0.03, 0.03], [0.05, 0.2, 0.2, 0.2])).x
    E = ray(p) + dm["full"]
    k = dm["soft"]  # a smooth max of the dome and her offset: the dome fills her hollows, never cuts into her
    core = 0.5 * (E + base + np.sqrt((E - base) ** 2 + k * k))
    b = smooth01((u - dm["u0"]) / (1 - dm["u0"]))
    out = core * (1 - b) + base * b
    print("dome", np.round(p * 1000, 1).tolist(), "lift over her offset mm: p50 %.1f max %.1f" %
          (np.median((out - base)[fit]) * 1000, (out - base)[fit].max() * 1000))
    return np.where(np.isfinite(out), out, base)


def shell_normals(pol, fr, PH, PS):
    e = 0.4
    def P(ph, ps):
        return pol.c + fr(np.stack([np.clip(ph, 0, pol.phis[-1]), ps % 360.0], -1))[..., None] * pol.dirs(ph, ps)
    dphi = P(PH + e, PS) - P(np.maximum(PH - e, 0), PS)
    dpsi = P(PH, PS + 2.0) - P(PH, PS - 2.0)
    n = U(np.cross(dphi, dpsi))
    d = pol.dirs(PH, PS)
    return n * np.sign((n * d).sum(-1, keepdims=True))


def catmull(P, n):
    P = np.asarray(P, float)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1:i + 3]
        for t in np.linspace(0, 1, n // (len(P) - 3), endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return np.array(out)


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


RECIPES = {"bodice": bodice}


def clearance(ref, part):
    q, n, d = ref.closest(part.P)
    return ((part.P - q) * n).sum(1)


def build(pid):
    d = os.path.join(SRC, pid)
    cfg = json.load(open(os.path.join(d, "build.json"), encoding="utf-8"))
    if cfg["recipe"] not in RECIPES:  # the limbs (boots, vambraces, gloves): tools/armor/kit_limbs.py
        import kit_limbs
        return kit_limbs.build(pid, cfg)
    mats = json.load(open(MATS, encoding="utf-8"))
    for m in cfg["mat"].values():
        assert m in mats, f"material {m} not in outfit_materials.json"
    ref = her_a()
    if cfg["recipe"] not in RECIPES:  # (a recipe in another module: build.json "module", e.g. kit_hips)
        import importlib
        RECIPES.update(importlib.import_module(cfg["module"]).RECIPES)
    plate, trim, straps, rigid = RECIPES[cfg["recipe"]](cfg, ref)
    pre = cfg.get("prefix", "bodice")
    pushed = 0
    for p in plate + trim + straps:  # never closer than clear_min (a rim's underside: 1.2 mm) along her normal
        fl = cfg["clear_min"] if p in plate else 0.0012
        for _ in range(4):  # (a push can change the closest point: again until it holds)
            c = clearance(ref, p)
            q, n, _ = ref.closest(p.P)
            low = c < fl
            if not low.any():
                break
            p.P[low] += n[low] * (fl - c[low] + 0.0001)[:, None]
            pushed += int(low.sum())
        p.N = vertex_normals(p.P, p.T)
    low_trim = {p.name: round(float(clearance(ref, p).min()) * 1000, 1) for p in trim + rigid}
    low_trim = {k: v for k, v in low_trim.items() if v < 1.5}
    parts = [Part.join(pre + "_plate", cfg["mat"]["plate"], plate), Part.join(pre + "_trim", cfg["mat"]["trim"], trim),
             Part.join(pre + "_straps", cfg["mat"]["strap"], straps)] + rigid
    for p in parts:
        p.N = vertex_normals(p.P, p.T)
    import gear_native as gn
    gn.write_glb(os.path.join(d, f"{pid}.glb"), [p.node() for p in parts], {"kit_build": {"piece": pid}})
    import hashlib
    piece = {k: v for k, v in cfg["piece"].items() if k != "layer"}
    piece = {"id": piece["id"], "name": piece["name"], "slot": piece["slot"], "style": "mesh",
             "params": {"file": f"{pid}.glb"}, **{k: v for k, v in piece.items() if k not in ("id", "name", "slot")},
             "layer": cfg["piece"].get("layer", 1), "body_sha1": hashlib.sha1(open(BODY, "rb").read()).hexdigest()}
    with open(os.path.join(d, "piece.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(piece, f, indent=1)
        f.write("\n")
    cp = clearance(ref, parts[0])
    inner = cp[cp < cfg["clear"] + 0.0015]
    rep = {"tris": int(sum(len(p.T) for p in parts)), "points": int(sum(len(p.P) for p in parts)),
           "by_part": {p.name: int(len(p.T)) for p in parts[:3]}, "pushed_to_min": pushed,
           "plate_clear_mm": [round(float(cp.min()) * 1000, 2), round(float(np.percentile(inner, 99)) * 1000, 2)],
           "trim_min_mm": round(float(clearance(ref, parts[1]).min()) * 1000, 2),
           "trim_low": low_trim, "strap_min_mm": round(float(clearance(ref, parts[2]).min()) * 1000, 2),
           "rigid_min_mm": round(float(min(clearance(ref, p).min() for p in rigid)) * 1000, 2) if rigid else None}
    print(json.dumps(rep, indent=1))
    return rep


if __name__ == "__main__":
    build(sys.argv[1])
