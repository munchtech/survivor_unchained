"""catch.py IMG...: each eye's catchlight: clock position about the iris centre, offset and size (equivalent radius)
as fractions of the iris radius, peak and mean lightness. Run with the facefit venv."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import face_fit as ff  # noqa
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
R = r"C:\Users\munch\Desktop\survivorsunchained_inputs\face4\refs_front"
def path(s):
    for p in (s, os.path.join(S, s + '.png'), os.path.join(R, s + '.png')):
        if os.path.exists(p): return p
for n in sys.argv[1:]:
    im = Image.open(path(n)).convert('RGB'); up = 2 if im.height < 900 else 1
    big = im.resize((im.width * up, im.height * up), Image.LANCZOS); a = np.asarray(big, np.float32) / 255
    L = ff.detect(np.asarray(big))[:, :2]
    out = []
    for c0, ring in ((468, range(469, 473)), (473, range(474, 478))):
        c = L[c0]; r = np.mean([np.linalg.norm(L[i] - c) for i in ring])
        y0, y1, x0, x1 = int(c[1] - r), int(c[1] + r) + 1, int(c[0] - r), int(c[0] + r) + 1
        p = a[y0:y1, x0:x1].mean(2); yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.hypot(xx - c[0], yy - c[1]) / r; inside = d < 0.95
        med = np.median(p[inside]); pk = p[inside].max()
        m = inside & (p > med + 0.6 * (pk - med))
        if m.sum() == 0: out.append("--"); continue
        cx, cy = xx[m].mean() - c[0], yy[m].mean() - c[1]
        clock = (np.degrees(np.arctan2(cx, -cy)) % 360) / 30
        out.append("%4.1f o'clock off %.2f size %.2f peak %.2f (iris %.2f, r %.0fpx)" % (clock if clock >= 0.5 else clock + 12, np.hypot(cx, cy) / r, np.sqrt(m.sum() / np.pi) / r, pk, med, r / up))
    print("%-18s" % n[:18], " | ".join(out))
