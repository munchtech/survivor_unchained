"""Try a sheathed socket without Godot (animation 44, solver idle 2).
usage: python socktry.py <socket> "<At>;<Shaft>;<Thick>" <clip> [<clip> ...] [--outfit=reaver] [--keys=viking_axe@hand_r,...]
       [--step=1] [--head=0.42] [--write=path]
<At>/<Shaft>/<Thick>: "x,y,z" in skeleton rest space as Arms.cs Sockets writes them; "old" keeps the row in
arms_local.json. Rebuilds each key's mount as Arms.Sheathed does (Mirrors for @hand_l), then per clip: the nearest
hand skin (hand, fingers, thumb and the forearm within 8 cm of the wrist) to the piece's head (its points above
--head m along the shaft from the sheath point: the axe's blade and haft top; the wand's crystal end) and to the whole
piece (mm, l/r, and the frame), and the piece's worst depth into her skin (mm, armscheck's measure, pushed out by the
outfit's clearance fitted at the new socket on idle_warden frame 0 as armscheck --sockets does). --write: an
arms_local.json with the new mounts (for armscheck --arms)."""
import json, sys, math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[3] / "tools" / "anim"
sys.path.insert(0, str(HERE))
import armscheck as ac  # noqa

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
sock, row, clips = args[0], args[1], args[2:]
outfit = opt.get("outfit", "reaver")
step = int(opt.get("step", 1))
headmin = float(opt.get("head", 0.42))
REST = {"pelvis": (20.6, (0, 1.0723, 0)), "spine_03": (-18.4, (0, 1.3335, 0.0364))}


def rest(bone):
    a, o = REST[bone]
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    M = np.eye(4)
    M[:3, :3] = [[1, 0, 0], [0, c, -s], [0, s, c]]
    M[:3, 3] = o
    return M


def mount(bone, at, shaft, thick, left, pistol=False, edge=False):
    at, shaft, thick = (np.array(v, float) for v in (at, shaft, thick))
    if left:
        at[0], shaft[0], thick[0] = -at[0], -shaft[0], -thick[0]
        if edge:
            thick = -thick   # Arms.cs Socket MirrorEdge
    shaft /= np.linalg.norm(shaft)
    thick = thick - shaft * thick.dot(shaft)
    thick /= np.linalg.norm(thick)
    third = np.cross(shaft, thick)
    S = np.eye(4)
    S[:3, :3] = np.column_stack([shaft, thick, np.cross(shaft, thick)] if pistol else [third, shaft, thick])
    S[:3, 3] = at
    return np.linalg.inv(rest(bone)) @ S


raw = json.loads((ac.DATA / "arms_local.json").read_text())
keys = opt.get("keys", "").split(",") if opt.get("keys") else [k for k, d in raw["sheathed"].items() if d["socket"] == sock]
parts = None if row == "old" else [[float(x) for x in p.split(",")] for p in row.split(";")]
new = {}
for k in keys:
    d = raw["sheathed"][k]
    M0 = np.vstack([np.array(d["mount"], float), [0, 0, 0, 1]])
    v = np.array(d["v"], float)
    u = (np.linalg.inv(M0) @ np.c_[v, np.ones(len(v))].T).T[:, :3]
    M1 = M0 if parts is None else mount(d["bone"], *parts, left=k.endswith("@hand_l"), pistol=k.startswith("crossbow"), edge=sock == "hip_loop")
    new[k] = dict(d, mount=M1[:3].tolist(), v=((M1 @ np.c_[u, np.ones(len(u))].T).T[:, :3]).tolist(), u=u)
if "write" in opt:
    out = json.loads(json.dumps(raw))
    for k, d in new.items():
        out["sheathed"][k].update(mount=d["mount"], v=d["v"])
    Path(opt["write"]).write_text(json.dumps(out))
tmp = Path(__file__).with_name("socktry_arms.json")
out = {"sheathed": {k: {kk: vv for kk, vv in d.items() if kk != "u"} for k, d in new.items()}}
tmp.write_text(json.dumps(out))
ck = ac.SocketChecker(outfit if outfit != "none" else "none", str(tmp))
b, I = ck.b, ck.I
clr = ck.fit(b.frames(b.clip("idle_warden"))[0])
vb = ck.vbone
FING = ("index", "middle", "ring", "pinky", "thumb")
HAND = {s: np.array([n.endswith("_" + s) and (n.startswith("hand") or n.split("_")[0] in FING) for n in vb]) for s in "lr"}
FORE = {s: vb == f"lowerarm_{s}" for s in "lr"}
for k, d in new.items():
    M = np.array(d["mount"])
    print(f"{k}: mount origin {np.round(M[:, 3], 3)}  clearance {1000 * clr.get(d['socket'], 0):.1f} mm  "
          f"head pts y>{headmin}: {(d['u'][:, 1] > headmin).sum()}")
for name in clips:
    Gs = b.frames(b.clip(name))
    for k, d in ck.sheathed.items():
        push = d["normal"] * clr.get(d["socket"], 0.0)
        pts = ck.pts_s[k] + push
        um = (np.linalg.inv(np.vstack([d["mount"], [0, 0, 0, 1]])) @ np.c_[ck.pts_s[k], np.ones(len(pts))].T).T
        head = um[:, 1] > headmin
        best = {s: [9e9, -1, 9e9, -1] for s in "lr"}
        deep, df, dpart = 0.0, -1, ""
        for f in range(0, len(Gs), step):
            G = Gs[f]
            P = b.pose(G)
            Mb = G[I[d["bone"]]]
            Q = pts @ Mb[:3, :3].T + Mb[:3, 3]
            th, ta = cKDTree(Q[head]), cKDTree(Q)
            for s in "lr":
                hj = G[I[f"hand_{s}"]][:3, 3]
                hv = P[HAND[s] | (FORE[s] & (np.linalg.norm(P - hj, axis=1) < 0.08))]
                dh = th.query(hv)[0].min()
                da = ta.query(hv)[0].min()
                if dh < best[s][0]:
                    best[s][0:2] = [dh, f]
                if da < best[s][2]:
                    best[s][2:4] = [da, f]
            ck.body.pose(P)
            keep, near, _ = ck.measure(P, ck.body, Q)
            j = int(keep.argmax())
            if keep[j] > deep:
                deep, df, dpart = float(keep[j]), f, vb[near[j]]
        print(f"{name:26} {k:20} head l {1000 * best['l'][0]:4.0f} (f{best['l'][1]}) r {1000 * best['r'][0]:4.0f} (f{best['r'][1]}) | "
              f"piece l {1000 * best['l'][2]:4.0f} r {1000 * best['r'][2]:4.0f} mm | into skin {deep:.1f} mm" + (f" f{df} {dpart}" if deep > 0 else ""))
