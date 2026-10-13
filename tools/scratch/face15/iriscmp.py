"""iriscmp.py TAG name...: from TAG_fit.json (em.py), each eye's iris: mid-ring Oklab, the pattern's dark end (p10 of
sRGB max channel over 0.35-0.85 R, outside the catchlight) and Oklab dE between the names' irises pairwise."""
import sys, os, json
import numpy as np
from PIL import Image
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
HERE = os.path.dirname(os.path.abspath(__file__))
def oklab(c):
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    return (np.cbrt(c @ M1.T)) @ M2.T
tag, names = sys.argv[1], sys.argv[2:]
fit = json.load(open(os.path.join(HERE, tag + "_fit.json")))
labs = {}
for n in names:
    a = np.asarray(Image.open(os.path.join(S, n + ".png")).convert("RGB")).astype(float) / 255
    L = []
    for s in "RL":
        f = fit[n][s]; c, R = np.array(f["c"]), f["R"]
        yy, xx = np.mgrid[int(c[1] - R):int(c[1] + R) + 1, int(c[0] - R):int(c[0] + R) + 1]
        r = np.hypot(xx - c[0], yy - c[1]) / R
        px = a[yy[(r > 0.35) & (r < 0.85)], xx[(r > 0.35) & (r < 0.85)]]
        mx = px.max(1) * 255
        px = px[mx < np.percentile(mx, 95)]
        p10 = np.percentile(px.max(1) * 255, 10)
        lab = oklab(np.array(f["rgb"]))
        L.append(lab)
        print("%-14s %s ring sRGB %s Oklab L%.3f C%.3f h%3.0f | pattern p10 %.0f" % (n, s, np.round(np.array(f["rgb"]) * 255).astype(int), lab[0],
              np.hypot(lab[1], lab[2]), np.degrees(np.arctan2(lab[2], lab[1])), p10))
    labs[n] = np.mean(L, 0)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        print("dE %s-%s %.3f" % (a, b, np.linalg.norm(labs[a] - labs[b])))
