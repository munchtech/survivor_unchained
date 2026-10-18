"""python soft.py <src.glb> <dst.glb> keep : her side-neck bump (theta 35-100, y 1.53-1.60) taken down to `keep` of its height over a smooth fit (MLS 2 cm), inward only; normals redone."""
import sys, shutil
sys.path.insert(0, "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1941eef2c79c45fe/tools/assets")
from lib import *
import heroine_neck as hn
src, dst, keep = sys.argv[1], sys.argv[2], float(sys.argv[3])
G_, P, inv, U, T, H = load(src)
th, r = cyl(U)
dh = cKDTree(H).query(U)[0]
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
f = ss((np.abs(th) - 15) / 12) * ss((115 - np.abs(th)) / 12) * ss((U[:, 1] - 1.50) / 0.015) * ss((1.615 - U[:, 1]) / 0.015) * ss((dh - 0.006) / 0.01) * (r < 0.17)
idx = np.nonzero(f > 1e-3)[0]
U2 = U.copy()
tot = np.zeros(len(U))
for it in range(3):
    Nn = vn(U2, T)
    S, res = mls(U2, Nn, idx, 0.05, 0.02)
    d = np.maximum(res, 0) * (1 - keep) * f[idx] * (0.6 if it else 1.0)
    U2[idx] -= Nn[idx] * d[:, None]
    tot[idx] += d
N2 = vn(U2, T)
shutil.copy(src, dst); Gl = hn._Gl(dst); g = Gl.g
pr = g["meshes"][g["nodes"][84]["mesh"]]["primitives"][:2]; o = 0
ring = f > 0
for p in pr:
    n = g["accessors"][p["attributes"]["POSITION"]]["count"]; ix = inv[o:o + n]; o += n
    X = Gl.get(p["attributes"]["POSITION"]); X[:] = U2[ix]; Gl.put(p["attributes"]["POSITION"], X.astype(np.float32))
    Nr = Gl.get(p["attributes"]["NORMAL"]); Nr[ring[ix]] = N2[ix][ring[ix]]; Gl.put(p["attributes"]["NORMAL"], Nr.astype(np.float32))
Gl.save()
print("points moved", int((tot > 1e-5).sum()), "max inward mm %.2f" % (tot.max() * 1e3))
np.save(dst + ".move.npy", tot)
