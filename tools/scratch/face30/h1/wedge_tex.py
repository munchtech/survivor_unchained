"""H1: her head's texels behind/above her ears, above her hairline, that are both uncovered by the
hair cap (cover = fade^2 < 0.5) and untinted (heroine_shadow.png green < 0.5), per style.
    python wedge_tex.py [shadow.png] [art dir for the hair gltfs] [styles...]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headlib import *  # noqa
from scipy.spatial import cKDTree
from PIL import Image
sys.path.insert(0, os.path.join(WT, "tools", "assets"))
import importlib.util
spec = importlib.util.spec_from_file_location("fs", os.path.join(WT, "tools", "assets", "face_shapes.py")); fs = importlib.util.module_from_spec(spec); spec.loader.exec_module(fs)
SH = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else os.path.join(ART, "head_tex", "heroine_shadow.png")
A = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else ART
STY = sys.argv[3:] or ["pixie", "ponytail", "braid"]
HV, UV, I, keys = head()
# her ear itself: its fine mesh (edges under 3 mm) within 2 cm of its flap, and the flap
n = len(HV); s = np.zeros(n); c = np.zeros(n)
for a, b in ((0, 1), (1, 2), (2, 0)):
    L = np.linalg.norm(HV[I[:, a]] - HV[I[:, b]], axis=1)
    for q in (a, b): np.add.at(s, I[:, q], L); np.add.at(c, I[:, q], 1)
el = s / np.maximum(c, 1)
flap = np.zeros(n, bool)
for k in ("ears_out+", "ears_pointed+", "ears_lobes+"):
    flap |= keys[k] > 0.1 * keys[k].max()
ear = ((el < 0.003) & (cKDTree(HV[flap]).query(HV)[0] < 0.02)) | flap
rows, cols, XE = raster(UV, I, np.c_[HV, ear.astype(float)])
X, earv = XE[:, :3], XE[:, 3]
d_ear = cKDTree(HV[ear]).query(X)[0]
d_flap = cKDTree(HV[flap]).query(X)[0]
th = np.arctan2(X[:, 0], X[:, 2])               # 0 her front (+Z), +-90 her sides
z = X[:, 1] - EYE_Y
rise = z - fs.hairline_height(th)
# behind or above her ear: within 25 mm of its flap, not in front of its centre unless above it
side = np.sign(X[:, 0])
out = []
for sg in (1, -1):
    e = HV[flap & (np.sign(HV[:, 0]) == sg)].mean(0)
    out.append(e)
EC = {1: out[0], -1: out[1]}
ecz = np.array([EC[int(q) if q != 0 else 1][2] for q in side]); ecy = np.array([EC[int(q) if q != 0 else 1][1] for q in side])
RISE = float(os.environ.get("H1_RISE", "0.010"))   # well over her hairline (its own fade aside)
region = (d_flap < 0.025) & (earv == 0) & (d_ear > 0.001) & (rise > RISE) & ((X[:, 2] < ecz) | (X[:, 1] > ecy + 0.01))
g = np.asarray(Image.open(SH).convert("RGB"), float)[..., 1] / 255
tint = g[rows, cols]
print("shadow", SH, "| region texels", region.sum())
for st in STY:
    cp = caps(os.path.join(A, f"heroine_hair_{st}.gltf"))
    CV = np.vstack([v for v, c_, i in cp]); CA = np.concatenate([c_[:, 3] for v, c_, i in cp])
    dd, ii = cKDTree(CV).query(X, k=3)
    w = 1 / np.maximum(dd, 1e-5); fade = (CA[ii] * w).sum(1) / w.sum(1)
    fade[dd[:, 0] > 0.004] = 0
    cover = fade ** 2
    bad = region & (cover < float(os.environ.get("H1_COVER", "0.5"))) & (tint < 0.5)
    msg = f"{st}: bad texels {bad.sum()} ({100 * bad.sum() / max(region.sum(), 1):.1f}% of region)"
    if bad.any():
        msg += "; their distance from the ear flap %.1f-%.1f mm (median %.1f), height over eye %.0f..%.0f mm" % (
            d_flap[bad].min() * 1e3, d_flap[bad].max() * 1e3, np.median(d_flap[bad]) * 1e3, z[bad].min() * 1e3, z[bad].max() * 1e3)
    print(msg)
    print("   uncovered-only %d, untinted-only %d" % ((region & (cover < 0.5)).sum(), (region & (tint < 0.5)).sum()))
if os.environ.get("H1_WHERE"):
    for nm, mm in (("bad", bad),):
        dzc = (X[:, 2] - ecz) * 1e3; dyc = (X[:, 1] - ecy) * 1e3
        H, xe, ye = np.histogram2d(dzc[mm], dyc[mm], bins=[np.arange(-30, 31, 5), np.arange(-40, 41, 10)])
        print(" bad by (front of ear centre mm rows) x (over ear centre mm cols", ye.astype(int), ")")
        for r, x0 in zip(H.astype(int), xe): print("  %+4d" % x0, r)
        print("  tint of bad: mean %.2f; cover mean %.2f; ear-dist median %.1f mm" % (tint[mm].mean(), cover[mm].mean(), np.median(d_ear[mm]) * 1e3))
if os.environ.get("H1_PLOT"):
    # side view of her left (+x): texels, back to the left; tint green, cover blue, ear grey, bad red
    S = 8; z0, z1, y0, y1 = -0.07, 0.03, 1.69, 1.81
    Wd = int((z1 - z0) * 1e3 * S); Hd = int((y1 - y0) * 1e3 * S)
    img = np.zeros((Hd, Wd, 3)); dep = np.full((Hd, Wd), -1.0)
    m = X[:, 0] > 0.04
    px = ((X[m, 2] - z0) * 1e3 * S).astype(int); py = ((y1 - X[m, 1]) * 1e3 * S).astype(int)
    col = np.stack([np.zeros(m.sum()), tint[m] * 0.8, cover[m] * 0.6], 1)
    col[earv[m] > 0] = (0.5, 0.5, 0.5)
    col[bad[m]] = (1, 0, 0)
    ok = (px >= 0) & (px < Wd) & (py >= 0) & (py < Hd)
    xs = X[m, 0]
    for i in np.where(ok)[0][np.argsort(xs[ok])]:
        img[py[i], px[i]] = col[i]
    Image.fromarray((img * 255).astype(np.uint8)).save(os.environ["H1_PLOT"])
if os.environ.get("H1_DUMP"):
    b = np.where(bad)[0]
    print(" bad rows %d..%d cols %d..%d" % (rows[b].min(), rows[b].max(), cols[b].min(), cols[b].max()))
    for i in b[:: max(1, len(b) // 12)]:
        print("  r%d c%d rise %.1f mm  x %.3f  dear %.1f  tint %.2f cover %.2f th %.0f" % (rows[i], cols[i], rise[i] * 1e3, X[i, 0], d_ear[i] * 1e3, tint[i], cover[i], np.degrees(th[i])))
fl_t = raster(UV, I, flap.astype(float)[:, None])[2][:, 0]
for nm, mm in (("ear (its fine mesh + flap)", earv >= 0.999), ("flap", fl_t >= 0.999)):
    print("tint on %s: mean %.3f, >0.1: %d of %d texels, >0.3: %d" % (nm, tint[mm].mean(), (tint[mm] > 0.1).sum(), mm.sum(), (tint[mm] > 0.3).sum()))
