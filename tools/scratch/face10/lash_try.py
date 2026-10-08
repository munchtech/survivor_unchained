"""lash_try.py OUT.png [seed]: heroine_lashes.paint() on the cards in lash_rows.json (no Blender), and a sheet of the
paint on skin at 1:1 and the alpha (OUT_sheet.jpg)."""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abe65bc929823a791\tools\assets")
import heroine_lashes as hl  # noqa: E402

D = os.path.dirname(os.path.abspath(__file__))
grids = []
for c in json.load(open(os.path.join(D, 'lash_rows.json'))):
    co, uv = np.array(c['co']), np.array(c['uv'])
    if abs(co[0, 0, 0]) > abs(co[0, -1, 0]):
        co, uv = co[:, ::-1], uv[:, ::-1]
    grids.append({'co': co, 'uv': uv, 'upper': c['upper']})
out = sys.argv[1]
img = hl.paint(grids, seed=int(sys.argv[2]) if len(sys.argv) > 2 else hl.SEED)
Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(out)
a = img[..., 3:4]
skin = np.array([0.93, 0.82, 0.74])
over = img[..., :3] * a + skin * (1 - a)
sheet = np.concatenate([over, np.repeat(a, 3, 2)], 1)
Image.fromarray((sheet * 255).astype(np.uint8)).save(out.replace('.png', '_sheet.jpg'), quality=92)
print('painted', out, 'cover>0.05: %.1f%%' % (100 * (a > 0.05).mean()))
