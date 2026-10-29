"""(E8 later) Low Ford's camp ground in the zone's paint (godot/data/zones/lowford/splat.png, R = trodden earth):
footpaths worn into the camp (from the road by the post lantern, north into the wood, south-west past the bedroll)
and the camp's earth broken up, grass let back in patches at its rim (thin tufts where R falls under about 0.5), its
edge ragged. (E8 later r2) It starts from the paint as committed before E8 later (the git blob PRE, so a rerun never
repeats the cut) and wears the zone's footpaths (flora_species.json "ground_paths", the lines the ground shader lightens)
to bare earth, R 1 at their core, so no grass grows on them. Run from the repo root (--from PATH: another start).

    python tools/assets/lowford_camp_paint.py [--from PATH]
"""
import io
import json
import math
import subprocess
import sys

import numpy as np
from PIL import Image

SPLAT = 'godot/data/zones/lowford/splat.png'
SIZE, RES = 260.0, 1024
FIRE = (-10.5, 90.5)
PRE = '58e2a203^:godot/data/zones/lowford/splat.png'   # the paint before E8 later's camp cut
# the paths (world x, z) from the zone's data, each worn bare (R 1) over its core width (m), fading at the far end
PATHS = [(line, 0.6, 1.0) for line in json.load(open('godot/data/zones/lowford/flora_species.json'))['ground_paths']]


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
    if '--from' in sys.argv:
        src = sys.argv[sys.argv.index('--from') + 1]
    else:
        src = io.BytesIO(subprocess.run(['git', 'show', PRE], capture_output=True, check=True).stdout)
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
        fade = 1.0 - np.clip((along - 0.75) / 0.25, 0, 1) * 0.6
        val = k * (0.85 + 0.15 * noise(x, z, 3.7, 5.0)) * fade
        r = np.maximum(r, core * val)
    im[i0:i1, j0:j1, 0] = np.clip(r, 0, 1)
    Image.fromarray((im * 255.0 + 0.5).astype(np.uint8)).save(SPLAT)
    print('camp paint: R mean in the window', round(float(r.mean()), 3))


main()
