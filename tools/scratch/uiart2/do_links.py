import os
import subprocess
import sys

import numpy as np

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
import chain  # noqa: E402
import forge as F  # noqa: E402

made = chain.links()
for rel, img in made.items():
    p = os.path.join(chain.OUT, 'sprites', rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    F.save(F.to_pil(np.clip(img, 0, 1)), p)
S = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(chain.OUT, 'sprites', 'chain')
files = [os.path.join(D, f) for f in ('flat_0.png', 'flat_1.png', 'flat_2.png', 'edge_0.png', 'edge_1.png', 'edge_2.png', 'hot.png')]
subprocess.run([sys.executable, os.path.join(S, 'sheet.py'), os.path.join(S, 'links_sheet.png'), '4.0', '#1e1819'] + files, check=True)
