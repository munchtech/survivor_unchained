"""Frame-to-frame turn of chosen bones in a built clip (degrees), to find
jitter: python jitter.py clip [bones...] [--hero] [--before]"""
import math
import sys
from pathlib import Path

W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np  # noqa: E402
import audit  # noqa: E402
from rig import DATA, Skeleton  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
name, bones = args[0], args[1:] or ["pelvis", "spine_03", "Head", "lowerarm_r", "hand_r", "hand_l"]
hero = "--hero" in sys.argv
sk = Skeleton.load(DATA / ("hero_skeleton.json" if hero else "heroine_skeleton.json"))
base = Path(__file__).parent / "out_before" if "--before" in sys.argv else W / "out"
d, rot, pos = audit.load(base / ("hero" if hero else "clips") / f"{name}.json", sk)
g, p = sk.fk(rot, pos)
I = sk.index
print("frame " + " ".join(f"{b:>10s}" for b in bones))
for f in range(1, rot.shape[0]):
    row = []
    for b in bones:
        q0, q1 = g[f - 1, I[b]], g[f, I[b]]
        row.append(math.degrees(2 * math.acos(min(1.0, abs(float(np.dot(q0, q1)))))))
    print(f"{f:5d} " + " ".join(f"{x:10.1f}" for x in row))
