"""THE BOUNDED TUCK's numbers (armor 7): before and after fields of her skin's tuck, from tuck_probe.py's probe.npz or
piece_blender.py's ARMOR_SCRATCH_ONLY tuck_probe.npz pairs.

    python tools/armor/tuck_measure.py probe <probe.npz>                 (an outfit: its channel and its slot)
    python tools/armor/tuck_measure.py piece <before.npz> <after.npz>    (a piece: two runs, TUCK_SMOOTH 0 and 1)

Per field: the neighbour depth step over the footprint (mm, max and p99; her split copies at one point count as
neighbours), left vs mirrored right along both cups' inner rims (|x| < 7 cm, height 1.25-1.45 m, front, within
12 mm of the footprint's border), and the points tucked whose ray met the piece at a graze (|cos| < 0.5).
"""
import sys

import numpy as np
from scipy.spatial import cKDTree


def depth(t):
    return 10.0 * np.where(t > 0.973, 1.0, t)


def stats(name, bv, edges, co_local, t, cos, ref_fp):
    gl = np.stack([bv[:, 0], bv[:, 2], -bv[:, 1]], 1)
    fp = ref_fp
    d = depth(t)
    _, gid = np.unique(np.round(co_local / 1e-6).astype(np.int64), axis=0, return_inverse=True)
    gid = np.asarray(gid).ravel()
    o = np.argsort(gid)
    same = np.nonzero(np.diff(gid[o]) == 0)[0]
    pairs = np.vstack([edges, np.stack([o[same], o[same + 1]], 1)])
    m = fp[pairs[:, 0]] | fp[pairs[:, 1]]
    st = np.abs(d[pairs[m, 0]] - d[pairs[m, 1]])
    hard = t > 0.973
    sst = np.abs(d[pairs[m & ~hard[pairs[:, 0]] & ~hard[pairs[:, 1]], 0]] - d[pairs[m & ~hard[pairs[:, 0]] & ~hard[pairs[:, 1]], 1]])
    # (the cups' inner rims: front, middle, the footprint's border band)
    reg = (np.abs(gl[:, 0]) < 0.07) & (gl[:, 1] > 1.25) & (gl[:, 1] < 1.45) & (gl[:, 2] > 0)
    outside = ~fp
    dout = cKDTree(gl[outside]).query(gl)[0]
    rim = reg & fp
    L = np.nonzero(rim & (gl[:, 0] > 0.003))[0]
    # (her mesh is not exactly mirrored: the right side's value at the mirrored point, from its 4 nearest within 15 mm)
    dm, jm = cKDTree(gl).query(gl[L] * np.array([-1, 1, 1]), k=4)
    ok = dm[:, 0] < 0.004
    w = 1.0 / np.maximum(dm, 1e-4)
    md = np.abs(t[L[ok]] - (t[jm[ok]] * w[ok]).sum(1) / w[ok].sum(1))
    k = int(np.argmax(md)) if len(md) else 0
    graze = int(((t > 0) & (np.nan_to_num(cos, nan=1.0) < 0.5)).sum())
    print("%-24s step max %5.2f p99 %5.2f mm; off full tucks max %5.2f p99 %5.2f | L-R rim %3d pts: mean %.3f max %.3f (at %s) | grazed+tucked %d | tucked %d"
          % (name, st.max(), np.percentile(st, 99), sst.max(), np.percentile(sst, 99), int(ok.sum()), md.mean() if len(md) else 0, md.max() if len(md) else 0,
             gl[L[ok]][k].round(3) if len(md) else "-", graze, int((t > 0).sum())))


if sys.argv[1] == "probe":
    z = np.load(sys.argv[2])
    for f in ("whole", "slot"):
        fp = (z[f + "0"] > 0) | (z[f + "1"] > 0)
        for mode in (0, 1):
            stats("%s %s" % (f, ["before", "after"][mode]), z["bv0"], z["edges"], z["co_local"], z[f"{f}{mode}"], z[f"{f}{mode}_cos"], fp)
    print("POSES", str(z["poses"]))
else:
    a, b = np.load(sys.argv[2]), np.load(sys.argv[3])
    fp = (a["tuck"] > 0) | (b["tuck"] > 0)
    for lab, z in (("before", a), ("after", b)):
        stats("piece tuck_of %s" % lab, z["bv0"], z["edges"], z["co_local"], z["tuck_of"], z["cos"], fp)
        stats("piece final %s" % lab, z["bv0"], z["edges"], z["co_local"], z["tuck"], z["cos"], fp)
