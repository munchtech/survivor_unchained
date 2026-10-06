"""grid4.py OUT SCALE img... : images (shots dir names or paths) scaled and laid two to a row, each labelled."""
import os
import sys
from PIL import Image, ImageDraw

G = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\godot\.shots'
D = os.path.dirname(os.path.abspath(__file__))
out, s = sys.argv[1], float(sys.argv[2])
fs = sys.argv[3:]
ims = []
for f in fs:
    box = None
    if '@' in f:
        f, b = f.split('@')
        box = tuple(int(v) for v in b.split(','))
    p = f if os.path.isabs(f) else (os.path.join(G, f) if os.path.exists(os.path.join(G, f)) else os.path.join(D, f))
    im = Image.open(p).convert('RGB')
    if box:
        im = im.crop(box)
    ims.append((os.path.basename(f) + (' %s' % (box,) if box else ''), im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)))
cols = 2 if len(ims) > 1 else 1
cw = max(i.width for _, i in ims)
rh = max(i.height for _, i in ims) + 16
rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cw * cols + 4 * (cols - 1), rh * rows), (255, 0, 255))
d = ImageDraw.Draw(S)
for k, (n, i) in enumerate(ims):
    x, y = (k % cols) * (cw + 4), (k // cols) * rh
    S.paste(i, (x, y + 16))
    d.rectangle((x, y, x + cw, y + 15), fill=(16, 16, 16))
    d.text((x + 4, y + 2), n, fill=(235, 235, 235))
S.save(os.path.join(D, out), quality=90)
print(out, S.size)
