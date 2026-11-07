"""Her fit's target: A's shipped body (Mesh_0 in node "Heroine", rest = the sculpt's A-pose) posed through her game
stack (tools/anim/skin.py Body with helpers: her correctives and helpers as the game drives them) into a base's rest,
so both stand alike before fitting. Only the posed shape is used. world=True (OUR topology's fit, wrap_topo.py): her
game Head scale and off-rest bind kept, so her neck stands under her head's world rest as our build's does (B2a's
headbake.py); world=False (v1's): the files' stored space.

    target(base_glb) -> dict: P [n,3] welded posed points (glTF), T [m,3], N [n,3], bones {name: (head, tail)} posed,
                              turns {bone: degrees turned}, rest_bones {name: (head, tail)} the base's
Each chain bone (clavicle, upperarm, lowerarm, hand, thigh, calf; both sides) is turned, root to leaf, by the
least rotation taking its direction (its head to the next joint's) onto the base's same bone's. The spine, neck and
pelvis are not turned: her trunk stands as sculpted (the head ring is the same in both); nor the foot: it stays flat
on the ground as the calf carries it (the feet are MakeHuman's; the joints' conventions differ there, so matching the
foot bone tilts her sole).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
ANIM = os.path.join(REPO, "tools", "anim")
A_PATH = os.path.join(REPO, "godot", "art", "people", "heroine.glb")
CHAIN = [("clavicle", "upperarm"), ("upperarm", "lowerarm"), ("lowerarm", "hand"), ("hand", "middle_01"),
         ("thigh", "calf"), ("calf", "foot")]
TRUNK = [("pelvis", "spine_01"), ("spine_03", "neck_01")]


def base_bones(glb_path):
    from gl import Glb
    fs = Glb(glb_path).skeleton(0)
    out = {}
    for s in "lr":
        for a, b in CHAIN:
            out[f"{a}_{s}"] = (fs.rest[fs.index[f"{a}_{s}"]][:3, 3], fs.rest[fs.index[f"{b}_{s}"]][:3, 3])
    return out


def weld(P, tol=1e-6):
    key = np.round(P / tol).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return first, inv.ravel()


def target(base_glb, a_path=A_PATH, world=False, want=None, normals=None):
    """(want: the chain bones {name: (head, tail)} to pose A to, instead of base_glb's rest; only their directions
    are used, so a target's own posed bones ("bones") re-pose A to that target exactly; a None entry leaves that
    bone at A's own rest turn)
    (normals: A's rest normals as its file stores them, [V, 3] in the body's point order (unwelded): returned posed as
    "N_file", each turned by its point's blended skinning matrix with the corrective shapes' normals in, as Godot
    skins them. "N" stays the welded mesh's area-weighted normals.)"""
    if ANIM not in sys.path:
        sys.path.insert(0, ANIM)
    import skin
    from rig import Skeleton, qbetween, qinv, qmul
    sk = Skeleton.load(skin.SKELETONS / "heroine_skeleton.json")
    body = skin.Body(sk, [(a_path, lambda n: n == "Heroine", "skin")], None, label="her", helpers=True)
    want = want if want is not None else base_bones(base_glb)
    # (the fit is in the files' stored space, where her head and ring and B's coincide: the game's Head scale (1.07)
    # and the off-rest bind it gives the body's points on Head (heroine_headscale.py) are taken off, so her rest
    # poses to her stored points exactly)
    nb = len(sk.names)
    if not world:   # (world: OUR topology's build stands under her head baked to its world rest, so does she)
        body.Jv = np.where(body.Jv >= nb, np.array([j for j, _ in body.vbind] + [0])[np.clip(body.Jv - nb, 0, None)], body.Jv)
        body.vbind = []
    rot = sk.rest_rot.copy()
    grot0, _ = sk.fk(rot[None])
    turns = {}
    for s in "lr":
        for a, b in CHAIN:
            j, k = sk.index[f"{a}_{s}"], sk.index[f"{b}_{s}"]
            if want.get(f"{a}_{s}", ()) is None:     # None: the bone keeps A's own rest turn (her_a_target "a_rest")
                turns[f"{a}_{s}"] = 0.0
                continue
            grot, gpos = sk.fk(rot[None])
            cur = gpos[0, k] - gpos[0, j]
            h, t = want[f"{a}_{s}"]
            w = t - h
            cur, w = cur / np.linalg.norm(cur), w / np.linalg.norm(w)
            q = qbetween(cur, w)
            turns[f"{a}_{s}"] = round(float(np.degrees(np.arccos(np.clip(cur @ w, -1, 1)))), 2)
            p = sk.parent[j]
            rot[j] = qmul(qinv(grot[0, p]), qmul(q, grot[0, j]))
        j = sk.index[f"foot_{s}"]                       # the foot keeps its rest's turn in the world (flat)
        grot, _ = sk.fk(rot[None])
        rot[j] = qmul(qinv(grot[0, sk.parent[j]]), grot0[0, j])
    clip = skin.Clip("pose", 30.0, rot[None], sk.rest_pos[None].copy(), False)
    G = body.globals(clip, 0, {}, 1 / 30)
    for j, sc in ({} if world else body.rest_scale).items():
        G[j, :3, :3] = G[j, :3, :3] / sc
    Pv = body.pose(G)
    first, inv = weld(body.P)
    P = Pv[first]
    T = inv[body.T]
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros_like(P)
    for c in range(3):
        np.add.at(N, T[:, c], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    bones = {}
    for s in "lr":
        for a, b in CHAIN:
            bones[f"{a}_{s}"] = (G[sk.index[f"{a}_{s}"]][:3, 3].copy(), G[sk.index[f"{b}_{s}"]][:3, 3].copy())
    want = {k: v for k, v in want.items() if v is not None}
    extra = {}
    if normals is not None:
        assert normals.shape == body.P.shape, ("the normals are not the body's points", normals.shape, body.P.shape)
        Nr = body.rest_normals(np.asarray(normals, np.float64), G)
        S = body.skin_mats(G)
        M = np.zeros((len(Nr), 3, 3))
        for k in range(body.Jv.shape[1]):
            M += body.W[:, k, None, None] * S[body.Jv[:, k], :3, :3]
        Nf = np.einsum("nij,nj->ni", M, Nr)
        extra["N_file"] = Nf / np.maximum(np.linalg.norm(Nf, axis=1, keepdims=True), 1e-12)
        extra["P_file"] = body.P            # (the rest points in that order, for the caller's check)
    return {**extra, "P": P, "T": T, "N": N, "bones": bones, "turns": turns, "rest_bones": want,
            "rest_P": body.P[first], "shapes": body.shape_weights(G), "J": body.Jv[first], "W": body.W[first],
            "names": list(sk.names)}
