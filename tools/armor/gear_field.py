"""Gear follow field (P2): how a bound piece follows a body other than its bind body, as one smooth surface.

gear_fit's exact evaluation (each vertex's own bound triangle + its offset in that triangle's frame) is right for a part
on the skin and wrong for a part that stands off it: neighbouring vertices of one stand-off surface (a pauldron over
the shoulder, a skirt over both thighs) are bound to different body parts whose moves differ, so the surface tears.
Production "smart fit" moves those parts by a SPATIALLY smooth deformation built from the body's own move instead:

  field     F(x) = the body's per-vertex move d_j (this body minus the bind body, head included) blended at x (a point on
            the bind body's side) with a compact C2 kernel (Wendland) on the LATERAL distance to body point j
            (sqrt(|x - x_j|^2 - c^2), c = x's distance to the body: the footprint on the skin under x), its radius growing
            with c (r = r_min + gain c, r_min = 2.5 body edge lengths, capped at 6 cm), weighted by the body point's
            area and by its AFFINITY: body points whose normal faces away from the kernel's mean normal at x (the other
            thigh, the inner arm seen from the torso's side) are dropped, smoothly, by how coherent that mean is (where
            normals cancel, e.g. midway between the thighs, nothing is dropped). F is a pure function of the position,
            so every mesh of a unit (and every unit) sees one field; it is evaluated on a lattice (cached per body pair)
            and read trilinearly, which also gives its Jacobian for the normals.
  blend     a vertex within NEAR_M of the bind skin keeps its exact bound evaluation (skin-tight stays skin-tight), one
            beyond NEAR_M + BLEND_M takes the field; smoothstep between.
  clearance no piece vertex ends nearer the new skin than it was to the bind skin (inside stays no deeper): the deficit
            is pushed along the new skin's normal, dilated and smoothed over the piece so the push does not dent it;
            rigid components get one translation each (the smallest that clears them).
On the bind body every move is zero, so the result is the bind geometry exactly.
"""
import numpy as np
from scipy.spatial import cKDTree

FIELD = {
    "near_m": -1.0,         # within: the exact bound evaluation; negative = none (round 2: every vertex on the field,
                            # the tight set held by HOLD; a 1 mm band measured worse on the weight body: 2 rows flagged
                            # against 1, its jumps across creases)
    "blend_m": 0.002,       # over this band: exact -> field
    "r_min_edges": 2.5,     # the kernel's smallest radius, in body edge lengths (close ~19 mm, play ~37 mm)
    "r_tight_edges": 2.5,   # the kernel's smallest radius within HOLD in_m of the skin (fading to r_min over fade_m)
    "r_gain": 1.2,          # radius growth per metre of stand-off
    "r_max_m": 0.06,
    "grid_edges": 0.75,     # lattice spacing, in body edge lengths
    "aff": (-0.1, 0.6),     # affinity: body normal . mean normal, smoothstep from -> to
    "coh": 0.5,             # coherence at which the affinity filter is full
    "coarse_m": 0.012,      # the coarse level's cluster size (kernels over 3-4 cm)
    "coarse_r": (0.03, 0.04),
    "push_m": (0.004, 0.02),  # a clearance push's smallest radius: min, max of its clearance share (0.5 c + min)
    "push_slope": 15.0,       # a push's radius is at least this times its depth (the lean: ~1.6 / 15 = 11% at most)
    "push_max_m": 0.06,
    "push_cos": 0.5,          # a smoothed push direction counts at least this much toward the skin's normal
    "expect": "G",            # the stretch gate's reference: "G" the map's own Jacobian, "Gk" the body's over the kernel
    "push_keep": 0.6,         # a stand-off vertex (past HOLD in_m) is pushed only when nearer than this share of its
                              # bind clearance (never below in_m): a part may settle toward a fuller body (a strap in a
                              # narrowing cleft), never into it
}


def push_req(c0):
    """The clearance the one-sided push keeps: the bind clearance up to HOLD in_m (and inside: no deeper), beyond it
    push_keep of it, never under in_m."""
    return np.where(c0 > HOLD["in_m"], np.maximum(HOLD["in_m"], FIELD["push_keep"] * c0), c0)


# the tight set holds its bind clearance (two-sided, along the new skin's normal): full within in_m, fading to none over
# fade_m beyond it (the exact binding is not used for that: it jumps where the binding changes body part at a crease)
HOLD = {"in_m": 0.004, "fade_m": 0.004, "rounds": 2,
        "dir_m": 0.008,   # the hold's direction: the new skin's normals averaged over the piece's held vertices this near
        "cos": 0.5,
        "coh": (0.6, 0.9),
        "smooth": 1.0}  # the neighbours' mean skin normal's length: no hold under the first, full over the second
# a rigid component's made-to-measure fit: rotation + translation + a scale per principal axis of its own (no shear)
RIGID = {"scale": (0.85, 1.25), "iters": 30, "reg": 0.02,
         "clear_m": 0.0003,   # a point clear on the bind body ends at least min(its bind clearance, this) out
         "near_m": 0.003,     # points within this of their target join the LP (so the change pushes no other in)
         "clear_w": 0.1,      # LP cost of a unit scale change, in metres of translation (1% ~ 1 mm)
         "clear_rounds": 4}


def U(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-20)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def wendland(q):
    q = np.clip(q, 0.0, 1.0)
    return (1 - q) ** 4 * (4 * q + 1)


def vertex_areas(V, T):
    a = 0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1) / 3.0
    A = np.zeros(len(V))
    for k in range(3):
        np.add.at(A, T[:, k], a)
    return A


def beta(c):
    """The field's share at bind clearance c (m): 0 within NEAR_M, 1 beyond NEAR_M + BLEND_M (1 everywhere when
    NEAR_M is negative)."""
    if FIELD["near_m"] < 0:
        return np.ones(np.shape(c))
    return smoothstep((np.abs(c) - FIELD["near_m"]) / FIELD["blend_m"])


