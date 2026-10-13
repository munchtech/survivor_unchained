"""Where her head is thin enough for light to come through it (her ears, the wings of her nose), for her skin's
shader to keep its light-through-skin term (BACKLIGHT) there and nowhere else.

Godot's BACKLIGHT has no thickness: it lights every surface turned from a lamp, so the underside of her jaw, turned
away from the key, took a salmon line along its edge (judge n2, 11 October 2026). This measures her head's
thickness at each point (a ray in along the inward normal to the far side of her: a few millimetres through an ear
or a nostril's wing, centimetres anywhere else, nothing at all where it leaves through her open neck) and writes
1 - smoothstep(THIN, THICK, depth), eased over her surface, into heroine_ao.png's blue (its red is her head's shade,
its green her seam's ease, heroine_ao_seam.py). The shader reads it as `thin_map` (People.Skin).

    python tools/assets/heroine_thin.py godot/art/people/heroine.glb godot/art/people/head_tex/heroine_ao.png

No Blender: her head's points, normals and UVs from the glb (trimesh with Embree for the rays). Run after
heroine_features.py, which rewrites heroine_ao.png.
"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
from heroine_ao_seam import raster  # noqa: E402

THIN, THICK = 0.004, 0.010   # (metres through her: an ear's rim is 2-4 mm, a nostril's wing 3-5, a lobe 5-7)
EASE = 3                     # (rounds of averaging with her neighbours, so no single point stands out)
LIDS = (0.017, 0.023)        # (metres from each eye's middle: her lids are thin too, but lit through from her shade
                             # they glowed red round her eyes; none within the first, all past the second)


def depth(P, N, T):
    mesh = trimesh.Trimesh(P, T, process=False)
    rays = trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)
    d = -N / np.linalg.norm(N, axis=1, keepdims=True)
    o = P + d * 2e-4
    loc, ri, _ = rays.intersects_location(o, d, multiple_hits=False)
    out = np.full(len(P), 1.0)
    out[ri] = np.linalg.norm(loc - o[ri], axis=1)
    return out


def ease(v, T, rounds):
    for _ in range(rounds):
        s = np.zeros_like(v); c = np.zeros_like(v)
        for a, b in ((0, 1), (1, 2), (2, 0)):
            np.add.at(s, T[:, a], v[T[:, b]]); np.add.at(c, T[:, a], 1)
            np.add.at(s, T[:, b], v[T[:, a]]); np.add.at(c, T[:, b], 1)
        v = 0.5 * v + 0.5 * s / np.maximum(c, 1)
    return v


def main(glb, png):
    js, binc = hs._load(glb)
    mats = [m.get("name") for m in js["materials"]]
    prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
    P = hs._read(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
    N = hs._read(js, binc, prim["attributes"]["NORMAL"]).astype(np.float64)
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    t = depth(P, N, T)
    x = np.clip((t - THIN) / (THICK - THIN), 0, 1)
    thin = 1 - x * x * (3 - 2 * x)
    eprim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "eyes")
    E = hs._read(js, binc, eprim["attributes"]["POSITION"]).astype(np.float64)
    centres = [E[E[:, 0] < 0].mean(0), E[E[:, 0] >= 0].mean(0)]
    r = np.min([np.linalg.norm(P - c, axis=1) for c in centres], axis=0)
    y = np.clip((r - LIDS[0]) / (LIDS[1] - LIDS[0]), 0, 1)
    thin = ease(thin * y * y * (3 - 2 * y), T, EASE)
    im = np.asarray(Image.open(png).convert("RGBA")).copy()
    w = raster(UV, T, thin, im.shape[0])
    im[..., 2] = (np.clip(w, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(im).save(png)
    print("THIN %s: %d points, %.1f%% thin (over 0.5), %.1f%% of texels over 0.5" %
          (png, len(P), 100 * (thin > 0.5).mean(), 100 * (w > 0.5).mean()))


if __name__ == "__main__":
    main(*sys.argv[1:3])
