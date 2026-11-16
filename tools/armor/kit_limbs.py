"""The kit's limb pieces (lane D, 16 Nov 2026): boots, vambraces, gloves, authored at body A's rest (heroine.glb).

    python tools/armor/kit_build.py kit_boots        (kit_build.py hands recipes it does not know to build() here)
    python tools/turn.py run blender "armor-D: kit_boots" -- python tools/armor/piece_ship.py kit_boots

Same contract and finish as the bodice (kit_build.py): data in godot/art/armor/src/<id>/build.json, materials steel /
gold / darkleather, rims as rolled gold beads (kit_build.bead).

Charts:
    Tube    rays from an axis curve inside a limb (u = row along it, th round it; th 0 = the recipe's `front`),
            with optional cap rows at its end that tilt the rays forward (a toe): rho(u, th) of her skin
    envelope   her skin's rho closed over hollows (toes, the Achilles) and smoothed: a boot, not a sock
    patch   a plate cut from a Tube field between two edge curves u_lo(th)..u_hi(th): exact smooth outlines
    skin_shell  her own triangles offset out (a glove: tight, bends with her fingers)
"""
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_build as kb  # noqa: E402
from native_build import Part, U, grid_tris, rand01, raycast, rivet, vertex_normals  # noqa: E402


def castf(ref, F, O, D, tmax):
    """First hits on a face subset; cached like kit_build.cast."""
    O, D = np.asarray(O, float), U(D)
    key = hashlib.sha1(O.round(7).tobytes() + D.round(7).tobytes() + str(tmax).encode() + ref.V[:50].tobytes() +
                       np.asarray(F).tobytes()[:4096] + str(len(F)).encode()).hexdigest()
    f = os.path.join(kb.CACHE, "limb_" + key + ".npz")
    if os.path.exists(f):
        return np.load(f)["t"]
    t, _ = raycast(ref.V, F, O, D, tmax, chunk=48)
    os.makedirs(kb.CACHE, exist_ok=True)
    np.savez(f, t=t)
    return t


def faces(ref, test):
    c = ref.V[ref.T].mean(1)
    return ref.T[test(c)]


class Tube:
    def __init__(self, ref, F, ctrl, front, step=0.004, dth=3.0, cap=0, cap_max=80.0, tmax=0.25):
        A = kb.resample(kb.catmull(ctrl, 60 * (len(ctrl) - 1)), step, False)
        t = U(np.gradient(A, axis=0))
        e = U(np.asarray(front, float) - t[0] * (t[0] @ front))
        E1 = [e]
        for k in range(1, len(A)):
            e = U(E1[-1] - t[k] * (t[k] @ E1[-1]))
            E1.append(e)
        E1 = np.array(E1)
        phi = np.zeros(len(A))
        if cap:
            n = len(A)
            A = np.vstack([A, np.repeat(A[-1:], cap, 0)])
            t = np.vstack([t, np.repeat(t[-1:], cap, 0)])
            E1 = np.vstack([E1, np.repeat(E1[-1:], cap, 0)])
            phi = np.r_[phi, np.linspace(cap_max / cap, cap_max, cap)]
            self.n_axis = n
        else:
            self.n_axis = len(A)
        self.O, self.Tn, self.E1, self.phi = A, t, E1, phi
        self.E2 = np.cross(t, E1)
        self.rows = np.arange(len(A), dtype=float)
        self.ths = np.arange(-180.0, 180.0, dth)
        UU, TH = np.meshgrid(self.rows, self.ths, indexing="ij")
        O, D = self.frame(UU.ravel(), TH.ravel())
        self.rho = castf(ref, F, O, D, tmax).reshape(UU.shape)

    def frame(self, u, th):
        u = np.clip(np.asarray(u, float), 0, self.rows[-1])
        i = np.minimum(np.floor(u).astype(int), len(self.rows) - 2)
        f = (u - i)[..., None]
        lerp = lambda X: X[i] * (1 - f) + X[i + 1] * f  # noqa: E731
        O, T, E1, E2 = lerp(self.O), U(lerp(self.Tn)), U(lerp(self.E1)), U(lerp(self.E2))
        ph = np.radians(np.interp(u, self.rows, self.phi))[..., None]
        r = np.radians(np.asarray(th, float))[..., None]
        return O, np.cos(ph) * (np.cos(r) * E1 + np.sin(r) * E2) + np.sin(ph) * T

    def field(self, rho):
        from scipy.interpolate import RegularGridInterpolator
        th = np.r_[self.ths, 180.0]
        f = RegularGridInterpolator((self.rows, th), np.c_[rho, rho[:, :1]], bounds_error=False, fill_value=None)
        return lambda u, t: f(np.stack(np.broadcast_arrays(np.clip(u, 0, self.rows[-1]),
                                                           (np.asarray(t, float) + 180.0) % 360.0 - 180.0), -1))

    def surf(self, F, u, th, off=0.0):
        """Points on the field F (+ off, a number or a function of (u, th)) and their outward normals."""
        u, th = np.broadcast_arrays(np.asarray(u, float), np.asarray(th, float))

        def S(uu, tt):
            O, D = self.frame(uu, tt)
            o = off(uu, tt) if callable(off) else off
            return O + (F(uu, tt) + o)[..., None] * D
        P = S(u, th)
        du = S(u + 0.35, th) - S(u - 0.35, th)
        dt = S(u, th + 1.0) - S(u, th - 1.0)
        n = U(np.cross(du, dt))
        _, D = self.frame(u, th)
        n = n * np.sign((n * D).sum(-1, keepdims=True) + 1e-12)
        return P, n


