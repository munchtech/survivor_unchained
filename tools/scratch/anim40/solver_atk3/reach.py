"""chain_strike: per frame, the left wrist's target on the haft vs her left shoulder (reach, % of arm), and the wrist
bend the target needs: angle between the forearm-ish line (elbow->target) and the target hand's +Y. reach.py FOLDER"""
import sys, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa
from rig import qmatrix
import clips.arts as M
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
d, rot, pos = A.load(Path(sys.argv[1]) / 'chain_strike.json', sk)
g, p = sk.fk(rot, pos)
R_lr, o_lr = M._left_on_haft()
for f in range(2, 11):
    Rr = qmatrix(g[f, I['hand_r']]); T = Rr @ R_lr; W = p[f, I['hand_r']] + Rr @ o_lr
    sh = p[f, I['upperarm_l']]; v = W - sh
    pv = p[f, I['pelvis']]
    print(f"{f:2d} reach {np.linalg.norm(v)/0.518*100:4.0f}%  target-from-shoulder(cm) {np.round(v*100).astype(int)}  "
          f"actual {np.round((p[f, I['hand_l']]-sh)*100).astype(int)}  hand_r {np.round((p[f, I['hand_r']]-pv)*100).astype(int)} shR {np.round((p[f, I['upperarm_r']]-pv)*100).astype(int)}")
