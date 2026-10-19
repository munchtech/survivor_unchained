import json, os, sys, struct
import numpy as np
sys.path.insert(0, "tools/assets")
from heroine_lod import Gltf
from scipy.spatial import cKDTree
art = sys.argv[1]
g = Gltf(os.path.join(art, "heroine.glb"))
node = next(n for n in g.js["nodes"] if n.get("name") == "Heroine")
pos = np.vstack([a["POSITION"][0] for _, a, _ in g.prims(node["mesh"])]).astype(np.float64)
q = np.round(pos * 1e5).astype(np.int64)
S = set(map(tuple, q)); T = cKDTree(q)
for f in sorted(os.listdir(os.path.join(art, "armor_tuck"))):
    b = open(os.path.join(art, "armor_tuck", f), "rb").read()
    n = struct.unpack_from("<I", b)[0]
    rec = np.frombuffer(b, dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")], count=n, offset=4)
    for r in rec:
        k = (int(r["x"]), int(r["y"]), int(r["z"]))
        if k not in S:
            d, j = T.query(k)
            print(f, k, "tuck %.3f" % r["t"], "nearest glb point %s, %.1f units (1e-5 m)" % (q[j], d))
