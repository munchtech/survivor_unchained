"""The hair styles' skinning: per style, vertices, the bones used, influences per vertex, and how
the chain (UV2) and sway weights fall on the bones (what moving the sway onto bones must keep)."""
import json
import os
import sys

import numpy as np

D = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a20bdef993e00f26b\godot\art\people"
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def acc(g, bins, i):
    a = g["accessors"][i]
    v = g["bufferViews"][a["bufferView"]]
    b = bins[v["buffer"]]
    n, c = a["count"], NC[a["type"]]
    dt = np.dtype(CT[a["componentType"]])
    off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = v.get("byteStride", 0) or dt.itemsize * c
    raw = np.frombuffer(b, dtype=np.uint8, count=stride * (n - 1) + dt.itemsize * c, offset=off)
    out = np.lib.stride_tricks.as_strided(raw, shape=(n, c * dt.itemsize), strides=(stride, 1)).copy()
    arr = out.view(dt).reshape(n, c)
    if a.get("normalized"):
        arr = arr.astype(np.float32) / np.iinfo(dt).max
    return arr


for style in sys.argv[1:] or ["bob", "pixie", "long", "braid"]:
    p = os.path.join(D, f"heroine_hair_{style}.gltf")
    if not os.path.exists(p):
        print(style, "missing")
        continue
    g = json.load(open(p, encoding="utf-8"))
    bins = [open(os.path.join(D, b["uri"]), "rb").read() for b in g["buffers"]]
    skin = g["skins"][0] if g.get("skins") else None
    names = [g["nodes"][j]["name"] for j in skin["joints"]] if skin else []
    print(f"== {style}: {len(g['meshes'])} meshes, skin joints {len(names)}")
    for m in g["meshes"]:
        for pr in m["primitives"]:
            at = pr["attributes"]
            mat = g["materials"][pr["material"]]["name"] if "material" in pr else "?"
            n = g["accessors"][at["POSITION"]]["count"]
            J = acc(g, bins, at["JOINTS_0"]) if "JOINTS_0" in at else None
            W = acc(g, bins, at["WEIGHTS_0"]).astype(np.float32) if "WEIGHTS_0" in at else None
            uv2 = acc(g, bins, at["TEXCOORD_1"]) if "TEXCOORD_1" in at else None
            line = f"  {m.get('name', '?')}/{mat}: {n} verts, attrs {sorted(at)}"
            print(line)
            if J is None:
                continue
            k = (W > 1e-4).sum(1)
            print(f"    influences per vertex: " + ", ".join(f"{i}:{(k == i).sum()}" for i in range(1, 5) if (k == i).any()))
            used = {}
            for j in range(4):
                for b, w in zip(J[:, j], W[:, j]):
                    if w > 1e-4:
                        used[names[b]] = used.get(names[b], 0) + 1
            print("    bones: " + ", ".join(f"{b} {c}" for b, c in sorted(used.items(), key=lambda t: -t[1])))
            if uv2 is not None:
                on = uv2[:, 1] > 0
                print(f"    chain-moved (UV2.y > 0): {on.sum()} verts; of those, influences " +
                      ", ".join(f"{i}:{(k[on] == i).sum()}" for i in range(1, 5) if (k[on] == i).any()))
