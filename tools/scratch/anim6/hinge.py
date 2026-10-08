"""On the built skeleton: each share bone's X against its joint's hinge (the
turn about its own line that would bring it there; about 0 when built
right), and the twist bones' rests."""
import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8d33b2672b7be905\tools\anim")
import numpy as np  # noqa: E402
from rig import Skeleton, qrot  # noqa: E402
import helpers as hp  # noqa: E402

sk = Skeleton.load(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8d33b2672b7be905\tools\anim\data\heroine_skeleton.json")
grot, gpos = sk.rest_globals()
I = sk.index
for h in hp.SPEC["helpers"]:
    for s in "lr":
        n = h["name"].replace("{s}", s)
        j = I[n]
        if h["kind"] == "share":
            b = I[h["bone"].replace("{s}", s)]
            above = sk.parent[b]
            t = hp.hinge_turn(grot[0, j], gpos[0, above], gpos[0, b], h["way"])
            x = qrot(grot[0, j], [1, 0, 0])
            print(f"{n:22s} hinge turn {t:7.2f} deg  at {np.round(gpos[0, j], 3)} (bone {np.round(gpos[0, b], 3)})  X {np.round(x, 3)}")
        else:
            p = sk.parent[j]
            print(f"{n:22s} rest rot {np.round(sk.rest_rot[j], 4)}  pos {np.round(sk.rest_pos[j], 4)} (parent's child at {np.round(sk.rest_pos[I[hp.MAIN_CHILD[sk.names[p].split('_')[0]] + '_' + s]], 4)})")