def envelope(rho, close=(5, 5), sig=(2.0, 2.0), rows=None):
    """Her rho closed over hollows (a max filter: the boot bridges toes and the Achilles) and smoothed, never under her."""
    from scipy.ndimage import gaussian_filter, maximum_filter
    r = kb.fill_rows(rho)
    r = np.where(np.isfinite(r), r, np.nanmedian(r))
    e = gaussian_filter(maximum_filter(r, size=close, mode=("nearest", "wrap")), sig, mode=("nearest", "wrap"))
    e = np.maximum(e, gaussian_filter(r, (1.0, 1.0), mode=("nearest", "wrap")))
    e = np.maximum(e, r)
    if rows is not None:  # outside these rows: her own rho, lightly smoothed
        m = np.zeros(len(r), bool)
        m[rows[0]:rows[1]] = True
        e = np.where(m[:, None], e, np.maximum(gaussian_filter(r, (1.0, 1.0), mode=("nearest", "wrap")), r))
    return e


def patch(tube, F, th, ulo, uhi, nr, off):
    th = np.asarray(th, float)
    s = np.linspace(0, 1, nr)[:, None]
    UU = np.asarray(ulo, float)[None, :] * (1 - s) + np.asarray(uhi, float)[None, :] * s
    TH = np.broadcast_to(th[None, :], UU.shape)
    return tube.surf(F, UU, TH, off)


def along(tube, F, uv, off, step):
    """A curve between (u, th) knots, resampled in the chart, on F + off."""
    uv = np.asarray(uv, float)
    seg = []
    for a, b in zip(uv[:-1], uv[1:]):
        n = max(int(np.hypot(b[0] - a[0], (b[1] - a[1]) / 2.0) * 3), 4)
        s = np.linspace(0, 1, n, endpoint=False)[:, None]
        seg.append(a * (1 - s) + b * s)
    seg.append(uv[-1:])
    q = np.vstack(seg)
    return tube.surf(F, q[:, 0], q[:, 1], off)[0]


def lace_rim(w=0.0042, h=0.0021):
    return {"w": w, "h": h, "sides": 5, "step": 0.004, "below": 0.0012}


def laces(ref, tube, F, u0, u1, n, half_arc, off, mat, tag, rho_ref, rim=None):
    """Crossed laces up a front: n crossings between eyelet columns `half_arc` m either side of th 0, studs at each."""
    us = np.linspace(u0, u1, n + 1)
    th_at = lambda u: float(np.degrees(half_arc / max(float(np.ravel(F(u, 0.0))[0]) + rho_ref, 0.02)))  # noqa: E731
    parts, studs = [], []
    for k in range(n):
        a, b = us[k], us[k + 1]
        ta, tb = th_at(a), th_at(b)
        for sgn, lift in ((1, 0.0), (-1, 0.0009)):
            E = along(tube, F, [(a, sgn * ta), ((a + b) / 2, 0.0), (b, -sgn * tb)], off + lift, 0.002)
            parts.append(kb.bead(ref, f"lace_{tag}{k}{sgn}", mat, E, rim or lace_rim(), 0.0, False, relax_it=1))
    for u in us:
        for sgn in (1, -1):
            P, N = tube.surf(F, np.array([u]), np.array([sgn * th_at(u)]), off)
            studs.append(rivet(P[0], N[0], r=0.0028, h=0.0016, name=f"stud_{tag}", material=mat))
    return parts + studs


