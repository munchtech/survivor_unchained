"""The walking staff in her right hand: per clip, the foot's drift and height, the crescent to the hat (brim), braid
and head, the staff to her skin and outfit (legs, arm), and the staff's tilt. No Godot.
usage: python walkcheck.py <clip> [--roll=DEG] [--slide=0.25] [--step=1] [--arms=FILE (key mage_staff@hand_r:walk)]
The walking transform (hand_r space): v -> At + Q (v - At - slide*Dir), Q the half-turn about n, n square to Dir at
`roll` deg from hand +X's part square to Dir (about Dir)."""
import json, sys, math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

W = Path(r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40")
sys.path.insert(0, str(W / "tools/anim"))
import skin  # noqa
from skin import Body, PEOPLE, Jiggle  # noqa
from rig import Skeleton, DATA  # noqa

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
clip_name = args[0]
step = int(opt.get("step", 1))
A = np.array([-0.0326, 0.0841, -0.0104]); D = np.array([-0.2116, 0.4141, 0.8853]); D /= np.linalg.norm(D)


def walk_of(v, roll, slide):
    x = np.array([1.0, 0, 0]); x = x - D * (x @ D); x /= np.linalg.norm(x)
    y = np.cross(D, x)
    nn = math.cos(math.radians(roll)) * x + math.sin(math.radians(roll)) * y
    Q = 2 * np.outer(nn, nn) - np.eye(3)
    return A + (v - A - slide * D) @ Q.T


raw = json.loads((DATA / "arms_local.json").read_text())
if "arms" in opt:
    v = np.array(json.loads(Path(opt["arms"]).read_text())["mage_staff@hand_r:walk"]["v"], float)
else:
    v = walk_of(np.array(raw["mage_staff@hand_r"]["v"], float), float(opt.get("roll", 0)), float(opt.get("slide", 0.25)))
s = (v - A) @ D           # along the fist's line: the foot is now at +s
foot_end = A + s.max() * D
FOOT = s > s.max() - 0.03
HEAD = s < -0.32          # the crescent and its collar (heel side)
LOW = s > 0.10            # the shaft below her hand (to her legs)

sk = Skeleton.load(DATA / "heroine_skeleton.json")
files = [(PEOPLE / "heroine.glb", lambda n: n in ("Heroine", "HeroineHead"), "skin"),
         (PEOPLE / "heroine_outfit_arcanist.gltf", lambda n: n.startswith("arcanist."), "garment"),
         (PEOPLE / "heroine_hair_braid.gltf", lambda n: True, "hair")]
b = Body(sk, files, Jiggle(sk), label="her", helpers=True)
I = sk.index
vb = np.array(sk.names)[b.J[np.arange(len(b.P)), b.W.argmax(1)]].astype(str)
loose = b.W.sum(1) < 0.5
SK, GA, HA = b.kind == "skin", b.kind == "garment", b.kind == "hair"
HAT = GA & np.char.startswith(b.piece.astype(str), "arcanist.head")
HEADSK = SK & np.isin(vb, ["head", "neck_01", "neck_02"])
RARM = np.char.endswith(vb, "_r") & (np.char.startswith(vb, "upperarm") | np.char.startswith(vb, "lowerarm"))
RHAND = np.char.endswith(vb, "_r") & (np.char.startswith(vb, "hand") | np.isin(np.char.partition(vb, "_")[:, 0], ["index", "middle", "ring", "pinky", "thumb"]))
LEG = np.char.startswith(vb, "thigh") | np.char.startswith(vb, "calf") | np.char.startswith(vb, "foot") | np.char.startswith(vb, "ball")
BODY = ~HAT & ~HA & ~RHAND & ~RARM
Gs = b.frames(b.clip(clip_name))
feet, tilt, out = [], [], {k: (9e9, -1) for k in ("hat", "braid", "headskin", "legs", "body", "r-arm", "lowest")}
deep = {k: (0.0, -1) for k in ("garment", "skin")}
for f in range(0, len(Gs), step):
    G = Gs[f]
    P = b.pose(G)
    if loose.any():
        Hb = G[I["head"]] @ b.rest_inv[I["head"]]
        P[loose] = (Hb[:3, :3] @ b.P[loose].T).T + Hb[:3, 3]
    H = G[I["hand_r"]]
    Q = v @ H[:3, :3].T + H[:3, 3]
    fe = H[:3, :3] @ foot_end + H[:3, 3]
    feet.append(fe)
    d = H[:3, :3] @ D
    tilt.append(math.degrees(math.acos(min(1.0, -d[1]))))
    th, tl, ta = cKDTree(Q[HEAD]), cKDTree(Q[LOW]), cKDTree(Q)
    def upd(k, x):
        if x < out[k][0]:
            out[k] = (x, f)
    upd("hat", th.query(P[HAT])[0].min())
    upd("braid", th.query(P[HA])[0].min())
    upd("headskin", th.query(P[HEADSK])[0].min())
    upd("legs", tl.query(P[LEG])[0].min())
    upd("body", ta.query(P[BODY & ~LEG])[0].min())
    upd("r-arm", tl.query(P[RARM & SK])[0].min())
    upd("lowest", Q[:, 1].min())
    for mask, lab in ((GA & ~HAT & ~RHAND, "garment"), (SK & ~RHAND, "skin")):
        idx = np.nonzero(mask)[0]
        N = skin._normals(P, b.T)[idx]
        dd, j = cKDTree(P[idx]).query(Q)
        near = dd < 0.03
        if near.any():
            dep = -np.einsum("ij,ij->i", Q[near] - P[idx][j[near]], N[j[near]])
            if dep.max() > deep[lab][0]:
                deep[lab] = (float(dep.max()), f)
feet = np.array(feet)
c = feet.mean(axis=0)
print(f"{clip_name}: frames {len(Gs)}  foot mean {np.round(c, 3)}  drift max {1000 * np.linalg.norm(feet - c, axis=1).max():.1f} mm"
      f"  foot y {feet[:, 1].min():.3f}..{feet[:, 1].max():.3f}  tilt {min(tilt):.1f}..{max(tilt):.1f} deg")
print("  min mm (frame): " + "  ".join(f"{k} {1000 * x:.0f} ({fr})" if k != "lowest" else f"lowest point y {x:.3f} ({fr})" for k, (x, fr) in out.items()))
print("  into mm (frame): " + "  ".join(f"{k} {1000 * x:.1f} ({fr})" for k, (x, fr) in deep.items()))
