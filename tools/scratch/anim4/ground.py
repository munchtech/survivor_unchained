"""Where a clip goes through the ground: per step, the lowest of each body part
(joints, with the flesh round them: knee 0.05, hip/pelvis 0.11, ankle 0.06, hand 0.02, elbow 0.04, head 0.10).
usage: python ground.py <spec> [body] [step]"""
import sys
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017")
sys.path.insert(0, str(WT / "tools" / "anim"))
import importlib
from keyed import Rig
from rig import DATA, Skeleton

spec = sys.argv[1]
body = sys.argv[2] if len(sys.argv) > 2 else "her"
step = int(sys.argv[3]) if len(sys.argv) > 3 else 6
skel = {"her": "heroine_skeleton.json", "hero": "hero_skeleton.json", "m": "folk_male_skeleton.json", "f": "folk_female_skeleton.json"}[body]
sk = Skeleton.load(DATA / skel)
rig = Rig(sk, body={"her": "her", "hero": "him"}.get(body, "her"))
kind, name = spec.split(":", 1)
mod = importlib.import_module(f"clips.{kind}")
clip = dict(mod.ALL)[name](rig)
g, p = sk.fk(clip.rot, clip.pos)
I = sk.index
flesh = {"calf_l": 0.05, "calf_r": 0.05, "pelvis": 0.11, "foot_l": 0.06, "foot_r": 0.06, "ball_l": 0.015, "ball_r": 0.015,
         "hand_l": 0.02, "hand_r": 0.02, "lowerarm_l": 0.04, "lowerarm_r": 0.04, "Head": 0.10, "spine_02": 0.11}
print(f"{spec}: {clip.frames} frames")
for fr in list(range(0, clip.frames, step)) + [clip.frames - 1]:
    under = {n: p[fr, I[n]][1] - r for n, r in flesh.items()}
    worst = min(under, key=under.get)
    low = sorted(under.items(), key=lambda kv: kv[1])[:3]
    flag = "  <-- through" if under[worst] < -0.015 else ""
    print(f"f{fr:3d} " + "  ".join(f"{n} {v:+.3f}" for n, v in low) + flag)
