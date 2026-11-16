"""The kit's lower half (lane D, 16 Nov 2026): recipes for tools/armor/kit_build.py (build.json "module": "kit_hips").

    python tools/armor/kit_build.py kit_brief     (first: the belt rides over it)
    python tools/armor/kit_build.py kit_belt      (reads kit_bodice.glb and kit_brief.glb: it rides over both)

brief  a high-cut gunmetal brief: her own skin patch (subdivided once) cut by a field (waist top under the belt, leg
       lines high at the hip, cheeky at the back), smoothed (bridges the cleft), pushed out to `clear`, a shell with a
       gold rolled rim on every edge.
belt   a wide brown leather belt (a ruled band over the bodice's lower edge and the brief), gold studs, a big square
       gold buckle, two keeper tabs with gold rings; hanging from it, rigid by CLEARANCE: a V-pointed front tasset
       (centre keel, gold rim), hip plates and back plates each side (gold rim, a raised gold interlace band).
Every measure is in the piece's build.json.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_build as kb  # noqa: E402
from native_build import Part, U, buckle, grid_tris, raycast, rivet, vertex_normals  # noqa: E402

smooth01 = kb.smooth01


# ---------------------------------------------------------------- mesh helpers

def subdivide(V, F):
    """1 -> 4 midpoint split (shared edge points)."""
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    Eu, inv = np.unique(E, axis=0, return_inverse=True)
    inv = inv.ravel()
    m = len(V) + np.arange(len(Eu))
    V2 = np.vstack([V, 0.5 * (V[Eu[:, 0]] + V[Eu[:, 1]])])
    n = len(F)
    a, b, c = m[inv[:n]], m[inv[n:2 * n]], m[inv[2 * n:]]
    F2 = np.vstack([np.c_[F[:, 0], a, c], np.c_[a, F[:, 1], b], np.c_[c, b, F[:, 2]], np.c_[a, b, c]])
    return V2, F2


def clip(V, F, g):
    """The part of a triangle mesh where g > 0 (cut on its edges by linear crossing)."""
    key, NV = {}, [V]
    nv = [len(V)]

    def cut(i, j):
        k = (min(i, j), max(i, j))
        if k not in key:
            t = g[i] / (g[i] - g[j])
            NV.append((V[i] + (V[j] - V[i]) * t)[None])
            key[k] = nv[0]
            nv[0] += 1
        return key[k]

    out = []
    for f in F:
        s = g[f] > 0
        if s.all():
            out.append(f)
        elif s.any():
            k = int(np.argmax(s != np.roll(s, 1))) if s.sum() == 1 else None
            if s.sum() == 1:
                i = int(np.nonzero(s)[0][0])
                a, b, c = f[i], f[(i + 1) % 3], f[(i + 2) % 3]
                out.append([a, cut(a, b), cut(a, c)])
            else:
                i = int(np.nonzero(~s)[0][0])
                a, b, c = f[i], f[(i + 1) % 3], f[(i + 2) % 3]
                ab, ac = cut(a, b), cut(a, c)
                out += [[ab, b, c], [ab, c, ac]]
            del k
    V2 = np.vstack(NV)
    F2 = np.array(out, np.int64)
    used = np.unique(F2)
    remap = np.full(len(V2), -1)
    remap[used] = np.arange(len(used))
    return V2[used], remap[F2]


def weld(V, F, tol=1e-6):
    q = np.round(V / tol).astype(np.int64)
    _, idx, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    F = inv.ravel()[F]
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 2] != F[:, 0])]
    return V[idx], F


def boundary_loops(F):
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    k = np.sort(E, 1)
    u, c = np.unique(k, axis=0, return_counts=True)
    bset = {tuple(e) for e in u[c == 1]}
    nxt = {}
    for a, b in E:
        if (min(a, b), max(a, b)) in bset:
            nxt[a] = b
    loops, seen = [], set()
    for s in list(nxt):
        if s in seen:
            continue
        L, v = [], s
        while v not in seen and v in nxt:
            seen.add(v)
            L.append(v)
            v = nxt[v]
        if len(L) > 3:
            loops.append(np.array(L))
    return loops


def laplace(P, F, it, fixed=None, lam=0.5):
    n = len(P)
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E = np.vstack([E, E[:, ::-1]])
    deg = np.bincount(E[:, 0], minlength=n).astype(float)
    for _ in range(it):
        S = np.zeros_like(P)
        np.add.at(S, E[:, 0], P[E[:, 1]])
        Q = S / np.maximum(deg, 1)[:, None]
        mv = lam * (Q - P)
        if fixed is not None:
            mv[fixed] = 0
        P = P + mv
    return P


def shell(name, mat, P, F, N, thick, col_w=1.0):
    """A closed shell from an open patch: inner P, outer P + N thick, walls on its boundary."""
    rn = kb.rand01(name)
    parts = []
    for Q, sgn in ((P + N * thick, 1), (P, -1)):
        T = kb.orient(Q, F, N * sgn)
        parts.append(Part(name, mat, Q, T, uv0=np.c_[Q[:, 0] + Q[:, 2], Q[:, 1]] * 3.0,
                          col=np.tile([1.0, rn, 0.0, col_w], (len(Q), 1))))
    cen = P[F].mean(1)
    for L in boundary_loops(F):
        a, b = P[L], P[L] + N[L] * thick
        nb = len(L)
        V = np.vstack([a, b])
        T = grid_tris(2, nb, close=True)
        mid = 0.5 * (a + np.roll(a, -1, 0))
        # outward of the edge: away from the patch's nearest face centre
        from scipy.spatial import cKDTree
        _, ci = cKDTree(cen).query(mid)
        out = U(mid - cen[ci])
        T = kb.orient(V, T, np.vstack([out, out]))
        parts.append(Part(name, mat, V, T, uv0=np.c_[V[:, 0] + V[:, 2], V[:, 1]] * 3.0,
                          col=np.tile([1.0, rn, 0.0, 0.0], (len(V), 1))))
    return Part.join(name, mat, parts)


class Normals:
    """A stand-in Ref for kb.bead on a plate: closest() gives the plate's own normal at the nearest point."""

    def __init__(self, P, N):
        from scipy.spatial import cKDTree
        self.P, self.N, self.t = P, N, cKDTree(P)

    def closest(self, X):
        d, i = self.t.query(np.asarray(X, float))
        return self.P[i], self.N[i], d


