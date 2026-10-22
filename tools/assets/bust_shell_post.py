"""An outfit top's bust as a smooth, full shell (armor 14, 21 October 2026; the owner: "mostly smooth, busty, full cups
without dents"). The arcanist bodysuit's leather over her cups had a hollow at her left lower inner breast by the zip,
lumps along the cups' zip edges and a nipple poke on both breasts: the garment's own shape (her nude skin there is
smooth). This post-step smooths the garment's outer surface over each cup at the 1-3 cm scale, in place, on a built
outfit gltf, and carries everything on it.

  - The leather is a thick shell (an outer face over an inner face, joined at a rim). Its outer points over each cup
    (an ellipse round the cup's apex in x, y, mirrored for her right; weight 1 inside, easing to 0 over its ease at
    the border) go to a moving-least-squares surface: each point to the height of a quadric fitted to its outer
    neighbours (Gaussian SIGMA) in a local frame, repeated ITERS times. A quadric holds the cup's own curvature, so the
    cup neither shrinks nor flattens (a Gaussian mean of positions would pull a round cup in by ~sigma^2/R); bumps
    and dips under ~2 sigma go. The fits leave out the points found proud or sunk past ROBUST of the last fit (the
    poke and the hollow don't steer their own fill) until the last passes.
  - The rest of the leather (its inner face, rim) and the riders on it (the config's meshes: stitching, piping, zip)
    move by the outer surface's displacement at their closest point on it, interpolated over its triangle
    (barycentric), so nothing is carried by a few nearest points.
  - Normals of the moved points: each copy's stored normal plus the change of its smooth group's geometric normal
    (the faces round its welded point whose normals lie within 60 deg of it: a designed hard edge keeps its sides;
    UV-seam copies agree), as breast_sym_post.follow_piece does.
  - Her skin stays under: the inner face is kept >= MIN_GAP off her rest skin where the smoothing would bring it
    closer (pushed out along her normal; the outer face and the riders over it go with it).

Then (the dome, armor 14 s3: shell(.., dome=True), done-mark "bust_dome") each cup's front is made one round, full dome
at the 3-6 cm scale (it was a flat top with a tight shoulder 4-5 cm out, which drew an apex highlight and a crease from
under it to the zip): a paraboloid height field over the apex's plane fitted to the outer face (Gaussian DOME_SIGMA
round the apex; the opening's rolled edge within DOME_RIM[1] and the fold under the cup left out), its radii held
within DOME_RADII (opened out: fuller), the outer face blended onto it (weight 1 within DOME_R[0] of the apex, easing
to 0 by DOME_R[1], the cup's border and the fold; the rolled edge carried by the moves beside it), inward only at the
apex (DOME_TIP), her tucked skin kept MIN_GAP under, the inner face and riders carried and normals remade as above.
It drops the "bust_detail" mark, so the convexity below is baked again from the new shape.

Then (detail(), armor 14 s2) the leather's baked convexity over the cups (UV2.y, read by the outfit shader) is made
smooth to match (s3: baked again from the piece's current shape, heroine_outfits.detail's formula): it was baked on the old shape, and its poke and hollow drew a glossy spot at each apex and a dark
crease from under it to the zip after the shape was smooth. Done-mark "bust_detail".

Idempotent: done-mark "bust_shell" in the gltf's asset extras (the largest move, mm); a file that has it is skipped.
Per-outfit config in CONFIG (heroine_body_post runs it for the arcanist only; ranger, warden, reaver could be added).

    python tools/assets/bust_shell_post.py <art dir> [outfit ..] [--force]
"""
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heroine_neck import _Gl  # noqa: E402
from breast_sym_post import _body, _vn, _ss, _closest_tri  # noqa: E402

