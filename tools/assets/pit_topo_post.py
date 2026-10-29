"""Her armpits' topology rebuilt on her REST mesh (Body 9 round 7, 25 October 2026).

Round 6 found that the dark notch where her raised arm's underside meets her breast (rows 1, 3, 5 of the arm sheet) is
no fold: its tip is her armpit's deepest point, ONE welded vertex (each side; the graft's old hole cap): 42 triangles
meet there, spokes 2-35 mm, 12 (right) and 19 (left) UV charts of her graft meeting at it, its fan turning through 447
degrees and folded over even at rest (6 folded faces within 21 mm on the right, 34 within 23 mm on the left). Its
neighbours carry valences 9-12. No sculpt or normal can light such a fan cleanly. This pass replaces that patch, both
sides, before the sculpt (it runs on Body 8's reweight, ahead of shoulder_sculpt_post):

  patch   per side the faces within R (geodesic, 36 mm) of the pole (the highest-valence point at her pit; skipped if
          it has no more than 12: already rebuilt), grown over every folded or sliver face within R + GROW (35 mm;
          round 7's 15 left 4 (right) and 6 (left) folded faces at rest within 80 mm, behind the pit at the patch's
          border and past it, 0 now; Body 9 round 8) and into
          a disk with a smooth border (no notches, no ears; one border loop). The border's points and every face and
          point outside are kept as they were, byte for byte
  remesh  isotropic (Botsch and Kobbelt): split edges > 4/3 L, collapse < 4/5 L (never a border point), flip toward
          valence 6 (her full valence at the border), tangential relaxation; each point put back on her old surface;
          L = the median of the border's edges (her mesh's own ~4.6 mm there, so no density step at the border)
  fair    the new points onto one smooth surface: least squares of the patch's Laplacian energy (thin plate; the rows
          at the border points take her outside points in, so the surface runs on with her own slope) and the
          distance to her old surface; the old surface has no say on the pole's fan and the folded or sliver faces
          (their flat spokes cut up to several mm under the real pit), so the pit's dome there is the thin plate's
          fill from her real skin round it; then a few relaxations on the faired surface (even spacing)
  carry   each new point's weights (all eight: her bones and the shoulder helpers), vertex colour (the outfits' tuck
          channels) and every shape key's position and normal offsets from her old surface (barycentric at its closest
          point there), the weights eased over the patch (TOPO_WSMOOTH passes, the border held) and capped to eight
          (shoulder_rig_post.merge_cap); normals area-weighted, as her stored ones are (the border keeps its own)
  paint   the patch goes on her body's material (Material_0.001; the fan was her graft's: no freckles, grain or relief
          there, measured) in a new UV island each side (LSCM), placed in free texels of her body paint and its paint
          baked from her old surface (texel -> its point on the new patch -> the closest point on her old surface ->
          that face's own UV and material's image, bilinear, 3 x 3 samples a texel, padded PAD texels). The islands'
          UV area is set so her mesh's pore scale (People.PoreScale: sqrt(area / UV area) of her whole body mesh) is
          exactly what it was: her pores keep their places everywhere outside the patch (the Look and idles)

    PIT_TOPO=1 python tools/assets/pit_topo_post.py <src.glb> <dst.glb> [--sides l,r]
Run after shoulder_reweight_post.py and before shoulder_sculpt_post.py (the sculpt then re-solves its join on the even
mesh), then heroine_arm_tone.py last. Without PIT_TOPO=1 it copies unchanged. Done-mark `pit_topo` in the asset's
extras (a second run refuses). Her vertex order changes inside each primitive (the patch's old points go, new ones
come at the end): anything keyed on her vertex ids must be re-made on this body (the outfits' tuck channels and
armor_tuck records for the patch's points, her LOD); records keyed by bind position stay valid outside the patch.
"""
import io
import json
import os
import shutil
import struct
import sys
from collections import defaultdict

import numpy as np
import scipy.sparse as sps
from scipy.sparse.csgraph import dijkstra
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
sys.path.insert(0, os.path.join(HERE, "arm_graft"))
from heroine_neck import _Gl, _CT, _NC  # noqa: E402
from geo import closest_tri  # noqa: E402

_E = os.environ.get
P = dict(R=float(_E("TOPO_R", 0.036)), grow=float(_E("TOPO_GROW", 0.035)), L=float(_E("TOPO_L", 0.0)),
         it=int(_E("TOPO_IT", 14)), relax=int(_E("TOPO_RELAX", 4)), pole=int(_E("TOPO_POLE", 12)),
         mu=float(_E("TOPO_MU", 30.0)), fairIt=int(_E("TOPO_FAIR_IT", 4)), post=int(_E("TOPO_POST", 6)),
         wsm=int(_E("TOPO_WSMOOTH", 4)), pad=int(_E("TOPO_PAD", 8)), sliver=float(_E("TOPO_SLIVER", 12.0)))


def acc(G, ai):
    """an accessor's data as stored (sparse accessors filled in; zeros under them without a bufferView)"""
    a = G.g["accessors"][ai]
    n, dt = _NC[a["type"]], np.dtype(_CT[a["componentType"]])
    x = G.get(ai) if "bufferView" in a else np.zeros((a["count"], n), dt)
    sp = a.get("sparse")
    if sp:
        def raw(d, dtype, cnt):
            bv = G.g["bufferViews"][d["bufferView"]]
            off = G.b0 + bv.get("byteOffset", 0) + d.get("byteOffset", 0)
            return np.frombuffer(bytes(G.buf[off:off + dtype.itemsize * cnt]), dtype)
        idx = raw(sp["indices"], np.dtype(_CT[sp["indices"]["componentType"]]), sp["count"]).astype(np.int64)
        val = raw(sp["values"], dt, sp["count"] * n).reshape(-1, n)
        x = x.copy()
        x[idx] = val
    return x


def fnormals(X, F):
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    a = np.linalg.norm(q, axis=1)
    return q / np.maximum(a, 1e-20)[:, None], a / 2


def vnormals(X, F, n=None):
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    out = np.zeros((len(X) if n is None else n, 3))
    for k in range(3):
        np.add.at(out, F[:, k], q)
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-20)


def edges(F):
    return np.unique(np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], axis=1), axis=0)


def min_angles(X, F):
    out = np.full(len(F), 180.0)
    for i in range(3):
        a, b, c = X[F[:, i]], X[F[:, (i + 1) % 3]], X[F[:, (i + 2) % 3]]
        u, v = b - a, c - a
        cs = (u * v).sum(1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-20)
        out = np.minimum(out, np.degrees(np.arccos(np.clip(cs, -1, 1))))
    return out


