"""cheeks_sheet.py OUT TAG [ids...]: each face's cheek and nose (under the eyes to the mouth), the portrait beside the
Look's close-up (TAG_pony / TAG_p_<id>), both scaled to one face size, at 2x: freckles judged by eye."""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\tools\assets")
import face_fit as ff  # noqa: E402

out, tag = sys.argv[1:3]
ids = sys.argv[3:]
w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
g = w + r'\godot\.shots'
s4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
sc = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
P = json.load(open(w + r'\tools\assets\heroine_face\presets.json', encoding='utf-8'))
FACE = 380   # brow-top to chin, the Look's close-up


def cheek(path, crop=None):
    im = Image.open(path).convert('RGB')
    if crop:
        im = im.crop(crop)
    a = np.asarray(im)
    k = 2 if a.shape[0] < 900 else 1
    L = ff.detect(np.asarray(im.resize((im.width * k, im.height * k), Image.LANCZOS)))
    if L is None:
        return None
    L = L[:, :2] / k
    s = FACE / np.linalg.norm(L[152] - L[10])
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    L = L * s
    x0, x1 = L[234, 0] + 0.1 * (L[454, 0] - L[234, 0]), L[454, 0] - 0.1 * (L[454, 0] - L[234, 0])
    y0, y1 = L[[145, 374], 1].max() + 8, L[[61, 291], 1].min()
    c = im.crop((int(x0), int(y0), int(x1), int(y1)))
    return c.resize((c.width * 2, c.height * 2), Image.LANCZOS)


rows = []
for p in P:
    if ids and p['id'] not in ids:
        continue
    ref = s4 + (r'\from_face3\refs_her\her_23.png' if p['id'] == 'own' else '\\refs_front\\' + p['ref'].split('/')[-1] + '.png')
    shot = g + ('\\%s_pony.png' % tag if p['id'] == 'own' else '\\%s_p_%s.png' % (tag, p['id']))
    a, b = cheek(ref), cheek(shot, (560, 100, 1360, 900))
    if a is None or b is None:
        print(p['id'], 'no face')
        continue
    rows.append((p['name'], a, b))
W = max(a.width + b.width for _, a, b in rows) + 6
H = sum(max(a.height, b.height) + 16 for _, a, b in rows)
S = Image.new('RGB', (W, H), (16, 16, 16))
d = ImageDraw.Draw(S)
y = 0
for n, a, b in rows:
    d.text((4, y + 2), n, fill=(235, 235, 235))
    S.paste(a, (0, y + 16))
    S.paste(b, (a.width + 6, y + 16))
    y += max(a.height, b.height) + 16
S.save(sc + '\\' + out, quality=90)
print(out, S.size)
