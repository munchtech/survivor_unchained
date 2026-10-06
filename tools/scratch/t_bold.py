import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import svgglyph as G, numpy as np
from PIL import Image
import preview as PV
keys = ['skull', 'coin', 'heart', 'flame', 'lock', 'eye', 'scroll', 'quest', 'talk', 'map', 'sun', 'moon', 'key', 'helm', 'ring', 'compass']
ims = []
for k in keys:
    b, c = G.bold(k, 128, stroke=2.2)
    a = np.clip(b - c, 0, 1)
    ims.append(Image.fromarray((a * 255).astype(np.uint8)).convert('RGBA'))
PV.sheet(ims, cols=8).save(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\glyph_bold.png')
