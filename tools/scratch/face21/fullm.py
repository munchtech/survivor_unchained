"""fullm.py SHOT...: the whole Look frame (--zoom 0): her cheek (landmark 205 on a 6x crop of her face) against her
thigh fronts and sword-side upper arm (fixed boxes, r9 pose), Oklab L C h and the hue and C against the cheek
(j7 (f): within 8 deg and 25%). Run with the facefit venv."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "face17"))
import meas  # noqa
BOX = {"thighL": (928, 615, 945, 640), "thighR": (982, 610, 998, 635), "armS": (888, 420, 902, 450)}
for n in sys.argv[1:]:
    im = Image.open(os.path.join(meas.S, n + ".png")).convert("RGB"); a = np.asarray(im, np.float32) / 255
    x0, y0 = 910, 250
    c = im.crop((x0, y0, x0 + 100, y0 + 100)).resize((600, 600), Image.LANCZOS)
    L = meas.ff.detect(np.asarray(c))[:, :2] / 6 + [x0, y0]
    cx, cy = L[205]; r = 2
    v = {"cheek": meas.ok(np.median(a[int(cy) - r:int(cy) + r, int(cx) - r:int(cx) + r].reshape(-1, 3), 0))}
    for k, (bx0, by0, bx1, by1) in BOX.items(): v[k] = meas.ok(np.median(a[by0:by1, bx0:bx1].reshape(-1, 3), 0))
    lch = {k: (q[0], np.hypot(q[1], q[2]), np.degrees(np.arctan2(q[2], q[1]))) for k, q in v.items()}
    ck = lch["cheek"]; out = "%-14s cheek(%d,%d) L.%02d C.%03d h%4.0f" % (n, cx, cy, ck[0] * 100, ck[1] * 1000, ck[2])
    for k in BOX:
        q = lch[k]; dh = (q[2] - ck[2] + 180) % 360 - 180; dc = (q[1] / ck[1] - 1) * 100
        out += " | %s L.%02d C.%03d h%4.0f dh%+4.0f dC%+4.0f%% %s" % (k, q[0] * 100, q[1] * 1000, q[2], dh, dc, "ok" if abs(dh) <= 8 and abs(dc) <= 25 else "FAIL")
    print(out)
