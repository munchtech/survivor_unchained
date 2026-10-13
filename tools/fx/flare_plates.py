"""The Flares' own textures, made here (ours, procedural; logged in docs/legal/ASSET_PROVENANCE.md).

frost_plate.png (1024², tiles): the ford's frost as it grows on stone, for Burns Twice's ground and glaze.
  R: feathered dendrites (hexagonal ice branches at 60 degrees, fractal), the crystal's height
  G: the finest needles and branch tips (the glints)
  B: a soft periodic cloud (where the frost lies thick or thin)
flare_noise.png (512², tiles): R, G, B periodic fbm at three scales, A cellular (for smoke, steam, char, the web).

Run: python tools/fx/flare_plates.py [out_dir] (default godot/art/fx/flare).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "godot", "art", "fx", "flare")
rng = np.random.default_rng(1112)


def periodic_fbm(size, octaves, base, seed, persistence=0.55):
    """Tileable value-noise fbm: each octave a random lattice upsampled with wrap (bicubic-ish via smooth interp)."""
    r = np.random.default_rng(seed)
    acc = np.zeros((size, size), np.float64)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cells = base * (2 ** o)
        lat = r.random((cells, cells))
        # smooth upsample with wrap
        xs = np.arange(size) * cells / size
        i0 = np.floor(xs).astype(int) % cells
        i1 = (i0 + 1) % cells
        f = xs - np.floor(xs)
        f = f * f * (3 - 2 * f)
        rows = lat[i0][:, None, :] * 0  # placeholder for shape
        a = lat[i0][:, i0] * (1 - f)[None, :] + lat[i0][:, i1] * f[None, :]
        b = lat[i1][:, i0] * (1 - f)[None, :] + lat[i1][:, i1] * f[None, :]
        v = a * (1 - f)[:, None] + b * f[:, None]
        acc += v * amp
        total += amp
        amp *= persistence
    acc /= total
    acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-9)
    return acc


def periodic_cells(size, n, seed):
    """Tileable cellular distance (F2-F1): 0 on the cells' edges."""
    r = np.random.default_rng(seed)
    pts = r.random((n, 2)) * size
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    f1 = np.full((size, size), 1e9)
    f2 = np.full((size, size), 1e9)
    for px, py in pts:
        dx = np.abs(xx - px); dx = np.minimum(dx, size - dx)
        dy = np.abs(yy - py); dy = np.minimum(dy, size - dy)
        d = np.sqrt(dx * dx + dy * dy)
        f2 = np.where(d < f1, f1, np.minimum(f2, d))
        f1 = np.minimum(f1, d)
    e = f2 - f1
    return np.clip(e / (size / math.sqrt(n) * 0.5), 0, 1)


def frost_plate(size=1024, ss=2):
    S = size * ss
    img = Image.new("F", (S, S), 0.0)
    tips = Image.new("F", (S, S), 0.0)
    d = ImageDraw.Draw(img)
    dt = ImageDraw.Draw(tips)

    def line(x0, y0, x1, y1, v, w, draw):
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                draw.line([(x0 + ox, y0 + oy), (x1 + ox, y1 + oy)], fill=v, width=max(1, int(round(w))))

    segs = []

    def branch(x, y, ang, length, gen, v):
        # A frost feather: a spine that wanders a little, side branches at 60 degrees, shorter each generation.
        step = 6.0 * ss
        n = int(length / step)
        px, py = x, y
        a = ang
        for k in range(n):
            a += rng.normal(0, 0.035)
            nx, ny = px + math.cos(a) * step, py + math.sin(a) * step
            w = max(1.0, (2.6 - gen * 0.75) * ss * (1 - 0.6 * k / max(1, n)))
            segs.append((px, py, nx, ny, v * (1 - 0.35 * k / max(1, n)), w))
            if gen < 3 and rng.random() < (0.55 if gen == 0 else 0.42):
                side = 1 if rng.random() < 0.5 else -1
                sub = length * (0.55 - 0.4 * k / max(1, n)) * rng.uniform(0.5, 0.95) * (0.62 ** gen)
                if sub > step * 2:
                    branch(nx, ny, a + side * math.pi / 3 * rng.uniform(0.92, 1.08), sub, gen + 1, v * 0.82)
                    if rng.random() < 0.6:
                        branch(nx, ny, a - side * math.pi / 3 * rng.uniform(0.92, 1.08), sub * rng.uniform(0.6, 1.0), gen + 1, v * 0.78)
            px, py = nx, ny
        # the tip: a glint
        dt.ellipse([px - 1.5 * ss, py - 1.5 * ss, px + 1.5 * ss, py + 1.5 * ss], fill=1.0)

    # Seeds: a few long feathers sweeping across (frost on stone grows in fans from a few nuclei), many small.
    for _ in range(26):
        x, y = rng.random() * S, rng.random() * S
        base = rng.random() * math.tau
        for k in range(rng.integers(3, 6)):
            branch(x, y, base + k * math.pi / 3 + rng.normal(0, 0.12), rng.uniform(0.18, 0.42) * S, 0, rng.uniform(0.7, 1.0))
    for _ in range(240):
        x, y = rng.random() * S, rng.random() * S
        branch(x, y, rng.random() * math.tau, rng.uniform(0.02, 0.08) * S, 1, rng.uniform(0.35, 0.7))
    for (x0, y0, x1, y1, v, w) in segs:
        line(x0, y0, x1, y1, float(v), w, d)

    a = np.asarray(img, np.float64)
    a = np.clip(a, 0, None)
    # wrap-safe soften
    def soft(arr, r):
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(arr, r, mode="wrap")
    height = np.clip(soft(a, 0.6 * ss) * 0.75 + soft(a, 3.0 * ss) * 0.6, 0, None)
    height = height / (np.percentile(height, 99.7) + 1e-9)
    t = np.asarray(tips, np.float64)
    fine = np.clip(soft(t, 0.8 * ss) * 1.5 + np.clip(a - 0.85, 0, 1) * 1.2, 0, 1)
    # downsample
    def down(arr):
        return np.asarray(Image.fromarray(arr.astype(np.float32), "F").resize((size, size), Image.LANCZOS), np.float64)
    R = np.clip(down(height), 0, 1)
    G = np.clip(down(fine), 0, 1)
    B = periodic_fbm(size, 5, 4, 77)
    return np.stack([R, G, B, np.ones_like(R)], -1)


def noise_tex(size=512):
    R = periodic_fbm(size, 6, 4, 11)
    G = periodic_fbm(size, 6, 8, 12)
    B = periodic_fbm(size, 5, 16, 13)
    A = periodic_cells(size, 90, 14)
    return np.stack([R, G, B, A], -1)


def save(arr, name):
    os.makedirs(OUT, exist_ok=True)
    im = Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    p = os.path.join(OUT, name)
    im.save(p)
    print("wrote", os.path.abspath(p))


if __name__ == "__main__":
    save(frost_plate(), "frost_plate.png")
    save(noise_tex(), "flare_noise.png")
