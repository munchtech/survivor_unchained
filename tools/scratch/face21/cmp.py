"""cmp.py NAMES BOXES: Oklab L/C/hue medians of each named box in each shot (godot/.shots/NAME.png).
NAMES comma-separated shot names; BOXES 'label=x0,y0,x1,y1;...'. Run with the facefit venv."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "face17"))
import meas  # noqa
names = sys.argv[1].split(",")
boxes = [(s.split("=")[0], [int(v) for v in s.split("=")[1].split(",")]) for s in sys.argv[2].split(";")]
print("%-16s" % "shot" + "".join("%-19s" % b[0] for b in boxes))
for n in names:
    p = os.path.join(meas.S, n + ".png")
    if not os.path.exists(p): print(n, "missing"); continue
    a = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255
    row = "%-16s" % n
    for _, (x0, y0, x1, y1) in boxes:
        L, A, B = meas.ok(np.median(a[y0:y1, x0:x1].reshape(-1, 3), 0))
        row += "L.%03d C.%03d h%4.0f  " % (round(L * 1000), round(np.hypot(A, B) * 1000), np.degrees(np.arctan2(B, A)))
    print(row)
