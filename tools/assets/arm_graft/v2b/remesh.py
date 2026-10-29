# Body 2 B: UV-preserving densify of a mesh region (split long edges, Delaunay flips, tangential relax with every moved
# vertex snapped back onto the reference surface of ITS OWN UV island, seams and region border locked).
# The reference surface S0 is a triangle set with corner UVs; each working face keeps the island of the S0 face it came
# from, and its corner UVs are re-sampled at the end by exact point location on that island (barycentric).
import numpy as np
from geo import Surf


def islands(T, UV, key=None, tol=1e-6):
    """Faces joined across an edge when both endpoints' UVs match (and key matches). Returns island id per face."""
    n = len(T); par = np.arange(n)

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    H = np.c_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]].reshape(-1, 2)
    HU = np.concatenate([UV[:, [0, 1]], UV[:, [1, 2]], UV[:, [2, 0]]], 1).reshape(-1, 2, 2)
    fid = np.repeat(np.arange(n), 3)
    N = T.max() + 1
    k = H[:, 0] * N + H[:, 1]; kr = H[:, 1] * N + H[:, 0]
    o = np.argsort(k); ks = k[o]
    j = np.searchsorted(ks, kr); j = np.clip(j, 0, len(ks) - 1); hit = ks[j] == kr
    for h in np.nonzero(hit)[0]:
        g = o[j[h]]
        if np.abs(HU[h, 0] - HU[g, 1]).max() < tol and np.abs(HU[h, 1] - HU[g, 0]).max() < tol and (key is None or key[fid[h]] == key[fid[g]]):
            a, b = find(fid[h]), find(fid[g])
            if a != b: par[a] = b
    r = np.array([find(i) for i in range(n)])
    _, inv = np.unique(r, return_inverse=True)
    return inv


class Ref:
    """Reference surface per island: point location restricted to an island."""
    def __init__(s, V, T, UV, FI, k=48):
        s.V, s.T, s.UV, s.FI = V, T, UV, FI; s.S = {}
        for i in np.unique(FI):
            f = np.nonzero(FI == i)[0]
            s.S[i] = (f, Surf(V, T[f], k=min(k, len(f))))

    def locate(s, X, isl):
        q = np.zeros_like(X); fi = np.zeros(len(X), int); bar = np.zeros((len(X), 3)); dist = np.zeros(len(X))
        for i in np.unique(isl):
            m = isl == i; f, S = s.S[i]
            qq, dd, ff, bb = S.query(X[m]); q[m] = qq; fi[m] = f[ff]; bar[m] = bb; dist[m] = dd
        return q, fi, bar, dist

    def uv(s, fi, bar):
        return (s.UV[fi] * bar[:, :, None]).sum(1)


def half(T):
    return np.c_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]].reshape(-1, 2)


