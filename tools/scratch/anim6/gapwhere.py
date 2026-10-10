"""Where skin comes through a garment in one pose: the inside points grouped
by garment piece and by the bone holding most of their weight, before the
helpers and with them.

    python -u gapwhere.py <outfit> "<pose>" [min depth mm]    (WTB=<worktree> reads another build)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
import gapcheck as gc  # noqa: E402
import motion  # noqa: E402
from sweep import pose  # noqa: E402

if os.environ.get("WTB"):
    gc.WT = Path(os.environ["WTB"])

outfit, pname = sys.argv[1], sys.argv[2]
mind = float(sys.argv[3]) / 1000 if len(sys.argv) > 3 else 0.0
for which in ("before", "after"):
    b = gc.load(which, outfit)
    skin = np.nonzero(b.kind == "skin")[0]
    gar = np.nonzero(b.kind == "garment")[0]
    T = b.T[np.isin(b.T[:, 0], skin)]
    surf = motion.Surface(T, len(b.P))
    surf.pose(b.P)
    d_rest, _ = surf.signed(b.P, b.P[gar])
    G = pose(b, gc.POSES[pname])
    P = b.pose(G)
    surf.pose(P)
    d, _ = surf.signed(P, P[gar])
    ok = np.isfinite(d) & np.isfinite(d_rest) & (d_rest > 0.0005)
    ins = ok & (d < -mind)
    g = gar[ins]
    top = b.J[g, 0]
    # nearest skin point at rest, and its top bone / helper share
    tree = cKDTree(b.P[skin])
    dist0, ns = tree.query(b.P[g], k=1)
    ns = skin[ns]
    print(f"== {outfit} {which} {pname}: {ins.sum()} points deeper than {mind*1000:.1f} mm")
    keys = {}
    for i, gi in enumerate(g):
        k = (b.piece[gi], b.sk.names[top[i]])
        keys.setdefault(k, []).append(i)
    for k, ii in sorted(keys.items(), key=lambda kv: -len(kv[1]))[:12]:
        ii = np.array(ii)
        dd = -d[ins][ii] * 1000
        c = b.P[g[ii]].mean(0)
        nsb = b.sk.names[b.J[ns[ii[np.argmax(dd)]], 0]]
        wsum = b.W[g[ii]].sum(1).mean()
        w4 = b.W[g[ii], 3].mean()
        print(f"  {k[0]:28s} {k[1]:22s} n={len(ii):5d} deepest {dd.max():5.1f} median {np.median(dd):4.1f} mm  "
              f"rest gap {np.median(d_rest[ins][ii])*1000:4.1f} mm  at ({c[0]:+.3f},{c[1]:.3f},{c[2]:+.3f})  "
              f"deepest's skin bone {nsb}  4th weight {w4:.3f}")
