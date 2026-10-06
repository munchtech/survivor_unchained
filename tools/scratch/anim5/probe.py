"""Arm geometry per frame of a keyed clip: python probe.py module fn [her|hero] [step] [side]
Prints, per frame: wrist and elbow relative to the shoulder (cm, her space: x left, y up, z fwd),
the blade (hand +Z) and knuckles (hand +Y), the forearm's nearest pass to the face (cm),
and the hand's turn from the last frame."""
import importlib
import math
import sys
from pathlib import Path

W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np  # noqa: E402
from keyed import Rig  # noqa: E402
from rig import DATA, Skeleton, qrot  # noqa: E402

mod, fn = sys.argv[1], sys.argv[2]
body = sys.argv[3] if len(sys.argv) > 3 else "her"
step = int(sys.argv[4]) if len(sys.argv) > 4 else 2
sides = sys.argv[5] if len(sys.argv) > 5 else "r"
sk = Skeleton.load(DATA / ("hero_skeleton.json" if body == "hero" else "heroine_skeleton.json"))
rig = Rig(sk, body="him" if body == "hero" else "her")
m = importlib.import_module(f"clips.{mod}")
c = dict(m.ALL)[fn](rig) if hasattr(m, "ALL") and fn in dict(m.ALL) else getattr(m, fn)(rig)
g, p = sk.fk(c.rot, c.pos)
I = sk.index


def seg_dist(a, b, x):
    ab = b - a
    t = max(0.0, min(1.0, float(np.dot(x - a, ab) / np.dot(ab, ab))))
    return float(np.linalg.norm(a + ab * t - x))


def cm(v):
    return "(" + ",".join(f"{100 * x:+4.0f}" for x in v) + ")"


for s in sides:
    print(f"--- {fn} {body} side {s}, {c.frames} frames")
    for f in list(range(0, c.frames, step)):
        S, E, Wr = p[f, I[f"upperarm_{s}"]], p[f, I[f"lowerarm_{s}"]], p[f, I[f"hand_{s}"]]
        head = p[f, I["Head"]] + np.array([0, 0.09, 0.06])
        hq = g[f, I[f"hand_{s}"]]
        blade = qrot(hq, [0, 0, 1.0])
        knk = qrot(hq, [0, 1.0, 0])
        face = min(seg_dist(E, Wr, head), seg_dist(S, E, head))
        step_ = math.degrees(2 * math.acos(min(1, abs(float(np.dot(hq, g[f - 1, I[f"hand_{s}"]])))))) if f else 0
        print(f"f{f:3d} wrist{cm(Wr - S)} elbow{cm(E - S)} blade({blade[0]:+.2f},{blade[1]:+.2f},{blade[2]:+.2f}) "
              f"knk({knk[0]:+.2f},{knk[1]:+.2f},{knk[2]:+.2f}) face {100 * face:3.0f} turn {step_:4.0f}")