def skin_shell(name, mat, V, T, N, clear, thick):
    """Her own triangles offset out by clear, a shell thick, an edge wall on the open boundary."""
    used = np.unique(T)
    remap = np.full(len(V), -1)
    remap[used] = np.arange(len(used))
    T = remap[T]
    V, N = V[used], N[used]
    Pin, Pout = V + N * clear, V + N * (clear + thick)
    n = len(V)
    E = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    ue, cnt = np.unique(E, axis=0, return_counts=True)
    b = ue[cnt == 1]
    wall = np.vstack([np.c_[b[:, 0], b[:, 1], b[:, 1] + n], np.c_[b[:, 0], b[:, 1] + n, b[:, 0] + n]])
    P = np.vstack([Pout, Pin])
    T2 = np.vstack([kb.orient(P, T, np.vstack([N, -N])), kb.orient(P, T + n, np.vstack([N, -N]))])
    W = _wall_dirs(P, wall, V, T, b)
    T2 = np.vstack([T2, W])
    rn = rand01(name)
    return Part(name, mat, P, T2, uv0=np.c_[P[:, 0] + P[:, 2], P[:, 1]] * 3.0,
                col=np.tile([1.0, rn, 0.0, 1.0], (len(P), 1)))


def _wall_dirs(P, wall, V, T, b):
    """Wall faces wound to look out of the shell: along the boundary edge's outward in-surface direction."""
    k = len(b)
    # the triangle owning each boundary edge: its third vertex lies inside, so outward = edge mid - third vertex (in plane)
    key = {tuple(e): i for i, e in enumerate(b)}
    third = np.zeros(k, int)
    for tri in T:
        for a, c, o in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
            e = tuple(sorted((tri[a], tri[c])))
            if e in key:
                third[key[e]] = tri[o]
    mid = V[b].mean(1)
    out = U(mid - V[third])
    W = wall.copy()
    fn = np.cross(P[W[:, 1]] - P[W[:, 0]], P[W[:, 2]] - P[W[:, 0]])
    d = np.vstack([out, out])
    flip = (fn * d).sum(1) < 0
    W[flip] = W[flip][:, ::-1]
    return W


# ---------------------------------------------------------------- boots

