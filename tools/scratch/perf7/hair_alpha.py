"""How much of her hair is solid: the strands atlas's alpha and the cards' vertex alpha.
    python hair_alpha.py PEOPLE_DIR STYLE"""
import json
import os
import sys

import numpy as np
from PIL import Image

D, style = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(os.path.join(D, "head_tex", "hair_strands.png")))
print("atlas", a.shape, a.dtype)
if a.shape[2] == 4:
    al = a[..., 3].astype(float) / 255
    print("  atlas alpha >= " + ", ".join(f"{t}: {(al >= t).mean() * 100:.1f}%" for t in (0.01, 0.1, 0.5, 0.9, 0.99)))
    print("  of the texels over 0.01: >= " + ", ".join(f"{t}: {(al[al > 0.01] >= t).mean() * 100:.1f}%" for t in (0.5, 0.9, 0.99)))
p = os.path.join(D, f"heroine_hair_{style}.gltf")
g = json.load(open(p))
buf = open(os.path.join(D, g["buffers"][0]["uri"]), "rb").read()
mats = [m.get("name") for m in g["materials"]]
for prim in g["meshes"][0]["primitives"]:
    if mats[prim["material"]] != "hair":
        continue
    acc = g["accessors"][prim["attributes"]["COLOR_0"]]
    bv = g["bufferViews"][acc["bufferView"]]
    ct = {5126: np.float32, 5123: np.uint16, 5121: np.uint8}[acc["componentType"]]
    n = {"VEC4": 4, "VEC3": 3}[acc["type"]]
    isz = np.dtype(ct).itemsize
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride", isz * n)
    raw = np.frombuffer(buf, np.uint8, count=stride * (acc["count"] - 1) + isz * n, offset=off)
    v = np.lib.stride_tricks.as_strided(raw, (acc["count"], isz * n), (stride, 1)).copy().view(ct).reshape(acc["count"], n).astype(float)
    if ct != np.float32:
        v /= np.iinfo(ct).max
    va = v[:, 3]
    print(f"vertex alpha: >= 0.99 {(va >= 0.99).mean() * 100:.1f}%, >= 0.9 {(va >= 0.9).mean() * 100:.1f}%, < 0.5 {(va < 0.5).mean() * 100:.1f}%")
