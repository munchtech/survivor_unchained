"""The raw twist the hand step asks of each arm, per frame (pass 2), for a run
or sprint: python twist.py sprint_reaver [side]"""
import sys
from pathlib import Path

W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np  # noqa: E402
from keyed import Rig  # noqa: E402
from rig import DATA, Skeleton  # noqa: E402

name = sys.argv[1]
side = sys.argv[2] if len(sys.argv) > 2 else "r"
sk = Skeleton.load(DATA / "heroine_skeleton.json")
rig = Rig(sk)
log = []
orig = rig._strain


def st(d_la, want, ha, fa, s):
    r = orig(d_la, want, ha, fa, s)
    log.append((s, r[0], r[1]))
    return r


rig._strain = st
if name.startswith("sprint"):
    from clips import sprint_stop
    c = sprint_stop.sprint(rig, "run" + name[6:])
else:
    from clips import run
    from gait import run_cycle
    from dataclasses import replace
    g, arms, weapon = run.RUNS[name]
    c = run_cycle(name, rig, replace(g, arms=arms), {"weapon": weapon})
mine = [x for x in log if x[0] == side]
n = c.frames
for f, (s, tw, sw) in enumerate(mine[-n:]):
    print(f"f{f:2d} twist {tw:+6.0f} swing {sw:4.0f}")
