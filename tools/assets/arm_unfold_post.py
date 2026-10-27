"""Her arms' folded face clusters relaxed out of the rest mesh (Body 6 fix, 24 Oct: the owner's "lump on the left arm
that's resting"; a left-only fold on the upper arm's lower half, rest (0.274, 1.309, -0.032), faces turned 127-149 deg
against the surface around them, from the mirror step):

    ARM_UNFOLD=1 python tools/assets/arm_unfold_post.py <in heroine.glb> <out heroine.glb>

Finds faces on her arms (0.22 < |x| < 0.50 m: shoulder to wrist, no hands) whose normal is over UNFOLD_DEG (60) off the
heavily smoothed surface's, and relaxes the points within UNFOLD_R (12 mm) of them (Taubin, eased out) until none is
left. Moves rest POSITION only, on every primitive of her body (the welded union's move), and turns each moved point's
NORMAL as its surface turned; weights, morph deltas and every other point are untouched. Any slot (run it last or
anywhere after the shape: it reads and writes only positions and normals). Without ARM_UNFOLD=1 it copies the body."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scap_rig_post import Glb  # noqa: E402
from wrap_post import skin_union  # noqa: E402

DEG = float(os.environ.get("UNFOLD_DEG", 60.0))
R = float(os.environ.get("UNFOLD_R", 0.012))


def _adj(F, n):
    from scipy.sparse import coo_matrix
    E = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]
    A = coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    return A, np.maximum(np.asarray(A.sum(1)).ravel(), 1)


def _fn(X, F):
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    return q / np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)


def _vn(X, F):
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    n = np.zeros_like(X)
    for k in range(3):
        np.add.at(n, F[:, k], q)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def folded(X, F, A, d, zone):
    Xs = X.copy()
    for _ in range(15):
        Xs = 0.5 * Xs + 0.5 * (A @ Xs) / d[:, None]
    ang = np.degrees(np.arccos(np.clip((_fn(X, F) * _fn(Xs, F)).sum(1), -1, 1)))
    return np.nonzero(zone & (ang > DEG))[0]


def unfold(U, F):
    """(new U, moved mask, report)"""
    A, d = _adj(F, len(U))
    fc = U[F].mean(1)
    zone = (np.abs(fc[:, 0]) > 0.22) & (np.abs(fc[:, 0]) < 0.50)
    bad = folded(U, F, A, d, zone)
    rep = {"faces": len(bad), "at": np.round(fc[bad], 3).tolist()}
    if not len(bad):
        return U, np.zeros(len(U), bool), rep
    from scipy.spatial import cKDTree
    dist, _ = cKDTree(fc[bad]).query(U)
    w = np.where(dist < R, (1 - (dist / R) ** 2) ** 2, 0.0)
    X = U.copy()
    for it in range(200):
        L = (A @ X) / d[:, None] - X
        X = X + 0.5 * w[:, None] * L
        L = (A @ X) / d[:, None] - X
        X = X - 0.53 * w[:, None] * L
        if it % 10 == 9 and not len(folded(X, F, A, d, zone)):
            break
    rep["iters"] = it + 1
    rep["left"] = len(folded(X, F, A, d, zone))
    rep["move_mm"] = round(float(np.linalg.norm(X - U, axis=1).max() * 1000), 2)
    return X, w > 0, rep


def run(src, dst):
    G = Glb(src)
    g = G.g
    U, F, J, W, wid = skin_union(G)
    X, moved, rep = unfold(U, F)
    print("UNFOLD", rep)
    dn = _vn(X, F) - _vn(U, F)
    hb = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    ps = [p for p in g["meshes"][hb["mesh"]]["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    o = 0
    for p in ps:
        a = p["attributes"]
        P = G.get(a["POSITION"])
        n = len(P)
        w = wid[o:o + n]
        o += n
        k = moved[w]
        if not k.any():
            continue
        P2 = P.astype(float)
        P2[k] = X[w[k]]
        G.put(a["POSITION"], P2.astype(P.dtype))
        acc = g["accessors"][a["POSITION"]]
        acc["min"] = np.minimum(acc["min"], P2.min(0)).tolist()
        acc["max"] = np.maximum(acc["max"], P2.max(0)).tolist()
        if "NORMAL" in a:
            N = G.get(a["NORMAL"]).astype(float)
            N2 = N.copy()
            N2[k] = N[k] + dn[w[k]]
            N2[k] /= np.maximum(np.linalg.norm(N2[k], axis=1, keepdims=True), 1e-12)
            G.put(a["NORMAL"], N2.astype(G.get(a["NORMAL"]).dtype))
    g["asset"].setdefault("extras", {})["arm_unfold"] = {"faces": rep["faces"], "move_mm": rep.get("move_mm", 0)}
    G.save(dst)
    print("UNFOLD ->", dst)


if __name__ == "__main__":
    if os.environ.get("ARM_UNFOLD", "0") != "1":
        import shutil
        shutil.copyfile(sys.argv[1], sys.argv[2])
        print("UNFOLD off (ARM_UNFOLD=1 builds it): copied")
    else:
        run(sys.argv[1], sys.argv[2])
