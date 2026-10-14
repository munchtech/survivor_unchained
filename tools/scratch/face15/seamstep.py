"""seamstep.py MASK SHOT [SHOT...]: along her head's lower edge on screen (MASK: an unshaded shot with her head
green), each SHOT's skin A px above the edge against B px below (bands 3-12 px), Oklab: dL, dE (corrected for
the neck's own fall of light, measured 12-30 px below), and the fine texture (std of a 3-px high-pass) above/below."""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
def ld(n):
    return np.asarray(Image.open(os.path.join(S, n + ".png")).convert("RGB")).astype(float) / 255
def oklab(c):
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    return (np.cbrt(c @ M1.T)) @ M2.T
m = ld(sys.argv[1]) * 255
head = (m[..., 1] > m[..., 0] + 40) & (m[..., 1] > m[..., 2] + 40)
head = ndimage.binary_opening(head & (m[..., 1] > 120), iterations=2)
lb, nl = ndimage.label(head)
head = lb == (np.argmax(np.bincount(lb.ravel())[1:]) + 1)
pts = []
H, W = head.shape
for x in range(0, W, 2):
    ys = np.where(head[:, x])[0]
    if len(ys) < 20: continue
    y = ys.max()
    if y + 32 >= H: continue
    below = m[y + 3:y + 30, x]
    if below.mean() < 50 or (below[:, 0] < below[:, 1] + 5).any() or (below[:, 0] < below[:, 2] + 10).any() or head[y + 3:y + 30, x].any(): continue
    pts.append((x, y))
print("edge y %d..%d" % (min(p[1] for p in pts), max(p[1] for p in pts)) if pts else ""); print("edge columns", len(pts), "x %d..%d" % (pts[0][0], pts[-1][0]) if pts else "")
for n in sys.argv[2:]:
    im = ld(n); lab = oklab(im)
    gray = lab[..., 0]
    hp = gray - ndimage.uniform_filter(gray, 5)
    A = np.array([lab[y - 12:y - 3, x].mean(0) for x, y in pts]); B = np.array([lab[y + 3:y + 12, x].mean(0) for x, y in pts])
    C = np.array([lab[y + 12:y + 21, x].mean(0) for x, y in pts]); D = np.array([lab[y + 21:y + 30, x].mean(0) for x, y in pts])
    ok = (A[:, 0] > 0.5) & (B[:, 0] > 0.5) & (C[:, 0] > 0.5) & (D[:, 0] > 0.5)
    A, B, C, D = A[ok], B[ok], C[ok], D[ok]
    print('   raw L above %.4f below %.4f | lower %.4f %.4f (%d cols)' % (A[:,0].mean(), B[:,0].mean(), C[:,0].mean(), D[:,0].mean(), ok.sum()))
    fall = (C - D).mean(0)                     # (what 9 px of her neck changes with no seam)
    d = (A - B).mean(0) - fall
    tA = np.mean([hp[y - 12:y - 3, x].std() for x, y in pts]); tB = np.mean([hp[y + 3:y + 12, x].std() for x, y in pts])
    tC = np.mean([hp[y + 12:y + 30, x].std() for x, y in pts])
    # worst 20-col stretch of the corrected dE
    dd = (A - B) - fall
    e = np.linalg.norm(dd, axis=1)
    worst = np.convolve(e, np.ones(10) / 10, "valid").max() if len(e) >= 10 else np.nan
    print("%-16s dL %+.4f da %+.4f db %+.4f | dE %.4f worst %.4f | texture above %.4f below %.4f lower %.4f" % (
        n, d[0], d[1], d[2], np.linalg.norm(d), worst, tA, tB, tC))
if os.environ.get("OVERLAY"):
    im = Image.open(os.path.join(S, sys.argv[2] + ".png")).convert("RGB")
    px = im.load()
    for x, y in pts:
        px[x, y] = (255, 0, 255)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    im.crop((min(xs) - 40, min(ys) - 120, max(xs) + 40, max(ys) + 80)).save(os.environ["OVERLAY"])
