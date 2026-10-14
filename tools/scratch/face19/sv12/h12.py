"""h12.py: solver 12's shared setup: the C# at HEAD (3732f72d: solver 11's carry push, s11=1) as the replica runs it, and
HAIRCLEAR replayed offline: the posed body and outfit vertices saved per photographed frame k (anim_review HAIRMESH) and
the chain's 7 links sampled 5 times each, signed distance (cm) along the nearest vertex's normal (negative = inside)."""
import sys, os; sys.path[:0] = ["../sv11", "../sv10", "../sv9", "../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from hs11 import *
from scipy.spatial import cKDTree
A = S + "f19/"
def run12(fr, st, **o): return run(fr, st, **dict(dict(s11=1, pad=0.025), **o))
MESH = {}
def mesh(folder, k):
    key = (folder, k)
    if key not in MESH:
        f = A + folder + "/k%02d.bin" % k
        if not os.path.exists(f): MESH[key] = None
        else:
            v = np.fromfile(f, np.float32).reshape(-1, 7).astype(float); MESH[key] = (v, cKDTree(v[:, :3]))
    return MESH[key]
def clear(x, folder, k):
    """per link 1..7: the worst signed distance (cm) of its 5 samples, as HAIRCLEAR (vertices within 0.45 m of the root)."""
    m = mesh(folder, k)
    if m is None: return None
    v, _ = m; sel = np.linalg.norm(v[:, :3] - x[0], axis=1) <= 0.45; vv = v[sel]; t = cKDTree(vv[:, :3]); out = []
    for i in range(1, 8):
        s = np.array([x[i - 1] + (x[i] - x[i - 1]) * j / 4 for j in range(5)])
        _, j = t.query(s); out.append(min(((s - vv[j, :3]) * vv[j, 3:6]).sum(1)) * 100)
    return out
def hclog(log):
    """HAIRCLEAR segs per k from a Godot log."""
    import re; seg = {}
    for l in open(A + log, errors="ignore"):
        m = re.match(r"HAIRCLEAR k=(\d+) segs (.*)", l)
        if m: seg[int(m.group(1))] = [float(v) for v in m.group(2).split()]
    return seg
