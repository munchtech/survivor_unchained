import os
import sys

import numpy as np
from PIL import Image

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
import relief as RL  # noqa: E402
import logo  # noqa: E402

RL.Relief.render = lambda self, name, **k: None
R, _ = logo.build(ss=1)
h = R.height
gy, gx = np.gradient(h)
shade = np.clip(0.5 + (-gx - gy) * 0.35, 0, 1) * (R.alpha > 0.5)
mat = R.mat.astype(np.float32)
rgb = np.dstack([shade, shade, shade])
rgb[R.mat == RL.IDS["chain"]] *= [0.8, 0.9, 1.1]
rgb[R.mat == RL.IDS["gold_dim"]] *= [1.2, 1.0, 0.5]
rgb = np.clip(rgb + R.emit * 0.5, 0, 1)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_prev.png")
Image.fromarray((rgb * 255).astype(np.uint8)).save(out)
print(out)
