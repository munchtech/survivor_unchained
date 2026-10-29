# Body 2 A: the patch's UV islands (g2e layout in ar.npz): area, density, PCA box in cm.  python isl.py <work>
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import load, uv_islands
WK = sys.argv[1]; a = load(os.path.join(WK, "ar.npz")); D = np.load(os.path.join(WK, "graft_data.npz")); V = D["V"]
nk = int(np.load(os.path.join(WK, "plan.npz"))["nk"]); nf = len(a["ls"]); pf = np.arange(nk, nf)
lab, n = uv_islands(a["ls"], a["lt"], a["lv"], a["uv"], a["mi"], pf)
def islands(lab, n, pf):
    out = []
    for k in range(n):
        F = pf[lab == k]; L = np.concatenate([np.arange(a["ls"][i], a["ls"][i] + a["lt"][i]) for i in F])
        A3 = A2 = 0
        for i in F:
            s, t = a["ls"][i], a["lt"][i]; v = a["lv"][s:s + t]; q = a["uv"][s:s + t]; p = V[v]
            for j in range(1, t - 1):
                A3 += 0.5 * np.linalg.norm(np.cross(p[j] - p[0], p[j + 1] - p[0]))
                A2 += 0.5 * abs((q[j, 0] - q[0, 0]) * (q[j + 1, 1] - q[0, 1]) - (q[j, 1] - q[0, 1]) * (q[j + 1, 0] - q[0, 0]))
        sc = np.sqrt(A3 / A2)  # metres per uv unit
        q = a["uv"][L] * sc * 100; c = q.mean(0); w, U = np.linalg.eigh(np.cov((q - c).T)); r = (q - c) @ U
        out.append(dict(k=k, nf=len(F), mi=int(a["mi"][F[0]]), side="r" if V[a["lv"][L]][:, 0].mean() < 0 else "l", A=A3 * 1e4, box=r.max(0) - r.min(0)))
    return out
if __name__ == "__main__":
    for o in islands(lab, n, pf): print(o)
