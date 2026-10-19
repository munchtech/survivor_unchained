import json, sys
import numpy as np
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
for k in sorted(set(a) | set(b)):
    if k not in a or k not in b:
        print(k, "only in", "new" if k in b else "old"); continue
    va, vb = a[k].get("v"), b[k].get("v")
    if isinstance(va, list) and isinstance(vb, list):
        A = np.array(va, float).reshape(-1, 3); B = np.array(vb, float).reshape(-1, 3)
        if A.shape != B.shape:
            print(k, "shape", A.shape, B.shape, "centroid move mm", np.round((B.mean(0) - A.mean(0)) * 1000, 1)); continue
        d = np.linalg.norm(A - B, axis=1) * 1000
        if d.max() > 0.05:
            print(k, f"max {d.max():.1f} mm, median {np.median(d):.1f} mm")
    if a[k].get("mount") != b[k].get("mount"):
        print(k, "mount changed")
