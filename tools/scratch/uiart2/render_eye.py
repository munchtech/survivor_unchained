"""Render the eye-bolt halves and the tab into the chain sprites, and update chain.json."""
import json
import os
import sys

import numpy as np

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
import chain  # noqa: E402
import forge as F  # noqa: E402

j = os.path.join(chain.OUT, 'links', 'chain.json')
keep = json.load(open(j))
made = chain.links(only_eye=True)
for rel, img in made.items():
    p = os.path.join(chain.OUT, 'sprites', rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    F.save(F.to_pil(np.clip(img, 0, 1)), p)
    print(rel, flush=True)
meta = json.load(open(j))
print(meta)
