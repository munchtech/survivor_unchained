"""The gore BAR on the installed plate_top_plain (P2 l16; the owner's ruling: "built ON the installed top as a recorded
step: no rebuild, no follow, the cups never move").

    python tools/armor/top_bar.py [--check] [--out <dir>]

Loads the installed godot/art/armor/plate_top_plain.gltf (+ .bin, .sockets.json), takes the gore tongue (its plate,
rolled edge and 3 rivets) out of top.steel, lod1.steel and shadow (found by welded component + the gore socket's one
rigid weight row + nearness to the gore socket, never by index ranges), and builds the bar in its place from
piece.json params.gore (the glTF frame, y up, +z front): a bridge between the CUPS (never her skin): rows `top + drop`
tall centred where the installed cups' inner rims stand closest (the cleavage's narrowest gap), each row a straight
chord between the two cups' fronts at their inner rims (the rolled-edge crowns, a least-squares line in y per side so
the plate is flat), set back `thick + roll height` (the bar's rolled edge crowns level with the cups', its face just
behind them), bowed forward `camber`, never closer than `lift` to her skin, `thick` thick, a rolled edge `roll` (width, height) over its cut, square ends
standing `clear` off the cups (the WHOLE bar, rolled edge included: past the join law's weld_m, so it links to both
cups as a bridge), 2 end rivets at mid-height. Every bar point carries the tongue's one rigid row and one delta per
morph target (the mean of the removed piece's position deltas, zero normal deltas: a rigid piece's normals do not
turn with a translation). The gore socket moves onto the bar's face. Idempotent: on a top that has a bar it finds
the bar and rebuilds it. Hard gate before any write: every other vertex and mesh byte-identical.
"""
import argparse
import json
import os
import shutil
import sys

import numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import RegularGridInterpolator
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import adorn  # noqa: E402
import piece_ship as ps  # noqa: E402
from carry_targets import closest  # noqa: E402

PID = "plate_top_plain"
ARMOR = os.path.join(ROOT, "godot", "art", "armor")
PIECE = os.path.join(ARMOR, "src", PID, "piece.json")
TONGUE = {"top.steel": 1833, "lod1.steel": 747, "shadow": 96}     # (the shipped tongue's vertex counts, facts.md)
MESHES = ("top.steel", "lod1.steel", "shadow")
PIECE_IDS = {"plate": 14, "roll": 13, "rivet": 15}                  # (the tongue's piece ids, reused by the bar)
NEAR = 0.065                                                        # (a tongue/bar point lies within this of the socket)
TOL = 0.0002


def say(*a):
    print("top_bar:", *a, flush=True)


# ---------------------------------------------------------------- her skin
def skin():
    js, b = ps._glb(ps.BODY)
    n = next(x for x in js["nodes"] if x.get("name") == "Heroine")
    assert not any(k in n for k in ("translation", "rotation", "scale", "matrix")), "Heroine node has a transform"
    V, F = [], []
    for p in js["meshes"][n["mesh"]]["primitives"]:
        P = ps._acc(js, b, p["attributes"]["POSITION"]).astype(np.float64)
        F.append(ps._acc(js, b, p["indices"]).reshape(-1, 3).astype(np.int64) + sum(len(v) for v in V))
        V.append(P)
    return np.vstack(V), np.vstack(F)