def folded(X, F, thr=0.0):
    """faces whose normal turns past 90 degrees (dot < thr) from a neighbour across an edge"""
    N, _ = fnormals(X, F)
    H = np.c_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]].reshape(-1, 2)
    fid = np.repeat(np.arange(len(F)), 3)
    k = np.sort(H, 1)
    k = k[:, 0].astype(np.int64) * (F.max() + 1) + k[:, 1]
    o = np.argsort(k, kind="stable")
    ks = k[o]
    s = np.nonzero(ks[1:] == ks[:-1])[0]
    f1, f2 = fid[o[s]], fid[o[s + 1]]
    bad = (N[f1] * N[f2]).sum(1) < thr
    m = np.zeros(len(F), bool)
    m[f1[bad]] = m[f2[bad]] = True
    return m


class Surf:
    """closest points on a triangle set; candidates by centroid (k nearest) and by vertex (their faces), so a long
    fan spoke's triangle is found even far from its centroid"""

    def __init__(s, V, T, k=48):
        s.V, s.T, s.k = V, T, k
        s.cen = V[T].mean(1)
        s.kd = cKDTree(s.cen)
        s.N, _ = fnormals(V, T)
        used = np.unique(T)
        s.kv = cKDTree(V[used])
        s.used = used
        vf = defaultdict(list)
        for i, t in enumerate(T):
            for v in t:
                vf[v].append(i)
        s.vf = vf

    def query(s, p, n=None):
        """(closest points, distances, face ids, barycentrics); with n (normals), faces facing away (dot < 0) are
        passed over unless nothing else is near"""
        p = np.atleast_2d(p)
        _, J = s.kd.query(p, min(s.k, len(s.T)))
        J = J.reshape(len(p), -1)
        _, Kv = s.kv.query(p, 6)
        extra = [sorted({f for v in s.used[row] for f in s.vf[v]}) for row in Kv.reshape(len(p), -1)]
        m = max(len(e) for e in extra)
        Je = np.array([e + [e[0]] * (m - len(e)) for e in extra])
        J = np.hstack([J, Je])
        best = np.full(len(p), np.inf)
        bq, bf, bb = np.zeros((len(p), 3)), np.zeros(len(p), int), np.zeros((len(p), 3))
        for j in range(J.shape[1]):
            f = J[:, j]
            T = s.T[f]
            q, bar = closest_tri(p, s.V[T[:, 0]], s.V[T[:, 1]], s.V[T[:, 2]])
            dd = ((q - p) ** 2).sum(1)
            if n is not None:
                dd = dd + np.where((s.N[f] * n).sum(1) < 0, 1.0, 0.0)
            m_ = dd < best
            best[m_], bq[m_], bf[m_], bb[m_] = dd[m_], q[m_], f[m_], bar[m_]
        d = np.linalg.norm(bq - p, axis=1)
        return bq, d, bf, bb


# ---------------------------------------------------------------------------------------------------- her model

