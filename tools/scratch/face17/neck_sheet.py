"""neck_sheet.py TAG OUT: the owner's neck-length sheet: today, -1.5, -2 and -3 cm; front and profile at the Look,
and in play (camera 12, upscaled 3x); labelled, with the note that no helmet or gorget model exists yet."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import face_fit as ff  # noqa
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
tag, out = sys.argv[1], sys.argv[2]
font = ImageFont.truetype('arial.ttf', 22); small = ImageFont.truetype('arial.ttf', 18)
L = ['0', '-1.5', '-2', '-3']; names = {'0': 'today', '-1.5': '1.5 cm shorter', '-2': '2 cm shorter', '-3': '3 cm shorter'}
def img(n): return Image.open(os.path.join(S, n + '.png')).convert('RGB')
f0 = img('%s_nk0_f' % tag); lm = ff.detect(np.asarray(f0))[:, :2]
pup = (lm[468] + lm[473]) / 2; chin = lm[152]; u = chin[1] - pup[1]; cx = chin[0]
fbox = (int(cx - 1.25 * u), int(pup[1] - 0.9 * u), int(cx + 1.25 * u), int(chin[1] + 2.1 * u))
pbox = (560, 60, 1160, 960); qbox = (890, 380, 1030, 680)
W = 420
def fit(im, w): return im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)
rows = [('At the Look, front', [fit(img('%s_nk%s_f' % (tag, n)).crop(fbox), W) for n in L]),
        ('At the Look, profile', [fit(img('%s_nk%s_p' % (tag, n)).crop(pbox), W) for n in L]),
        ('In play (camera 12), 3x', [fit(img('%s_play12_nk%s' % (tag, n)).crop(qbox), W) for n in L])]
H = sum(r[1][0].height + 34 for r in rows) + 40 + 70
sh = Image.new('RGB', (4 * (W + 8) + 8, H), (24, 24, 24)); d = ImageDraw.Draw(sh)
for i, n in enumerate(L): d.text((8 + i * (W + 8) + 6, 8), names[n], fill=(255, 230, 120), font=font)
y = 40
for title, tiles in rows:
    d.text((10, y + 4), title, fill=(200, 200, 200), font=small); y += 30
    for i, t in enumerate(tiles): sh.paste(t, (8 + i * (W + 8), y))
    y += tiles[0].height + 4
d.text((10, y + 8), "Her neck only; her head, face and body are unchanged. No helmet, gorget or high-collar model exists yet,", fill=(230, 230, 230), font=small)
d.text((10, y + 32), "so none is shown: a longer neck leaves room for one without covering her bust.", fill=(230, 230, 230), font=small)
sh.save(out, quality=93); print(out, sh.size)
