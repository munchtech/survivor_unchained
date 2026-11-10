"""The native armor builder (P2): a piece authored directly on her_b (godot/art/people/body_p1) as numpy, no Blender.

A piece is data: godot/art/gear/native/<id>/build.json names a recipe and its params. One command rebuilds the piece
dir that gear_native binds (the mesh at her rest, piece.json with its rest stamp and each rigid part's ride rule,
the sockets file):

    python tools/armor/native_build.py plate_cuisses_plain
    python tools/armor/gear_native.py validate godot/art/gear/native/plate_cuisses_plain
    python tools/armor/gear_native.py bind godot/art/gear/native/plate_cuisses_plain

Primitives (general to a limb or the head; every one works on any (points, triangles) body, see test_native_build):
    Ref            the body: surface, joints, a role's share of the skin (rigid_roles.json "roles")
    Frame          a frame on a bone or a landmark pair: (s along the axis, theta round it from the front, rho out);
                   hand = -1 mirrors it for her other side (every part is built on its own side of her)
    raycast        first hit of rays on a mesh; radial() = a surface's rho over an (s, theta) grid
    Law            a smooth Chebyshev law rho(s, theta) fitted ABOVE the skin (an envelope: her maximum + clear)
    edge_curve     a smooth edge s(theta) from control points, the skin a role owns, another piece's rim
    Sheet          a plate or a lame over an (s, theta) domain on a law: thickness, a ridge, a rolled edge on every
                   edge, an edge wall and a lip down to the skin, a lift over what it covers, a cap under what covers
                   it; vertex data for the gear shader (TEXCOORD_1 = edge distance, convexity; COLOR_0 = ao, random,
                   painted, flag 0 on a rolled edge / 1 on plate)
    skin_band      a strap that follows her skin along a path, climbing onto the plates it crosses (tab rows ride the
                   plate, the rest her skin)
    buckle, rivet  fixings on a point and a normal
    Part, write_piece   parts -> <id>.glb, piece.json, <id>.sockets.json
"""
import hashlib
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
NATIVE = os.path.join(REPO, "godot", "art", "gear", "native")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "body"))
MM = 0.001


def U(v):
    v = np.asarray(v, float)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- the body

class Ref:
    """A body as the builder reads it: V, T, vertex normals, joints {name: rest position}, dense weights by name."""

    def __init__(self, V, T, N=None, joints=None, joint_names=None, J=None, W=None, hashes=None, rest_body=None):
        self.V, self.T = np.asarray(V, float), np.asarray(T, np.int64)
        self.N = vertex_normals(self.V, self.T) if N is None else np.asarray(N, float)
        self.joints, self.joint_names, self.J, self.W = joints or {}, joint_names or [], J, W
        self.hashes, self.rest_body = hashes or {}, rest_body
        self._surf = None

    @classmethod
    def her(cls, body_dir=None):
        import gear_fit as g
        from gl import FileSkeleton, Glb
        body_dir = body_dir or g.BIND_BODY
        b = g.Body.load(body_dir, "close")
        sk = FileSkeleton(Glb(os.path.join(body_dir, "body.glb")))
        joints = {n: np.asarray(sk.head(i), float)[:3] for i, n in enumerate(sk.names)}
        hashes = {t: g.sha1(os.path.join(body_dir, "body.glb" if t == "close" else "play.glb")) for t in g.TIERS}
        r = cls(b.V, b.T, b.N, joints, list(b.joint_names), b.J, b.W, hashes, os.path.relpath(body_dir, REPO).replace("\\", "/"))
        r.body = b
        return r

    @property
    def surf(self):
        if self._surf is None:
            from surfdist import Surface
            self._surf = Surface(self.V, self.T)
        return self._surf

    def closest(self, X):
        """(point on the skin, unit outward normal there, distance) for each X."""
        q, _, tri, d = self.surf.closest(np.asarray(X, float), k=16)
        Tv = self.T[tri]
        w = bary(q, self.V[Tv[:, 0]], self.V[Tv[:, 1]], self.V[Tv[:, 2]])
        return q, U((self.N[Tv] * w[:, :, None]).sum(1)), d

    def share(self, role, side):
        """Per vertex: the share of its skin weights on a role's bones (rigid_roles.json "roles"), her `side` ('l'/'r')."""
        roles = json.load(open(os.path.join(HERE, "rigid_roles.json")))["roles"]
        pats = [p.replace("[lr]", side) for p in roles.get(role, [role])]
        cols = np.array([any(re.fullmatch(p, n) for p in pats) for n in self.joint_names])
        return (self.W * cols[self.J]).sum(1)


def bary(q, a, b, c):
    v0, v1, v2 = b - a, c - a, q - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-20)
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.c_[1 - v - w, v, w]


