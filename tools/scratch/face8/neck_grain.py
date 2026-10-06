"""neck_grain.py img[@crop] ... : fair_grain's measure on her face's cheeks and on her neck (a box from a quarter to
three fifths of her face's height under her chin, the middle half of her jaw's width), each scaled as fair_grain
scales, and the neck's over the face's: does her neck's skin read as her face's does?"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
import skin_sample as ss
from fair_grain import FACE_PX


def both(path, crop=None):
    img = Image.open(path).convert('RGB')
    if crop:
        img = img.crop(crop)
    a = np.asarray(img)
    up = 2 if a.shape[0] < 900 else 1
    L = ss.ff.detect(np.asarray(img.resize((img.width * up, img.height * up), Image.LANCZOS)))
    if L is None:
        return None
    L = L[:, :2] / up
    h = np.linalg.norm(L[152] - L[10])
    k = FACE_PX / h
    im = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
    a = np.asarray(im)
    L = L * k
    li = ss.lin(a) @ [0.2126, 0.7152, 0.0722]
    oval = ndimage.binary_erosion(ss.poly(a.shape, L[ss.ff.OVAL]), iterations=4)
    feat = np.zeros_like(oval)
    for ring in (ss.EYE_R, ss.EYE_L, ss.BROW_A, ss.BROW_B, ss.LIPS, ss.NOSE):
        feat |= ss.poly(a.shape, L[ring], 3)
    rows = np.arange(a.shape[0])[:, None] * np.ones(a.shape[1])[None]
    top = L[[105, 334], 1].min() - 0.35 * (L[152, 1] - L[10, 1]) * 0.25
    face = oval & ~feat & (rows > top)
    chin = L[152]
    hw = abs(L[397, 0] - L[172, 0]) * 0.25
    neck = np.zeros_like(face)
    y0, y1 = int(chin[1] + 0.25 * FACE_PX), int(chin[1] + 0.6 * FACE_PX)
    neck[max(y0, 0):min(y1, a.shape[0]), int(chin[0] - hw):int(chin[0] + hw)] = True
    if neck.sum() < 200:
        return None
    out = []
    for m in (face, neck):
        mean = li[m].mean()
        out.append([(li - ndimage.gaussian_filter(li, s))[m].std() / mean for s in (0.8, 1.6, 3.2)])
    return out


if __name__ == '__main__':
    print('%-22s %-26s %-26s %s' % ('', 'face s0.8 s1.6 s3.2', 'neck s0.8 s1.6 s3.2', 'neck/face'))
    for p in sys.argv[1:]:
        c = None
        if '@' in p:
            p, b = p.split('@')
            c = [int(v) for v in b.split(',')]
        r = both(p, c)
        n = p.replace('\\', '/').split('/')[-1][:22]
        if r is None:
            print(n, 'no face or neck')
            continue
        f, k = np.array(r[0]), np.array(r[1])
        print('%-22s %s   %s   %s' % (n, ' '.join('%.4f' % v for v in f), ' '.join('%.4f' % v for v in k), ' '.join('%.2f' % v for v in k / f)))
