"""farneck_portrait.py (farneck.py's spot(), importable): TAG [faces]: the far side of her neck at 40 degrees (TAG_e_FACE), 0.3 pupil-to-chin below her far jaw
corner, against her portrait's shaded neck side at the same spot (judge j6: hue within 5 deg, C within 15%; the
owner's cool grey-lilac). Run with the facefit venv. Writes TAG_farneck.png (each spot boxed, both)."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face17")
import meas  # noqa
ff = meas.ff


def spot(path, far=None):
    im = Image.open(path).convert("RGB"); a = np.asarray(im, np.float32) / 255
    up = 2 if im.height < 900 else 1
    L = ff.detect(np.asarray(im.resize((im.width * up, im.height * up), Image.LANCZOS)))[:, :2] / up
    pc = np.linalg.norm((L[468] + L[473]) / 2 - L[152])
    r = max(3, int(0.04 * pc))
    def edge(y, x0, step):
        # (walk from x0 toward step's side along the row until the skin ends: the neck's silhouette)
        row = np.array([meas.ok(c) for c in a[int(y) - 1:int(y) + 2].mean(0)])
        x, ref = int(x0), row[int(x0)]
        while 0 < x + step < a.shape[1] - 1 and np.linalg.norm(row[x + step] - ref) < float(os.environ.get('EDGE', '0.05')):
            x += step
            ref = 0.9 * ref + 0.1 * row[x]
        return x
    def sample(x, y):
        x0, y0 = int(x - r), int(y - r)
        Lk, A, B = meas.ok(np.median(a[y0:y0 + 2 * r, x0:x0 + 2 * r].reshape(-1, 3), 0))
        return (x0, y0, 2 * r), (Lk, np.hypot(A, B), np.degrees(np.arctan2(B, A)))
    if far is None:      # (the portrait, square on: both sides of its neck, 0.3 below its jaw corners; its shaded one)
        y = (L[136][1] + L[365][1]) / 2 + 0.3 * pc
        sides = [sample(edge(y, L[152][0], s) - s * 0.12 * pc, y) for s in (-1, 1)]
        return min(sides, key=lambda q: q[1][0]), im
    # (the render, turned: the side her nose turns to, 0.3 below her chin, just inside the neck's far edge)
    s = 1 if L[1][0] > (L[234][0] + L[454][0]) / 2 else -1
    y = L[152][1] + float(os.environ.get('BELOW', '0.15')) * pc
    return sample(edge(y, L[152][0] - s * 0.3 * pc, s) - s * 0.1 * pc, y), im