def vertex_normals(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros_like(P)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    return U(N)


# ---------------------------------------------------------------- frames, rays, laws

class Frame:
    """c + s * axis + rho * (cos(theta) front + sin(theta) side): theta 0 at the front, +90 at her outer side.
    hand -1 is the same frame on her right (side = -x)."""

    def __init__(self, c, tip, front=(0, 0, 1), hand=1):
        self.c, self.hand = np.asarray(c, float), hand
        a = np.asarray(tip, float) - self.c
        self.L = float(np.linalg.norm(a))
        self.a = a / self.L
        f = np.asarray(front, float)
        self.f = U(f - self.a * (f @ self.a))
        o = np.cross(self.a, self.f)
        self.o = o if o[0] * hand > 0 else -o

    @classmethod
    def bones(cls, ref, a, b, hand=1, front=(0, 0, 1)):
        return cls(ref.joints[a], ref.joints[b], front, hand)

    def radial(self, th):
        t = np.radians(np.asarray(th, float))[..., None]
        return np.cos(t) * self.f + np.sin(t) * self.o

    def pt(self, s, th, rho):
        return self.c + np.asarray(s, float)[..., None] * self.a + np.asarray(rho, float)[..., None] * self.radial(th)

    def cyl(self, P):
        d = np.asarray(P, float) - self.c
        x, y = d @ self.f, d @ self.o
        return d @ self.a, np.degrees(np.arctan2(y, x)), np.hypot(x, y)


def raycast(V, T, O, D, tmax=1.0, chunk=96):
    """First hit of each ray O + t D (unit D) on the mesh: (t, triangle), t = nan where none within tmax."""
    v0 = V[T[:, 0]]
    e1, e2 = V[T[:, 1]] - v0, V[T[:, 2]] - v0
    out_t, out_i = np.full(len(O), np.nan), np.full(len(O), -1)
    for a in range(0, len(O), chunk):
        o, d = O[a:a + chunk, None, :], D[a:a + chunk, None, :]
        h = np.cross(d, e2[None])
        det = (e1[None] * h).sum(-1)
        ok = np.abs(det) > 1e-14
        inv = 1.0 / np.where(ok, det, 1.0)
        sv = o - v0[None]
        u = (sv * h).sum(-1) * inv
        q = np.cross(sv, e1[None])
        v = (d * q).sum(-1) * inv
        t = (e2[None] * q).sum(-1) * inv
        hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-6) & (t < tmax)
        t = np.where(hit, t, np.inf)
        i = t.argmin(1)
        tt = t[np.arange(len(i)), i]
        out_t[a:a + chunk] = np.where(np.isfinite(tt), tt, np.nan)
        out_i[a:a + chunk] = np.where(np.isfinite(tt), i, -1)
    return out_t, out_i


def near(V, T, fr, s0, s1, rmax):
    """The triangles of a mesh inside a frame's can (s0..s1, rho < rmax): what its rays can meet."""
    s, _, rho = fr.cyl(V)
    ok = (s > s0) & (s < s1) & (rho < rmax)
    return T[ok[T].any(1)]


def radial(V, T, fr, s, th, rmax=0.3):
    """rho of a surface along the frame's rays from its axis (first hit; nan where none): shape broadcast(s, th);
    also the hit triangles (indices into T)."""
    s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
    t, i = raycast(V, T, (fr.c + s.reshape(-1, 1) * fr.a), fr.radial(th.reshape(-1)), rmax)
    return t.reshape(s.shape), i.reshape(s.shape)


class Law:
    """rho(s, theta) = a tensor Chebyshev series over [s0, s1] x [t0, t1] (clamped outside) + add."""

    def __init__(self, s0, s1, t0, t1, coef, add=0.0):
        self.dom, self.coef, self.add = (s0, s1, t0, t1), np.asarray(coef, float), add

    def basis(self, s, th):
        s0, s1, t0, t1 = self.dom
        x = np.clip(2 * (np.asarray(s, float) - s0) / (s1 - s0) - 1, -1, 1)
        y = np.clip(2 * (np.asarray(th, float) - t0) / (t1 - t0) - 1, -1, 1)
        C = np.polynomial.chebyshev
        return C.chebvander(x, self.coef.shape[0] - 1), C.chebvander(y, self.coef.shape[1] - 1)

    def __call__(self, s, th):
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        A, B = self.basis(s.reshape(-1), th.reshape(-1))
        return (np.einsum("ni,ij,nj->n", A, self.coef, B) + self.add).reshape(s.shape)

    def plus(self, d):
        return Law(*self.dom, self.coef, self.add + d)

    @classmethod
    def envelope(cls, s, th, rho, deg=(7, 7), dom=None, iters=40, over=30.0, soft=None):
        """The smooth law lying on or above every sample (s, th, rho): an asymmetric least-squares fit (a sample above
        the law weighs `over` times one below), then lifted by the last sample still above it. soft (bool per sample):
        skin no plate lies over; it guides the fit across the domain and never lifts the law."""
        s, th, rho = (np.asarray(v, float).reshape(-1) for v in (s, th, rho))
        hard = np.ones(len(s), bool) if soft is None else ~np.asarray(soft, bool).reshape(-1)
        ok = np.isfinite(rho)
        s, th, rho, hard = s[ok], th[ok], rho[ok], hard[ok]
        dom = dom or (s.min(), s.max(), th.min(), th.max())
        law = cls(*dom, np.zeros(deg))
        A, B = law.basis(s, th)
        M = np.einsum("ni,nj->nij", A, B).reshape(len(s), -1)
        w = np.ones(len(s))
        for _ in range(iters):
            c = np.linalg.lstsq(M * w[:, None], rho * w, rcond=None)[0]
            r = rho - M @ c
            w = np.where(hard, np.where(r > 0, np.sqrt(over), 1.0), 0.3)
        law.coef = c.reshape(deg)
        law.add = float(max(r[hard].max(), 0.0)) if hard.any() else 0.0
        law.rms = float(np.sqrt((r[hard] ** 2).mean())) if hard.any() else 0.0
        return law


