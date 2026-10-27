"""Sampled-surface profile of a sheathed piece along mount +Y, plus the hang pivot in mount space (Body 17)."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "anim"))
import armscheck as ac
r = json.loads((ac.DATA / "arms_local.json").read_text())["sheathed"]
PV = np.array([-0.110, 1.06, -0.190])
c, s = np.cos(np.radians(20.6)), np.sin(np.radians(20.6))
REST = np.eye(4); REST[:3, :3] = [[1, 0, 0], [0, c, -s], [0, s, c]]; REST[:3, 3] = (0, 1.0723, 0)
k = sys.argv[1]; y0, y1 = float(sys.argv[2]), float(sys.argv[3])
d = r[k]; A = np.vstack([np.array(d["mount"]), [0, 0, 0, 1]])
p = ac.sample(np.array(d["v"], float), np.array(d["t"], int))
m = (np.linalg.inv(A) @ np.c_[p, np.ones(len(p))].T).T[:, :3]
pv = PV.copy()
if k.endswith("@hand_l"): pv[0] = -pv[0]
print("pivot mount", np.round((np.linalg.inv(A) @ np.linalg.inv(REST) @ np.r_[pv, 1])[:3], 3))
for y in np.arange(y0, y1, 0.01):
    s_ = m[(m[:, 1] >= y) & (m[:, 1] < y + 0.01)]
    near = s_[np.abs(s_[:, 0]) < 0.06]
    if len(s_): print(f" y {y:+.3f} n {len(s_):4d} x {s_[:,0].min():+.3f}..{s_[:,0].max():+.3f} z {s_[:,2].min():+.3f}..{s_[:,2].max():+.3f}" + (f" | |x|<6cm x {near[:,0].min():+.3f}..{near[:,0].max():+.3f} z {near[:,2].min():+.3f}..{near[:,2].max():+.3f}" if len(near) else ""))
