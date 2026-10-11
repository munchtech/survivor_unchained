"""neck_sheet.py TAG OUT: the owner's neck-length sheet: today, -1.5, -2 and -3 cm; front and profile at the Look,
and in play facing the camera (camera 12, upscaled 3x); her portrait as a fifth column at the same eye-to-chin size; a
guide line at today's collarbone (env NOTCH_Y: its height in TAG_nk0_f.png); labelled, with the note that no helmet or
gorget model exists yet."""
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
R = "C:/Users/munch/Desktop/survivorsunchained_inputs/face4/refs_front"
ref = Image.open(os.path.join(R, 'own_her_23.png')).convert('RGB'); rl = ff.detect(np.asarray(ref))[:, :2]
rp = (rl[468] + rl[473]) / 2; rc = rl[152]; ru = rc[1] - rp[1]; k = u / ru
ref = ref.resize((int(ref.width * k), int(ref.height * k)), Image.LANCZOS); rp, rc = rp * k, rc * k
rbox = (int(rc[0] - 1.25 * u), int(rp[1] - 0.9 * u), int(rc[0] + 1.25 * u), int(rc[1] + 2.1 * u))
front = [fit(img('%s_nk%s_f' % (tag, n)).crop(fbox), W) for n in L] + [fit(ref.crop(rbox), W)]
ny = os.environ.get('NOTCH_Y')
if ny:
    gy = int((float(ny) - fbox[1]) * W / (fbox[2] - fbox[0]))
    for t in front[:4]:
        dd = ImageDraw.Draw(t)
        for x0 in range(0, W, 14): dd.line((x0, gy, x0 + 8, gy), fill=(120, 230, 255), width=2)
rows = [("At the Look, front (dashed: today's collarbone; right: her portrait at the same eye-to-chin size)", front),
        ('At the Look, profile', [fit(img('%s_nk%s_p' % (tag, n)).crop(pbox), W) for n in L]),
        ('In play facing the camera (camera 12), 3x. Seen from behind in play, the four read alike.',
         [fit(img('%s_pf_nk%s' % (tag, n)).crop(qbox), W) for n in L])]
H = sum(r[1][0].height + 34 for r in rows) + 40 + 70
sh = Image.new('RGB', (5 * (W + 8) + 8, H + 24), (24, 24, 24)); d = ImageDraw.Draw(sh)
for i, n in enumerate(L): d.text((8 + i * (W + 8) + 6, 8), names[n], fill=(255, 230, 120), font=font)
d.text((8 + 4 * (W + 8) + 6, 8), 'her portrait', fill=(255, 230, 120), font=font)
y = 40
for title, tiles in rows:
    d.text((10, y + 4), title, fill=(200, 200, 200), font=small); y += 30
    for i, t in enumerate(tiles): sh.paste(t, (8 + i * (W + 8), y))
    y += tiles[0].height + 4
d.text((10, y + 8), "Her neck only; her head, face and body are unchanged. No helmet, gorget or high-collar model exists yet,", fill=(230, 230, 230), font=small)
d.text((10, y + 32), "so none is shown: a longer neck leaves room for one without covering her bust.", fill=(230, 230, 230), font=small)
d.text((10, y + 56), "By a rough measure today's neck is about a third longer than the ten portraits'; 3 cm shorter matches them. Today's length stays a full option.", fill=(230, 230, 230), font=small)
sh.save(out, quality=93); print(out, sh.size)
