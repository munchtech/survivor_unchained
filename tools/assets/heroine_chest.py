"""Her chest skin made smooth (outfits s25, knob CHEST_SMOOTH in heroine_outfits.py; run on her body just
before the export's mend_folds, after every piece is fitted to her, so no garment changes).

The sculpt's triangulation over her breasts is irregular (edges 3-20 mm, valence 3-12, slivers), so her
normals there were 11 deg off a smooth fit of her skin at p90 and 27 at p99: under a low light each
triangle read as its own facet, the pale wedge on her left breast inside the Arcanist neckline (the
same with her paint made one flat colour: it is her shape, not her paint). Three steps, all inside the
area (|x| < 0.20, y 1.345-1.505, front), her nipples' cores and her armpit crease left as they are:
  1. edges flipped toward better triangles (each flip cuts the bend over its quad's five edges and keeps
     the smallest angle; never across a UV seam, a material or a quad; no edge bent 6 deg past its own);
  2. her points faired (sum(1 - cos) of the bend over her edges) within the caps (CHEST_CAPN along her
     normal, CHEST_CAPT along her skin), eased to 0 over 2-3 rings at every edge of the area; the moves'
     local mean along her normal held near 0 (no dent, no bulge), no face turned past CHEST_ROT, no edge
     bent past its own by CHEST_CREASE, a sliver's corner barely moving (CHEST_KH);
  3. her normals there taken from a smooth fit of her skin (a quadric over 10 mm), as custom normals,
     which mend_folds carries and the export writes (her two morph targets, the elbows, leave her chest).
Vertex count, UVs, weights and shape keys' deltas are untouched (shape keys take the same offsets).

Coordinates: the fit works in glTF's frame (x her left, y up, z front); Blender's world is (x, -z, y) of that.
"""
import os

import numpy as np
import scipy.optimize as so
import scipy.sparse as sp
from scipy.spatial import cKDTree


def ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def fnormals(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    a = np.linalg.norm(fn, axis=1)
    return fn / np.maximum(a[:, None], 1e-18), a / 2


def vnormals(P, T):
    fn, _ = fnormals(P, T)
    n = np.zeros_like(P)
    for k in range(3):
        a = P[T[:, (k + 1) % 3]] - P[T[:, k]]; c = P[T[:, (k + 2) % 3]] - P[T[:, k]]
        ang = np.arctan2(np.linalg.norm(np.cross(a, c), axis=1), (a * c).sum(1))
        np.add.at(n, T[:, k], fn * ang[:, None])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)


def edge_faces(T):
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); fi = np.tile(np.arange(len(T)), 3)
    es = np.sort(e, 1); o = np.lexsort((es[:, 1], es[:, 0])); es, fi = es[o], fi[o]
    k = np.where(np.all(es[1:] == es[:-1], 1))[0]
    return es[k], fi[k], fi[k + 1]


def dihedral(P, T, E=None):
    fn, _ = fnormals(P, T)
    es, f0, f1 = E if E is not None else edge_faces(T)
    return es, np.degrees(np.arccos(np.clip((fn[f0] * fn[f1]).sum(1), -1, 1))), f0, f1


def _ang(P, p, q, r):
    u, v = P[q] - P[p], P[r] - P[p]
    return np.arctan2(np.linalg.norm(np.cross(u, v)), u @ v)


def _dih(n1, n2):
    return np.degrees(np.arccos(np.clip(n1 @ n2, -1, 1)))


def _tri_n(P, t):
    n = np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]])
    a = np.linalg.norm(n)
    return n / max(a, 1e-18), a / 2