MARK = "bust_shell"
DOME_MARK = "bust_dome"
SIGMA = 0.012
REACH = 0.030       # fit neighbourhood radius
ITERS = 16
ROBUST = 0.00025    # a point this far off the last fit is left out of the next fits
MIN_GAP = 0.0012    # the inner face's least gap over her rest skin
UNDER = -0.8        # a point whose designed normal's y is under this is not moved (eased over 0.3)
RIM = (0.001, 0.004)    # the opening's rolled edge: carried within RIM[0] of its rim, smoothed in full past RIM[1]
RIMFIT = 0.003      # and the fits leave out its points within this of the rim (the roll doesn't bend the cup's fit)
RELAX = 30          # passes relaxing the carried shell points' moves along its edges
FOLD = 0.7          # a fit's neighbours: normals within ~45 deg of the point's (full weight past ~35)
# the dome (armor 14 s3): the cup's front at the 3-6 cm scale
DOME_SIGMA = 0.030  # the dome's fit: a Gaussian weight round the apex (the front's 3-6 cm shape, not its 1 cm detail)
DOME_RADII = (0.080, 0.140)   # the dome's radii held within these (a rounder cup is opened out to 8 cm: fuller)
DOME_R = (0.035, 0.075)   # weight 1 within DOME_R[0] of the cup's apex, easing to 0 by DOME_R[1] (and the cup's border)
DOME_TIP = 0.025    # inward moves only within this of the apex (the cone tip; eased over 10 mm past it)
DOME_RIM = (0.002, 0.008)  # the opening's rolled edge: left out of the fit within DOME_RIM[1], carried within it
DOME_FOLD = (-0.6, -0.3)   # faces turned down past n_y DOME_FOLD[0] (the fold under the cup): out of the fit and weight
CONFIG = {
    # centre (x, y) of her left cup, radii (x, y) of the full-weight ellipse (mirrored for her right), the ease past
    # it, and the least z of a point it moves
    "arcanist": dict(shell="arcanist.top.plumleather",
                     riders=("arcanist.top.thread", "arcanist.top.darkpurple", "arcanist.top.claspgold",
                             "arcanist.top.amethyst"),
                     centre=(0.08, 1.378), radii=(0.062, 0.05), ease=0.015, zmin=0.06,
                     tuck="armor_tuck/arcanist.top.bin"),
}


def _weld(P, tol=0.0):
    """Points welded by place (copies within tol: one point, so a seam's copies move alike). Returns (U, wid)."""
    _, first, wid = np.unique(np.round(P * 1e6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    U, wid = P[first].copy(), wid.ravel()
    if tol > 0:
        import scipy.sparse as sp
        from scipy.sparse.csgraph import connected_components
        pr = cKDTree(U).query_pairs(tol, output_type="ndarray")
        A = sp.coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(len(U), len(U)))
        _, lab = connected_components(A, directed=False)
        U = np.zeros((lab.max() + 1, 3))
        np.add.at(U, lab, P[first])
        U /= np.bincount(lab)[:, None]
        wid = lab[wid]
    return U, wid


def cup_weight(X, cfg, ease=None):
    """1 inside either cup's ellipse, easing to 0 over the ease past it (by distance in x, y)."""
    ease = cfg["ease"] if ease is None else ease
    cx, cy = cfg["centre"]
    rx, ry = cfg["radii"]
    w = np.zeros(len(X))
    for s in (1, -1):
        dx, dy = X[:, 0] - s * cx, X[:, 1] - cy
        r = np.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)
        rr = np.sqrt(dx ** 2 + dy ** 2) / np.maximum(r, 1e-9)    # the ellipse's radius on this point's ray
        w = np.maximum(w, _ss(1 - (r - 1) * rr / ease))
    return w * (X[:, 2] > cfg["zmin"])


def mls(Q, C, keep=None, NQ=None, NC=None, sigma=SIGMA, reach=REACH, k=160):
    """Heights of points Q over the quadric fitted (Gaussian sigma) to the cloud C round each, in its local frame
    (the weighted plane's normal n). keep: C's points the fits may use. NQ, NC: the points' (designed) normals; a
    neighbour whose normal parts from the point's past ~40 deg is left out (a fold, e.g. under the cup, is not
    bridged). Returns (h, n): Q + h n lies on the fit."""
    use = np.arange(len(C)) if keep is None else np.where(keep)[0]
    T = cKDTree(C[use])
    d, j = T.query(Q, k=k, distance_upper_bound=reach)
    ok = np.isfinite(d)
    j = np.where(ok, j, 0)
    Y = C[use][j] - Q[:, None]
    w = np.where(ok, np.exp(-0.5 * (np.where(ok, d, 0) / sigma) ** 2), 0.0)
    if NQ is not None:
        w = w * _ss((np.einsum("nkc,nc->nk", NC[use][j], NQ) - FOLD) / 0.15)
    m = (Y * w[..., None]).sum(1) / np.maximum(w.sum(1), 1e-12)[:, None]
    Z = Y - m[:, None]
    cov = np.einsum("nk,nki,nkj->nij", w, Z, Z)
    _, ev = np.linalg.eigh(cov)
    n = ev[:, :, 0]
    e1 = ev[:, :, 2]
    e2 = np.cross(n, e1)
    u, v, h = (Y * e1[:, None]).sum(2), (Y * e2[:, None]).sum(2), (Y * n[:, None]).sum(2)
    A = np.stack([u * u, u * v, v * v, u, v, np.ones_like(u)], -1)
    M = np.einsum("nk,nki,nkj->nij", w, A, A) + np.eye(6) * 1e-14
    b = np.einsum("nk,nki,nk->ni", w, A, h)
    c = np.linalg.solve(M, b[..., None])[..., 0]
    return c[:, 5], n


