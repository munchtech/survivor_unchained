import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge")
import kit  # noqa: E402

S = os.path.dirname(os.path.abspath(__file__))
vs = {
    "b_smooth": dict(iron="#242026", tilt=0.012, rough=0.30, cell=40.0, dent=0.02),
    "b2": dict(iron="#28242a", tilt=0.010, rough=0.30, cell=48.0, dent=0.015, rubk=3.5),
    "b3": dict(iron="#28242a", tilt=0.010, rough=0.24, cell=48.0, dent=0.015, rubk=5.0, tone="#1a1213"),
}
rows = []
for name, kw in vs.items():
    img = kit.binding(1024, 200, (0.0, 86.0), (84.0, 96.0), (5.0, 79.5), "below", **kw)
    bg = np.ones((200, 1024, 3), np.float32) * np.array([0.10, 0.084, 0.089])
    comp = img[..., :3] * img[..., 3:4] + bg * (1 - img[..., 3:4])
    rows.append(comp[110:200, :700])
out = np.concatenate(rows, 0)
Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).resize((1400, 540), Image.NEAREST).save(os.path.join(S, "band_ab.png"))
print("ok")
