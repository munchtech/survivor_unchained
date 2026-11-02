"""Her Oathblade sweep's streaks: one tileable strip baked to godot/art/fx/oath_streaks.png (shaders/oath_sweep.gdshader).

    python tools/fxsim/oath_streaks.py [--seed 9] [--out godot/art/fx/oath_streaks.png] [--px 1024x256] [--preview OUT.jpg]

U runs along the swing (tiles: the strip wraps), V across the crescent (0 = the inner edge by her hand, 1 = the blade's
reach). R: 20-40 fine broken streaks of varied length, each hot at its head and fading along its tail, at random depths
across the band, thin (1-3 cm on a 1.4 m band), with dark between (a blade's smear is streaked, never an even fan).
G: an erosion noise, drawn out along U as a fast thing's is, equalized to 0..1 (the sweep is eaten from its tail by it).
B: a faint fine grain, for the streaks' broken edges. A: 1.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage


def opt(k, d, t=str):
    a = sys.argv
    return t(a[a.index(k) + 1]) if k in a else d


def main():
    seed = opt("--seed", 9, int)
    W, H = (int(v) for v in opt("--px", "1024x256").split("x"))
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out = opt("--out", os.path.join(root, "godot", "art", "fx", "oath_streaks.png"))
    rng = np.random.default_rng(seed)

    u = np.arange(W)[None, :] / W
    v = (np.arange(H)[:, None] + 0.5) / H
    streak = np.zeros((H, W))
    n = int(rng.integers(30, 37))
    # Depths across the band: spread (no two on top of each other), jittered, never on an even grid.
    depths = np.sort((np.arange(n) + rng.uniform(0.15, 0.85, n)) / n)
    for d in depths:
        # 1-3 broken runs per depth, each 8-60% of the strip, with gaps between.
        for _ in range(int(rng.integers(1, 4))):
            length = rng.uniform(0.08, 0.6)
            head = rng.uniform(0, 1)
            width = rng.uniform(0.9, 2.6) / H  # sigma across, in V
            amp = rng.uniform(0.35, 1.0)
            # Along: distance behind the head (wrapping), hot at the head, fading along the tail, a soft nose.
            behind = (head - u) % 1.0
            along = np.where(behind < length, np.clip(1 - behind / length, 0, 1) ** 1.4, 0.0)
            nose = np.clip(1 - ((u - head) % 1.0) / 0.012, 0, 1) ** 2 * (((u - head) % 1.0) < 0.012)
            along = np.maximum(along, nose)
            # Broken: a breakup along the run (fast noise, drawn out), so no run is a clean line.
            dd = d + rng.normal(0, 0.004)
            across = np.exp(-0.5 * ((v - dd) / width) ** 2)
            streak += amp * along * across
    # The breakup, drawn out along U, wrapping in U.
    brk = ndimage.gaussian_filter(rng.random((H, W)), (1.2, 10.0), mode=("nearest", "wrap"))
    brk = (brk - brk.min()) / (np.ptp(brk) + 1e-9)
    streak *= np.clip((brk - 0.25) / 0.5, 0, 1) ** 0.8
    streak = np.clip(streak / np.percentile(streak[streak > 0.02], 99.0), 0, 1)

    # Erosion noise: three octaves, each drawn out 4x along U, wrapping in U.
    ero = np.zeros((H, W))
    for amp, s in ((0.55, 18.0), (0.3, 7.0), (0.15, 2.5)):
        o = ndimage.gaussian_filter(rng.random((H, W)), (s * 0.5, s * 2.0), mode=("nearest", "wrap"))
        ero += amp * (o - o.mean()) / (o.std() + 1e-9)
    # Equalized: a flat histogram, so the erosion's threshold eats evenly over its frames.
    ero = np.argsort(np.argsort(ero.ravel())).reshape(H, W) / (H * W - 1)

    grain = ndimage.gaussian_filter(rng.random((H, W)), (0.6, 2.0), mode=("nearest", "wrap"))
    grain = (grain - grain.min()) / (np.ptp(grain) + 1e-9)

    rgba = np.dstack([streak, ero, grain, np.ones((H, W))])
    img = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print(f"oath_streaks: {n} depths, {W}x{H} -> {out}")
    prev = opt("--preview", None)
    if prev:
        Image.fromarray((np.clip(streak, 0, 1) * 255).astype(np.uint8)).resize((W, H * 2)).convert("RGB").save(prev, quality=90)


if __name__ == "__main__":
    main()
