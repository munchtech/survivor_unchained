"""Her skin's coarse pore layer: skin_peel.png, a tiling detail normal (RGB, 0.5 + 0.5 n) and a cavity (A, 1 flat, lower in
the pores) on a TILE_MM tile.

The pore tile (skin_pores.png, a tile every 9 mm) is all fine detail: at the Look's zoom 1 (about 3 px a millimetre) the
tile falls to its 32 px mip, where its pores average out flat, so pores never showed (max judge b1, face 44; pore_depth
1.2 changed no pixel by more than 1 of 255). This tile's detail sits where that zoom resolves it: pores as shallow wells
(PORE_R, PER_MM2 of them, of mixed size), an orange-peel undulation between them (PEEL_MM), and the cavity, so the
highlight breaks up over them. Made periodic (on a torus, by FFT), so it tiles. The skin shader reads it as `peel_map`
(heroine_skin.gdshader's peel, peel_scale; People.HerZones).

    python tools/assets/skin_peel.py        (writes godot/art/people/skin_peel.png)
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "godot", "art", "people", "skin_peel.png")
N = 512                 # (texels a side)
TILE_MM = 27.0          # (the tile: 3 of the pore tile's 9 mm)
PER_MM2 = 1.6           # (pores a square millimetre)
PORE_R = (0.10, 0.22)   # (their radii, mm: Gaussian sigma, uniform between)
PEEL_MM = 0.9           # (the undulation's scale, mm)
PEEL_H = 0.35           # (its height against a pore's depth)
SEED = 4417


def blur_periodic(a, sigma_px):
    f = np.fft.fftfreq(a.shape[0])
    k = np.exp(-2 * (np.pi * sigma_px) ** 2 * (f[:, None] ** 2 + f[None, :] ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * k))


def main():
    rng = np.random.default_rng(SEED)
    px_mm = N / TILE_MM
    h = np.zeros((N, N))
    count = int(PER_MM2 * TILE_MM * TILE_MM)
    # (pores of mixed size, each a well of depth by its size: splatted per size band, then blurred on the torus)
    bands = np.linspace(PORE_R[0], PORE_R[1], 4)
    for r in bands:
        g = np.zeros((N, N))
        n = count // len(bands)
        ys, xs = rng.integers(0, N, n), rng.integers(0, N, n)
        np.add.at(g, (ys, xs), rng.uniform(0.6, 1.0, n))
        s = r * px_mm
        h -= blur_periodic(g, s) * (2 * np.pi * s * s) * (r / PORE_R[1])
    pores = h.copy()
    peel = blur_periodic(rng.standard_normal((N, N)), PEEL_MM * px_mm)
    peel /= peel.std()
    h = h / max(-h.min(), 1e-6) + PEEL_H * peel / max(np.abs(peel).max(), 1e-6)
    # (slopes per mm of height; normalized so the steepest 1% have slope 1: the shader's peel scales it)
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2
    s = np.percentile(np.hypot(gx, gy), 99)
    gx, gy = gx / s, gy / s
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    cav = 1 - np.clip(-pores / max(-pores.min(), 1e-6), 0, 1) ** 0.7
    img = np.concatenate([n * 0.5 + 0.5, cav[..., None]], -1)
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(OUT)
    print("PEEL", OUT, "slope p50 %.2f p99 1, cavity mean %.3f" % (np.median(np.hypot(gx, gy)), cav.mean()))


if __name__ == "__main__":
    main()