def torus(c, n, up, R, r, name, mat, seg=28, tube=8):
    n, up = U(np.asarray(n, float)), U(np.asarray(up, float))
    x = U(np.cross(up, n))
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    b = np.linspace(0, 2 * np.pi, tube, endpoint=False)
    ring = np.cos(a)[:, None] * x + np.sin(a)[:, None] * up
    P = (c + ring[:, None, :] * (R + r * np.cos(b))[None, :, None] + n * (r * np.sin(b))[None, :, None]).reshape(-1, 3)
    T = grid_tris(seg, tube, close=True)
    T = np.vstack([T, T])[:len(T)]
    # wrap the seg rows too
    i = np.arange(tube)
    last = np.c_[(seg - 1) * tube + i, (seg - 1) * tube + (i + 1) % tube, (i + 1) % tube]
    last2 = np.c_[(seg - 1) * tube + i, (i + 1) % tube, i]
    T = np.vstack([T, last, last2])
    D = (P.reshape(seg, tube, 3) - (c + ring * R)[:, None, :]).reshape(-1, 3)
    T = kb.orient(P, T, D)
    return Part(name, mat, P, T, uv0=P[:, :2] * 2.5, uv1=np.tile([0.0, 0.9], (len(P), 1)),
                col=np.tile([0.95, kb.rand01(name), 0.0, 0.0], (len(P), 1)))


# ---------------------------------------------------------------- the brief