class Her:
    """her body mesh (both primitives) as stored, and welded by place as skin_union welds it"""

    def __init__(s, G):
        g = s.g = G.g
        s.G = G
        s.node = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
        s.mesh = g["meshes"][s.node["mesh"]]
        s.prims = s.mesh["primitives"]
        assert all(g["materials"][p["material"]].get("name") != "skin_head" for p in s.prims)
        s.mat = [g["materials"][p["material"]]["name"] for p in s.prims]
        s.body = s.mat.index("Material_0.001")
        s.A = []
        for p in s.prims:
            d = {k: acc(G, v) for k, v in p["attributes"].items()}
            d["F"] = acc(G, p["indices"]).reshape(-1, 3).astype(np.int64)
            d["T"] = [{k: acc(G, v) for k, v in t.items()} for t in p.get("targets", [])]
            s.A.append(d)
        s.cnt = [len(d["POSITION"]) for d in s.A]
        s.off = np.r_[0, np.cumsum(s.cnt)]
        Pp = np.vstack([d["POSITION"] for d in s.A]).astype(np.float64)
        _, first, wid = np.unique(np.round(Pp / 1e-6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
        s.wid, s.first = wid.ravel(), first
        s.U = Pp[first]
        Fo = np.vstack([d["F"] + s.off[i] for i, d in enumerate(s.A)])
        fp = np.concatenate([np.full(len(d["F"]), i) for i, d in enumerate(s.A)])
        Fw = s.wid[Fo]
        ok = (Fw[:, 0] != Fw[:, 1]) & (Fw[:, 1] != Fw[:, 2]) & (Fw[:, 2] != Fw[:, 0])
        assert ok.all(), "her body has welded-degenerate faces"
        s.Fo, s.fprim, s.F = Fo, fp, Fw
        s.UV = np.vstack([d["TEXCOORD_0"] for d in s.A]).astype(np.float64)
        s.N = np.vstack([d["NORMAL"] for d in s.A]).astype(np.float64)
        # per welded point (its first copy): dense weights, colour, the shape keys' offsets
        sk = g["skins"][0]
        s.names = [g["nodes"][j].get("name") for j in sk["joints"]]
        J = np.vstack([np.hstack([d["JOINTS_0"], d["JOINTS_1"]]) for d in s.A]).astype(np.int64)
        W = np.vstack([np.hstack([d["WEIGHTS_0"], d["WEIGHTS_1"]]) for d in s.A]).astype(np.float64)
        s.Wd = np.zeros((len(s.U), len(s.names)))
        np.add.at(s.Wd, (np.repeat(np.arange(len(s.U)), 8), J[first].ravel()), W[first].ravel())
        s.C = np.vstack([d["COLOR_0"] for d in s.A]).astype(np.float64)[first] / 65535.0
        s.nt = len(s.A[0]["T"])
        assert all(len(d["T"]) == s.nt for d in s.A)
        s.TP = [np.vstack([d["T"][t]["POSITION"] for d in s.A]).astype(np.float64)[first] for t in range(s.nt)]
        s.TN = [np.vstack([d["T"][t]["NORMAL"] for d in s.A]).astype(np.float64)[first] for t in range(s.nt)]
        E = edges(s.F)
        el = np.linalg.norm(s.U[E[:, 0]] - s.U[E[:, 1]], axis=1)
        n = len(s.U)
        s.GR = sps.coo_matrix((np.r_[el, el], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
        s.deg = np.diff(s.GR.indptr)


def pole_of(her, side):
    """her pit's pole: the highest-valence point in the pit's box on that side"""
    U = her.U
    sg = 1 if side == "l" else -1
    m = ((U[:, 0] * sg > 0.11) & (U[:, 0] * sg < 0.20) & (U[:, 1] > 1.36) & (U[:, 1] < 1.50)
         & (np.abs(U[:, 2] + 0.01) < 0.06))
    idx = np.nonzero(m)[0]
    v = int(idx[np.argmax(her.deg[idx])])
    return v, int(her.deg[v])


def patch_of(her, pole, p=P):
    """the patch's faces (a disk round the pole): geodesic R, grown over the folded and sliver faces near, notches
    filled, ears cut, one border loop"""
    U, F = her.U, her.F
    d = dijkstra(her.GR, indices=pole, limit=p["R"] + p["grow"] + 0.03)
    fd = d[F].max(1)
    m = fd < p["R"]
    bad = (folded(U, F) | (min_angles(U, F) < p["sliver"])) & (fd < p["R"] + p["grow"])
    m |= bad
    VF = sps.coo_matrix((np.ones(F.size), (np.repeat(np.arange(len(F)), 3), F.ravel())), shape=(len(F), len(U))).tocsr()
    FF = (VF @ VF.T).tocsr()      # faces sharing a point
    for _ in range(2):                                             # a ring round the bad faces
        m |= (FF @ bad.astype(float) > 0) & (fd < p["R"] + p["grow"] + 0.01)
        bad = m & bad
    # edge adjacency of faces
    H = np.c_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]].reshape(-1, 2)
    k = np.sort(H, 1)
    k = k[:, 0].astype(np.int64) * len(U) + k[:, 1]
    o = np.argsort(k, kind="stable")
    ks = k[o]
    s = np.nonzero(ks[1:] == ks[:-1])[0]
    fid = np.repeat(np.arange(len(F)), 3)
    f1, f2 = fid[o[s]], fid[o[s + 1]]
    for _ in range(50):
        nb = np.zeros(len(F), int)
        np.add.at(nb, f1, m[f2].astype(int))
        np.add.at(nb, f2, m[f1].astype(int))
        add = ~m & (nb >= 2)                                       # notches
        vin = np.zeros(len(U), bool)
        vin[F[m].ravel()] = True
        add |= ~m & vin[F].all(1)                                   # faces whose three points are in already
        if not add.any():
            break
        m |= add
    # one piece (the pole's) and no holes: enclosed outside pieces taken in
    from scipy.sparse.csgraph import connected_components
    both = m[f1] & m[f2]
    Gm = sps.coo_matrix((np.ones(both.sum()), (f1[both], f2[both])), shape=(len(F), len(F)))
    _, lab = connected_components(Gm, directed=False)
    pl = lab[np.nonzero((F == pole).any(1))[0][0]]
    m &= lab == pl
    out = ~m
    bo = out[f1] & out[f2]
    Go = sps.coo_matrix((np.ones(bo.sum()), (f1[bo], f2[bo])), shape=(len(F), len(F)))
    _, lo_ = connected_components(Go, directed=False)
    far = np.unique(lo_[out & (fd > p["R"] + p["grow"] + 0.02)])
    m |= out & ~np.isin(lo_, far)
    # one border loop, a disk
    Fm = F[m]
    Hm = np.c_[Fm[:, [0, 1]], Fm[:, [1, 2]], Fm[:, [2, 0]]].reshape(-1, 2)
    km = Hm[:, 0].astype(np.int64) * len(U) + Hm[:, 1]
    kr = Hm[:, 1].astype(np.int64) * len(U) + Hm[:, 0]
    bnd = Hm[~np.isin(km, kr)]
    nxt = {}
    for a, b in bnd:
        assert a not in nxt, "the patch's border pinches at a point"
        nxt[a] = b
    loop = [bnd[0, 0]]
    while True:
        b = nxt[loop[-1]]
        if b == loop[0]:
            break
        loop.append(b)
    assert len(loop) == len(bnd), "the patch has %d border edges but its loop %d (holes?)" % (len(bnd), len(loop))
    V = np.unique(Fm)
    E = edges(Fm)
    chi = len(V) - len(E) + len(Fm)
    assert chi == 1, "the patch is no disk (Euler %d)" % chi
    return np.nonzero(m)[0], np.array(loop)


# ---------------------------------------------------------------------------------------------------- remesh

class Remesh:
    """isotropic remeshing of a disk patch, its border points locked (local ids: 0..nb-1 the border loop)"""

    def __init__(s, X, T, nborder, vout, ref, L, outadj=()):
        s.X = [np.asarray(x, float) for x in X]
        s.outadj = {(min(a, b), max(a, b)) for a, b in outadj}   # border pairs joined by an edge outside the patch
        s.T = {}
        s.vf = defaultdict(set)
        s.nid = 0
        for t in T:
            s._add(tuple(int(v) for v in t))
        s.nb = nborder
        s.vout = vout            # border point -> its outside neighbours (not in the patch)
        s.ref = ref
        s.L, s.hi, s.lo = L, 4.0 / 3.0 * L, 0.8 * L
        s.alive = [True] * len(s.X)

    def _add(s, t):
        s.T[s.nid] = t
        for v in t:
            s.vf[v].add(s.nid)
        s.nid += 1

    def _del(s, f):
        for v in s.T[f]:
            s.vf[v].discard(f)
        del s.T[f]

    def nbrs(s, v):
        out = set()
        for f in s.vf[v]:
            out.update(s.T[f])
        out.discard(v)
        return out

    def val(s, v):
        return len(s.nbrs(v)) + (s.vout.get(v, 0) if v < s.nb else 0)

    def efaces(s, a, b):
        return [f for f in s.vf[a] if b in s.T[f]]

    def border_edge(s, a, b):
        return len(s.efaces(a, b)) < 2

    def edge_list(s):
        E = set()
        for t in s.T.values():
            for i in range(3):
                a, b = t[i], t[(i + 1) % 3]
                E.add((min(a, b), max(a, b)))
        return sorted(E)

    def fn(s, t, X=None):
        X = s.X if X is None else X
        a, b, c = X[t[0]], X[t[1]], X[t[2]]
        q = np.cross(b - a, c - a)
        n = np.linalg.norm(q)
        return q / max(n, 1e-20), n / 2

    def vn(s, v):
        n = np.zeros(3)
        for f in s.vf[v]:
            q, a = s.fn(s.T[f])
            n += q * a
        return n / max(np.linalg.norm(n), 1e-20)

    # -- operations
    def split(s, a, b):
        fs = s.efaces(a, b)
        if len(fs) != 2:
            return False
        m = len(s.X)
        s.X.append((s.X[a] + s.X[b]) / 2)
        s.alive.append(True)
        for f in fs:
            t = s.T[f]
            i = t.index(a)
            if t[(i + 1) % 3] == b:           # (a, b, c)
                c = t[(i + 2) % 3]
                s._del(f)
                s._add((a, m, c))
                s._add((m, b, c))
            else:                              # (b, a, d)
                c = t[(i + 1) % 3] if t[(i + 1) % 3] != b else t[(i + 2) % 3]
                j = t.index(b)
                d = t[(j + 2) % 3]
                s._del(f)
                s._add((b, m, d))
                s._add((m, a, d))
        return True

    def collapse(s, a, b):
        """b into a (b must be free); False if not allowed"""
        if b < s.nb:
            return False
        fs = s.efaces(a, b)
        if len(fs) != 2:
            return False
        opp = [[v for v in s.T[f] if v not in (a, b)][0] for f in fs]
        if s.nbrs(a) & s.nbrs(b) != set(opp):
            return False
        if a < s.nb and any((min(a, v), max(a, v)) in s.outadj for v in s.nbrs(b) if v < s.nb):
            return False
        for c in opp:
            if s.val(c) <= 4:
                return False
        if s.val(a) + s.val(b) - 4 > 9:
            return False
        newp = s.X[a] if a < s.nb else (s.X[a] + s.X[b]) / 2
        for v in s.nbrs(b) | (s.nbrs(a) if a >= s.nb else set()):
            if v in (a, b):
                continue
            if np.linalg.norm(s.X[v] - newp) > s.hi:
                return False
        X2 = list(s.X)
        X2[a] = newp
        X2[b] = newp
        moved = (s.vf[b] | (s.vf[a] if a >= s.nb else set())) - set(fs)
        for f in moved:
            t = s.T[f]
            t2 = tuple(a if v == b else v for v in t)
            n0, a0 = s.fn(t)
            n1, a1 = s.fn(t2, X2)
            if a1 < 0.05 * a0 or (n0 @ n1) < 0.5:
                return False
        for f in list(s.vf[b]):
            t = s.T[f]
            s._del(f)
            if a in t:
                continue
            s._add(tuple(a if v == b else v for v in t))
        s.X[a] = newp
        s.alive[b] = False
        return True

    def flip(s, a, b):
        fs = s.efaces(a, b)
        if len(fs) != 2:
            return False
        t1, t2 = s.T[fs[0]], s.T[fs[1]]
        i = t1.index(a)
        if t1[(i + 1) % 3] != b:
            t1, t2 = t2, t1
            fs = fs[::-1]
            i = t1.index(a)
        c = t1[(i + 2) % 3]
        j = t2.index(b)
        d = t2[(j + 2) % 3]
        if d in s.nbrs(c) or (min(c, d), max(c, d)) in s.outadj:
            return False
        n1 = (c, a, d)
        n2 = (d, b, c)
        q0 = s.fn(t1)[0] + s.fn(t2)[0]
        q0 /= max(np.linalg.norm(q0), 1e-20)
        for t in (n1, n2):
            q, ar = s.fn(t)
            if (q @ q0) < 0.5 or ar < 1e-10:
                return False
        if min_angles(np.array([s.X[v] for v in (c, a, d, b)]), np.array([[0, 1, 2], [2, 3, 0]])).min() < 12:
            return False
        s._del(fs[0])
        s._del(fs[1])
        s._add(n1)
        s._add(n2)
        return True

    # -- passes
    def split_long(s):
        n = 0
        for _ in range(6):
            k = 0
            for a, b in s.edge_list():
                if np.linalg.norm(s.X[a] - s.X[b]) > s.hi and not (a < s.nb and b < s.nb and s.border_edge(a, b)):
                    if s.split(a, b):
                        k += 1
            n += k
            if not k:
                break
        return n

    def collapse_short(s):
        n = 0
        E = s.edge_list()
        E.sort(key=lambda e: np.linalg.norm(s.X[e[0]] - s.X[e[1]]))
        for a, b in E:
            if not (s.alive[a] and s.alive[b]) or not s.efaces(a, b):
                continue
            if np.linalg.norm(s.X[a] - s.X[b]) >= s.lo:
                continue
            if a < s.nb and b < s.nb:
                continue
            if b < s.nb:
                a, b = b, a
            if s.collapse(a, b):
                n += 1
        return n

    def flip_valence(s):
        n = 0
        for _ in range(4):
            k = 0
            for a, b in s.edge_list():
                fs = s.efaces(a, b)
                if len(fs) != 2:
                    continue
                c = [v for v in s.T[fs[0]] if v not in (a, b)][0]
                d = [v for v in s.T[fs[1]] if v not in (a, b)][0]
                va, vb, vc, vd = s.val(a), s.val(b), s.val(c), s.val(d)
                before = (va - 6) ** 2 + (vb - 6) ** 2 + (vc - 6) ** 2 + (vd - 6) ** 2
                after = (va - 7) ** 2 + (vb - 7) ** 2 + (vc - 5) ** 2 + (vd - 5) ** 2
                if after < before and s.flip(a, b):
                    k += 1
            n += k
            if not k:
                break
        return n

    def relax(s, ref=None, its=1, damp=0.5):
        ref = ref or s.ref
        free = [v for v in range(s.nb, len(s.X)) if s.alive[v] and s.vf[v]]
        for _ in range(its):
            new = []
            for v in free:
                nb = list(s.nbrs(v))
                q = np.mean([s.X[u] for u in nb], 0)
                n = s.vn(v)
                dlt = q - s.X[v]
                dlt -= n * (n @ dlt)
                new.append(s.X[v] + damp * dlt)
            new = np.array(new)
            nn = np.array([s.vn(v) for v in free])
            pq, _, _, _ = ref.query(new, nn)
            for v, x in zip(free, pq):
                s.X[v] = x

    def run(s, its, relax=4):
        for i in range(its):
            a = s.split_long()
            b = s.collapse_short()
            c = s.flip_valence()
            s.relax(its=relax)
        return s

    def arrays(s):
        """(positions, faces) compacted: border points keep their local ids 0..nb-1"""
        used = sorted({v for t in s.T.values() for v in t})
        assert all(v in used for v in range(s.nb)), "a border point lost its faces"
        mp = {v: i for i, v in enumerate(used)}
        X = np.array([s.X[v] for v in used])
        T = np.array([[mp[v] for v in t] for t in s.T.values()])
        return X, T


# ---------------------------------------------------------------------------------------------------- fair

def ulap(n, T, extra=None):
    """uniform Laplacian rows (sparse, n x n) from faces T (and extra edges: outside neighbours)"""
    E = edges(T)
    if extra is not None and len(extra):
        E = np.unique(np.vstack([E, np.sort(extra, 1)]), axis=0)
    A = sps.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
    A.data[:] = 1
    dg = np.asarray(A.sum(1)).ravel()
    return (sps.diags(1.0 / np.maximum(dg, 1)) @ A - sps.identity(n)).tocsr()


def fair(Xall, T, nfixed, rows, ext_edges, ref, wdata, mu, its):
    """free points (ids >= nfixed) by least squares: |L x|^2 over `rows` + mu sum w |x - p|^2, p the closest point on
    ref (re-found each pass)"""
    n = len(Xall)
    L = ulap(n, T, ext_edges)
    free = np.arange(nfixed, n)
    fix = np.arange(nfixed)
    Lr = L[rows]
    Lf, Lc = Lr[:, free], Lr[:, fix]
    X = Xall.copy()
    W = sps.diags(mu * wdata)
    M = (Lf.T @ Lf + W).tocsc()
    for _ in range(its):
        Nn = vnormals(X, T, n)[free]
        pq, _, _, _ = ref.query(X[free], Nn)
        rhs = -(Lf.T @ (Lc @ X[fix])) + W @ pq
        X[free] = spsolve(M, rhs)
    return X


# ---------------------------------------------------------------------------------------------------- uv

def lscm(X, T):
    """least squares conformal map of a disk (UV, n x 2), two far border points pinned"""
    n = len(X)
    Nf, A = fnormals(X, T)
    rows, cols, vals = [], [], []
    r = 0
    for t, (i, j, k) in enumerate(T):
        e1 = X[j] - X[i]
        ex = e1 / np.linalg.norm(e1)
        ey = np.cross(Nf[t], ex)
        z = [0j, complex(e1 @ ex, e1 @ ey), complex((X[k] - X[i]) @ ex, (X[k] - X[i]) @ ey)]
        a, b = z[2] - z[0], z[1] - z[0]
        w = 1.0 / np.sqrt(max(A[t], 1e-20))
        for v, c in ((i, (b - a) * w), (j, a * w), (k, -b * w)):
            rows += [r, r, r + 1, r + 1]
            cols += [v, n + v, v, n + v]
            vals += [c.real, -c.imag, c.imag, c.real]
        r += 2
    M = sps.coo_matrix((vals, (rows, cols)), shape=(r, 2 * n)).tocsr()
    # pins: the two border points farthest apart
    E = edges(T)
    cnt = defaultdict(int)
    for t in T:
        for q in range(3):
            a_, b_ = t[q], t[(q + 1) % 3]
            cnt[(min(a_, b_), max(a_, b_))] += 1
    bv = sorted({v for e, c in cnt.items() if c == 1 for v in e})
    B = X[bv]
    dd = np.linalg.norm(B[:, None] - B[None], axis=2)
    p0, p1 = np.unravel_index(dd.argmax(), dd.shape)
    p0, p1 = bv[p0], bv[p1]
    L01 = np.linalg.norm(X[p1] - X[p0])
    pin = {p0: (0.0, 0.0), p1: (L01, 0.0)}
    fixc = [p0, n + p0, p1, n + p1]
    fixv = np.array([0.0, 0.0, L01, 0.0])
    freec = np.setdiff1d(np.arange(2 * n), fixc)
    Mf, Mc = M[:, freec], M[:, fixc]
    sol = spsolve((Mf.T @ Mf).tocsc(), -(Mf.T @ (Mc @ fixv)))
    x = np.zeros(2 * n)
    x[freec] = sol
    x[fixc] = fixv
    return np.stack([x[:n], x[n:]], 1)


def uv_area(UV, T):
    a = UV[T[:, 1]] - UV[T[:, 0]]
    b = UV[T[:, 2]] - UV[T[:, 0]]
    return np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) / 2


def raster_tris(UVpx, T, W, H):
    """texels whose centres lie in each triangle (texel px coords): (ys, xs, face, barycentrics)"""
    out_y, out_x, out_f, out_b = [], [], [], []
    for t, (i, j, k) in enumerate(T):
        a, b, c = UVpx[i], UVpx[j], UVpx[k]
        lo = np.floor(np.minimum(np.minimum(a, b), c) - 0.5).astype(int)
        hi = np.ceil(np.maximum(np.maximum(a, b), c) + 0.5).astype(int)
        xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], W - 1) + 1), np.arange(max(lo[1], 0), min(hi[1], H - 1) + 1))
        q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        v0, v1, v2 = b - a, c - a, q - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        l1 = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        l2 = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        l0 = 1 - l1 - l2
        m = (l0 >= -1e-9) & (l1 >= -1e-9) & (l2 >= -1e-9)
        out_y.append(ys.ravel()[m])
        out_x.append(xs.ravel()[m])
        out_f.append(np.full(m.sum(), t))
        out_b.append(np.stack([l0[m], l1[m], l2[m]], 1))
    return np.concatenate(out_y), np.concatenate(out_x), np.concatenate(out_f), np.vstack(out_b)


