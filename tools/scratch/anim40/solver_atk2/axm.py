"""anim41 solver 2: the axe in chain_strike per frame. python axm.py CLIP [--folder DIR] [--cam 45] [--pitch 20]
low: the axe's lowest vertex above the ground (cm, her root; - = in the ground); hc: the head's centre height;
dir: the haft's way (her space: x left, y up, z fwd); yaw: the haft's yaw toward her left (deg); pitch: below level;
flat.cam: |the blade's flat . the way to the camera| (1 = faces it); face_el, face.cam: her face (headm.py's)."""
import sys, json, math, argparse
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa
from rig import qinv, qmul, qrot  # noqa
ap = argparse.ArgumentParser()
ap.add_argument('clip'); ap.add_argument('--folder'); ap.add_argument('--cam', type=float, default=45)
ap.add_argument('--pitch', type=float, default=20); ap.add_argument('--key', default='viking_axe@hand_r')
a = ap.parse_args()
label, folder, skel = A.SETS[0]
folder = Path(a.folder) if a.folder else folder
sk = A.Skeleton.load(A.DATA / skel); I = sk.index
arms = json.load(open(ANIM / 'data/arms_local.json'))
d, rot, pos = A.load(folder / f'{a.clip}.json', sk)
g, p = sk.fk(rot, pos)
gr, pr = sk.rest_globals(); gr, pr = gr[0], pr[0]
bone = a.key.split('@')[1]; h = I[bone]
v = np.array(arms[a.key]['v']); r = np.linalg.norm(v, axis=1)
far = v[r > r.max() - 0.12]; head_l = far.mean(0); hd = head_l / np.linalg.norm(head_l)
mid = v[(r > 0.05) & (r < 0.35)]; m0 = mid.mean(0); ax = np.linalg.svd(mid - m0)[2][0]; ax = ax if ax @ hd > 0 else -ax
off = far - m0; off = off - np.outer(off @ ax, ax); edge_l = off.mean(0); edge_l /= np.linalg.norm(edge_l)
flat_l = np.cross(ax, edge_l); flat_l /= np.linalg.norm(flat_l)
ca, cp = math.radians(a.cam), math.radians(a.pitch)
cam = np.array([math.sin(ca) * math.cos(cp), math.sin(cp), math.cos(ca) * math.cos(cp)])
H = I['Head']; face_l = qrot(qinv(gr[H]), np.array([0, 0, 1.0]))
print(f"{a.clip}: f  low  hc   dir(x,y,z)          yaw pitch flat.cam  face_el face.cam  hand_l-haft(cm)")
for f in range(rot.shape[0]):
    rq = qmul(g[f, I['root']], qinv(gr[I['root']])); iv = qinv(rq); r0 = p[f, I['root']]
    loc = lambda x: qrot(iv, x)
    pts = np.array([loc(p[f, h] + qrot(g[f, h], x) - r0) for x in v])
    head = loc(p[f, h] + qrot(g[f, h], head_l) - r0); hp = loc(p[f, h] - r0)
    axw = loc(qrot(g[f, h], ax)); fl = loc(qrot(g[f, h], flat_l))
    yaw = math.degrees(math.atan2(axw[0], axw[2])); pit = -math.degrees(math.asin(max(-1, min(1, axw[1]))))
    fc = loc(qrot(g[f, H], face_l)); el = math.degrees(math.asin(max(-1, min(1, fc[1]))))
    hl = loc(p[f, I['hand_l']] - r0); base = loc(p[f, h] + qrot(g[f, h], m0) - r0)
    dl = hl - base; dl = dl - axw * (dl @ axw)
    print(f"{f:3d} {pts[:, 1].min() * 100:5.0f} {head[1] * 100:4.0f} {np.round(axw, 2)!s:19} {yaw:5.0f} {pit:5.0f} {abs(fl @ cam):6.2f}"
          f" {el:8.0f} {fc @ cam:7.2f} {np.linalg.norm(dl) * 100:9.1f}")
