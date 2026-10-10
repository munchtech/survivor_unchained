"""Coincident points (seams) in a built body: same joints and weights but in
another order (the GPU's sums then round apart: pinholes), or different weights."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "anim"))
import numpy as np  # noqa: E402
from skin import Gltf  # noqa: E402

for path in sys.argv[1:]:
    g = Gltf(Path(path))
    for n in g.js["nodes"]:
        if n.get("name") != "Heroine" or "mesh" not in n:
            continue
        for pr in g.js["meshes"][n["mesh"]]["primitives"]:
            a = pr["attributes"]
            P = g.accessor(a["POSITION"]).astype(float)
            J = g.accessor(a["JOINTS_0"]).astype(int)
            W = g.accessor(a["WEIGHTS_0"]).astype(float)
            key = np.round(P / 1e-6).astype(np.int64)
            _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
            inv = inv.ravel()
            dup = np.nonzero(cnt[inv] > 1)[0]
            first = {}
            same = order = diff = 0
            for v in dup:
                k = inv[v]
                if k not in first:
                    first[k] = v
                    continue
                u = first[k]
                if np.array_equal(J[u], J[v]) and np.array_equal(W[u], W[v]):
                    same += 1
                else:
                    su = sorted(zip(J[u], W[u])); sv = sorted(zip(J[v], W[v]))
                    du = {j: w for j, w in su if w > 0}; dv = {j: w for j, w in sv if w > 0}
                    if du == dv:
                        order += 1
                    else:
                        diff += 1
            print(f"{Path(path).name}: {len(dup)} seam points; pairs identical {same}, same weights in another order {order}, different weights {diff}")
