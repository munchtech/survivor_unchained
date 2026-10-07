"""UV2 (the chain's place and weight) per hair style and part: its range, and the sway weight
(hang^2 * tip * moves) the shader's other branch would use, at rest."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from hair_skin import acc, D  # noqa: E402

for style in sys.argv[1:]:
    g = json.load(open(os.path.join(D, f"heroine_hair_{style}.gltf"), encoding="utf-8"))
    bins = [open(os.path.join(D, b["uri"]), "rb").read() for b in g["buffers"]]
    chain = os.path.exists(os.path.join(D, f"heroine_hair_{style}.chain.json"))
    print(f"== {style} (chain file: {chain})")
    for m in g["meshes"]:
        for pr in m["primitives"]:
            at = pr["attributes"]
            mat = g["materials"][pr["material"]]["name"]
            uv2 = acc(g, bins, at["TEXCOORD_1"])
            print(f"  {mat}: UV2.x {uv2[:, 0].min():.3f}..{uv2[:, 0].max():.3f}  UV2.y {uv2[:, 1].min():.3f}..{uv2[:, 1].max():.3f}"
                  f"  y quantiles {np.quantile(uv2[:, 1], [0.1, 0.5, 0.9]).round(3)}")
