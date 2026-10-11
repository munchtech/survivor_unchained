"""Her head's nearness to her neck's seam, for her skin's shader to ease her head's own skin into her graft's there.

Her head and the graft below it meet along SPLIT as one surface (heroine_seam.py), and her paint matches across it,
but her head's skin is set otherwise than her body's: more matte (rough 0.6, shine 0.36 against 0.5 and 0.42),
deeper pores, her face's grain. Seen side on, that drew SPLIT across her neck as a stair-stepped line, the head's
side greyer and grained, the graft's smooth and pinker, a sheen on it stopping dead at the line (judge n1, 11
October 2026). The shader eases her head's skin into the graft's (People.Skin's seam_* uniforms) by this: 1 on her
head, 0 at SPLIT, smoothstepped over the SEAM metres above it, written into heroine_ao.png's green (its red is her
head's shade; the shader reads only the red for that).

    python tools/assets/heroine_ao_seam.py godot/art/people/heroine.glb godot/art/people/head_tex/heroine_ao.png

No Blender: her head's points and UVs from the glb. heroine_features.py rewrites heroine_ao.png; run this after it.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

SEAM = 0.03          # (metres above SPLIT over which her head's skin comes in)


def split_gl(P):
    """Above SPLIT (heroine_head.py's s_split), from glTF's axes (y up, -z Blender's y)."""
    return P[:, 1] - (1.625 + 0.27 * (-P[:, 2] + 0.02))


def weight(P):
    x = np.clip(split_gl(P) / SEAM, 0, 1)
    return x * x * (3 - 2 * x)


def raster(UV, T, val, size):
    """Per texel, from its triangle's points (UV in glTF's, top row first); texels no triangle covers take the
    nearest covered one's."""
    out = np.ones((size, size), np.float32)
    cov = np.zeros((size, size), bool)
    U = UV * size
    for k, t in enumerate(U[T]):
        x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, c = t
        v0, v1, v2 = b - a, c - a, q - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        vv = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        ww = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        bb = np.stack([1 - vv - ww, vv, ww], 1)
        m = (bb > -1e-3).all(1)
        out[ys.ravel()[m], xs.ravel()[m]] = (val[T[k]][None] * bb[m]).sum(1)
        cov[ys.ravel()[m], xs.ravel()[m]] = True
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return out[iy, ix]


def main(glb, png):
    js, binc = hs._load(glb)
    mats = [m.get("name") for m in js["materials"]]
    prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
    node = next(n for n in js["nodes"] if n.get("mesh") is not None and any(
        p is prim for p in js["meshes"][n["mesh"]]["primitives"]))
    assert not any(k in node for k in ("matrix", "rotation", "scale", "translation")) or \
        node.get("translation", [0, 0, 0]) == [0, 0, 0], "her head's node moves it: points not in her frame"
    P = hs._read(js, binc, prim["attributes"]["POSITION"])
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    im = np.asarray(Image.open(png).convert("RGBA")).copy()
    w = raster(UV, T, weight(P), im.shape[0])
    im[..., 1] = (np.clip(w, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(im).save(png)
    print("SEAM WEIGHT %s: %d points, %.1f%% of texels under 1" % (png, len(P), 100 * (w < 0.999).mean()))


if __name__ == "__main__":
    main(*sys.argv[1:3])
