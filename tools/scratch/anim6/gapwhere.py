"""Where skin comes through a garment in one pose with the helpers and not
before (new), and the reverse (cured): grouped by garment piece and top bone,
with where they sit against the nearest knee or elbow at rest (dz > 0: in
front of the joint; dy: above it).

    python -u gapwhere.py <outfit> "<pose>" [min depth mm]    (WTB=<worktree> reads another build)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import gapcheck as gc  # noqa: E402
import motion  # noqa: E402
from sweep import pose  # noqa: E402

if os.environ.get("WTB"):
    gc.WT = Path(os.environ["WTB"])

outfit, pname = sys.argv[1], sys.argv[2]
mind = float(sys.argv[3]) / 1000 if len(sys.argv) > 3 else 0.0
R = {}
for which in ("before", "after"):
    b = gc.load(which, outfit)
    skin = np.nonzero(b.kind == "skin")[0]
    gar = np.nonzero(b.kind == "garment")[0]
    T = b.T[np.isin(b.T[:, 0], skin)]
    surf = motion.Surface(T, len(b.P))
    surf.pose(b.P)
    d_rest, _ = surf.signed(b.P, b.P[gar])
    P = b.pose(pose(b, gc.POSES[pname]))
    surf.pose(P)
    d, _ = surf.signed(P, P[gar])
    ok = np.isfinite(d) & np.isfinite(d_rest) & (d_rest > 0.0005)
    R[which] = (b, gar, ok & (d < -mind), d)
b, gar, ia, da = R["after"]
_, _, ib, db = R["before"]
joints = {n: b.rest[b.sk.index[n]][:3, 3] for n in ("calf_l", "calf_r", "lowerarm_l", "lowerarm_r")}
J = np.array(list(joints.values()))
for label, m, d in (("new", ia & ~ib, da), ("cured", ib & ~ia, db)):
    g = gar[m]
    print(f"== {outfit} {pname}: {label} {m.sum()} points (deeper than {mind*1000:.1f} mm)")
    if not m.any():
        continue
    near = np.argmin(((b.P[g][:, None, :] - J[None]) ** 2).sum(2), 1)
    off = b.P[g] - J[near]
    keys = {}
    for i, gi in enumerate(g):
        keys.setdefault((b.piece[gi], list(joints)[near[i]]), []).append(i)
    for k, ii in sorted(keys.items(), key=lambda kv: -len(kv[1]))[:8]:
        ii = np.array(ii)
        dd = -d[m][ii] * 1000
        print(f"  {k[0]:26s} near {k[1]:11s} n={len(ii):5d} deepest {dd.max():5.1f} median {np.median(dd):4.1f} mm  "
              f"in front {np.mean(off[ii, 2] > 0):.2f}  dz {np.median(off[ii, 2])*100:+5.1f} dy {np.median(off[ii, 1])*100:+5.1f} cm  "
              f"dist {np.median(np.linalg.norm(off[ii], axis=1))*100:4.1f} cm")
