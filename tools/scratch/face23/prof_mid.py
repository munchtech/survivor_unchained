import sys, numpy as np
R = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0"
sys.path.insert(0, R + "/tools/assets")
import heroine_seam as hs
js, binc = hs._load(R + "/godot/art/people/heroine.glb")
mats = js["materials"]
prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]].get("name") == "skin_head")
P = hs._read(js, binc, prim["attributes"]["POSITION"])
m = np.abs(P[:, 0]) < 0.003
for y in np.arange(1.66, 1.82, 0.005):
    s = m & (np.abs(P[:, 1] - y) < 0.0025)
    if s.any(): print(round(y, 3), round(P[s, 2].max(), 4))
