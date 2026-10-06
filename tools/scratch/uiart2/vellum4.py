"""Black vellum, procedural, v4: veins, follicles in groups, cockle, fibre, dye uneven."""
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge")
import forge as F  # noqa: E402
import kit  # noqa: E402

S = os.path.dirname(os.path.abspath(__file__))


def warp(f, n, amp, scale, seed):
    wx = F.fbm(n, n, scale=scale, octaves=3, seed=seed) * amp
    wy = F.fbm(n, n, scale=scale, octaves=3, seed=seed + 1) * amp
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    return cv2.remap(f.astype(np.float32), (xx + wx) % n, (yy + wy) % n, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def vellum(n=2048, seed=7, tone="#1b1618"):
    # Cockle: slow swells of the skin.
    cock = F.fbm(n, n, scale=700, octaves=3, seed=seed)
    swell = F.fbm(n, n, scale=160, octaves=3, seed=seed + 1)
    # Veins: thin meandering lines (the zero set of a warped noise), branching, sparse.
    v1 = warp(F.fbm(n, n, scale=260, octaves=4, seed=seed + 2), n, 60, 300, seed + 3)
    v2 = warp(F.fbm(n, n, scale=110, octaves=3, seed=seed + 4), n, 30, 200, seed + 5)
    vein = np.exp(-(v1 / 0.025) ** 2) * 0.8 + np.exp(-(v2 / 0.018) ** 2) * 0.35
    vein *= np.clip(F.fbm(n, n, scale=300, octaves=2, seed=seed + 6) * 1.5 + 0.3, 0, 1)   # only here and there
    # Follicles: pits in twos and threes along the hair's lie.
    rng = np.random.default_rng(seed + 7)
    pits = np.zeros((n, n), np.float32)
    lie = F.fbm(n, n, scale=500, octaves=2, seed=seed + 8) * math.pi
    for _ in range(int(n * n / 900)):
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        a = lie[int(cy) % n, int(cx) % n] + 0.6
        for k in range(rng.integers(1, 4)):
            px = cx + math.cos(a) * k * rng.uniform(2.5, 4.0)
            py = cy + math.sin(a) * k * rng.uniform(2.5, 4.0)
            r = rng.uniform(0.6, 1.2)
            x0, y0 = int(px - 4), int(py - 4)
            ys = np.arange(y0, y0 + 9) % n
            xs = np.arange(x0, x0 + 9) % n
            dx = (np.arange(x0, x0 + 9) - px)[None, :]
            dy = (np.arange(y0, y0 + 9) - py)[:, None]
            pits[np.ix_(ys, xs)] = np.maximum(pits[np.ix_(ys, xs)], np.exp(-(dx * dx + dy * dy) / (2 * r * r)))
    # Fibre: a faint grain along the lie.
    rngf = np.random.default_rng(seed + 9)
    fib = rngf.standard_normal((n, n)).astype(np.float32)
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    ang = 0.5
    u = fx * math.cos(ang) + fy * math.sin(ang)
    v = -fx * math.sin(ang) + fy * math.cos(ang)
    g = np.exp(-2 * math.pi ** 2 * ((u * 12) ** 2 + (v * 1.2) ** 2))
    fib = np.real(np.fft.ifft2(np.fft.fft2(fib) * g)).astype(np.float32)
    fib /= np.abs(fib).max()
    h = cock * 40 + swell * 4 - pits * 0.6 + fib * 0.25 - vein * 0.5
    d, sp = kit.shade(h, spec=0.05, rough=6, Lz=1.0)
    took = np.clip(F.fbm(n, n, scale=420, octaves=4, seed=seed + 10) * 0.8 + 0.5, 0, 1)[..., None]
    mott = F.fbm(n, n, scale=60, octaves=3, seed=seed + 11)[..., None]
    violet, brown = F.hexc("#1a1520"), F.hexc("#221a17")
    col = violet * (1 - took) + brown * took
    col = col * (1 + 0.08 * mott) * (1 - vein[..., None] * 0.18) * (1 - pits[..., None] * 0.35)
    lin = col * d[..., None] + sp[..., None] * F.hexc("#4a4048")
    lin = lin * (F.hexc(tone) / lin.reshape(-1, 3).mean(0))
    return F.lin_to_srgb(lin)


if __name__ == "__main__":
    img = vellum()
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(S, "vellum4.png"))
    print(img.reshape(-1, 3).mean(0), img.reshape(-1, 3).std(0))
