"""fair_grain.py img[@crop] ...: each face's skin grain with every face first scaled to one size (brow-top to chin
FACE_PX pixels, the size of her face at the Look's close-up), at fine and middling scales: what a player could see of
it at that size. (skin_sample.py's grain is relative to its picture's height, so a portrait twice the pixels of a
shot shows grain the screen can't.)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
import skin_sample as ss

FACE_PX = 380


def grain(path, crop=None):
    img = Image.open(path).convert("RGB")
    if crop:
        img = img.crop(crop)
    a = np.asarray(img)
    up = 2 if a.shape[0] < 900 else 1
    big = np.asarray(img.resize((img.width * up, img.height * up), Image.LANCZOS))
    L = ss.ff.detect(big)
    if L is None:
        return None
    L = L[:, :2] / up
    h = np.linalg.norm(L[152] - L[10])
    k = FACE_PX / h
    im = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
    a = np.asarray(im)
    L = L * k
    oval = ndimage.binary_erosion(ss.poly(a.shape, L[ss.ff.OVAL]), iterations=4)
    feat = np.zeros_like(oval)
    for ring in (ss.EYE_R, ss.EYE_L, ss.BROW_A, ss.BROW_B, ss.LIPS, ss.NOSE):
        feat |= ss.poly(a.shape, L[ring], 3)
    rows = np.arange(a.shape[0])[:, None] * np.ones(a.shape[1])[None]
    top = L[[105, 334], 1].min() - 0.35 * (L[152, 1] - L[10, 1]) * 0.25
    m = oval & ~feat & (rows > top)
    li = ss.lin(a) @ [0.2126, 0.7152, 0.0722]
    mean = li[m].mean()
    out = []
    for s in (0.8, 1.6, 3.2):
        hp = li - ndimage.gaussian_filter(li, s)
        out.append(hp[m].std() / mean)
    return out


if __name__ == "__main__":
    print("%-24s %8s %8s %8s   (face %d px tall)" % ("", "s0.8", "s1.6", "s3.2", FACE_PX))
    for p in sys.argv[1:]:
        crop = None
        if "@" in p:
            p, c = p.split("@")
            crop = [int(v) for v in c.split(",")]
        r = grain(p, crop)
        name = p.replace("\\", "/").split("/")[-1][:24]
        print("%-24s %s" % (name, "no face" if r is None else "  ".join("%.4f" % v for v in r)))
