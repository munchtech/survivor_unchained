"""Worn metal's shared detail, our own: one tiling 1024 square of scratches
and pits laid over every metal of her outfits (the look bible's armor-metal
page, item 1: "one tiled scratch-and-pit detail ... shared by all of them").
At 2.5 repeats a metre a texel is 0.39 mm.

Writes godot/art/outfit/metal_wear_detail.png, linear data, not a colour:
  R, G  the detail's normal, x and y (OpenGL, 0.5 flat)
  B     roughness offset (0.5 none; 1.0 = +0.5)
  A     cavity (1 open metal; lower where a pit or a deep scratch holds dirt)

Everything is drawn on a torus, so the tile repeats without a seam.

    python tools/assets/metal_wear_detail.py
"""
import os

import numpy as np
from PIL import Image

N = 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "outfit", "metal_wear_detail.png")


def blur(a, sigma):
    """Gaussian blur on the torus (FFT), sigma in texels."""
    k = np.fft.fftfreq(N)
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (k[:, None] ** 2 + k[None, :] ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g))


def lines(rng, n, len_px, ang, ang_spread, width):
    """n anti-aliased scratches on the torus: lengths `len_px` (lo, hi),
    angles about `ang` by +-`ang_spread` (radians), `width` texels across.
    Returns depth (0..1) and a per-scratch brightness (some polished
    tracks, some rough ones) as roughness sign."""
    depth = np.zeros((N, N), np.float32)
    rsign = np.zeros((N, N), np.float32)
    for _ in range(n):
        L = rng.uniform(*len_px) ** 1.0
        a = ang + rng.uniform(-ang_spread, ang_spread)
        x0, y0 = rng.uniform(0, N, 2)
        # a slight bow, as a dragged grit makes
        bow = rng.normal(0, 0.04) * L
        d = rng.uniform(0.35, 1.0)
        s = 1.0 if rng.random() < 0.55 else -1.0
        steps = int(L * 2) + 2
        t = np.linspace(0, 1, steps)
        px = x0 + np.cos(a) * L * t - np.sin(a) * bow * 4 * t * (1 - t)
        py = y0 + np.sin(a) * L * t + np.cos(a) * bow * 4 * t * (1 - t)
        # tapered ends: shallow where the grit came in and left
        taper = np.sin(np.pi * t) ** 0.5
        for xx, yy, tp in zip(px, py, taper):
            ix, iy = int(np.floor(xx)), int(np.floor(yy))
            fx, fy = xx - ix, yy - iy
            for dx, wx in ((0, 1 - fx), (1, fx)):
                for dy, wy in ((0, 1 - fy), (1, fy)):
                    v = d * tp * wx * wy
                    X, Y = (ix + dx) % N, (iy + dy) % N
                    if v > depth[Y, X]:
                        depth[Y, X] = v
                        rsign[Y, X] = s
    if width > 1.0:
        depth = np.clip(blur(depth, (width - 1.0) * 0.5) * width, 0, 1)
    return depth, rsign


def main():
    rng = np.random.default_rng(2610)
    # Scratches: two wiping directions and a scatter of stray ones; fine and long, fewer coarse and short.
    d1, s1 = lines(rng, 2200, (8, 70), 0.35, 0.35, 1.0)
    d2, s2 = lines(rng, 1300, (6, 50), 2.0, 0.4, 1.0)
    d3, s3 = lines(rng, 260, (4, 26), 0.0, np.pi, 1.0)
    d4, s4 = lines(rng, 70, (20, 120), 1.1, np.pi, 1.6)        # (a few deeper gouges)
    sc = np.maximum.reduce([d1 * 0.6, d2 * 0.5, d3 * 0.7, d4])
    ssign = np.where(d4 >= np.maximum.reduce([d1 * 0.6, d2 * 0.5, d3 * 0.7]), s4,
                     np.where(d1 * 0.6 >= np.maximum(d2 * 0.5, d3 * 0.7), s1, np.where(d2 * 0.5 >= d3 * 0.7, s2, s3)))
    # Pits: corrosion pitting in clusters, 0.4-1.5 mm, never a regular sprinkle.
    clus = blur(rng.standard_normal((N, N)), 40)
    clus = (clus - clus.mean()) / clus.std()
    pit = np.zeros((N, N), np.float32)
    yy, xx = np.mgrid[-4:5, -4:5]
    cand = rng.uniform(0, N, (9000, 2))
    keep = clus[cand[:, 1].astype(int), cand[:, 0].astype(int)] > rng.normal(1.0, 0.5, len(cand))
    for x, y in cand[keep]:
        r = rng.uniform(0.6, 2.0)
        bowl = np.clip(1 - ((xx - (x % 1)) ** 2 + (yy - (y % 1)) ** 2) / (r * r), 0, 1) ** 0.7 * rng.uniform(0.5, 1.0)
        X = (int(x) + xx) % N
        Y = (int(y) + yy) % N
        pit[Y, X] = np.maximum(pit[Y, X], bowl)
    # Height: grooves and bowls down, a faint orange-peel of the forging between.
    peel = blur(rng.standard_normal((N, N)), 3.0)
    peel /= np.abs(peel).max()
    # (fine scratches mostly in the roughness: as normals, massed, they read as a leather grain)
    h = -0.15 * sc - 0.6 * d4 - 1.0 * pit + 0.05 * peel
    hb = blur(h, 0.7)
    gx = (np.roll(hb, -1, 1) - np.roll(hb, 1, 1)) * 0.5
    gy = (np.roll(hb, -1, 0) - np.roll(hb, 1, 0)) * 0.5
    k = 2.2
    nx, ny = -gx * k, gy * k    # (OpenGL: +y up, rows run down)
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny = nx / ln, ny / ln
    # Roughness: a scratch is a polished track or a rough one; a pit rough; a broad, faint mottle.
    mott = blur(rng.standard_normal((N, N)), 24)
    mott /= np.abs(mott).max()
    rough = 0.10 * sc * ssign + 0.22 * pit + 0.05 * mott
    cav = 1.0 - 0.55 * pit - 0.18 * np.clip(sc - 0.4, 0, 1)
    img = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, np.clip(0.5 + rough, 0, 1), np.clip(cav, 0.3, 1)], -1)
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(OUT)
    print(OUT, "scratch cover %.3f, pit cover %.3f, rough %.3f..%.3f" % ((sc > 0.1).mean(), (pit > 0.1).mean(), rough.min(), rough.max()))


if __name__ == "__main__":
    main()
