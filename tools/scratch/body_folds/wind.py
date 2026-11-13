"""Winding finder (same rule as Marionette base_winding.py): triangles whose face normal disagrees (dot < 0) with
the mean of their edge-neighbours' normals. Runs on any (V, T)."""
import collections
import numpy as np


def face_normals(V, T):
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def neighbours(T):
    em = collections.defaultdict(list)
    for t, tri in enumerate(T):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            em[(min(tri[a], tri[b]), max(tri[a], tri[b]))].append(t)
    nb = collections.defaultdict(list)
    for v in em.values():
        if len(v) == 2:
            nb[v[0]].append(v[1])
            nb[v[1]].append(v[0])
    return nb


def bad(V, T, nb=None):
    nb = nb or neighbours(T)
    fn = face_normals(V, T)
    out = []
    for t in range(len(T)):
        n = nb.get(t)
        if not n:
            continue
        m = fn[n].mean(0)
        m /= max(np.linalg.norm(m), 1e-9)
        if np.dot(fn[t], m) < 0:
            out.append(t)
    return np.array(out, int)