def boots(cfg, ref):
    M, rim = cfg["mat"], cfg["rim"]
    G = {"leather": [], "plate": [], "trim": [], "laces": [], "sole": []}
    rigid = []
    for side, sx in (("l", 1.0), ("r", -1.0)):
        J = ref.joints
        F = faces(ref, lambda c: (c[:, 0] * sx > 0.008) & (c[:, 1] < cfg["faces_y"]))
        ctrl = [[J[f"calf_{side}"][0] + sx * a[0], a[1], a[2]] for a in cfg["axis"]]
        tube = Tube(ref, F, np.array(ctrl), [0, 0, 1.0], step=cfg["step"], dth=cfg["dth"], cap=cfg["cap"],
                    cap_max=cfg["cap_max"])
        nA = tube.n_axis
        yax = tube.O[:nA, 1]
        bend = int(np.argmax(yax < cfg["y_bend"]))
        env = envelope(tube.rho, tuple(cfg["close"]), tuple(cfg["sig"]), rows=None)
        tb = cfg["toe"]  # the toe box: one smooth round over her toes (a boot, never toes)
        z = np.r_[tube.O[:nA, 2], np.full(len(tube.rows) - nA, tube.O[nA - 1, 2])]
        w = kb.smooth01((z - tb["from_z"]) / tb["blend"])[:, None]
        env = env * (1 - w) + (envelope(tube.rho, tuple(tb["close"]), tuple(tb["sig"])) + tb["lift"]) * w
        Fe = tube.field(env)
        u_of_y = lambda y: np.interp(-np.asarray(y, float), -yax[:bend + 1], np.arange(bend + 1))  # noqa: E731
        cl, th_l = cfg["clear"], cfg["thick"]
        th = tube.ths
        R = len(tube.rows)

        def top_y(t, front, back):
            return back + (front - back) * (1 + np.cos(np.radians(t))) / 2

        # -- the leather upper: toe tip (row 0) up to under the cuff
        c = cfg["cuff"]
        nr, nc = cfg["mesh"]
        th = np.linspace(-180, 180, nc, endpoint=False)
        u_top = u_of_y(top_y(th, c["top_front"], c["top_back"]) - c["h"] + c["under"])
        UU = u_top[None, :] + (R - 1 - u_top[None, :]) * np.linspace(1, 0, nr)[:, None]
        P, N = tube.surf(Fe, UU, np.broadcast_to(th, UU.shape), cl)
        P[..., 1] = np.maximum(P[..., 1], cfg["sole"]["floor"])  # (under her sole: flat, inside the sole)
        G["leather"].append(kb.slab(f"boot_{side}", M["leather"], P, N, th_l, closed_c=True, fan=True))

        lo = cl + th_l + 0.0006   # over the leather
        # -- the cuff: a plate band at the top, gold rims both edges
        nt = 90
        tc = np.linspace(-180, 180, nt, endpoint=False)
        ut, ub = u_of_y(top_y(tc, c["top_front"], c["top_back"])), u_of_y(top_y(tc, c["top_front"], c["top_back"]) - c["h"])
        cf = lambda uu, t: lo + c["flare"] * np.clip((np.asarray(uu) - ub.mean()) / (ut.mean() - ub.mean()), 0, 1) ** 2  # noqa: E731
        P, N = patch(tube, Fe, tc, ub, ut, 7, cf)
        G["plate"].append(kb.slab(f"cuff_{side}", M["plate"], P, N, cfg["plate_thick"], closed_c=True))
        eo = cfg["plate_thick"] * 0.5 + 0.0003
        G["trim"].append(kb.bead(ref, f"trim_cuff_top_{side}", M["trim"], P[-1], rim, eo, True, relax_it=1))
        G["trim"].append(kb.bead(ref, f"trim_cuff_bot_{side}", M["trim"], P[0], rim, eo, True, relax_it=1))

        # -- the toe cap: over the toe, a curved back edge, gold rim on it
        tcap = cfg["toecap"]
        tt = np.linspace(-tcap["th"], tcap["th"], 41)
        u_back = tcap["u"] - tcap["sweep"] * (tt / tcap["th"]) ** 2
        # (its own field: her toes closed under one wide smooth round, never under the boot's: a smooth cap, no toe bumps)
        Fc = tube.field(np.maximum(envelope(tube.rho, tuple(tcap.get("close", (9, 17))), tuple(tcap.get("sig", (4.0, 5.0)))) +
                                   tcap.get("lift", 0.0), env))
        Pc, Nc = patch(tube, Fc, tt, nA - 1 - u_back, np.full_like(tt, R - 1.0), tcap.get("nr", 16), lo)
        Pc, Nc = smooth_out(Pc, Nc, tcap.get("smooth", 0))
        G["plate"].append(kb.slab(f"toecap_{side}", M["plate"], Pc, Nc, cfg["plate_thick"]))
        G["trim"].append(kb.bead(ref, f"trim_toecap_{side}", M["trim"], Pc[0], rim, eo, False, relax_it=1))

        # -- the knee cop: a pointed shield over the knee, standing off; rigid
        k = cfg["kneecop"]
        tk = np.linspace(-k["th"], k["th"], 33)
        x = tk / k["th"]
        kb_y = k["bot"] + k["bot_rise"] * x ** 2
        kt_y = k["top"] - (k["top"] - k["side_top"]) * np.abs(x) ** k["point"]
        ridge = lambda uu, t: k["off"] + k["ridge"] * np.clip(1 - np.abs(t) / k["ridge_w"], 0, 1) ** 2 + \
            k["dome"] * (1 - (np.asarray(t) / k["th"]) ** 2)  # noqa: E731
        Fk = tube.field(envelope(tube.rho, (9, 9), (4.0, 4.0)))
        Pk, Nk = patch(tube, Fk, tk, u_of_y(kb_y), u_of_y(kt_y), 12, ridge)
        cop = kb.slab(f"kneecop_{side}_rigid", M["plate"], Pk[::-1], Nk[::-1], cfg["plate_thick"] + 0.0004)
        ring = np.vstack([Pk[0], Pk[1:-1, -1], Pk[-1][::-1], Pk[-2:0:-1, 0]])
        cop_trim = kb.bead(ref, f"kneecop_{side}_trim_rigid", M["trim"], ring, rim, eo, True, relax_it=1)
        rigid += [cop, cop_trim]

        # -- laces: instep to the cuff
        L = cfg["laces"]
        u_inst = float(np.argmax(tube.O[:nA, 2] > L["z_start"]))
        G["laces"] += laces(ref, tube, Fe, u_of_y(c["top_front"] - c["h"] - L["below_cuff"]), u_inst, L["n"],
                            L["half"], cl + th_l + 0.0002, M["trim"], side, 0.0,
                            lace_rim(L.get("w", 0.0042), L.get("h", 0.0021)))

        # -- the sole and the block heel (her foot stays flat: the heel is a block round her heel, at her stance)
        G["sole"] += sole(cfg, P_bottom(tube, Fe, cl, nA, R), side, M["sole"])
    return G, rigid


