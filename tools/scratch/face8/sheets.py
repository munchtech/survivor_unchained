"""sheets.py TAG: the default side-by-side (four columns) and the ten-face sheet (each under its reference), as v7's."""
import json
import os
import sys
from PIL import Image, ImageDraw

tag = sys.argv[1]
w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
g = w + r'\godot\.shots'
s4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
H = 560


def fit(im, h=H):
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)


crop = (660, 150, 1160, 740)
cols = [('reference (her_23, Krea 2)', fit(Image.open(s4 + r'\from_face3\refs_her\her_23.png').convert('RGB').crop((100, 170, 934, 1150)))),
        ('before: FACE v3 in game', fit(Image.open(s4 + r'\from_face3\sbs_v3.jpg').convert('RGB').crop((468, 22, 865, 480)))),
        ('now (%s): Loose, Look close-up' % tag, fit(Image.open(g + r'\%s_long.png' % tag).convert('RGB').crop(crop))),
        ('now (%s): Tail, Look close-up' % tag, fit(Image.open(g + r'\%s_pony.png' % tag).convert('RGB').crop(crop)))]
S = Image.new('RGB', (sum(i.width for _, i in cols), H + 22), (16, 16, 16))
d = ImageDraw.Draw(S)
x = 0
for t, i in cols:
    S.paste(i, (x, 22))
    d.text((x + 6, 5), t, fill=(235, 235, 235))
    x += i.width
S.save(g + r'\sbs_default_%s.jpg' % tag, quality=90)
pre = json.load(open(w + r'\tools\assets\heroine_face\presets.json', encoding='utf-8'))
cw, rh = 330, 380
S = Image.new('RGB', (cw * 5, (rh * 2 + 22) * 2), (16, 16, 16))
d = ImageDraw.Draw(S)
for k, p in enumerate(pre):
    ref = p.get('ref', 'front/her_23').split('/')[-1]
    rp = s4 + (r'\refs_front\%s.png' % ref if p['id'] != 'own' else r'\from_face3\refs_her\her_23.png')
    shot = g + (r'\%s_pony.png' % tag if p['id'] == 'own' else r'\%s_p_%s.png' % (tag, p['id']))
    if not os.path.exists(shot):
        continue
    x, y = (k % 5) * cw, (k // 5) * (rh * 2 + 22)
    r = Image.open(rp).convert('RGB')
    r = r.crop((int(r.width * 0.12), int(r.height * 0.1), int(r.width * 0.88), int(r.height * 0.72))).resize((cw, rh), Image.LANCZOS)
    s = Image.open(shot).convert('RGB').crop((700, 160, 1120, 640)).resize((cw, rh), Image.LANCZOS)
    S.paste(r, (x, y + 22))
    S.paste(s, (x, y + 22 + rh))
    d.text((x + 6, y + 5), p['name'], fill=(235, 235, 235))
S.save(g + r'\presets_%s.jpg' % tag, quality=88)
print('SHEETS done', g + r'\sbs_default_%s.jpg' % tag, g + r'\presets_%s.jpg' % tag)
