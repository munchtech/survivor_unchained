"""Her upper lids' paint cleaned of the lashes painted on them. Her face was
painted (heroine_face.py) with her eyes open, and the painting drew her
lash line where the lid meets the eye; when she blinks, the lid stretches
down over the eye and that line with it, into stripes. Her lashes are their
own mesh: on the lid itself there should be only skin.

The lid is found as what her blink moves (her head's blink_l and blink_r
shape keys, points moving down more than 1.5 mm), drawn into her head's
paint by its UVs (feathered), and there every thin dark line (thinner than
a few texels) is closed over by the skin round it: a grey-scale closing,
which keeps the lid's colour and shading and drops the lashes.

As a step of heroine_head.py (clean(head, path)), or alone on the blend it
saved:

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_lids.py
"""
import os

import numpy as np


def clean(head, path, size=13, moved=0.0015):
    """Her upper lids in the paint at `path` (her head's) cleaned in place."""
    from PIL import Image, ImageDraw
    from scipy import ndimage
    me = head.data
    keys = me.shape_keys.key_blocks
    base = np.array([v.co[:] for v in keys["Basis"].data])
    down = np.zeros(len(base), bool)
    for name in ("blink_l", "blink_r"):
        if name in keys:
            d = np.array([v.co[:] for v in keys[name].data]) - base
            down |= (d[:, 2] < -moved)
    img = Image.open(path).convert("RGB")
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    uv = me.uv_layers.active.data
    lids = 0
    for p in me.polygons:
        if down[list(p.vertices)].sum() * 2 > len(p.vertices):
            draw.polygon([(uv[li].uv[0] * w, (1 - uv[li].uv[1]) * h) for li in p.loop_indices], fill=255)
            lids += 1
    m = np.asarray(mask, np.float32) / 255
    m = ndimage.gaussian_filter(ndimage.maximum_filter(m, 7), 3)[..., None]
    a = np.asarray(img, np.float32)
    closed = np.stack([ndimage.grey_closing(a[..., c], size=(size, size)) for c in range(3)], -1)
    closed = np.stack([ndimage.gaussian_filter(closed[..., c], 1.2) for c in range(3)], -1)
    out = a * (1 - m) + closed * m
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path, quality=92)
    print("LIDS cleaned:", lids, "faces of her upper lids in", os.path.basename(path))


if __name__ == "__main__":
    import bpy
    head = bpy.data.objects["HeroineHead"]
    tex = next(n.image for n in head.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE")
    path = bpy.path.abspath(tex.filepath)
    clean(head, path)
    # (packed in the blend: its old paint dropped, the new read and packed)
    if tex.packed_file:
        tex.unpack(method="REMOVE")
    tex.filepath = path
    tex.reload()
    tex.pack()
    bpy.ops.wm.save_mainfile()
