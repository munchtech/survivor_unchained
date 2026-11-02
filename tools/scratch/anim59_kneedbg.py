"""Debug the kneel: per round, at a frame, the wanted vs solved right hip, knee, ankle."""
import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-59\tools\anim")
import numpy as np
from keyed import Rig
from rig import Skeleton, DATA
from clips import flare_long_cut as M
from clips.actions import _legs
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk, body="her")
I = rig.I
FR = int(sys.argv[1]) if len(sys.argv) > 1 else 30
L = M.LongCut(rig)
pel, hip, Lt, S, ankle, calf = _legs(rig)
print("thigh", round(Lt, 3), "shin", round(S, 3), "rest ankle", np.round(ankle["r"], 3))
for r in range(int(sys.argv[2]) if len(sys.argv) > 2 else 3):
    S_r, S_l, chest = L.body()
    HR = L.right(S_r, chest); HL = L.left(S_l, chest)
    clip = L.solve(HR, HL)
    pose = L.pose(FR)
    _, p = sk.fk(clip.rot, clip.pos)
    np.set_printoptions(precision=3, suppress=True)
    print("round", r, "real", p[FR, I["thigh_r"]], )
    print("   knee", p[FR, I["calf_r"]], "ankle", p[FR, I["foot_r"]], "foot_r key", np.array(pose["foot_r"]["pos"]), "pole", np.array(pose["foot_r"]["pole"]))
    print("   |hip-knee|", np.linalg.norm(p[FR, I["thigh_r"]] - p[FR, I["calf_r"]]), "|knee-ankle|", np.linalg.norm(p[FR, I["calf_r"]] - p[FR, I["foot_r"]]),
          "|hip-ankle|", np.linalg.norm(p[FR, I["thigh_r"]] - p[FR, I["foot_r"]]))
    L.hands_of(clip)
