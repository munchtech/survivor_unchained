"""Joint positions of a crowd.KEYED clip at given frames: python joints.py name sex f1 f2 ..."""
import sys
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017")
sys.path.insert(0, str(WT / "tools" / "anim"))
import crowd
from keyed import Rig
from rig import DATA, Skeleton
name, sex = sys.argv[1], sys.argv[2]
sk = Skeleton.load(DATA / ("folk_female_skeleton.json" if sex == "f" else "folk_male_skeleton.json"))
clip = crowd.KEYED[name](f"{sex}_{name}", Rig(sk))
g, p = sk.fk(clip.rot, clip.pos)
names = ("pelvis", "Head", "upperarm_l", "upperarm_r", "hand_l", "hand_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_r")
for f in map(int, sys.argv[3:]):
    print(f, "  ".join(f"{n}=({p[f, sk.index[n]][0]:+.2f},{p[f, sk.index[n]][1]:.2f},{p[f, sk.index[n]][2]:+.2f})" for n in names))
