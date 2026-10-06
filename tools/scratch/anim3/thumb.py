import sys
import numpy as np
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70")
sys.path.insert(0, str(WT / "tools" / "anim"))
from keyed import Rig
from rig import DATA, Skeleton
sk = Skeleton.load(DATA / "folk_male_skeleton.json")
rig = Rig(sk)
I = sk.index
for op in (0, 0.6, 1.0, 1.3):
    f = {"curl": 1.0, "thumb": 0.9, "cascade": 0.05, "oppose": op}
    loc, pos = rig.solve({"fingers_l": f, "fingers_r": f})
    g, p = sk.fk(loc[None], pos[None])
    out = []
    for s in "lr":
        tip = p[0, I[f"thumb_04_leaf_{s}"]]
        mid = p[0, I[f"middle_02_{s}"]]
        idx = p[0, I[f"index_02_{s}"]]
        palm = (p[0, I[f"hand_{s}"]] + p[0, I[f"middle_01_{s}"]]) / 2
        out.append(f"{s}: tip-index2 {np.linalg.norm(tip - idx):.3f} tip-mid2 {np.linalg.norm(tip - mid):.3f} tip-palm {np.linalg.norm(tip - palm):.3f}")
    print(op, " | ".join(out))
