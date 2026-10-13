"""probe.py IMG [x0,y0,x1,y1 ...]: landmarks (pupil-chin, chin 152, jaw corners 136/365, nose 1) and the Oklab median
(L, C, hue) of each box. Run with the facefit venv."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "face17"))
import meas  # noqa
ff = meas.ff

def lab(a):
    """Oklab of an (..., 3) sRGB array in 0..1."""
    sh = a.shape
    v = meas.ok(a.reshape(-1, 3).T).T
    return v.reshape(sh)

def box(a, b):
    x0, y0, x1, y1 = b
    L, A, B = meas.ok(np.median(a[y0:y1, x0:x1].reshape(-1, 3), 0))
    return L, np.hypot(A, B), np.degrees(np.arctan2(B, A))

def marks(a):
    L = ff.detect((a * 255).astype(np.uint8))[:, :2]
    return L

if __name__ == "__main__":
    p = sys.argv[1]
    a = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255
    if os.environ.get("LM", "1") == "1":
        L = marks(a)
        pc = np.linalg.norm((L[468] + L[473]) / 2 - L[152])
        print("pupil-chin %.1f chin %s jaw136 %s jaw365 %s nose1 %s ear234 %s ear454 %s" % (pc, L[152].round(), L[136].round(), L[365].round(), L[1].round(), L[234].round(), L[454].round()))
    for s in sys.argv[2:]:
        b = [int(v) for v in s.split(",")]
        Lk, C, h = box(a, b)
        print("%-22s L.%03d C.%03d h%4.0f" % (s, round(Lk * 1000), round(C * 1000), h))
