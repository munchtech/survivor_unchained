"""Each face's brow dye mask (godot/art/people/paint/brows_<face>.png), so every face's painted brows take her hair's
colour (People.HerPaint, shaders/heroine_paint.gdshader), as her own face's do (paint/brows.png, heroine_paint.py).

Face lead 32, 21 October 2026: the max judges at the creation Look found Highborn, Moonlit and Fey's brows thin and
gray-ash under any hair, and Own's ginger under near-black hair: only Own's brows were dyed, and at their painted
lightness. Each other face's portrait paints its brows a little off Own's in her head's UV (Own's mask on them dyed
their lid crease), so each gets its own mask, found in its own paint:

  - near Own's brows (brows.png, closed and widened: her head's UV is one for every face, and each portrait's brows
    lie a little off Own's, hugging the lid more or less);
  - in it, hairs: texels darker than the skin a little way off, dense, the two biggest pieces (one a brow), closed,
    widened a little, feathered (Moonlit's and Doe's solid bands as Fey's and Highborn's faint strokes);
  - in red (0-1): the brow's core darkness against the skin round it (the 97th percentile of the shader's own
    measure, times CORE; stored sRGB-encoded, so the shader reads it linear): the shader counts a hair that dark as a whole one, so a faint face's brows (Fey 0.13,
    Own 0.46) are dyed as fully as a dense one's. Alpha the mask; green, blue 1.

    python tools/assets/heroine_browdye.py            (all nine; Own's brows.png gets only its red set)
    python tools/assets/heroine_browdye.py --sheet OUT.png  (each face's paint with its mask's outline, to look at)
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")
OUT = os.path.join(ROOT, "godot", "art", "people", "paint")
FACES = ["doe", "fey", "hardwon", "highborn", "moonlit", "saffron", "sunborn", "vixen", "wildling"]
SIZE = 2048
NEAR = (8, 14)             # (texels: Own's brows closed, then widened by this: where every face's brows are)
DK = (12.0, 1.0, 0.04)     # (texels: skin blur, hair blur; a texel this share darker than its skin is a hair)
DENSE = (4.0, 0.15, 6, 4)  # (hairs' density blur, its floor; the two brows closed, then widened)
SKIN = (70, 61, 6.0)       # (percentile, window, blur: her skin round a brow, its hairs left out)
CORE = 0.75


def paint(face):
    f = os.path.join(TEX, "heroine_head%s.jpg" % ("" if face == "own" else "_" + face))
    return np.asarray(Image.open(f).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)).astype(np.float32) / 255


def luma(p):
    return p @ np.array([0.3, 0.59, 0.11], np.float32)


def near(own_alpha):
    """Where every face's brows are: Own's (brows.png's big pieces over her face; under row 1400 her body's paint
    shares the sheet), closed and widened. Her head's UV is one for every face; each portrait paints its brows a
    little off Own's, hugging the eye's lid more or less."""
    m = own_alpha > 8 / 255
    m[1400:] = False
    lab, k = ndimage.label(m)
    sz = ndimage.sum(m, lab, range(1, k + 1))
    m = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s > 1000])
    return ndimage.binary_dilation(ndimage.binary_closing(m, iterations=NEAR[0]), iterations=NEAR[1])


def found(L, zone):
    """The brows found in one face's paint (0-1, feathered): hairs (texels darker than the skin a little way off),
    near Own's, dense, the two biggest pieces (a brow each: the lid's edge and stray specks are smaller), closed,
    widened a little, feathered."""
    sk = ndimage.gaussian_filter(L, DK[0])
    dk = (sk - ndimage.gaussian_filter(L, DK[1])) / np.maximum(sk, 1e-3)
    den = ndimage.gaussian_filter(((dk > DK[2]) & zone).astype(np.float32), DENSE[0])
    m = ndimage.binary_opening(den > DENSE[1], iterations=2)
    lab, k = ndimage.label(m)
    sz = ndimage.sum(m, lab, range(1, k + 1))
    m = np.isin(lab, [i + 1 for i in np.argsort(sz)[::-1][:2]])
    m = ndimage.binary_closing(m, iterations=DENSE[2])
    return np.clip(ndimage.gaussian_filter(ndimage.binary_dilation(m, iterations=DENSE[3]).astype(np.float32), 2.5) * 1.5, 0, 1)


def linear(p):
    return np.where(p <= 0.04045, p / 12.92, ((p + 0.055) / 1.055) ** 2.4).astype(np.float32)


def encode(v):
    """Linear 0-1 to sRGB bytes (the shader reads the mask as colour, so linear again)."""
    v = np.clip(v, 0, 1)
    return np.round(np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1 / 2.4) - 0.055) * 255).astype(np.uint8)


def skin_under(L, m):
    """Her skin's lightness under and round her brows, hairs left out (linear luma): the SKIN[0]th percentile of a
    SKIN[1]-texel window, blurred; the shader measures each hair against it (the brightest of a ring of samples
    a brow's breadth out, as before, caught her lid's and eye's highlights where a face's brows hug the lid)."""
    out = ndimage.gaussian_filter(L, 12)
    ys, xs = np.where(m > 0.01)
    y0, y1 = max(ys.min() - 60, 0), min(ys.max() + 60, SIZE)
    x0, x1 = max(xs.min() - 60, 0), min(xs.max() + 60, SIZE)
    sub = ndimage.percentile_filter(L[y0:y1, x0:x1], SKIN[0], size=SKIN[1])
    out[y0:y1, x0:x1] = ndimage.gaussian_filter(sub, SKIN[2])
    return out


def core(L, sk, m):
    """The brow's core darkness against her skin there (as heroine_paint.gdshader measures it), times CORE."""
    c = (sk - L) / np.maximum(sk, 1e-3)
    return float(np.clip(np.percentile(c[m > 0.5], 97) * CORE, 0.08, 1.0))


def main():
    own = np.asarray(Image.open(os.path.join(OUT, "brows.png")))
    zone = near(own[..., 3].astype(np.float32) / 255)
    sheet = []
    for f in FACES + ["own"]:
        P = paint(f)
        L = luma(linear(P))
        if f == "own":
            path = os.path.join(OUT, "brows.png")
            img = np.asarray(Image.open(path)).copy()
            a = img[..., 3].astype(np.float32) / 255
            a[1400:] = 0           # (her body's paint shares the sheet below; not brows, left be)
        else:
            a = found(luma(P), zone)
            img = np.full((SIZE, SIZE, 4), 255, np.uint8)
            img[..., 3] = np.round(a * 255).astype(np.uint8)
            path = os.path.join(OUT, "brows_%s.png" % f)
        sk = skin_under(L, a)
        c = core(L, sk, a)
        img[..., 0] = encode(np.float32(c))
        img[..., 1] = encode(sk)
        if "--sheet" not in sys.argv:
            Image.fromarray(img).save(path)
        print("%-9s core %.3f  mask texels %d  -> %s" % (f, c, int((a > 0.5).sum()), os.path.relpath(path, ROOT)))
        if "--sheet" in sys.argv:
            p = (P[880:1380, 880:1380] * 255).astype(np.uint8)
            e = a[880:1380, 880:1380] > 0.5
            p[e & ~ndimage.binary_erosion(e, iterations=2)] = [0, 255, 0]
            sheet.append(p[::2, ::2])
    if "--sheet" in sys.argv:
        rows = [np.concatenate(sheet[i:i + 5], 1) for i in (0, 5)]
        Image.fromarray(np.concatenate(rows, 0)).save(sys.argv[sys.argv.index("--sheet") + 1])


if __name__ == "__main__":
    main()
