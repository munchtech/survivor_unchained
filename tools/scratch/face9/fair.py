"""fair.py: a face's brows and lips measured at one size (brow-top to chin FACE_PX pixels, as fair_grain.py does), so a
sharp portrait twice a shot's size is not set against what a screen can show.

    fair.py TAG [ids...]        each face's white-rig shot (TAG_white, TAG_w_<id>) against its portrait
    fair.py --img A.png[@crop] [B.png ...]   any pictures

Brows (each side, then their mean): the outline (MediaPipe's, grown a little) against a ring of skin round it (not the
eye): `dark` the median of its darkest third over the skin (linear lightness), `mass` the mean darkening over the
outline (1 - L/skin: darkness and fullness both), `hair` how much of the outline is darker than 0.9 of the skin.
Lips: `up`/`lo` the upper and lower lip's heights and `w` the mouth's width, over the face's height (10 to 152);
`col` the lips' median colour over the skin's (linear, r g b), and `L` its lightness over the skin's; `edge` how much
darker the lips are than the skin just outside their outline (the border's contrast). Run with the facefit venv."""
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
from skin_sample import poly, BROW_A, BROW_B, LIPS
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29\tools\assets")
import face_fit as ff  # noqa: E402
from iris_sample import lin, EYE_R, EYE_L  # noqa: E402

FACE_PX = 380
LW = np.array([0.2126, 0.7152, 0.0722])
INNER = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29'
G = W + r'\godot\.shots'
S4 = r'C:\Users\munch\Desktop\survivorsunchained_inputs\face4'
CROP = [660, 150, 1160, 740]


def resize(img, size):
    """Made smaller as a camera or the GPU would (FAIR_LIN=1: an area average in linear light: thin dark hairs on
    light skin come out lighter than a LANCZOS in sRGB, which keeps them dark), else LANCZOS in sRGB."""
    import os
    if os.environ.get('FAIR_LIN') != '1' or size[0] >= img.width:
        return img.resize(size, Image.LANCZOS)
    a = np.asarray(img).astype(np.float32) / 255
    a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    out = np.stack([np.asarray(Image.fromarray(a[..., c]).resize(size, Image.BOX)) for c in range(3)], 2)
    out = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.maximum(out, 0) ** (1 / 2.4) - 0.055)
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))


def at_size(path, crop=None):
    img = Image.open(path).convert('RGB')
    if crop:
        img = img.crop(crop)
    a = np.asarray(img)
    up = 2 if a.shape[0] < 900 else 1
    big = np.asarray(img.resize((img.width * up, img.height * up), Image.LANCZOS))
    L = ff.detect(big)
    if L is None:
        return None, None
    L = L[:, :2] / up
    k = FACE_PX / np.linalg.norm(L[152] - L[10])
    im = resize(img, (max(1, round(img.width * k)), max(1, round(img.height * k))))
    a = np.asarray(im)
    # (landmarks again at this size: scaled ones drift a pixel or two at the brows)
    up = 2
    big = np.asarray(im.resize((im.width * up, im.height * up), Image.LANCZOS))
    L2 = ff.detect(big)
    L = (L2[:, :2] / up) if L2 is not None else L * k
    return a, L


def brows(a, L):
    li = lin(a)
    lum = li @ LW
    eyes = poly(a.shape, L[EYE_R], 6) | poly(a.shape, L[EYE_L], 6)
    out = []
    for ring in (BROW_A, BROW_B):
        m = poly(a.shape, L[ring], 2)
        around = ndimage.binary_dilation(m, iterations=7) & ~ndimage.binary_dilation(m, iterations=3) & ~eyes
        skin = np.median(li[around], 0)
        sl = skin @ LW
        pl = lum[m]
        dark = li[m][pl <= np.percentile(pl, 33)]
        b = np.median(dark, 0)
        out.append(((b @ LW) / sl, np.clip(1 - pl / sl, 0, 1).mean(), (pl < 0.9 * sl).mean(), b / skin))
    return [np.mean([o[i] for o in out], 0) for i in range(4)]


