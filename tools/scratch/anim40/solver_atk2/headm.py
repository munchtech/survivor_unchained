"""anim41 solver 2: per frame, her face and chest. python headm.py CLIP [--play IDLE] [--folder DIR] [--cam 45] [--pitch 20]
face el: the face's direction above level (deg, + up); face.cam: its dot with the way to the camera (1 = faces it);
chest: spine_03's lean from upright (deg, + forward); head-chest: the head's pitch against the chest (deg, + down)."""
import sys, math, argparse
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa
from rig import qinv, qmul, qrot  # noqa
ap = argparse.ArgumentParser()
ap.add_argument('clip'); ap.add_argument('--play'); ap.add_argument('--folder')
ap.add_argument('--cam', type=float, default=45); ap.add_argument('--pitch', type=float, default=20)
a = ap.parse_args()
label, folder, skel = A.SETS[0]
folder = Path(a.folder) if a.folder else folder
sk = A.Skeleton.load(A.DATA / skel); I = sk.index
d, rot, pos = A.load(folder / f'{a.clip}.json', sk)
if a.play:
    _, ir, ip = A.load(ANIM / 'out/clips' / f'{a.play}.json', sk)
    for name, j in I.items():
        if name in ('root', 'pelvis') or name.startswith(('thigh', 'calf', 'foot', 'ball', 'glute')):
            rot[:, j] = ir[0, j]; pos[:, j] = ip[0, j]
g, p = sk.fk(rot, pos)
gr, pr = sk.rest_globals(); gr, pr = gr[0], pr[0]
hd, s3 = I['Head'], I['spine_03']
face_l = qrot(qinv(gr[hd]), np.array([0, 0, 1.0]))
up3 = qrot(qinv(gr[s3]), np.array([0, 1.0, 0]))
fwd3 = qrot(qinv(gr[s3]), np.array([0, 0, 1.0]))
ca, cp = math.radians(a.cam), math.radians(a.pitch)
cam = np.array([math.sin(ca) * math.cos(cp), math.sin(cp), math.cos(ca) * math.cos(cp)])
print(f"{a.clip} {'play over ' + a.play if a.play else 'own'}: f  face_el face.cam  chest_lean  head-chest  head_h(cm)")
for f in range(rot.shape[0]):
    rq = qmul(g[f, I['root']], qinv(gr[I['root']]))
    fc = qrot(qinv(rq), qrot(g[f, hd], face_l))
    u3 = qrot(qinv(rq), qrot(g[f, s3], up3)); f3 = qrot(qinv(rq), qrot(g[f, s3], fwd3))
    el = math.degrees(math.asin(max(-1, min(1, fc[1]))))
    lean = math.degrees(math.atan2(u3[2], u3[1]))
    cel = math.degrees(math.asin(max(-1, min(1, f3[1]))))
    hh = (p[f, hd] - p[f, I['root']])[1] * 100
    print(f"{f:3d} {el:7.0f} {fc @ cam:7.2f} {lean:9.0f} {cel - el:10.0f} {hh:9.0f}")
