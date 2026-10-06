import numpy as np
from PIL import Image
from scipy import ndimage
S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\r"
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd\tools\comfy\out\heroes\hero_tex\hero_body_normal.png"
im = np.asarray(Image.open(P).convert("RGB"), np.float32) / 255
n = im * 2 - 1
inside = np.abs(im - 0.5).sum(2) > 0.01
z = n[..., 2]
print("z percentiles inside", np.percentile(z[inside], [0.1, 1, 5, 25, 50]))
for t in (0.9, 0.8, 0.7, 0.6, 0.5):
    print("z <", t, (inside & (z < t)).sum())
vis = (im * 255).astype(np.uint8)
bad = inside & (z < 0.75)
vis[bad] = [255, 0, 255]
Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save(S + r"\nrm_bad.png")
