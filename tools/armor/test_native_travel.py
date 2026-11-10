"""native_travel.skin: her skin as the game shows it (linear blend of her rest plus her corrective shapes)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gear_fit as gf  # noqa: E402
import native_travel as nt  # noqa: E402


def _ref():
    n = 6
    px, py = np.meshgrid(np.linspace(0, 0.1, n), np.linspace(0, 0.1, n))
    V = np.c_[px.ravel(), py.ravel(), np.zeros(n * n)]
    T = np.array([[i * n + j, i * n + j + 1, (i + 1) * n + j] for i in range(n - 1) for j in range(n - 1)]
                 + [[i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j] for i in range(n - 1) for j in range(n - 1)])
    t = V[:, 0] / 0.1
    J = np.c_[np.zeros(n * n, int), np.ones(n * n, int)]
    W = np.c_[1 - t, t]
    dP = np.zeros_like(V)
    dP[:, 2] = 0.01 * np.sin(np.pi * t) * np.sin(np.pi * V[:, 1] / 0.1)

    class Ref:
        pass
    r = Ref()
    r.V, r.T, r.J, r.W, r.joint_names, r.shapes = V, T, J, W, ["a", "b"], {"bulge": dP}
    r.wid = np.arange(len(V))
    r.N = gf.vertex_normals(V, T)
    return r


def _S(F=3):
    S = np.tile(np.eye(4), (F, 2, 1, 1))
    for f in range(F):
        c, s = np.cos(0.3 * f), np.sin(0.3 * f)
        S[f, 1, :3, :3] = [[c, 0, s], [0, 1, 0], [-s, 0, c]]
        S[f, 1, :3, 3] = [0.01 * f, 0, 0.002 * f]
    return S


def _old_skin(ref, S, index, vs):
    jm = np.array([index[n] for n in ref.joint_names])
    J, W = jm[np.asarray(ref.J)[vs]], np.asarray(ref.W, float)[vs]
    Vh = np.c_[ref.V[vs], np.ones(len(vs))]
    V, N = np.zeros((len(S), len(vs), 3)), np.zeros((len(S), len(vs), 3))
    for k in range(J.shape[1]):
        Sk = S[:, J[:, k]]
        V += W[None, :, k, None] * np.einsum("fvij,vj->fvi", Sk[:, :, :3, :], Vh)
        N += W[None, :, k, None] * np.einsum("fvij,vj->fvi", Sk[:, :, :3, :3], ref.N[vs])
    return V, N / np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-12)


def test_skin_without_shapes_is_bit_identical():
    r, S, ix = _ref(), _S(), {"a": 0, "b": 1}
    vs = np.arange(5, 30)
    for a, b in zip(nt.skin(r, S, ix, vs), _old_skin(r, S, ix, vs)):
        np.testing.assert_array_equal(a, b)


def test_skin_with_shapes_moves_by_the_weighted_delta_before_skinning():
    """A synthetic shape at weight w per frame: the skin is LBS(V + w dP) exactly, and its normals are the deformed
    mesh's own (at w 0 and rest: the stored normals)."""
    r, S, ix = _ref(), _S(), {"a": 0, "b": 1}
    vs = np.arange(len(r.V))
    w = np.array([0.0, 0.5, 1.0])
    V, N = nt.skin(r, S, ix, vs, cw={"bulge": w})
    for f in range(len(S)):
        R = r.V + w[f] * r.shapes["bulge"]
        Vh = np.c_[R, np.ones(len(R))]
        ref_V = sum(r.W[:, k, None] * np.einsum("vij,vj->vi", S[f, r.J[:, k], :3, :], Vh) for k in range(2))
        np.testing.assert_allclose(V[f], ref_V, atol=1e-12)
        np.testing.assert_allclose(N[f], gf.vertex_normals(ref_V, r.T), atol=1e-9)
    V0, N0 = nt.skin(r, np.tile(np.eye(4), (1, 2, 1, 1)), ix, vs, cw={"bulge": np.array([0.0])})
    np.testing.assert_allclose(N0[0], r.N, atol=1e-12)
    # a patch inside the mesh has the full ring's normals
    inner = np.array([14, 15, 20, 21])
    Vi, Ni = nt.skin(r, S, ix, inner, cw={"bulge": w})
    np.testing.assert_allclose(Ni, N[:, inner], atol=1e-12)
    np.testing.assert_allclose(Vi, V[:, inner], atol=1e-12)