def smooth_out(P, N, it):
    """A grid surface smoothed `it` times (Laplacian on the grid), never moved inward of where it started: bumps
    bridged over (a cap over toes), its outline kept. Returns the points and fresh normals."""
    if not it:
        return P, N
    P0, N0 = P.copy(), N.copy()
    P = P.copy()
    for _ in range(it):
        Q = P.copy()
        Q[1:-1, 1:-1] = (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:]) / 4.0
        Q[0, 1:-1] = (P[0, :-2] + P[0, 2:]) / 2.0
        Q[-1, 1:-1] = (P[-1, :-2] + P[-1, 2:]) / 2.0
        P = P + (Q - P) * 0.7
        s = ((P - P0) * N0).sum(-1)
        P = P - N0 * np.minimum(s, 0.0)[..., None]
    du = np.gradient(P, axis=0)
    dt = np.gradient(P, axis=1)
    n = U(np.cross(du, dt))
    n = n * np.sign((n * N0).sum(-1, keepdims=True) + 1e-12)
    return P, n


def P_bottom(tube, F, cl, nA, R):
    UU, TH = np.meshgrid(np.arange(nA - 60 if nA > 60 else 0, R, 0.5), tube.ths, indexing="ij")
    P, _ = tube.surf(F, UU, TH, cl + 0.0016)
    return P.reshape(-1, 3)


def sole(cfg, P, side, mat):
    from scipy.spatial import ConvexHull
    s = cfg["sole"]
    Q = P[P[:, 1] < s["foot_y"]][:, [0, 2]]
    h = ConvexHull(Q)
    ring = Q[h.vertices]
    ring = kb.resample(np.c_[ring, np.zeros(len(ring))], 0.004, True)[:, :2]
    ring = kb.relax(np.c_[ring, np.zeros(len(ring))], 3, True)[:, :2]
    c = ring.mean(0)
    nrm = ring - c
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    ring = ring + nrm * s["margin"]
    parts = [prism(f"sole_{side}", mat, ring, s["y_bot"], s["y_top"], s["bevel"], hollow=s["hollow"])]
    zb = ring[:, 1].min()
    heel = clip_poly(ring, zb + s["heel_len"])
    hc = heel.mean(0)
    heel = heel + (heel - hc) / np.linalg.norm(heel - hc, axis=1, keepdims=True) * s["heel_extra"]
    bot = hc + (heel - hc) * s["heel_taper"]
    parts.append(prism(f"heel_{side}", mat, heel, s["y_bot"] - 0.0005, s["heel_top"], 0.0015, bot=bot, hollow=s["hollow"] + s["heel_extra"]))
    return parts


def clip_poly(ring, zmax):
    out = []
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        ina, inb = a[1] <= zmax, b[1] <= zmax
        if ina:
            out.append(a)
        if ina != inb:
            t = (zmax - a[1]) / (b[1] - a[1])
            out.append(a + (b - a) * t)
    return kb.resample(np.c_[np.array(out), np.zeros(len(out))], 0.004, True)[:, :2]


def prism(name, mat, ring, y0, y1, bevel, bot=None, hollow=0.0):
    """A prism over a ring (x, z): bottom (ring `bot`, else ring) at y0, top at y1, its top edge bevelled. hollow > 0:
    the top is an annulus that wide (open inside: no face through her foot, the boot's leather closes it)."""
    bot = ring if bot is None else bot
    c = ring.mean(0)
    inw = (c - ring) / np.linalg.norm(c - ring, axis=1, keepdims=True)
    inset = ring + inw * bevel
    lift = lambda R, y: np.c_[R[:, 0], np.full(len(R), y), R[:, 1]]  # noqa: E731
    rings = [lift(bot, y0), lift(ring, y1 - bevel), lift(inset, y1)]
    if hollow:
        rings.append(lift(ring + inw * (bevel + hollow), y1))
    n, nr = len(ring), len(rings)
    V = np.vstack(rings + [[c[0], y0, c[1]], [c[0], y1, c[1]]])
    j = np.arange(n)
    T = [grid_tris(nr, n, close=True), np.c_[np.full(n, nr * n), j, (j + 1) % n]]
    if not hollow:
        T.append(np.c_[np.full(n, nr * n + 1), (nr - 1) * n + j, (nr - 1) * n + (j + 1) % n])
    cen = np.array([c[0], (y0 + y1) / 2, c[1]])
    D = V - cen
    if hollow:
        D[2 * n:4 * n] = [0, 1.0, 0]
    T = kb.orient(V, np.vstack(T), D)
    return Part(name, mat, V, T, uv0=np.c_[V[:, 0] + V[:, 2], V[:, 1]] * 3.0, col=np.tile([1.0, rand01(name), 0, 0.0], (len(V), 1)))


# ---------------------------------------------------------------- vambraces

