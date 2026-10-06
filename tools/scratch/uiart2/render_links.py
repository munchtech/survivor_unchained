"""Render the tab chain's sprites (Blender, CPU) into chain/sprites/chain/. Run inside a blender turn."""
import os
import sys

import numpy as np

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
import chain  # noqa: E402
import forge as F  # noqa: E402

for rel, img in chain.links().items():
    p = os.path.join(chain.OUT, 'sprites', rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    F.save(F.to_pil(np.clip(img, 0, 1)), p)
print('links done', flush=True)
