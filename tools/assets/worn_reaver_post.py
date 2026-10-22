"""Her body while the reaver's top is worn (armor 15 w1, 22 October 2026).

The owner: "reaver needs underboob, its a defining part of its outfit"; the judge on the bare underside: "perfect
half-spheres ... rigid spheres ... make the underside heavier and more teardrop, with less sideways bulge; a soft
roll of flesh at its lower edge". The coordinator: the soft, supported read comes from the breast shape under it,
subtle, and only while the reaver's top is worn. Two things on heroine.glb:

  1. the reaver's channel of her vertex colours (COLOR_0 .b, People.OutfitChannels) rebuilt as the largest of the
     reaver's slot tuck records (armor_tuck/reaver.*.bin), on her body and its back graft: the plain calling then
     tucks her as the pieces path does. Replaced, not max-combined: the channel's top values were the old band's
     (1.378-1.468 m), which the wrap no longer covers; the other slots' values already equal their records (within
     8 bits), so for them nothing changes.
  2. a morph target, worn_reaver, on both of the body's primitives (People.WornShape sets it to 1 under the reaver's
     top, in both the plain calling and the pieces path): left = right, zero at its borders, nothing under the band:
       - ROLL: a soft swell along her normal just below the wrap's real lower edge (reaver.top's darkleather),
         peaking ROLL_PEAK below it and gone by ROLL_END, on her breasts' fronts only (sternum and ribs 0);
       - LOWER POLE: the underside's middle a little lower and fuller (POLE_DOWN down, POLE_OUT out), the fold kept
         (0 at her ribs, eased in over FOLD_EASE), fading out toward the band;
       - OUTER SIDE: the outer curve below the band in by SIDE_IN (the "sideways ball");
     normal deltas from the morphed shape's own normals. Positions unchanged: at 0 she is bit-identical.

Idempotent: the channel is a pure function of the records; the morph is skipped when the glb already has it
(done-mark worn_reaver).

    python tools/assets/worn_reaver_post.py [art dir, default godot/art/people] [--dry]
"""
import glob
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heroine_neck import _Gl, _mark  # noqa: E402
from wrap_post import skin_union  # noqa: E402