def bilinear(img, uv):
    """img (H, W, C) float sampled at glTF uv (origin top-left), clamped"""
    H, W = img.shape[:2]
    x = np.clip(uv[:, 0] * W - 0.5, 0, W - 1)
    y = np.clip(uv[:, 1] * H - 0.5, 0, H - 1)
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, W - 1), np.minimum(y0 + 1, H - 1)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy) + img[y1, x0] * (1 - fx) * fy
            + img[y1, x1] * fx * fy)


# ---------------------------------------------------------------------------------------------------- one side

def rebuild_side(her, side, p=P, log=print):
    """(patch faces, border loop (welded ids), new interior points, new faces in [border ids | new ids >= n]) or None"""
    U, F, A = her.U, her.F, her.GR
    pole, val = pole_of(her, side)
    if val <= p["pole"]:
        log("PIT_TOPO %s: no pole (valence %d at most): left as it is" % (side, val))
        return None
    pf, loop = patch_of(her, pole, p)
    Fp = F[pf]
    Vp = np.unique(Fp)
    inner = np.setdiff1d(Vp, loop)
    loc = np.r_[loop, inner]
    g2l = {v: i for i, v in enumerate(loc)}
    T = np.vectorize(g2l.get)(Fp)
    border = set(loop.tolist())
    pnb = {v: set() for v in loop}
    for t in Fp:
        for a in t:
            if a in pnb:
                pnb[a].update(t)
    pe = set(map(tuple, edges(Fp)))
    vout, outadj = {}, []
    for i, v in enumerate(loop):
        full = set(A.indices[A.indptr[v]:A.indptr[v + 1]].tolist())
        pnb[v].discard(v)
        vout[i] = len(full - pnb[v])
        outadj += [(i, g2l[u]) for u in full if u in border and (min(u, v), max(u, v)) not in pe]
    ring = np.isin(F, Vp).any(1)
    for _ in range(2):
        ring = np.isin(F, np.unique(F[ring])).any(1)
    ref = Surf(U, F[ring])
    el = np.linalg.norm(U[loop] - U[np.roll(loop, -1)], axis=1)
    L = p["L"] or float(np.median(el))
    R = Remesh(U[loc], T, len(loop), vout, ref, L, outadj).run(p["it"], p["relax"])
    for _ in range(3):
        R.flip_valence()
    X, Tn = R.arrays()
    nb = len(loop)
    # fair: rows at the patch's points; the border's outside neighbours (and theirs) held
    n_out = sorted(set(A[loop].indices.tolist()) - set(Vp.tolist()))
    n_out2 = sorted(set(A[n_out].indices.tolist()) - set(Vp.tolist()) - set(n_out))
    ext = np.r_[loop, n_out, n_out2]                      # fixed: border, ring 1, ring 2
    Xall = np.vstack([U[ext], X[nb:]])
    nfix = len(ext)
    mp = np.r_[np.arange(nb), nfix + np.arange(len(X) - nb)]   # local (border | new) -> Xall
    Tall = mp[Tn]
    gi = {v: i for i, v in enumerate(ext)}
    outF = F[np.isin(F, ext).all(1) & ~np.isin(np.arange(len(F)), pf)]
    oute = edges(np.vectorize(gi.get)(outF)) if len(outF) else None
    # the old surface's say: none on the pole's fan and the folded / sliver faces (and a ring round them)
    badf = (F[ring] == pole).any(1) | folded(U, F[ring]) | (min_angles(U, F[ring]) < p["sliver"])
    badv = np.unique(F[ring][badf])
    nearbad = np.isin(F[ring], badv).any(1)
    ref2 = ref
    pq, _, ff, _ = ref2.query(Xall[nfix:], vnormals(Xall, Tall)[nfix:])
    w = np.where(nearbad[ff], 0.0, 1.0)
    rows = np.r_[np.arange(nb), np.arange(nfix, len(Xall))]
    X2 = fair(Xall, Tall, nfix, rows, oute, ref2, w, p["mu"], p["fairIt"])
    # even spacing on the faired surface, then fair again onto it
    Rf = Remesh(np.vstack([X2[:nb], X2[nfix:]]), Tn, nb, vout, Surf(np.vstack([X2[:nb], X2[nfix:]]), Tn), L, outadj)
    Rf.relax(its=p["post"])
    X3 = np.array(Rf.X)
    Xall2 = np.vstack([U[ext], X3[nb:]])
    X4 = fair(Xall2, Tall, nfix, rows, oute, Surf(np.vstack([X2[:nb], X2[nfix:]]), Tn), np.ones(len(X3) - nb), p["mu"], 2)
    Xn = X4[nfix:]
    # stats
    Xs = np.vstack([X[:nb], Xn])
    E = edges(Tn)
    el2 = np.linalg.norm(Xs[E[:, 0]] - Xs[E[:, 1]], axis=1)
    vals = np.array([Rf.val(v) for v in range(len(Rf.X))])
    dev = ref.query(Xn, vnormals(Xs, Tn)[nb:])[1]
    info = dict(pole=int(pole), pole_valence=int(val), old_faces=int(len(pf)), new_faces=int(len(Tn)), border=int(nb),
                L_mm=round(L * 1e3, 2), valence=np.bincount(vals).tolist(),
                edge_mm=[round(float(x), 2) for x in np.percentile(el2 * 1e3, [1, 50, 99])],
                min_angle_p1=round(float(np.percentile(min_angles(Xs, Tn), 1)), 1),
                folded=int(folded(Xs, Tn).sum()),
                dev_mm_data=[round(float(x), 2) for x in np.percentile(dev[w > 0] * 1e3, [50, 95, 100])] if (w > 0).any() else [],
                dev_mm_fan=[round(float(x), 2) for x in np.percentile(dev[w == 0] * 1e3, [50, 95, 100])] if (w == 0).any() else [])
    log("PIT_TOPO %s: %s" % (side, info))
    return dict(pf=pf, loop=loop, Xn=Xn, T=Tn, info=info, ref=ref)