def bodice_bot(th, b):
    a = np.abs(th)
    v = b["point"] + (b["hip"] - b["point"]) * np.clip(a / b["v_theta"], 0, 1)
    return np.where(a > b["v_theta"], b["hip"] + (b["back_bot"] - b["hip"]) * smooth01((a - b["v_theta"]) / (180 - b["v_theta"])), v)


def belt_line(th, bl):
    """The belt's centre height round her (theta 0 front): low at the front (slung over the bodice's V), high at the hip."""
    a = np.abs(np.asarray(th, float))
    s = smooth01(a / bl["side_th"])
    y = bl["front_y"] + (bl["side_y"] - bl["front_y"]) * s
    return y + (bl["back_y"] - bl["side_y"]) * smooth01((a - bl["side_th"]) / (180 - bl["side_th"]))


def live_lines(cfg):
    """(build.json "live": true) the bodice's bottom line and the belt's line read from their own build.json, so the
    brief always tucks under what they are now (the bodice is another builder's)."""
    if not cfg.get("live"):
        return
    for key, pid, sub in (("bodice", "kit_bodice", "corset"), ("belt", "kit_belt", "belt")):
        f = os.path.join(kb.SRC, pid, "build.json")
        if os.path.exists(f):
            src = json.load(open(f, encoding="utf-8"))[sub]
            cfg[key] = {k: src[k] for k in cfg[key]}


def brief(cfg, ref):
    live_lines(cfg)
    M, bc, bl = cfg["mat"], cfg["brief"], cfg["belt"]
    z0 = cfg["axis_z"]
    V, F = ref.V, ref.T
    c = V[F].mean(1)
    sel = F[(c[:, 1] > bc["y_min"]) & (c[:, 1] < bc["y_max"]) & (np.abs(c[:, 0]) < 0.25)]
    used = np.unique(sel)
    remap = np.full(len(V), -1)
    remap[used] = np.arange(len(used))
    P, T = V[used], remap[sel]
    for _ in range(bc.get("subdiv", 1)):
        P, T = subdivide(P, T)
        P, _, _ = ref.closest(P)  # (new points back onto her skin)

    def field(X):
        th = np.degrees(np.arctan2(X[:, 0], X[:, 2] - z0))
        top = np.minimum(belt_line(th, bl) - bl["w"] / 2 + bc["tuck"], bodice_bot(th, cfg["bodice"]) - bc["under_bodice"])
        s = np.abs(X[:, 0])
        lf, lb = bc["leg_front"], bc["leg_back"]
        hF = lf["y0"] + (lf["y1"] - lf["y0"]) * np.clip(s / lf["s1"], 0, 1) ** lf["p"]
        hB = lb["y0"] + (lb["y1"] - lb["y0"]) * np.clip(s / lb["s1"], 0, 1) ** lb["p"]
        wf = smooth01((X[:, 2] - bc["z_mid"] + 0.03) / 0.06)
        h = np.minimum(wf * hF + (1 - wf) * hB, top - bc["side_w"])
        return np.minimum(top - X[:, 1], X[:, 1] - h)

    P, T = clip(P, T, field(P))
    P, T = weld(P, T, 1e-7)
    # keep the largest component
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    A = sp.coo_matrix((np.ones(len(T) * 3), (np.repeat(T[:, 0], 3), T.ravel())), shape=(len(P), len(P)))
    nc, lab = connected_components(A + A.T, directed=False)
    big = np.argmax(np.bincount(lab[T[:, 0]]))
    T = T[lab[T[:, 0]] == big]
    used = np.unique(T)
    remap = np.full(len(P), -1)
    remap[used] = np.arange(len(used))
    P, T = P[used], remap[T]
    # lift: her normal x clear, then smoothed (bridges the cleft and the crease) and never under clear_min
    q, n, _ = ref.closest(P)
    Q = q + n * cfg["clear"]
    bnd = np.concatenate(boundary_loops(T))
    Q = laplace(Q, T, bc["smooth"], lam=0.5)
    for _ in range(4):
        q, n, _ = ref.closest(Q)
        cl = ((Q - q) * n).sum(1)
        low = cl < cfg["clear_min"]
        Q[low] += n[low] * (cfg["clear_min"] - cl[low] + 1e-4)[:, None]
        Q = laplace(Q, T, 2, lam=0.3)
    q, n, _ = ref.closest(Q)
    cl = ((Q - q) * n).sum(1)
    low = cl < cfg["clear_min"]
    Q[low] += n[low] * (cfg["clear_min"] - cl[low] + 1e-4)[:, None]
    N = vertex_normals(Q, T)
    N = np.where(((N * n).sum(1) < 0)[:, None], -N, N)
    plate = [shell("brief", M["plate"], Q, T, N, cfg["thick"])]
    trim = []
    rim = cfg["rim"]
    for k, L in enumerate(boundary_loops(T)):
        trim.append(kb.bead(ref, f"trim_brief{k}", M["trim"], Q[L], rim, cfg["thick"] * 0.5 + 0.0003, True, relax_it=2))
    del bnd
    return plate, trim, [], []