CH = 2  # (People.OutfitChannels: warden, arcanist, reaver, ranger)
ROLL, ROLL_PEAK, ROLL_END = 0.0015, 0.004, 0.010
POLE_DOWN, POLE_OUT, FOLD_EASE = 0.0025, 0.0008, 0.010
SIDE_IN = 0.004
STERNUM = (0.012, 0.028)  # (|x|: 0 inside, full outside)
SMOOTH = 12


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _vn(X, F):
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    n = np.zeros_like(X)
    for k in range(3):
        np.add.at(n, F[:, k], q)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def _records(art):
    at = {}
    for p in sorted(glob.glob(os.path.join(art, "armor_tuck", "reaver.*.bin"))):
        d = open(p, "rb").read()
        n = struct.unpack("<I", d[:4])[0]
        r = np.frombuffer(d[4:4 + 16 * n], dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
        for x, y, z, t in zip(r["x"], r["y"], r["z"], r["t"]):
            k = (int(x), int(y), int(z))
            at[k] = max(at.get(k, 0.0), float(t))
    return at


def channel(G, prims, art):
    at = _records(art)
    for p in prims:
        ai = p["attributes"]["COLOR_0"]
        C = G.get(ai)
        P = G.get(p["attributes"]["POSITION"])
        K = np.round(P.astype(np.float64) * 1e5).astype(np.int64)
        t = np.array([at.get(tuple(k), 0.0) for k in K])
        new = np.round(np.round(np.clip(t, 0, 1) * 255) / 255 * 65535).astype(np.uint16)
        # (kept where it already holds the value to 8 bits: only the top's region changes)
        new = np.where(np.abs(new.astype(int) - C[:, CH]) <= 65535 / 255 + 1, C[:, CH], new).astype(np.uint16)
        print("WORN_REAVER channel %s: %d marked (was %d), %d changed" % (
            G.g["materials"][p["material"]]["name"], int((new > 0).sum()), int((C[:, CH] > 0).sum()),
            int((new != C[:, CH]).sum())))
        C[:, CH] = new
        G.put(ai, C)


def edge(art):
    """The wrap's lower edge: (points along it, 1 mm apart, left = right)."""
    O = _Gl(os.path.join(art, "heroine_outfit_reaver.gltf"))
    n = [x for x in O.g["nodes"] if x.get("name") == "reaver.top.darkleather"][0]
    P = np.vstack([O.get(p["attributes"]["POSITION"]) for p in O.g["meshes"][n["mesh"]]["primitives"]]).astype(float)
    P = np.vstack([P, P * [-1, 1, 1]])  # (left = right)
    c = np.array([0.0, (P[:, 2].min() + P[:, 2].max()) / 2])
    th = np.arctan2(P[:, 0] - c[0], P[:, 2] - c[1])
    nb = 360
    b = np.floor((th + np.pi) / (2 * np.pi) * nb).astype(int) % nb
    E = []
    for i in range(nb):
        m = np.nonzero(b == i)[0]
        if len(m):
            E.append(P[m[np.argmin(P[m, 1])]])
    E = np.array(E)
    # (resampled densely, closed)
    E2 = np.vstack([E, E[:1]])
    seg = np.linalg.norm(np.diff(E2, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    q = np.arange(0, s[-1], 0.001)
    out = np.c_[[np.interp(q, s, E2[:, k]) for k in range(3)]].T
    print("WORN_REAVER edge: %d points, front y %.4f, min %.4f max %.4f" % (
        len(out), out[np.argmax(out[:, 2]), 1], out[:, 1].min(), out[:, 1].max()))
    return out, c


def morph(U, F, N, J, W, names, E, c):
    ky = cKDTree(E)
    de, ie = ky.query(U)
    # (below the edge: her point under the edge's nearest point)
    below = U[:, 1] < E[ie, 1] - 1e-4
    d_e = np.where(below, de, -de)
    ax = np.abs(U[:, 0])
    # her breasts: their bones' weights, left = right
    bl, br = names.index("breast_l"), names.index("breast_r")
    wb = (W * ((J == bl) | (J == br))).sum(1)
    _, im = cKDTree(U * [-1, 1, 1]).query(U)
    wb = np.maximum(wb, wb[im])
    mb = _ss((wb - 0.08) / 0.4)
    front = (U[:, 2] > 0.0)
    stern = _ss((ax - STERNUM[0]) / (STERNUM[1] - STERNUM[0]))
    # her ribs under the fold (facing forward or up, below the breasts' middle, behind their front)
    rib = (U[:, 1] < 1.35) & (N[:, 1] > -0.2) & (U[:, 2] < 0.14) & front
    d_f = cKDTree(U[rib]).query(U)[0]
    ef = _ss(d_f / FOLD_EASE)
    # ROLL
    r1 = _ss(d_e / ROLL_PEAK) * (1 - _ss((d_e - ROLL_PEAK) / (ROLL_END - ROLL_PEAK)))
    w_roll = np.where(below, r1, 0) * mb * stern * front
    # LOWER POLE
    w_lp = _ss((-N[:, 1] - 0.15) / 0.45) * ef * mb * stern * _ss(d_e / 0.006) * below * front
    # OUTER SIDE
    nl = N[:, 0] * np.sign(U[:, 0])
    w_sd = _ss((nl - 0.3) / 0.4) * _ss(d_f / 0.008) * mb * _ss(d_e / 0.006) * below
    D = N * (ROLL * w_roll + POLE_OUT * w_lp - SIDE_IN * w_sd)[:, None]
    D[:, 1] -= POLE_DOWN * w_lp
    # smooth falloff (umbrella over her mesh), then the borders held at 0
    nbr = [[] for _ in range(len(U))]
    for a, b_ in ((0, 1), (1, 2), (2, 0)):
        for i, j in zip(F[:, a], F[:, b_]):
            nbr[i].append(j)
            nbr[j].append(i)
    rows = np.repeat(np.arange(len(U)), [len(x) for x in nbr])
    cols = np.concatenate([np.array(x, int) for x in nbr])
    from scipy.sparse import coo_matrix
    A = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(U), len(U))).tocsr()
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    for _ in range(SMOOTH):
        D = 0.5 * D + 0.5 * (A @ D) / deg[:, None]
    hold = _ss(d_e / 0.003) * stern * (~rib) * _ss((mb - 0.0) / 0.15)
    # left = right: the field averaged with its own mirror image (her mesh is not mirrored point for point: the
    # mirror's value read off its nearest points, inverse-distance weighted), twice
    tree = cKDTree(U)

    def mir(X):
        dq, jq = tree.query(U * [-1, 1, 1], k=6)
        wq = 1 / np.maximum(dq, 1e-5) ** 2
        return (X[jq] * wq[..., None]).sum(1) / wq.sum(1)[:, None] * [-1, 1, 1]
    hold = np.minimum(hold, mir(np.c_[hold, hold, hold])[:, 1])
    D *= hold[:, None]
    for _ in range(3):
        D = 0.5 * (D + mir(D))
    D[(hold <= 0) | (np.linalg.norm(D, axis=1) < 1e-6)] = 0
    asym = np.linalg.norm(D - mir(D), axis=1)
    unp = np.zeros(len(U), bool)
    ia = np.argmax(asym)
    print("WORN_REAVER L=R p99 %.3f mm, p95 %.3f mm, mean over moved %.3f" % (1000 * np.percentile(asym[asym > 0], 99), 1000 * np.percentile(asym[asym > 0], 95), 1000 * asym[asym > 0].mean()))
    print("WORN_REAVER worst L=R at", U[ia].round(4), "D", (1000 * D[ia]).round(3), "mirror", (1000 * mir(D)[ia]).round(3))
    print("WORN_REAVER morph: %d points moved; roll %.2f mm, down %.2f, side in %.2f; most %.2f mm; L=R max %.4f mm "
          "(%d)" % (
              int((np.linalg.norm(D, axis=1) > 0).sum()), 1000 * (np.linalg.norm(D, axis=1) * (w_roll > 0.5)).max(),
              -1000 * D[:, 1].min(), 1000 * (-(D * N).sum(1)).max(), 1000 * np.linalg.norm(D, axis=1).max(),
              1000 * asym.max(), int(unp.sum())))
    return D, rib


def _append(g, binb, data, target=None):
    while len(binb) % 4:
        binb.append(0)
    bv = {"buffer": 0, "byteOffset": len(binb), "byteLength": len(data)}
    if target:
        bv["target"] = target
    binb.extend(data)
    g["bufferViews"].append(bv)
    return len(g["bufferViews"]) - 1


def _sparse(g, binb, n, idx, val):
    if not len(idx):
        # (a sparse accessor holds one entry at least: her first point, unmoved)
        idx, val = np.zeros(1, int), np.zeros((1, 3))
    iv = _append(g, binb, idx.astype("<u4").tobytes())
    vv = _append(g, binb, val.astype("<f4").tobytes())
    a = {"componentType": 5126, "count": int(n), "type": "VEC3",
         "sparse": {"count": int(len(idx)), "indices": {"bufferView": iv, "componentType": 5125},
                    "values": {"bufferView": vv}}}
    if len(idx):
        a["min"] = [float(x) for x in np.minimum(val.min(0), 0)]
        a["max"] = [float(x) for x in np.maximum(val.max(0), 0)]
    else:
        a["min"], a["max"] = [0.0] * 3, [0.0] * 3
    g["accessors"].append(a)
    return len(g["accessors"]) - 1


def main(a):
    art = next((x for x in a if not x.startswith("--")), "godot/art/people")
    path = os.path.join(art, "heroine.glb")
    G = _Gl(path)
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    channel(G, prims, art)
    has = "worn_reaver" in (mesh.get("extras") or {}).get("targetNames", [])
    U, F, J, W, wid = skin_union(G)
    if has:
        print("WORN_REAVER: the morph is on the glb already")
        D = None
    else:
        N0 = np.vstack([G.get(p["attributes"]["NORMAL"]) for p in prims]).astype(float)
        Nu = np.zeros_like(U)
        Nu[wid] = N0
        Nu /= np.maximum(np.linalg.norm(Nu, axis=1, keepdims=True), 1e-12)
        E, c = edge(art)
        D, _ = morph(U, F, Nu, J, W, G.names(), E, c)
        dN = _vn(U + D, F) - _vn(U, F)
    if "--dry" in a:
        return
    # (positions untouched; the colour channel written in place; the morph's sparse accessors appended)
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    if D is not None:
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
            print("WORN_REAVER %s: %d positions, %d normals in the morph" % (
                g["materials"][p["material"]]["name"], len(ip), len(inn)))
            o += n
        mesh.setdefault("extras", {}).setdefault("targetNames", []).append("worn_reaver")
        mesh["weights"] = list(mesh.get("weights", [])) + [0]
        g.setdefault("asset", {}).setdefault("extras", {})["worn_reaver"] = {
            "roll_mm": ROLL * 1000, "pole_down_mm": POLE_DOWN * 1000, "side_in_mm": SIDE_IN * 1000}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(path, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("WORN_REAVER: written", path)


if __name__ == "__main__":
    main(sys.argv[1:])