def _bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    d20, d21 = v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-30:
        return np.array([1.0, 0, 0])
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.array([1 - v - w, v, w])


class _Field:
    """A displacement D on a surface's points (V, F), read at any point at its closest point on the surface
    (interpolated over that triangle)."""

    def __init__(s, V, F, D, k=10):
        s.V, s.F, s.D, s.k, s.tree = V, F, D, k, cKDTree(V)
        s.vt = [[] for _ in range(len(V))]
        for t, f in enumerate(F):
            for v in f:
                s.vt[v].append(t)

    def at(s, Q):
        _, nn = s.tree.query(Q, s.k)
        out = np.zeros_like(Q)
        for i, q in enumerate(Q):
            ts = np.array(sorted({t for v in nn[i] for t in s.vt[v]}), int)
            if not len(ts):
                out[i] = s.D[nn[i][0]]
                continue
            T = s.V[s.F[ts]]
            cp = _closest_tri(q, T)
            j = np.linalg.norm(cp - q, axis=1).argmin()
            bc = np.clip(_bary(cp[j], *T[j]), 0, 1)
            out[i] = (s.D[s.F[ts[j]]] * (bc / bc.sum())[:, None]).sum(0)
        return out


def _normals(G, p, P0, P1, moved):
    """Each moved copy's stored normal plus the change of its smooth group's geometric normal (the faces round its
    welded point within 60 deg of its stored normal)."""
    I = G.get(p["indices"]).astype(np.int64).reshape(-1, 3)
    _, wid = _weld(P0)
    F = wid[I]
    nw = wid.max() + 1
    U0 = np.zeros((nw, 3)); U0[wid] = P0
    U1 = np.zeros((nw, 3)); U1[wid] = P1
    q0 = np.cross(U0[F[:, 1]] - U0[F[:, 0]], U0[F[:, 2]] - U0[F[:, 0]])
    q1 = np.cross(U1[F[:, 1]] - U1[F[:, 0]], U1[F[:, 2]] - U1[F[:, 0]])
    u0 = q0 / np.maximum(np.linalg.norm(q0, axis=1, keepdims=True), 1e-20)
    N = G.get(p["attributes"]["NORMAL"]).astype(float)
    mw = np.zeros(nw, bool); mw[wid[moved]] = True
    byw = {}
    for t in np.where(mw[F].any(1))[0]:
        for v in F[t]:
            byw.setdefault(v, []).append(t)
    out = N.copy()
    for c in np.where(moved)[0]:
        ts = np.array(byw.get(wid[c], []), int)
        if not len(ts):
            continue
        ts = ts[(u0[ts] @ N[c]) > 0.5]
        if not len(ts):
            continue
        a, b = q0[ts].sum(0), q1[ts].sum(0)
        out[c] = N[c] + b / max(np.linalg.norm(b), 1e-20) - a / max(np.linalg.norm(a), 1e-20)
    out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)
    return out


def _prim(G, name):
    return [m for m in G.g["meshes"] if m["name"] == name][0]["primitives"][0]


def _skin(art, tuck=None):
    """Her rest skin (points, normals, tree), tucked by the piece's armor_tuck record as her shader draws it (10 mm x
    the mark, all of it past 0.973; points marked 0.995 and over are not drawn: left out), as tools/armor/wearcheck.py
    reads it."""
    H = _Gl(os.path.join(art, "heroine.glb"))
    _, _, _, B, BF = _body(H)
    BN = _vn(B, BF)
    pth = os.path.join(art, tuck) if tuck else ""
    if os.path.isfile(pth):
        raw = open(pth, "rb").read()
        n = struct.unpack("<I", raw[:4])[0]
        rec = np.frombuffer(raw[4:4 + 16 * n], dtype=[("k", "<i4", 3), ("t", "<f4")])
        d = {tuple(int(v) for v in r["k"]): float(r["t"]) for r in rec}
        t = np.array([d.get(tuple(k), 0.0) for k in np.round(B * 1e5).astype(np.int64)])
        t = np.round(np.clip(t, 0, 1) * 255) / 255
        T, TN = B - (0.010 * np.where(t > 0.973, 1.0, t))[:, None] * BN, BN
        T, TN = T[t < 0.995], TN[t < 0.995]
        return B, BN, cKDTree(B), (T, TN, cKDTree(T))
    return B, BN, cKDTree(B), None


