"""anim41 solver: per frame, a held piece and both hands, on the clip's own legs or play-true.

  python atkm.py CLIP [--play IDLE] [--folder DIR] [--key viking_axe@hand_r] [--cam 45] [--pitch 20] [--frames a-b]

--play IDLE: her root, pelvis and legs from IDLE's frame 0 (PlayerView --hold's upperShot), as play shows an upper clip.
Columns (cm, her frame: x her left, y up, z forward, from her pelvis): the right and left wrists; the piece's head
(centre of its far end); its direction; |flat . camera| (1 = the head's flat faces the camera, 0 = edge-on);
the piece's angle on screen (deg: 0 right, 90 up, -90 down); edge.velocity (+ = the edge leads).
Camera: --cam degrees round from her front toward her left, --pitch degrees down (0.6 zoom about 20)."""
import sys, json, math, argparse
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa

LEGS = ('root', 'pelvis', 'thigh', 'calf', 'foot', 'ball', 'glute')
ap = argparse.ArgumentParser()
ap.add_argument('clip'); ap.add_argument('--play'); ap.add_argument('--folder')
ap.add_argument('--key', default='viking_axe@hand_r'); ap.add_argument('--cam', type=float, default=45)
ap.add_argument('--pitch', type=float, default=20); ap.add_argument('--frames')
a = ap.parse_args()
label, folder, skel = A.SETS[0]
folder = Path(a.folder) if a.folder else folder
sk = A.Skeleton.load(A.DATA / skel); I = sk.index
arms = json.load(open(ANIM / 'data/arms_local.json'))
d, rot, pos = A.load(folder / f'{a.clip}.json', sk)
if a.play:
    _, ir, ip = A.load(ANIM / 'out/clips' / f'{a.play}.json', sk)
    for name, j in I.items():
        if name in ('root', 'pelvis') or name.startswith(LEGS[2:]):
            rot[:, j] = ir[0, j]; pos[:, j] = ip[0, j]
g, p = sk.fk(rot, pos)
key = a.key; bone = key.split('@')[1]; h = I[bone]
v = np.array(arms[key]['v']); r = np.linalg.norm(v, axis=1)
far = v[r > r.max() - 0.12]; head_l = far.mean(0)
hd = head_l / np.linalg.norm(head_l)
mid = v[(r > 0.05) & (r < 0.35)]; m0 = mid.mean(0); ax = np.linalg.svd(mid - m0)[2][0]; ax = ax if ax @ hd > 0 else -ax
off = far - m0; off = off - np.outer(off @ ax, ax); edge_l = off.mean(0); edge_l /= np.linalg.norm(edge_l)
flat_l = np.cross(ax, edge_l); flat_l /= np.linalg.norm(flat_l)
ca, cp = math.radians(a.cam), math.radians(a.pitch)
cam = np.array([math.sin(ca) * math.cos(cp), math.sin(cp), math.cos(ca) * math.cos(cp)])
right = np.cross(-cam, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, -cam)
fr = range(rot.shape[0])
if a.frames:
    s, e = a.frames.split('-'); fr = range(int(s), int(e) + 1)
heads = np.array([p[f, h] + A.qrot(g[f, h], head_l) for f in range(rot.shape[0])])
print(f"{d['name']} {'play-true over ' + a.play if a.play else 'own legs'}; cam {a.cam:.0f} pitch {a.pitch:.0f}")
print(' f   hand_r(cm)      hand_l(cm)      head(cm)         dir               flat.cam scr  edge.v  scr: hand_r  head  hand_l')
for f in fr:
    pv = p[f, I['pelvis']]
    hr, hl = (p[f, I['hand_r']] - pv) * 100, (p[f, I['hand_l']] - pv) * 100
    hp = p[f, h]; head = heads[f]; dv = (head - hp) / np.linalg.norm(head - hp)
    flat = A.qrot(g[f, h], flat_l); edge = A.qrot(g[f, h], edge_l)
    scr = math.degrees(math.atan2(dv @ up, dv @ right))
    vel = heads[min(f + 1, len(heads) - 1)] - heads[max(f - 1, 0)]
    ev = float(edge @ vel / (np.linalg.norm(vel) + 1e-9))
    print(f"{f:2d} {np.round(hr).astype(int)!s:15} {np.round(hl).astype(int)!s:15} {np.round((head - pv) * 100).astype(int)!s:16} "
          f"{np.round(dv, 2)!s:17} {abs(flat @ cam):5.2f} {scr:6.0f} {ev:6.2f}  "
          + "  ".join(f"({x @ right:4.0f},{x @ up:4.0f})" for x in (hr, (head - pv) * 100, hl)))
