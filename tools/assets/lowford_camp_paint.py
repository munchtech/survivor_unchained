"""(E8 later) Low Ford's camp ground in the zone's paint (godot/data/zones/lowford/splat.png, R = trodden earth):
footpaths worn into the camp (from the road by the post lantern, north into the wood, south-west past the bedroll)
and the camp's earth broken up, grass let back in patches at its rim (thin tufts where R falls under about 0.5), its
edge ragged. Run once from the repo root on the paint as committed before E8 later (it reads splat.png and writes it
back; --from PATH reads another copy, e.g. the git blob).

    python tools/assets/lowford_camp_paint.py [--from PATH]
"""
import math
import sys

import numpy as np
from PIL import Image

SPLAT = 'godot/data/zones/lowford/splat.png'
SIZE, RES = 260.0, 1024
FIRE = (-10.5, 90.5)
# the paths (world x, z), each with its core width (m) and its worn strength (R) along it, fading at the far end
PATHS = [
    ([(-6.6, 91.0), (-5.2, 91.9), (-3.9, 92.6), (-2.6, 93.0)], 0.75, 0.82),   # east to the road by the post lantern
    ([(-10.6, 86.2), (-11.2, 84.0), (-11.9, 81.6), (-12.3, 79.0)], 0.6, 0.72),  # north into the wood
    ([(-13.0, 94.4), (-13.9, 96.6), (-14.6, 98.8), (-15.2, 100.8)], 0.55, 0.66),  # south-west
]


def noise(x, z, f, seed):
    return (np.sin(x * f * 3.1 + seed) * np.cos(z * f * 2.7 - seed) + 0.6 * np.sin((x * 1.9 + z * 0.7) * f + seed * 2)
            + 0.4 * np.sin(z * f * 5.3 - x * f * 1.3 + seed * 3)) / 2.0


def seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    dx, dz = bx - ax, bz - az
    t = np.clip(((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz), 0, 1)
    return np.hypot(px - (ax + t * dx), pz - (az + t * dz)), t


def main():
    src = sys.argv[sys.argv.index('--from') + 1] if '--from' in sys.argv else SPLAT
    im = np.array(Image.open(src)).astype(np.float32) / 255.0
    # the window round the camp (x -22..2, z 74..106)
    i0, i1 = int((74 + 130) / SIZE * RES), int((106 + 130) / SIZE * RES)
    j0, j1 = int((-22 + 130) / SIZE * RES), int((2 + 130) / SIZE * RES)
    jj, ii = np.meshgrid(np.arange(j0, j1), np.arange(i0, i1))
    x = (jj + 0.5) / RES * SIZE - SIZE / 2
    z = (ii + 0.5) / RES * SIZE - SIZE / 2
    r = im[i0:i1, j0:j1, 0].copy()
    # the camp's earth broken: away from the fire (past 2.2 m) patches drop toward grass, the rim ragged
    d = np.hypot(x - FIRE[0], z - FIRE[1])
    blob = 0.5 + 0.5 * noise(x, z, 0.55, 3.0) * 0.7 + 0.5 * 0.3 * noise(x, z, 1.7, 7.0)
    away = np.clip((d - 2.2) / 1.6, 0, 1)
    camp = r > 0.5
    cut = away * np.clip((blob - 0.45) / 0.25, 0, 1) * 0.55
    r = np.where(camp & (x < -4.0), r - cut * r, r)
    # the paths: worn earth, ragged edges, fading out at the far end
    for pts, w, k in PATHS:
        best = np.full(r.shape, 1e9)
        along = np.zeros(r.shape)
        n = len(pts) - 1
        for s in range(n):
            ds, t = seg_dist(x, z, pts[s], pts[s + 1])
            m = ds < best
            best = np.where(m, ds, best)
            along = np.where(m, (s + t) / n, along)
        hw = w * 0.5 * (1.0 + 0.3 * noise(x, z, 2.3, 11.0))
        core = 1.0 - np.clip((best - hw * 0.6) / (hw * 0.9), 0, 1)
        fade = 1.0 - np.clip((along - 0.6) / 0.4, 0, 1) * 0.75
        val = k * (0.85 + 0.15 * noise(x, z, 3.7, 5.0)) * fade
        r = np.maximum(r, core * val)
    im[i0:i1, j0:j1, 0] = np.clip(r, 0, 1)
    Image.fromarray((im * 255.0 + 0.5).astype(np.uint8)).save(SPLAT)
    print('camp paint: R mean in the window', round(float(r.mean()), 3))


main()
