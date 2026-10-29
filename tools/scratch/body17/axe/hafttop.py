"""Arms.HaftTop's twin on the dump's vertices (mount space), the grip window put at a few heights (Body 17)."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "anim"))
import armscheck as ac
r = json.loads((ac.DATA / "arms_local.json").read_text())["sheathed"]
for k in sys.argv[1:]:
    d = r[k]; A = np.vstack([np.array(d["mount"]), [0, 0, 0, 1]]); v = np.array(d["v"], float)
    q = (np.linalg.inv(A) @ np.c_[v, np.ones(len(v))].T).T[:, :3]
    tip = q[:, 1].max()
    for g in (-0.05, 0.0, 0.1, 0.2):
        w = q[np.abs(q[:, 1] - g) < 0.04]
        cx, cz = (w[:, 0].min() + w[:, 0].max()) / 2, (w[:, 2].min() + w[:, 2].max()) / 2
        rr = max(np.ptp(w[:, 0]), np.ptp(w[:, 2])) / 2; rim = 1.5 * rr + 0.005
        dd = np.hypot(q[:, 0] - cx, q[:, 2] - cz)
        m = (q[:, 1] > g + 0.10) & (dd > rim) & (dd < 0.10)
        top = q[m, 1].min() if m.any() else tip - 0.12
        s = q[(q[:, 1] >= top - 0.08) & (q[:, 1] <= top - 0.005) & (dd <= rim)]
        print(f"{k} grip@{g:+.2f}: axis ({cx:+.4f},{cz:+.4f}) r {rr:.4f} top {top:.4f} half {np.abs(s[:,0]-cx).max() if len(s) else 0:.4f} {np.abs(s[:,2]-cz).max() if len(s) else 0:.4f} n{len(s)}")