def offset(X, skin):
    """Points' offset along her normal from the nearest skin point (m); over her tucked skin when the skin has a tuck
    (never less than over her untucked skin: the tuck only takes her in; the nearest tucked point can be a neighbour
    the tuck moved off another way)."""
    B, BN, bt = skin[:3]
    _, j = bt.query(X)
    g = ((X - B[j]) * BN[j]).sum(1)
    if len(skin) > 3 and skin[3] is not None:
        g = np.maximum(g, offset(X, skin[3]))
    return g


def _fair(X, NX, fit, free, a, report=True):
    """A cup's outer points' moves onto one round dome: a quadric height field (a paraboloid: one even curvature in
    each direction) over the plane through its apex a (normal: the mean of its points' normals within 30 mm), fitted
    by least squares to the fit points (not the opening's rolled edge, not the fold under the cup) with a Gaussian
    (DOME_SIGMA) weight round the apex. Returns each point's move onto it (along the plane's normal)."""
    nz = NX[np.linalg.norm(X - a, axis=1) < 0.03].mean(0)
    nz /= np.linalg.norm(nz)
    e1 = np.cross([0.0, 1.0, 0.0], nz)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(nz, e1)
    Y = X - a
    u, v, h = Y @ e1, Y @ e2, Y @ nz
    ok = fit & ((NX @ nz) > 0.4)
    wt = np.exp(-0.5 * (np.linalg.norm(Y, axis=1) / DOME_SIGMA) ** 2) * ok
    M = np.c_[u * u, u * v, v * v, u, v, np.ones_like(u)]
    c = np.linalg.lstsq(M * np.sqrt(wt)[:, None], h * np.sqrt(wt), rcond=None)[0]
    # (its radii held within DOME_RADII: a cup rounder than the smallest is opened out to it, about the apex: fuller)
    k, ev = np.linalg.eigh(np.array([[2 * c[0], c[1]], [c[1], 2 * c[2]]]))
    k = np.clip(k, -1 / DOME_RADII[0], -1 / DOME_RADII[1])
    S = ev @ np.diag(k) @ ev.T
    c[0], c[1], c[2] = S[0, 0] / 2, S[0, 1], S[1, 1] / 2
    d = M @ c - h
    if report:
        q = free & ok
        print("BUST_DOME: cup at x %+.3f: dome radii %.1f, %.1f cm; moves over its weight %.2f..%.2f mm" %
              (a[0], -100 / k[0], -100 / k[1], d[q].min() * 1000, d[q].max() * 1000))
    return d[:, None] * nz