def flip(P, T, K, UVc, mat, allow, mode="delaunay", slack=1.0, minang=12.0, max_pass=60, ref_d=None, crease_lim=6.0):
    """Lawson-style edge flips on triangles T (point ids into P; K per corner: the corner's identity,
    equal on both faces where no UV/normal seam runs; UVc per corner (m,3,2); mat per face).
    An edge a-b between faces (a,b,c), (b,a,d) becomes c-d when: all four points are `allow`ed, a and b
    have the same corner identity on both faces, both faces share a material, the new triangles keep
    the UV and 3D orientation, no edge of the quad gets bent more than `slack` deg past the quad's
    sharpest edge before, and
      mode 'delaunay': the angles opposite the edge sum past 180 deg (3D);
      mode 'ddt': the bend summed over the quad's five edges, sum(1-cos), drops, and the new smallest
                  angle is at least min(old smallest, minang)."""
    T = T.copy(); K = K.copy(); UVc = UVc.copy()
    flips = []
    for it in range(max_pass):
        E = {}
        for f, t in enumerate(T):
            for i in range(3):
                a, b = t[i], t[(i + 1) % 3]
                E.setdefault((min(a, b), max(a, b)), []).append(f)
        fn, _ = fnormals(P, T)
        cand = []
        for (a, b), fs in E.items():
            if len(fs) != 2 or not (allow[a] and allow[b]):
                continue
            f1, f2 = fs
            c = [v for v in T[f1] if v != a and v != b]; d = [v for v in T[f2] if v != a and v != b]
            if len(c) != 1 or len(d) != 1 or c[0] == d[0]:
                continue
            c, d = c[0], d[0]
            if not (allow[c] and allow[d]) or mat[f1] != mat[f2]:
                continue
            if (c, d) in E or (d, c) in E or (min(c, d), max(c, d)) in E:
                continue   # (would duplicate an edge)
            if mode == "delaunay":
                score = _ang(P, c, a, b) + _ang(P, d, a, b) - np.pi
                if score <= 1e-3:
                    continue
            else:
                score = 1.0
            cand.append((score, f1, f2, a, b, c, d))
        cand.sort(key=lambda t: -t[0])
        used = set(); done = 0
        for score, f1, f2, a, b, c, d in cand:
            if f1 in used or f2 in used:
                continue
            t1, t2 = list(T[f1]), list(T[f2])
            i0 = t1.index(a)
            if t1[(i0 + 1) % 3] != b:
                a, b = b, a
                i0 = t1.index(a)
            # (now t1 = (a, b, c) cyclically, t2 = (b, a, d))
            ka1, kb1, kc = K[f1][t1.index(a)], K[f1][t1.index(b)], K[f1][t1.index(c)]
            ka2, kb2, kd = K[f2][t2.index(a)], K[f2][t2.index(b)], K[f2][t2.index(d)]
            if ka1 != ka2 or kb1 != kb2:
                continue
            ua, ub, uc = UVc[f1][t1.index(a)], UVc[f1][t1.index(b)], UVc[f1][t1.index(c)]
            ud = UVc[f2][t2.index(d)]
            n1t, n2t = [a, d, c], [d, b, c]
            m1, ar1 = _tri_n(P, n1t); m2, ar2 = _tri_n(P, n2t)
            nav = fn[f1] + fn[f2]; nav /= np.linalg.norm(nav)
            if m1 @ nav < 0.5 or m2 @ nav < 0.5 or min(ar1, ar2) < 1e-10:
                continue

            def uvs(p, q, r):
                return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
            s0 = np.sign(uvs(ua, ub, uc))
            if s0 == 0 or np.sign(uvs(ua, ud, uc)) != s0 or np.sign(uvs(ud, ub, uc)) != s0:
                continue
            # the quad's outer edges: their other faces
            outer = []
            for (p, q, f, newf) in ((b, c, f1, 1), (c, a, f1, 0), (a, d, f2, 0), (d, b, f2, 1)):
                fs = E.get((min(p, q), max(p, q)), [])
                o = [g for g in fs if g != f]
                outer.append((o[0] if o else None, f, newf))
            old = [_dih(fn[f1], fn[f2])] + [_dih(fn[o], fn[f]) for o, f, _ in outer if o is not None]
            new = [_dih(m1, m2)] + [_dih(fn[o], (m1, m2)[nf]) for o, f, nf in outer if o is not None]
            if max(new) > max(old) + slack:
                continue
            if ref_d is not None:
                ek = [(min(a, b), max(a, b))] + [(min(p, q), max(p, q)) for (p, q) in ((b, c), (c, a), (a, d), (d, b))]
                okk = [o is not None for o, f, _ in outer]
                refs = [ref_d.get(ek[0], 0.0)] + [ref_d.get(e, 0.0) for e, ok_ in zip(ek[1:], okk) if ok_]
                if any(nw > rf + crease_lim for nw, rf in zip(new, refs)):
                    continue
            if mode == "ddt":
                b_old = sum(1 - np.cos(np.radians(x)) for x in old)
                b_new = sum(1 - np.cos(np.radians(x)) for x in new)
                if b_new > b_old * 0.97 - 1e-6:
                    continue
                angs_old = [_ang(P, *r) for r in ((a, b, c), (b, c, a), (c, a, b), (b, a, d), (a, d, b), (d, b, a))]
                angs_new = [_ang(P, *r) for r in ((a, d, c), (d, c, a), (c, a, d), (d, b, c), (b, c, d), (c, d, b))]
                if min(angs_new) < min(min(angs_old), np.radians(minang)):
                    continue
            T[f1] = n1t; T[f2] = n2t
            K[f1] = [ka1, kd, kc]; K[f2] = [kd, kb1, kc]
            UVc[f1] = [ua, ud, uc]; UVc[f2] = [ud, ub, uc]
            used |= {f1, f2}; done += 1
            flips.append((f1, f2, a, b, c, d))
            if ref_d is not None:
                ref_d[(min(c, d), max(c, d))] = ref_d.pop((min(a, b), max(a, b)), 0.0)
            fn[f1], fn[f2] = m1, m2
        if done == 0:
            break
    return T, K, UVc, flips


