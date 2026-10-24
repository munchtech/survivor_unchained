"""Her pec fold as an arm rises (armor 16 R1, 22 October 2026).

The max judge (RJ1) on HerRaise's lift: "the underside of the raised arm meets the outer breast in a notch ... the
fold needs a morph (this bone can't make it)". Morph targets on heroine.glb's body, per side (_l, _r), driven by
HerRaise's weight (0 arm down, 1 arm well up):
  axilla_fold (on under steel cups too: the fold sits above them)
  - RIDGE: a soft ridge (RIDGE_H high, RIDGE_W wide) along the pec's outer edge, from the inner upper arm into the
    breast's upper outer part, along her posed normal;
  - HOLLOW: a shallow armpit hollow (HOLLOW_D deep, HOLLOW_R across) behind it;
  raise_crease (with the bone's lift: off under steel, as the lift is)
  - CREASE: the crease under the breast filled CREASE_FILL of the way to its smoothed surface;
  - KINK: the breast's lower edge, where its bone's weight gives way, lightly smoothed (the lift's shear).
Authored on her posed shape at full raise (tools/assets/axilla_fold_pose.json: every bone's skeleton-space pose in
cast_raise at 0.10 s with HerRaise on, from a game run with --pose-dump) and carried back to her bind shape through
the inverse of each point's blended skin matrix, so at that pose it is exactly the shape authored and in other raised
poses it rides with the skin. Her left side is authored, her right is its mirror (in bind space, x to -x). Normals
from the morphed shape's own. Positions unchanged: at 0 she is bit-identical.

Each outfit's tops and pauldrons (heroine_outfit_*.gltf) carry the same morphs, moved as the skin under them
(follow), so nothing pokes through and HerRaise drives them with her.

Idempotent: the body's morphs are skipped when the glb has them (done-mark axilla_fold), an outfit when its file is
marked axilla_fold.

    python tools/assets/axilla_fold_post.py [art dir, default godot/art/people] [--dry]
"""
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heroine_neck import _Gl  # noqa: E402
from wrap_post import skin_union  # noqa: E402
from worn_reaver_post import _sparse, _vn, _ss  # noqa: E402

POSE = os.path.join(HERE, "axilla_fold_pose.json")
# the pec's outer edge in her posed chest frame (spine_03: x her left, y up, z forward), arm to breast, metres;
# each (x, y) taken to her front surface
RIDGE_LINE = [(0.215, 0.19), (0.19, 0.14), (0.17, 0.105), (0.15, 0.08)]
RIDGE_H, RIDGE_W = 0.010, 0.036
RIDGE_TAPER = (0.2, 0.3)  # (fraction of its length eased in at the arm, out into the breast)
HOLLOW_BACK, HOLLOW_D, HOLLOW_R = 0.035, 0.004, 0.025
CREASE_FILL, CREASE_BAND = 0.5, 0.015
KINK, KINK_SMOOTH = 1.0, 8
SMOOTH = 6


def _pose(names):
    d = json.load(open(POSE))
    missing = [n for n in names if n not in d]
    if missing:
        # (her twist chain, helpers SPEC "twist_chain": a body built with it needs a pose dumped from it)
        raise SystemExit(f"axilla_fold_pose.json has no pose for {missing}: dump it again from a game run of this body "
                         "(--pose-dump, cast_raise at 0.10 s, HerRaise on)")
    T = {}
    for n in names:
        v = d[n]
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = v[0:3], v[3:6], v[6:9], v[9:12]
        T[n] = m
    return T


def _ibm(G):
    sk = G.g["skins"][0]
    return G.get(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)


def _blend(J, W, M):
    """Each point's blended skin matrix (4x4)."""
    B = np.zeros((len(J), 4, 4))
    for k in range(J.shape[1]):
        B += W[:, k, None, None] * M[J[:, k]]
    return B


