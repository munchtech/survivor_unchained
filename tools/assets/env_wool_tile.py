#!/usr/bin/env python3
"""A fulled wool blanket's cloth (C01 set: the camp's bedroll): a tiling sheet, 0.4 m a tile at 512 px, near-white so
the prop's vertex colours (env_props.py: the blanket's dye, its bands, the baked occlusion) carry the colour.
A 2/2 twill of soft woollen yarn (about 3 mm a thread, the twill's ribs on the diagonal) under a felted nap: the yarn
uneven in thickness and tone, a fuzz over it that blurs the weave, a few pills, a soft mottle. The atlas's cloth region
(a 1.75 m blanket fitted into its 0.4 m tile) showed its weave 4x too coarse ("a rubber doormat").

    python tools/assets/env_wool_tile.py   ->  godot/art/world/props/wool_tile.png, wool_tile_n.png (OpenGL normal)

Every tiling here is periodic (the noise is filtered in the frequency domain).
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
    rng = np.random.default_rng(11)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    per = 4.0  # px a thread (0.78 mm a px): 128 threads a tile
    ix, iy = np.floor(x / per), np.floor(y / per)
    # 2/2 twill: the warp over two, under two, stepping one a row
    over = (((ix + iy) % 4) < 2).astype(np.float32)
    rows = np.tile(pnoise(rng, 50)[:, :1], (1, N))
    cols = np.tile(pnoise(rng, 50)[:1, :], (N, 1))
    warp = 0.5 + 0.5 * np.cos(2 * np.pi * (x / per - 0.5) + 0.0)
    weft = 0.5 + 0.5 * np.cos(2 * np.pi * (y / per - 0.5))
    yarn = over * warp * (1 + 0.3 * cols) + (1 - over) * weft * (1 + 0.3 * rows)
    # the nap: a felted fuzz over the weave, softening it (fulled wool), and a few pills
    nap = pnoise(rng, 90) * 0.5 + pnoise(rng, 160) * 0.5
    pills = np.clip(pnoise(rng, 70) - 2.1, 0, None)
    h = 0.55 * yarn + 0.3 * (nap * 0.5 + 0.5) + 0.6 * pills
    mott = pnoise(rng, 5) * 0.6 + pnoise(rng, 14) * 0.4
    tone = 0.86 + 0.03 * (over * cols + (1 - over) * rows) + 0.035 * mott + 0.04 * (yarn - 0.5) + 0.02 * nap + 0.03 * pills
    alb = np.stack([tone * 1.0, tone * 0.98, tone * 0.955], -1)
    Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8)).save(OUT / "wool_tile.png")
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    s = 0.9
    nx, ny, nz = -dx * s, dy * s, np.ones_like(dx)
    l = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    nrm = np.stack([nx / l, ny / l, nz / l], -1) * 0.5 + 0.5
    Image.fromarray((nrm * 255).astype(np.uint8)).save(OUT / "wool_tile_n.png")
    print("wrote wool_tile.png, wool_tile_n.png")


if __name__ == "__main__":
    main()