# ---------------------------------------------------------------------------------------------------- the glb

def _img(G, mi):
    from PIL import Image
    t = G.g["materials"][mi]["pbrMetallicRoughness"]["baseColorTexture"]["index"]
    si = G.g["textures"][t]["source"]
    bv = G.g["bufferViews"][G.g["images"][si]["bufferView"]]
    off = G.b0 + bv.get("byteOffset", 0)
    im = Image.open(io.BytesIO(bytes(G.buf[off:off + bv["byteLength"]])))
    return si, im.mode, np.asarray(im.convert("RGBA")).astype(np.float64)


def _areas(her, keepf=None):
    """(3D area, UV area) of her mesh's faces (all, or the kept ones), as People.PoreScale sums them"""
    X = np.vstack([d["POSITION"] for d in her.A]).astype(np.float64)
    Fo = her.Fo if keepf is None else her.Fo[keepf]
    a = np.linalg.norm(np.cross(X[Fo[:, 1]] - X[Fo[:, 0]], X[Fo[:, 2]] - X[Fo[:, 0]]), axis=1) / 2
    return a.sum(), uv_area(her.UV, Fo).sum()


def place(occ, mask):
    """top-left (x, y) where the island's (dilated) mask meets no occupied texel, nearest the texture's centre"""
    import cv2
    H, W = occ.shape
    h, w = mask.shape
    best = None
    ii = cv2.integral(occ.astype(np.uint8))
    for y in range(8, H - h - 8, 8):
        for x in range(8, W - w - 8, 8):
            if ii[y + h, x + w] - ii[y, x + w] - ii[y + h, x] + ii[y, x] == 0:
                d = (x + w / 2 - W / 2) ** 2 + (y + h / 2 - H / 2) ** 2
                if best is None or d < best[0]:
                    best = (d, x, y)
    assert best, "no free texels for the island"
    return best[1], best[2]