def lips(a, L):
    li = lin(a)
    lum = li @ LW
    h = np.linalg.norm(L[152] - L[10])
    outer = poly(a.shape, L[LIPS])
    inner = poly(a.shape, L[INNER], 1)
    lipm = ndimage.binary_erosion(outer, iterations=1) & ~inner
    # (the skin: a band round the lips' outline, past the border, not into the mouth)
    ring = ndimage.binary_dilation(outer, iterations=6) & ~ndimage.binary_dilation(outer, iterations=2)
    skin = np.median(li[ring], 0)
    col = np.median(li[lipm], 0)
    # (the border's contrast: just inside the outline against just outside it)
    ins = outer & ~ndimage.binary_erosion(outer, iterations=3) & ~inner
    ous = ndimage.binary_dilation(outer, iterations=3) & ~outer
    edge = 1 - np.median(lum[ins]) / np.median(lum[ous])
    up = np.linalg.norm(L[0] - L[13]) / h
    lo = np.linalg.norm(L[14] - L[17]) / h
    w = np.linalg.norm(L[61] - L[291]) / h
    return up, lo, w, col / skin, (col @ LW) / (skin @ LW), edge


def report(name, path, crop=None):
    a, L = at_size(path, crop)
    if a is None:
        print('%-10s no face' % name)
        return None
    br = brows(a, L)
    lp = lips(a, L)
    ear = (np.linalg.norm(L[159] - L[145]) / np.linalg.norm(L[33] - L[133]) + np.linalg.norm(L[386] - L[374]) / np.linalg.norm(L[263] - L[362])) / 2
    print('%-10s brows dark %.2f mass %.3f hair %.2f (r %.2f g %.2f b %.2f) | lips up %.3f lo %.3f w %.3f col %.2f %.2f %.2f L %.2f edge %.3f | eyes open %.3f' % (
        name, br[0], br[1], br[2], *br[3], lp[0], lp[1], lp[2], *lp[3], lp[4], lp[5], ear))
    return br, lp


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--img':
        for p in args[1:]:
            crop = None
            if '@' in p:
                p, c = p.split('@')
                crop = [int(v) for v in c.split(',')]
            report(p.replace('\\', '/').split('/')[-1][:10], p, crop)
        sys.exit()
    tag, ids = args[0], args[1:]
    P = json.load(open(W + r'\tools\assets\heroine_face\presets.json', encoding='utf-8'))
    res = {}
    for p in P:
        if ids and p['id'] not in ids:
            continue
        ref = S4 + (r'\from_face3\refs_her\her_23.png' if p['id'] == 'own' else '\\refs_front\\' + p['ref'].split('/')[-1] + '.png')
        shot = G + ('\\%s_white.png' % tag if p['id'] == 'own' else '\\%s_w_%s.png' % (tag, p['id']))
        a = report(p['id'] + ' ref', ref)
        b = report(p['id'] + ' game', shot, CROP)
        if a and b:
            res[p['id']] = {'ref': [list(map(float, np.ravel(np.hstack([x for x in a[0]])))), list(map(float, np.ravel(np.hstack(a[1]))))],
                            'game': [list(map(float, np.ravel(np.hstack([x for x in b[0]])))), list(map(float, np.ravel(np.hstack(b[1]))))]}
            print('%-10s brow mass game/ref %.2f, dark (1-L) game/ref %.2f | lips L game/ref %.2f, up %.2f lo %.2f' % (
                '', b[0][1] / max(a[0][1], 1e-6), (1 - b[0][0]) / max(1 - a[0][0], 1e-6), b[1][4] / a[1][4], b[1][0] / a[1][0], b[1][1] / a[1][1]))
    json.dump(res, open(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9\fair_%s.json' % tag, 'w'), indent=1)
