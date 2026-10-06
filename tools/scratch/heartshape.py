import sys
import numpy as np
from sp import *
sys.path.insert(0, os.path.join(W, "tools", "uiforge"))
import medals as M
yy, xx = np.mgrid[0:256, 0:256].astype(np.float32) + 0.5
sd = M.heart_sd(xx, yy, 128, 128, 100)
m = (sd > 0).astype(np.uint8) * 255
im = Image.fromarray(m)
im.save(os.path.join(V, "heartshape.png"))
ys, xs = np.nonzero(m)
print(xs.min(), xs.max(), ys.min(), ys.max())