class Level:
    """Body points for the kernel: bind positions P, bind normals N, areas A, and per point the affine map of the body's
    move there, x -> a + F x (F the body's deformation gradient at the point, a = its new position - F P): 12 channels."""

    def __init__(self, P, N, C, A):
        self.P, self.N, self.C, self.A = P, N, C, A
        self.tree = cKDTree(P)


def clusters(P, N, C, A, size):
    k = np.floor(P / size).astype(np.int64)
    _, inv = np.unique(k, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    n = inv.max() + 1
    s = np.bincount(inv, A, n)
    m = lambda X: np.stack([np.bincount(inv, A * X[:, i], n) for i in range(X.shape[1])], 1) / s[:, None]  # noqa: E731
    return Level(m(P), U(m(N)), m(C), s)


def frames3(V, T):
    """[n,3,3] per triangle: columns edge 1, edge 2, unit normal."""
    e1 = V[T[:, 1]] - V[T[:, 0]]
    e2 = V[T[:, 2]] - V[T[:, 0]]
    return np.stack([e1, e2, U(np.cross(e1, e2))], -1)


def deformation(bbody, body):
    """Per body vertex: the body's deformation gradient (bind -> body; each triangle's [e1 e2 n] map, area-weighted
    over the vertex's triangles; it keeps the normal's length, so an offset along the normal keeps its length)."""
    V0, T = bbody.V, bbody.T
    M0 = frames3(V0, T)
    a = 0.5 * np.linalg.norm(np.cross(M0[:, :, 0], M0[:, :, 1]), axis=1)
    ok = a > 1e-12
    Ft = np.tile(np.eye(3), (len(T), 1, 1))
    Ft[ok] = frames3(body.V, T[ok]) @ np.linalg.inv(M0[ok])
    w = np.where(ok, a, 0.0)
    Fv = np.zeros((len(V0), 9))
    s = np.zeros(len(V0))
    for k in range(3):
        np.add.at(Fv, T[:, k], w[:, None] * Ft.reshape(-1, 9))
        np.add.at(s, T[:, k], w)
    Fv = np.where(s[:, None] > 0, Fv / np.maximum(s, 1e-30)[:, None], np.eye(3).reshape(1, 9))
    return Fv.reshape(-1, 3, 3)


class Field:
    """The body's move as a smooth map around the bind body (one per body pair and tier): x -> x' = the kernel blend of
    the body points' affine maps (a_j + F_j x), so an offset from the skin turns and stretches with the skin under it."""

    def __init__(self, body, bbody):
        V0 = bbody.V
        A = vertex_areas(V0, bbody.T)
        keep = A > 0
        Tt = bbody.T[:bbody.ntri_t]
        e = np.linalg.norm(V0[Tt[:, 0]] - V0[Tt[:, 1]], axis=1)
        self.edge = float(np.median(e))
        self.r_min = FIELD["r_min_edges"] * self.edge
        self.g = FIELD["grid_edges"] * self.edge
        self.zero = not np.abs(body.V - V0).max() > 0
        Fj = deformation(bbody, body) if not self.zero else np.tile(np.eye(3), (len(V0), 1, 1))
        a = body.V - np.einsum("nij,nj->ni", Fj, V0)
        C = np.hstack([a, Fj.reshape(-1, 9)])[keep]
        self.fine = Level(V0[keep], bbody.N[keep], C, A[keep])
        self.coarse = clusters(V0[keep], bbody.N[keep], C, A[keep], FIELD["coarse_m"])
        self.keys = np.zeros(0, np.int64)
        self.vals = np.zeros((0, 12))

    # ------------------------------------------------------------------ the kernel at points
    def radius(self, c):
        # near the skin (the tight set) the kernel may shrink toward r_tight_edges (measured on second's gloves: the
        # field's own stretch grew more than the clearance improved, so it is left at r_min)
        rm = self.edge * (FIELD["r_tight_edges"] + (FIELD["r_min_edges"] - FIELD["r_tight_edges"])
                          * smoothstep((c - HOLD["in_m"]) / HOLD["fade_m"]))
        return np.clip(rm + FIELD["r_gain"] * c, rm, max(FIELD["r_max_m"], self.r_min))

    def _blend(self, lv, Y, c, r, chunk=4000):
        """Kernel blend of the level's channels at Y (with their clearance c and radius r): (sum w C, sum w)."""
        k_ = lv.C.shape[1]
        S = np.zeros((len(Y), k_))
        Wt = np.zeros(len(Y))
        R = np.sqrt(r * r + c * c)
        order = np.argsort(R)
        a0, a1 = FIELD["aff"]
        for s in range(0, len(Y), chunk):
            idx = order[s:s + chunk]
            sm = cKDTree(Y[idx]).sparse_distance_matrix(lv.tree, float(R[idx].max()), output_type="ndarray")
            if not len(sm):
                continue
            i, j, dist = sm["i"].astype(np.int64), sm["j"].astype(np.int64), sm["v"]
            del sm
            gi = idx[i]
            ok = dist <= R[gi]
            i, j, dist, gi = i[ok], j[ok], dist[ok], gi[ok]
            rho = np.sqrt(np.maximum(dist * dist - c[gi] ** 2, 0.0))
            w0 = lv.A[j] * wendland(rho / r[gi])
            n = len(idx)
            mn = np.stack([np.bincount(i, w0 * w0 * lv.N[j, k], n) for k in range(3)], 1)
            mw2 = np.bincount(i, w0 * w0, n)
            coh = smoothstep(np.linalg.norm(mn, axis=1) / np.maximum(mw2, 1e-30) / FIELD["coh"])
            nt = U(mn)
            s_ = smoothstep(((lv.N[j] * nt[i]).sum(1) - a0) / (a1 - a0))
            w = w0 * (1.0 - coh[i] * (1.0 - s_))
            Wt[idx] = np.bincount(i, w, n)
            for k in range(k_):
                S[idx, k] = np.bincount(i, w * lv.C[j, k], n)
        return S, Wt

    def at_points(self, Y):
        """[n,12] at arbitrary points (no lattice): the mapped point x' (3) and the blended gradient F (9)."""
        Y = np.asarray(Y, np.float64)
        c, jn = self.fine.tree.query(Y)
        r = self.radius(c)
        lo, hi = FIELD["coarse_r"]
        t = smoothstep((r - lo) / (hi - lo))
        C = np.zeros((len(Y), 12))
        for lv, wt in ((self.fine, 1 - t), (self.coarse, t)):
            a = wt > 0
            if not a.any():
                continue
            S, W = self._blend(lv, Y[a], c[a], r[a])
            S = np.where(W[:, None] > 0, S / np.maximum(W, 1e-30)[:, None], self.fine.C[jn[a]])
            C[a] += wt[a][:, None] * S
        F = C[:, 3:].reshape(-1, 3, 3)
        return np.hstack([C[:, :3] + np.einsum("nij,nj->ni", F, Y), C[:, 3:]])

    # ------------------------------------------------------------------ the lattice
    @staticmethod
    def _key(I):
        o = 1 << 20
        return ((I[:, 0] + o) << 42) | ((I[:, 1] + o) << 21) | (I[:, 2] + o)

    def _nodes(self, keys):
        """Lattice values at keys (computed and cached on first use)."""
        u = np.unique(keys)
        miss = u[~np.isin(u, self.keys)] if len(self.keys) else u
        if len(miss):
            o = 1 << 20
            I = np.stack([(miss >> 42) - o, ((miss >> 21) & ((1 << 21) - 1)) - o, (miss & ((1 << 21) - 1)) - o], 1)
            vals = self.at_points(I * self.g)
            k = np.concatenate([self.keys, miss])
            v = np.vstack([self.vals, vals])
            s = np.argsort(k)
            self.keys, self.vals = k[s], v[s]
        return self.vals[np.searchsorted(self.keys, keys)]

    def __call__(self, X):
        """(x' [n,3], J [n,3,3]) at bind-side points X: each lattice corner's map carried to X by its own gradient
        (x'_c + F_c (X - y_c)), blended trilinearly (exact for an affine move). J is the map's own Jacobian there (the
        blended gradients plus the trilinear weights' gradients times the corner maps: where the body's move is not
        affine within the kernel, e.g. two walls of a cleft closing in, the second term is what the field does), so the
        normals (J^-T) and the expected stretch see the deformation the field really applies."""
        X = np.asarray(X, np.float64)
        if self.zero or not len(X):
            return X.copy(), np.tile(np.eye(3), (len(X), 1, 1))
        s = X / self.g
        I0 = np.floor(s).astype(np.int64)
        f = s - I0
        Xn = np.zeros_like(X)
        J = np.zeros((len(X), 3, 3))
        for cx in (0, 1):
            for cy in (0, 1):
                for cz in (0, 1):
                    o = np.array([cx, cy, cz])
                    val = self._nodes(self._key(I0 + o))
                    fw = np.where(o == 1, f, 1 - f)
                    w = fw.prod(1)
                    # d w / d X: one factor differentiated (+-1/g), the other two kept
                    dw = np.stack([np.where(o[k] == 1, 1.0, -1.0) / self.g * np.delete(fw, k, 1).prod(1) for k in range(3)], 1)
                    Fc = val[:, 3:].reshape(-1, 3, 3)
                    xc = val[:, :3] + np.einsum("nij,nj->ni", Fc, X - (I0 + o) * self.g)
                    Xn += w[:, None] * xc
                    J += w[:, None, None] * Fc + xc[:, :, None] * dw[:, None, :]
        return Xn, J

    def gradient(self, X):
        """[n,3,3] the body's own deformation over the kernel's footprint at bind-side points X (the corners' blended
        gradients, trilinear): what the field asks of a piece edge there. Unlike the map's Jacobian it has no
        trilinear-weight term, so where the body's move is far from affine within the kernel (a smaller foot's toe
        tip seen from the boot's toe box) it does not fold to nothing."""
        X = np.asarray(X, np.float64)
        if self.zero or not len(X):
            return np.tile(np.eye(3), (len(X), 1, 1))
        s = X / self.g
        I0 = np.floor(s).astype(np.int64)
        f = s - I0
        F = np.zeros((len(X), 3, 3))
        for cx in (0, 1):
            for cy in (0, 1):
                for cz in (0, 1):
                    o = np.array([cx, cy, cz])
                    w = np.where(o == 1, f, 1 - f).prod(1)
                    F += w[:, None, None] * self._nodes(self._key(I0 + o))[:, 3:].reshape(-1, 3, 3)
        return F


_CACHE = {}


def field_for(body, bbody):
    """The field for this body pair (one cached pair per tier: a build evaluates every unit on one body)."""
    key = (id(body), id(bbody))
    f = _CACHE.get(key)
    if f is None:
        for k in [k for k in _CACHE if k[1] == id(bbody) or k[0] == id(body)]:
            del _CACHE[k]
        f = _CACHE[key] = Field(body, bbody)
    return f


# ---------------------------------------------------------------------- clearance

def signed_clear(body, X, k=8):
    """(signed distance to the body's surface, the push direction there): the sign and direction from the body's
    vertex normals interpolated at the closest point (a face normal at an edge or a corner can flip the sign)."""
    q, fn, t, d = body.surf.closest(X, k=k)
    Tv = body.T[t]
    v0, v1, v2 = body.V[Tv[:, 0]], body.V[Tv[:, 1]], body.V[Tv[:, 2]]
    e0, e1, e2 = v1 - v0, v2 - v0, q - v0
    d00, d01, d11 = (e0 * e0).sum(1), (e0 * e1).sum(1), (e1 * e1).sum(1)
    d20, d21 = (e2 * e0).sum(1), (e2 * e1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-30)
    b1 = (d11 * d20 - d01 * d21) / den
    b2 = (d00 * d21 - d01 * d20) / den
    n = U((1 - b1 - b2)[:, None] * body.N[Tv[:, 0]] + b1[:, None] * body.N[Tv[:, 1]] + b2[:, None] * body.N[Tv[:, 2]])
    return d * np.sign(((X - q) * n).sum(1) + 1e-15), n


def clear_push(body, X, c_req, sel, rounds=4, tol=2e-4):
    """X moved so that each selected vertex's signed clearance on body is at least c_req: each deficit is a smooth bump
    along the new skin's normal (its depth m at the vertex, falling to 0 over a radius that grows with the depth and the
    clearance: PUSH_SLOPE depth, so the push leans the piece out instead of denting it), the vertices taking the largest
    bump over them (never less than their own deficit), in rounds until clear. Returns (X, stats)."""
    X = X.copy()
    sel = np.where(sel)[0]
    st = {"pushed": 0, "max_push_mm": 0.0, "left_mm": 0.0}
    if not len(sel):
        return X, st
    lo, hi = FIELD["push_m"]
    base = np.clip(0.5 * np.abs(c_req[sel]) + lo, lo, hi)
    total = np.zeros((len(sel), 3))
    c, fn = signed_clear(body, X[sel])
    for it in range(rounds + 1):
        Xs = X[sel]
        dfc = c_req[sel] - c
        bad = dfc > tol
        if not bad.any() or it == rounds:
            st["left_mm"] = round(float(max(dfc.max(), 0.0)) * 1000, 3)
            break
        b = np.where(bad)[0]
        m = dfc[b] + tol
        rad = np.clip(np.maximum(base[b], FIELD["push_slope"] * m), lo, FIELD["push_max_m"])
        # bumps: the deepest deficit per cell of a quarter radius (the rounds take any left between)
        cell = np.floor(Xs[b] / (0.25 * rad[:, None])).astype(np.int64)
        key = np.c_[cell, np.round(np.log2(rad / lo) * 4).astype(np.int64)]
        order = np.lexsort((-m,) + tuple(key.T[::-1]))
        ks = key[order]
        first = np.r_[True, (ks[1:] != ks[:-1]).any(1)]
        kb = order[first]
        bx, bm, br, bn = Xs[b][kb], m[kb], rad[kb], fn[b][kb]
        sm = cKDTree(bx).sparse_distance_matrix(cKDTree(Xs), float(br.max()), output_type="ndarray")
        k, i, dist = sm["i"].astype(np.int64), sm["j"].astype(np.int64), sm["v"]
        del sm
        ok = dist < br[k]
        k, i, dist = k[ok], i[ok], dist[ok]
        h = bm[k] * wendland(dist / br[k])
        n = len(sel)
        p = np.zeros(n)
        np.maximum.at(p, i, h)
        # the push direction: the bumps' skin normals averaged by their kernels (not the deepest one's alone: across a
        # crease or a cleft the closest skin flips side between neighbours, and so would a per-vertex normal), the
        # depth divided by its cosine to the vertex's own skin normal so the clearance is met
        d = U(np.stack([np.bincount(i, h * bn[k, a], n) for a in range(3)], 1))
        cos = np.maximum((d * fn).sum(1), FIELD["push_cos"])
        mv = (p / cos)[:, None] * d
        X[sel] += mv
        total += mv
        moved = np.where(p > 0)[0]
        c[moved], fn[moved] = signed_clear(body, X[sel[moved]])
    pn = np.linalg.norm(total, axis=1)
    st["pushed"] = int((pn > 1e-7).sum())
    st["max_push_mm"] = round(float(pn.max()) * 1000, 3)
    return X, st


def hold_clear(body, X, c_req, sel):
    """X with each selected vertex near the bind skin moved along the new skin's normal to its bind clearance c_req (in
    or out: the tight set keeps its offset), by the weight 1 within HOLD in_m of the skin, 0 past in_m + fade_m."""
    X = X.copy()
    w = 1.0 - smoothstep((np.abs(c_req) - HOLD["in_m"]) / HOLD["fade_m"])
    idx = np.where(sel & (w > 0))[0]
    st = {"held": int(len(idx)), "hold_max_mm": 0.0}
    if not len(idx):
        return X, st
    total = np.zeros(len(idx))
    for r in range(HOLD["rounds"]):
        c, n = signed_clear(body, X[idx])
        # (the later rounds refine only the full-weight vertices: a partial weight is applied once)
        wr = w[idx] if r == 0 else (w[idx] >= 1.0).astype(np.float64)
        dlt = wr * (c_req[idx] - c)
        # the direction: the skin normals averaged over the neighbours (over a cleft the closest skin flips side)
        Y = X[idx]
        sm = cKDTree(Y).sparse_distance_matrix(cKDTree(Y), HOLD["dir_m"], output_type="ndarray")
        a_, b_, dd = sm["i"].astype(np.int64), sm["j"].astype(np.int64), sm["v"]
        kw = wendland(dd / HOLD["dir_m"])
        mn = np.stack([np.bincount(a_, kw * n[b_, k], len(idx)) for k in range(3)], 1) / np.bincount(a_, kw, len(idx))[:, None]
        d = U(mn + 1e-9 * n)
        cos = np.maximum((d * n).sum(1), HOLD["cos"])
        # in a cleft (neighbours' skin normals disagree: a strap between two walls that close in) a clearance from both
        # walls cannot be held without crushing the part; there the one-sided push keeps it out instead
        coh = smoothstep((np.linalg.norm(mn, axis=1) - HOLD["coh"][0]) / (HOLD["coh"][1] - HOLD["coh"][0]))
        if r == 0:
            w[idx] *= coh
            dlt *= coh
        # the correction itself averaged over the same neighbours (its weight falls off with the bind clearance, which
        # can change fast across a part in a crease: unsmoothed, neighbours would be moved apart)
        if HOLD["smooth"]:
            dlt = np.bincount(a_, kw * dlt[b_], len(idx)) / np.bincount(a_, kw, len(idx))
        X[idx] += (dlt / cos)[:, None] * d
        total += dlt
    st["hold_max_mm"] = round(float(np.abs(total).max()) * 1000, 3)
    return X, st


# ---------------------------------------------------------------------- the follow solve (round 3)
# One smooth correction over a tier's bendy piece meshes together (replaces round 2's hold and bump push): unknowns the
# piece positions X; energy  w_e sum_e k_e |x_b - x_a - G_e e0|^2   (each edge keeps the field's expected deformation of
# its bind edge: the stretch gate's own target, so the field's lattice ripples are ironed out and a correction cannot tear)
#   + bend^2 (X - Y)^T K M^-1 K (X - Y)   (the correction is smooth: bumps, not dents)
#   + sum_i A_i |X_i - Y_i|^2 / data^2   (the field's result kept, weakly)
# under clearance constraints along the new skin's normal (the tight set at its her_b clearance two-sided, the rest no
# nearer than push_req; a tight vertex in a cleft one-sided), each linearized at the closest skin point and re-linearized
# per round, solved by ADMM (one sparse factorization per round, the constraint planes projected per iteration).
SOLVE = {
    "data_m": 0.02,       # the field's result is kept at wavelengths over this
    "bend_m": 0.006,      # the correction is smooth under this
    "gamma": 1.0,         # constraint penalty, times the system's own diagonal (a broad push is met; a lone vertex
                          # meets a share of it: no spikes)
    "rounds": 4,          # re-linearizations (closest skin points)
    "iters": 25,          # local-global iterations per round
    "reach_m": 0.04,      # the system spans the vertices this near an active one (bind space)
    "margin_m": 0.0002,   # a one-sided limit is aimed this far past (the penalty's residual)
    "glue_m": 0.002,      # components within this of each other in bind space are tied by edges (stitches, trims)
    "edge_floor_m": 2e-4,
    "cleft": 0.75,        # neighbours' mean skin normal length under which a tight vertex is in a cleft (one-sided)
    "cleft_m": 0.008,
    "band_m": 0.0004,     # the tight set is held within this of its bind clearance (not exactly: the two bodies' facets)
    "hold_m": 0.0015,
    "smooth_m": 0.004,    # the two-sided correction's smoothing radius     # a tight vertex is held two-sided only when the field left it this near its bind clearance
    "side_cos": 0.3,      # the closest skin's normal . the carried bind normal under this: the far side (march instead)
    "march_m": 0.0005, "march_n": 50,    # the tight set is held within this of its bind clearance (not exactly: the two bodies' facets)
    "target": "G",        # the edges' target deformation: "Gk" the body's over the kernel (Field.gradient), "G" the map's
}


def _tri_edges(T):
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    e = np.sort(e, 1)
    e = e[e[:, 0] != e[:, 1]]
    return np.unique(e, axis=0)


def _factor(M):
    """A sparse SPD factorization: SuperLU in symmetric mode (fast), checked on a probe; if the probe's residual says the
    unpivoted factors lost accuracy (a near-singular corner of the ordering), the pivoting factorization instead."""
    from scipy.sparse.linalg import splu
    M = M.tocsc()
    lu = splu(M, permc_spec="MMD_AT_PLUS_A", diag_pivot_thresh=0.0, options={"SymmetricMode": True})
    p = np.random.default_rng(0).standard_normal(M.shape[0])
    x = lu.solve(p)
    if np.isfinite(x).all() and np.linalg.norm(M @ x - p) <= 1e-8 * np.linalg.norm(p):
        return lu
    return splu(M, permc_spec="COLAMD")


def follow_solve(body, Y, Xb, T, G, Gk, c0, n0, sel, stats=None):
    """Y (the field's result, one tier's meshes stacked) corrected on body as one smooth surface: see SOLVE. Xb the bind
    positions, T the stacked triangles, G the edges' target deformation per vertex, Gk the body's (Field.gradient: it
    carries the bind normal), c0 the bind clearance, n0 the bind
    skin's normal there, sel the bendy vertices. A vertex whose new closest skin is not on its bind side (it is inside,
    or the closest skin faces away from its bind normal carried by Gk: the far side of a thin toe, the other wall of a
    cleft) is moved along that carried normal, as far as it takes to clear (marched), never through the nearest wall.
    Returns (X, stats)."""
    from scipy import sparse
    from scipy.sparse.csgraph import connected_components
    from scipy.sparse.linalg import splu
    st = {"n": 0}
    idx = np.where(sel)[0]
    n = len(idx)
    if not n:
        return Y, st
    loc = -np.ones(len(Y), np.int64)
    loc[idx] = np.arange(n)
    T = loc[T[sel[T].all(1)]]
    P0, Y0, Gs, c0s = Xb[idx], Y[idx], G[idx], c0[idx]
    nb = U(np.linalg.solve(np.transpose(Gk[idx], (0, 2, 1)), n0[idx][:, :, None])[:, :, 0])   # the bind side, carried
    A = vertex_areas(P0, T) if len(T) else np.zeros(n)
    A = np.maximum(A, 0.2 * (np.median(A[A > 0]) if (A > 0).any() else 1e-6))
    E = _tri_edges(T) if len(T) else np.zeros((0, 2), np.int64)
    # glue: separate components close in bind space move together (a stitch on its leather)
    if len(E):
        ncomp, lab = connected_components(sparse.coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), (n, n)), directed=False)
    else:
        ncomp, lab = n, np.arange(n)
    if ncomp > 1:
        # each vertex to its nearest vertex of another component within glue_m (one tie each: no fill)
        kq = min(12, n)
        dq, jq = cKDTree(P0).query(P0, k=kq, distance_upper_bound=SOLVE["glue_m"])
        jq = np.where(np.isfinite(dq), jq, -1)
        other = (jq >= 0) & (lab[np.maximum(jq, 0)] != lab[:, None])
        has = other.any(1)
        first = np.argmax(other, 1)
        pr = np.c_[np.where(has)[0], jq[has, first[has]]]
        pr = np.unique(np.sort(pr, 1), axis=0) if len(pr) else pr.reshape(0, 2)
        st["glue"] = int(len(pr))
        E = np.vstack([E, np.sort(pr, 1)]) if len(pr) else E
    a, b = E[:, 0], E[:, 1]
    e0 = P0[b] - P0[a]
    l2 = (e0 * e0).sum(1)
    # coincident / tiny edges (split normals, welded seams) tied, not stiffer than a short edge: a huge 1/l^2 makes the
    # system ill-conditioned (and the bending term squares it)
    l2 = np.maximum(l2, max(SOLVE["edge_floor_m"], 0.3 * float(np.sqrt(np.median(l2[l2 > 0])) if (l2 > 0).any() else 0.0)) ** 2)
    k = (A[a] + A[b]) / (3.0 * l2)
    t = 0.5 * np.einsum("nij,nj->ni", Gs[a] + Gs[b], e0)
    K = sparse.coo_matrix((np.r_[-k, -k], (np.r_[a, b], np.r_[b, a])), (n, n)).tocsr()
    K = (K - sparse.diags(np.asarray(K.sum(1)).ravel())).tocsr()       # PSD: diag sum k, off -k
    f = np.zeros((n, 3))
    for ax in range(3):
        f[:, ax] = np.bincount(b, k * t[:, ax], n) - np.bincount(a, k * t[:, ax], n)
    Bd = (K @ sparse.diags(1.0 / A) @ K).tocsr() * SOLVE["bend_m"] ** 2
    Md = sparse.diags(A / SOLVE["data_m"] ** 2)
    S = (K + Bd + Md).tocsr()
    rhs0 = f + Bd @ Y0 + Md @ Y0
    diag = S.diagonal()
    X = Y0.copy()
    act = np.zeros(n, bool)
    req1 = push_req(c0s)
    tight = np.abs(c0s) < HOLD["in_m"]
    lim = np.where(tight, c0s, req1)
    st.update(n=n, rounds=0, marched=0)
    tree0 = cKDTree(P0)
    for r in range(SOLVE["rounds"]):
        c, nn = signed_clear(body, X, k=16)
        # clefts: the neighbours' skin normals disagree (the closest skin flips side): a tight vertex there one-sided
        cl = np.zeros(n, bool)
        if tight.any():
            ti = np.where(tight)[0]
            sm = cKDTree(X[ti]).sparse_distance_matrix(cKDTree(X[ti]), SOLVE["cleft_m"], output_type="ndarray")
            i_, j_, d_ = sm["i"].astype(np.int64), sm["j"].astype(np.int64), sm["v"]
            kw = wendland(d_ / SOLVE["cleft_m"])
            mn = np.stack([np.bincount(i_, kw * nn[ti[j_], q], len(ti)) for q in range(3)], 1)
            mn /= np.maximum(np.bincount(i_, kw, len(ti)), 1e-30)[:, None]
            cl[ti] = np.linalg.norm(mn, axis=1) < SOLVE["cleft"]
        # the constraint plane (x - X) . d = off (two-sided, within band) or >= off: d the closest skin's normal, except
        # for a vertex inside the new skin whose closest skin is not on its bind side (the far side of a thin toe):
        # there the carried bind normal, as far along it as it takes to clear (marched)
        d = nn.copy()
        off = lim - c
        amb = (c < np.minimum(lim, 0.0)) & ((nn * nb).sum(1) < SOLVE["side_cos"])
        if amb.any():
            ai = np.where(amb)[0]
            ss = np.arange(1, SOLVE["march_n"] + 1) * SOLVE["march_m"]
            Q = X[ai][:, None, :] + ss[None, :, None] * nb[ai][:, None, :]
            cq, _ = signed_clear(body, Q.reshape(-1, 3), k=16)
            okq = cq.reshape(len(ai), -1) >= lim[ai][:, None]
            first = np.where(okq.any(1), np.argmax(okq, 1), len(ss) - 1)
            d[ai] = nb[ai]
            off[ai] = ss[first]
            st["marched"] += int(amb.sum())
        # two-sided only where the field is near its bind clearance (a tight vertex far off it has its closest skin
        # elsewhere: across a crease or a fold; pulling it in would tear it from its neighbours): one-sided there
        eq = tight & ~cl & ~amb & (np.abs(off) < SOLVE["hold_m"])
        viol = np.where(eq, np.abs(off) > SOLVE["band_m"], off > 0)
        act |= viol
        if not act.any():
            break
        # the system over the vertices near the active ones (the rest stay on the field)
        free = np.zeros(n, bool)
        for lst in tree0.query_ball_point(P0[act], SOLVE["reach_m"]):
            free[lst] = True
        fi, bi = np.where(free)[0], np.where(~free)[0]
        Sff = S[fi][:, fi]
        rhs = rhs0[fi] - (S[fi][:, bi] @ X[bi] if len(bi) else 0.0)
        rho = np.where(act[fi], SOLVE["gamma"] * diag[fi], 0.0)
        lu = _factor(Sff + sparse.diags(rho))
        base, df, of_, eqf, af = X[fi].copy(), d[fi], off[fi], eq[fi], act[fi]
        hb = 0.5 * SOLVE["band_m"]
        # the two-sided correction is smoothed over the held neighbours (bind space): the two bodies' facets put a
        # few tenths of a mm of noise in each clearance, which a per-vertex hold would print into short edges
        ei = np.where(eqf)[0]
        Ws = None
        if len(ei):
            sm = cKDTree(P0[fi[ei]]).sparse_distance_matrix(cKDTree(P0[fi[ei]]), SOLVE["smooth_m"], output_type="ndarray")
            i_, j_ = sm["i"].astype(np.int64), sm["j"].astype(np.int64)
            # only neighbours whose plane faces the same way (across a cleft the closest skin flips side)
            ws_ = wendland(sm["v"] / SOLVE["smooth_m"]) * ((df[ei[i_]] * df[ei[j_]]).sum(1) > 0.5)
            Ws = sparse.coo_matrix((ws_, (i_, j_)), (len(ei), len(ei))).tocsr()
            Ws = sparse.diags(1.0 / np.maximum(np.asarray(Ws.sum(1)).ravel(), 1e-30)) @ Ws
            # the target offsets smoothed once per round (a fixed plane each: the local step stays a projection)
            of_ = of_.copy()
            of_[ei] = Ws @ of_[ei]
        Xf = X[fi]
        for it in range(SOLVE["iters"]):
            # local: each active vertex to its constraint (a penalty, not exact: a lone vertex cannot spike out)
            h = ((Xf - base) * df).sum(1) - of_
            h = np.where(eqf, np.sign(h) * np.maximum(np.abs(h) - hb, 0.0), np.minimum(h - SOLVE["margin_m"], 0.0))
            z = Xf - (h * af)[:, None] * df
            Xf = lu.solve(rhs + rho[:, None] * z)
        X[fi] = Xf
        st["rounds"] = r + 1
        st["free"] = max(st.get("free", 0), int(len(fi)))
    c, _ = signed_clear(body, X, k=16)
    st["active"] = int(act.sum())
    st["left_mm"] = round(float(max(0.0, (req1 - c)[~tight].max() if (~tight).any() else 0.0)) * 1000, 3)
    st["tight_p95_mm"] = round(float(np.percentile(np.abs(c - c0s)[tight], 95)) * 1000, 3) if tight.any() else None
    st["max_move_mm"] = round(float(np.linalg.norm(X - Y0, axis=1).max()) * 1000, 3)
    out = Y.copy()
    out[idx] = X
    return out, st


