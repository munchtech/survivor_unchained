"""pair.py OUT.jpg SHOT[@x0,y0,x1,y1] REF [SHOT2[@crop] REF2 ...]: each game crop beside its portrait, the portrait
scaled so its face (MediaPipe 10 to 152) is as tall as the crop's face; at 1:1 for the game crop (no rescale).
Run with the facefit venv."""
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abe65bc929823a791\tools\assets")
import face_fit as ff  # noqa: E402


def face_h(img):
    a = np.asarray(img.convert('RGB'))
    up = 2 if a.shape[0] < 900 else 1
    L = ff.detect(np.asarray(img.convert('RGB').resize((img.width * up, img.height * up), Image.LANCZOS)))
    if L is None:
        return None, None
    L = L[:, :2] / up
    return np.linalg.norm(L[152] - L[10]), L


def load(spec):
    p, _, c = spec.partition('@')
    im = Image.open(p).convert('RGB')
    if c:
        im = im.crop(tuple(int(v) for v in c.split(',')))
    return im


out = sys.argv[1]
items = sys.argv[2:]
rows = []
for shot, ref in zip(items[0::2], items[1::2]):
    g = load(shot)
    r = load(ref)
    hg, Lg = face_h(g)
    hr, Lr = face_h(r)
    if hg and hr:
        k = hg / hr
        r = r.resize((max(1, round(r.width * k)), max(1, round(r.height * k))), Image.LANCZOS)
        # (the portrait cropped about its face as the game crop is about its own)
        cx, cy = (Lr[10] + Lr[152]) / 2 * k
        gx, gy = (Lg[10] + Lg[152]) / 2
        x0, y0 = int(cx - gx), int(cy - gy)
        r = r.crop((x0, y0, x0 + g.width, y0 + g.height))
    else:
        r = r.resize((round(r.width * g.height / r.height), g.height), Image.LANCZOS)
    row = Image.new('RGB', (g.width + r.width + 8, max(g.height, r.height)), (20, 20, 20))
    row.paste(g, (0, 0))
    row.paste(r, (g.width + 8, 0))
    rows.append(row)
W = max(r.width for r in rows)
sheet = Image.new('RGB', (W, sum(r.height for r in rows) + 8 * (len(rows) - 1)), (20, 20, 20))
y = 0
for r in rows:
    sheet.paste(r, (0, y))
    y += r.height + 8
sheet.save(out, quality=93)
print(out, sheet.size)