def edge_curve(th, s, deg=4, side=0, dom=None):
    """A smooth edge s(theta): a polynomial through control points (least squares), lifted to lie on or past them all
    (side +1: s >= every point, -1: s <= every point, 0: the plain fit). Clamped outside its theta range."""
    th, s = np.asarray(th, float), np.asarray(s, float)
    t0, t1 = dom or (th.min(), th.max())
    x = lambda t: np.clip(2 * (np.asarray(t, float) - t0) / (t1 - t0) - 1, -1, 1)  # noqa: E731
    c = np.polynomial.chebyshev.chebfit(x(th), s, min(deg, len(th) - 1))
    r = s - np.polynomial.chebyshev.chebval(x(th), c)
    c[0] += r.max() if side > 0 else r.min() if side < 0 else 0.0
    return lambda t: np.polynomial.chebyshev.chebval(x(t), c)


def edge_points(th, s):
    """A smooth edge s(theta) THROUGH its control points: a C1 monotone cubic (no overshoot between points), clamped
    outside their theta range. An edge drawn where the measures say it must run (edge_curve is a fit, this is the line)."""
    th, s = np.asarray(th, float), np.asarray(s, float)
    o = np.argsort(th)
    th, s = th[o], s[o]
    h, d = np.diff(th), np.diff(s) / np.diff(th)
    m = np.zeros(len(th))
    m[0], m[-1] = d[0], d[-1]
    for k in range(1, len(th) - 1):   # (the harmonic mean of the two slopes, 0 where they change sign: Fritsch-Carlson)
        if d[k - 1] * d[k] > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])

    def f(t):
        t = np.clip(np.asarray(t, float), th[0], th[-1])
        k = np.clip(np.searchsorted(th, t, side="right") - 1, 0, len(th) - 2)
        x = (t - th[k]) / h[k]
        return ((2 * x ** 3 - 3 * x ** 2 + 1) * s[k] + (x ** 3 - 2 * x ** 2 + x) * h[k] * m[k]
                + (-2 * x ** 3 + 3 * x ** 2) * s[k + 1] + (x ** 3 - x ** 2) * h[k] * m[k + 1])
    return f


def owned_line(ref, fr, role, share, th, s_scan, rmax=0.3, last=False):
    """Where a role comes to own the skin along each theta: the first s (down the frame's axis) from which the role's
    share of the skin weights stays >= `share`. The line a rigid plate riding that role may start from. last: where
    it stops owning it instead (the last s of the scan before its share falls under `share`): where the plate ends."""
    Tn = near(ref.V, ref.T, fr, s_scan.min() - 0.05, s_scan.max() + 0.05, rmax)
    S, TH = np.meshgrid(s_scan, th, indexing="ij")
    _, i = radial(ref.V, Tn, fr, S, TH, rmax)
    w = ref.share(role, "l" if fr.hand > 0 else "r")
    wt = np.where(i >= 0, w[Tn[np.maximum(i, 0)]].mean(-1), 0.0)
    below = wt < share
    if last:
        return s_scan[np.maximum(np.where(below.any(0), below.argmax(0), len(s_scan)) - 1, 0)]
    last = np.where(below.any(0), len(s_scan) - 1 - below[::-1].argmax(0), -1)
    return s_scan[np.minimum(last + 1, len(s_scan) - 1)]


# ---------------------------------------------------------------- parts

class Part:
    """One node of the piece's mesh: a name (`*_rigid` never bends), a material, points, triangles, vertex data."""

    def __init__(self, name, material, P, T, uv0=None, uv1=None, col=None, N=None):
        n = len(P)
        self.name, self.material = name, material
        self.P, self.T = np.asarray(P, float), np.asarray(T, np.int64).reshape(-1, 3)
        self.uv0 = np.zeros((n, 2)) if uv0 is None else np.asarray(uv0, float)
        self.uv1 = np.tile([0.05, 0.5], (n, 1)) if uv1 is None else np.asarray(uv1, float)
        self.col = np.tile([1.0, 0.5, 0.0, 1.0], (n, 1)) if col is None else np.asarray(col, float)
        self.N = vertex_normals(self.P, self.T) if N is None else np.asarray(N, float)

    @staticmethod
    def join(name, material, parts):
        off = np.cumsum([0] + [len(p.P) for p in parts[:-1]])
        cat = lambda k: np.vstack([getattr(p, k) for p in parts])  # noqa: E731
        return Part(name, material, cat("P"), np.vstack([p.T + o for p, o in zip(parts, off)]), cat("uv0"), cat("uv1"),
                    cat("col"), cat("N"))

    def node(self):
        return {"name": self.name, "material": self.material, "P": self.P, "N": self.N, "T": self.T, "uv0": self.uv0,
                "uv1": self.uv1, "col": self.col}


