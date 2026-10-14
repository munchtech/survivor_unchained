"""ruler.py OUT IMG...: each image from the eyes to below the collarbones, scaled so pupil-to-chin is 100 px, with
lines below the chin at 0.25 steps of pupil-to-chin (labelled), to read where the sternal notch falls."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import face_fit as ff  # noqa
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
R = r"C:\Users\munch\Desktop\survivorsunchained_inputs\face4\refs_front"
font = ImageFont.truetype('arial.ttf', 13)
tiles = []
for n in sys.argv[2:]:
    p = next(q for q in (os.path.join(S, n + '.png'), os.path.join(R, n + '.png')) if os.path.exists(q))
    im = Image.open(p).convert('RGB'); up = 2 if im.height < 900 else 1
    L = ff.detect(np.asarray(im.resize((im.width * up, im.height * up), Image.LANCZOS)))
    if L is None:   # (a small face in a wide frame: look again in its middle third, doubled)
        c = im.crop((im.width // 3, 0, 2 * im.width // 3, im.height // 2)); L = ff.detect(np.asarray(c.resize((c.width * 2, c.height * 2), Image.LANCZOS)))
        if L is None: print("no face", n); continue
        L = L[:, :2] / 2 + [im.width // 3, 0]
    else: L = L[:, :2] / up
    pupil = (L[468] + L[473]) / 2; chin = L[152]; u = chin[1] - pupil[1]; k = 240 / u
    box = (chin[0] - 0.8 * u, chin[1] - 0.15 * u, chin[0] + 0.8 * u, chin[1] + 1.2 * u)
    t = im.crop(tuple(int(v) for v in box)).resize((int(1.6 * u * k), int(1.35 * u * k)), Image.LANCZOS)
    d = ImageDraw.Draw(t); y0 = (chin[1] - box[1]) * k
    for j in range(0, 10):
        y = y0 + j * 30
        d.line((0, y, t.width, y), fill=(0, 255, 255), width=1); d.line((t.width - 18, y, t.width, y), fill=(0, 255, 255), width=1)
        d.text((20, y - 7), "%.3f" % (j * 0.125), fill=(0, 255, 255), font=font)
    d.text((4, 2), n, fill=(255, 255, 0), font=font)
    tiles.append(t)
cols = 5; tw, th = tiles[0].width, tiles[0].height
sh = Image.new('RGB', (cols * (tw + 4), ((len(tiles) + cols - 1) // cols) * (th + 4)), (10, 10, 10))
for i, t in enumerate(tiles): sh.paste(t.resize((tw, th)), ((i % cols) * (tw + 4), (i // cols) * (th + 4)))
sh.save(sys.argv[1], quality=92); print(sh.size)
