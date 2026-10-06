"""eyes_sheet.py OUT KIND TAG [ids...]: each face's brows and eyes band, the portrait over the render, each found by its
landmarks and scaled to one width. KIND: w (TAG_w_<id>, the white rig) or p (TAG_p_<id>, the Look). Run with the
facefit venv's python."""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\tools\assets")
import face_fit as ff  # noqa: E402

out, kind, tag = sys.argv[1:4]
ids = sys.argv[4:]
w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
g = w + r'\godot\.shots'
s4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
sc = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
P = json.load(open(w + r'\tools\assets\heroine_face\presets.json', encoding='utf-8'))
W = 600


def band(path, crop=None):
    im = Image.open(path).convert('RGB')
    if crop:
        im = im.crop(crop)
    a = np.asarray(im)
    k = 1
    if a.shape[0] < 900:
        k = 2
        a = np.asarray(im.resize((im.width * 2, im.height * 2), Image.LANCZOS))
    L = ff.detect(a)
    if L is None:
        return None
    L = L[:, :2] / k
    x0, x1 = L[[33, 263, 127, 356], 0].min(), L[[33, 263, 127, 356], 0].max()
    span = x1 - x0
    yb = L[[105, 334, 66, 296], 1].min()
    ye = L[[145, 374], 1].max()
    y0, y1 = yb - 0.12 * span, ye + 0.1 * span
    b = im.crop((int(x0 - 0.04 * span), int(y0), int(x1 + 0.04 * span), int(y1)))
    return b.resize((W, int(b.height * W / b.width)), Image.LANCZOS)


rows = []
for p in P:
    if ids and p['id'] not in ids:
        continue
    ref = s4 + (r'\from_face3\refs_her\her_23.png' if p['id'] == 'own' else '\\refs_front\\' + p['ref'].split('/')[-1] + '.png')
    if kind == 'w':
        shot = g + ('\\%s_white.png' % tag if p['id'] == 'own' else '\\%s_w_%s.png' % (tag, p['id']))
    else:
        shot = g + ('\\%s_pony.png' % tag if p['id'] == 'own' else '\\%s_p_%s.png' % (tag, p['id']))
    a, b = band(ref), band(shot, (560, 100, 1360, 900))
    if a is None or b is None:
        print(p['id'], 'no face')
        continue
    rows.append((p['name'], a, b))
H = sum(a.height + b.height + 18 for _, a, b in rows)
cols = 2 if len(rows) > 3 else 1
per = (len(rows) + cols - 1) // cols
colH = [sum(a.height + b.height + 18 for _, a, b in rows[c * per:(c + 1) * per]) for c in range(cols)]
S = Image.new('RGB', (W * cols + 6 * (cols - 1), max(colH)), (16, 16, 16))
d = ImageDraw.Draw(S)
for c in range(cols):
    y = 0
    for n, a, b in rows[c * per:(c + 1) * per]:
        x = c * (W + 6)
        d.text((x + 4, y + 3), n, fill=(235, 235, 235))
        S.paste(a, (x, y + 16))
        S.paste(b, (x, y + 16 + a.height))
        y += a.height + b.height + 18
S.save(sc + '\\' + out, quality=90)
print('written', out, S.size)
