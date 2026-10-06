import numpy as np
from PIL import Image
from scipy import ndimage
S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\r"
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd\tools\comfy\out\heroes\hero_tex\hero_body_paint.png"
im = np.asarray(Image.open(P).convert("RGB"), np.float32) / 255
inside = im.sum(2) > 0.03
lum = im @ np.array([0.3, 0.59, 0.11])
w = ndimage.gaussian_filter(inside.astype(np.float32), 12)
loc = ndimage.gaussian_filter(lum * inside, 12) / np.maximum(w, 1e-4)
sat = im.max(2) - im.min(2)
hi = inside & (lum - loc > 0.12)
print("bright outliers", hi.sum(), "of", inside.sum())
lab, n = ndimage.label(ndimage.binary_dilation(hi, iterations=2))
sizes = ndimage.sum(np.ones_like(lum), lab, range(1, n + 1))
print(n, "blobs; biggest", np.sort(sizes)[-10:])
ys, xs = np.nonzero(hi)
print("lum of outliers mean", lum[hi].mean(), "sat", sat[hi].mean(), "vs skin sat", sat[inside].mean())
# show a map
vis = (im * 0.5 * 255).astype(np.uint8)
vis[hi] = [255, 0, 255]
Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save(S + r"\specks.png")
# biggest blob crops
order = np.argsort(sizes)[::-1][:4]
crops = []
for k in order:
    yy, xx = np.nonzero(lab == k + 1)
    cy, cx = int(yy.mean()), int(xx.mean())
    print("blob", k, sizes[k], cy, cx)
    crops.append(Image.fromarray((im[max(0, cy - 100):cy + 100, max(0, cx - 100):cx + 100] * 255).astype(np.uint8)).resize((400, 400)))
sh = Image.new("RGB", (1600, 400))
for i, c in enumerate(crops):
    sh.paste(c, (i * 400, 0))
sh.save(S + r"\speck_crops.png")
