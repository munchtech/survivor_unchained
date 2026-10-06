import math
import sys
from pathlib import Path
W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np
import audit
from rig import DATA, Skeleton, qrot
sk = Skeleton.load(DATA / "heroine_skeleton.json")
d, rot, pos = audit.load(Path(__file__).parent / "out_before" / "clips" / f"{sys.argv[1]}.json", sk)
g, p = sk.fk(rot, pos)
I = sk.index
for f in (0, 1, 2, 10, 30, 60, 90):
    h = g[f, I["Head"]]
    print(f, np.round(h, 4), "fwd", np.round(qrot(h, [0, 0, 1.0]), 3), "up", np.round(qrot(h, [0, 1.0, 0]), 3))
print("keys head:", [t for t in d["tracks"] if t["bone"] == "Head"][0]["keys"][:3])
