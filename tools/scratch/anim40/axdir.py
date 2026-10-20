"""anim41: per frame, the hand's height and the axe head's direction (world, Y up?) for a clip."""
import sys, json, numpy as np
sys.path.insert(0, '.')
import audit as A
from pathlib import Path
label, folder, skel = A.SETS[0]
sk = A.Skeleton.load(A.DATA/skel); I = sk.index
arms = json.load(open('data/arms_local.json'))
clip, key, bone = sys.argv[1], sys.argv[2], sys.argv[3]
d, rot, pos = A.load(Path(f'out/clips/{clip}.json'), sk); g, p = sk.fk(rot, pos)
v = np.array(arms[key]['v']); r = np.linalg.norm(v, axis=1); far = v[r > r.max()-0.12].mean(0)
h = I[bone]
for f in range(rot.shape[0]):
    hp = p[f, h]; head = hp + A.qrot(g[f, h], far); dv = (head-hp)/np.linalg.norm(head-hp)
    print(f, 'hand', np.round((hp - p[f, I['pelvis']])*100).astype(int), 'axe dir', np.round(dv, 2), 'head-of-axe height cm', round((head[1]-p[f, I['pelvis']][1])*100))
