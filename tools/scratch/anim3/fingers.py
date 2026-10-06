import json, sys, math
import numpy as np
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70")
sys.path.insert(0, str(WT / "tools" / "anim"))
from rig import DATA, Skeleton, qinv, qmul
sk = Skeleton.load(DATA / "folk_male_skeleton.json")
d = json.loads((WT / "tools/anim/out/folk" / f"{sys.argv[1]}.json").read_text())
fr = int(sys.argv[2])
tr = {t["bone"]: t for t in d["tracks"] if t["type"] == "rot"}
for n in ("hand_l", "index_01_l", "index_02_l", "index_03_l", "thumb_01_l", "thumb_02_l", "middle_01_l"):
    if n not in tr:
        print(n, "rest (no track)")
        continue
    q = np.array(tr[n]["keys"][fr])
    rel = qmul(qinv(sk.rest_rot[sk.index[n]]), q)
    ang = 2 * math.degrees(math.acos(min(1, abs(rel[3]))))
    print(n, f"{ang:.0f} deg from rest")
