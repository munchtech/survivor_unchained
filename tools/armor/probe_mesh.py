"""The exact install's test fixture (lane D, 16 Nov 2026): a free mesh made from heroine.glb's own skin.

    python tools/armor/probe_mesh.py [<out dir, default godot/art/armor/src/kit_probe>] [--id kit_probe]

Writes <id>.glb and piece.json (style mesh, slot top, steel): `band`, a shell OFF mm off her skin over her torso from
under her bust to her navel (her points whose weights are her pelvis and spine, y BAND), and `sternum_rigid`, a small
closed plate (W x H, THICK thick) STAND off her sternum, riding one blend. glTF axes, metres, at her rest, unskinned:
the free-mesh contract (docs/armor/PIECE_SCHEMA.md). Ship it with `python tools/armor/piece_ship.py <id>`.
"""
import hashlib
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "assets"))
BODY = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
OFF = 0.003                     # m: the band off her skin
BAND = (1.04, 1.20)             # m: navel .. under her bust (her front's profile, 16 Nov)
TORSO = ("pelvis", "spine_01", "spine_02", "spine_03")
PLATE = dict(y=1.215, w=0.030, h=0.050, stand=0.007, thick=0.002, n=(5, 7))


def band(B):
    ti = [B.names.index(n) for n in TORSO]
    keep = (B.U[:, 1] > BAND[0]) & (B.U[:, 1] < BAND[1]) & (B.W[:, ti].sum(1) > 0.6)
    F = B.F[keep[B.F].all(1)]
    used = np.unique(F)
    remap = np.full(len(B.U), -1)
    remap[used] = np.arange(len(used))
    return B.U[used] + OFF * B.N[used], remap[F]


def plate(B):
    """A plate on her sternum: a grid laid on her skin (each point at her front's closest place) STAND off, a back face
    and a front face THICK apart, closed round its edge."""
    from scipy.spatial import cKDTree
    p = PLATE
    nx, ny = p["n"]
    xs, ys = np.linspace(-p["w"] / 2, p["w"] / 2, nx), np.linspace(p["y"] - p["h"] / 2, p["y"] + p["h"] / 2, ny)
    front = B.U[:, 2] > 0.05
    kd = cKDTree(B.U[front][:, :2])
    G = np.array([[x, y] for y in ys for x in xs])
    _, j = kd.query(G, k=6)
    z = B.U[front][j][:, :, 2].max(1)
    n = B.N[front][j].mean(1)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    base = np.c_[G, z]
    back, top = base + n * p["stand"], base + n * (p["stand"] + p["thick"])
    P = np.vstack([back, top])
    m = nx * ny
    F = []
    for r in range(ny - 1):
        for c in range(nx - 1):
            a, b, d, e = r * nx + c, r * nx + c + 1, (r + 1) * nx + c, (r + 1) * nx + c + 1
            F += [(a + m, b + m, e + m), (a + m, e + m, d + m), (a, e, b), (a, d, e)]
    ring = [c for c in range(nx)] + [r * nx + nx - 1 for r in range(1, ny)] + [(ny - 1) * nx + c for c in range(nx - 2, -1, -1)] + \
           [r * nx for r in range(ny - 2, 0, -1)]
    for k in range(len(ring)):
        a, b = ring[k], ring[(k + 1) % len(ring)]
        F += [(a, b, b + m), (a, b + m, a + m)]
    return P, np.array(F)


def write_glb(path, objs, mat="steel"):
    """objs: [(name, P, F)] -> one glb, a node and mesh each, one material."""
    bin_, views, accs, meshes, nodes = b"", [], [], [], []
    for name, P, F in objs:
        for arr, ty, ct, tgt in ((np.asarray(P, np.float32), "VEC3", 5126, 34962), (np.asarray(F, np.uint32).ravel(), "SCALAR", 5125, 34963)):
            bin_ += b"\0" * (-len(bin_) % 4)
            views.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": arr.nbytes, "target": tgt})
            a = {"bufferView": len(views) - 1, "componentType": ct, "count": int(len(arr)), "type": ty}
            if ty == "VEC3":
                a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
            accs.append(a)
            bin_ += arr.tobytes()
        meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": len(accs) - 2}, "indices": len(accs) - 1, "material": 0}]})
        nodes.append({"name": name, "mesh": len(meshes) - 1})
    bin_ += b"\0" * (-len(bin_) % 4)
    js = {"asset": {"version": "2.0", "generator": "probe_mesh.py"}, "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}],
          "nodes": nodes, "meshes": meshes, "materials": [{"name": mat}], "accessors": accs, "bufferViews": views,
          "buffers": [{"byteLength": len(bin_)}]}
    j = json.dumps(js).encode()
    j += b" " * (-len(j) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(bin_))
    out += struct.pack("<II", len(j), 0x4E4F534A) + j + struct.pack("<II", len(bin_), 0x004E4942) + bin_
    open(path, "wb").write(out)


def main(argv):
    import body_follow_post as bf
    pid = argv[argv.index("--id") + 1] if "--id" in argv else "kit_probe"
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--id")]
    out = os.path.abspath(pos[0]) if pos else os.path.join(ROOT, "godot", "art", "armor", "src", pid)
    os.makedirs(out, exist_ok=True)
    B = bf.Body(BODY)
    bP, bF = band(B)
    pP, pF = plate(B)
    write_glb(os.path.join(out, pid + ".glb"), [("band", bP, bF), ("sternum_rigid", pP, pF)])
    piece = {"id": pid, "name": "Exact-install probe (torso band, sternum plate)", "slot": "top", "style": "mesh",
             "params": {"file": pid + ".glb"}, "material": "steel", "tint": None, "tier": 2, "tier_name": "riveted",
             "covers": ["top"], "hold": {"amount": 0.55, "squash": 0}, "adorn": [],
             "body_sha1": hashlib.sha1(open(BODY, "rb").read()).hexdigest()}
    json.dump(piece, open(os.path.join(out, "piece.json"), "w", encoding="utf-8"), indent=1)
    print("PROBE %s: band %d pts %d tris, plate %d pts %d tris -> %s" % (pid, len(bP), len(bF), len(pP), len(pF), out))


if __name__ == "__main__":
    main(sys.argv[1:])
