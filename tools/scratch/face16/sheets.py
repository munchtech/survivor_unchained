"""sheets.py: judge j1's sheets. Run with the facefit venv (landmarks align render and portrait crops)."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import face_fit as ff  # noqa
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
R = r"C:\Users\munch\Desktop\survivorsunchained_inputs\face4\refs_front"
O = os.environ['SHEETS']
font = ImageFont.truetype('arial.ttf', 20)
def img(n):
    p = os.path.join(S, n + '.png') if os.path.exists(os.path.join(S, n + '.png')) else os.path.join(R, n + '.png')
    return Image.open(p).convert('RGB')
def lm(im):
    up = 2 if im.height < 900 else 1
    return ff.detect(np.asarray(im.resize((im.width * up, im.height * up), Image.LANCZOS)))[:, :2] / up
def neck_crop(n, W):
    im = img(n); L = lm(im); h = np.linalg.norm(L[152] - L[10]); c = L[152]
    box = (c[0] - 0.6 * h, c[1] - 0.45 * h, c[0] + 0.6 * h, c[1] + 0.55 * h)
    t = im.crop(tuple(int(v) for v in box))
    if W is None: return t, h
    return t.resize((W, int(W * t.height / t.width)), Image.LANCZOS), h
def eyes_crop(n, W):
    im = img(n); L = lm(im); h = np.linalg.norm(L[152] - L[10]); c = (L[33] + L[263]) / 2
    t = im.crop(tuple(int(v) for v in (c[0] - 0.5 * h, c[1] - 0.14 * h, c[0] + 0.5 * h, c[1] + 0.14 * h)))
    if W is None: W = 2 * t.width
    return t.resize((W, int(W * t.height / t.width)), Image.LANCZOS)
def grid(rows, out, gap=6):
    W = max(sum(t.width for _, t in r) + gap * (len(r) - 1) for r in rows); H = sum(max(t.height for _, t in r) + 26 for r in rows)
    sh = Image.new('RGB', (W, H), (15, 15, 15)); d = ImageDraw.Draw(sh); y = 0
    for r in rows:
        x = 0
        for lab, t in r: d.text((x + 4, y + 2), lab, fill=(255, 255, 255), font=font); sh.paste(t, (x, y + 26)); x += t.width + gap
        y += max(t.height for _, t in r) + 26
    sh.save(os.path.join(O, out), quality=94); print(out, sh.size)
FACES = [('own', 't2_own', None), ('highborn', 't2_highborn', 'highborn_11'), ('doe', 't3_doe', 'doe_11'), ('sunborn', 't3_sunborn', 'sunborn_11'),
         ('vixen', 't4_vixen', 'vixen_11'), ('moonlit', 't3_moonlit', 'moonlit_11'), ('saffron', 't3_saffron', 'saffron_11'),
         ('wildling', 't3_wildling', 'wildling_11'), ('hardwon', 't4_hardwon', 'hardwon_11'), ('fey', 't4_fey', 'fey_11')]
which = sys.argv[1]
if len(sys.argv) > 2: FACES = [(f, sys.argv[2] + '_' + f, r) for f, _, r in FACES]
if which == 'neck':
    for half, fs in (('a', FACES[:5]), ('b', FACES[5:])):
        rows = []
        for f, shot, ref in fs:
            r = [(f + ' render (1:1 of face height %d px)', None)]
            t, h = neck_crop(shot, None); r = [('%s render 1:1' % f, t)]
            if ref: r.append(('%s portrait' % f, neck_crop(ref, t.width)[0]))
            rows.append(r)
        grid(rows, 'neck_%s.jpg' % half)
if which == 'eyes':
    rows = []
    for f, shot, ref in FACES:
        if f not in ('doe', 'sunborn', 'moonlit', 'saffron'): continue
        rt = eyes_crop(shot, None); rows_w = rt.width
        rows.append([('%s render 2x' % f, rt), ('%s portrait' % f, eyes_crop(ref, rows_w))])
    grid(rows, 'eyes_dark4.jpg')
