"""Skin's fine relief, drawn once: a tile of pores and the fine creases
between them, as a normal map (for shaders/heroine_skin.gdshader), its
alpha how rough the skin is there (a pore duller than the skin round it).

    python tools/assets/skin_pores.py

Writes godot/art/people/skin_pores.png (1024 square, tiling every way).
The pores are dimples scattered evenly (a few hundred to the tile, each its
own size and depth), over a fine grain and a looser, softer undulation;
all of it drawn on a torus so its edges meet.
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DST = os.path.join(ROOT, "godot", "art", "people", "skin_pores.png")
N = 1024
rng = np.random.default_rng(5)


def wrapped_noise(sigma):
    """Smooth noise that tiles (blurred on a torus), from -1 to 1."""
    h = ndimage.gaussian_filter(rng.standard_normal((N, N)), sigma, mode="wrap")
    return h / (np.abs(h).max() + 1e-9)


h = np.zeros((N, N))
# Pores: dimples, evenly spread (a jittered grid), each its own size and depth.
cells = 22
yy, xx = np.mgrid[0:N, 0:N]
for i in range(cells):
    for j in range(cells):
        cx = (i + rng.uniform(0.15, 0.85)) * N / cells
        cy = (j + rng.uniform(0.15, 0.85)) * N / cells
        r = rng.uniform(2.2, 4.2)
        depth = rng.uniform(0.6, 1.0)
        x0, y0 = int(cx - 4 * r), int(cy - 4 * r)
        span = int(8 * r) + 1
        xs = (np.arange(x0, x0 + span) % N)
        ys = (np.arange(y0, y0 + span) % N)
        gx, gy = np.meshgrid(np.arange(x0, x0 + span) - cx, np.arange(y0, y0 + span) - cy)
        h[np.ix_(ys, xs)] -= depth * np.exp(-(gx ** 2 + gy ** 2) / (2 * r * r))
pores = h.copy()
# The fine grain and the creases between the pores, and a soft undulation.
h += 0.18 * wrapped_noise(1.2) + 0.25 * wrapped_noise(6) + 0.35 * wrapped_noise(40)
# Normals from the height (on the torus), gentle.
dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2
dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2
k = 1.6
n = np.dstack([-dx * k, dy * k, np.ones_like(h)])
n /= np.linalg.norm(n, axis=2)[..., None]
rough = np.clip(0.5 - pores * 0.5, 0, 1)                 # (in a pore, duller)
img = np.dstack([(n * 0.5 + 0.5), rough[..., None]])
Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(DST)
print("WRITTEN", DST)
