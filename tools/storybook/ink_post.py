"""The shared ink treatment for the storybook's ink/woodcut plates (Storybook 3).

Applied identically to every layer of every plate, so they read as one hand:
  1. Lanczos up to the plate's target width (before quantizing: crisp edges at 1:1),
  2. map to the shared inks (nearest in Oklab), a 3x3 majority filter on the ink index
     (kills speckle), then 0.78 inks + 0.22 the drawing (keeps the carved edges' life),
  3. a real paper scan (ambientCG Paper005, CC0) as fibre grain and blotch, sampled at the
     layer's position in the plate so every layer of a plate shares one sheet of paper,
  4. ink wear (paper peeking through the solid blacks where the fibre stands up),
  5. one black point and "parchment lights": nothing darker than the black ink's floor,
     nothing lighter than warm paper (never pure white).

    from ink_post import post, upscale
    out = post(rgb_float_HxWx3, offset=(x0, y0))      # offset: px in the plate's posted image
    python tools/storybook/ink_post.py <in.png> <target_w> <out.png>   # a whole plate
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.join(HERE, "out", "paper_Paper005.jpg")   # ambientCG Paper005 4K Color, CC0 (ink_provenance.md)

INKS = {  # the shared inks, the same list for every plate
    "black": "0e0d14", "navy": "1c2642", "slate": "3e4e74", "snow": "687c8e",
    "ember": "ff8a3a", "gold": "ffd07a", "parchment": "e8dbbe", "cage": "8ac8ff",
    "rose": "7a4c58", "green": "0f1d18",
}
PAL = np.array([[int(h[i:i + 2], 16) for i in (0, 2, 4)] for h in INKS.values()], np.float32) / 255
MIX = 0.78
GRAIN, BLOTCH = 0.12, 0.03          # fibre and blotch strength (multiplicative)
WEAR = 1.15                         # fibre z-score above which paper shows through solid ink
BLACK = PAL[0] * 0.92               # the black point: no pixel darker
LIGHT = np.array([0.925, 0.875, 0.775], np.float32)  # the parchment light: no pixel lighter
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
LUM_MAX = float(LIGHT @ LUM)        # lights capped by lightness (the cage blue keeps its hue)
TINT = np.array([1.0, 0.985, 0.95], np.float32)
# per-plate light step (the plate config's "light"): "cold" turns the warm lights (parchment, gold, ember, rose) into
# the cage blue / snow blue-gray by the drawing's lightness, the brightest core a pale blue-white, never warm
COLD_LIGHT = np.array([0.86, 0.92, 0.97], np.float32)     # the cold plate's cap (pale blue-white)
COLD_TINT = np.array([0.97, 0.99, 1.0], np.float32)
COLD_COOL = np.array([0.78, 0.93, 1.08], np.float32)      # the 22% drawing mix: lightness carried on a cool hue


def _oklab(rgb):
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]], np.float32)
    lms = np.cbrt(c @ m1.T)
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]], np.float32)
    return lms @ m2.T


PAL_LAB = _oklab(PAL)
# the plate-specific inks (dusk rose, river green-black) must win clearly: a night sky is not green
BIAS = np.array([{"rose": 0.04, "green": 0.08}.get(k, 0.0) if k in ("rose", "green") else 0.0 for k in INKS], np.float32)


def quantize(rgb):
    """Ink index per pixel (nearest ink in Oklab, lightness weighted a little up)."""
    h, w, _ = rgb.shape
    flat = rgb.reshape(-1, 3)
    idx = np.empty(len(flat), np.uint8)
    wgt = np.array([1.25, 1.8, 1.8], np.float32)   # hue counts: blue-gray snow never goes rose
    for s in range(0, len(flat), 1 << 20):
        lab = _oklab(flat[s:s + (1 << 20)])
        d = (((lab[:, None, :] - PAL_LAB[None]) * wgt) ** 2).sum(-1) + BIAS ** 2
        idx[s:s + (1 << 20)] = d.argmin(-1)
    return idx.reshape(h, w)


_paper = None


def paper():
    """(fibre, blotch): the scan's luminance split into fine fibre and broad blotch, each z-scored."""
    global _paper
    if _paper is None:
        L = np.asarray(Image.open(PAPER).convert("L")).astype(np.float32)
        lo = nd.gaussian_filter(L, 10, mode="wrap")
        fib = L - lo
        blo = lo - nd.gaussian_filter(lo, 120, mode="wrap")
        _paper = (fib / fib.std(), blo / blo.std())
    return _paper