def seat(part, ref, floor=0.0005):
    """No point of a part under her skin: any point closer than `floor` above it (or inside) moves out along the
    skin's normal to the floor. Returns how many moved."""
    q, n, _ = ref.closest(part.P)
    c = ((part.P - q) * n).sum(1)
    low = c < floor
    part.P[low] += n[low] * (floor - c[low])[:, None]
    if low.any():
        part.N = vertex_normals(part.P, part.T)
    return int(low.sum())


def rand01(name):
    return int(hashlib.sha1(name.encode()).hexdigest()[:6], 16) / 0xFFFFFF


def outward(P, T, D):
    """T wound so its faces look along D (per-vertex directions): flipped as a whole when most look the other way."""
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    return T if (fn * D[T].mean(1)).sum() >= 0 else T[:, ::-1]


def grid_tris(nr, nc, close=False):
    i, j = np.meshgrid(np.arange(nr - 1), np.arange(nc if close else nc - 1), indexing="ij")
    a, b = (i * nc + j).reshape(-1), (i * nc + (j + 1) % nc).reshape(-1)
    c, d = a + nc, b + nc
    return np.r_[np.c_[a, b, d], np.c_[a, d, c]]


ROLL_D = np.array([0.0, 0.133, 0.333, 0.667, 0.867, 1.0])      # a rolled edge's knots, in its widths from the edge
ROLL_B = np.sqrt(np.maximum(1 - (2 * ROLL_D - 1) ** 2, 0.0))   # ... and its bead there (a round)
RIDGE_X = np.array([-1.0, -0.4, -0.08, 0.0, 0.08, 0.4, 1.0])   # a ridge's knots across it, in half widths
RIDGE_H = np.array([0.0, 0.52, 0.96, 1.0, 0.96, 0.52, 0.0])    # a tent with a crisp crest: light splits on it


