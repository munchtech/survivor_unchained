import numpy as np
from PIL import Image
S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd"
d = np.load(S + r"\texels.npz")
rows, cols, P = d["rows"], d["cols"], d["P"]
nim = np.asarray(Image.open(WT + r"\tools\comfy\out\heroes\hero_tex\hero_body_normal.png").convert("RGB"), np.float32)[::-1] / 255
n = nim[rows, cols] * 2 - 1
clav = (P[:, 2] > 1.5) & (P[:, 2] < 1.62) & (np.abs(P[:, 0]) < 0.2) & (P[:, 1] < 0)
xy = np.linalg.norm(n[:, :2], axis=1)
print("clav xy pct", np.percentile(xy[clav], [50, 90, 99, 99.9]))
# the blotch location from the render: near the sternal notch, either side, ~ x 0.05-0.12, z ~1.56
for x0 in (-0.1, -0.06, 0.06, 0.1):
    m = clav & (np.abs(P[:, 0] - x0) < 0.02) & (np.abs(P[:, 2] - 1.57) < 0.02)
    if m.any():
        print(x0, m.sum(), "xy mean %.3f max %.3f" % (xy[m].mean(), xy[m].max()), "n mean", np.round(n[m].mean(0), 2))
# paint there
pim = np.asarray(Image.open(WT + r"\tools\comfy\out\heroes\hero_tex\hero_body_paint.png").convert("RGB"), np.float32)[::-1] / 255
c = pim[rows, cols]
lum = c @ [0.3, 0.59, 0.11]
print("clav lum pct", np.percentile(lum[clav], [1, 10, 50, 90, 99]))
# island sizes: texel rows/cols of clavicle region -> show the UV region bounding boxes
m = clav & (np.abs(P[:, 2] - 1.57) < 0.03) & (np.abs(P[:, 0]) < 0.14) & (np.abs(P[:, 0]) > 0.03)
print("uv rows", rows[m].min(), rows[m].max(), "cols", cols[m].min(), cols[m].max())
img = np.zeros((4096, 4096, 3), np.uint8)
img[rows[m], cols[m]] = (nim[rows[m], cols[m]] * 255).astype(np.uint8)
ys, xs = rows[m], cols[m]
Image.fromarray(img[::-1]).crop((xs.min(), 4096 - ys.max(), xs.max(), 4096 - ys.min())).save(S + r"\r\clav_nrm.png")
img2 = np.zeros((4096, 4096, 3), np.uint8)
img2[rows[m], cols[m]] = (pim[rows[m], cols[m]] * 255).astype(np.uint8)
Image.fromarray(img2[::-1]).crop((xs.min(), 4096 - ys.max(), xs.max(), 4096 - ys.min())).save(S + r"\r\clav_paint.png")
