"""How a hair glTF's cards are ordered in its index buffer: the mean depth (COLOR_0.r,
1 outermost) and height of each tenth of its triangles, in drawing order.
    python hair_order.py GLTF [PRIMITIVE_MATERIAL]"""
import json
import os
import sys

import numpy as np

path = sys.argv[1]
want = sys.argv[2] if len(sys.argv) > 2 else "hair"
g = json.load(open(path))
binp = os.path.join(os.path.dirname(path), g["buffers"][0]["uri"])
buf = open(binp, "rb").read()
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def acc(i):
    a = g["accessors"][i]
    bv = g["bufferViews"][a["bufferView"]]
    dt = np.dtype(CT[a["componentType"]])
    n = NC[a["type"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", dt.itemsize * n)
    raw = np.frombuffer(buf, dtype=np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * n, offset=off)
    out = np.lib.stride_tricks.as_strided(raw, shape=(a["count"], dt.itemsize * n), strides=(stride, 1)).copy()
    v = out.view(dt).reshape(a["count"], n)
    if a.get("normalized") and dt != np.float32:
        v = v.astype(np.float32) / np.iinfo(dt).max
    return v.astype(np.float32)


mats = [m.get("name") for m in g["materials"]]
for m in g["meshes"]:
    for p in m["primitives"]:
        if mats[p["material"]] != want:
            continue
        idx = acc(p["indices"]).astype(np.int64).reshape(-1, 3)
        col = acc(p["attributes"]["COLOR_0"])
        pos = acc(p["attributes"]["POSITION"])
        d = col[idx, 0].mean(axis=1)
        y = pos[idx, 1].mean(axis=1)
        a = col[idx, 3].mean(axis=1) if col.shape[1] > 3 else np.ones(len(idx))
        print(f"{path}: {len(idx)} triangles; depth min {d.min():.2f} max {d.max():.2f}")
        for k, part in enumerate(np.array_split(np.arange(len(idx)), 10)):
            print(f"  tenth {k}: depth mean {d[part].mean():.3f}  (10%..90%: {np.percentile(d[part], 10):.2f}..{np.percentile(d[part], 90):.2f})  height {y[part].mean():.3f}  vertex alpha {a[part].mean():.2f}")
        # How often drawing order goes outward-then-inward (a later card lying deeper than an earlier one)
        runs = np.diff(d[::2]) < -0.05
        print(f"  steps inward by more than 0.05 (in card pairs): {runs.mean() * 100:.1f}%")