def similarity_fit(A, B, wt=None):
    """(M [3,3], ca, cb, s, P): the best X -> M (X - ca) + cb taking points A onto B with M = R P diag(s) P^T, P the
    principal axes of A (no shear), each scale s clamped to RIGID "scale" and pulled lightly toward 1 where A barely
    spans that axis (a plate's thickness). Alternating: Kabsch for R at the scales, then each axis' least squares."""
    w = np.ones(len(A)) if wt is None else wt
    ca = (w[:, None] * A).sum(0) / w.sum()
    cb = (w[:, None] * B).sum(0) / w.sum()
    a, b = A - ca, B - cb
    C = (w[:, None] * a).T @ a
    ev_, P = np.linalg.eigh(C)
    P = P[:, ::-1]
    if np.linalg.det(P) < 0:
        P[:, 2] *= -1
    lo, hi = RIGID["scale"]
    x = a @ P
    sxx = (w[:, None] * x * x).sum(0)
    lam = RIGID["reg"] * sxx.max()
    s = np.ones(3)
    R = np.eye(3)
    for _ in range(RIGID["iters"]):
        S = P @ np.diag(s) @ P.T
        H = (w[:, None] * (a @ S.T)).T @ b
        u, _, vt = np.linalg.svd(H)
        d = np.sign(np.linalg.det(vt.T @ u.T))
        R = vt.T @ np.diag([1, 1, d]) @ u.T
        y = b @ R @ P
        s_new = np.clip(((w[:, None] * y * x).sum(0) + lam) / (sxx + lam), lo, hi)
        if np.abs(s_new - s).max() < 1e-7:
            s = s_new
            break
        s = s_new
    M = R @ P @ np.diag(s) @ P.T
    return M, ca, cb, s, P