# ---------------------------------------------------------------- the belt and its plates

def under_mesh(ref, files):
    """Her torso faces + the pieces she wears under the belt, as one mesh (n_skin: her faces come first)."""
    import gear_native as gn
    V, F = [ref.V], [ref.torso]
    off = len(ref.V)
    for f in files:
        for p in gn.read_parts(f):
            V.append(p["P"].astype(float))
            F.append(p["T"] + off)
            off += len(p["P"])
    return np.vstack(V), np.vstack(F), len(ref.torso)


def outer_rho(UV, UF, nsk, wrap, Y, TH, R=0.42):
    """Per (y, theta): the outermost surface along the wrap ray (cast inward from R); is it her skin."""
    D = wrap.dirs(TH.ravel())
    O = wrap.pt(Y.ravel(), TH.ravel(), np.full(Y.size, R))
    t, i = raycast(UV, UF, O, -D, R, chunk=64)
    rho = (R - t).reshape(Y.shape)
    return rho, (i < nsk).reshape(Y.shape)


def hang(ref, wrap, name, ths, y_top, rho_top, length, a0, need, it=8, sig=1.5, rows=14, a_max=None):
    """A rigid hanging plate: columns at ths from (y_top, rho_top) down a cone tilted a0 (deg) out from vertical,
    each column's tilt raised until every point stands `need` (m, per row fraction) off her skin. Returns the inner
    grid (rows, cols, 3), its outward normals and the tilts."""
    from scipy.ndimage import gaussian_filter1d
    C = len(ths)
    a = np.full(C, np.radians(a0))
    v = np.linspace(0, 1, rows)[:, None] * length[None, :]
    o = wrap.dirs(ths)
    T0 = wrap.pt(y_top, ths, rho_top)
    nd = need(np.linspace(0, 1, rows))[:, None]

    def grid(a):
        d = np.array([0, -1.0, 0])[None, :] * np.cos(a)[:, None] + o * np.sin(a)[:, None]
        return T0[None] + v[..., None] * d[None]

    for _ in range(it):
        G = grid(a)
        q, n, _ = ref.closest(G.reshape(-1, 3))
        cl = ((G.reshape(-1, 3) - q) * n).sum(1).reshape(G.shape[:2])
        defi = np.max(np.where(v > 0.004, (nd - cl) / np.maximum(v, 1e-3), -1), 0)
        if (defi <= 1e-4).all():
            break
        a = a + np.clip(defi, 0, None) * 1.1
        a = np.maximum(a, gaussian_filter1d(a, sig, mode="nearest"))
        if a_max is not None:  # (a plate never flares past a_max: the design hangs them near her line)
            a = np.minimum(a, np.radians(a_max))
    G = grid(a)
    du = np.gradient(G, axis=1)
    dv = np.gradient(G, axis=0)
    N = U(np.cross(dv, du))
    N = np.where(((N * o[None]).sum(-1) < 0)[..., None], -N, N)
    return G, N, np.degrees(a)


