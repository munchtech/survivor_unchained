# Body 1 g2c (armor 18, 22 Oct 2026): the arm root's shape and weights on a fresh graft, so the whole chain re-runs from
# heroine_built.blend.  python post.py <dump of the grafted blend.npz> <weights source dump.npz> <source VG.npy> <people dir> <out dir>
#   weights: G2b's (the source: heroine_built_armroot_g1.blend's dump + VG_v1.npy) carried by surface interpolation
#            (a kept vertex at the same place takes its own row), top 4, normalised;
#   shape:   heroine_arm_shape.py's field (g2a edit.arm_shape_field, shares from the graft's own carried weights) and
#            Taubin fairing of both pits (edit.pit_mask, 30 iterations), as g2b baked it.
# Writes P.npy, VG.npy (dump order) and names.npy for g2b/w_write.py.
import os, sys
a = sys.argv[1:]
os.environ["ANIM_PEOPLE"] = os.path.abspath(a[3])
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "g2a"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
from scipy.spatial import cKDTree
from g2lib import load_dump, blendv, tri_polys
from geo import Surf
from skin import Body
import edit
d = load_dump(a[0]); s = load_dump(a[1]); VGs = np.load(a[2]); out = a[4]; os.makedirs(out, exist_ok=True)
assert d["names"] == s["names"], "group order differs"
P, Ps = d["P"], s["P"]
# weights
VG = np.zeros_like(d["VG"])
dd, j = cKDTree(Ps).query(P); same = dd < 1e-7
VG[same] = VGs[j[same]]
Ts = tri_polys(s["polys"]); S = Surf(Ps, Ts)
q, dist, fi, bar = S.query(P[~same]); W = (VGs[Ts[fi]] * bar[:, :, None]).sum(1)
top = np.argsort(-W, 1)[:, :4]; r = np.arange(len(W))[:, None]; W4 = np.zeros_like(W); W4[r, top] = W[r, top]; W4[W4 < 1e-4] = 0
VG[~same] = W4 / np.maximum(W4.sum(1, keepdims=True), 1e-9)
# g2d: the inner elbow's upperarm/lowerarm split (helpers.split's x = W_low/(W_up+W_low)) widened by masked Laplacian
# smoothing of x on the front of the elbow (ELBOW_IT iterations), the pair's sum kept
b0 = Body.heroine(jiggle=False, head=True, helpers=True); C0 = edit.Ctx(d, b0); nmL = list(d["names"])
for sd in "lr":
    f = C0.frame(sd); iu, il = nmL.index("upperarm_" + sd), nmL.index("lowerarm_" + sd)
    m = f["side"] * edit.win(f["t"], ((0.70, 0.82), (1.18, 1.30))) * ((1 + np.cos(np.radians(f["phi"] - 90))) / 2) ** float(os.environ.get("ELBOW_POW", "1"))
    su = VG[:, iu] + VG[:, il]; x = np.where(su > 1e-6, VG[:, il] / np.maximum(su, 1e-9), 0); m = m * (su > 0.2)
    for _ in range(int(os.environ.get("ELBOW_IT", "0"))):
        x = x + 0.5 * m * (C0.Wn @ x - x)
    VG[:, il] = np.where(su > 1e-6, su * x, VG[:, il]); VG[:, iu] = np.where(su > 1e-6, su * (1 - x), VG[:, iu])
    print("elbow split", sd, "vertices touched", int((m > 0.01).sum()))
print("weights: kept rows", int(same.sum()), "interpolated", int((~same).sum()), "source dist mm p95 %.2f max %.2f" % (np.percentile(dist, 95) * 1e3, dist.max() * 1e3))
# shape
b = Body.heroine(jiggle=False, head=True, helpers=True)
C = edit.Ctx(d, b)
SH = C.shares(d["VG"])
X = C.Pg + edit.arm_shape_field(C, SH)
mk = np.maximum(edit.pit_mask(C, "r"), edit.pit_mask(C, "l"))
X = edit.fair(C, X, mk, iters=int(os.environ.get("FAIR_IT", "30")))
# g2d: the trap-to-acromion junction faired (Taubin, TOP_IT iterations) on the shoulder top and back, only on vertices
# the graft already moved (so no neck-graft npz point that sits on the original blend moves)
if int(os.environ.get("TOP_IT", "0")):
    her = np.load(os.path.join(os.path.dirname(os.path.abspath(a[0])), "her.npz"))["P"]
    own = cKDTree(her).query(P)[0] > 1e-6
    mt = np.zeros(len(P))
    for sd in "lr":
        f = C.frame(sd)
        mt = np.maximum(mt, f["side"] * edit.win(f["t"], tuple(map(tuple, np.array(eval(os.environ.get("TOP_T", "((-0.60,-0.50),(-0.10,0.0))"))))))
                        * edit.ss((float(os.environ.get("TOP_PHI1", "40")) - f["phi"]) / 20) * edit.ss((f["phi"] + 130) / 20))
    mt *= own
    X = edit.fair(C, X, mt, iters=int(os.environ["TOP_IT"]))
    print("top fair: vertices", int((mt > 0.01).sum()))
Pn = blendv(X); mv = np.linalg.norm(Pn - P, axis=1)
print("shape: moved", int((mv > 1e-7).sum()), "max %.1f mm" % (mv.max() * 1e3))
np.save(os.path.join(out, "P.npy"), Pn); np.save(os.path.join(out, "VG.npy"), VG.astype(np.float32)); np.save(os.path.join(out, "names.npy"), np.array(d["names"]))