def plan(G, cfg, skin, report=True, dome=False):
    """The shell's welded points U, their displacement D, the outer mask, the field over the outer surface. dome: the
    s3 step (the cup's front onto a large-scale fit) instead of the 1-3 cm smoothing."""
    tag = "BUST_DOME" if dome else "BUST_SHELL"
    B, BN, bt = skin[:3]
    p = _prim(G, cfg["shell"])
    P0 = G.get(p["attributes"]["POSITION"]).astype(float)
    N0 = G.get(p["attributes"]["NORMAL"]).astype(float)
    U, wid = _weld(P0, 0.0001)
    F = wid[G.get(p["indices"]).astype(np.int64).reshape(-1, 3)]
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 2] != F[:, 0])]
    # outer: the welded points whose copies' normals all face out of her (her normal at the nearest skin point)
    _, bj = bt.query(U)
    nd = np.full(len(U), 9.0)
    np.minimum.at(nd, wid, (N0 * BN[bj[wid]]).sum(1))
    NU = np.zeros_like(U)
    np.add.at(NU, wid, N0)
    NU /= np.maximum(np.linalg.norm(NU, axis=1, keepdims=True), 1e-12)
    # (the cup's underside, turning under to her ribs, is not moved: its designed normal facing down past UNDER)
    W = cup_weight(U, cfg) * _ss((NU[:, 1] - UNDER) / 0.3)
    reg = cup_weight(U, cfg, cfg["ease"] + REACH + 0.01) > 0
    outer = (nd > 0.5) & reg
    oi = np.where(outer)[0]
    X = U[oi].copy()
    live = W[oi] > 0
    # (the opening's rolled edge is carried, not smoothed: the weight eases in over RIM off the rim)
    rim = np.where((np.abs(nd) <= 0.5) & reg)[0]
    drim = cKDTree(U[rim]).query(X)[0] if len(rim) else np.full(len(X), 1.0)
    rr = DOME_RIM if dome else RIM
    ramp = _ss((drim - rr[0]) / (rr[1] - rr[0]))
    w = W[oi] * ramp
    if dome:
        # (weight: 1 round each cup's apex (its outer face's most forward point), easing to 0 by DOME_R[1] and at the
        # cup's border; not on the fold under the cup)
        X0 = U[oi]
        side = np.where(X0[:, 0] >= 0, 0, 1)
        dap = np.full(len(X0), 9.0)
        apex = []
        for sd, sg in ((0, 1), (1, -1)):
            q = np.where((side == sd) & (cup_weight(X0, cfg) > 0.999))[0]
            a = X0[q[X0[q, 2].argmax()]]
            dap[side == sd] = np.linalg.norm(X0[side == sd] - a, axis=1)
            apex.append(a)
            if report:
                print("BUST_DOME: apex %+d at %s" % (sg, np.round(a, 3)))
        wd = _ss((DOME_R[1] - dap) / (DOME_R[1] - DOME_R[0])) * cup_weight(X0, cfg) * \
            _ss((NU[oi][:, 1] - DOME_FOLD[0]) / (DOME_FOLD[1] - DOME_FOLD[0]))
        w = wd * ramp
        live = w > 0
        tip = _ss((DOME_TIP + 0.010 - dap) / 0.010)
        fitpts = (drim > DOME_RIM[1]) & (NU[oi][:, 1] > DOME_FOLD[0])
    # (and moves with the surface beside it: its points take the Gaussian (5 mm) mean move of the points past the ramp)
    edge = np.where(live & (ramp < 0.999))[0]
    core = np.where(ramp >= 0.999)[0]
    de, je = cKDTree(X[core]).query(X[edge], k=48, distance_upper_bound=0.015)
    ke = np.where(np.isfinite(de), np.exp(-0.5 * (np.where(np.isfinite(de), de, 0) / 0.005) ** 2), 0.0)
    je = np.where(np.isfinite(de), je, 0)
    ke /= np.maximum(ke.sum(1, keepdims=True), 1e-12)
    NX = NU[oi]
    # her skin under: each outer point's least offset over her (tucked) skin so the inner face under it keeps MIN_GAP
    # (the inner points under an outer point: those nearest it; only where the cup's weight moves it)
    inn = np.where((nd < -0.5) & (cup_weight(U, cfg, cfg["ease"] + 0.01) > 0))[0]
    go = offset(X, skin)
    own = cKDTree(X).query(U[inn])[1]
    gi = offset(U[inn], skin)
    req = np.full(len(X), -1.0)
    np.maximum.at(req, own, go[own] - gi + MIN_GAP)
    _, bj = bt.query(X)
    out_n = BN[bj]
    keep0 = drim > RIMFIT
    keep = keep0.copy()
    held = 0
    for it in range(1 if dome else ITERS):
        if dome:
            # (each cup's front faired as a thin plate over its apex plane: out freely, in only at the apex)
            mv = np.zeros_like(X)
            for sd in (0, 1):
                q = side == sd
                mv[q] = _fair(X[q], NX[q], fitpts[q], w[q] > 0.5, apex[sd], report)
            nm = (mv * NX).sum(1)
            mv -= (np.minimum(nm, 0) * (1 - tip))[:, None] * NX
            X[live] += w[live, None] * mv[live]
        else:
            h, n = mls(X[live], X, keep, NX[live], NX)
            # (moved along its designed normal, onto the fit: no sliding along the surface)
            c = np.abs((n * NX[live]).sum(1))
            X[live] += (w[live] * h * np.sign((n * NX[live]).sum(1)) / np.maximum(c, 0.5))[:, None] * NX[live]
        if cfg.get("mirror", True):
            # (the fuller of the cup and its mirror: each point out to its mirror's surface where that is proud)
            M = X.copy(); M[:, 0] *= -1
            d, j = cKDTree(M).query(X[live])
            up = ((M[j] - X[live]) * NX[live]).sum(1)
            up = np.where((d < 0.004) & (up > 0), up, 0.0) * w[live]
            X[live] += up[:, None] * NX[live]
        Dc = X[core] - U[oi][core]
        X[edge] = U[oi][edge] + ramp[edge, None] * (X[edge] - U[oi][edge]) +             (1 - ramp[edge])[:, None] * (Dc[je] * ke[..., None]).sum(1)
        lo = np.maximum(req[live] - offset(X[live], skin), 0)
        held = int((lo > 1e-6).sum())
        if held:
            # (a smooth rise, not a spike: each point out by the most any point needs, falling off as a 6 mm Gaussian)
            li = np.where(live)[0]
            hi = li[lo > 1e-6]
            dd, jj = cKDTree(X[hi]).query(X[li], k=min(32, len(hi)), distance_upper_bound=0.018)
            dd, jj = dd.reshape(len(li), -1), jj.reshape(len(li), -1)
            ok = np.isfinite(dd)
            g = np.where(ok, lo[lo > 1e-6][np.where(ok, jj, 0)] * np.exp(-0.5 * (np.where(ok, dd, 0) / 0.006) ** 2), 0)
            # (along the point's own normal, by what her normal's share of it needs)
            X[li] += (g.max(1) / np.maximum((NX[li] * out_n[li]).sum(1), 0.5))[:, None] * NX[li]
        if dome:
            pass
        elif it < ITERS - 4:
            r, _ = mls(X, X, keep, NX, NX)
            keep = keep0 & (np.abs(r) < ROBUST)
        else:
            keep = keep0.copy()
    D = np.zeros_like(U)
    # (the move itself averaged over 1.5 mm: points closer than the mesh's spacing, e.g. at a V's tip, move alike)
    dd, jj = cKDTree(U[oi]).query(U[oi], k=16, distance_upper_bound=0.004)
    ok = np.isfinite(dd)
    g = np.where(ok, np.exp(-0.5 * (np.where(ok, dd, 0) / 0.0015) ** 2), 0)
    D[oi] = ((X - U[oi])[np.where(ok, jj, 0)] * g[..., None]).sum(1) / g.sum(1)[:, None]
    remap = -np.ones(len(U), int); remap[oi] = np.arange(len(oi))
    ofld = _Field(U[oi], remap[F[outer[F].all(1)]], D[oi])
    rest = np.where(~outer & (cup_weight(U, cfg, cfg["ease"] + 0.01) > 0))[0]
    D[rest] = ofld.at(U[rest])
    # (then relaxed over the shell's own edges, the outer points held: a rim's side wall between two sheets would
    # otherwise take one sheet's move or the other's point by point)
    E = np.unique(np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1), axis=0)
    E = np.r_[E, E[:, ::-1]]
    deg = np.bincount(E[:, 0], minlength=len(U)).astype(float)
    isr = np.zeros(len(U), bool); isr[rest] = True
    isr[oi[~live]] = cup_weight(U[oi[~live]], cfg, cfg["ease"] + 0.01) > 0     # (and the outer points it didn't move)
    for _ in range(RELAX):
        S = np.zeros_like(D)
        np.add.at(S, E[:, 0], D[E[:, 1]])
        D[isr] = 0.5 * D[isr] + 0.5 * S[isr] / np.maximum(deg[isr], 1)[:, None]
    # the riders' carrier: the whole shell round the cups
    near = cup_weight(U, cfg, cfg["ease"] + 0.02) > 0
    fld = _Field(U[near], (np.cumsum(near) - 1)[F[near[F].all(1)]], D[near])
    if report and held:
        print(tag + ": %d outer points held out so the inner face keeps %.1f mm over her skin" % (held, MIN_GAP * 1000))
    if report:
        print(tag + ": %d outer points smoothed (%d at full weight), %d shell points carried, largest move %.2f mm" %
              (int(live.sum()), int((w > 0.999).sum()), len(rest), np.linalg.norm(D, axis=1).max() * 1000))
    return U, wid, D, outer, fld