def interlace(G, Nn, j0, j1, v0, v1, wl, name, mat, ref_n, beads):
    """A raised gold interlace band on a plate grid between columns j0..j1 and rows-fractions v0..v1: two borders
    and two crossing waves (a plait), plus a small boss at each crossing's eye."""
    R, C = G.shape[:2]
    from scipy.interpolate import RegularGridInterpolator
    gi = RegularGridInterpolator((np.linspace(0, 1, R), np.arange(C)), G)
    ni = RegularGridInterpolator((np.linspace(0, 1, R), np.arange(C)), Nn)
    rm = int(R * (v0 + v1) / 2)
    span = np.linalg.norm(G[rm, int(round(j1))] - G[rm, int(round(j0))])
    js = np.linspace(j0, j1, max(int(span / 0.0015), 20))
    s = (js - j0) / max(j1 - j0, 1e-6) * span
    mid, amp = (v0 + v1) / 2, (v1 - v0) / 2 * 0.72
    out = []
    lines = [np.full_like(js, v0), np.full_like(js, v1)]
    for ph in (0.0, np.pi):
        lines.append(mid + amp * np.sin(2 * np.pi * s / wl + ph))
    for k, vv in enumerate(lines):
        X = np.stack([vv, js], 1)
        E = gi(X)
        Nq = ni(X)
        rim = beads[0] if k < 2 else beads[1]
        out.append(kb.bead(Normals(E, U(Nq)), f"{name}{k}", mat, E, rim, ref_n, False, relax_it=1))
    return out


