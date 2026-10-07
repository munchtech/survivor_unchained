"""Shimmer in motion: the world's frame-to-frame change once the camera's own movement is taken out.
    python mres.py TAG [TAG ...]
For each pair of consecutive frames of a run, tiles of the ground (away from her and the interface)
are lined up by phase correlation to a fiftieth of a pixel, the second shifted onto the first by a
Fourier shift (exact for what the picture can hold), and what still differs is measured: crawling
edges, popping blades and noise. Read it beside sharpness: blur lowers it too."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402

T = 128


def shift_of(a, b):
    """Where b's content sits relative to a's (b = a moved by d), to sub-pixel."""
    w = np.outer(np.hanning(T), np.hanning(T))
    fa, fb = np.fft.fft2(a * w), np.fft.fft2(b * w)
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    c = np.fft.ifft2(r).real
    py, px = np.unravel_index(np.argmax(c), c.shape)

    def sub(cm, c0, cp):
        d = cm - 2 * c0 + cp
        return 0.0 if abs(d) < 1e-12 else 0.5 * (cm - cp) / d

    dy = py + sub(c[(py - 1) % T, px], c[py, px], c[(py + 1) % T, px])
    dx = px + sub(c[py, (px - 1) % T], c[py, px], c[py, (px + 1) % T])
    dy = dy - T if dy > T / 2 else dy
    dx = dx - T if dx > T / 2 else dx
    # (The peak sits at minus the displacement, by numpy's inverse transform.)
    return -dy, -dx, c.max()


def fshift(b, dy, dx):
    ky = np.fft.fftfreq(T)[:, None]
    kx = np.fft.fftfreq(T)[None, :]
    return np.fft.ifft2(np.fft.fft2(b) * np.exp(-2j * np.pi * (ky * dy + kx * dx))).real


def run(tag):
    fs = C.frames(tag)
    if len(fs) < 2:
        return None
    ims = [C.load(f) for f in fs]
    H, W = ims[0].shape[:2]
    c = C.her_at(fs[0], ims[0])
    res, n, moved, grad = [], 0, [], []
    for i in range(len(ims) - 1):
        a, b = ims[i].mean(axis=2), ims[i + 1].mean(axis=2)
        for y in range(int(H * 0.15), int(H * 0.78) - T, T):
            for x in range(int(W * 0.05), int(W * 0.95) - T, T):
                # Not her (nor her shadow), nor the interface's corners.
                if abs(x + T / 2 - c[0]) < H * 0.16 and abs(y + T / 2 - c[1]) < H * 0.2:
                    continue
                ta, tb = a[y:y + T, x:x + T], b[y:y + T, x:x + T]
                if ta.std() < 2:
                    continue
                dy, dx, peak = shift_of(ta, tb)
                if peak < 0.2 or abs(dy) > 12 or abs(dx) > 12:
                    continue
                tb2 = fshift(tb, -dy, -dx)
                m = 16
                d = np.abs(ta[m:-m, m:-m] - tb2[m:-m, m:-m])
                res.append(d.mean())
                core = ta[m:-m, m:-m]
                grad.append(np.abs(np.diff(core, axis=0)).mean() + np.abs(np.diff(core, axis=1)).mean())
                moved.append(np.hypot(dy, dx))
                n += 1
    res, grad = np.array(res), np.array(grad)
    return res.mean(), np.percentile(res, 90), np.mean(moved), n, grad.mean(), (res / grad).mean()


if __name__ == "__main__":
    print(f"{'run':16s} {'residual':>9s} {'p90':>6s} {'moved px':>9s} {'tiles':>6s} {'ground grad':>12s} {'res/grad':>9s}")
    for t in sys.argv[1:]:
        r = run(t)
        if r:
            print(f"{t:16s} {r[0]:9.3f} {r[1]:6.3f} {r[2]:9.2f} {r[3]:6d} {r[4]:12.3f} {r[5]:9.3f}")
