"""regions.py OUT REGION ZOOM img[@crop] ...: one region of each face (brows, lips, eyes, cheek, jaw, face), every
picture brought to the first one's face size (landmarks 10 to 152), side by side, each pixel ZOOM times as a block.
The first is usually the portrait; the rest shots (crop x0,y0,x1,y1). Labels from the file names."""
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29\tools\assets")
import face_fit as ff  # noqa: E402

REG = {
    'brows': ([70, 63, 105, 66, 107, 300, 293, 334, 296, 336, 46, 276, 55, 285], (0.08, 0.08, 1.2, 1.0)),
    'lips': ([61, 291, 0, 17, 37, 267, 84, 314], (0.6, 0.6, 1.2, 0.9)),
    'eyes': ([33, 133, 263, 362, 159, 386, 145, 374], (0.25, 0.25, 1.4, 1.2)),
    'face': ([10, 152, 234, 454], (0.08, 0.08, 0.08, 0.08)),
    'jaw': ([152, 172, 397, 58, 288], (0.25, 0.25, 0.4, 0.2)),
    'cheekL': ([234, 50, 205, 187], (0.3, 0.3, 0.4, 0.4)),
    'cheekR': ([454, 280, 425, 411], (0.3, 0.3, 0.4, 0.4)),
}


def load(p):
    crop = None
    if '@' in p:
        p, c = p.split('@')
        crop = [int(v) for v in c.split(',')]
    im = Image.open(p).convert('RGB')
    if crop:
        im = im.crop(crop)
    return p, im


def marks(im):
    up = 2 if im.height < 900 else 1
    L = ff.detect(np.asarray(im.resize((im.width * up, im.height * up), Image.LANCZOS)))
    return None if L is None else L[:, :2] / up


out, reg, zoom = sys.argv[1], sys.argv[2], int(sys.argv[3])
idx, (ml, mr, mt, mb) = REG[reg]
tiles, size = [], None
for p in sys.argv[4:]:
    name, im = load(p)
    L = marks(im)
    if L is None:
        print('no face', name)
        continue
    h = np.linalg.norm(L[152] - L[10])
    if size is None:
        size = h
    k = size / h
    if abs(k - 1) > 0.01:
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        L = L * k
    q = L[idx]
    x0, y0 = q.min(0)
    x1, y1 = q.max(0)
    bw, bh = x1 - x0, y1 - y0
    box = [int(x0 - ml * bw), int(y0 - mt * bh), int(x1 + mr * bw), int(y1 + mb * bh)]
    t = im.crop(box)
    t = t.resize((t.width * zoom, t.height * zoom), Image.NEAREST)
    d = ImageDraw.Draw(t)
    d.rectangle([0, 0, 200, 14], fill=(0, 0, 0))
    d.text((3, 1), name.replace('\\', '/').split('/')[-1][:30], fill=(255, 255, 255))
    tiles.append(t)
if tiles[0].width > 2 * tiles[0].height:
    Wd = max(t.width for t in tiles)
    H = sum(t.height for t in tiles) + 4 * (len(tiles) - 1)
    sheet = Image.new('RGB', (Wd, H), (20, 20, 20))
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height + 4
else:
    H = max(t.height for t in tiles)
    Wd = sum(t.width for t in tiles) + 4 * (len(tiles) - 1)
    sheet = Image.new('RGB', (Wd, H), (20, 20, 20))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width + 4
sheet.save(out, quality=92)
print(out, sheet.size)
