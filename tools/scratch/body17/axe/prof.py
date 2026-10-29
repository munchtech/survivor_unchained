"""Profile a sheathed piece along its mount +Y (Body 17): per 1 cm slice the X/Z extent and centre (mount space)."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "anim"))
import armscheck as ac
r = json.loads((ac.DATA / "arms_local.json").read_text())["sheathed"]
for k in sys.argv[1:]:
    d = r[k]; A = np.vstack([np.array(d["mount"]), [0, 0, 0, 1]])
    v = np.array(d["v"], float)
    m = (np.linalg.inv(A) @ np.c_[v, np.ones(len(v))].T).T[:, :3]
    print(k, "y", m[:, 1].min().round(3), m[:, 1].max().round(3), "mount", np.round(A[:3], 3).tolist())
    for y in np.arange(m[:, 1].min(), m[:, 1].max(), 0.01):
        s = m[(m[:, 1] >= y) & (m[:, 1] < y + 0.01)]
        if len(s): print(f" y {y:+.3f} n {len(s):4d} x {s[:,0].min():+.3f}..{s[:,0].max():+.3f} z {s[:,2].min():+.3f}..{s[:,2].max():+.3f}")
