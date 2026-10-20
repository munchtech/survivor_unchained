"""|axe flat . camera| per frame (camera 45 deg off her front to her left, 20 up), head height (cm), face pitch"""
import sys, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A
from rig import qmatrix
import clips.arts as M
sk = A.Skeleton.load(A.DATA / A.SETS[0][2]); I = sk.index
d, rot, pos = A.load(Path(sys.argv[1]) / 'chain_strike.json', sk); g, p = sk.fk(rot, pos)
C, H, N, Wd = M._haft()
ca, cp = math.radians(45), math.radians(20)
cam = np.array([math.sin(ca) * math.cos(cp), math.sin(cp), math.cos(ca) * math.cos(cp)])
out = []
for f in range(1, 13):
    R = qmatrix(g[f, I['hand_r']]); n = R @ N; h = R @ H
    out.append(f"{f}:{abs(n @ cam):.2f}/{math.degrees(math.asin(-h[1] / np.linalg.norm(h))):.0f}")
print('flat/haftpitch', ' '.join(out))
