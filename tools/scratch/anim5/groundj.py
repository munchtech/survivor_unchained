"""Ground check on a built clip's JSON: python groundj.py name [hero|folk_m|folk_f] [--before] [step]"""
import sys
from pathlib import Path
W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import audit
from rig import DATA, Skeleton
args = [a for a in sys.argv[1:] if not a.startswith("--")]
name = args[0]
body = args[1] if len(args) > 1 else "her"
step = int(args[2]) if len(args) > 2 else 4
skel, folder = {"her": ("heroine_skeleton.json", "clips"), "hero": ("hero_skeleton.json", "hero"),
                "folk_m": ("folk_male_skeleton.json", "folk"), "folk_f": ("folk_female_skeleton.json", "folk")}[body]
base = Path(__file__).parent / "out_before" if "--before" in sys.argv else W / "out"
sk = Skeleton.load(DATA / skel)
d, rot, pos = audit.load(base / folder / f"{name}.json", sk)
g, p = sk.fk(rot, pos)
I = sk.index
flesh = {"calf_l": 0.05, "calf_r": 0.05, "pelvis": 0.11, "foot_l": 0.06, "foot_r": 0.06, "ball_l": 0.015, "ball_r": 0.015,
         "hand_l": 0.02, "hand_r": 0.02, "lowerarm_l": 0.04, "lowerarm_r": 0.04, "Head": 0.10, "spine_02": 0.11}
n = rot.shape[0]
for fr in list(range(0, n, step)) + [n - 1]:
    under = {k: p[fr, I[k]][1] - r for k, r in flesh.items()}
    low = sorted(under.items(), key=lambda kv: kv[1])[:3]
    flag = "  <-- through" if low[0][1] < -0.015 else ""
    print(f"f{fr:3d} " + "  ".join(f"{k} {v:+.3f}" for k, v in low) + f"  root y {p[fr, I['pelvis']][1]:.2f}" + flag)
