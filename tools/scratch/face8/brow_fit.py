"""brow_fit.py TAG [ids...]: each face's brows under the white rig (TAG_w_<id>.png; hers TAG_white.png) against its
portrait's: within each brow's outline (MediaPipe's, grown a little), how dark the brow is against the skin under it
(median of its darkest third, linear, per channel and in lightness), how much of the outline is hair (darker than
the skin by a tenth), and its outline's height over the eye's width. Run with the facefit venv's python."""
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
from skin_sample import poly, BROW_A, BROW_B, measure as skin_measure
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\tools\assets")
import face_fit as ff  # noqa: E402
from iris_sample import lin  # noqa: E402

tag = sys.argv[1]
ids = sys.argv[2:]
w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
g = w + r'\godot\.shots'
s4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
crop = [660, 150, 1160, 740]
LW = np.array([0.2126, 0.7152, 0.0722])
P = json.load(open(w + r'\tools\assets\heroine_face\presets.json', encoding='utf-8'))


def brows(path, crop=None):
    img = np.asarray(Image.open(path).convert('RGB'))
    if crop:
        img = img[crop[1]:crop[3], crop[0]:crop[2]]
    if img.shape[0] < 900:
        img = np.asarray(Image.fromarray(img).resize((img.shape[1] * 2, img.shape[0] * 2), Image.LANCZOS))
    L = ff.detect(img)
    if L is None:
        return None
    L = L[:, :2]
    li = lin(img)
    lum = li @ LW
    g_ = max(2, img.shape[0] // 150)
    out = []
    for ring, under in ((BROW_A, (223, 222, 221)), (BROW_B, (443, 442, 441))):
        m = poly(img.shape, L[ring], g_)
        # (the skin under it: the lid's top, between brow and eye)
        ys = L[list(under), 1].mean()
        xs = L[list(under), 0]
        sk = li[int(ys) - g_:int(ys) + g_, int(xs.min()):int(xs.max())].reshape(-1, 3)
        skin = np.median(sk, 0)
        px, pl = li[m], lum[m]
        dark = px[pl <= np.percentile(pl, 33)]
        b = np.median(dark, 0)
        hair = (pl < 0.9 * (skin @ LW)).mean()
        out.append((b / skin, (b @ LW) / (skin @ LW), hair))
    return [np.mean([o[0] for o in out], 0), np.mean([o[1] for o in out]), np.mean([o[2] for o in out])]


for p in P:
    if ids and p['id'] not in ids:
        continue
    ref = s4 + (r'\from_face3\refs_her\her_23.png' if p['id'] == 'own' else '\\refs_front\\' + p['ref'].split('/')[-1] + '.png')
    shot = g + ('\\%s_white.png' % tag if p['id'] == 'own' else '\\%s_w_%s.png' % (tag, p['id']))
    a, b = brows(ref), brows(shot, crop)
    if a is None or b is None:
        print(p['id'], 'no face')
        continue
    print('%-9s brow/skin  portrait r %.2f g %.2f b %.2f L %.2f hair %.2f | game r %.2f g %.2f b %.2f L %.2f hair %.2f' % (
        p['id'], *a[0], a[1], a[2], *b[0], b[1], b[2]))