def min_translation(fn, short, iters=400):
    """A small translation t with fn_i . t >= short_i for all i (cyclic projections onto the violated half-spaces)."""
    t = np.zeros(3)
    for _ in range(iters):
        v = short - fn @ t
        k = int(np.argmax(v))
        if v[k] <= 1e-7:
            break
        t = t + v[k] * fn[k]
    return t


def rigid_clear(body, Xs, c_req):
    """One translation for a rigid group (its placed points Xs, their bind clearances): the smallest that keeps every
    point that was clear on the bind body out of the new skin. (Kept for a group without a fit; rigid_fit_clear is the
    made-to-measure path.)"""
    c, fn = signed_clear(body, Xs)
    need = np.where(c_req >= 0, np.maximum(0.0, -c) + 1e-4, 0.0)
    m = need > 1e-4 + 1e-9
    if not m.any():
        return np.zeros(3)
    return min_translation(fn[m], need[m])


def rigid_fit_clear(body, A, B, Ag, c_req):
    """A rigid group made to measure and cleared: the similarity fit of its leader's bind points A onto their followed
    points B (similarity_fit), then the smallest change of translation and per-axis scales (an LP: L1 of the translation
    + RIGID "clear_w" x the scales' change, the scales kept in their clamp) that puts every point of the group Ag that was
    clear on the bind body at least min(its bind clearance, RIGID "clear_m") out of the new skin, linearized and
    re-measured over a few rounds. A plate that wraps the body (front, sides) cannot clear by one translation; a scale can.
    Returns (M, ca, cb, info)."""
    from scipy.optimize import linprog
    M, ca, cb, s, P = similarity_fit(A, B)
    R = M @ P @ np.diag(1.0 / s) @ P.T
    lo, hi = RIGID["scale"]
    t = np.zeros(3)
    x = (Ag - ca) @ P
    ok_req = c_req >= 0
    tgt = np.minimum(c_req, RIGID["clear_m"])
    info = {"scale_fit": [round(float(v), 4) for v in s], "rounds": 0, "left_mm": 0.0}
    for r in range(RIGID["clear_rounds"] + 1):
        Mr = R @ P @ np.diag(s) @ P.T
        Y = (Ag - ca) @ Mr.T + cb + t
        c, fn = signed_clear(body, Y)
        need = tgt - c
        info["left_mm"] = round(float(max(0.0, need[ok_req].max() if ok_req.any() else 0.0)) * 1000, 3)
        m = ok_req & (need > -RIGID["near_m"])
        if not (need[m] > 1e-5).any() or r == RIGID["clear_rounds"]:
            break
        gs = x[m] * (fn[m] @ R @ P)          # d(fn . Y) / d s_k
        G = np.hstack([fn[m], gs])
        cw = np.r_[np.ones(3), RIGID["clear_w"] * np.ones(3)]
        # v = v+ - v-, both >= 0; G v >= need  ->  -G v+ + G v- <= -need
        res = linprog(np.r_[cw, cw], A_ub=np.hstack([-G, G]), b_ub=-(need[m] + 2e-5),
                      bounds=[(0, None)] * 3 + [(0, max(0.0, hi - v)) for v in s] + [(0, None)] * 3
                      + [(0, max(0.0, v - lo)) for v in s], method="highs")
        if res.status != 0:
            # infeasible within the clamp: the translation alone (cyclic projections), the row is flagged by its numbers
            bad = m & (need > 0)
            t = t + min_translation(fn[bad], need[bad])
            info["lp"] = "infeasible"
            continue
        v = res.x[:6] - res.x[6:]
        t = t + v[:3]
        s = np.clip(s + v[3:], lo, hi)
        info["rounds"] = r + 1
    M = R @ P @ np.diag(s) @ P.T
    info.update(scale=[round(float(v), 4) for v in s], clear_mm=round(float(np.linalg.norm(t)) * 1000, 2))
    return M, ca, cb + t, info


