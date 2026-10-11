"""earmeas.py TAG [faces]: her lit ear against her lit cheek at 40 degrees (judge j6's accept: lit helix L within .04 of
the lit cheek's, C within 15%, hue within 6 deg). Shots TAG_m_FACE (the marker paint: ear green, cheekbone blue) and
TAG_e_FACE (as she is). Lit = the brightest 40% of each region's pixels (Oklab L), their median. The near ear only (the
largest green blob), and the cheek patch nearest it. Also writes TAG_earcrops.png: each face's ear and cheek, 2x."""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/tools/scratch/face17")
import meas  # noqa

tag = sys.argv[1]
faces = sys.argv[2:] or ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']


def blob(mask, near=None):
    lab, n = ndimage.label(mask)
    if n == 0: return None
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    if near is None:
        return lab == (1 + int(np.argmax(sizes)))
    cs = ndimage.center_of_mass(mask, lab, range(1, n + 1))
    best = min((i for i in range(n) if sizes[i] > 30), key=lambda i: np.hypot(cs[i][0] - near[0], cs[i][1] - near[1]), default=None)
    return None if best is None else lab == best + 1


def lit(a, m):
    px = a[m]
    oks = np.array([meas.ok(c) for c in px[:: max(1, len(px) // 4000)]])
    top = oks[oks[:, 0] >= np.percentile(oks[:, 0], float(os.environ.get("TOP", "60")))]
    L, A, B = np.median(top, 0)
    return L, np.hypot(A, B), np.degrees(np.arctan2(B, A)) % 360


crops = []
print("%-9s %-22s %-22s %s" % ("face", "ear L C h", "cheek L C h", "dL dC% dh  verdict"))
for fc in faces:
    mk = np.asarray(Image.open(os.path.join(meas.S, "%s_m_%s.png" % (tag, fc))).convert("RGB"), np.float32) / 255
    a = np.asarray(Image.open(os.path.join(meas.S, "%s_e_%s.png" % (tag, fc))).convert("RGB"), np.float32) / 255
    s = mk.sum(2) + 1e-4
    g, b = mk[..., 1] / s, mk[..., 2] / s
    ear = blob(ndimage.binary_erosion((g > 0.55) & (s > 0.1), iterations=2))
    if ear is None: print(fc, "no ear"); continue
    cy, cx = ndimage.center_of_mass(ear)
    cheek = blob(ndimage.binary_erosion((b > 0.55) & (s > 0.1), iterations=2), (cy, cx))
    if cheek is None: print(fc, "no cheek"); continue
    e, c = lit(a, ear), lit(a, cheek)
    dL, dC, dh = e[0] - c[0], (e[1] / c[1] - 1) * 100, (e[2] - c[2] + 180) % 360 - 180
    ok = abs(dL) <= 0.04 and abs(dC) <= 15 and abs(dh) <= 6
    print("%-9s L.%02d C.%03d h%3.0f       L.%02d C.%03d h%3.0f       %+.3f %+4.0f%% %+4.0f  %s" % (
        fc, round(e[0] * 100), round(e[1] * 1000), e[2], round(c[0] * 100), round(c[1] * 1000), c[2], dL, dC, dh, "PASS" if ok else "FAIL"))
    ys, xs = np.nonzero(ear | cheek)
    y0, y1, x0, x1 = max(0, ys.min() - 20), ys.max() + 20, max(0, xs.min() - 20), xs.max() + 20
    crops.append(Image.fromarray((a[y0:y1, x0:x1] * 255).astype(np.uint8)))
if crops:
    h = 360
    rs = [c.resize((int(c.width * h / c.height), h), Image.LANCZOS) for c in crops]
    out = Image.new("RGB", (sum(r.width for r in rs), h))
    x = 0
    for r in rs: out.paste(r, (x, 0)); x += r.width
    out.save(os.path.join(meas.S, tag + "_earcrops.png"))
