import sys, json, math, numpy as np
from pathlib import Path
W = Path(r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40")
sys.path.insert(0, str(W / "tools/anim"))
from keyed import Rig
from rig import Skeleton, DATA, qrot, qmul, qinv
from clips import idle
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk)
base = idle.base_of(rig, "arcanist_town")
over = idle.staff_walk(rig, base)
j = json.loads((W / "tools/anim/out/clips/idle_arcanist_staff_town.json").read_text())
rot = np.array([np.tile(sk.rest_rot[k], (base.frames, 1)) for k in range(len(sk))]).transpose(1, 0, 2)
pos = np.array([np.tile(sk.rest_pos[k], (base.frames, 1)) for k in range(len(sk))]).transpose(1, 0, 2)
for t in j["tracks"]:
    k = sk.i(t["bone"]); a = np.array(t["keys"])
    if t["type"] == "rot": rot[:, k] = a
    else: pos[:, k] = a
g, p = sk.fk(rot, pos)
h = sk.i("hand_r")
for f in range(0, base.frames, 30):
    s = over(f / (base.frames - 1), f)["hand_r"]
    R = np.stack([qrot(g[f, h], e) for e in np.eye(3)], axis=1)
    from keyed import GRIP
    from rig import qaxis
    lq = qaxis([1.0, 0, 0], -18.0); gz = qrot(lq, [0, 0, 1.0])
    print(f, "pos want", np.round(s["pos"], 3), "got", np.round(p[f, h], 3), "blade want", np.round(s["blade"], 2), "got", np.round(R @ gz, 2))
print("--- wanted hand vs actual forearm")
la = sk.i("lowerarm_r"); gr = rig.grest
from rig import qfrom_basis
for f in range(0, base.frames, 30):
    s = over(f / (base.frames - 1), f)["hand_r"]
    z = np.array(s["blade"]); y = np.array(s["knuckles"]); y = y - z * (y @ z); y /= np.linalg.norm(y)
    Rg = np.stack([np.cross(y, z), y, z], axis=1)          # grip frame
    Rl = np.stack([qrot(lq, e) for e in np.eye(3)], axis=1)
    R = Rg @ Rl.T
    fa = p[f, h] - p[f, la]; fa /= np.linalg.norm(fa)
    fh = R.T @ fa
    # twist: hand rel. to forearm bone vs rest relation
    Rla = np.stack([qrot(g[f, la], e) for e in np.eye(3)], axis=1)
    Rla0 = np.stack([qrot(gr[la], e) for e in np.eye(3)], axis=1); Rh0 = np.stack([qrot(gr[h], e) for e in np.eye(3)], axis=1)
    rel = (Rla @ Rla0.T @ Rh0).T @ R    # wanted hand relative to the hand riding the (solved) forearm
    ax = Rh0.T @ (Rla0 @ (Rla0.T @ (p[0, h]*0 + fa)))
    print(f, "phi", round(math.degrees(math.atan2(fh[0], fh[1]))), "dev", round(math.degrees(math.atan2(-fh[2], fh[1]))), "rel angle", round(math.degrees(math.acos(np.clip((np.trace(rel) - 1) / 2, -1, 1)))), "fa", np.round(fa, 2), "E", np.round(p[f, la], 3))
