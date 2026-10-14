import sys, os
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import numpy as np, heroine_seam as hs
a, b = [hs._load(p) for p in sys.argv[1:3]]
def head(js):
    mats = [m.get("name") for m in js["materials"]]
    for m in js["meshes"]:
        for p in m["primitives"]:
            if mats[p["material"]] == "skin_head": return m, p
(ma, pa), (mb, pb) = head(a[0]), head(b[0])
P = hs._read(*a, pa["attributes"]["POSITION"])
out = []
for k, (ta, tb) in enumerate(zip(pa["targets"], pb["targets"])):
    da = hs._read(*a, ta["POSITION"]); db = hs._read(*b, tb["POSITION"])
    c = np.linalg.norm(db - da, axis=1)
    if c.max() > 1e-4:
        i = c.argmax()
        out.append((c.max(), ma["extras"]["targetNames"][k], np.linalg.norm(da, axis=1).max(), P[i]))
for c, n, m, p in sorted(out, reverse=True):
    print("%-26s change max %5.1f mm (key's own max move %5.1f) at %s" % (n, c * 1000, m * 1000, np.round(p, 3)))
