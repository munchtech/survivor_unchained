"""Her head's rest in the world, and the +7% head scale baked into the head meshes (P1 B2a, the approved undo (i)).

A (godot/art/people/heroine.glb) draws her head 7% larger by a rest scale on the Head joint left out of its inverse
bind (tools/assets/heroine_headscale.py, spec "bone_scale": {"Head": 1.07}); its Head bind also sits off its rest.
So in the world at rest each head vertex is  sum_k w_k S_k p  with S_k = rest_k @ ibm_k (identity for every joint
but Head: a uniform 1.07 scale plus a move). Baked: the head meshes' rest shape IS that world position, every joint
unscaled with a plain bind (ibm = inverse rest), so nothing in the file scales and the head is where A draws it.

    rest_world(mesh, skel) -> (Pw [V,3], c [V])   the mesh's rest world positions and each vertex's blended linear
                                                  scale (every S_k's linear part is c_k I: checked)
    bake(A, heads) -> {node: {"P", "c", "targets": {name: dP * c}}}   the head meshes' baked rest shapes; a blend
                                                  shape's move scales by the same c (it is added before skinning), its
                                                  normals' move and every normal are unchanged (a uniform scale keeps
                                                  directions)

Derivation: (a) the game's need (no rest scale for the game rig, outfits or the poser to carry; the head identical
in the world); (c) inherited: A's head meshes, their UVs, triangles, normals and blend shapes, named and unchanged
but for the bake. Pure numpy.
"""
import numpy as np


def skin_mats(skel):
    """S_k = rest_k @ ibm_k per joint, checked uniform-scale-plus-move."""
    S = skel.rest @ skel.ibm
    for k in range(len(S)):
        L = S[k][:3, :3]
        c = np.trace(L) / 3.0
        assert np.abs(L - c * np.eye(3)).max() < 1e-5, ("a joint's rest skin is not a uniform scale", skel.names[k])
    return S


def rest_world(mesh, skel):
    S = skin_mats(skel)
    P = mesh.P.astype(np.float64)
    Ph = np.concatenate([P, np.ones((len(P), 1))], 1)
    W = mesh.W / np.maximum(mesh.W.sum(1, keepdims=True), 1e-12)
    Pw = np.zeros_like(P)
    c = np.zeros(len(P))
    for k in range(mesh.J.shape[1]):
        Sk = S[mesh.J[:, k]]
        Pw += W[:, k:k + 1] * np.einsum("nij,nj->ni", Sk[:, :3, :], Ph)
        c += W[:, k] * np.einsum("nii->n", Sk[:, :3, :3]) / 3.0
    return Pw, c


def bake(A, heads):
    sk = A.skeleton()
    out = {}
    for h in heads:
        m = A.mesh(h)
        Pw, c = rest_world(m, sk)
        out[h] = {"P": Pw, "c": c,
                  "targets": {nm: t["POSITION"].astype(np.float64) * c[:, None] for nm, t in m.targets.items()}}
    return out