def vambraces(cfg, ref):
    M, rim = cfg["mat"], cfg["rim"]
    G = {"leather": [], "plate": [], "trim": [], "laces": []}
    rigid = []
    for side, sx in (("l", 1.0), ("r", -1.0)):
        J = ref.joints
        e, h = J[f"lowerarm_{side}"], J[f"hand_{side}"]
        a = U(h - e)
        wide = U(J[f"index_01_{side}"] - J[f"pinky_01_{side}"])
        dors = U(np.cross(wide, a))
        dors = dors if dors[1] > 0 else -dors  # (A pose, palms to her thighs: the back of her hand looks up and out)
        F = faces(ref, lambda c: (c[:, 0] * sx > cfg["faces_x"]) & (c[:, 1] > 0.95) & (c[:, 1] < 1.45))
        L = np.linalg.norm(h - e)
        s0, s1 = cfg["axis"]
        tube = Tube(ref, F, np.array([e + a * s0, e + a * (s0 + s1) / 2, e + a * s1]), dors, step=cfg["step"], dth=cfg["dth"])
        rows_s = s0 + (s1 - s0) * tube.rows / tube.rows[-1]
        u_of = lambda s: np.interp(s, rows_s, tube.rows)  # noqa: E731
        env = envelope(tube.rho, tuple(cfg["close"]), tuple(cfg["sig"]))
        Fe = tube.field(env)
        cl, tl, tp = cfg["clear"], cfg["thick"], cfg["plate_thick"]
        lin = cfg["lining"]
        th = np.linspace(-180, 180, lin.get("nc", 120), endpoint=False)
        c = np.cos(np.radians(th))
        s_lo = lin["elbow"] + (lin["elbow_in"] - lin["elbow"]) * (1 - c) / 2
        P, N = patch(tube, Fe, th, u_of(s_lo), np.full_like(th, u_of(lin["wrist"])), lin.get("nr", 40), cl)
        G["leather"].append(kb.slab(f"vamb_lining_{side}", M["leather"], P, N, tl, closed_c=True))

        p = cfg["plate"]
        tp_ = np.linspace(-p["th"], p["th"], p.get("nc", 61))
        lo = cl + tl + 0.0006
        fl = p["flare"]
        flare = lambda uu, t: lo + fl * np.clip(1 - (np.interp(uu, tube.rows, rows_s) - p["elbow"]) / p["flare_len"], 0, 1) ** 2  # noqa: E731
        se = p["elbow"] + p["elbow_dip"] * (np.abs(tp_) / p["th"]) ** 2
        Pp, Np = patch(tube, Fe, tp_, u_of(se), np.full_like(tp_, u_of(p["wrist"])), p.get("nr", 36), flare)
        eo = tp * 0.5 + 0.0003
        # the plate is rigid on her forearm (by clearance: metal need not bend); its rim one ring round it
        rigid.append(kb.slab(f"vamb_plate_{side}_rigid", M["plate"], Pp, Np, tp))
        edge = np.vstack([Pp[0], Pp[1:, -1], Pp[-1][::-1][1:], Pp[-2:0:-1, 0]])
        rigid.append(kb.bead(ref, f"vamb_plate_{side}_trim_rigid", M["trim"], edge, dict(rim, w=rim["w"] * p.get("rim_k", 0.85)), eo, True, relax_it=1))
        # the gold elbow band: a rim round the lining's top edge
        G["trim"].append(kb.bead(ref, f"trim_vamb_top_{side}", M["trim"], P[0], dict(rim, w=rim["w"] * 0.7, h=rim["h"] * 0.8), tl * 0.5 + 0.0003, True, relax_it=1))
        # the gold wrist band: a full ring over plate and lining
        wb = cfg["wrist_band"]
        lob = lo + tp + 0.0006
        Pb, Nb = patch(tube, Fe, th, np.full_like(th, u_of(wb["s0"])), np.full_like(th, u_of(wb["s1"])), 6, lob)
        G["trim"].append(kb.slab(f"vamb_band_{side}", M["trim"], Pb, Nb, wb["thick"], closed_c=True))
        G["trim"].append(kb.bead(ref, f"trim_band_a_{side}", M["trim"], Pb[0], dict(rim, w=rim["w"] * 0.6, h=rim["h"] * 0.7), wb["thick"] * 0.5 + 0.0003, True, relax_it=1))
        G["trim"].append(kb.bead(ref, f"trim_band_b_{side}", M["trim"], Pb[-1], dict(rim, w=rim["w"] * 0.6, h=rim["h"] * 0.7), wb["thick"] * 0.5 + 0.0003, True, relax_it=1))
        for k, tr in enumerate(np.linspace(-180, 180, wb.get("rivets", 8), endpoint=False)):
            Pr, Nr = tube.surf(Fe, np.array([u_of((wb["s0"] + wb["s1"]) / 2)]), np.array([tr]), lob + wb["thick"])
            G["trim"].append(rivet(Pr[0], Nr[0], r=0.0024, h=0.0014, name=f"vamb_rivet_{side}{k}", material=M["trim"]))
        # crossed laces over the open inner side
        lc = cfg["laces"]
        Fi = lambda uu, t: Fe(uu, np.asarray(t) + 180.0)  # noqa: E731
        tube_in = _Rot(tube, 180.0)
        G["laces"] += laces(ref, tube_in, Fi, u_of(lc["s0"]), u_of(lc["s1"]), lc["n"], lc["half"], cl + tl + 0.0002, M["trim"], "v" + side, 0.0)
    return G, rigid