def shell(path, cfg, art, force=False, report=True, dome=False):
    """The step on one outfit gltf, in place; returns the largest move (m), or None when it has had it. dome: the s3
    step (done-mark DOME_MARK; it drops the convexity bake's mark, so detail() bakes again from the new shape)."""
    G = _Gl(path)
    mark, tag = (DOME_MARK, "BUST_DOME") if dome else (MARK, "BUST_SHELL")
    if G.g.get("asset", {}).get("extras", {}).get(mark) is not None and not force:
        print("%s: %s has had it" % (tag, os.path.basename(path)))
        return None
    U, wid, D, outer, fld = plan(G, cfg, _skin(art, cfg.get("tuck")), report, dome)
    big = 0.0
    for name in (cfg["shell"],) + tuple(cfg["riders"]):
        pr = _prim(G, name)
        Pp = G.get(pr["attributes"]["POSITION"]).astype(float)
        if name == cfg["shell"]:
            mvp = D[wid]
        else:
            mvp = np.zeros_like(Pp)
            sel = np.where(cup_weight(Pp, cfg, cfg["ease"] + 0.01) > 0)[0]
            if len(sel):
                mvp[sel] = fld.at(Pp[sel])
        moved = np.linalg.norm(mvp, axis=1) > 1e-7
        if not moved.any():
            continue
        P1 = Pp + mvp
        G.put(pr["attributes"]["POSITION"], P1.astype(np.float32))
        if "NORMAL" in pr["attributes"]:
            G.put(pr["attributes"]["NORMAL"], _normals(G, pr, Pp, P1, moved).astype(np.float32))
        P1f = G.get(pr["attributes"]["POSITION"]).astype(float)
        a = G.g["accessors"][pr["attributes"]["POSITION"]]
        a["min"], a["max"] = P1f.min(0).tolist(), P1f.max(0).tolist()
        mm = float(np.linalg.norm(mvp, axis=1).max())
        big = max(big, mm)
        if report:
            print(tag + ":   %s: %d points moved, largest %.2f mm" % (name, int(moved.sum()), mm * 1000))
    ex = G.g.setdefault("asset", {}).setdefault("extras", {})
    ex[mark] = round(big * 1000, 3)
    if dome:
        ex.pop(DMARK, None)
    G.save()
    return big


