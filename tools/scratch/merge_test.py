import os
import sys

import numpy as np
from PIL import Image

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
import cardcolour as CC  # noqa: E402

RAW = CC.RAW
base = np.asarray(Image.open(os.path.join(RAW, "guides", "card_rare_dressed.png")).convert("RGB"), np.float32) / 255
src = os.path.join(RAW, "card3", "card3po_rare_30_693_0.png")
for keep in (0.4, 0.6):
    out = CC.merge(base, src, keep=keep)
    p = os.path.join(RAW, "card3", f"card3m_rare_30_693_0_k{int(keep * 100)}.png")
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p)
    print(p)
