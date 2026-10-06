"""Her skin's own fine grain, as a tile: the high frequencies of her face's
paint (a photograph's skin: pores, fine lines, the mottle between them),
taken from the plainest stretch of it, freckles and blemishes clipped out,
made seamless. The skin shader lays it on her neck and body, whose paint is
smooth (filled in where her hair lay, and no noise laid over it: a texel's
noise read as sandpaper), so they read as the same skin as her face.

    python tools/assets/heroine_grain.py

Reads tools/assets/heroine_face/face_paint.png and godot/art/people/head_tex/
heroine_features.png; writes godot/art/people/head_tex/heroine_grain.png
(grey: 0.5 her skin as it is, each step of 0.25 a 6% change). Run again when
her face's paint is laid again.
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAINT = os.path.join(ROOT, 'tools', 'assets', 'heroine_face', 'face_paint.png')
FEATURES = os.path.join(ROOT, 'godot', 'art', 'people', 'head_tex', 'heroine_features.png')
OUT = os.path.join(ROOT, 'godot', 'art', 'people', 'head_tex', 'heroine_grain.png')
T = 256                      # the tile, in her face paint's texels (about 2.8 cm of her)
STEP = 0.06                  # a change of 6% is 0.25 of the tile's grey

p = np.asarray(Image.open(PAINT).convert('RGBA'), np.float32) / 255
lum = p[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
alpha = p[..., 3]
S = p.shape[0]
feat = np.asarray(Image.open(FEATURES).convert('RGB').resize((S, S), Image.BILINEAR), np.float32) / 255
busy = ndimage.maximum_filter(np.maximum(feat[..., 0], feat[..., 1]), size=64)
# (the grain: each texel against its neighbourhood, two and a half millimetres round: finer, it is
# all below a pixel at the Look's close-up and averaged away)
ratio = lum / np.maximum(ndimage.gaussian_filter(lum, 24), 1e-3)
# The plainest stretch: wholly her face's paint, away from eyes, brows and lips, least spread at
# coarse scales (no shadow's edge or crease in it).
best, at = None, None
coarse = ndimage.gaussian_filter(lum, 24)
for y in range(0, S - T, 32):
    for x in range(0, S - T, 32):
        if alpha[y:y + T, x:x + T].min() < 0.99 or busy[y:y + T, x:x + T].max() > 0.05:
            continue
        c = coarse[y:y + T, x:x + T]
        score = c.std() / max(c.mean(), 1e-3)
        if best is None or score < best:
            best, at = score, (y, x)
y, x = at
g = ratio[y:y + T, x:x + T] - 1
# (freckles and blemishes, the few marks far past the grain's spread, clipped back into it)
s = g.std()
g = np.clip(g, -2.5 * s, 2.5 * s)
g -= g.mean()
# Seamless: the tile over itself shifted half its size, each where it is furthest from its own
# edge, the spread kept where they blend.
h = np.roll(np.roll(g, T // 2, 0), T // 2, 1)
e = np.minimum(np.arange(T), T - 1 - np.arange(T)) / (T / 2)
w = np.minimum(e[:, None], e[None, :])
w = np.clip(w * 2, 0, 1)
t = (w * g + (1 - w) * h) / np.sqrt(w * w + (1 - w) * (1 - w))
img = np.clip(0.5 + t / STEP * 0.25, 0, 1)
Image.fromarray((img * 255 + 0.5).astype(np.uint8), 'L').save(OUT)
print('GRAIN from her face paint at', at, 'spread %.4f (%.1f%%), written' % (s, 100 * s), OUT)