def belt(cfg, ref):
    M, bl, z0 = cfg["mat"], cfg["belt"], cfg["axis_z"]
    under = [os.path.join(kb.SRC, f, f + ".glb") for f in cfg["under"]]
    UV, UF, nsk = under_mesh(ref, under)
    wrap = kb.Wrap(ref, z0, 0.90, 1.16)
    plate, trim, straps, rigid = [], [], [], []
    hw = bl["w"] / 2
    TH = np.arange(-180.0, 180.0, bl["col_step"])
    Cn = len(TH)
    yc = belt_line(TH, bl)
    rows = 7
    w = np.linspace(-1, 1, rows)
    Y = yc[None, :] + w[:, None] * hw
    THg = np.broadcast_to(TH[None], Y.shape)
    # what she wears there, sampled finer across the band
    ws = np.linspace(-1.15, 1.15, 13)
    Ys = yc[None, :] + ws[:, None] * hw
    rho_u, is_skin = outer_rho(UV, UF, nsk, wrap, Ys, np.broadcast_to(TH[None], Ys.shape))
    need = rho_u + np.where(is_skin, cfg["clear"], bl["gap"])
    need = np.where(np.isfinite(need), need, np.nan)
    need = kb.fill_rows(need)
    # ruled across: a line in y per column over every need point, smoothed round her
    from scipy.ndimage import gaussian_filter1d, maximum_filter1d
    A = np.c_[np.ones(len(ws)), ws * hw]
    coef = np.linalg.lstsq(A, need, rcond=None)[0]  # (2, C)
    coef = np.stack([gaussian_filter1d(coef[k], bl["sig"], mode="wrap") for k in range(2)])
    lift = np.max(need - A @ coef, 0)
    lift = gaussian_filter1d(maximum_filter1d(lift, 5, mode="wrap"), 1.5, mode="wrap")
    lift = np.maximum(lift, np.max(need - A @ coef, 0))
    rho_in = (np.c_[np.ones(rows), w * hw] @ coef) + lift[None]
    Pin = wrap.pt(Y, THg, rho_in)
    Nout = wrap.dirs(THg)
    bt = bl["thick"]
    straps.append(kb.slab("belt", M["strap"], Pin, Nout, bt, closed_c=True))

    def belt_pt(y, th, up):
        th = np.atleast_1d(np.asarray(th, float))
        y = np.atleast_1d(np.asarray(y, float))
        j = np.interp((th + 180) % 360 - 180, np.r_[TH, 180.0], np.arange(Cn + 1)) % Cn
        j0 = np.floor(j).astype(int)
        f = j - j0
        cf = coef[:, j0] * (1 - f) + coef[:, (j0 + 1) % Cn] * f
        lf = lift[j0] * (1 - f) + lift[(j0 + 1) % Cn] * f
        yy = y - (yc[j0] * (1 - f) + yc[(j0 + 1) % Cn] * f)
        r = cf[0] + cf[1] * yy + lf + up
        return wrap.pt(y, th, r), wrap.dirs(th)

    # edge stitching beads (thin, dark leather): skip; studs in gold along the centre line
    st = bl["studs"]
    for th in np.arange(-180.0, 180.0, st["step"]):
        if min(abs(th - s) for s in st["skip"]) < st["skip_w"] or abs(th) < st["skip_front"]:
            continue
        for dy in st["rows"]:
            p, n = belt_pt(belt_line(th, bl) + dy, th, bt)
            trim.append(rivet(p[0], n[0], r=st["r"], h=st["h"], name=f"stud{len(trim)}", material=M["trim"]))
    # buckle (rigid) at the front
    bk = bl["buckle"]
    p, n = belt_pt(belt_line(0.0, bl), 0.0, bt + 0.0008)
    up = U(belt_pt(belt_line(0.0, bl) + 0.01, 0.0, bt)[0][0] - belt_pt(belt_line(0.0, bl) - 0.01, 0.0, bt)[0][0])
    rigid.append(buckle(p[0], n[0], np.cross(up, n[0]) if False else up, w=bk["w"], h=bk["h"], bar=bk["bar"],
                        name="buckle_rigid", material=M["trim"]))
    # keeper tabs with rings
    rg = bl["rings"]
    for h in (1, -1):
        th = h * rg["th"]
        y1 = belt_line(th, bl) + hw - 0.004
        y0 = belt_line(th, bl) - hw - rg["drop"]
        ys = np.linspace(y0, y1, 8)
        tw = rg["tab_w"] / 2
        AA = th + np.degrees(np.array([-tw, -tw / 3, tw / 3, tw]) / 0.13)
        YY, AG = np.meshgrid(ys, AA, indexing="ij")
        PP, NN = belt_pt(YY.ravel(), AG.ravel(), bt + 0.0006)
        straps.append(kb.slab(f"tab_{h}", M["strap"], PP.reshape(YY.shape + (3,)), NN.reshape(YY.shape + (3,)), 0.0025))
        pc, nc = belt_pt(y0 - rg["R"] + 0.004, th, bt + rg.get("out", 0.004))
        rigid.append(torus(pc[0], nc[0], [0, 1.0, 0], rg["R"], rg["r"], f"ring_{'l' if h > 0 else 'r'}_rigid", M["trim"]))
        pr, nr = belt_pt(y0 + 0.006, th, bt + 0.003)
        rigid.append(rivet(pr[0], nr[0], r=0.003, h=0.002, name=f"tabrivet_{'l' if h > 0 else 'r'}_rigid",
                           material=M["trim"]))

    # ---- hanging plates
    rim = cfg["rim"]
    pt_th = cfg["plate_thick"]
    edge_off = pt_th * 0.5 + 0.0003
    from scipy.interpolate import interp1d
    for pl in cfg["plates"]:
        for h in ((1, -1) if pl.get("mirror", True) else (1,)):
            nm = pl["name"] + ("" if not pl.get("mirror", True) else ("_l" if h > 0 else "_r"))
            a0, a1 = pl["th"]
            ths = np.linspace(a0, a1, pl["cols"]) * h
            if not pl.get("mirror", True):
                ths = np.linspace(-a1, a1, pl["cols"])
            y_top = belt_line(ths, bl) - hw + pl["tuck"]
            rho_t = np.array([np.linalg.norm((belt_pt(yy, t, 0.0010)[0][0] - [0, yy, z0])[[0, 2]]) for yy, t in zip(y_top, ths)])
            u = (np.abs(ths) - min(abs(a0), abs(a1))) / max(abs(a1 - a0), 1e-6) if pl.get("mirror", True) else np.abs(ths) / a1
            Lk = np.array(pl["len"])
            length = interp1d(np.linspace(0, 1, len(Lk)), Lk, kind="quadratic" if len(Lk) > 2 else "linear")(np.clip(u, 0, 1))
            nd = pl["need"]
            G, Nn, tilt = hang(ref, wrap, nm, ths, y_top, rho_t, length, pl["tilt"],
                               lambda f, nd=nd: nd[0] + (nd[1] - nd[0]) * f, rows=pl["rows"], a_max=pl.get("tilt_max"))
            ex = None
            if pl.get("keel"):
                k_ = pl["keel"]
                xs = np.linalg.norm(G - G[:, [len(ths) // 2]], axis=-1)
                ex = k_["h"] * np.clip(1 - xs / (k_["w"] / 2), 0, 1) ** 1.0
            # two hinged lames (the sheet's): the upper rides her pelvis (short, above the hip joint), the lower hangs
            # OUTSIDE its bottom edge by `lap` and rides her thigh (its own node: its own blend, the mean of her
            # weights over it), so it swings with the thigh and slides under nothing; a plate without "split" is one.
            R_ = G.shape[0]
            if pl.get("split"):
                k_ = int(round(pl["split"] * (R_ - 1)))
                sp = pl.get("lap_rows", 2)
                lames = [("_up", slice(0, k_ + 1), 0.0, False), ("_lo", slice(max(k_ - sp, 0), R_), pl.get("lap", 0.004), True)]
            else:
                lames = [("", slice(0, R_), 0.0, True)]
            for sfx, rs, push, band_on in lames:
                Gl, Nl = G[rs] + Nn[rs] * push, Nn[rs]
                exl = None if ex is None else ex[rs]
                plate_p = kb.slab(nm + sfx + "_rigid", M["plate"], Gl, Nl, pt_th, extra=exl)
                plate_p.name = nm + sfx + "_rigid"
                rigid.append(plate_p)
                # its rim (all but the top, which is under the belt or the lame above): one rigid gold part with the band
                E = np.vstack([Gl[:, 0], Gl[-1, 1:], Gl[::-1, -1][1:]])
                gold = [kb.bead(Normals(Gl.reshape(-1, 3), Nl.reshape(-1, 3)), nm + sfx + "_rim", M["trim"], E, rim, edge_off,
                                False, relax_it=1)]
                if pl.get("band") and band_on:
                    b_ = pl["band"]
                    Gs = Gl + Nl * (pt_th + (0 if exl is None else exl[..., None]))
                    gold += interlace(Gs, Nl, 1.2, len(ths) - 2.2, b_["v"][0], b_["v"][1], b_["wl"], nm + sfx + "_band",
                                      M["trim"], 0.0, [dict(rim, w=b_["border_w"], h=b_["border_h"], below=0.0003),
                                                       dict(rim, w=b_["w"], h=b_["h"], below=0.0003)])
                # (the SAME node name as its plate: the importer reads them as one source part (`<name>_rigid`, `.001`),
                # whose parts ride ONE common blend (piece_blender by_src), so the gold never drifts off its steel)
                rigid.append(Part.join(nm + sfx + "_rigid", M["trim"], gold))
            print(nm, "tilt", np.round(tilt.min(), 1), np.round(tilt.max(), 1), "len", np.round(length.max(), 3))
    return plate, trim, straps, rigid


RECIPES = {"brief": brief, "belt": belt}