def _bake(her, r, imgs, pxg, Ww, Hh):
    """(ys, xs, colours) of the island's texels: 3 x 3 samples a texel, each from her old surface's own UV and image"""
    F = her.F
    ring_f = np.nonzero(np.isin(F, np.unique(r["ref"].T)).all(1))[0]
    key = {tuple(sorted(t)): i for i, t in zip(ring_f, F[ring_f].tolist())}
    Nv = vnormals(r["Xs"], r["T"])
    acc_ = np.zeros((Hh, Ww, 4))
    cnt = np.zeros((Hh, Ww))
    for sy in (-1 / 3, 0, 1 / 3):
        for sx in (-1 / 3, 0, 1 / 3):
            ys, xs, fi, bar = raster_tris(pxg - [sx, sy], r["T"], Ww, Hh)
            X3 = np.einsum("nk,nkj->nj", bar, r["Xs"][r["T"][fi]])
            N3 = np.einsum("nk,nkj->nj", bar, Nv[r["T"][fi]])
            _, _, ff, bb = r["ref"].query(X3, N3)
            RT = r["ref"].T[ff]
            hf = np.array([key[tuple(sorted(t))] for t in RT.tolist()])
            Fw_ = F[hf]
            ordr = np.argmax(Fw_[:, None, :] == RT[:, :, None], axis=2)      # RT's k-th point is Fw_'s ordr[k]-th
            cuv = np.take_along_axis(her.UV[her.Fo[hf]], ordr[:, :, None], 1)
            suv = np.einsum("nk,nkj->nj", bb, cuv)
            col = np.zeros((len(suv), 4))
            for pi in np.unique(her.fprim[hf]):
                mm = her.fprim[hf] == pi
                col[mm] = bilinear(imgs[pi], suv[mm])
            np.add.at(acc_, (ys, xs), col)
            np.add.at(cnt, (ys, xs), 1)
    has = cnt > 0
    ys, xs = np.nonzero(has)
    return ys, xs, acc_[has] / cnt[has][:, None]


