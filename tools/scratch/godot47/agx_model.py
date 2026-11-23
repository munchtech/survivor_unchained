"""The two engines' AgX curves as code (neutral greys), to fit 4.7.2's TonemapAgxContrast / TonemapAgxWhite to 4.5.1's curve.

4.5.1 (servers/rendering/renderer_rd/shaders/effects/tonemap.glsl at 4.5.1-stable; the polynomial's numbers are from
memory of that file and are CHECKED here only by 0.18 -> 0.18 and 1.0 at the top, and against the measured frames):
  log2 encode over [-12.4739, 4.0261] EV -> 6th-order polynomial -> pow 2.4.
4.7.2 (same file at 4.7.2-stable + servers/rendering/storage/environment_storage.cpp, read 23 Nov): the allenwp curve,
  a power toe below 0.18 and a Reinhard-like shoulder above, from contrast and white.
For a grey the inset and outset matrices cancel (rows sum to 1), so the curve alone is the whole tonemapper.

  python tools/scratch/godot47/agx_model.py                 table at the defaults + the least-squares fit
  python tools/scratch/godot47/agx_model.py CONTRAST WHITE  table at those
"""
import sys
import numpy as np


def srgb(x):
    x = np.clip(x, 0, None)
    return np.where(x < 0.0031308, 12.92 * x, 1.055 * np.power(np.maximum(x, 1e-12), 1 / 2.4) - 0.055)


def t45(x):
    lo, hi = -12.4739311883324, 4.02606881166759
    v = (np.clip(np.log2(np.maximum(x, 1e-10)), lo, hi) - lo) / (hi - lo)
    v2 = v * v; v4 = v2 * v2
    p = 0.021 * v + 4.0111 * v2 - 25.682 * v2 * v + 70.359 * v4 - 74.778 * v4 * v + 27.069 * v4 * v2
    return np.power(np.maximum(p, 0), 2.4)


def t47(x, contrast=1.25, white=16.29, out_max=1.0):
    cp = 0.18
    sh_max = out_max - cp
    toe_a = (1 / cp - 1) * cp ** contrast
    den = cp ** contrast + toe_a
    slope = contrast * cp ** (contrast - 1) * toe_a / (den * den)
    w = (max(white, 2.0) - cp) ** 2 / sh_max * slope
    s = x - cp
    ss = slope * s
    sh = ss * (1 + s / w) / (1 + ss / sh_max) + cp
    t = np.power(np.maximum(x, 0), contrast)
    t = t / (t + toe_a)
    return np.minimum(np.where(x < cp, t, sh), out_max)


def table(c, w, e=1.0):
    print(f"contrast {c} white {w} exposure x{e}")
    print("scene | 4.5.1 display | 4.7.2 display | diff")
    for x in [0.0005, 0.001, 0.002, 0.004, 0.008, 0.015, 0.03, 0.05, 0.08, 0.12, 0.18, 0.27, 0.4, 0.6, 0.9, 1.4, 2.2, 4, 8, 16]:
        a, b = float(srgb(t45(np.array(x)))), float(srgb(t47(np.array(x * e), c, w)))
        print(f"{x:7.4f} | {a:.4f} | {b:.4f} | {b - a:+.4f}")


def fit(lo=0.0005, hi=16.0, exposure=False):
    xs = np.exp(np.linspace(np.log(lo), np.log(hi), 400))
    ref = srgb(t45(xs))
    best = None
    for c in np.arange(1.0, 1.6001, 0.005):
        for w in [2, 3, 4, 5, 6, 8, 10, 12, 14, 16.29, 20, 25, 32, 45, 64]:
            for e in (np.arange(0.9, 1.1001, 0.01) if exposure else [1.0]):
                err = np.sqrt(np.mean((srgb(t47(xs * e, c, w)) - ref) ** 2))
                if best is None or err < best[0]:
                    best = (err, c, w, e)
    return best


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        table(float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
    else:
        table(1.25, 16.29)
        for name, lo, hi in [("whole range", 0.0005, 16), ("our frame's range (display 0.02-0.9)", 0.002, 1.2)]:
            for ex in (False, True):
                err, c, w, e = fit(lo, hi, ex)
                print(f"fit over {name}{' with exposure' if ex else ''}: contrast {c:.3f} white {w} exposure x{e:.2f} rms {err:.4f}")