def quality(P, T):
    e = np.array([np.linalg.norm(P[T[:, i]] - P[T[:, (i + 1) % 3]], axis=1) for i in range(3)]).T
    _, ar = fnormals(P, T)
    return 4 * np.sqrt(3) * ar / (e ** 2).sum(1)


def lowpass(P, N, act, sigma=0.010, cos_min=0.7):
    """row-normalised Gaussian average over points within 2.5 sigma whose normals agree (not across her cleavage)"""
    idx = np.where(act)[0]
    tr = cKDTree(P[idx])
    rows, cols, vals = [], [], []
    for r, nb in enumerate(tr.query_ball_point(P[idx], 2.5 * sigma)):
        nb = np.array(nb)
        d = np.linalg.norm(P[idx[nb]] - P[idx[r]], axis=1)
        ok = (N[idx[nb]] @ N[idx[r]]) > cos_min
        g = np.exp(-0.5 * (d[ok] / sigma) ** 2)
        rows += [r] * ok.sum(); cols += list(nb[ok]); vals += list(g / g.sum())
    return sp.csr_matrix((vals, (rows, cols)), shape=(len(idx), len(idx)))


def fair(P0, T, w, Nref, capn=0.001, capt=0.00173, kt=20.0, klf=200.0, krot=1e4, rot_deg=25.0,
         kvol=50.0, lf_sigma=0.010, it=3000, shrink=0.6, ref_fn=None, ref_d=None, crease_lim=8.0, kcr=1e4, kh=0.0):
    """P0 with the points where w > 0 moved to minimise the bend across her edges, sum(1-cos), within
    caps (eased by w); the moves' local mean along her normal (a Gaussian over lf_sigma) held near 0 (no
    dents, no bulges: klf), no face turned past rot_deg from ref_fn (krot), a triangle never shrinking
    below `shrink` of its area, and each breast's volume kept (kvol)."""
    var = np.where(w > 1e-4)[0]
    nv = len(var)
    vi = np.full(len(P0), -1); vi[var] = np.arange(nv)
    fm = (vi[T] >= 0).any(1)
    es, f0, f1 = edge_faces(T)
    ke = fm[f0] | fm[f1]
    f0, f1 = f0[ke], f1[ke]
    eref = np.array([ref_d.get((a, b), 180.0) for a, b in es[ke]]) if ref_d is not None else np.full(len(f0), 180.0)
    qlim = 1 - np.cos(np.radians(np.minimum(eref + crease_lim, 179.0)))
    fu = np.unique(np.r_[f0, f1, np.where(fm)[0]])
    Tu = T[fu]
    fidx = np.full(len(T), -1); fidx[fu] = np.arange(len(fu))
    g0, g1 = fidx[f0], fidx[f1]
    NN = Nref[var]
    T1 = np.cross(NN, np.where(np.abs(NN[:, 1:2]) < 0.9, [[0, 1, 0]], [[1, 0, 0]]))
    T1 /= np.linalg.norm(T1, axis=1, keepdims=True)
    T2 = np.cross(NN, T1)
    a0 = np.linalg.norm(np.cross(P0[Tu[:, 1]] - P0[Tu[:, 0]], P0[Tu[:, 2]] - P0[Tu[:, 0]]), axis=1)
    if ref_fn is None:
        ref_fn = fnormals(P0, T)[0]
    rf = ref_fn[fu]
    crot = np.cos(np.radians(rot_deg))
    sc = 1e3
    cw = w[var].copy()
    if kh > 0:
        # (no point moves more than kh of its height over any of its triangles' far edges: a sliver's corner
        # barely moves, so no triangle turns far)
        hmin = np.full(len(P0), np.inf)
        for k in range(3):
            p, q, r = T[:, k], T[:, (k + 1) % 3], T[:, (k + 2) % 3]
            ar2 = np.linalg.norm(np.cross(P0[q] - P0[p], P0[r] - P0[p]), axis=1)
            h = ar2 / np.maximum(np.linalg.norm(P0[r] - P0[q], axis=1), 1e-12)
            np.minimum.at(hmin, p, h)
        cw = np.minimum(cw, kh * hmin[var] / capn)
    tb = capt / np.sqrt(2) * np.minimum(cw, w[var]) * sc
    nb = capn * np.minimum(cw, w[var]) * sc
    bounds = list(zip(np.r_[-tb, -tb, -nb], np.r_[tb, tb, nb]))
    side = np.sign(P0[var, 0])
    _, Va = _varea(P0, T)
    Vv = Va[var]
    LP = lowpass(P0, Nref, w > 1e-4, sigma=lf_sigma)
    LPT = LP.T.tocsr()
    av = Vv / Vv.mean()

    def pos(x):
        P = P0.copy()
        P[var] += (x[:nv, None] * T1 + x[nv:2 * nv, None] * T2 + x[2 * nv:, None] * NN) / sc
        return P

    def fg(x):
        P = pos(x)
        p0 = P[Tu[:, 0]]
        e1, e2 = P[Tu[:, 1]] - p0, P[Tu[:, 2]] - p0
        C = np.cross(e1, e2)
        L = np.linalg.norm(C, axis=1)
        nf = C / L[:, None]
        q = np.maximum(1 - (nf[g0] * nf[g1]).sum(1), 0)
        E = q.sum() * 1e3
        xc = np.maximum(q - qlim, 0)
        E += kcr * (xc ** 2).sum()
        ge = 1e3 + 2 * kcr * xc
        Gn = np.zeros_like(nf)
        np.add.at(Gn, g0, -ge[:, None] * nf[g1])
        np.add.at(Gn, g1, -ge[:, None] * nf[g0])
        # faces kept within rot_deg of their reference
        cr = (nf * rf).sum(1)
        over = np.maximum(crot - cr, 0)
        E += krot * (over ** 2).sum()
        Gn += (-2 * krot * over)[:, None] * rf
        sh = np.maximum(shrink - L / a0, 0)
        E += (sh ** 2).sum() * 1e3
        Gc = (Gn - (Gn * nf).sum(1)[:, None] * nf) / L[:, None] + (-2e3 * sh / a0 / L)[:, None] * C
        GP = np.zeros_like(P)
        np.add.at(GP, Tu[:, 1], np.cross(e2, Gc))
        np.add.at(GP, Tu[:, 2], np.cross(Gc, e1))
        np.add.at(GP, Tu[:, 0], -np.cross(e2, Gc) - np.cross(Gc, e1))
        gv = GP[var]
        g = np.r_[(gv * T1).sum(1), (gv * T2).sum(1), (gv * NN).sum(1)] / sc
        E += kt * (x[:2 * nv] ** 2).sum()
        g[:2 * nv] += kt * 2 * x[:2 * nv]
        c = x[2 * nv:]
        lf = LP @ c
        E += klf * (av * lf ** 2).sum()
        g[2 * nv:] += LPT @ (2 * klf * av * lf)
        for s in (1, -1):
            k = side == s
            vol = (c[k] * Vv[k]).sum() * 1e3
            E += kvol * vol ** 2
            g[2 * nv:][k] += kvol * 2 * vol * Vv[k] * 1e3
        return E, g

    r = so.minimize(fg, np.zeros(3 * nv), jac=True, method="L-BFGS-B", bounds=bounds,
                    options=dict(maxiter=it, maxfun=it * 2, ftol=1e-13, gtol=1e-9))
    return pos(r.x), r