class Work:
    def __init__(s, V, T, FI, locked, ref):
        s.V = V.copy(); s.T = T.copy(); s.FI = FI.copy(); s.ref = ref
        H, twin = s.edges(); border, isl = s.seam_mask(H, twin)
        s.locked = locked.copy(); s.locked[H[isl].ravel()] = True

    def edges(s):
        H = half(s.T); N = len(s.V)
        k = H[:, 0] * N + H[:, 1]; kr = H[:, 1] * N + H[:, 0]
        o = np.argsort(k); ks = k[o]; j = np.clip(np.searchsorted(ks, kr), 0, len(ks) - 1)
        twin = np.where(ks[j] == kr, o[j], -1)
        return H, twin

    def seam_mask(s, H, twin):
        """per half-edge: True if it may not be split/flipped (border, island change, locked both ends on a seam)."""
        f = np.arange(len(H)) // 3
        border = twin < 0
        isl = np.where(border, True, s.FI[f] != s.FI[np.maximum(twin, 0) // 3])
        return border, isl

    def split(s, thr):
        H, twin = s.edges(); border, isl = s.seam_mask(H, twin)
        L = np.linalg.norm(s.V[H[:, 0]] - s.V[H[:, 1]], axis=1)
        mark = (L > thr) & ~border
        # a face with a long border edge is kept whole (splitting its other edges would fan slivers onto the border)
        f = np.arange(len(H)) // 3
        bad = np.zeros(len(s.T), bool); bad[f[border & (L > thr)]] = True
        mark &= ~bad[f] & ~np.where(twin >= 0, bad[np.maximum(twin, 0) // 3], False)
        # one new vertex per undirected marked edge
        und = mark & ((H[:, 0] < H[:, 1]) | (twin < 0))
        idx = np.nonzero(und)[0]
        nv0 = len(s.V)
        mid = np.full(len(H), -1); mid[idx] = nv0 + np.arange(len(idx))
        tw = twin[idx]; mid[tw[tw >= 0]] = mid[idx[tw >= 0]]
        Pm = 0.5 * (s.V[H[idx, 0]] + s.V[H[idx, 1]])
        # midpoints of interior non-seam edges may be chords off the surface: put them back on their island
        fis = s.FI[idx // 3]
        q, _, _, _ = s.ref.locate(Pm, fis)
        on_seam = isl[idx]
        Pm = np.where(on_seam[:, None], Pm, q)
        s.V = np.vstack([s.V, Pm])
        s.locked = np.r_[s.locked, on_seam]
        M = mid.reshape(-1, 3)   # per face: mid of edge (0-1), (1-2), (2-0)
        newT = []; newF = []
        for fi_, (t, m) in enumerate(zip(s.T, M)):
            a, b, c = t; mab, mbc, mca = m; k = int(mab >= 0) + int(mbc >= 0) + int(mca >= 0); F = s.FI[fi_]
            if k == 0: newT.append(t); newF.append(F); continue
            if k == 3:
                newT += [(a, mab, mca), (mab, b, mbc), (mca, mbc, c), (mab, mbc, mca)]; newF += [F] * 4; continue
            # rotate so the first marked edge is (a,b)
            for _ in range(3):
                if (k == 1 and mab >= 0) or (k == 2 and mca < 0): break
                a, b, c = b, c, a; mab, mbc, mca = mbc, mca, mab
            if k == 1:
                newT += [(a, mab, c), (mab, b, c)]; newF += [F] * 2
            else:  # marked (a,b) and (b,c)
                # split the quad (a, mab, mbc, c) on its shorter diagonal
                newT.append((mab, b, mbc)); newF.append(F)
                if np.linalg.norm(s.V[a] - s.V[mbc]) < np.linalg.norm(s.V[mab] - s.V[c]):
                    newT += [(a, mab, mbc), (a, mbc, c)]
                else:
                    newT += [(a, mab, c), (mab, mbc, c)]
                newF += [F] * 2
        s.T = np.array(newT); s.FI = np.array(newF)
        return len(idx)

    def flip(s, passes=20, maxdih=25.0):
        tot = 0
        for _ in range(passes):
            H, twin = s.edges(); border, isl = s.seam_mask(H, twin)
            V = s.V; T = s.T
            h = np.nonzero(~border & ~isl & (H[:, 0] < H[:, 1]))[0]
            g = twin[h]; f1 = h // 3; f2 = g // 3
            a, b = H[h, 0], H[h, 1]
            c = T[f1, (h % 3 + 2) % 3]; dd = T[f2, (g % 3 + 2) % 3]

            def ang(p, q, r):
                u = V[q] - V[p]; v = V[r] - V[p]
                return np.arctan2(np.linalg.norm(np.cross(u, v), axis=1), (u * v).sum(1))
            viol = ang(c, a, b) + ang(dd, b, a) > np.pi + 1e-3
            n1 = np.cross(V[b] - V[a], V[c] - V[a]); n2 = np.cross(V[a] - V[b], V[dd] - V[b])
            n1 /= np.maximum(np.linalg.norm(n1, axis=1), 1e-15)[:, None]; n2 /= np.maximum(np.linalg.norm(n2, axis=1), 1e-15)[:, None]
            dih = np.degrees(np.arccos(np.clip((n1 * n2).sum(1), -1, 1)))
            m1 = np.cross(V[a] - V[c], V[dd] - V[c]); m2 = np.cross(V[b] - V[dd], V[c] - V[dd])
            nn = n1 + n2
            val = np.bincount(T.ravel(), minlength=len(V))
            ok = viol & (val[a] > 4) & (val[b] > 4) & (dih < maxdih) & ((m1 * nn).sum(1) > 0) & ((m2 * nn).sum(1) > 0) & (c != dd)
            # the new edge must not exist already
            N = len(V); ek = set((H[:, 0] * N + H[:, 1]).tolist())
            used = np.zeros(len(T), bool); cnt = 0
            for i in np.nonzero(ok)[0]:
                if used[f1[i]] or used[f2[i]]: continue
                if (c[i] * N + dd[i]) in ek: continue
                T[f1[i]] = (c[i], a[i], dd[i]); T[f2[i]] = (dd[i], b[i], c[i])
                used[f1[i]] = used[f2[i]] = True; cnt += 1
                ek.add(c[i] * N + dd[i]); ek.add(dd[i] * N + c[i])
            tot += cnt
            if cnt == 0: break
        return tot

    def vnorm(s):
        V, T = s.V, s.T
        fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]); N = np.zeros_like(V)
        for k in range(3): np.add.at(N, T[:, k], fn)
        return N / np.maximum(np.linalg.norm(N, axis=1), 1e-15)[:, None]

    def relax(s, iters=5, lam=0.5, extra_fixed=None):
        fixed = s.locked.copy()
        if extra_fixed is not None: fixed |= extra_fixed
        for _ in range(iters):
            V, T = s.V, s.T
            # area-weighted centroid of the 1-ring faces
            fc = V[T].mean(1); fa = 0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1)
            C = np.zeros_like(V); A = np.zeros(len(V))
            for k in range(3): np.add.at(C, T[:, k], fc * fa[:, None]); np.add.at(A, T[:, k], fa)
            C = C / np.maximum(A, 1e-15)[:, None]
            N = s.vnorm(); D = C - V; D -= (D * N).sum(1)[:, None] * N
            used = A > 0
            mv = used & ~fixed
            X = V.copy(); X[mv] += lam * D[mv]
            # snap onto the island of the vertex (any incident face; free vertices touch one island only)
            isl = np.zeros(len(V), int); isl[T.ravel()] = np.repeat(s.FI, 3)
            q, _, _, _ = s.ref.locate(X[mv], isl[mv])
            X[mv] = q; s.V = X

    def corner_uv(s):
        T = s.T; X = s.V[T.ravel()]; isl = np.repeat(s.FI, 3)
        q, fi, bar, dist = s.ref.locate(X, isl)
        return s.ref.uv(fi, bar).reshape(-1, 3, 2), dist.reshape(-1, 3)

    def vertex_anchor(s):
        """per vertex: an S0 face and barycentric (for weights, which have no seams)."""
        isl = np.zeros(len(s.V), int); isl[s.T.ravel()] = np.repeat(s.FI, 3)
        q, fi, bar, dist = s.ref.locate(s.V, isl)
        k = np.argmax(dist); print("  worst anchor", k, dist[k], "isl", isl[k], "used", k in set(s.T.ravel().tolist()), "locked", s.locked[k])
        return fi, bar, dist
