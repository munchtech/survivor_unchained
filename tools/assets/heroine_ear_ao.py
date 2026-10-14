"""Her ears' hollows as a shade of their own: heroine_ear_ao.png (red; white everywhere else).

The bowl of her ear (the concha), the notch under it and the fold under her helix read grey-white inside a warm ear
at the Look (judge rj5v, 13 October 2026): her head's shade (heroine_ao.png, 5 cm rays per point) barely dims them,
so the cool fill and the sky reach into the bowl. This is a short-reach shade over her ears alone: per texel, RAYS
cosine-weighted rays against her head out to REACH (nearer hits counting more), smoothed over her surface (SIGMA),
GAIN times, floored at FLOOR, and eased in over the ear's reach (heroine_ears.py's EAR_R, and |x| past DEEP so the
bowl's deep floor is in). The skin shader (ear_ao) multiplies it into her head's shade, lets it dim the lamps too
(ear_light) and warms by it (ear_tint): People.Skin, her head only.

    python tools/assets/heroine_ear_ao.py        (writes godot/art/people/head_tex/heroine_ear_ao.png; trimesh, Embree)
"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage
from trimesh.ray.ray_pyembree import RayMeshIntersector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lobe as hl  # noqa: E402

SIZE = 2048
REACH = 0.012          # (metres: the ear's own folds, not her head's side)
RAYS = 64
SIGMA = 0.0005
GAIN, FLOOR = 2.2, 0.45
DEEP = (0.050, 0.054)
BOX = (0.046, 1.684, 1.792, -0.068, 0.022)
PAD = 16


def dirs(k, seed=7):
    n = int(np.sqrt(k))
    rng = np.random.default_rng(seed)
    i, j = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    u = (i.ravel() + rng.random(n * n)) / n
    v = (j.ravel() + rng.random(n * n)) / n
    return np.c_[np.sqrt(u) * np.cos(2 * np.pi * v), np.sqrt(u) * np.sin(2 * np.pi * v), np.sqrt(1 - u)]


def occlusion(pos, nrm, mi, chunk=20000):
    D = dirs(RAYS)
    occ = np.zeros(len(pos))
    for s0 in range(0, len(pos), chunk):
        p, n = pos[s0:s0 + chunk], nrm[s0:s0 + chunk]
        a = np.where(np.abs(n[:, 2:3]) < 0.9, [[0, 0, 1.0]], [[1.0, 0, 0]])
        t1 = np.cross(n, a)
        t1 /= np.linalg.norm(t1, axis=1, keepdims=True)
        t2 = np.cross(n, t1)
        w = (D[None, :, 0:1] * t1[:, None] + D[None, :, 1:2] * t2[:, None] + D[None, :, 2:3] * n[:, None]).reshape(-1, 3)
        o = np.repeat(p + n * 0.0004, RAYS, 0)
        locs, ir, _ = mi.intersects_location(o, w, multiple_hits=False)
        d = np.linalg.norm(locs - o[ir], axis=1)
        wt = np.zeros(len(o))
        wt[ir[d < REACH]] = 1 - d[d < REACH] / REACH
        occ[s0:s0 + chunk] = wt.reshape(-1, RAYS).mean(1)
    return occ


def main():
    P, N, UV, T = hl.head()
    mi = RayMeshIntersector(trimesh.Trimesh(P, T, process=False))
    hl.BOX = BOX
    img = np.ones((SIZE, SIZE))
    for side in (-1, 1):
        r, c, pos, nrm = hl.texels(P, N, UV, T, side, SIZE)
        occ = hl.smoothed(pos, occlusion(pos, nrm, mi)[:, None], SIGMA)[:, 0]
        ax = pos[:, 0] * side
        d = np.linalg.norm(np.c_[ax, pos[:, 1], pos[:, 2]] - np.array(hl.EAR), axis=1)
        gate = (1 - hl.smooth(hl.EAR_R[0], hl.EAR_R[1], d)) * hl.smooth(DEEP[0], DEEP[1], ax)
        ea = 1 - (1 - np.maximum(FLOOR, 1 - GAIN * occ)) * gate
        img[r, c] = ea
        x0, y0 = max(c.min() - PAD - 2, 0), max(r.min() - PAD - 2, 0)
        x1, y1 = min(c.max() + PAD + 3, SIZE), min(r.max() + PAD + 3, SIZE)
        cov = hl.covered(UV, T, SIZE, (x0, y0, x1, y1))
        sub = img[y0:y1, x0:x1]
        dist, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
        pad = (~cov) & (dist <= PAD)
        sub[pad] = sub[iy[pad], ix[pad]]
        core = gate > 0.9
        print("EAR AO side %+d: %d texels, shade under 0.9 on %d, median in it %.2f, min %.2f" % (
            side, len(r), int((ea < 0.9).sum()), np.median(ea[ea < 0.9]) if (ea < 0.9).any() else 1, ea[core].min()))
    out = os.path.join(hl.TEX, "heroine_ear_ao.png")
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(out)
    print("EAR AO", out)


if __name__ == "__main__":
    main()
