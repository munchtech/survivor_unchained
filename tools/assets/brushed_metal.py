"""A brushed metal of our own, tiling, 2048 square: fine streaks along u
(a plate's band, laid round her arm), no blotches. Writes
godot/art/outfit/Brushed_diff.jpg and Brushed_nor.jpg (OpenGL normals).

(judge 4: the scanned metal on the Ranger's pauldron read as blotchy
brushing across the bands; its colour varied in patches a few centimetres
wide.)

    python tools/assets/brushed_metal.py
"""
import os

import numpy as np
from PIL import Image

N = 2048
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "outfit")


def streaks(rng, along, across):
    """White noise blurred `along` pixels down u and `across` over v, on a
    torus so the tile repeats seamlessly; unit variance."""
    w = rng.standard_normal((N, N))
    f = np.fft.fft2(w)
    ku = np.fft.fftfreq(N)[None, :]
    kv = np.fft.fftfreq(N)[:, None]
    g = np.exp(-2 * (np.pi ** 2) * ((ku * along) ** 2 + (kv * across) ** 2))
    s = np.real(np.fft.ifft2(f * g))
    return s / s.std()


def main():
    rng = np.random.default_rng(48)
    # Long fine lines, a few coarser ones, and a faint long wash so it is
    # not dead flat (kept small: patches were the fault).
    h = 1.0 * streaks(rng, 220, 0.6) + 0.45 * streaks(rng, 90, 1.6) + 0.12 * streaks(rng, 600, 40)
    h /= h.std()
    col = np.clip(128 + 9.0 * h, 0, 255)
    Image.fromarray(np.repeat(col[:, :, None], 3, 2).astype(np.uint8)).save(os.path.join(OUT, "Brushed_diff.jpg"), quality=95)
    # Normals from the fine height only: the lines catch the light across them.
    fine = streaks(rng, 260, 0.7)
    dv = (np.roll(fine, -1, 0) - np.roll(fine, 1, 0)) / 2
    du = (np.roll(fine, -1, 1) - np.roll(fine, 1, 1)) / 2
    k = 0.05
    n = np.dstack([-du * k, dv * k, np.ones_like(du)])
    n /= np.linalg.norm(n, axis=2)[:, :, None]
    Image.fromarray(np.clip((n * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "Brushed_nor.jpg"), quality=95)
    print("brushed metal written", OUT)


if __name__ == "__main__":
    main()