# ---------------------------------------------------------------------- test bodies

SLIDER_TESTS = (("weight", 1.0), ("bust_size", 1.0), ("hips", 1.0), ("height", 1.0), ("build", -1.0))


def slider_body(bind_bodies, name, value, spec="tools/body/specs/her_b.json"):
    """{tier: Body}: the bind body (her_b) with one slider moved from her spec's value to `value`, laid as build_topo's
    stage_base lays a slider (its move less the neck band's shift, times the join weight: none at the head's seam), and
    the whole body moved rigidly so her soles stay where they were (build_topo.ground_offset: the head moves with it)."""
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(os.path.dirname(here))
    for p in (os.path.join(repo, "tools", "body"), os.path.join(repo, "tools", "anim")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import build_topo as bt
    from sliders import load_spec
    sp = bt.with_defaults(load_spec(os.path.join(repo, spec)))
    her = float(sp.get("sliders", {}).get(name, 0.0) or 0.0)
    out, dy = {}, None
    from sliders import OurSliders
    from scipy.spatial import cKDTree as _T
    for tier in ("close", "play"):
        sl = OurSliders(os.path.join(repo, "tools", "body", "base", f"sliders_{tier}.npz"))
        V0 = sl.V0
        d = sl.delta(name, value) - sl.delta(name, her)
        # build_topo.join_weight on the topology's triangles (its quads live in a git-ignored build folder)
        Tt = bind_bodies[tier].T[:bind_bodies[tier].ntri_t]
        e = np.sort(np.concatenate([Tt[:, [0, 1]], Tt[:, [1, 2]], Tt[:, [2, 0]]]), 1)
        u, cnt = np.unique(e, axis=0, return_counts=True)
        ring = np.unique(u[cnt == 1])
        assert len(ring) == 94, ("the open neck ring", tier, len(ring))
        jw = bt.s01((bt.split_depth(V0) - bt.HOLD_M) / bt.EASE_M)
        if sp.get("join", "split") == "ring":
            jw = np.maximum(jw, bt.s01((_T(V0[ring]).query(V0)[0] - bt.HOLD_M) / bt.EASE_M))
        jw = jw[:, None]
        dep = bt.split_depth(V0)
        t = d[(dep > 0) & (dep < 0.04)].mean(0)
        t[0] = 0.0
        b = bind_bodies[tier]
        assert len(V0) == b.nt, ("slider bake is not this body's topology", tier, len(V0), b.nt)
        Pt = b.V[:b.nt] + jw * (d - t)
        if dy is None:
            dy = float(b.V[:b.nt, 1].min() - Pt[:, 1].min())
        V = np.vstack([Pt, b.V[b.nt:]]) + np.array([0.0, dy, 0.0])
        out[tier] = b.with_points(V, f"{name}{value:+g}")
    return out


def expected_edges(bbody, body, tri, E, X0, beta_=None, G=None):
    """The body's own deformation applied to each piece edge (bind -> body, by the bound triangles' 3x3 gradients
    [e1 e2 n] -> [e1' e2' n'], the two ends' mean): the length a skin-tight piece edge would have. With the field's
    share beta_ and its blended gradient G per vertex: the deformation the follow asks of each vertex, (1 - beta) of the
    skin under it + beta of the field's (the body's gradient over the kernel's footprint)."""
    ut, inv = np.unique(tri, return_inverse=True)

    def M(b):
        Tv = b.T[ut]
        e1 = b.V[Tv[:, 1]] - b.V[Tv[:, 0]]
        e2 = b.V[Tv[:, 2]] - b.V[Tv[:, 0]]
        return np.stack([e1, e2, U(np.cross(e1, e2))], -1)
    Fm = M(body) @ np.linalg.inv(M(bbody))
    Fv = Fm[inv]
    if beta_ is not None:
        Fv = Fv + beta_[:, None, None] * (G - Fv)
    e = X0[E[:, 1]] - X0[E[:, 0]]
    v = 0.5 * (np.einsum("nij,nj->ni", Fv[E[:, 0]], e) + np.einsum("nij,nj->ni", Fv[E[:, 1]], e))
    return np.linalg.norm(v, axis=1)


def least_rotations(a, b):
    """[n,3,3] the smallest rotations taking unit vectors a onto b (Rodrigues; a = -b: none)."""
    v = np.cross(a, b)
    c = (a * b).sum(1)
    K = np.zeros((len(a), 3, 3))
    K[:, 0, 1], K[:, 0, 2], K[:, 1, 2] = -v[:, 2], v[:, 1], -v[:, 0]
    K[:, 1, 0], K[:, 2, 0], K[:, 2, 1] = v[:, 2], -v[:, 1], v[:, 0]
    f = np.where(c > -1 + 1e-9, 1.0 / np.maximum(1 + c, 1e-9), 0.0)
    return np.eye(3)[None] + K + (K @ K) * f[:, None, None]


def exact_follow(X, F, Xb, Fb, off):
    """The bound evaluation made continuous across triangles: the bound point's move plus the bind offset turned by the
    least rotation of the interpolated (continuous) normal, not by each triangle's own tangent frame (which differs
    triangle to triangle). Returns (X', R [n,3,3]); on the bind body X' = Xb exactly."""
    o = off.astype(np.float64)
    p = X - np.einsum("nij,nj->ni", F, o)
    pb = Xb - np.einsum("nij,nj->ni", Fb, o)
    R = least_rotations(Fb[:, :, 2], F[:, :, 2])
    return p + np.einsum("nij,nj->ni", R, Xb - pb), R