class _Rot:
    """A Tube seen with th turned by `d` degrees (its th 0 = the original's d)."""

    def __init__(self, tube, d):
        self.t, self.d = tube, d

    def surf(self, F, u, th, off=0.0):
        return self.t.surf(lambda uu, tt: F(uu, np.asarray(tt) - self.d), u, np.asarray(th) + self.d,
                           (lambda uu, tt: off(uu, np.asarray(tt) - self.d)) if callable(off) else off)


# ---------------------------------------------------------------- gloves

def gloves(cfg, ref):
    M = cfg["mat"]
    G = {"leather": []}
    J = ref.joints
    for side in ("l", "r"):
        h, e = J[f"hand_{side}"], J[f"lowerarm_{side}"]
        a = U(h - e)
        segs = [(h, J[f"middle_01_{side}"], 1.0, "hand")]
        for f in ("index", "middle", "ring", "pinky"):
            segs.append((J[f"{f}_01_{side}"], J[f"{f}_02_{side}"], cfg["finger_t"], f))
            segs.append((J[f"{f}_02_{side}"], J[f"{f}_03_{side}"], 0.0, f))
            segs.append((J[f"{f}_03_{side}"], J[f"{f}_04_leaf_{side}"], 0.0, f))
        segs.append((J[f"thumb_01_{side}"], J[f"thumb_02_{side}"], 1.0, "thumb"))
        segs.append((J[f"thumb_02_{side}"], J[f"thumb_03_{side}"], cfg["thumb_t"], "thumb"))
        segs.append((J[f"thumb_03_{side}"], J[f"thumb_04_leaf_{side}"], 0.0, "thumb"))
        V = ref.V
        near = np.linalg.norm(V - h, axis=1) < 0.16
        s = (V - h) @ a
        best = np.full(len(V), np.inf)
        keep = np.zeros(len(V), bool)
        seg_of = np.full(len(V), -1)
        for k, (p0, p1, tmax, _) in enumerate(segs):
            d = p1 - p0
            t = np.clip(((V - p0) @ d) / (d @ d), 0, 1)
            dist = np.linalg.norm(V - (p0 + t[:, None] * d), axis=1)
            better = dist < best
            best = np.where(better, dist, best)
            keep = np.where(better, t <= tmax + 1e-9, keep)
            seg_of = np.where(better, k, seg_of)
        keep &= near & (s > cfg["wrist_s"])
        # the finger openings cut clean: every triangle touching a kept point, its points past a cut slid back onto
        # the cut's plane (a ring across the finger at finger_t / thumb_t, not her triangles' saw edge)
        inr = near & (s > cfg["wrist_s"])
        T = ref.T[keep[ref.T].any(1) & inr[ref.T].all(1)]
        Vg = V.copy()
        out = np.unique(T[~keep[T]])
        ok = keep.copy()
        for k, (p0, p1, tmax, _) in enumerate(segs):
            if not 0.0 < tmax < 1.0:
                continue
            d = p1 - p0
            dn = U(d)
            # the points past this cut: nearest to this segment or to the next ones of the same finger
            sel = out[np.isin(seg_of[out], [k, k + 1]) & (segs[k][3] == np.array([segs[j][3] for j in seg_of[out]]))]
            sl = ((V[sel] - p0) @ dn) - tmax * np.linalg.norm(d)
            sel, sl = sel[sl < 0.012], sl[sl < 0.012]
            Vg[sel] -= dn * np.maximum(sl, 0.0)[:, None]
            ok[sel] = True
        T = T[ok[T].all(1)]  # (a triangle reaching past a cut it cannot slide to: left out)
        G["leather"].append(skin_shell(f"glove_{side}", M["leather"], Vg, T, ref.N, cfg["clear"], cfg["thick"]))
        G.setdefault("trim", [])
        # the cuff: a stiffer leather band round her wrist over the glove, gold studs round it, a gold bead at its top
        c = cfg["cuff"]
        wide = U(J[f"index_01_{side}"] - J[f"pinky_01_{side}"])
        dors = U(np.cross(wide, a))
        dors = dors if dors[1] > 0 else -dors
        sx = 1.0 if side == "l" else -1.0
        F = faces(ref, lambda q: (q[:, 0] * sx > 0.26) & (q[:, 1] > 0.95) & (q[:, 1] < 1.45))
        tube = Tube(ref, F, np.array([h + a * c["s0"], h + a * (c["s0"] + c["s1"]) / 2, h + a * c["s1"]]), dors,
                    step=0.003, dth=3.0)
        rows_s = c["s0"] + (c["s1"] - c["s0"]) * tube.rows / tube.rows[-1]
        u_of = lambda q: np.interp(q, rows_s, tube.rows)  # noqa: E731
        Fe = tube.field(envelope(tube.rho, (3, 7), (1.5, 2.5)))
        lo = cfg["clear"] + cfg["thick"] + c["gap"]
        th = np.linspace(-180, 180, c.get("nc", 64), endpoint=False)
        P, N = patch(tube, Fe, th, np.full_like(th, u_of(c["bot"])), np.full_like(th, u_of(c["top"])), c.get("nr", 8), lo)
        G["leather"].append(kb.slab(f"glove_cuff_{side}", M["leather"], P, N, c["thick"], closed_c=True))
        rim = cfg["rim"]
        G["trim"].append(kb.bead(ref, f"glove_cuff_top_{side}", M["trim"], P[-1], rim, c["thick"] * 0.5 + 0.0003, True, relax_it=1))
        for k, tr in enumerate(np.linspace(-180, 180, c["studs"], endpoint=False)):
            Pr, Nr = tube.surf(Fe, np.array([u_of((c["bot"] + c["top"]) / 2 - 0.002)]), np.array([tr]), lo + c["thick"])
            G["trim"].append(rivet(Pr[0], Nr[0], r=c["stud_r"], h=c["stud_h"], name=f"glove_stud_{side}{k}", material=M["trim"]))
    return G, []


