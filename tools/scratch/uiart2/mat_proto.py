"""Material swatches for the kit's panel ground, seen at 1:1 over the page's vellum."""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge")
import forge as F  # noqa: E402

S = os.path.dirname(os.path.abspath(__file__))
UI = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\godot\art\ui"


def worley(n, cell, seed):
    """F1 and F2 distances (px) of a periodic cell noise on an n x n canvas."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    k = max(4, int(n * n / (cell * cell)))
    pts = rng.random((k, 2)) * n
    tree = cKDTree(pts, boxsize=[n, n])
    yy, xx = np.mgrid[0:n, 0:n]
    q = np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], 1) % n
    d, _ = tree.query(q, k=2)
    return d[:, 0].reshape(n, n).astype(np.float32), d[:, 1].reshape(n, n).astype(np.float32)


def shade(h, L=(-0.55, -0.7, 0.9), spec=0.25, rough=24.0):
    """Light a height field (px) from the upper left: (diffuse ratio to flat, specular)."""
    gy, gx = np.gradient(h)
    nx, ny, nz = -gx, -gy, np.ones_like(h)
    inv = 1 / np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx * inv, ny * inv, nz * inv
    L = np.array(L, np.float32)
    L /= np.linalg.norm(L)
    d = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1) / L[2]
    H = L + np.array([0, 0, 1], np.float32)
    H /= np.linalg.norm(H)
    s = np.clip(nx * H[0] + ny * H[1] + nz * H[2], 0, 1) ** rough * spec
    return d, s


def leather(n=1024, seed=1, pebble=7.0):
    """Goatskin: a pebble grain of small rounded cells between fine creases, a few long soft
    creases, the dye mottled. n file px square (512 shown), periodic."""
    f1, f2 = worley(n, pebble, seed)
    cellh = np.clip((f2 - f1) / (pebble * 0.5), 0, 1) ** 0.5       # 0 in the creases, 1 on a pebble
    f1b, f2b = worley(n, pebble * 3.2, seed + 7)
    big = np.clip((f2b - f1b) / (pebble * 1.4), 0, 1) ** 0.7
    flow = F.fbm(n, n, scale=160, octaves=3, seed=seed + 2)
    crease = (1 - np.abs(F.fbm(n, n, scale=260, octaves=2, seed=seed + 3))) ** 8
    h = cellh * 0.9 + big * 0.7 + flow * 3.0 - crease * 1.2
    d, s = shade(h)
    mott = F.fbm(n, n, scale=220, octaves=4, seed=seed + 4)
    mott2 = F.fbm(n, n, scale=40, octaves=3, seed=seed + 5)
    base = F.hexc("#2a1714")
    ox = F.hexc("#3a1512")
    brown = F.hexc("#2c1c16")
    k = np.clip(mott * 0.5 + 0.5, 0, 1)[..., None]
    col = ox * (1 - k) + brown * k
    col = col * (1 + 0.12 * mott2[..., None])
    lin = col * d[..., None] + s[..., None] * F.hexc("#8a6a58")
    return lin, base


def vellum_leaf(n=1024, seed=11):
    """A leaf of lighter vellum: slow cockle, fibre one way, follicles in twos and threes."""
    cock = F.fbm(n, n, scale=300, octaves=3, seed=seed)
    swell = F.fbm(n, n, scale=70, octaves=3, seed=seed + 1)
    rng = np.random.default_rng(seed + 2)
    fib = rng.standard_normal((n, n)).astype(np.float32)
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    g = np.exp(-2 * np.pi ** 2 * ((fx * 10) ** 2 + (fy * 1.0) ** 2))
    fib = np.real(np.fft.ifft2(np.fft.fft2(fib) * g)).astype(np.float32)
    fib /= np.abs(fib).max()
    h = cock * 14 + swell * 2.0 + fib * 0.25
    d, s = shade(h, spec=0.12, rough=10)
    mott = F.fbm(n, n, scale=200, octaves=4, seed=seed + 3)
    col = F.hexc("#221b20") * (1 + 0.14 * mott[..., None])
    return col * d[..., None] + s[..., None] * F.hexc("#6a5a60"), None


def tile_to(img, W, H):
    reps = (H // img.shape[0] + 1, W // img.shape[1] + 1, 1)
    return np.tile(img, reps)[:H, :W]


def main():
    vel = np.asarray(Image.open(os.path.join(UI, "page", "vellum.png")).convert("RGB"), np.float32) / 255
    W, H = 1200, 520
    page = tile_to(F.srgb_to_lin(vel), W * 2, H * 2)     # at file scale (2x)
    out = page.copy()
    sw = [("leather", leather()[0]), ("leather_fine", leather(pebble=5.0, seed=3)[0]), ("vellum_leaf", vellum_leaf()[0])]
    x = 60
    for name, m in sw:
        a = 0.85
        y0, y1, x0, x1 = 80, 960, x, x + 700
        out[y0:y1, x0:x1] = page[y0:y1, x0:x1] * (1 - a) + m[: y1 - y0, : x1 - x0] * a
        x += 760
    img = F.lin_to_srgb(out)
    small = F.downsample(np.dstack([img, np.ones(img.shape[:2])]), (W, H))[..., :3]
    Image.fromarray((np.clip(small, 0, 1) * 255).astype(np.uint8)).save(os.path.join(S, "mat_swatch_1080.png"))
    print("ok")


if __name__ == "__main__":
    main()
