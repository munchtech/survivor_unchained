"""The warden's guard at one frame, in her space (cm; x her left, y up, z
forward): eyes, the shield's centre and top of its rim, the sword hand, the
blade's tip, and the blade's height as it crosses the shield's plane.
python guard.py [frame] [her|hero]  (out/clips/warden_show.json)"""
import sys
from pathlib import Path

W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np  # noqa: E402
import audit  # noqa: E402
from keyed import GRIP  # noqa: E402
from rig import DATA, Skeleton, qaxis, qmul, qrot  # noqa: E402

fr = int(sys.argv[1]) if len(sys.argv) > 1 else 30
body = sys.argv[2] if len(sys.argv) > 2 else "her"
name = sys.argv[3] if len(sys.argv) > 3 else "warden_show"
sk = Skeleton.load(DATA / ("hero_skeleton.json" if body == "hero" else "heroine_skeleton.json"))
folder = W / "out" / ("hero" if body == "hero" else "clips")
d, rot, pos = audit.load(folder / f"{name}.json", sk)
g, p = sk.fk(rot, pos)
I = sk.index


def cm(v):
    return "(" + ",".join(f"{100 * x:+5.0f}" for x in v) + ")"


la = I["lowerarm_l"]
# The shield as anim_review/Arms mount it: 0.14 along the forearm, its face
# along the bone's -X, 0.05 out; radius 0.30 (0.33 in the game).
fq = g[fr, la]
centre = p[fr, la] + qrot(fq, [0, 0.14, 0]) + qrot(fq, [-0.05, 0, 0])
normal = qrot(fq, [-1.0, 0, 0])
up = np.array([0, 1.0, 0]) - normal * normal[1]
up /= np.linalg.norm(up)
top = centre + up * 0.31
h = I["hand_r"]
lq = qaxis([1.0, 0, 0], -GRIP["sword"])
grip = p[fr, h] + qrot(g[fr, h], [-0.025, 0.075, 0])
blade = qrot(qmul(g[fr, h], lq), [0, 0, 1.0])
tip = grip + blade * 0.80
head = p[fr, I["Head"]]
eyes = head + np.array([0, 0.09, 0.08])
print(f"frame {fr}: eyes {cm(eyes)} shield centre {cm(centre)} rim top {cm(top)} normal ({normal[0]:+.2f},{normal[1]:+.2f},{normal[2]:+.2f})")
print(f"  sword grip {cm(grip)} blade ({blade[0]:+.2f},{blade[1]:+.2f},{blade[2]:+.2f}) tip {cm(tip)}")
# Where the blade crosses the shield's plane, and how far above its top that is.
den = float(np.dot(blade, normal))
if abs(den) > 1e-6:
    t = float(np.dot(centre - grip, normal)) / den
    x = grip + blade * t
    print(f"  crosses the shield's plane {100 * t:.0f} cm out at {cm(x)}: {100 * (x[1] - top[1]):+.0f} cm above the rim's top, "
          f"{100 * np.linalg.norm(x - centre):.0f} cm from its centre")

# Targets in her space (env GRIP=x,y,z cm; BLADE=x,y,z) put in the chest's
# frame, as a key would give them.
import os  # noqa: E402
from rig import qinv  # noqa: E402
if os.environ.get("GRIP"):
    from keyed import Rig  # noqa: E402
    rig = Rig(sk)
    s3 = I["spine_03"]
    chest = qmul(g[fr, s3], qinv(rig.grest[s3]))
    ci = qinv(chest)
    want = np.array([float(x) for x in os.environ["GRIP"].split(",")]) / 100
    sh = p[fr, I["upperarm_r"]]
    # (The keyed point is the wrist; the grip sits a few cm on along the hand.)
    wrist = want - (grip - p[fr, h])
    v = qrot(ci, wrist - sh)
    b = qrot(ci, np.array([float(x) for x in os.environ["BLADE"].split(",")]))
    b /= np.linalg.norm(b)
    print(f"  key: arc_of(({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})) blade _n({b[0]:.2f}, {b[1]:.2f}, {b[2]:.2f})  (shoulder {cm(sh)})")