def run(src, dst, sides=("l", "r"), log=print):
    import cv2
    from PIL import Image
    from shoulder_rig_post import merge_cap, rest_globals
    import helpers as hp
    from wrap_post import compact
    G = _Gl(src)
    g = G.g
    assert "pit_topo" not in g["asset"].get("extras", {}), "PIT_TOPO: already on this body"
    her = Her(G)
    U, F = her.U, her.F
    A0, UV0 = _areas(her)
    k0 = np.sqrt(A0 / UV0) / 0.009
    res = {s: rebuild_side(her, s, log=log) for s in sides}
    res = {s: r for s, r in res.items() if r}
    if not res:
        shutil.copyfile(src, dst)
        return
    gone = np.zeros(len(F), bool)
    for r in res.values():
        gone[r["pf"]] = True
    names, _, Grest = rest_globals(G)
    frames = hp.shoulder_rest(Grest)
    for s, r in res.items():
        loop, Xn, T = r["loop"], r["Xn"], r["T"]
        nb = len(loop)
        Xs = np.vstack([U[loop], Xn])
        Ns = vnormals(Xs, T)
        _, _, ff, bb = r["ref"].query(Xn, Ns[nb:])
        ov = r["ref"].T[ff]
        Wall = np.vstack([her.Wd[loop], np.einsum("nk,nkj->nj", bb, her.Wd[ov])])
        Ad = sps.coo_matrix((np.ones(3 * len(T)), (T.ravel(), T[:, [1, 2, 0]].ravel())), shape=(len(Xs),) * 2)
        Ad = ((Ad + Ad.T) > 0).astype(float).tocsr()
        Ad = sps.diags(1 / np.maximum(np.asarray(Ad.sum(1)).ravel(), 1)) @ Ad
        for _ in range(P["wsm"]):
            Wall[nb:] = 0.5 * Wall[nb:] + 0.5 * (Ad @ Wall)[nb:]
        r["W"] = merge_cap(Wall[nb:], names, frames, cap=8)
        r["C"] = np.einsum("nk,nkj->nj", bb, her.C[ov])
        r["TP"] = [np.einsum("nk,nkj->nj", bb, tp[ov]) for tp in her.TP]
        r["TN"] = [np.einsum("nk,nkj->nj", bb, tn[ov]) for tn in her.TN]
        r["N"] = Ns[nb:]
        r["Xs"], r["area"] = Xs, fnormals(Xs, T)[1].sum()
    # UV islands: LSCM, scaled so her mesh's pore scale holds, placed in free texels of her body paint, baked
    keepf = ~gone
    Ak, UVk = _areas(her, keepf)
    Anew = Ak + sum(r["area"] for r in res.values())
    UVnew = Anew / A0 * UV0 - UVk
    dens = UVnew / sum(r["area"] for r in res.values())
    bsi, bmode, paint = _img(G, her.prims[her.body]["material"])
    Hh, Ww = paint.shape[:2]
    occ = np.zeros((Hh, Ww), np.uint8)
    for t in (her.UV[her.Fo[keepf & (her.fprim == her.body)]] * [Ww, Hh]).astype(np.int32):
        cv2.fillConvexPoly(occ, t, 1)
    occ = cv2.dilate(occ, np.ones((2 * P["pad"] + 1,) * 2, np.uint8))
    imgs = {pi: (paint.copy() if pi == her.body else _img(G, p_["material"])[2]) for pi, p_ in enumerate(her.prims)}
    isl = {}
    for s, r in res.items():
        uv = lscm(r["Xs"], r["T"])
        uv -= uv.mean(0)
        _, evec = np.linalg.eigh(np.cov(uv.T))
        uv = uv @ evec
        uv *= np.sqrt(dens * r["area"] / uv_area(uv, r["T"]).sum())
        px = (uv - uv.min(0)) * [Ww, Hh] + P["pad"] + 1
        h, w = int(np.ceil(px[:, 1].max())) + P["pad"] + 2, int(np.ceil(px[:, 0].max())) + P["pad"] + 2
        m = np.zeros((h, w), np.uint8)
        for t in px[r["T"]].astype(np.int32):
            cv2.fillConvexPoly(m, t, 1)
        m = cv2.dilate(m, np.ones((2 * P["pad"] + 1,) * 2, np.uint8))
        x0, y0 = place(occ, m)
        occ[y0:y0 + h, x0:x0 + w] |= m
        pxg = px + [x0, y0]
        r["uv"] = pxg / [Ww, Hh]
        ys, xs, col = _bake(her, r, imgs, pxg, Ww, Hh)
        isl_m = np.zeros((h, w), np.uint8)
        isl_m[ys - y0, xs - x0] = 1
        blk = paint[y0:y0 + h, x0:x0 + w]
        blk[ys - y0, xs - x0] = col
        dist, lab = cv2.distanceTransformWithLabels((1 - isl_m).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        yy, xx = np.nonzero(isl_m)
        src_of = np.zeros(lab.max() + 1, int)
        src_of[lab[yy, xx]] = np.arange(len(yy))
        padm = (isl_m == 0) & (dist <= P["pad"]) & (m > 0)
        py_, px_ = np.nonzero(padm)
        j = src_of[lab[padm]]
        blk[py_, px_] = blk[yy[j], xx[j]]
        isl[s] = [int(x0), int(y0), int(w), int(h)]
        log("PIT_TOPO %s: island %dx%d texels at (%d, %d), %.3f m a UV unit" % (s, w, h, x0, y0, 1 / np.sqrt(dens)))
    # ---- the primitives: kept faces (their points compacted), the new faces on her body's material
    nt = her.nt
    outp = []
    for pi, d in enumerate(her.A):
        kf = her.Fo[keepf & (her.fprim == pi)] - her.off[pi]
        used = np.unique(kf)
        remap = -np.ones(her.cnt[pi], np.int64)
        remap[used] = np.arange(len(used))
        at = {k: [v[used]] for k, v in d.items() if k not in ("F", "T")}
        tg = [{k: [v[used].astype(np.float64)] for k, v in t.items()} for t in d["T"]]
        faces = [remap[kf]]
        if pi == her.body:
            base = len(used)
            for s, r in res.items():
                loop = r["loop"]
                nb = len(loop)
                f0 = her.first[loop]
                pj = np.searchsorted(her.off, f0, side="right") - 1
                jj = f0 - her.off[pj]
                bt = {k: np.array([her.A[a][k][b] for a, b in zip(pj, jj)]) for k in at}
                bT = [{k: np.array([her.A[a]["T"][t][k][b] for a, b in zip(pj, jj)]).astype(np.float64) for k in ("POSITION", "NORMAL")} for t in range(nt)]
                top = np.argsort(-r["W"], 1, kind="stable")[:, :8]
                tw = np.clip(np.take_along_axis(r["W"], top, 1), 0, None)
                tw[tw < 1e-5] = 0
                tw /= tw.sum(1, keepdims=True)
                top[tw == 0] = 0
                new = {"POSITION": r["Xn"], "NORMAL": r["N"], "JOINTS_0": top[:, :4], "JOINTS_1": top[:, 4:],
                       "WEIGHTS_0": tw[:, :4], "WEIGHTS_1": tw[:, 4:], "COLOR_0": np.clip(np.round(r["C"] * 65535), 0, 65535)}
                for k in at:
                    if k == "TEXCOORD_0":
                        at[k].append(r["uv"].astype(d[k].dtype))
                    else:
                        at[k].append(np.vstack([bt[k], np.asarray(new[k]).astype(d[k].dtype)]))
                for t in range(nt):
                    tg[t]["POSITION"].append(np.vstack([bT[t]["POSITION"], r["TP"][t]]))
                    tg[t]["NORMAL"].append(np.vstack([bT[t]["NORMAL"], r["TN"][t]]))
                faces.append(base + r["T"])
                base += nb + len(r["Xn"])
        outp.append(({k: np.vstack(v) for k, v in at.items()}, [{k: np.vstack(v) for k, v in t.items()} for t in tg], np.vstack(faces)))
    # ---- write: new accessors, the paint, compacted
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])

    def view(data, target=None):
        while len(binb) % 4:
            binb.append(0)
        g["bufferViews"].append({"buffer": 0, "byteOffset": len(binb), "byteLength": len(data), **({"target": target} if target else {})})
        binb.extend(data)
        return len(g["bufferViews"]) - 1

    def put(arr, ctype, typ, target=None, norm=None, mm=False):
        a = {"bufferView": view(np.ascontiguousarray(arr).tobytes(), target), "componentType": ctype, "count": int(len(arr)), "type": typ}
        if norm:
            a["normalized"] = True
        if mm:
            a["min"] = [float(x) for x in arr.min(0)]
            a["max"] = [float(x) for x in arr.max(0)]
        g["accessors"].append(a)
        return len(g["accessors"]) - 1

    def sparse(arr):
        nz = np.nonzero(np.abs(arr).max(1) > 0)[0]
        if not len(nz):
            nz = np.zeros(1, np.int64)
        iv = view(nz.astype("<u4").tobytes())
        vv = view(arr[nz].astype("<f4").tobytes())
        g["accessors"].append({"componentType": 5126, "count": int(len(arr)), "type": "VEC3",
                               "sparse": {"count": int(len(nz)), "indices": {"bufferView": iv, "componentType": 5125}, "values": {"bufferView": vv}},
                               "min": [float(x) for x in np.minimum(arr[nz].min(0), 0)], "max": [float(x) for x in np.maximum(arr[nz].max(0), 0)]})
        return len(g["accessors"]) - 1
    for p_, (at, tg, faces) in zip(her.prims, outp):
        old = p_["attributes"]
        newa = {}
        for k, arr in at.items():
            oa = g["accessors"][old[k]]
            newa[k] = put(arr.astype(np.dtype(_CT[oa["componentType"]])), oa["componentType"], oa["type"], 34962, oa.get("normalized"), k == "POSITION")
        p_["attributes"] = newa
        idt, ict = (np.uint16, 5123) if len(at["POSITION"]) < 65536 else (np.uint32, 5125)
        p_["indices"] = put(faces.astype(idt).ravel(), ict, "SCALAR", 34963)
        p_["targets"] = [{k: sparse(t[k]) for k in ("POSITION", "NORMAL")} for t in tg]
    buf = io.BytesIO()
    im = Image.fromarray(np.clip(np.round(paint), 0, 255).astype(np.uint8), "RGBA")
    (im if bmode == "RGBA" else im.convert("RGB")).save(buf, "PNG")
    g["images"][bsi]["bufferView"] = view(buf.getvalue())
    g["images"][bsi]["mimeType"] = "image/png"
    g["buffers"][0]["byteLength"] = len(binb)
    G.buf, G.b0 = binb, 0
    compact(G)
    g["asset"].setdefault("extras", {})["pit_topo"] = {"params": P, "sides": {s: r["info"] for s, r in res.items()}, "islands": isl}
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binb = G.buf
    while len(binb) % 4:
        binb.append(0)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    her2 = Her(_Gl(dst))
    A1, UV1 = _areas(her2)
    k1 = np.sqrt(A1 / UV1) / 0.009
    log("PIT_TOPO: pore scale %.6f -> %.6f (%+.1e); faces %d -> %d; -> %s" % (k0, k1, k1 / k0 - 1, len(F), len(her2.F), dst))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    sides = next((x.split("=", 1)[1].split(",") for x in sys.argv if x.startswith("--sides=")), ["l", "r"])
    if os.environ.get("PIT_TOPO", "0") != "1":
        shutil.copyfile(a[0], a[1])
        print("PIT_TOPO off (PIT_TOPO=1 builds it): copied")
    else:
        run(a[0], a[1], sides)
