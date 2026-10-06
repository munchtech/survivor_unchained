"""Per frame of a run: the sword arm's forearm and blade in the chest's frame,
the angle between them, and the arm's swing k. python runarm.py run_warden [her|hero]"""
import math
import sys
from pathlib import Path

W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np  # noqa: E402
from keyed import Rig, GRIP  # noqa: E402
from rig import DATA, Skeleton, qaxis, qinv, qmul, qrot  # noqa: E402
from clips import run  # noqa: E402
from gait import run_cycle  # noqa: E402
from dataclasses import replace  # noqa: E402

name = sys.argv[1]
body = sys.argv[2] if len(sys.argv) > 2 else "her"
side = sys.argv[3] if len(sys.argv) > 3 else "r"
sk = Skeleton.load(DATA / ("hero_skeleton.json" if body == "hero" else "heroine_skeleton.json"))
rig = Rig(sk, body="him" if body == "hero" else "her")
if name.startswith("sprint"):
    from clips import sprint_stop
    c = sprint_stop.sprint(rig, "run" + name[6:])
else:
    g, arms, weapon = run.RUNS[name]
    c = run_cycle(name, rig, replace(g, arms=arms), {"weapon": weapon})
G, P = sk.fk(c.rot, c.pos)
I = sk.index
lean = rig.grip.get(side, 0.0)
lq = qaxis([1.0, 0, 0], -lean)
s3 = I["spine_03"]
for f in range(c.frames):
    ph = f / (c.frames - 1)
    off = 0.0 if side == "l" else 0.5
    k = 0.5 - 0.5 * math.cos(2 * math.pi * (ph - off - 0.5))
    chest = qmul(G[f, s3], qinv(rig.grest[s3]))
    ci = qinv(chest)
    fa = P[f, I[f"hand_{side}"]] - P[f, I[f"lowerarm_{side}"]]
    fa = qrot(ci, fa / np.linalg.norm(fa))
    bl = qrot(ci, qrot(qmul(G[f, I[f"hand_{side}"]], lq), [0, 0, 1.0]))
    ang = math.degrees(math.acos(max(-1, min(1, float(np.dot(fa, bl))))))
    ua = P[f, I[f"lowerarm_{side}"]] - P[f, I[f"upperarm_{side}"]]
    fw = P[f, I[f"hand_{side}"]] - P[f, I[f"lowerarm_{side}"]]
    bend = math.degrees(math.acos(max(-1, min(1, float(np.dot(ua, fw) / np.linalg.norm(ua) / np.linalg.norm(fw))))))
    print(f"f{f:2d} bend {bend:3.0f} k {k:.2f} forearm({fa[0]:+.2f},{fa[1]:+.2f},{fa[2]:+.2f}) blade({bl[0]:+.2f},{bl[1]:+.2f},{bl[2]:+.2f}) angle {ang:3.0f}")
