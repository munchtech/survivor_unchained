"""solver 7a: the idle (left) axe in axes_right, standing (whole clip). python la.py frames(comma) [clip]
hl = left hand from the left shoulder (upperarm_l) cm (x her left, y up, z fwd); haft = hand->axe head: from vertical (deg),
lean az (deg, 0 fwd, 90 her left); hdz = head height above shoulder cm."""
import sys, json, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
import audit as A
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
arms = json.load(open(ANIM / 'data/arms_local.json'))
v = np.array(arms['viking_axe@hand_l']['v']); r = np.linalg.norm(v, axis=1); far = v[r > r.max() - 0.12].mean(0)
_, rot, pos = A.load(ANIM / 'out/clips' / f'{sys.argv[2] if len(sys.argv) > 2 else "axes_right"}.json', sk)
g, p = sk.fk(rot, pos)
for f in map(int, sys.argv[1].split(',')):
    J = lambda n: p[f, I[n]]
    hl = (J('hand_l') - J('upperarm_l')) * 100
    hd = A.qrot(g[f, I['hand_l']], far); d = hd / np.linalg.norm(hd)
    print(f"f{f}: hl {np.round(hl).astype(int)} haft vert {math.degrees(math.acos(d[1])):4.0f} az {math.degrees(math.atan2(d[0], d[2])):5.0f} hdz {(J('hand_l')[1]+hd[1]-J('upperarm_l')[1])*100:4.0f}")
