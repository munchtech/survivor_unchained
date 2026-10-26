#!/usr/bin/env python3
"""The market stalls' canvas (E9d): a tiling sheet, 0.5 m a tile at 512 px, near-white so the stall's vertex colours
(dye, stripes, fading, soiling: env_props.py stall) carry the colour. A plain tabby weave of slubbed linen threads
(warp and weft about 1.5 mm), the threads uneven in thickness and tone, a soft mottle over it.

    python tools/assets/env_canvas_tile.py   ->  godot/art/world/props/canvas_tile.png, canvas_tile_n.png (OpenGL normal)

The props' atlas could not hold it: a 3 m awning mapped into the atlas's 0.4 m canvas tile showed its weave 7x too big
(a basket weave at the close camera). Every tiling here is periodic (the noise is filtered in the frequency domain).
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "godot" / "art" / "world" / "props"
N = 512


def pnoise(rng, f0):
    """Periodic noise: white noise low-passed in the frequency domain (cycles per tile ~ f0)."""
    w = rng.standard_normal((N, N))
    fy = np.fft.fftfreq(N)[:, None] * N
    fx = np.fft.fftfreq(N)[None, :] * N
    g = np.exp(-(fx ** 2 + fy ** 2) / (2 * f0 ** 2))
    n = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    return (n - n.mean()) / (n.std() + 1e-9)


def main():
    rng = np.random.default_rng(5)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    per = 3.0  # px per thread
    # thread thickness and tone vary along each thread (slubs): per-row / per-column noise, periodic
    rows = np.tile(pnoise(rng, 40)[:, :1], (1, N))
    cols = np.tile(pnoise(rng, 40)[:1, :], (N, 1))
    slub_r = np.tile(pnoise(rng, 60)[:, 7:8], (1, N)) * 0.5 + pnoise(rng, 24) * 0.5
    slub_c = np.tile(pnoise(rng, 60)[7:8, :], (N, 1)) * 0.5 + pnoise(rng, 24) * 0.5
    warp = 0.5 + 0.5 * np.cos(2 * np.pi * x / per)
    weft = 0.5 + 0.5 * np.cos(2 * np.pi * y / per)
    over = ((np.floor(x / per) + np.floor(y / per)) % 2).astype(np.float32)
    h = over * warp * (1 + 0.25 * slub_c) + (1 - over) * weft * (1 + 0.25 * slub_r)
    tone = 0.9 + 0.035 * (over * cols + (1 - over) * rows) + 0.04 * pnoise(rng, 6) + 0.025 * pnoise(rng, 20) + 0.05 * (h - 0.5)
    alb = np.stack([tone * 1.0, tone * 0.985, tone * 0.95], -1)
    Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8)).save(OUT / "canvas_tile.png")
    hz = h * 0.6 + 0.4 * pnoise(rng, 10) * 0.2
    dx = (np.roll(hz, -1, 1) - np.roll(hz, 1, 1)) * 0.5
    dy = (np.roll(hz, -1, 0) - np.roll(hz, 1, 0)) * 0.5
    s = 1.2
    nx, ny, nz = -dx * s, dy * s, np.ones_like(dx)
    l = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    nrm = np.stack([nx / l, ny / l, nz / l], -1) * 0.5 + 0.5
    Image.fromarray((nrm * 255).astype(np.uint8)).save(OUT / "canvas_tile_n.png")
    print("wrote canvas_tile.png, canvas_tile_n.png")


if __name__ == "__main__":
    main()
