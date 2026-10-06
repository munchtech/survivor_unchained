"""Where a retargeted take's body is, frame by frame: python take_info.py prompt take [warp a,b,d ...] [place]"""
import sys
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274")
sys.path.insert(0, str(WT / "tools" / "anim"))
from clips.generated import make
from keyed import Rig
from rig import DATA, Skeleton

prompt, take = sys.argv[1], sys.argv[2]
warp = [tuple(float(x) for x in w.split(",")) for w in sys.argv[3:] if "," in w]
place = next((a for a in sys.argv[3:] if a in ("keep", "pin", "line")), "keep")
sk = Skeleton.load(DATA / "folk_male_skeleton.json")
rig = Rig(sk)
c = make(rig, "x", "kimodo", f"{prompt}_{take}.bvh", warp_=warp or None, place=place)
g, p = sk.fk(c.rot, c.pos)
I = sk.index
print(c.frames, "frames", round(c.length, 2), "s")
for f in list(range(0, c.frames, 15)) + [c.frames - 1]:
    row = []
    for n in ("pelvis", "Head", "hand_l", "hand_r", "foot_l", "foot_r"):
        v = p[f, I[n]]
        row.append(f"{n}=({v[0]:+.2f},{v[1]:.2f},{v[2]:+.2f})")
    print(f"{f:4d} {f/30:5.2f}s " + " ".join(row))
