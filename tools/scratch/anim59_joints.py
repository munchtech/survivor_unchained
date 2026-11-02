"""Joint places (her space, m) of a clip's frames, staged as the game plays it (--raw: as written).
    python ../scratch/anim59_joints.py flare_long_cut 3,5,7 [--raw]   (from tools/anim)"""
import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-59\tools\anim")
import numpy as np
import staged
if "--raw" in sys.argv:
    staged.set_from_argv(["--raw"])
from skin import Body
b = Body.heroine(outfit=None)
c = b.clip(sys.argv[1])
g, p = b.sk.fk(c.rot, c.pos)
I = b.sk.index
J = ["pelvis", "spine_03", "thigh_r", "thigh_l", "upperarm_r", "lowerarm_r", "hand_r", "upperarm_l", "lowerarm_l", "hand_l"]
np.set_printoptions(precision=2, suppress=True)
for f in [int(x) for x in sys.argv[2].split(",")]:
    print(f"f{f}: " + "  ".join(f"{j} {np.round(p[f, I[j]], 2)}" for j in J))
