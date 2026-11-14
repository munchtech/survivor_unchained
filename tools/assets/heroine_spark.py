"""Where her head may take the cel model's small hard highlight: heroine_spark.png, for the skin shader's spark_map.

The skin's cel highlight (heroine_skin.gdshader CEL_SPEC) is a disc of 6 degrees round N.H. On a small, tightly
curved form (her nose's tip, her lips, her lids' rims, her ears) those 6 degrees are a few millimetres: a spark. On a
broad one (her forehead, cheeks, temples, jaw) they cover centimetres, and the disc's outline follows the normal's
every wobble: pale, hard-edged patches on her forehead and cheek and on an NPC's jaw (13 Nov, after the same patches
were taken off her body: Look.SkinHighlight). So the disc is kept where her head's surface is tightly curved: her
mean convex curvature (from each point's edges, (n_j - n_i).(p_j - p_i) / |p_j - p_i|^2, its largest and smallest
eased over her surface and averaged) smoothstepped from LOW to HIGH per metre (a radius of about 22 mm to 12 mm), as
a gray map in her head's UV. It is her base head's, so every NPC on that head takes it too.

    python tools/assets/heroine_spark.py godot/art/people/heroine.glb godot/art/people/head_tex/heroine_spark.png

No Blender: her head's points, normals and UVs from the glb, as heroine_thin.py.
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
from heroine_ao_seam import raster  # noqa: E402
from heroine_thin import ease  # noqa: E402

LOW, HIGH = 45.0, 85.0   # (mean curvature per metre: her forehead 10-15, cheekbones about 30, nose tip about 140)
EASE = 4                 # (rounds of averaging with her neighbours: her edges are about 2 mm, one ring alone is noisy)
SIZE = 1024


def curvature(P, N, T):
    """Each point's largest and smallest convex curvature along its edges (per metre; convex positive)."""
    N = N / np.linalg.norm(N, axis=1, keepdims=True)
    E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    E = np.concatenate([E, E[:, ::-1]])
    d = P[E[:, 1]] - P[E[:, 0]]
    k = ((N[E[:, 1]] - N[E[:, 0]]) * d).sum(1) / np.maximum((d * d).sum(1), 1e-12)
    hi = np.full(len(P), -1e9); lo = np.full(len(P), 1e9)
    np.maximum.at(hi, E[:, 0], k); np.minimum.at(lo, E[:, 0], k)
    return hi, lo


def main(glb, png):
    js, binc = hs._load(glb)
    mats = [m.get("name") for m in js["materials"]]
    prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
    P = hs._read(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
    N = hs._read(js, binc, prim["attributes"]["NORMAL"]).astype(np.float64)
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    hi, lo = curvature(P, N, T)
    mean = 0.5 * (ease(hi, T, EASE) + ease(lo, T, EASE))
    x = np.clip((mean - LOW) / (HIGH - LOW), 0, 1)
    w = raster(UV, T, x * x * (3 - 2 * x), SIZE)
    g = (np.clip(w, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(np.stack([g, g, g], -1), "RGB").save(png)   # (gray in RGB: the shader reads red)
    print("SPARK %s: %d points, %.1f%% spark (over 0.5), %.1f%% of texels over 0.5" %
          (png, len(P), 100 * (x > 0.5).mean(), 100 * (w > 0.5).mean()))


if __name__ == "__main__":
    main(*sys.argv[1:3])
