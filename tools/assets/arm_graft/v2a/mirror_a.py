# Body 2 A step 4: the left arm from the right, geometry AND weights, by SURFACE (the two patches' topologies differ).
#   python mirror_a.py <work dir> <shaped P.npy> <out prefix>   -> <prefix>_P.npy, <prefix>_VG.npy
# Each left graft vertex: its pre-shape point (graft_data V, on her surface) mirrored x -> -x, the closest point on the
# right's pre-shape surface (triangle + barycentrics), that same point on the right's FINAL surface, mirrored back, plus
# its bones' offsets (the left skeleton is not an exact mirror: elbow 2.6 mm, hand 2.4 mm farther out; each bone's head
# offset weighted by the vertex's rows). Weights the same way (groups _r -> _l). Faded to the left's own (its own
# shoulder move included) over FADE m of mesh distance from the left's kept skin (the torso ring, the hand ring).
import sys, os, heapq, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib import load, fan, edges, ss
from geo import Surf
from scipy.spatial import cKDTree
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
WK, PIN, OUT = sys.argv[1:4]; J = lambda f: os.path.join(WK, f)
FADE = float(os.environ.get("FADE", "0.03"))
a = load(J("ar.npz")); V = np.load(J("graft_data.npz"))["V"]; P = np.load(PIN).astype(float); W8 = np.load(J("wts.npz"))
VG = W8["VG"].astype(float); own = W8["own"]; names = a["names"]; ix = {n: i for i, n in enumerate(names)}
mir = np.array([-1.0, 1, 1])
perm = np.array([ix.get(n[:-2] + "_l", i) if n.endswith("_r") else (ix.get(n[:-2] + "_r", i) if n.endswith("_l") else i) for i, n in enumerate(names)])
T, _, _ = fan(a["ls"], a["lt"], a["lv"]); E = edges(a["ls"], a["lt"], a["lv"])
from lib import armframe
def wrist_kept(sd):
    Fa = armframe(a, sd, V); u_, f_ = Fa["u"], Fa["f"]; nb_ = u_["n"] + f_["n"]; nb_ /= np.linalg.norm(nb_)
    return Fa["side"] & (~own) & (((V - f_["o"]) @ nb_) > 0) & (f_["t"] > 0.6) & (f_["t"] < 1.0) & (f_["r"] < 0.06), f_["t"]
wkR, _ = wrist_kept("r"); wkL, tfL = wrist_kept("l")
R = (own & (V[:, 0] < 0)) | wkR; Lm = (own & (V[:, 0] > 0)) | wkL
# right pre-shape surface: right graft triangles and the kept ones within 3 cm of them
cen = V[T].mean(1); nearR = cKDTree(V[R]).query(cen)[0] < 0.03
TR = T[nearR & (cen[:, 0] < 0)]
S = Surf(V, TR); iL = np.where(Lm)[0]
_, dist, fi, bar = S.query(V[iL] * mir)
Q = (P[TR[fi]] * bar[:, :, None]).sum(1) * mir
WR = (VG[TR[fi]] * bar[:, :, None]).sum(1)[:, perm]          # right rows, renamed to the left
WR = WR / np.maximum(WR.sum(1, keepdims=True), 1e-9)
bh = a["bh"]; bn = a["bn"]; bix = {n: i for i, n in enumerate(bn)}
off = np.zeros((len(names), 3))
for i, n in enumerate(names):
    if n.endswith("_l") and n in bix and n[:-2] + "_r" in bix: off[i] = bh[bix[n]] - bh[bix[n[:-2] + "_r"]] * mir
delta = WR @ off
Q = Q + delta
# fade from the left's kept skin (mesh distance over the left graft)
Le = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
G = sp.coo_matrix((np.r_[Le, Le], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(len(V),) * 2).tocsr()
src = np.where((~Lm) & (V[:, 0] > 0))[0]
src = src[np.asarray(G[src][:, iL].sum(1)).ravel() > 0]      # kept skin touching the mirrored set: the torso ring, the hand side
hand = tfL[src] > 0.95
d_t = dijkstra(G, indices=src[~hand], min_only=True, limit=FADE * 1.5)[iL]; d_h = dijkstra(G, indices=src[hand], min_only=True, limit=0.02)[iL]
fd = np.minimum(ss(np.nan_to_num(d_t, posinf=1.0) / FADE), ss(np.nan_to_num(d_h, posinf=1.0) / 0.005))[:, None]
Pn = P.copy(); VGn = VG.copy()
Pn[iL] = fd * Q + (1 - fd) * P[iL]; VGn[iL] = fd * WR + (1 - fd) * VG[iL]
VGn /= np.maximum(VGn.sum(1, keepdims=True), 1e-9)
mv = np.linalg.norm(Pn[iL] - P[iL], axis=1)
print("mirror: left graft %d, pre-surface distance mm p50 %.2f p95 %.2f max %.2f; bone offset mm max %.1f; change vs own mm p50 %.1f p95 %.1f max %.1f; faded %d" % (
    len(iL), np.median(dist) * 1e3, np.percentile(dist, 95) * 1e3, dist.max() * 1e3, np.linalg.norm(delta, axis=1).max() * 1e3,
    np.median(mv) * 1e3, np.percentile(mv, 95) * 1e3, mv.max() * 1e3, int((fd < 0.999).sum())))
np.save(OUT + "_P.npy", Pn); np.save(OUT + "_VG.npy", VGn.astype(np.float32))
print("MIRRORED", OUT)
