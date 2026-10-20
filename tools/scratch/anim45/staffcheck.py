"""The staff slung on her back (animation 45): clearances socktry.py does not measure. No Godot.
usage: python staffcheck.py "<At>;<Shaft>;<Thick>"|old <clip> [<clip> ...] [--outfit=arcanist] [--step=1] [--clr=0.012]
Rebuilds mage_staff@hand_r's sheathed mount (arms_local.json "sheathed", as Arms.Sheathed) from the row, pushed out
along the row's normal (0,0,-1) by --clr (the outfit's back_staff clearance; default socket_clearance.json's
back_diag for the outfit), and per clip prints the minimum over frames of:
  head:  the staff's head (points > 0.30 m up the shaft from the grip) to her head and neck skin, the hat (<outfit>.head.*)
         and the braid (heroine_hair_braid, rigid on her head bone: no physics), each
  foot:  the staff's foot (points < -0.55 m) to her calves and feet (skin) and boots
  hands: both hands (hand and fingers, the forearm within 8 cm of the wrist) to the whole staff
  into:  the worst depth of the staff into her outfit's garment surface (signed by the garment's normals, near points only)
"""
import json, sys, math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "anim"))
import skin  # noqa
from skin import Body, PEOPLE, Jiggle  # noqa
from rig import Skeleton, DATA  # noqa

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
row, clips = args[0], args[1:]
outfit = opt.get("outfit", "arcanist")
step = int(opt.get("step", 1))
clrf = json.loads((ROOT / "godot/art/anim/socket_clearance.json").read_text())
clr = float(opt.get("clr", clrf.get(outfit, {}).get("back_staff", clrf.get(outfit, {}).get("back_diag", 0.012))))
REST = {"spine_03": (-18.4, (0, 1.3335, 0.0364))}


def rest(bone):
    a, o = REST[bone]
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    M = np.eye(4)
    M[:3, :3] = [[1, 0, 0], [0, c, -s], [0, s, c]]
    M[:3, 3] = o
    return M


raw = json.loads((DATA / "arms_local.json").read_text())["sheathed"]["mage_staff@hand_r"]
M0 = np.vstack([np.array(raw["mount"], float), [0, 0, 0, 1]])
v = np.array(raw["v"], float)
u = (np.linalg.inv(M0) @ np.c_[v, np.ones(len(v))].T).T[:, :3]
if row == "old":
    M1 = M0
else:
    at, shaft, thick = (np.array([float(x) for x in p.split(",")]) for p in row.split(";"))
    shaft /= np.linalg.norm(shaft)
    thick = thick - shaft * thick.dot(shaft)
    thick /= np.linalg.norm(thick)
    S = np.eye(4)
    S[:3, :3] = np.column_stack([np.cross(shaft, thick), shaft, thick])
    S[:3, 3] = at
    M1 = np.linalg.inv(rest("spine_03")) @ S
normal_b = np.linalg.inv(rest("spine_03"))[:3, :3] @ np.array([0, 0, -1.0])
pts = (M1 @ np.c_[u, np.ones(len(u))].T).T[:, :3] + normal_b * clr   # spine_03 space
head, foot = u[:, 1] > 0.30, u[:, 1] < -0.55

sk = Skeleton.load(DATA / "heroine_skeleton.json")
files = [(PEOPLE / "heroine.glb", lambda n: n in ("Heroine", "HeroineHead"), "skin"),
         (PEOPLE / f"heroine_outfit_{outfit}.gltf", lambda n, o=outfit: n.startswith(o + "."), "garment"),
         (PEOPLE / "heroine_hair_braid.gltf", lambda n: True, "hair")]
b = Body(sk, files, Jiggle(sk, amount=0.55 if outfit == "warden" else 1.0, squash=0.0 if outfit == "warden" else 1.0),
         label="her", helpers=True)
