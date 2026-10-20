"""per-frame arm rows: python au2.py FOLDER CLIP side a-b"""
import sys
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
import audit as A
from audit import swing_twist, wrist_bend, angle, qmul, qinv, qrot
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
d, rot, pos = A.load(Path(sys.argv[1]) / f'{sys.argv[2]}.json', sk); g, p = sk.fk(rot, pos)
s = sys.argv[3]; a, b = map(int, sys.argv[4].split('-'))
fa, h = I[f"lowerarm_{s}"], I[f"hand_{s}"]; mid = I[f"middle_01_{s}"]
fa_axis = sk.rest_pos[h] / np.linalg.norm(sk.rest_pos[h]); h_axis = sk.rest_pos[mid] / np.linalg.norm(sk.rest_pos[mid])
print('f  step stepfa fa_tw h_tw rollh rollfa flex dev')
for f in range(a, b + 1):
    dfa = qmul(qinv(sk.rest_rot[fa]), rot[f, fa]); dh = qmul(qinv(sk.rest_rot[h]), rot[f, h])
    _, fa_tw = swing_twist(dfa, fa_axis); h_sw, h_tw = swing_twist(dh, h_axis)
    step = angle(g[f, h], g[f - 1, h]) if f else 0; sfa = angle(g[f, fa], g[f - 1, fa]) if f else 0
    rh = rf = 0
    if f:
        ax = qrot(g[f, h], h_axis); rh = abs(swing_twist(qmul(g[f, h], qinv(g[f - 1, h])), ax / np.linalg.norm(ax))[1])
        ax = qrot(g[f, fa], fa_axis); rf = abs(swing_twist(qmul(g[f, fa], qinv(g[f - 1, fa])), ax / np.linalg.norm(ax))[1])
    fl, dv = wrist_bend(dh, h_axis, s)
    print(f"{f:2d} {step:5.0f} {sfa:5.0f} {fa_tw:6.0f} {h_tw:5.0f} {rh:5.0f} {rf:5.0f} {fl:5.0f} {dv:4.0f}")