# ------------------------------------------------------------------------------------------ the baked detail --
DMARK = "bust_detail"
DSIGMA = 0.020      # the convexity's smoothing over the cups (m)
DFLOOR = 0.45       # no less convex than this over the cups: the shader's `hollow` (darker, rougher) starts under 0.45
DEDGE = (0.004, 0.008)  # the opening's rolled edge (baked edge distance, m) keeps its own value, eased in over this


def _convexity(P, N, I):
    """heroine_outfits.detail's convexity of each point (0.5 flat; over it convex), from the welded shape: how far it
    stands out from the mean of its edge neighbours along its normal per mean edge length, smoothed over ~12 mm."""
    import scipy.sparse as sparse
    U, wid = _weld(P)
    T = wid[I]
    NU = np.zeros_like(U)
    np.add.at(NU, wid, N)
    NU /= np.maximum(np.linalg.norm(NU, axis=1, keepdims=True), 1e-12)
    e = np.unique(np.sort(np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1), axis=0)
    e = e[e[:, 0] != e[:, 1]]
    Am = sparse.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])),
                           shape=(len(U), len(U))).tocsr()
    Am.data[:] = 1
    deg = np.asarray(Am.sum(1)).ravel()
    has = deg > 0
    mnb = lambda x: np.where(has if x.ndim == 1 else has[:, None],
                             (Am @ x) / np.maximum(deg, 1).reshape((-1,) + (1,) * (x.ndim - 1)), x)
    L = np.linalg.norm(U[e[:, 0]] - U[e[:, 1]], axis=1)
    el = np.zeros(len(U))
    np.add.at(el, e[:, 0], L)
    np.add.at(el, e[:, 1], L)
    el = el / np.maximum(deg, 1) + 1e-6
    c = np.where(has, -((mnb(U) - U) * NU).sum(1) / el, 0.0)
    for _ in range(int(np.clip((0.012 / max(float(np.median(el)), 1e-4)) ** 2, 3, 120))):
        c = 0.5 * c + 0.5 * mnb(c)
    return (np.tanh(c * 4) * 0.5 + 0.5)[wid]


