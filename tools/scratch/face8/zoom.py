"""zoom.py OUT SCALE img@x0,y0,x1,y1 ... : boxes from shots, enlarged by SCALE with no smoothing (each pixel a block),
side by side: what the player's pixels are."""
import os
import sys
from PIL import Image

G = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\godot\.shots'
D = os.path.dirname(os.path.abspath(__file__))
out, s = sys.argv[1], int(sys.argv[2])
ims = []
for a in sys.argv[3:]:
    f, b = a.split('@')
    p = f if os.path.isabs(f) else (os.path.join(G, f) if os.path.exists(os.path.join(G, f)) else os.path.join(D, f))
    im = Image.open(p).convert('RGB').crop(tuple(int(v) for v in b.split(',')))
    ims.append(im.resize((im.width * s, im.height * s), Image.NEAREST))
S = Image.new('RGB', (sum(i.width for i in ims) + 6 * (len(ims) - 1), max(i.height for i in ims)), (255, 0, 255))
x = 0
for i in ims:
    S.paste(i, (x, 0))
    x += i.width + 6
S.save(os.path.join(D, out))
print(out, S.size)
