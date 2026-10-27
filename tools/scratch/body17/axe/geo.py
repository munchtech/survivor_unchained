import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "anim"))
import armscheck as ac
r = json.loads((ac.DATA / "arms_local.json").read_text())["sheathed"]
d = r["viking_axe@hand_r"]; A = np.vstack([np.array(d["mount"]), [0, 0, 0, 1]]); v = np.array(d["v"], float)
q = (np.linalg.inv(A) @ np.c_[v, np.ones(len(v))].T).T[:, :3]
print("n", len(q), "y", q[:,1].min(), q[:,1].max())
for y0 in np.arange(0.50, q[:,1].max()+0.01, 0.02):
    w = q[(q[:,1]>=y0)&(q[:,1]<y0+0.02)]
    if len(w): print(f"y {y0:.2f}: x {w[:,0].min():+.3f}..{w[:,0].max():+.3f} z {w[:,2].min():+.3f}..{w[:,2].max():+.3f} n{len(w)}")