def detail(path, cfg, art, force=False, report=True):
    """The leather's baked convexity over the cups made to match the smooth shell (armor 14 s2). heroine_outfits.detail
    bakes each point's convexity (UV2.y: the shader's leather is lighter and glossier where it is over 0.55, darker
    and rougher under 0.45) from the piece as made, so the old nipple poke and the hollow at her lower inner cup stayed
    in it after the shell step smoothed the shape: dips to 0.34 under each cup's apex toward the zip (a dark, rough
    trail: the crease) round an apex at 0.45 (a lighter, glossier spot: the poke). Over the cups' outward faces (the
    cup weight, eased off within DEDGE of the opening's edge and on faces turned down past n_y -0.7..-0.85: the fold under the cup keeps
    its crease) the value becomes its Gaussian (DSIGMA) mean over the outer face, floored at DFLOOR. The rest of the
    leather, its inner face and the riders are left as baked. Idempotent: done-mark DMARK (the largest change)."""
    G = _Gl(path)
    if G.g.get("asset", {}).get("extras", {}).get(DMARK) is not None and not force:
        print("BUST_DETAIL: %s has had it" % os.path.basename(path))
        return None
    pr = _prim(G, cfg["shell"])
    A = pr["attributes"]
    P = G.get(A["POSITION"]).astype(float)
    N = G.get(A["NORMAL"]).astype(float)
    D = G.get(A["TEXCOORD_1"]).astype(float)
    # (s3: the convexity baked again from the piece's current shape, heroine_outfits.detail's formula, so a shape step
    # before this (the dome) is what the shader sees; then smoothed and floored as below)
    cs = _convexity(P, N, G.get(pr["indices"]).astype(np.int64).reshape(-1, 3))
    B, BN, bt = _skin(art)[:3]
    _, j = bt.query(P)
    out = (N * BN[j]).sum(1) > 0.5
    w = cup_weight(P, cfg) * out * _ss((D[:, 0] - DEDGE[0]) / (DEDGE[1] - DEDGE[0])) * _ss((N[:, 1] + 0.85) / 0.15)
    U, wid = _weld(P[out])
    cu = np.zeros(len(U))
    np.add.at(cu, wid, cs[out])
    cu /= np.bincount(wid, minlength=len(U))
    nu = np.zeros_like(U)
    np.add.at(nu, wid, N[out])
    nu /= np.maximum(np.linalg.norm(nu, axis=1, keepdims=True), 1e-12)
    sel = np.where(w > 0)[0]
    T = cKDTree(U)
    nb = T.query_ball_point(P[sel], 3 * DSIGMA)
    sm = np.empty(len(sel))
    for k, (i, js) in enumerate(zip(sel, nb)):
        js = np.asarray(js)
        g = np.exp(-0.5 * (np.linalg.norm(U[js] - P[i], axis=1) / DSIGMA) ** 2) * _ss((nu[js] @ N[i] - FOLD) / 0.15)
        sm[k] = (g * cu[js]).sum() / max(g.sum(), 1e-12)
    new = D[:, 1].copy()
    new[sel] = D[sel, 1] + w[sel] * (np.maximum(sm, DFLOOR) - D[sel, 1])
    if report:
        q = sel[w[sel] > 0.999]
        print("BUST_DETAIL: from the shape over the cups p1/p50/p99 %.3f/%.3f/%.3f; set %.3f..%.3f" %
              (*np.percentile(cs[q], [1, 50, 99]), new[q].min(), new[q].max()))
    big = float(np.abs(new - D[:, 1]).max())
    D[:, 1] = new
    G.put(A["TEXCOORD_1"], D.astype(np.float32))
    G.g.setdefault("asset", {}).setdefault("extras", {})[DMARK] = round(big, 4)
    G.save()
    if report:
        print("BUST_DETAIL: %s: %d points' convexity set, largest change %.3f" % (cfg["shell"], len(sel), big))
    return big


def main(a):
    pos = [x for x in a if not x.startswith("--")]
    art = pos[0] if pos else "godot/art/people"
    for o in pos[1:] or ["arcanist"]:
        pth = os.path.join(art, "heroine_outfit_%s.gltf" % o)
        if os.path.exists(pth) and o in CONFIG:
            shell(pth, CONFIG[o], art, force="--force" in a)
            shell(pth, CONFIG[o], art, force="--force" in a, dome=True)
            detail(pth, CONFIG[o], art, force="--force" in a)


if __name__ == "__main__":
    main(sys.argv[1:])
