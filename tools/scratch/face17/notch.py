import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import face_fit as ff  # noqa
from scipy.ndimage import gaussian_filter1d
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
R = r"C:\Users\munch\Desktop\survivorsunchained_inputs\face4\refs_front"
for n in sys.argv[1:]:
    p = next(q for q in (os.path.join(S, n + '.png'), os.path.join(R, n + '.png')) if os.path.exists(q))
    im = Image.open(p).convert('L'); a = np.asarray(im, np.float32)
    up = 2 if im.height < 900 else 1
    L = ff.detect(np.asarray(Image.open(p).convert('RGB').resize((im.width * up, im.height * up))))
    if L is None:
        c = Image.open(p).convert('RGB').crop((im.width // 3, 0, 2 * im.width // 3, im.height // 2)); L = ff.detect(np.asarray(c.resize((c.width * 2, c.height * 2)))); L = L[:, :2] / 2 + [im.width // 3, 0]
    else: L = L[:, :2] / up
    pupil = (L[468] + L[473]) / 2; chin = L[152]; u = chin[1] - pupil[1]
    x0 = int(chin[0]); w = max(2, int(0.04 * u))
    ys = np.arange(int(chin[1] + 0.3 * u), min(a.shape[0] - 1, int(chin[1] + 1.0 * u)))
    prof = gaussian_filter1d(a[ys, x0 - w:x0 + w].mean(1), 0.02 * u)
    d2 = gaussian_filter1d(prof, 0.03 * u, order=2)   # a dip: the second derivative's peak
    mins = [i for i in range(1, len(d2) - 1) if d2[i] > d2[i - 1] and d2[i] > d2[i + 1]]
    best = sorted(mins, key=lambda i: -d2[i])[:3]
    print("%-14s pupil-chin %4.0f px; dips at %s" % (n, u, ", ".join("%.2f (%.2f)" % ((ys[i] - chin[1]) / u, d2[i]) for i in sorted(best))))
