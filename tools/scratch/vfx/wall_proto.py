"""Prototype of shaders/fire_wall.gdshader in numpy: a strip of the wall (a stretch of the ring,
its full height) at a few moments, over the night ground, to judge the tongues offline."""
import sys
import numpy as np
from PIL import Image

SEED = 13.0


def grad(ix, iy):
    a = np.modf(np.sin(ix * 127.1 + iy * 311.7 + SEED) * 43758.5453)[0]
    a = np.abs(a) * 6.2831853
    return np.cos(a), np.sin(a)


def gnoise(px, py, period):
    ix, iy = np.floor(px), np.floor(py)
    fx, fy = px - ix, py - iy
    ux = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    uy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    x0, x1 = np.mod(ix, period), np.mod(ix + 1, period)
    def dot(gx, gy, dx, dy):
        return gx * dx + gy * dy
    ga = grad(x0, iy); gb = grad(x1, iy); gc = grad(x0, iy + 1); gd = grad(x1, iy + 1)
    a = dot(*ga, fx, fy); b = dot(*gb, fx - 1, fy); c = dot(*gc, fx, fy - 1); d = dot(*gd, fx - 1, fy - 1)
    return (a + (b - a) * ux) + ((c + (d - c) * ux) - (a + (b - a) * ux)) * uy


def fbm(px, py, period):
    s, a = 0.0, 0.5
    for _ in range(4):
        s = s + a * gnoise(px, py, period)
        px, py, period, a = px * 2, py * 2, period * 2, a * 0.5
    return np.clip(s * 1.1 + 0.5, 0, 1)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def frame(t, W=900, H=180, cells=60.0, span=0.2):
    u = (np.arange(W) + 0.5) / W * span
    up = 1 - (np.arange(H) + 0.5) / H
    U, UP = np.meshgrid(u, up)
    x = U * cells
    lick = fbm(x * 1.7, UP * 2.4 - t * 2.2, cells * 1.7) - 0.5
    xs = x + lick * 0.7 * UP
    # Ridged: each tongue rises to a point.
    n = fbm(xs * 1.1, np.full_like(xs, t * 0.9), cells * 1.1)
    ridge = 1 - np.abs(2 * n - 1)
    high = 0.12 + 0.88 * ridge ** 2.2 * (0.88 + 0.12 * np.sin(t * 15 + xs * 2.3))
    tear = fbm(xs * 2.6, UP * 4.0 - t * 3.6, cells * 2.6)
    body = 1 - UP / np.maximum(0.05, high)
    f = np.clip(body * 1.25 - (1 - tear) * 0.55 * np.sqrt(UP), 0, 1)
    f = np.maximum(f, (1 - smooth(0, 0.1, UP)) * (0.7 + 0.3 * tear))
    hot, mid, deep = np.array([1.25, 0.78, 0.22]), np.array([1.0, 0.36, 0.05]), np.array([0.42, 0.05, 0.01])
    k1 = smooth(0.08, 0.5, f)[..., None]
    col = deep + (mid - deep) * k1
    k2 = smooth(0.62, 0.95, f)[..., None]
    col = col + (hot - col) * k2
    a = smooth(0.0, 0.35, f)[..., None]
    bg = np.ones((H, W, 3)) * np.array([0.05, 0.045, 0.06])
    out = col * a + bg * (1 - a * 0.35)
    # A plain filmic squeeze so values over 1 show as they bloom.
    return (np.clip(out ** (1 / 2.2), 0, 1) * 255).astype(np.uint8)


if __name__ == "__main__":
    rows = [frame(t) for t in (0.0, 0.37, 0.81)]
    Image.fromarray(np.concatenate(rows, axis=0)).save(sys.argv[1] if len(sys.argv) > 1 else "wall_proto.png")
