# Body 2 A step 2: the arm patch's own texture (material skin_arm, image heroine_arm_paint) and its UVs.
#   python bake_a.py <work dir>      reads her.npz, ar.npz (the g2e islands: one arm strip + one cap per side),
#   graft_data.npz (V: the patch BEFORE any shape move, on her surface), plan.npz, old_body.npy / old_graft.npy
#   writes <work>/arm_uv.npz (uv per patch loop, faces >= nk in order; size), arm_paint.npy (rows bottom-up), arm_paint.png
# Each g2e island keeps its shape (same unwrap: one straight strip per arm), turned by its PCA (rotation only) and scaled to
# ARM_PX / CAP_PX px per cm (2x her highest: Material_0.001 p99 12.8, the cap's skin_graft 17.5). Layout (px, bottom-up):
# the two arm strips lying along x, stacked at the left (r below); the two caps standing in the right column.
# Bake per texel centre (no supersampling, no box filter): the texel's point on V -> closest point on HER surface (V lies
# on it: p95 0.5 mm) -> her UV there and her face's material -> her image, bilinear. Islands padded PAD px (nearest texel).
import sys, os, numpy as np, cv2
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib import load, fan, uv_islands
from geo import Surf
WK = sys.argv[1]; J = lambda f: os.path.join(WK, f)
ARM_PX = float(os.environ.get("ARM_PX", "26")); CAP_PX = float(os.environ.get("CAP_PX", "35")); PAD = int(os.environ.get("PAD", "8"))
TW = int(os.environ.get("TW", "2048"))
h = load(J("her.npz")); a = load(J("ar.npz")); V = np.load(J("graft_data.npz"))["V"]; nk = int(np.load(J("plan.npz"))["nk"])
ls, lt, lv, uv0 = a["ls"], a["lt"], a["lv"], a["uv"]; nf = len(ls); pf = np.arange(nk, nf)
lab, n = uv_islands(ls, lt, lv, uv0, a["mi"], pf)
Lp = np.concatenate([np.arange(ls[i], ls[i] + lt[i]) for i in pf]); fl_p = np.repeat(pf, lt[pf]); lab_l = np.repeat(lab, lt[pf])
new = np.zeros((len(Lp), 2))
isl = []
for k in range(n):
    F = pf[lab == k]; m = lab_l == k; L = Lp[m]
    T, tf, TL = fan(ls[F] - ls[F] + np.r_[0, np.cumsum(lt[F])[:-1]], lt[F], lv[np.concatenate([np.arange(ls[i], ls[i] + lt[i]) for i in F])])
    q = uv0[L]; p = V[lv[L]]
    tri = TL; A3 = 0.5 * np.linalg.norm(np.cross(p[tri[:, 1]] - p[tri[:, 0]], p[tri[:, 2]] - p[tri[:, 0]]), axis=1).sum()
    e1 = q[tri[:, 1]] - q[tri[:, 0]]; e2 = q[tri[:, 2]] - q[tri[:, 0]]; A2 = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]).sum()
    cm_per_uv = np.sqrt(A3 / A2) * 100
    mi = int(a["mi"][F[0]]); side = "r" if p[:, 0].mean() < 0 else "l"
    px = (ARM_PX if mi == 0 else CAP_PX) * cm_per_uv
    c = q.mean(0); w, U = np.linalg.eigh(np.cov((q - c).T))
    if np.linalg.det(U) < 0: U[:, 0] = -U[:, 0]
    r = (q - c) @ U * px   # px, axis 1 = long
    if mi == 0: r = r[:, ::-1] * np.array([1, -1])   # arms lie along x (a rotation by 90 deg)
    r -= r.min(0)
    isl.append(dict(k=k, mi=mi, side=side, m=m, r=r, size=r.max(0), A=A3 * 1e4))
arms = sorted([i for i in isl if i["mi"] == 0], key=lambda i: i["side"] != "r"); caps = sorted([i for i in isl if i["mi"] == 1], key=lambda i: i["side"] != "r")
y = PAD; xr = 0
for i in arms: i["off"] = np.array([PAD, y]); y += i["size"][1] + 2 * PAD; xr = max(xr, PAD + i["size"][0] + 2 * PAD)
ya = y; y = PAD
for i in caps: i["off"] = np.array([xr, y]); y += i["size"][1] + 2 * PAD; assert xr + i["size"][0] + PAD <= TW, "caps do not fit"
assert xr - PAD <= TW
TH = int(np.ceil(max(ya, y) / 64) * 64)
for i in isl:
    new[i["m"]] = (i["r"] + i["off"]) / np.array([TW, TH])
    print("island", i["side"], "arm" if i["mi"] == 0 else "cap", "%.0f cm2" % i["A"], "box px %dx%d at" % tuple(i["size"]), tuple(i["off"].astype(int)))
