"""brows_view.py OUT [ids...]: her brows' mask (paint/brows.png) outlined over each face's head paint, around the
brows (UV space), to see whether each face's own brows lie in it."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
sc = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
out = sys.argv[1]
ids = sys.argv[2:] or ['own']
m = np.asarray(Image.open(w + r'\godot\art\people\paint\brows.png').convert('RGBA'))[..., 3].astype(np.float32) / 255
S = m.shape[0]
ys, xs = np.nonzero(m > 0.1)
y0, y1, x0, x1 = ys.min() - 40, ys.max() + 40, xs.min() - 40, xs.max() + 40
edge = (m > 0.3) & ~ndimage.binary_erosion(m > 0.3, iterations=2)
tiles = []
for i in ids:
    p = w + r'\godot\art\people\head_tex\heroine_head%s.jpg' % ('' if i == 'own' else '_' + i)
    h = np.asarray(Image.open(p).convert('RGB').resize((S, S), Image.LANCZOS)).copy()
    h[edge] = (0, 255, 255)
    tiles.append(h[y0:y1, x0:x1])
im = np.concatenate(tiles, 0)
Image.fromarray(im).save(sc + '\\' + out)
print(out, im.shape, (y0, y1, x0, x1))
