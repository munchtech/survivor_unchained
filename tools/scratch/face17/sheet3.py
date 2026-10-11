"""sheet3.py TAG OUTDIR: the judge's sheets for the Look's rig and skin trims."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import face_fit as ff  # noqa
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
R = r"C:\Users\munch\Desktop\survivorsunchained_inputs\face4\refs_front"
tag, O = sys.argv[1], sys.argv[2]
os.makedirs(O, exist_ok=True)
font = ImageFont.truetype('arial.ttf', 18)
def img(n):
    for p in (os.path.join(S, n + '.png'), os.path.join(R, n + '.png')):
        if os.path.exists(p): return Image.open(p).convert('RGB')
def lm(im):
    up = 2 if im.height < 900 else 1
    return ff.detect(np.asarray(im.resize((im.width * up, im.height * up), Image.LANCZOS)))[:, :2] / up
def face_crop(n, W):
    im = img(n); L = lm(im); h = np.linalg.norm(L[152] - L[10]); cx = L[1][0]
    t = im.crop((int(cx - 0.62 * h), int(L[10][1] - 0.12 * h), int(cx + 0.62 * h), int(L[152][1] + 0.62 * h)))
    return t.resize((W, int(W * t.height / t.width)), Image.LANCZOS)
def grid(rows, out, gap=6):
    W = max(sum(t.width for _, t in r) + gap * (len(r) - 1) for r in rows); H = sum(max(t.height for _, t in r) + 24 for r in rows)
    sh = Image.new('RGB', (W, H), (15, 15, 15)); d = ImageDraw.Draw(sh); y = 0
    for r in rows:
        x = 0
        for lab, t in r: d.text((x + 4, y + 2), lab, fill=(255, 255, 255), font=font); sh.paste(t, (x, y + 24)); x += t.width + gap
        y += max(t.height for _, t in r) + 24
    sh.save(os.path.join(O, out), quality=93); print(out, sh.size)
REF = {'own': 'own_her_23'}
faces = ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']
W = 340
for half, fs in (('a', faces[:5]), ('b', faces[5:])):
    rows = [[], []]
    for f in fs:
        rows[0].append(('%s render' % f, face_crop('%s_%s' % (tag, f), W)))
        rows[1].append(('%s portrait' % f, face_crop(REF.get(f, f + '_11'), W)))
    grid(rows, 'skin_%s.jpg' % half)
rows = []
for f in ('own', 'highborn'):
    old = '%s_%s_was' % (tag, f)
    rows.append([('%s before (body tone half, no shade tint)' % f, face_crop(old, W)), ('%s untrimmed' % f, face_crop('%s_%s_untrim' % (tag, f), W)),
                 ('%s new rig + trims' % f, face_crop('%s_%s' % (tag, f), W)), ('%s portrait' % f, face_crop(REF.get(f, f + '_11'), W))])
grid(rows, 'trim_ab.jpg')
# turned 40: the ear and cheek (fixed crop round her ear side)
rows = [[]]
for f in ('own', 'highborn', 'sunborn', 'saffron'):
    t = img('%s_%s_t40' % (tag, f)); rows[0].append(('%s t40' % f, t.crop((700, 200, 1220, 820)).resize((390, 465), Image.LANCZOS)))
grid(rows, 'ears_t40.jpg')
# the whole frame at the Look (armour, particles), halved
rows = [[('own close (default framing), half size', img('%s_own' % tag).resize((960, 540), Image.LANCZOS)), ('own head and shoulders, half size', img('%s_own_bust' % tag).resize((960, 540), Image.LANCZOS))]]
grid(rows, 'frames.jpg')