print("texture %dx%d, arm %.1f px/cm, cap %.1f px/cm" % (TW, TH, ARM_PX, CAP_PX))
# --- bake
Th, tfh, TLh = fan(h["ls"], h["lt"], h["lv"])
from scipy.spatial import cKDTree
near = cKDTree(V[np.unique(lv[Lp])]).query(h["P"][Th].mean(1))[0] < 0.04
S = Surf(h["P"], Th[near]); TLs = TLh[near]; TFs = tfh[near]
IMG = {0: np.load(J("old_body.npy")).astype(np.float64), 1: np.load(J("old_graft.npy")).astype(np.float64)}
def sample(img, q):
    H, W = img.shape[:2]; x = q[:, 0] * W - 0.5; y_ = q[:, 1] * H - 0.5; x0 = np.floor(x).astype(int); y0 = np.floor(y_).astype(int); fx = (x - x0)[:, None]; fy = (y_ - y0)[:, None]
    g = lambda yy, xx: img[np.clip(yy, 0, H - 1), np.clip(xx, 0, W - 1), :3]
    return g(y0, x0) * (1 - fx) * (1 - fy) + g(y0, x0 + 1) * fx * (1 - fy) + g(y0 + 1, x0) * (1 - fx) * fy + g(y0 + 1, x0 + 1) * fx * fy
T, tf, TL = fan(ls[pf] - ls[nk], lt[pf], lv[Lp])   # local loop ids into Lp / new
pts = []; pix = []
Q = new[TL] * np.array([TW, TH]) - 0.5; P3 = V[T]
for t in range(len(T)):
    q = Q[t]; d = (q[1, 0] - q[0, 0]) * (q[2, 1] - q[0, 1]) - (q[2, 0] - q[0, 0]) * (q[1, 1] - q[0, 1])
    if abs(d) < 1e-12: continue
    lo = np.floor(q.min(0)).astype(int); hi = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1)); xs = xs.ravel(); ys = ys.ravel()
    b1 = ((xs - q[0, 0]) * (q[2, 1] - q[0, 1]) - (q[2, 0] - q[0, 0]) * (ys - q[0, 1])) / d
    b2 = ((q[1, 0] - q[0, 0]) * (ys - q[0, 1]) - (xs - q[0, 0]) * (q[1, 1] - q[0, 1])) / d; b0 = 1 - b1 - b2
    k = (b0 >= -1e-6) & (b1 >= -1e-6) & (b2 >= -1e-6)
    if k.any(): pts.append(b0[k, None] * P3[t, 0] + b1[k, None] * P3[t, 1] + b2[k, None] * P3[t, 2]); pix.append(np.c_[ys[k], xs[k]])
pts = np.concatenate(pts); pix = np.concatenate(pix)
_, ui = np.unique(pix[:, 0] * TW + pix[:, 1], return_index=True); pts = pts[ui]; pix = pix[ui]
col = np.zeros((len(pts), 3)); dist = np.zeros(len(pts))
for s0 in range(0, len(pts), 200000):
    sl = slice(s0, s0 + 200000); _, dd, fi, bar = S.query(pts[sl]); dist[sl] = dd
    ouv = (h["uv"][TLs[fi]] * bar[:, :, None]).sum(1); om = h["mi"][TFs[fi]]; c_ = np.zeros((len(fi), 3))
    for mm in (0, 1):
        s_ = om == mm
        if s_.any(): c_[s_] = sample(IMG[mm], ouv[s_])
    col[sl] = c_
out = np.zeros((TH, TW, 3)); cov = np.zeros((TH, TW), bool); out[pix[:, 0], pix[:, 1]] = col; cov[pix[:, 0], pix[:, 1]] = True
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
zone = cv2.dilate(cov.astype(np.uint8), np.ones((2 * PAD + 1,) * 2, np.uint8)).astype(bool)
fill = out[iy, ix]; out[zone & ~cov] = fill[zone & ~cov]
bg = col.mean(0); out[~zone] = bg
print("baked texels %d, padded %d; her surface distance mm p50 %.2f p95 %.2f p99 %.2f max %.2f" % (cov.sum(), (zone & ~cov).sum(), np.median(dist) * 1e3, np.percentile(dist, 95) * 1e3, np.percentile(dist, 99) * 1e3, dist.max() * 1e3))
np.save(J("arm_paint.npy"), out.astype(np.float32))
cv2.imwrite(J("arm_paint.png"), np.clip(np.round(out[::-1] * 255), 0, 255).astype(np.uint8)[:, :, ::-1])
np.savez(J("arm_uv.npz"), uv=new, nk=nk, size=np.array([TW, TH]))
print("BAKED", J("arm_paint.png"))