I = sk.index
vb = np.array(sk.names)[b.J[np.arange(len(b.P)), b.W.argmax(1)]]
loose = b.W.sum(1) < 0.5          # weighted only to bones the skeleton lacks (the braid's chain): rigid on the head
SK, GA, HA = b.kind == "skin", b.kind == "garment", b.kind == "hair"
HAT = GA & np.char.startswith(b.piece.astype(str), f"{outfit}.head")
HEADSK = SK & np.isin(vb, ["head", "neck_01", "neck_02"])
CALF = SK & (np.char.startswith(vb.astype(str), "calf") | np.char.startswith(vb.astype(str), "foot") | np.char.startswith(vb.astype(str), "ball"))
BOOT = GA & np.char.find(b.piece.astype(str), ".boots") >= 0
FING = ("index", "middle", "ring", "pinky", "thumb")
HAND = {s: np.array([n.endswith("_" + s) and (n.startswith("hand") or n.split("_")[0] in FING) for n in vb]) & SK for s in "lr"}
FORE = {s: (vb == f"lowerarm_{s}") & SK for s in "lr"}
print(f"row {row}  outfit {outfit}  clearance {1000 * clr:.1f} mm  hat pts {HAT.sum()}  hair pts {HA.sum()} (loose {int((loose & HA).sum())})")
Grest = None
for name in clips:
    clip = b.clip(name)
    Gs = b.frames(clip)
    best = {k: (9e9, -1) for k in ("head-head", "head-hat", "head-braid", "foot-calf", "foot-boot", "hand l", "hand r", "staff-braid")}
    deep = (0.0, -1, "")
    for f in range(0, len(Gs), step):
        G = Gs[f]
        P = b.pose(G)
        if loose.any():
            Hb = G[I["head"]] @ b.rest_inv[I["head"]]
            P[loose] = (Hb[:3, :3] @ b.P[loose].T).T + Hb[:3, 3]
        Mb = G[I["spine_03"]]
        Q = pts @ Mb[:3, :3].T + Mb[:3, 3]
        th, tf, ta = cKDTree(Q[head]), cKDTree(Q[foot]), cKDTree(Q)
        def upd(k, d):
            if d < best[k][0]:
                best[k] = (d, f)
        upd("head-head", th.query(P[HEADSK])[0].min())
        if HAT.any(): upd("head-hat", th.query(P[HAT])[0].min())
        if HA.any():
            upd("head-braid", th.query(P[HA])[0].min())
            upd("staff-braid", ta.query(P[HA])[0].min())
        upd("foot-calf", tf.query(P[CALF])[0].min())
        if BOOT.any(): upd("foot-boot", tf.query(P[BOOT])[0].min())
        for s in "lr":
            hj = G[I[f"hand_{s}"]][:3, 3]
            hv = P[HAND[s] | (FORE[s] & (np.linalg.norm(P - hj, axis=1) < 0.08))]
            upd(f"hand {s}", ta.query(hv)[0].min())
        # Into the garment and skin: staff points behind the nearest surface vertex's normal (within 3 cm).
        for mask, lab in ((GA & ~HAT, "garment"), (HAT, "hat"), (SK, "skin")):
            if not mask.any():
                continue
            idx = np.nonzero(mask)[0]
            N = skin._normals(P, b.T)[idx]
            d, j = cKDTree(P[idx]).query(Q)
            near = d < 0.03
            if near.any():
                depth = -np.einsum("ij,ij->i", Q[near] - P[idx][j[near]], N[j[near]])
                k = depth.argmax()
                if depth[k] > deep[0]:
                    deep = (float(depth[k]), f, f"{lab} {b.piece[idx][j[near]][k]} {vb[idx][j[near]][k]}")
    print(f"{name:24} " + "  ".join(f"{k} {1000 * d:4.0f}(f{fr})" for k, (d, fr) in best.items())
          + f"  | into {1000 * deep[0]:.1f} mm" + (f" f{deep[1]} {deep[2]}" if deep[0] > 0 else ""))