RECIPES = {"boots": boots, "vambraces": vambraces, "gloves": gloves}


# ---------------------------------------------------------------- build

def build(pid, cfg=None):
    d = os.path.join(kb.SRC, pid)
    cfg = cfg or json.load(open(os.path.join(d, "build.json"), encoding="utf-8"))
    mats = json.load(open(kb.MATS, encoding="utf-8"))
    for m in cfg["mat"].values():
        assert m in mats, f"material {m} not in outfit_materials.json"
    ref = kb.her_a()
    ref.torso = ref.T  # (the push and clearance read her whole skin)
    G, rigid = RECIPES[cfg["recipe"]](cfg, ref)
    pushed = 0
    floor = {"leather": cfg["clear_min"], "plate": cfg["clear_min"], "sole": -1.0}
    for g, ps in G.items():
        for p in ps:
            fl = floor.get(g, 0.0012)
            if fl < 0:
                continue
            for _ in range(4):
                c = kb.clearance(ref, p)
                q, n, _ = ref.closest(p.P)
                low = c < fl
                if not low.any():
                    break
                p.P[low] += n[low] * (fl - c[low] + 0.0001)[:, None]
                pushed += int(low.sum())
            p.N = vertex_normals(p.P, p.T)
    parts = [Part.join(f"{pid[4:]}_{g}", ps[0].material, ps) for g, ps in G.items() if ps] + rigid
    for p in parts:
        p.N = vertex_normals(p.P, p.T)
    import gear_native as gn
    gn.write_glb(os.path.join(d, f"{pid}.glb"), [p.node() for p in parts], {"kit_build": {"piece": pid}})
    piece = {k: v for k, v in cfg["piece"].items() if k != "layer"}
    piece = {"id": piece["id"], "name": piece["name"], "slot": piece["slot"], "style": "mesh",
             # (build.json "params": e.g. tuck_under, her skin sunk under named parts as piece_blender reads it)
             "params": {"file": f"{pid}.glb", **cfg.get("params", {})},
             **{k: v for k, v in piece.items() if k not in ("id", "name", "slot")},
             "layer": cfg["piece"].get("layer", 1), "body_sha1": hashlib.sha1(open(kb.BODY, "rb").read()).hexdigest()}
    with open(os.path.join(d, "piece.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(piece, f, indent=1)
        f.write("\n")
    rep = {"tris": int(sum(len(p.T) for p in parts)), "points": int(sum(len(p.P) for p in parts)),
           "by_part": {p.name: int(len(p.T)) for p in parts}, "pushed_to_min": pushed,
           "min_clear_mm": {p.name: round(float(kb.clearance(ref, p).min()) * 1000, 2) for p in parts}}
    print(json.dumps(rep, indent=1))
    return rep


if __name__ == "__main__":
    build(sys.argv[1])