def _sample(tex, x0, y0, h, w):
    th, tw = tex.shape
    ys = (np.arange(h) + y0) % th
    xs = (np.arange(w) + x0) % tw
    return tex[np.ix_(ys, xs)]


def upscale(img, w, h=None):
    """Lanczos up (PIL image or float array) to w x h."""
    if isinstance(img, np.ndarray):
        img = Image.fromarray((img.clip(0, 1) * 255 + 0.5).astype(np.uint8))
    h = h or round(img.height * w / img.width)
    return np.asarray(img.convert("RGB").resize((w, h), Image.LANCZOS)).astype(np.float32) / 255


def _cold(idx, rgb):
    """The cold light step: warm-ink pixels -> snow / cage / ice by the drawing's lightness; the drawing mix cooled."""
    q = PAL[idx]
    names = list(INKS)
    warm = np.isin(idx, [names.index(k) for k in ("parchment", "gold", "ember", "rose")])
    l = rgb @ LUM
    ice = COLD_LIGHT
    to = np.where((l > 0.78)[..., None], ice, np.where((l > 0.45)[..., None], PAL[names.index("cage")], PAL[names.index("snow")]))
    q = np.where(warm[..., None], to, q)
    cool = np.where((warm | (l > 0.35))[..., None], np.clip(l[..., None] * COLD_COOL, 0, 1), rgb)   # the dark water keeps its green
    return q, cool


def post(rgb, offset=(0, 0), light="warm"):
    """rgb: float HxWx3 already at the target scale. offset: where its top-left sits in the
    plate's posted image (px), so a plate's layers share the paper. light: the plate's light step
    ("warm" default, "cold" for p7u). Returns float HxWx3."""
    h, w, _ = rgb.shape
    idx = quantize(rgb)
    idx = np.asarray(Image.fromarray(idx).filter(ImageFilter.ModeFilter(3)))
    cold = light == "cold"
    if cold:
        q, drawing = _cold(idx, rgb)
    else:
        q, drawing = PAL[idx], rgb
    mix = MIX * q + (1 - MIX) * drawing
    cap = COLD_LIGHT if cold else LIGHT
    fib_t, blo_t = paper()
    fib = _sample(fib_t, offset[0], offset[1], h, w)
    blo = _sample(blo_t, offset[0], offset[1], h, w)
    out = mix * (1 + GRAIN * np.clip(fib, -3, 3)[..., None] + BLOTCH * np.clip(blo, -3, 3)[..., None])
    ink = (mix.mean(-1) < 0.2)
    wear = (ink & (fib + 0.5 * blo > WEAR))[..., None]
    out = np.where(wear, out * 0.6 + cap * 0.12, out)
    out = out * (COLD_TINT if cold else TINT) + 0.008
    lum = out @ LUM
    out = out * np.minimum(1, float(cap @ LUM) / np.maximum(lum, 1e-6))[..., None]
    if cold:
        out = np.minimum(out, cap)
    return np.clip(np.maximum(out, BLACK), 0, 1)


def save(arr, path, alpha=None):
    a = (arr.clip(0, 1) * 255 + 0.5).astype(np.uint8)
    if alpha is not None:
        a = np.dstack([a, (alpha.clip(0, 1) * 255 + 0.5).astype(np.uint8)])
    Image.fromarray(a).save(path)


if __name__ == "__main__":
    src, tw, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    save(post(upscale(Image.open(src), tw)), dst)
