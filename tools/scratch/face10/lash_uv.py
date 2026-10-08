"""Blender: her lashes' cards: their UV triangles drawn over the lash paint (lash_uv.png), and each card's points
in UV and in 3D (lash_cards.json: for each face, its UV and its points' positions, and the head's eye centres), so a
new paint can be drawn where the cards' roots are.

    blender -b heroine_built.blend --python lash_uv.py -- OUTDIR
"""
import json
import os
import sys

import bpy
import numpy as np

out = sys.argv[sys.argv.index("--") + 1]
names = [o.name for o in bpy.data.objects if o.type == "MESH"]
print("MESHES", names)
lash = next(o for o in bpy.data.objects if o.type == "MESH" and "ash" in o.name)
me = lash.data
print("LASHES", lash.name, len(me.vertices), "points", len(me.polygons), "faces", [m.name for m in me.materials],
      "keys", [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else None)
uv = me.uv_layers.active.data
mw = np.array(lash.matrix_world)
faces = []
for p in me.polygons:
    faces.append({"uv": [list(uv[li].uv) for li in p.loop_indices],
                  "co": [list((mw @ np.r_[np.array(me.vertices[v].co), 1.0])[:3]) for v in p.vertices],
                  "v": list(p.vertices)})
eyes = bpy.data.objects.get("HeroineEyes")
cent = []
if eyes:
    V = np.array([eyes.matrix_world @ v.co for v in eyes.data.vertices])
    left = V[:, 0] > 0
    cent = [list(V[left].mean(0)), list(V[~left].mean(0))]
json.dump({"faces": faces, "eyes": cent}, open(os.path.join(out, "lash_cards.json"), "w"))
from PIL import Image, ImageDraw  # noqa: E402
base = os.path.join(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abe65bc929823a791\godot\art\people\head_tex",
                    "heroine_lashes.png")
im = Image.open(base).convert("RGBA")
bg = Image.new("RGBA", im.size, (235, 225, 215, 255))
bg.alpha_composite(im)
big = bg.convert("RGB").resize((1024, 1024))
d = ImageDraw.Draw(big)
for f in faces:
    pts = [(u * 1024, (1 - v) * 1024) for u, v in f["uv"]]
    d.polygon(pts, outline=(255, 0, 0))
big.save(os.path.join(out, "lash_uv.png"))
print("LASH UV written")