class Sheet:
    """A plate or a lame: the surface `law` + its height over the domain theta in [t0, t1], s in [top(th), bot(th)].

    thick; roll (width, height): a rolled edge on the edges named in `roll_on` ("t" top, "b" bottom, "0" / "1" the
    theta t0 / t1 side: an edge hidden under another plate takes none); ridge {theta, h, w, fade}; lift {band, h}:
    its last `band` before the bottom edge stands `h` further out (room for the lame under it); lift_top {band, h,
    ease, theta [a, b]}: its first `band` after the TOP edge stands `h` further out, easing back over `ease` (a lame
    that laps OVER the plate above it; theta: only from a on, in full from b; h a number, or h(s, theta): the room
    the plate beneath needs where the lame slides along it); cap(s, th) -> the rho its outer face
    must stay under (the plate or the cop that covers it); lip: how far above the law - `clear` its inner lip ends
    (the edge wall runs down to the skin, so no void shows under an edge; under a lifted edge it is the steel's own
    thickness and its lip turns in over the plate beneath; an edge with no roll, hidden under another plate, has no
    wall at all). t0 / t1: a number, or a line theta(s): a side edge that
    runs into the lames below it (a taper), never a step in the outline. ridge "stop": it has faded out this far
    before the bottom edge (the band hidden under the next lame). step / step_s: the mesh's spacing round the limb /
    down it (rows cluster only on a rolled edge)."""

    def __init__(self, fr, law, t0, t1, top, bot, thick, roll=(0.0045, 0.001), ridge=None, lift=None, cap=None,
                 clear=0.003, lip=0.0008, step=0.011, flare=None, roll_on="tb01", lift_top=None, step_s=None):
        self.fr, self.law, self.t0, self.t1, self.top, self.bot = fr, law, t0, t1, top, bot
        self.thick, self.roll, self.ridge, self.lift, self.cap, self.clear, self.lip, self.step, self.flare = \
            thick, roll, ridge, lift, cap, clear, lip, step, flare
        self.roll_on, self.lift_top, self.step_s = roll_on, lift_top, step_s or step

    def side(self, k, s):
        """The theta of its t0 (k = 0) / t1 (k = 1) side edge at s."""
        t = self.t1 if k else self.t0
        return np.asarray(t(s), float) if callable(t) else np.full(np.shape(s), float(t))

    def roll_d(self, s, th):
        """Distance to the nearest ROLLED edge (inf when none is)."""
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        d = np.full(s.shape, np.inf)
        R = self.law(s, th)
        for k, v in (("t", s - self.top(th)), ("b", self.bot(th) - s), ("0", np.radians(th - self.side(0, s)) * R),
                     ("1", np.radians(self.side(1, s) - th) * R)):
            if k in self.roll_on:
                d = np.minimum(d, v)
        return d

    def edge_d(self, s, th):
        """Distance to the nearest edge inside the domain (negative outside)."""
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        R = self.law(s, th)
        return np.minimum(np.minimum(s - self.top(th), self.bot(th) - s),
                          np.minimum(np.radians(th - self.side(0, s)), np.radians(self.side(1, s) - th)) * R)

    def height(self, s, th):
        """The outer face's height over the law at (s, theta): thickness, lift, flare, ridge and rolled edge."""
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        R = self.law(s, th)
        h = np.full(s.shape, self.thick)
        if self.lift:
            h = h + self.lift["h"] * smooth(1 - (self.bot(th) - s) / self.lift["band"])
        if self.flare:
            h = h + self.flare["h"] * smooth(1 - (self.bot(th) - s) / self.flare["band"])
        if self.lift_top:
            lt = self.lift_top
            k = smooth(1 - (s - self.top(th) - lt["band"]) / lt.get("ease", lt["band"]))
            if lt.get("theta"):
                k = k * smooth((th - lt["theta"][0]) / (lt["theta"][1] - lt["theta"][0]))
            h = h + (lt["h"](s, th) if callable(lt["h"]) else lt["h"]) * k
        if self.ridge:
            r = self.ridge
            x = np.radians(th - r["theta"]) * R / (r["w"] / 2)
            end = smooth(np.minimum(s - self.top(th), self.bot(th) - r.get("stop", 0.0) - s) / r["fade"])
            h = h + r["h"] * np.interp(x, RIDGE_X, RIDGE_H, left=0, right=0) * end
        if self.roll:
            d = self.roll_d(s, th) / self.roll[0]
            h = h + self.roll[1] * np.interp(d, ROLL_D, ROLL_B, left=0, right=0)
        if self.cap is not None:
            h = np.maximum(np.minimum(h, self.cap(s, th) - R), 0.4 * self.thick)
        return h

    def outer(self, s, th):
        return self.law(s, th) + self.height(s, th)

    def at(self, s, th, up=0.0):
        """A point on the outer face (+ up along its normal) and the unit normal there."""
        s, th = np.asarray(s, float), np.asarray(th, float)
        e = 0.0015
        P = self.fr.pt(s, th, self.outer(s, th))
        R = np.maximum(self.law(s, th), 1e-3)
        dt = np.degrees(e / R)
        ds = self.fr.pt(s + e, th, self.outer(s + e, th)) - self.fr.pt(s - e, th, self.outer(s - e, th))
        dth = self.fr.pt(s, th + dt, self.outer(s, th + dt)) - self.fr.pt(s, th - dt, self.outer(s, th - dt))
        n = U(np.cross(ds, dth))
        n = n * np.sign((n * self.fr.radial(th)).sum(-1, keepdims=True))
        return P + n * up, n

    def knots(self):
        """(S, TH) node grids: rows cluster on the top and bottom edges' roll, columns on the side edges' roll and
        the ridge, even between (about `step` apart)."""
        w = self.roll[0] if self.roll else 0.004
        dk = np.r_[ROLL_D * w, 1.25 * w]
        num = lambda t, s: float(t(s)) if callable(t) else float(t)  # noqa: E731
        tm, sm = 0.0, 0.0
        for _ in range(3):   # (the middle of a sheet whose sides are lines theta(s))
            tm = 0.5 * (num(self.t0, sm) + num(self.t1, sm))
            sm = 0.5 * float(self.top(tm) + self.bot(tm))
        Lm = float(self.bot(tm) - self.top(tm))
        Rm = float(self.law(sm, tm))
        dkt, dkb = (dk if "t" in self.roll_on else dk[:1]), (dk if "b" in self.roll_on else dk[:1])
        nv = max(int(round((Lm - dkt[-1] - dkb[-1]) / self.step_s)), 1)
        fixed = [(self.t0, +1, dk), (self.t1, -1, dk[::-1])]
        if self.ridge:
            fixed.insert(1, (self.ridge["theta"], +1, RIDGE_X * self.ridge["w"] / 2))
        ss = np.linspace(float(self.top(tm)), float(self.bot(tm)), 9)
        wide = lambda t: np.array([num(t, v) for v in ss])  # noqa: E731  (a side line's thetas down the sheet)
        # columns: [edge cluster | even | ridge cluster | even | edge cluster]; each row sets its own thetas, so a
        # cluster keeps its width in metres where the limb thins
        cols = []
        for k, (tc, sg, offs) in enumerate(fixed):
            cols += [("fix", tc, sg * o) for o in offs]
            if k + 1 < len(fixed):
                arc = np.radians((wide(fixed[k + 1][0]) - wide(tc)).max()) * Rm - abs(offs[-1]) - abs(fixed[k + 1][2][0])
                n = max(int(round(arc / self.step)), 1)
                cols += [("free", k, (i + 1) / n) for i in range(n - 1)]
        rows = [("top", d) for d in dkt] + [("mid", (i + 1) / nv) for i in range(nv - 1)] + [("bot", d) for d in dkb[::-1]]
        S, TH = np.zeros((len(rows), len(cols))), np.zeros((len(rows), len(cols)))

        def thetas(s_of):
            th = np.zeros(len(cols))
            th[:] = tm
            for _ in range(6):   # (thetas and the row's s depend on each other through the edge curves: settle)
                s = s_of(th)
                R = np.maximum(self.law(s, th), 1e-3)
                for j, c in enumerate(cols):
                    if c[0] == "fix":
                        th[j] = num(c[1], s[j]) + np.degrees(c[2] / R[j])
                for j, c in enumerate(cols):
                    if c[0] == "free":
                        lo = max(jj for jj in range(j) if cols[jj][0] == "fix")
                        hi = min(jj for jj in range(j, len(cols)) if cols[jj][0] == "fix")
                        th[j] = th[lo] + (th[hi] - th[lo]) * c[2]
            return th

        for i, r in enumerate(rows):
            if r[0] == "top":
                s_of = lambda th, d=r[1]: self.top(th) + d  # noqa: E731
            elif r[0] == "bot":
                s_of = lambda th, d=r[1]: self.bot(th) - d  # noqa: E731
            else:
                s_of = lambda th, t=r[1]: (self.top(th) + dkt[-1]) * (1 - t) + (self.bot(th) - dkb[-1]) * t  # noqa: E731
            TH[i] = thetas(s_of)
            S[i] = s_of(TH[i])
        return S, TH

    def build(self, name, material, repeats=2.5, ao=1.0):
        fr = self.fr
        S, TH = self.knots()
        nr, nc = S.shape
        Rl = self.law(S, TH)
        H = self.height(S, TH)
        D = np.maximum(self.edge_d(S, TH), 0.0)
        Dr = np.maximum(self.roll_d(S, TH), 0.0)   # (the shader's rolled-edge data: only where an edge is rolled)
        P = fr.pt(S, TH, Rl + H).reshape(-1, 3)
        base = fr.pt(S, TH, Rl)
        rad = fr.radial(TH)
        T = outward(P, grid_tris(nr, nc), rad.reshape(-1, 3))
        w = self.roll[0] if self.roll else 0.0
        # the shader's data: edge distance (m), convexity (0.5 flat, high on a crest, low in a crease)
        conv = np.full(S.shape, 0.5)
        if self.roll:
            x = Dr / w
            conv = np.where(x < 1.0, 0.5 + 0.4 * np.interp(x, ROLL_D, ROLL_B), conv)
            conv = np.where(np.abs(x - 1.0) < 0.05, 0.15, conv)
        if self.ridge:
            x = np.abs(np.radians(TH - self.ridge["theta"]) * Rl / (self.ridge["w"] / 2))
            conv = np.where(x < 0.1, 0.95, np.where(np.abs(x - 1) < 0.05, np.minimum(conv, 0.3), conv))
        aov = np.where(np.abs(Dr - w) < 1e-5, 0.7, 1.0) * ao if self.roll else np.full(S.shape, ao)
        flag = (Dr > w + 1e-6).astype(float)
        # arc-length UVs (metres x the material's repeats): u round the limb at each row, v down it
        du = np.linalg.norm(np.diff(P.reshape(nr, nc, 3), axis=1), axis=2)
        uu = np.c_[np.zeros(nr), np.cumsum(du, 1)]
        uu = uu - uu[:, [nc // 2]]
        dv = np.linalg.norm(np.diff(P.reshape(nr, nc, 3), axis=0), axis=2)
        vv = np.r_[np.zeros((1, nc)), np.cumsum(dv, 0)]
        uv = np.c_[uu.reshape(-1), vv.reshape(-1)] * repeats
        rnd = rand01(name)
        col = np.c_[aov.reshape(-1), np.full(nr * nc, rnd), np.zeros(nr * nc), flag.reshape(-1)]
        uv1 = np.c_[D.reshape(-1), conv.reshape(-1)]
        # the edge wall and the lip: three rings round the whole boundary (nose, inner corner, lip toward her skin)
        idx = np.arange(nr * nc).reshape(nr, nc)
        loop = np.r_[idx[0, :-1], idx[:-1, -1], idx[-1, :0:-1], idx[:0:-1, 0]]
        inner = np.r_[idx[1, :-1], idx[:-1, -2], idx[-2, :0:-1], idx[:0:-1, 1]]
        n_loop = len(loop)
        bl, rl = base.reshape(-1, 3)[loop], rad.reshape(-1, 3)[loop]
        tang = np.roll(P[loop], -1, 0) - np.roll(P[loop], 1, 0)
        e = U(np.cross(tang, rl))
        e = e * np.sign((e * (P[loop] - P[inner])).sum(1, keepdims=True))   # out of the sheet, along the surface
        hb = H.reshape(-1)[loop]
        drop = max(self.clear - self.lip, 0.0)
        # (an edge lifted over another plate: its wall is the steel's own thickness and its lip turns in under it,
        # above the plate beneath; any other edge: the wall runs down to her skin)
        under = np.maximum(hb - self.thick, 0.0)
        rings = [bl + e * 0.25 * self.thick + rl * (under + 0.45 * np.minimum(hb, self.thick))[:, None],
                 bl - e * 0.0002 + rl * (under - 0.0002)[:, None],
                 bl - e * 0.0028 + rl * np.where(under > 0.0006, under - 0.0005, -drop)[:, None]]
        Pw = np.vstack(rings)
        k0 = nr * nc
        # (an edge no roll is on lies hidden under another plate and takes no wall: a wall there would stand between
        # her skin and the plate over it, and the tuck's rays read its steep faces as a rim, an edge of the piece)
        rw, cw = np.divmod(loop, nc)
        hid = np.zeros(n_loop, bool)
        for k, on in (("t", rw == 0), ("b", rw == nr - 1), ("0", cw == 0), ("1", cw == nc - 1)):
            if k not in self.roll_on:
                hid |= on & np.roll(on, -1)
        Tw = []
        prev = loop
        for k in range(3):
            cur = k0 + k * n_loop + np.arange(n_loop)
            a, b = prev, np.roll(prev, -1)
            c, d = cur, np.roll(cur, -1)
            Tw += [np.c_[a, b, d][~hid], np.c_[a, d, c][~hid]]
            prev = cur
        n_seg = int((~hid).sum())
        Tw = np.vstack(Tw)
        Pall = np.vstack([P, Pw])
        fn = np.cross(Pall[Tw[:, 1]] - Pall[Tw[:, 0]], Pall[Tw[:, 2]] - Pall[Tw[:, 0]])
        if (fn[:2 * n_seg] * np.r_[e[~hid], e[~hid]]).sum() < 0:
            Tw = Tw[:, ::-1]
        nw = len(Pw)
        uvw = np.vstack([uv[loop]] * 3) + np.repeat(np.array([[0, 0.002], [0, 0.004], [0, 0.007]]) * repeats, n_loop, 0)
        colw = np.c_[np.repeat([0.7, 0.45, 0.3], n_loop) * ao, np.full(nw, rnd), np.zeros(nw), np.zeros(nw)]
        uv1w = np.c_[np.zeros(nw), np.repeat([0.8, 0.5, 0.5], n_loop)]
        Tall = np.vstack([T, Tw])
        used = np.zeros(len(Pall), bool)
        used[Tall] = True
        part = Part(name, material, Pall[used], (np.cumsum(used) - 1)[Tall], np.vstack([uv, uvw])[used], np.vstack([uv1, uv1w])[used],
                    np.vstack([col, colw])[used])
        part.grid = (S, TH, idx)
        return part


def skin_band(ref, path, width, thick, name, material, lift=0.0004, lifts=None, tab=None, repeats=2.5, bevel=0.0012,
              cap=True):
    """A strap following her skin along `path` (points near the skin): each cross-section point stands on its own
    skin point, `lifts` (per path point) higher where it climbs over a plate. tab: a bool per path point, True on the
    rows that ride a plate; returns (strap part or None, tab part or None), the row between them in both."""
    path = np.asarray(path, float)
    n = len(path)
    q, nq, _ = ref.closest(path)
    t = U(np.gradient(q, axis=0))
    b = U(np.cross(nq, t))
    lifts = np.full(n, lift) if lifts is None else np.maximum(np.asarray(lifts, float), lift)
    xs = np.array([-0.5, -0.5, 0.5, 0.5]) * width + np.array([0, bevel, -bevel, 0])
    hs = np.array([0.0, thick, thick, 0.0])
    X = q[:, None, :] + b[:, None, :] * xs[None, :, None]
    qx, nx, _ = ref.closest(X.reshape(-1, 3))
    nx = U(nx.reshape(n, 4, 3) * 0.5 + nq[:, None, :] * 0.5)
    P = qx.reshape(n, 4, 3) + nx * (lifts[:, None, None] + hs[None, :, None])
    P[:, [0, 3]] -= nx[:, [0, 3]] * 0.0003   # (its edges bite in a hair: no slit of light under a strap)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
    uv = np.stack([np.broadcast_to(xs + 0.5 * width, (n, 4)), np.broadcast_to(arc[:, None], (n, 4))], -1) * repeats
    rnd = rand01(name)
    out = []
    tab = np.zeros(n, bool) if tab is None else np.asarray(tab, bool)
    for want, nm in ((False, name), (True, name + "_tab")):
        rows = np.where(tab == want)[0]
        if not len(rows):
            out.append(None)
            continue
        # (runs of rows; a run takes the row beyond each end so the two parts meet)
        runs = np.split(rows, np.where(np.diff(rows) > 1)[0] + 1)
        parts = []
        for r in runs:
            r = np.arange(max(r[0] - (1 if want else 0), 0), min(r[-1] + (2 if not want else 1), n))
            if len(r) < 2:
                continue
            Pr = P[r].reshape(-1, 3)
            T = grid_tris(len(r), 4)
            ends = []
            if cap:
                m = len(r)
                ends = [[0, 1, 2], [0, 2, 3], [(m - 1) * 4, (m - 1) * 4 + 2, (m - 1) * 4 + 1], [(m - 1) * 4, (m - 1) * 4 + 3, (m - 1) * 4 + 2]]
            Dn = np.repeat(nq[r], 4, 0)
            T = outward(Pr, T, Dn)
            if ends:
                T = np.vstack([T, ends])
            edge = np.tile(np.array([0.0, bevel, bevel, 0.0]), len(r))
            parts.append(Part(nm, material, Pr, T, uv[r].reshape(-1, 2), np.c_[edge, np.tile([0.7, 0.6, 0.6, 0.7], len(r))],
                              np.c_[np.tile([0.6, 1, 1, 0.6], len(r)), np.full(len(Pr), rnd), np.zeros(len(Pr)), np.ones(len(Pr))]))
        out.append(Part.join(nm, material, parts) if parts else None)
    return out[0], out[1]


def box(c, x, y, z, hx, hy, hz):
    """A box at c with unit axes x, y, z and half sizes: (P, T) with hard corners (24 points)."""
    P, T = [], []
    for ax, (u, v, w), (hu, hv, hw) in ((0, (y, z, x), (hy, hz, hx)), (1, (z, x, y), (hz, hx, hy)), (2, (x, y, z), (hx, hy, hz))):
        for sg in (1, -1):
            o = c + w * hw * sg
            q = [o - u * hu - v * hv, o + u * hu - v * hv, o + u * hu + v * hv, o - u * hu + v * hv]
            k = len(P)
            P += q
            T += [[k, k + 1, k + 2], [k, k + 2, k + 3]] if sg > 0 else [[k, k + 2, k + 1], [k, k + 3, k + 2]]
    return np.array(P), np.array(T)


def buckle(c, n, up, w=0.022, h=0.017, bar=0.0026, name="buckle_rigid", material="steel"):
    """A strap buckle: a frame of four bars and a tongue, on a point, its normal and the strap's direction."""
    n, up = U(n), U(up - U(n) * (U(n) @ up))
    x = np.cross(up, n)
    c = np.asarray(c, float) + n * bar * 0.6
    bars = [box(c + up * (h / 2 - bar / 2) * sg, x, up, n, w / 2, bar / 2, bar / 2) for sg in (1, -1)]
    bars += [box(c + x * (w / 2 - bar / 2) * sg, x, up, n, bar / 2, h / 2, bar / 2) for sg in (1, -1)]
    bars.append(box(c + n * bar * 0.5, x, up, n, bar * 0.4, h / 2, bar * 0.35))
    parts = [Part(name, material, P, T, uv0=(P - c) @ np.c_[x, up] * 2.5, col=np.tile([0.9, rand01(name), 0, 0], (len(P), 1)),
                  uv1=np.tile([0.0, 0.8], (len(P), 1))) for P, T in bars]
    return Part.join(name, material, parts)


def rivet(c, n, r=0.0022, h=0.0012, seg=8, name="rivets_rigid", material="steel"):
    """A domed rivet head on a point and its normal."""
    n = U(n)
    x = U(np.cross(n, [0.3, 1.0, 0.2]))
    y = np.cross(n, x)
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    ring = lambda rr, hh: c + n * hh + rr * (np.cos(a)[:, None] * x + np.sin(a)[:, None] * y)  # noqa: E731
    P = np.vstack([ring(r, -0.0003), ring(r * 0.98, h * 0.35), ring(r * 0.62, h * 0.85), c + n * h])
    T = np.vstack([grid_tris(3, seg, close=True)[:, ::-1], np.c_[2 * seg + np.arange(seg), 2 * seg + (np.arange(seg) + 1) % seg, np.full(seg, 3 * seg)]])
    T = outward(P, T, U(P - (c - n * r)))
    m = len(P)
    return Part(name, material, P, T, uv0=(P - c) @ np.c_[x, y] * 2.5, uv1=np.c_[np.zeros(m), np.full(m, 0.85)],
                col=np.tile([0.85, rand01(name + str(np.round(c, 4))), 0, 0], (m, 1)))


# ---------------------------------------------------------------- the piece dir

def write_piece(pid, piece, parts, sockets=None, out=None):
    """<id>.glb (one node a part), piece.json (with the rest stamp passed in `piece`), <id>.sockets.json."""
    import gear_native as gn
    d = out or os.path.join(NATIVE, pid)
    os.makedirs(d, exist_ok=True)
    gn.write_glb(os.path.join(d, f"{pid}.glb"), [p.node() for p in parts], {"native_build": {"piece": pid}})
    with open(os.path.join(d, "piece.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(piece, f, indent=1)
        f.write("\n")
    if sockets:
        with open(os.path.join(d, f"{pid}.sockets.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(sockets, f, indent=1)
            f.write("\n")
    return d


def read_mesh(gltf, want=None, hand=0):
    """(V, T) of a built gear file's meshes whose node name matches `want` (a regex), its lod and shadow nodes left
    out; hand +1 / -1 keeps her left / right half."""
    sys.path.insert(0, os.path.join(REPO, "tools", "anim"))
    from skin import Gltf
    g = Gltf(gltf)
    Vs, Ts, off = [], [], 0
    for n in g.js["nodes"]:
        if "mesh" not in n or ".lod" in n.get("name", "") or n.get("name", "").endswith(".shadow"):
            continue
        if want and not re.search(want, n["name"]):
            continue
        pr = g.js["meshes"][n["mesh"]]["primitives"][0]
        V = g.accessor(pr["attributes"]["POSITION"]).astype(float)
        T = g.accessor(pr["indices"]).reshape(-1, 3).astype(np.int64)
        if hand:
            T = T[(V[T][:, :, 0].mean(1) * hand) > 0]
        Vs.append(V)
        Ts.append(T + off)
        off += len(V)
    return np.vstack(Vs), np.vstack(Ts)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("id", help="a piece under godot/art/gear/native/ with a build.json")
    ap.add_argument("--out", help="write the piece dir elsewhere (a trial)")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(NATIVE, a.id, "build.json"), encoding="utf-8"))
    import native_recipes
    import native_spaulder
    rep = {**native_recipes.RECIPES, **native_spaulder.RECIPES}[cfg["recipe"]](a.id, cfg, out=a.out)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