def _adj(F, n):
    r = np.concatenate([F[:, 0], F[:, 1], F[:, 2], F[:, 1], F[:, 2], F[:, 0]])
    c = np.concatenate([F[:, 1], F[:, 2], F[:, 0], F[:, 0], F[:, 1], F[:, 2]])
    A = coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)).tocsr()
    A.data[:] = 1
    return A, np.maximum(np.asarray(A.sum(1)).ravel(), 1)


def _front(X, N, x, y, r=0.008):
    m = (np.hypot(X[:, 0] - x, X[:, 1] - y) < r) & (N[:, 2] > 0)
    i = np.nonzero(m)[0]
    return i[np.argmax(X[i, 2])]


def posed_chest(U, J, W, names, ibm, pose=None):
    """Her points posed (POSE, or the given {bone: 4x4}) in the posed chest frame; each point's blend; the frame."""
    T = pose or _pose(names)
    M = np.array([T[n] @ ibm[k] for k, n in enumerate(names)])
    B = _blend(J, W, M)
    X = np.einsum("nij,nj->ni", B, np.c_[U, np.ones(len(U))])[:, :3]
    C = np.linalg.inv(T["spine_03"])
    return B, X @ C[:3, :3].T + C[:3, 3], C


def morph(U, F, J, W, names, ibm, log=print):
    """The left side's bind-space deltas (n x 3), and the posed chest-frame ones with the posed shape (for checks)."""
    B, X, C = posed_chest(U, J, W, names, ibm)
    N = _vn(X, F)
    A, deg = _adj(F, len(U))
    left = U[:, 0] > 0.01
    # RIDGE: the edge's curve on her front surface, densely resampled
    P = np.array([X[_front(X, N, x, y)] for x, y in RIDGE_LINE])
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    tt = np.linspace(0, s[-1], 200)
    Q = np.c_[[np.interp(tt, s, P[:, k]) for k in range(3)]].T
    dq, iq = cKDTree(Q).query(X)
    t = tt[iq] / s[-1]
    nq = N[cKDTree(X).query(Q)[1]]
    facing = (N * nq[iq]).sum(1)
    prof = np.cos(np.clip(dq / (RIDGE_W / 2), 0, 1) * np.pi / 2) ** 2
    taper = _ss(t / RIDGE_TAPER[0]) * _ss((1 - t) / RIDGE_TAPER[1])
    w_r = prof * taper * _ss((facing - 0.2) / 0.4) * left
    # HOLLOW: behind the edge's middle, on her armpit's surface
    mid = Q[len(Q) // 2]
    want = mid + np.array([0.01, 0.0, -HOLLOW_BACK])
    hc = X[np.argmin(np.linalg.norm(X - want, axis=1) + 1.0 * (~left))]
    dh = np.linalg.norm(X - hc, axis=1)
    w_h = np.cos(np.clip(dh / HOLLOW_R, 0, 1) * np.pi / 2) ** 2 * (1 - _ss(dq / (RIDGE_W / 2))) * left
    # CREASE: under her breast, the concave band, part way to a smoothed surface
    Xs = X.copy()
    for _ in range(40):
        Xs = 0.5 * Xs + 0.5 * (A @ Xs) / deg[:, None]
    conc = (((A @ X) / deg[:, None] - X) * N).sum(1)
    wb = (W * (J == names.index("breast_l"))).sum(1)
    near_b = cKDTree(X[wb > 0.3]).query(X)[0]
    # (the fold under her breast only: below its lowest third, off the breast itself, not the cleavage)
    by = np.percentile(X[wb > 0.5, 1], 30)
    under = (X[:, 1] < by) & (X[:, 1] > -0.09) & (N[:, 2] > 0.0) & left & (X[:, 0] < 0.17) & (wb < 0.5)
    w_c = under * _ss(conc / 0.0006) * (1 - _ss((near_b - CREASE_BAND) / 0.01)) * _ss((X[:, 0] - 0.035) / 0.02)
    Dc = CREASE_FILL * (Xs - X) * w_c[:, None]
    # KINK: the breast's lower edge, where its bone's weight gives way to the ribs', sheared into a small corner as
    # the bone lifts and stretches (RJ1: "a small dark tick at the bottom centre"): there, lightly smoothed
    Xk = X.copy()
    for _ in range(KINK_SMOOTH):
        Xk = 0.5 * Xk + 0.5 * (A @ Xk) / deg[:, None]
    yb = np.median(X[wb > 0.9, 1])
    band = np.sin(np.clip(wb, 0, 1) * np.pi) * _ss((yb - X[:, 1]) / 0.02) * left * (N[:, 2] > -0.2)
    Dc = Dc + KINK * (Xk - X) * band[:, None]
    parts = {"axilla_fold": N * (RIDGE_H * w_r - HOLLOW_D * w_h)[:, None], "raise_crease": Dc}
    out = {}
    for key, Dp in parts.items():
        for _ in range(SMOOTH):
            Dp = 0.5 * Dp + 0.5 * (A @ Dp) / deg[:, None]
        Dp[~left] = 0
        # back to her bind shape: chest frame to skeleton space to each point's own bind (inverse blended linear part)
        Ds = Dp @ np.linalg.inv(C[:3, :3]).T
        Db = np.einsum("nij,nj->ni", np.linalg.inv(B[:, :3, :3]), Ds)
        Db[np.linalg.norm(Db, axis=1) < 1e-6] = 0
        dn = (Dp * N).sum(1)
        log("AXILLA_FOLD %s left: %d points moved; out %.1f mm, in %.1f mm; most %.1f mm" % (
            key, int((np.linalg.norm(Db, axis=1) > 0).sum()), 1000 * dn.max(), -1000 * dn.min(),
            1000 * np.linalg.norm(Dp, axis=1).max()))
        out[key] = (Db, Dp)
    return out, X, N


def mirror(U, D):
    """D for the other side: each point's value read at its mirror image (x to -x), x flipped."""
    dq, jq = cKDTree(U).query(U * [-1, 1, 1], k=4)
    wq = 1 / np.maximum(dq, 1e-5) ** 2
    M = (D[jq] * wq[..., None]).sum(1) / wq.sum(1)[:, None] * [-1, 1, 1]
    M[U[:, 0] > -0.01] = 0
    M[np.linalg.norm(M, axis=1) < 1e-6] = 0
    return M


# (not the warden: its cups are steel, which holds; the fold sits above them and the skin stays under them)
OUTFITS = ("arcanist", "ranger", "reaver")
FOLLOW_NEAR, FOLLOW_FAR = 0.015, 0.03
FOLLOW_K, FOLLOW_POW = 3, 4


def follow(path, U, shapes, mark="axilla_fold", parts=(".top.", ".pauldrons."), near=FOLLOW_NEAR, far=FOLLOW_FAR):
    """An outfit's tops (and pauldrons) carry the same two morphs, each point moved as her skin under it moves
    (her nearest points' deltas, inverse-distance weighted; whole within FOLLOW_NEAR of her, none past FOLLOW_FAR), so
    the gap between them holds and nothing pokes through. Done-mark axilla_fold on the file."""
    G = _Gl(path)
    g = G.g
    if mark in ((g.get("asset") or {}).get("extras") or {}):
        print("%s: %s follows already" % (mark.upper(), os.path.basename(path)))
        return
    tree = cKDTree(U)
    binb = bytearray(G.buf)
    moved = 0
    for n in g["nodes"]:
        if "mesh" not in n or not any(k in n.get("name", "") for k in parts):
            continue
        mesh = g["meshes"][n["mesh"]]
        for p in mesh["primitives"]:
            P = G.get(p["attributes"]["POSITION"]).astype(float)
            d, j = tree.query(P, k=FOLLOW_K)
            w = 1 / np.maximum(d, 1e-4) ** FOLLOW_POW
            w /= w.sum(1, keepdims=True)
            fade = 1 - _ss((d[:, 0] - near) / (far - near))
            Ff = G.get(p["indices"]).reshape(-1, 3).astype(int) if "indices" in p else np.arange(len(P)).reshape(-1, 3)
            for _, D in shapes:
                Dp = (D[j] * w[..., None]).sum(1) * fade[:, None]
                Dp[np.linalg.norm(Dp, axis=1) < 1e-6] = 0
                dN = _vn(P + Dp, Ff) - _vn(P, Ff)
                dN[np.abs(dN).max(1) < 1e-5] = 0
                ip = np.nonzero(np.abs(Dp).max(1) > 0)[0]
                inn = np.nonzero(np.abs(dN).max(1) > 0)[0]
                t = {"POSITION": _sparse(g, binb, len(P), ip, Dp[ip])}
                if "NORMAL" in p["attributes"]:
                    t["NORMAL"] = _sparse(g, binb, len(P), inn, dN[inn])
                p.setdefault("targets", []).append(t)
                moved += len(ip)
        mesh.setdefault("extras", {}).setdefault("targetNames", []).extend([nm for nm, _ in shapes])
        k = len(shapes)
        mesh["weights"] = list(mesh.get("weights", [0] * (len(mesh["primitives"][0]["targets"]) - k))) + [0] * k
    g.setdefault("asset", {}).setdefault("extras", {})[mark] = {"follow_mm": [near * 1000, far * 1000]}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    G.buf = binb
    G.save()
    print("%s: %s follows (%d point moves)" % (mark.upper(), os.path.basename(path), moved))


def main(a):
    art = next((x for x in a if not x.startswith("--")), "godot/art/people")
    path = os.path.join(art, "heroine.glb")
    G = _Gl(path)
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    U, F, J, W, wid = skin_union(G)
    out, _, _ = morph(U, F, J, W, G.names(), _ibm(G))
    shapes = []
    for key, (Dl, _) in out.items():
        shapes += [(key + "_l", Dl), (key + "_r", mirror(U, Dl))]
    if "--dry" in a:
        return
    for o in OUTFITS:
        op = os.path.join(art, f"heroine_outfit_{o}.gltf")
        if os.path.exists(op):
            follow(op, U, shapes)
    if "axilla_fold_l" in (mesh.get("extras") or {}).get("targetNames", []):
        print("AXILLA_FOLD: the morphs are on the glb already")
        return
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    for name, D in shapes:
        dN = _vn(U + D, F) - _vn(U, F)
        o = 0
        for p in prims:
            n = g["accessors"][p["attributes"]["POSITION"]]["count"]
            w = wid[o:o + n]
            Dp = D[w]
            Ns = G.get(p["attributes"]["NORMAL"]).astype(float)
            Nn = Ns + dN[w]
            Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
            dNp = np.where((np.abs(dN[w]).max(1) > 1e-5)[:, None], Nn - Ns, 0)
            ip = np.nonzero(np.abs(Dp).max(1) > 0)[0]
            inn = np.nonzero(np.abs(dNp).max(1) > 0)[0]
            p.setdefault("targets", []).append({
                "POSITION": _sparse(g, binb, n, ip, Dp[ip]),
                "NORMAL": _sparse(g, binb, n, inn, dNp[inn])})
            print("AXILLA_FOLD %s %s: %d positions, %d normals" % (
                name, g["materials"][p["material"]]["name"], len(ip), len(inn)))
            o += n
        mesh.setdefault("extras", {}).setdefault("targetNames", []).append(name)
        mesh["weights"] = list(mesh.get("weights", [])) + [0]
    g.setdefault("asset", {}).setdefault("extras", {})["axilla_fold"] = {
        "ridge_mm": RIDGE_H * 1000, "hollow_mm": HOLLOW_D * 1000, "crease_fill": CREASE_FILL}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(path, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("AXILLA_FOLD: written", path)


if __name__ == "__main__":
    main(sys.argv[1:])