def front_z(V, F, X, Y):
    """Her skin's front-most z under each (x, y) (a ray from the front along -z), nan on a miss."""
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    lo, hi = np.minimum.reduce([A, B, C]), np.maximum.reduce([A, B, C])
    sel = (hi[:, 0] > X.min() - 0.01) & (lo[:, 0] < X.max() + 0.01) & (hi[:, 1] > Y.min() - 0.01) & \
          (lo[:, 1] < Y.max() + 0.01) & (hi[:, 2] > 0.0)
    A, B, C, lo, hi = A[sel], B[sel], C[sel], lo[sel], hi[sel]
    out = np.full(len(X), np.nan)
    for i, (x, y) in enumerate(zip(X, Y)):
        k = (lo[:, 0] <= x) & (hi[:, 0] >= x) & (lo[:, 1] <= y) & (hi[:, 1] >= y)
        if not k.any():
            continue
        a, b_, c = A[k], B[k], C[k]
        d = (b_[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b_[:, 1] - a[:, 1])
        ok = np.abs(d) > 1e-18
        u = ((x - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (y - a[:, 1])) / np.where(ok, d, 1)
        v = ((b_[:, 0] - a[:, 0]) * (y - a[:, 1]) - (x - a[:, 0]) * (b_[:, 1] - a[:, 1])) / np.where(ok, d, 1)
        hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        if hit.any():
            z = a[:, 2] + u * (b_[:, 2] - a[:, 2]) + v * (c[:, 2] - a[:, 2])
            out[i] = z[hit].max()
    return out


# ---------------------------------------------------------------- finding the tongue (or the bar)
def welded_comps(m):
    P = m["attrs"]["POSITION"][0]
    _, inv = np.unique(np.round(P / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    inv = inv.ravel()
    T = inv[m["tris"]]
    n = int(inv.max()) + 1
    A = coo_matrix((np.ones(T.size), (T.ravel(), np.roll(T, 1, 1).ravel())), shape=(n, n))
    return connected_components(A, directed=False)[1][inv]


def gore_row(model, sock):
    return {model.joints.index(j): w for j, w in sock["sockets"]["gore"]["weights"]}


def on_row(m, row):
    J, W = adorn.joints_weights(m["attrs"])
    ok = np.ones(len(J), bool)
    for j, w in row.items():
        ok &= ((J == j) & (np.abs(W - w) < 0.002)).any(1)
    return ok & ((W > 1e-4).sum(1) == len(row))


def find_gore(m, row, at):
    """The gore piece's vertices: whole welded components all on the gore row, within NEAR of the gore socket."""
    c = welded_comps(m)
    r = on_row(m, row)
    P = m["attrs"]["POSITION"][0].astype(np.float64)
    near = np.linalg.norm(P - at, axis=1) < NEAR
    sel = np.zeros(len(P), bool)
    for k in np.unique(c[r & near]):
        s = c == k
        if r[s].all() and near[s].all():
            sel |= s
    return sel


def kinds(m, sel):
    """The found piece's points as plate / roll / rivet (by the shell's conventions: a plate's TEXCOORD_1.x is the
    0.05 cap, small components are rivets), per vertex."""
    c = welded_comps(m)
    out = np.full(len(sel), "", object)
    for k in np.unique(c[sel]):
        s = c == k
        P = m["attrs"]["POSITION"][0][s]
        if np.linalg.norm(P.max(0) - P.min(0)) < 0.009:
            out[s] = "rivet"
        elif "TEXCOORD_1" in m["attrs"] and np.all(m["attrs"]["TEXCOORD_1"][0][s, 0] >= 0.0499):
            out[s] = "plate"
        else:
            out[s] = "roll"
    return out


# ---------------------------------------------------------------- the bar
class Surf:
    """The bar's back surface z(x, y): per row a straight chord between the two cups' FRONT at their inner rims
    (`rim(ys)` -> (x_left < 0, z_left, x_right > 0, z_right): the installed rim's x, the cup's front-most z there), set
    back `back` (so the face sits level with / just behind the cups' fronts), bowed forward `camber` at the middle;
    never closer than `lift` to her skin (in the valley it stands far off it)."""

    def __init__(self, V, F, y0, y1, hw, rim, back, camber, lift):
        self.xs = np.arange(-hw - 0.008, hw + 0.008 + 1e-9, 0.0005)
        self.ys = np.arange(y0 - 0.006, y1 + 0.006 + 1e-9, 0.0005)
        X, Y = np.meshgrid(self.xs, self.ys)
        Zs = front_z(V, F, X.ravel(), Y.ravel()).reshape(X.shape)
        assert not np.isnan(Zs).any(), "her skin missed under the bar"
        self.skin = RegularGridInterpolator((self.ys, self.xs), Zs)
        xl, zl, xr, zr = rim(self.ys)
        t = np.clip((self.xs[None, :] - xl[:, None]) / (xr - xl)[:, None], 0, 1)
        zb = zl[:, None] + (zr - zl)[:, None] * t - back
        xm, ha = 0.5 * (xl + xr), 0.5 * (xr - xl)
        zb = zb + camber * np.clip(1 - ((self.xs[None, :] - xm[:, None]) / ha[:, None]) ** 2, 0, 1)
        Z = np.maximum(Zs + lift, zb)
        self.z = RegularGridInterpolator((self.ys, self.xs), Z)
        gy, gx = np.gradient(Z, self.ys, self.xs)
        self.gx = RegularGridInterpolator((self.ys, self.xs), gx)
        self.gy = RegularGridInterpolator((self.ys, self.xs), gy)

    def at(self, x, y):
        q = np.c_[y, x]
        N = np.c_[-self.gx(q), -self.gy(q), np.ones(len(q))]
        N /= np.linalg.norm(N, axis=1, keepdims=True)
        return np.c_[x, y, self.z(q)], N

    def skin_z(self, x, y):
        return self.skin(np.c_[y, x])


def profile(w, h, oh, thick, n1, n2):
    """The rolled edge's section (u out past the cut, v up off the back face) and its normals: from the front face
    `w - oh` inside the cut, over a crown `h` high, round the cut `oh` past it, down to the back face's edge."""
    a, uc = w / 2, oh - w / 2
    t1 = np.linspace(np.pi, 0, n1)
    t2 = np.linspace(0, -np.pi / 2, n2 + 1)[1:]
    u = np.r_[uc + a * np.cos(t1), oh * np.cos(t2)]
    v = np.r_[thick + h * np.sin(t1), thick + thick * np.sin(t2)]
    nu = np.r_[np.cos(t1) / a, np.cos(t2) / oh]
    nv = np.r_[np.sin(t1) / h, np.sin(t2) / thick]
    nn = np.hypot(nu, nv)
    return u, v, nu / nn, nv / nn


def grid_tris(nr, nc, off=0):
    i = (np.arange(nr - 1)[:, None] * nc + np.arange(nc - 1)[None, :]).ravel() + off
    return np.vstack([np.c_[i, i + nc, i + 1], np.c_[i + 1, i + nc, i + nc + 1]])


def orient(P, T, N):
    """Each triangle wound to face along its vertices' normals."""
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    flip = (fn * (N[T[:, 0]] + N[T[:, 1]] + N[T[:, 2]])).sum(1) < 0
    T = T.copy()
    T[flip] = T[flip][:, ::-1]
    return T


class Bar:
    def __init__(self, surf, gp, ends, y0, y1):
        self.s, self.gp, self.ends, self.y0, self.y1 = surf, gp, ends, y0, y1   # ends(y) -> (xl, xr) of the cut

    def outline(self, nr, nc):
        ys = np.linspace(self.y0, self.y1, nr)
        xl, xr = self.ends(ys)
        X = xl[:, None] + (xr - xl)[:, None] * np.linspace(0, 1, nc)[None, :]
        Y = np.repeat(ys[:, None], nc, 1)
        return X, Y

    def parts(self, nr, nc, n1, n2, rivets, faces=True):
        """[(kind, P, N, T, edge)] : the plate (front and back faces), the rolled edge, the rivets."""
        thick, (w, h), oh = self.gp["thick"], self.gp["roll"], OVERHANG
        X, Y = self.outline(nr, nc)
        B, N = self.s.at(X.ravel(), Y.ravel())
        out = []
        if faces:
            Fp, Bp = B + N * thick, B
            T = grid_tris(nr, nc)
            P = np.vstack([Fp, Bp])
            NN = np.vstack([N, -N])
            TT = np.vstack([orient(Fp, T, N), orient(Bp, T, -N) + len(Fp)])
            out.append(("plate", P, NN, TT, np.full(len(P), 0.05)))
        # (the cut's loop, its in-plane outward direction mitred at the corners)
        idx = np.arange(nr * nc).reshape(nr, nc)
        loop = np.r_[idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]]
        L, LN = B[loop], N[loop]
        t = np.roll(L, -1, 0) - np.roll(L, 1, 0)
        t /= np.linalg.norm(t, axis=1, keepdims=True)
        o = np.cross(t, LN)
        o /= np.linalg.norm(o, axis=1, keepdims=True)
        cen = B.mean(0)
        if ((L - cen) * o).sum(1).mean() < 0:
            o = -o
        e = np.roll(L, -1, 0) - L
        e /= np.linalg.norm(e, axis=1, keepdims=True)
        eb = L - np.roll(L, 1, 0)
        eb /= np.linalg.norm(eb, axis=1, keepdims=True)
        cos_h = np.sqrt(np.clip((1 + (e * eb).sum(1)) / 2, 0.2, 1))   # (a corner's mitre: 1 / cos of half its turn)
        u, v, nu, nv = profile(w, h, oh, thick, n1, n2)
        P = (L[:, None, :] + o[:, None, :] * (u[None, :, None] / cos_h[:, None, None]) + LN[:, None, :] * v[None, :, None])
        NR = o[:, None, :] * nu[None, :, None] + LN[:, None, :] * nv[None, :, None]
        nl, npf = len(L), len(u)
        P, NR = P.reshape(-1, 3), NR.reshape(-1, 3)
        NR /= np.linalg.norm(NR, axis=1, keepdims=True)
        i = (np.arange(nl)[:, None] * npf + np.arange(npf - 1)[None, :]).ravel()
        j = ((np.arange(nl)[:, None] + 1) % nl * npf + np.arange(npf - 1)[None, :]).ravel()
        T = np.vstack([np.c_[i, j, i + 1], np.c_[i + 1, j, j + 1]])
        edge = np.tile(np.abs(np.minimum(u, 0)), nl)
        out.append(("roll", P, NR, orient(P, T, NR), edge))
        if rivets:
            ym = 0.5 * (self.y0 + self.y1)
            xl, xr = self.ends(np.array([ym]))
            for x in (float(xl[0]) + RIVET_IN, float(xr[0]) - RIVET_IN):
                b, n = self.s.at(np.array([x]), np.array([ym]))
                out.append(("rivet",) + rivet(b[0] + n[0] * thick, n[0], RIVET_R))
        return out


def rivet(p0, n, r, rise=0.42, nu=8):
    """piece_blender low_rivets, one head: an 8-sided dome of two rings on a thin flange."""
    t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
    t /= np.linalg.norm(t)
    b = np.cross(n, t)
    fl = 0.08 * r
    q, rad = [p0 + n * (fl + r * rise)], [0.0]
    for rr, hh in ((r * 0.62, fl + r * rise * 0.78), (r, fl + r * rise * 0.18), (r * 1.1, -0.0004)):
        for j in range(nu):
            ph = 2 * np.pi * (j + 0.5 * (rr == r)) / nu
            q.append(p0 + (np.cos(ph) * t + np.sin(ph) * b) * rr + n * hh)
            rad.append(rr)
    tri = [(0, 1 + j, 1 + (j + 1) % nu) for j in range(nu)]
    for k in range(2):
        a0, b0 = 1 + k * nu, 1 + (k + 1) * nu
        for j in range(nu):
            j1 = (j + 1) % nu
            tri += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
    P, T = np.array(q), np.array(tri)
    N = P - (p0 - n * r * 1.5)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    return P, N, orient(P, T, N), np.array(rad)


UNDER = 0.03          # (a bar point with a cup within this in front of it is under the cup)
OVERHANG = 0.0012     # (the rolled edge's reach past the cut: bind_edges' overhang)
RIVET_R = 0.0024
RIVET_IN = 0.0055


# ---------------------------------------------------------------- the tool
def load(src):
    gl = os.path.join(src, PID + ".gltf")
    return adorn.Model(gl), json.load(open(os.path.join(src, PID + ".sockets.json"), encoding="utf-8"))


def run(src, dst=None, check=False):
    gp = json.load(open(PIECE, encoding="utf-8"))["params"]["gore"]
    bar_p = gp["bar"]
    M, sock = load(src)
    row = gore_row(M, sock)
    at = np.asarray(sock["sockets"]["gore"]["point"], float)
    V, F = skin()

    old = {k: M.get(f"{PID}.{k}") for k in MESHES}
    sel = {k: find_gore(old[k], row, at) for k in MESHES}
    for k in MESHES:
        say(f"{k}: gore piece found {sel[k].sum()} verts")
    steel = old["top.steel"]
    keep_t = ~sel["top.steel"][steel["tris"]].any(1)
    assert (sel["top.steel"][steel["tris"]].all(1) | keep_t).all(), "a triangle straddles the gore piece"
    cupV = steel["attrs"]["POSITION"][0].astype(np.float64)
    cupF = steel["tris"][keep_t]

    # (the cups' inner rims, from the installed rims (their inner branches, x(y) and z(y)); the bar's rows cover the
    # band where they stand closest (the cleavage's narrowest gap), top + drop tall, centred there)
    branch = {}
    for k, r in sock["rims"].items():
        if not k.startswith("cup_rim"):
            continue
        R = np.asarray(r["points"], float)
        R = R[R[:, 2] > 0.1]
        R = R[(np.abs(R[:, 0]) < 0.06) & (np.abs(R[:, 1] - R[np.argmin(np.abs(R[:, 0])), 1]) < 0.03)]
        R = R[np.argsort(R[:, 1])]
        assert len(R) > 6 and np.all(np.diff(R[:, 1]) > 0), f"{k}: no single inner branch"
        branch[int(np.sign(np.median(R[:, 0])))] = R
    assert set(branch) == {-1, 1}, "top_bar: need both cups' rims"
    ylo = max(branch[-1][0, 1], branch[1][0, 1])
    yhi = min(branch[-1][-1, 1], branch[1][-1, 1])
    yy = np.arange(np.ceil(ylo / 0.0002), np.floor(yhi / 0.0002) + 1) * 0.0002
    rim_x = lambda sx, ys: np.interp(ys, branch[sx][:, 1], branch[sx][:, 0])
    gap = rim_x(1, yy) - rim_x(-1, yy)
    yc = float(yy[np.argmin(gap)])
    H = gp["top"] + gp["drop"]
    y0, y1 = yc - H / 2, yc + H / 2
    assert ylo < y0 - 0.006 and y1 + 0.006 < yhi, "top_bar: the rims do not span the bar's rows"
    x_in = float(min(np.abs(rim_x(-1, yy[np.abs(yy - yc) <= H / 2])).min(), rim_x(1, yy[np.abs(yy - yc) <= H / 2]).min()))
    hw = x_in + 0.012

    def cup_front(sx, ys):
        """The cup's front-most z at its rim's x (the rolled edge's crown), per row."""
        z = front_z(cupV, cupF, rim_x(sx, ys), ys)
        assert not np.isnan(z).any(), "the cup missed at its rim"
        return z

    # (the cups' fronts as the bar sees them: a straight line in y per side, least squares over the bar's rows +- 6 mm,
    # so the plate is flat (the crowns' ray hits are faceted: a per-row chord would ripple the face))
    yf = np.linspace(y0 - 0.006, y1 + 0.006, 29)
    fit = {sx: np.polyfit(yf, cup_front(sx, yf), 1) for sx in (-1, 1)}

    def rim(ys):
        return rim_x(-1, ys), np.polyval(fit[-1], ys), rim_x(1, ys), np.polyval(fit[1], ys)
    # (depth: the plate's face level with the cups' rolled-edge crowns minus the bar's own roll height, so the bar's
    # rolled edge crowns level with the cups' and its face stands just behind them)
    back = gp["thick"] + gp["roll"][1]
    say(f"cups' inner rims: narrowest gap {gap.min() * 1000:.1f} mm at y {yc:.4f}, x_in {x_in * 1000:.1f} mm; bar rows"
        f" y {y0:.4f}..{y1:.4f}; set back {back * 1000:.2f} mm from the cups' fronts")
    surf = Surf(V, F, y0, y1, hw, rim, back, bar_p["camber"], gp["lift"])
    clear = bar_p["clear"]

    def env(x, y, sx):
        """The bar's outermost points at a cut point (x, y): the rolled edge's reach past it and its crown."""
        b, n = surf.at(x, y)
        o = np.c_[sx * np.ones(len(x)), np.zeros(len(x)), np.zeros(len(x))]
        pts = [b + o * OVERHANG, b + o * OVERHANG + n * gp["thick"] * 0.5, b + n * (gp["thick"] + gp["roll"][1]),
               b + o * OVERHANG * 0.7 + n * (gp["thick"] + gp["roll"][1] * 0.6)]
        return pts

    def dcup(P):
        return closest(np.asarray(P, np.float64), cupV, cupF, k=32)[0]

    cA, cB, cC = cupV[cupF[:, 0]], cupV[cupF[:, 1]], cupV[cupF[:, 2]]
    ctree = cKDTree((cA + cB + cC) / 3)

    def under(P, N, reach=0.012):
        """A point is under a cup if a ray out along its normal meets the cup within `reach` (gore_plate's test)."""
        out = np.zeros(len(P), bool)
        for i, (p, n) in enumerate(zip(P, N)):
            f = np.array(ctree.query_ball_point(p + n * reach / 2, reach / 2 + 0.006), int)
            if not len(f):
                continue
            a, e1, e2 = cA[f], cB[f] - cA[f], cC[f] - cA[f]
            h = np.cross(n, e2)
            det = (e1 * h).sum(1)
            ok = np.abs(det) > 1e-14
            inv = 1 / np.where(ok, det, 1)
            sv = p - a
            u = (sv * h).sum(1) * inv
            q = np.cross(sv, e1)
            v = (q @ n) * inv
            t = (e2 * q).sum(1) * inv
            out[i] = (ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= reach)).any()
        return out

    # (each row's square end: as far out as the whole bar stays `clear` (+ margin) off the cups, at most hw)
    yr = np.linspace(y0 - OVERHANG, y1 + OVERHANG, 29)
    xs = np.arange(0.0, hw + 1e-9, 0.00025)
    ends = np.zeros((len(yr), 2))
    margin = 0.0003
    for si, sx in enumerate((-1.0, 1.0)):
        for r, y in enumerate(yr):
            X = sx * xs
            d = np.min([dcup(p) for p in env(X, np.full(len(X), y), sx)], 0)
            b_, n_ = surf.at(X, np.full(len(X), y))
            # (under a cup = a ray out to the FRONT (+z, the play camera's side) meets it within UNDER: the bar's
            # face here is steep (its rows chord her inner breasts), so its own normal would slide under the cups)
            fz = np.tile([0.0, 0.0, 1.0], (len(X), 1))
            bad = np.nonzero((d < clear + margin) | under(b_, fz, UNDER))[0]
            ends[r, si] = X[bad[0] - 1] if len(bad) else X[-1]
    # (the end of a row at y holds for every row the rolled edge reaches: the tightest within OVERHANG of it)
    def end_fn(ys):
        xl = np.array([ends[np.abs(yr - y) <= OVERHANG + 1e-9, 0].max() for y in ys])
        xr = np.array([ends[np.abs(yr - y) <= OVERHANG + 1e-9, 1].min() for y in ys])
        return xl, xr

    bar = Bar(surf, gp, end_fn, y0, y1)

    def build(nr, nc, n1, n2, rivets, faces=True):
        return bar.parts(nr, nc, n1, n2, rivets, faces)

    full = build(11, 33, 9, 5, True)
    lod1 = build(6, 13, 5, 3, False)
    shadow = build(3, 6, 3, 1, False)

    # ---------- attributes by the shell's conventions
    tk = adorn.target_keys(steel["attrs"])
    tongue_t = sel["top.steel"]

    def one_delta(D):
        """A rigid piece's one delta: the found piece's mean (a bar's: its one value, exactly)."""
        return D[0].copy() if np.all(D == D[0]) else D.astype(np.float64).mean(0)
    dpos = {k: (one_delta(steel["attrs"][k][0][tongue_t]) if k.endswith("P") else np.zeros(3)) for k in tk}
    new = {}
    for name, parts in (("top.steel", full), ("lod1.steel", lod1), ("shadow", shadow)):
        m = old[name]
        a = m["attrs"]
        s = sel[name]
        kd = kinds(m, s)
        P = np.vstack([p[1] for p in parts])
        N = np.vstack([p[2] for p in parts])
        T, off, pieces = [], 0, []
        for p in parts:
            T.append(p[3] + off)
            off += len(p[1])
            if pieces and pieces[-1][0] == p[0]:
                pieces[-1][1] += len(p[3])
            else:
                pieces.append([p[0], len(p[3])])
        T = np.vstack(T)
        kind = np.concatenate([[p[0]] * len(p[1]) for p in parts])
        edge = np.concatenate([p[4] for p in parts])
        at_new = {"POSITION": P.astype(np.float32), "NORMAL": N.astype(np.float32)}
        i0 = np.nonzero(s)[0][0]
        for key in adorn.weight_keys(a):
            at_new[key] = np.repeat(a[key][0][i0:i0 + 1], len(P), 0)
        for key in tk:
            at_new[key] = np.repeat(dpos[key][None].astype(np.float32), len(P), 0)
        src_k = {k_: (s & (kd == k_)) for k_ in ("plate", "roll", "rivet")}
        src_k["rivet"] = src_k["rivet"] if src_k["rivet"].any() else src_k["roll"]
        if "TEXCOORD_0" in a:
            U = np.zeros((len(P), 2))
            for k_ in ("plate", "roll", "rivet"):
                q, sk = kind == k_, src_k[k_]
                if q.any():
                    Xs = np.c_[a["POSITION"][0][sk].astype(np.float64), np.ones(sk.sum())]
                    coef = np.linalg.lstsq(Xs, a["TEXCOORD_0"][0][sk].astype(np.float64), rcond=None)[0]
                    U[q] = np.c_[P[q], np.ones(q.sum())] @ coef
            at_new["TEXCOORD_0"] = U.astype(np.float32)
            U1 = np.zeros((len(P), 2), np.float32)
            U1[:, 0] = np.minimum(edge, 0.05)
            for k_ in ("plate", "roll", "rivet"):
                U1[kind == k_, 1] = np.median(a["TEXCOORD_1"][0][src_k[k_], 1])
            at_new["TEXCOORD_1"] = U1
            at_new["TEXCOORD_2"] = np.repeat(a["TEXCOORD_2"][0][i0:i0 + 1], len(P), 0)
            C = np.zeros((len(P), 4), a["COLOR_0"][0].dtype)
            for k_ in ("plate", "roll", "rivet"):
                C[kind == k_] = np.median(a["COLOR_0"][0][src_k[k_]].astype(np.float64), 0).round()
            at_new["COLOR_0"] = C
        if s.sum() == len(P) and np.array_equal(a["POSITION"][0][s], at_new["POSITION"]):
            # (a re-run on this tool's own bar: the same points, so its shading rows are kept as they are (a refit of
            # the uv projection on float32 data would drift in the last bit): the run is a fixed point)
            for k in ("TEXCOORD_0", "TEXCOORD_1", "COLOR_0"):
                if k in a:
                    at_new[k] = a[k][0][s].copy()
        assert set(at_new) == set(a), (name, set(a) ^ set(at_new))
        new[name] = (at_new, T, pieces)

    # (what was found is the shipped tongue (facts.md counts) or a bar this tool built (its counts), nothing else)
    for name in MESHES:
        nf, nb = int(sel[name].sum()), len(new[name][0]["POSITION"])
        assert nf in (TONGUE[name], nb), f"top_bar: {name} gore piece {nf} verts is neither the tongue ({TONGUE[name]}) nor the bar ({nb})"

    # ---------- apply, then the hard gate
    before = {m["name"]: adorn.soup(m) for m in M.meshes}
    kept = {}
    for name in MESHES:
        m = old[name]
        s = sel[name]
        kt = ~s[m["tris"]].any(1)
        kept[name] = adorn.soup(m, kt)
        remap = -np.ones(len(s), np.int64)
        remap[~s] = np.arange((~s).sum())
        n_keep = int((~s).sum())
        at_new, T, pieces = new[name]
        rows_before = {k: m["attrs"][k][0][~s].copy() for k in m["attrs"]}
        for k in m["attrs"]:
            arr, norm = m["attrs"][k]
            m["attrs"][k] = [np.concatenate([arr[~s], at_new[k].astype(arr.dtype)]), norm]
        tri_before = m["tris"][kt]
        m["tris"] = np.vstack([remap[m["tris"][kt]], T + n_keep]).astype(m["tris"].dtype)
        if "pieces" in m["extras"]:
            # (the gore's pieces out (their triangles all in the found set), the bar's appended, in its order)
            pc, t0, keepc = m["extras"]["pieces"], 0, []
            gore_t = ~kt
            for pid, nt in pc:
                g = gore_t[t0:t0 + nt]
                assert g.all() or not g.any(), f"piece {pid} is part gore"
                if not g.any():
                    keepc.append([pid, nt])
                t0 += nt
            m["extras"]["pieces"] = keepc + [[PIECE_IDS[k_], n] for k_, n in pieces]
        if "adorn_tris" in m["extras"]:
            raise SystemExit(f"top_bar: {name} has adorn_tris (run on the plain top only)")
        # (gate: every kept vertex byte-identical in every attribute, every kept triangle the same soup)
        for k in rows_before:
            assert m["attrs"][k][0][:n_keep].tobytes() == rows_before[k].tobytes(), f"GATE: {name} {k} changed"
        assert np.array_equal(m["tris"][:len(tri_before)], remap[tri_before]), f"GATE: {name} tris changed"
        assert adorn.soup(m, np.arange(len(tri_before))) == kept[name], f"GATE: {name} kept soup changed"
        say(f"{name}: removed {int(s.sum())} verts / {int((~kt).sum())} tris, added {len(at_new['POSITION'])} verts"
            f" / {len(T)} tris" + (f"; pieces {m['extras']['pieces'][-3:]}" if "pieces" in m["extras"] else ""))
    for m in M.meshes:
        if m["name"].split(".", 1)[1] not in MESHES:
            assert adorn.soup(m) == before[m["name"]], f"GATE: {m['name']} changed"

    # ---------- numbers
    BP = new["top.steel"][0]["POSITION"].astype(np.float64)
    allBP = np.vstack([new[k][0]["POSITION"] for k in MESHES]).astype(np.float64)
    d = dcup(allBP)
    dfull = dcup(BP)
    st_z = allBP[:, 2] - surf.skin_z(allBP[:, 0], allBP[:, 1])
    st_n = closest(allBP, V, F, k=32)[0]
    wmm = (BP[:, 0].max() - BP[:, 0].min()) * 1000
    hmm = (BP[:, 1].max() - BP[:, 1].min()) * 1000
    bL = BP[:, 0] < 0
    gates = {"bar_w_mm": round(wmm, 2), "bar_h_mm": round(hmm, 2), "bar_to_cups_min_mm": round(float(d.min()) * 1000, 2),
             "bar_to_cups_left_mm": round(float(dfull[bL].min()) * 1000, 2),
             "bar_to_cups_right_mm": round(float(dfull[~bL].min()) * 1000, 2),
             "skin_standoff_min_mm": round(float(st_z.min()) * 1000, 2), "skin_dist_min_mm": round(float(st_n.min()) * 1000, 2)}
    # (the face: its normal's angle to +z (the front), and the ends' face depth against the cups' fronts at the rims)
    X_, Y_ = bar.outline(11, 33)
    _, Nf = surf.at(X_.ravel(), Y_.ravel())
    ang = np.degrees(np.arccos(np.clip(Nf[:, 2], -1, 1)))
    ye = np.linspace(y0, y1, 11)
    xl_, xr_ = end_fn(ye)
    dz = []
    for sx, xe in ((-1, xl_), (1, xr_)):
        fz = surf.z(np.c_[ye, xe]) + gp["thick"]
        dz.append(cup_front(sx, ye) - fz)
    dz = np.concatenate(dz)
    gates.update({"face_normal_deg_mean": round(float(ang.mean()), 2), "face_normal_deg_max": round(float(ang.max()), 2),
                  "end_face_behind_rim_front_mm_min": round(float(dz.min()) * 1000, 2),
                  "end_face_behind_rim_front_mm_max": round(float(dz.max()) * 1000, 2)})
    say("GATES", json.dumps(gates))
    assert gates["face_normal_deg_mean"] <= 25, "GATE: the bar's face does not face the front"
    assert np.abs(dz).max() <= 0.005, "GATE: the bar's ends are not at the rims' depth"
    assert d.min() >= clear - TOL, f"GATE: bar {d.min() * 1000:.2f} mm off the cups (< {clear * 1000 - 0.2:.1f})"
    assert st_z.min() > 0, "GATE: bar behind her skin"
    assert dfull[bL].min() < 0.010 and dfull[~bL].min() < 0.010, "GATE: bar not within link_m of both cups"

    # ---------- the gore socket onto the bar's face
    ym = 0.5 * (y0 + y1)
    b, n = surf.at(np.array([0.0]), np.array([ym]))
    sock["sockets"]["gore"]["point"] = np.round(b[0] + n[0] * gp["thick"], 5).tolist()
    sock["sockets"]["gore"]["normal"] = np.round(n[0], 5).tolist()
    say("gore socket", sock["sockets"]["gore"]["point"], sock["sockets"]["gore"]["normal"])
    if check:
        say("--check: gates hold, nothing written")
        return gates
    out = dst or src
    os.makedirs(out, exist_ok=True)
    M.save(os.path.join(out, PID + ".gltf"))
    with open(os.path.join(out, PID + ".sockets.json"), "w", encoding="utf-8") as f:
        json.dump(sock, f, indent=1, ensure_ascii=False)
    say("wrote", os.path.join(out, PID + ".gltf"))
    return gates


def stage(dst):
    """The installed top's three files copied to dst (a test's staging)."""
    os.makedirs(dst, exist_ok=True)
    for ext in (".gltf", ".bin", ".sockets.json"):
        shutil.copy2(os.path.join(ARMOR, PID + ext), os.path.join(dst, PID + ext))
    return dst


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--src", default=ARMOR)
    a = ap.parse_args()
    run(a.src, a.out, a.check)
