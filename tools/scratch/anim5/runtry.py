"""Try a thumb carry on a run: python runtry.py run_warden bx,by,bz fx,fy,fz [--write]
(thumb at the back swing and at the front, chest frame, right hand; mirrored
for the left). Prints the blade per frame and whether it passes through her."""
import math
import sys
from dataclasses import replace
from pathlib import Path

W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np  # noqa: E402
from keyed import Rig  # noqa: E402
from rig import DATA, Skeleton, qaxis, qinv, qmul, qrot, write_clip  # noqa: E402
from clips import run  # noqa: E402
from gait import run_cycle  # noqa: E402
import blade as B  # noqa: E402

name = sys.argv[1]
back = np.array([float(x) for x in sys.argv[2].split(",")])
fwd = np.array([float(x) for x in sys.argv[3].split(",")])
sk = Skeleton.load(DATA / "heroine_skeleton.json")
rig = Rig(sk)


import os  # noqa: E402
from gait import arc_of  # noqa: E402
SWB = np.array([float(x) for x in os.environ["SWB"].split(",")]) if os.environ.get("SWB") else None
SWF = np.array([float(x) for x in os.environ["SWF"].split(",")]) if os.environ.get("SWF") else None


def carry(sign):
    def f(ph, k, hand):
        hand = dict(hand)
        t = back * (1 - k) + fwd * k
        hand.update({"thumb": (t[0] * sign, t[1], t[2]), "frame": "chest", "twist": 0.5})
        if SWB is not None:
            e = k * k * (3 - 2 * k)
            v = SWB + (SWF - SWB) * e
            v = v * [-sign, 1, 1]
            hand["arc"] = arc_of(v)
        return hand
    return f


g, arms, weapon = run.RUNS[name]
arms = {s: (carry(1 if s == "r" else -1) if s in ("r", "l") and arms[s].__qualname__.startswith("blade_carry") else arms[s]) for s in arms}
c = run_cycle(name, rig, replace(g, arms=arms), {"weapon": weapon})
G, P = sk.fk(c.rot, c.pos)
I = sk.index
lq = qaxis([1.0, 0, 0], -rig.grip.get("r", 0.0))
s3 = I["spine_03"]
hits = 0
for f in range(c.frames):
    chest = qmul(G[f, s3], qinv(rig.grest[s3]))
    h = I["hand_r"]
    q = qmul(G[f, h], lq)
    bl = qrot(qinv(chest), qrot(q, [0, 0, 1.0]))
    a = P[f, h] + qrot(G[f, h], [-0.025, 0.075, 0.0])
    b = a + qrot(q, [0, 0, 1.0]) * 0.8
    worst = 0
    for j0, j1, r in B.CAPS:
        dist, s_ = B.seg_seg(a, b, P[f, I[j0]], P[f, I[j1]])
        if s_ > 0.12:
            worst = max(worst, r + 0.01 - dist)
    hits += worst > 0
    tip = b - P[f, I["pelvis"]]
    print(f"f{f:2d} blade(chest)({bl[0]:+.2f},{bl[1]:+.2f},{bl[2]:+.2f}) tip from pelvis({100*tip[0]:+4.0f},{100*tip[1]:+4.0f},{100*tip[2]:+4.0f})" + (f"  THROUGH {100*worst:.0f}" if worst > 0 else ""))
print(hits, "frames through her")
if "--write" in sys.argv:
    write_clip(c, sk, W / "out" / "clips")
    print("written")
