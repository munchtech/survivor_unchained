"""Per-time metrics of a clip for judging hand-to-face work: head pitch/yaw, each hand's distance to the mouth,
hand heights, chest pitch, pelvis travel.
usage: python metrics.py <spec> [body] [step frames]   (spec as stick.py)"""
import math
import sys
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017")
sys.path.insert(0, str(WT / "tools" / "anim"))
import numpy as np
from keyed import Rig
from rig import DATA, Skeleton, qinv, qmul, qrot

args = [a for a in sys.argv[1:] if "=" not in a]
kw = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
spec = args[0]
body = args[1] if len(args) > 1 else "her"
step = int(args[2]) if len(args) > 2 else 6
skel = {"her": "heroine_skeleton.json", "hero": "hero_skeleton.json", "m": "folk_male_skeleton.json", "f": "folk_female_skeleton.json"}[body]
sk = Skeleton.load(DATA / skel)
rig = Rig(sk, body={"her": "her", "hero": "him"}.get(body, "her"))
kind, name = spec.split(":", 1)
if kind == "warden":
    from clips import warden
    clip = warden.CLIPS[name](name, rig)
elif kind == "take":
    from clips.generated import make
    prompt, t = name.rsplit("_", 1)
    clip = make(rig, name, "kimodo", f"{prompt}_{t}.bvh", place=kw.get("place", "keep"))
elif kind == "story":
    from clips import story
    clip = dict(story.ALL)[name](rig)
elif kind == "keyed":
    import crowd
    clip = crowd.KEYED[name](name, rig)
else:
    import importlib
    clip = dict(importlib.import_module(f"clips.{kind}").ALL)[name](rig)
g, p = sk.fk(clip.rot, clip.pos)
I = sk.index
grest, prest = sk.rest_globals()
H = I["Head"]
mouth_off = np.array(kw.get("mouth", "0,0.05,0.10").split(","), float)  # from the head joint, at rest, character space
off_local = qrot(qinv(grest[0, H]), mouth_off)
def fwd(j, f):
    return qrot(g[f, j], qrot(qinv(grest[0, j]), np.array([0, 0, 1.0])))
print(f"{spec}: {clip.frames} frames {clip.length:.2f} s; mouth at rest {prest[0, H] + mouth_off}")
print("  t     headP headY chestP |  mouth y  | dR    dL   | hR(y,z)      hL(y,z)     | pelvis xz")
for f in list(range(0, clip.frames, step)) + ([clip.frames - 1] if (clip.frames - 1) % step else []):
    m = p[f, H] + qrot(g[f, H], off_local)
    hf = fwd(H, f)
    cf = fwd(I["spine_03"], f)
    hp = math.degrees(math.asin(np.clip(hf[1], -1, 1)))
    hy = math.degrees(math.atan2(hf[0], hf[2]))
    cp = math.degrees(math.asin(np.clip(cf[1], -1, 1)))
    hr, hl = p[f, I["hand_r"]], p[f, I["hand_l"]]
    dr, dl = np.linalg.norm(hr - m), np.linalg.norm(hl - m)
    pel = p[f, I["pelvis"]]
    print(f"{f/30:5.2f}  {hp:+5.0f} {hy:+5.0f} {cp:+5.0f}  | {m[1]:.2f}      | {dr:.2f} {dl:.2f} | {hr[1]:.2f},{hr[2]:+.2f}   {hl[1]:.2f},{hl[2]:+.2f}  | {pel[0]:+.2f},{pel[2]:+.2f}")
