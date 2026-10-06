"""His neck and chest seen from the front, as texels: the relief's tilt and the paint."""
import sys
import numpy as np
from PIL import Image
S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd"
d = np.load(S + r"\texels.npz")
rows, cols, P = d["rows"], d["cols"], d["P"]
which = sys.argv[1] if len(sys.argv) > 1 else "hero_body_normal.png"
im = np.asarray(Image.open(WT + r"\tools\comfy\out\heroes\hero_tex\\" + which).convert("RGB"), np.float32)[::-1] / 255
m = (P[:, 2] > 1.38) & (P[:, 2] < 1.72) & (np.abs(P[:, 0]) < 0.3) & (P[:, 1] < 0.0)
res = 2000  # px per metre
W, H = int(0.6 * res), int(0.34 * res)
x = ((P[m, 0] + 0.3) * res).astype(int).clip(0, W - 1)
z = ((1.72 - P[m, 2]) * res).astype(int).clip(0, H - 1)
y = P[m, 1]
out = np.zeros((H, W, 3), np.float32)
depth = np.full((H, W), np.inf)
order = np.argsort(-y)  # far first, near overwrite
c = im[rows[m], cols[m]]
for i in order:
    pass
# vectorised z-buffer: keep the most front (smallest y)
key = z * W + x
srt = np.lexsort((y, key))
k2 = key[srt]
first = np.r_[True, k2[1:] != k2[:-1]]
sel = srt[first]
out.reshape(-1, 3)[key[sel]] = c[sel]
Image.fromarray((out * 255).astype(np.uint8)).save(S + r"\r\front_" + which.replace(".png", ".jpg"))