def _varea(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    a = np.zeros(len(P))
    al = np.linalg.norm(fn, axis=1) / 6
    for k in range(3):
        np.add.at(a, T[:, k], al)
    return None, a


def mls_normals(P, T, act, sigma=0.010, R=0.025, nrm=None):
    """the normal of a quadric fit (Gaussian sigma, within R straight-line, normals agreeing) at each act point"""
    if nrm is None:
        nrm = vnormals(P, T)
    out = nrm.copy()
    idx = np.where(act)[0]
    tr = cKDTree(P)
    for i, nb in zip(idx, tr.query_ball_point(P[idx], R)):
        nb = np.array(nb)
        nz = nrm[i]
        nb = nb[(nrm[nb] @ nz) > 0.5]
        q = P[nb] - P[i]
        t1 = np.cross(nz, [0, 1, 0] if abs(nz[1]) < 0.9 else [1, 0, 0]); t1 /= np.linalg.norm(t1)
        t2 = np.cross(nz, t1)
        u, v, h = q @ t1, q @ t2, q @ nz
        wg = np.sqrt(np.exp(-0.5 * (np.linalg.norm(q, axis=1) / sigma) ** 2))
        A = np.c_[np.ones_like(u), u, v, u * u, u * v, v * v]
        c, *_ = np.linalg.lstsq(A * wg[:, None], h * wg, rcond=None)
        g = nz - c[1] * t1 - c[2] * t2
        out[i] = g / np.linalg.norm(g)
    return out


# ---------------------------------------------------------------- the build's step (Blender)
_f = lambda k, d: float(os.environ.get(k, d))
CAPN = _f("CHEST_CAPN", "0.001")        # (m) along her normal
CAPT = _f("CHEST_CAPT", "0.00173")      # (m) along her skin
HALFW = _f("CHEST_X", "0.20")           # (m) the area: |x| < HALFW, y from Y0 to Y1, front only
Y0 = _f("CHEST_Y0", "1.345")            # (above her inframammary fold, which stays as it is)
Y1 = _f("CHEST_Y1", "1.505")            # (below throat_fill's band, 1.525 up)
RAMP = _f("CHEST_RAMP", "0.022")        # (eased over 2-3 rings at the area's edges)
RAMP_LO = _f("CHEST_RAMP_LO", "0.025")  # (and over 3 above her fold)
TIP_CORE, TIP_IN, TIP_OUT, TIP_W = _f("CHEST_TIP_CORE", "0.012"), 0.025, _f("CHEST_TIP_OUT", "0.040"), 0.149
ARM0 = _f("CHEST_ARM0", "0.25")         # (her armpit crease: none moves where her upper arm holds this much)
KH = _f("CHEST_KH", "0.15")             # (no point moves past KH of its height over a triangle's far edge)
ROT = _f("CHEST_ROT", "20")             # (deg: no face turned past this in the fairing)
KLF = _f("CHEST_KLF", "200")            # (the moves' local mean along her normal held near 0: no dents)
KCR = _f("CHEST_KCR", "1e5")            # (no edge bent past its own bend + CREASE)
CREASE = _f("CHEST_CREASE", "7")
FLIP = os.environ.get("CHEST_FLIP", "ddt")
NRM = os.environ.get("CHEST_NRM", "1") == "1"
NSIG = _f("CHEST_NSIG", "0.010")
NCORE, NTIP = _f("CHEST_NCORE", "0.010"), _f("CHEST_NTIP", "0.010")
ITER = int(_f("CHEST_ITER", "5000"))
TIP_GUESS = (np.array([0.119, 1.422, 0.163]), np.array([-0.121, 1.425, 0.156]))


def find_tips(P):
    tips = []
    for g in TIP_GUESS:
        d = np.linalg.norm(P - g, axis=1)
        tips.append(P[np.argmin(d)] if d.min() < 0.005 else g)
    return tips


def weights(P, tips, arm):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    w = ss((HALFW - np.abs(x)) / RAMP) * ss((y - Y0) / RAMP_LO) * ss((Y1 - y) / RAMP) * ss(z / 0.02)
    for t in tips:
        d = np.linalg.norm(P - t, axis=1)
        w *= np.where(d < TIP_IN, TIP_W * ss((d - TIP_CORE) / (TIP_IN - TIP_CORE)),
                      TIP_W + (1 - TIP_W) * ss((d - TIP_IN) / (TIP_OUT - TIP_IN)))
    return w * ss((ARM0 - arm) / 0.15)


def nweights(P, tips, arm):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    w = ss((HALFW - np.abs(x)) / 0.02) * ss((y - Y0) / 0.02) * ss((Y1 - y) / 0.02) * ss(z / 0.02)
    for t in tips:
        w *= ss((np.linalg.norm(P - t, axis=1) - NCORE) / NTIP)
    return w * ss((ARM0 - arm) / 0.15)


def chest_smooth(obj, mend=None):
    """mend: heroine_outfits.mend_folds (her chest's fold clusters mended first, at P6's places).
    Then: edges flipped toward better triangles (never across a UV seam, a material or a quad), her points
    faired within the caps, and her normals there taken from a smooth fit of her skin (custom normals,
    which the export keeps and mend_folds carries)."""
    import bmesh
    me = obj.data
    mw = obj.matrix_world
    if mend is not None:
        def _box(co):
            p = mw @ co
            return abs(p.x) < 0.20 and 1.30 < p.z < 1.50 and p.y < 0.03
        mend(me, obj, free=_box, normals=False)
    co = np.array([v.co[:] for v in me.vertices])
    Pw = np.array([(mw @ v.co)[:] for v in me.vertices])
    G = np.c_[Pw[:, 0], Pw[:, 2], -Pw[:, 1]]          # (glTF's frame, per Blender vertex)
    _, w_ = np.unique(np.round(Pw / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    w_ = w_.ravel()
    Gw = np.zeros((w_.max() + 1, 3)); Gw[w_] = G
    up = {g.index for g in obj.vertex_groups if "upperarm" in g.name.lower()}
    arm = np.array([sum(e.weight for e in v.groups if e.group in up) for v in me.vertices])
    armw = np.zeros(len(Gw)); np.maximum.at(armw, w_, arm)
    tips = find_tips(Gw)
    # ---- flips (on her triangles as Blender has them: a quad's two halves are never flipped)
    nfl, bad = 0, 0
    if FLIP != "none":
        me.calc_loop_triangles()
        T = np.array([t.vertices[:] for t in me.loop_triangles])
        Lc = np.array([t.loops[:] for t in me.loop_triangles])
        pi = np.array([t.polygon_index for t in me.loop_triangles])
        uv = np.empty(len(me.loops) * 2); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
        UVc = uv[Lc]
        kk = np.c_[T.reshape(-1), np.round(UVc.reshape(-1, 2) * 1e6).astype(np.int64)]
        K = np.unique(kk, axis=0, return_inverse=True)[1].ravel().reshape(-1, 3)
        psz = np.array([p.loop_total for p in me.polygons]); pm = np.array([p.material_index for p in me.polygons])
        mat = np.where(psz[pi] == 3, pm[pi], -1 - np.arange(len(T)))
        wv = weights(G, tips, arm)
        dt = np.min([np.linalg.norm(G - t, axis=1) for t in tips], axis=0)
        allow = (np.abs(G[:, 0]) < HALFW) & (G[:, 1] > Y0) & (G[:, 1] < Y1) & (G[:, 2] > 0) & (dt > TIP_CORE) & (wv > 0.05)
        es0, d0, _, _ = dihedral(G, T)
        ref_d = {(int(a), int(b)): d for (a, b), d in zip(es0, d0)}
        _, _, _, fl = flip(G, T, K, UVc, mat, allow, mode=FLIP, slack=1.0, minang=12.0, ref_d=ref_d, crease_lim=6.0)
        bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
        for f1, f2, a, b, c, d in fl:
            e = bm.edges.get((bm.verts[a], bm.verts[b]))
            if e is None or len(e.link_faces) != 2 or any(len(f.verts) != 3 for f in e.link_faces):
                bad += 1
                continue
            bmesh.ops.rotate_edges(bm, edges=[e], use_ccw=False)
            if bm.edges.get((bm.verts[c], bm.verts[d])) is None:
                bad += 1
        bm.to_mesh(me); bm.free(); me.update()
        nfl = len(fl)
    me.calc_loop_triangles()
    Tb = np.array([t.vertices[:] for t in me.loop_triangles])
    Tw = w_[Tb]
    Tw = Tw[(Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])]
    # ---- fairing (welded points: split points move together)
    ww = weights(Gw, tips, armw)
    esw, dw0, _, _ = dihedral(Gw, Tw)
    refw = {(int(a), int(b)): d for (a, b), d in zip(esw, dw0)}
    N0 = vnormals(Gw, Tw)
    Gn, res = fair(Gw, Tw, ww, N0, capn=CAPN, capt=CAPT, klf=KLF, krot=1e5, rot_deg=ROT, it=ITER, ref_d=refw,
                   crease_lim=CREASE, kcr=KCR, kh=KH)
    D = Gn - Gw
    Dw = np.c_[D[:, 0], -D[:, 2], D[:, 1]]
    dl = Dw[w_] @ np.array(mw.inverted().to_3x3()).T
    moved = np.nonzero(np.linalg.norm(dl, axis=1) > 1e-9)[0]
    for i in moved:
        me.vertices[i].co = (co[i] + dl[i]).tolist()
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            for i in moved:
                kb.data[i].co = (np.array(kb.data[i].co[:]) + dl[i]).tolist()
    me.update()
    # ---- normals: a smooth fit's over her chest (blended to her own at the area's edges and nipples)
    nn = 0
    if NRM:
        wn = nweights(Gn, tips, armw)
        act = wn > 1e-4
        nb = vnormals(Gn, Tw)
        nm = mls_normals(Gn, Tw, act, sigma=NSIG, R=2.5 * NSIG, nrm=nb)
        out = nb * (1 - wn[:, None]) + nm * wn[:, None]
        out /= np.linalg.norm(out, axis=1, keepdims=True)
        ob = np.c_[out[:, 0], -out[:, 2], out[:, 1]] @ np.array(mw.to_3x3())   # (to her local frame: mw rotation-only)
        ob /= np.linalg.norm(ob, axis=1, keepdims=True)
        nl = len(me.loops)
        cn = np.empty(nl * 3, np.float32); me.corner_normals.foreach_get("vector", cn); cn = cn.reshape(-1, 3).astype(float)
        lv = np.empty(nl, np.int64); me.loops.foreach_get("vertex_index", lv)
        lw = w_[lv]
        # (never across a normal seam: a point whose corners' normals differ keeps them, or the export
        # would weld its copies and her vertex count would change)
        mean = np.zeros((len(Gw), 3)); np.add.at(mean, lw, cn)
        mean /= np.maximum(np.linalg.norm(mean, axis=1, keepdims=True), 1e-12)
        spread = np.ones(len(Gw)); np.minimum.at(spread, lw, (cn * mean[lw]).sum(1))
        act &= spread > np.cos(np.radians(1.0))
        sel = act[lw]
        cn[sel] = ob[lw[sel]]
        me.normals_split_custom_set([tuple(v) for v in cn])
        nn = int(act.sum())
    if os.environ.get("CHEST_DUMP"):
        np.savez(os.environ["CHEST_DUMP"], G=Gw, Gn=Gn, T=Tw, w=ww, tips=np.array(tips))
    mv = np.linalg.norm(D, axis=1)
    _, Va = _varea(Gw, Tw)
    dn = (D * N0).sum(1)
    print("CHEST: %d flips (%d failed), %d points moved, %.2f mm at most (%.2f along her normal), %.2f mean; vol L %+.3f R %+.3f cm3; "
          "%d iterations (%s); normals from the fit at %d points"
          % (nfl, bad, len(moved), mv.max() * 1e3, np.abs(dn).max() * 1e3, mv[mv > 1e-9].mean() * 1e3 if (mv > 1e-9).any() else 0,
             (dn * Va)[Gw[:, 0] > 0].sum() * 1e6, (dn * Va)[Gw[:, 0] < 0].sum() * 1e6, res.nit, res.message, nn))
