"""Closest points on a triangle mesh (numpy, exact): each query against the triangles nearest it by centroid.

    S = Surface(V, T); q, n, tri, d = S.closest(P, k=12)   # point, its triangle's normal, triangle, distance
The k triangles whose centroids are nearest each query are tested exactly (Ericson's region test).
"""
import numpy as np
from scipy.spatial import cKDTree


def closest_on_tris(p, a, b, c):
    """Vectorised closest point of p [n,3] on triangles (a, b, c) [n,3] each."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = np.einsum("ij,ij->i", ab, ap), np.einsum("ij,ij->i", ac, ap)
    bp = p - b
    d3, d4 = np.einsum("ij,ij->i", ab, bp), np.einsum("ij,ij->i", ac, bp)
    cp = p - c
    d5, d6 = np.einsum("ij,ij->i", ab, cp), np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v = vb / den
    w = vc / den
    out = a + ab * v[:, None] + ac * w[:, None]
    with np.errstate(divide="ignore", invalid="ignore"):
        # edges
        m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
        t = d1 / (d1 - d3)
        out[m] = (a + ab * t[:, None])[m]
        m2 = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
        t = d2 / (d2 - d6)
        out[m2] = (a + ac * t[:, None])[m2]
        m3 = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
        t = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        out[m3] = (b + (c - b) * t[:, None])[m3]
    # vertices
    out[(d1 <= 0) & (d2 <= 0)] = a[(d1 <= 0) & (d2 <= 0)]
    m = (d3 >= 0) & (d4 <= d3)
    out[m] = b[m]
    m = (d6 >= 0) & (d5 <= d6)
    out[m] = c[m]
    return out


class Surface:
    def __init__(self, V, T):
        self.V, self.T = np.asarray(V, float), np.asarray(T)
        A, B, C = self.V[self.T[:, 0]], self.V[self.T[:, 1]], self.V[self.T[:, 2]]
        fn = np.cross(B - A, C - A)
        self.FN = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-20)
        self.cent = (A + B + C) / 3
        self.tree = cKDTree(self.cent)

    def closest(self, P, k=12):
        P = np.asarray(P, float)
        _, cand = self.tree.query(P, k=k)
        best_d = np.full(len(P), np.inf)
        best_q = np.zeros_like(P)
        best_t = np.zeros(len(P), np.int64)
        for j in range(k):
            t = cand[:, j]
            q = closest_on_tris(P, self.V[self.T[t, 0]], self.V[self.T[t, 1]], self.V[self.T[t, 2]])
            d = np.linalg.norm(P - q, axis=1)
            m = d < best_d
            best_d[m], best_q[m], best_t[m] = d[m], q[m], t[m]
        return best_q, self.FN[best_t], best_t, best_d
