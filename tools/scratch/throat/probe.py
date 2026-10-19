"""python probe.py <src.glb> <dst.glb> th_lo th_hi y_lo y_hi mm : push her neck skin in that band inward (smooth fade), normals redone."""
import sys, shutil
sys.path.insert(0, "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1941eef2c79c45fe/tools/assets")
from lib import *
import heroine_neck as hn
src, dst = sys.argv[1:3]
a0, a1, y0, y1, mm = [float(v) for v in sys.argv[3:8]]
G_, P, inv, U, T, H = load(src)
th, r = cyl(U)
dh = cKDTree(H).query(U)[0]
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
f = ss((np.abs(th) - a0) / 10) * ss((a1 - np.abs(th)) / 10) * ss((U[:, 1] - y0) / 0.01) * ss((y1 - U[:, 1]) / 0.01) * ss((dh - 0.004) / 0.008) * (r < 0.17)
Nn = vn(U, T)
U2 = U - Nn * (f * mm * 1e-3)[:, None]
N2 = vn(U2, T)
shutil.copy(src, dst); Gl = hn._Gl(dst); g = Gl.g
pr = g["meshes"][g["nodes"][84]["mesh"]]["primitives"][:2]; o = 0
ring = f > 0
for p in pr:
    n = g["accessors"][p["attributes"]["POSITION"]]["count"]; ix = inv[o:o + n]; o += n
    X = Gl.get(p["attributes"]["POSITION"]); X[:] = U2[ix]; Gl.put(p["attributes"]["POSITION"], X.astype(np.float32))
    Nr = Gl.get(p["attributes"]["NORMAL"]); Nr[ring[ix]] = N2[ix][ring[ix]]; Gl.put(p["attributes"]["NORMAL"], Nr.astype(np.float32))
Gl.save(); print("moved", int((f > 0.01).sum()), "max mm", (f * mm).max())
