"""strand.py: how thick each style's tail is about its chain at rest: per link 3-7, the hair vertices nearest that link
(by projection), their distance from it (cm): median, 90th percentile, max."""
import sys; sys.path[:0] = ["../sv11"]
from pads import load, verts
import json, numpy as np
P = "../../../../godot/art/people/"
for st in ("ponytail", "braid"):
    pts = np.array(json.load(open(P + "heroine_hair_%s.chain.json" % st))["points"]); g, a = load("heroine_hair_%s.gltf" % st)
    V = np.vstack([v for n, v in verts(g, a)]); out = []
    for i in range(3, 8):
        p, q = pts[i - 1], pts[i]; d = q - p; t = (V - p) @ d / (d @ d); s = (t >= 0) & (t <= 1)
        r = np.linalg.norm(V[s] - (p + np.outer(t[s], d)), axis=1) * 100; r = r[r < 8]
        out.append("seg%d %.1f/%.1f/%.1f" % (i, np.median(r), np.percentile(r, 90), r.max()))
    print(st, " ".join(out))
