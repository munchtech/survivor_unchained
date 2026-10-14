"""diff.py A B OUT [x0 y0 x1 y1]: where two shots differ (abs diff x8, crop), with the bbox and mean of the changed area."""
import sys, os
import numpy as np
from PIL import Image
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
a = np.asarray(Image.open(os.path.join(S, sys.argv[1] + ".png")).convert("RGB"), np.float32)
b = np.asarray(Image.open(os.path.join(S, sys.argv[2] + ".png")).convert("RGB"), np.float32)
d = np.abs(a - b).max(2)
ys, xs = np.nonzero(d > 3)
print("changed px %d, bbox x %d-%d y %d-%d" % (len(xs), xs.min(), xs.max(), ys.min(), ys.max()) if len(xs) else "no change")
box = tuple(map(int, sys.argv[4:8])) if len(sys.argv) > 7 else (0, 0, a.shape[1], a.shape[0])
c = np.clip(d * 8, 0, 255).astype(np.uint8)[box[1]:box[3], box[0]:box[2]]
Image.fromarray(c).save(sys.argv[3])
