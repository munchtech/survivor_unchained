"""H8: close-up #5 crown box luma vs the hair round it (hair pixels: red > green > blue, saturated)."""
import sys, numpy as np
from PIL import Image
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots\\"
for n in sys.argv[1:]:
    a = np.asarray(Image.open(SH + n + ".png").convert("RGB"), float)
    L = a @ [0.2126, 0.7152, 0.0722]
    hair = (a[..., 0] > a[..., 1] * 1.25) & (a[..., 1] > a[..., 2]) & (a[..., 0] > 25)
    ring = np.zeros(L.shape, bool); ring[238:280, 750:845] = True
    box = np.zeros(L.shape, bool); box[252:266, 785:812] = True
    r = ring & ~box & hair; b = box & hair
    print(n, "crown %.1f (%d px) vs hair round it %.1f (%d px): %.0f%%" % (L[b].mean(), b.sum(), L[r].mean(), r.sum(), 100 * (L[b].mean() / L[r].mean() - 1)))
