"""meas.py DIR out.txt [names...]: Oklab (L, C, h) of cheek / neck side / upper chest boxes in each DIR/*.png.
Boxes (x0,y0,x1,y1, 1920x1080 Look frame) in BOXES; each box's pixels with L in its 30-85th percentile (lit skin,
no freckle/shadow/spec), mean in linear then to Oklab."""
import sys, glob, os, math
import numpy as np
from PIL import Image

BOXES = {}  # filled from boxes.txt beside this file: name x0 y0 x1 y1
for ln in open(os.path.join(os.path.dirname(__file__), "tone_boxes.txt")):
    p = ln.split()
    if len(p) == 5: BOXES[p[0]] = tuple(int(v) for v in p[1:])

def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def oklab(rgb):
    r, g, b = rgb
    l = 0.4122214708*r + 0.5363325363*g + 0.0514459929*b
    m = 0.2119034982*r + 0.6806995451*g + 0.1073969566*b
    s = 0.0883024619*r + 0.2817188376*g + 0.6299787005*b
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    L = 0.2104542553*l + 0.7936177850*m - 0.0040720468*s
    a = 1.9779984951*l - 2.4285922050*m + 0.4505937099*s
    bb = 0.0259040371*l + 0.7827717662*m - 0.8086757660*s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a))

def region(im, box):
    x0, y0, x1, y1 = box
    px = lin(im[y0:y1, x0:x1].reshape(-1, 3))
    Y = px @ np.array([0.2126, 0.7152, 0.0722])
    lo, hi = np.percentile(Y, [30, 85])
    sel = px[(Y >= lo) & (Y <= hi)]
    return oklab(sel.mean(0))

d, out = sys.argv[1], sys.argv[2]
names = sys.argv[3:] or sorted(os.path.basename(f)[:-4] for f in glob.glob(d + "/*.png"))
rows = ["name               | cheek L   C     h   | neck L   C     h   | chest L   C     h   | dh(n) dL(n) dh(c) dL(c)  flag"]
for n in names:
    f = f"{d}/{n}.png"
    if not os.path.exists(f): continue
    im = np.asarray(Image.open(f).convert("RGB")).astype(np.float64) / 255
    v = {k: region(im, b) for k, b in BOXES.items()}
    ck, nk, cs = v["cheek"], v["neck"], v["chest"]
    dh = lambda a, b: (a[2] - b[2] + 180) % 360 - 180
    dn, dc = dh(ck, nk), dh(ck, cs)
    Ln, Lc = 100 * (ck[0] - nk[0]), 100 * (ck[0] - cs[0])
    flag = "FAIL" if max(abs(dn), abs(dc)) > 10 or max(abs(Ln), abs(Lc)) > 4 else ""
    rows.append(f"{n:18s} | {100*ck[0]:5.1f} {ck[1]:.3f} {ck[2]:5.1f} | {100*nk[0]:5.1f} {nk[1]:.3f} {nk[2]:5.1f} | {100*cs[0]:5.1f} {cs[1]:.3f} {cs[2]:5.1f} | {dn:+5.1f} {Ln:+5.1f} {dc:+5.1f} {Lc:+5.1f}  {flag}")
open(out, "w").write("\n".join(rows) + "\n")
print("\n".join(rows))
