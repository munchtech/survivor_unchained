"""anim41 solver 2: chain_strike's left fist against its place on the haft (arts._left_on_haft), per frame.
  python lfit.py [--folder DIR] [--frames a-b]
off: the fist's channel point from the haft's line (mm); tilt: its channel from the haft's way (deg);
roll: its turn about the haft from where it belongs (deg); err: the whole turn off (deg); slide: along the haft (mm)."""
import sys, argparse, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa
from rig import qmatrix  # noqa
import clips.arts as M  # noqa
ap = argparse.ArgumentParser(); ap.add_argument('--folder'); ap.add_argument('--frames', default='0-15')
a = ap.parse_args()
label, folder, skel = A.SETS[0]
folder = Path(a.folder) if a.folder else folder
sk = A.Skeleton.load(A.DATA / skel); I = sk.index
d, rot, pos = A.load(folder / 'chain_strike.json', sk)
g, p = sk.fk(rot, pos)
C, H, N, Wd = M._haft(); R_lr, o_lr = M._left_on_haft()
c, hl_, n_ = M.L_CHANNEL; hl_ = hl_ / np.linalg.norm(hl_)
s, e = (int(x) for x in a.frames.split('-'))
print(' f   off  tilt  roll   err  slide')
for f in range(s, e + 1):
    Rr = qmatrix(g[f, I['hand_r']]); Rl = qmatrix(g[f, I['hand_l']])
    T = Rr @ R_lr; Tw = p[f, I['hand_r']] + Rr @ o_lr
    E = Rl.T @ T; err = math.degrees(math.acos(max(-1, min(1, (np.trace(E) - 1) / 2))))
    hw = Rr @ H; cpt = p[f, I['hand_l']] + Rl @ c; cpt0 = Tw + T @ c
    dv = cpt - (p[f, I['hand_r']] + Rr @ C); off = np.linalg.norm(dv - hw * (dv @ hw))
    tilt = math.degrees(math.acos(min(1, abs((Rl @ hl_) @ hw))))
    nn = Rl @ n_; nt = T @ n_
    nn = nn - hw * (nn @ hw); nt = nt - hw * (nt @ hw)
    roll = math.degrees(math.atan2(np.cross(nt, nn) @ hw, nt @ nn))
    print(f"{f:2d} {off * 1000:5.1f} {tilt:5.1f} {roll:5.1f} {err:5.1f} {(cpt - cpt0) @ hw * 1000:6.1f}")
