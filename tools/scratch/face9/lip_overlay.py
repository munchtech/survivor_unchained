"""lip_overlay.py DIR OUT: the reference's lips (MediaPipe on DIR/painted_front.png) outlined on her clay (DIR/clay_front.png)
and on the painting, the mouth cropped and doubled: does the painted mouth lie on the sculpted one?"""
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29\tools\assets")
import face_fit as ff  # noqa: E402

D, out = sys.argv[1], sys.argv[2]
OUTER = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]
INNER = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
paint = Image.open(D + r'\painted_front.png').convert('RGB')
clay = Image.open(D + r'\clay_front.png').convert('RGB')
Lp = ff.detect(np.asarray(paint))[:, :2]
Lc = ff.detect(np.asarray(clay))
Lc = Lc[:, :2] if Lc is not None else None
q = Lp[OUTER]
x0, y0 = q.min(0) - [60, 70]
x1, y1 = q.max(0) + [60, 50]
tiles = []
for im in (clay, paint):
    im = im.copy()
    d = ImageDraw.Draw(im)
    d.line([tuple(v) for v in Lp[OUTER + OUTER[:1]]], fill=(0, 255, 255), width=1)
    d.line([tuple(v) for v in Lp[INNER + INNER[:1]]], fill=(0, 255, 255), width=1)
    if Lc is not None:
        d.line([tuple(v) for v in Lc[OUTER + OUTER[:1]]], fill=(255, 0, 255), width=1)
    t = im.crop((int(x0), int(y0), int(x1), int(y1)))
    tiles.append(t.resize((t.width * 2, t.height * 2), Image.LANCZOS))
s = Image.new('RGB', (tiles[0].width * 2 + 4, tiles[0].height))
s.paste(tiles[0], (0, 0))
s.paste(tiles[1], (tiles[0].width + 4, 0))
s.save(out, quality=92)
h = np.linalg.norm(Lp[152] - Lp[10])
print('portrait lips on the front: upper %.3f lower %.3f of the face' % (np.linalg.norm(Lp[0] - Lp[13]) / h, np.linalg.norm(Lp[14] - Lp[17]) / h))
if Lc is not None:
    print('clay lips (MediaPipe on the clay): upper %.3f lower %.3f' % (np.linalg.norm(Lc[0] - Lc[13]) / h, np.linalg.norm(Lc[14] - Lc[17]) / h))
