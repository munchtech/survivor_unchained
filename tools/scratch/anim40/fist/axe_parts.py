import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools" / "assets"))
import grip_conform as gc
pc = gc.load("viking_axe")
N = pc.g.js["nodes"]; base = 0
t, Q = pc.local()
X, Z = pc.turn[0], pc.turn[2]
for node, p, M in pc.parts:
    n = pc.g.js["accessors"][p["attributes"]["POSITION"]]["count"]
    s = slice(base, base + n); base += n
    tt = t[s]; u = Q[s] @ X * pc.mm; v = Q[s] @ Z * pc.mm
    print(N[node].get("name"), p.get("material"), n, f"t {tt.min():.0f}..{tt.max():.0f} u {u.min():.0f}..{u.max():.0f} v {v.min():.0f}..{v.max():.0f}")
    near = np.abs(u) < 40
    for a in range(-140, 700, 40):
        q = near & (tt >= a) & (tt < a + 40)
        if q.sum(): print(f"   {a:5d} n{q.sum():4d} u {u[q].min():6.1f}..{u[q].max():6.1f} v {v[q].min():6.1f}..{v[q].max():6.1f}")
print("--- long triangles")
node, p, M = pc.parts[0]
a = pc.g.js["accessors"][p["indices"]]; bv = pc.g.js["bufferViews"][a["bufferView"]]
off = pc.g.bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
I = np.frombuffer(bytes(pc.g.b[off:off + a["count"] * 4]), "<u4")
I = np.asarray(I).reshape(-1, 3)
tt = t[:len(t)]
u = Q @ X * pc.mm; v = Q @ Z * pc.mm
span = tt[I].max(1) - tt[I].min(1)
L = I[span > 100]
print(len(L), "triangles span >100 mm")
vs = np.unique(L)
for i in vs[np.argsort(tt[vs])][:: max(1, len(vs)//40)]:
    print(f"  t {tt[i]:7.1f} u {u[i]:6.1f} v {v[i]:6.1f}")
