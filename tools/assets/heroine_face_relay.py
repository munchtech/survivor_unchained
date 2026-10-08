"""A face's new paint laid on her head's texture without building her again (heroine_head.py lays a face paint over
her skin by its alpha: head = base x (1 - alpha) + paint x alpha, the base matched to the paint only by its broad
colour where they meet). So the new head is the old one's raw copy (before heroine_face_fixes) plus alpha times the
change in the paint, then the fixes run again on it (in Blender, on her built head, shaped as that face).

    python tools/assets/heroine_face_relay.py ID NEW_FACE_PAINT.png [OUT.jpg]        # ID: own, doe, sunborn, ...
    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_face_relay.py -- ID NEW.png [OUT]

Without Blender the fixes are skipped (her lids' painted lash line and, for her own face, her nostrils and the line
between her lips are left as the raw paint has them): enough to look at a paint in the game, not to ship it. The old
paint (tools/assets/heroine_face/face_paint[_ID].png) must be the one her head was built from: its alpha is checked
against the new one's, and the raw copy is tools/comfy/out/heroes/heroine_head_raw[_ID].jpg.
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
FACE_DIR = os.path.join(HERE, "heroine_face")
RAW_DIR = os.path.join(ROOT, "tools", "comfy", "out", "heroes")
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")


def paths(face):
    own = face in ("own", "", None)
    sfx = "" if own else "_" + face
    return (os.path.join(FACE_DIR, f"face_paint{sfx}.png"), os.path.join(RAW_DIR, f"heroine_head_raw{sfx}.jpg"),
            os.path.join(TEX, f"heroine_head{sfx}.jpg"))


def relay(face, new_paint, out=None, raw_out=None):
    """The head's raw paint with the new face paint laid in place of the old; written to raw_out (or beside `out`
    as <out>_raw.jpg) and returned as an array (rows from the top, 0 to 255)."""
    old_p, raw_p, tex_p = paths(face)
    out = out or tex_p
    old = np.asarray(Image.open(old_p).convert("RGBA"), np.float32) / 255
    new = np.asarray(Image.open(new_paint).convert("RGBA"), np.float32) / 255
    raw = np.asarray(Image.open(raw_p).convert("RGB"), np.float32)
    da = np.abs(new[..., 3] - old[..., 3])
    print("RELAY %s: alpha changed by %.4f at most (mean %.5f) over %d%% of the paint" % (
        face, da.max(), da.mean(), 100 * (old[..., 3] > 0.5).mean()))
    a = old[..., 3:4]
    if da.max() > 0.02:
        # (laid where both cover: the old paint's alpha is what her head was built with)
        a = np.minimum(old[..., 3:4], new[..., 3:4])
    # (the paints' colours as 0-255 sRGB, as heroine_head.py saved them: an 8-bit step at most)
    d = (new[..., :3] - old[..., :3]) * 255 * a
    out_a = np.clip(raw + d, 0, 255)
    edge = (a[..., 0] > 0.02) & (a[..., 0] < 0.5)
    if edge.any():
        print("RELAY %s: at the paint's soft edge the colour moves %.2f%% (mean)" % (face, 100 * np.abs(d[edge]).mean() / 255))
    raw_out = raw_out or os.path.splitext(out)[0] + "_raw.jpg"
    Image.fromarray((out_a + 0.5).astype(np.uint8)).save(raw_out, quality=95, subsampling=0)
    return out_a, raw_out


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    face, new_paint = args[0], os.path.abspath(args[1])
    out = os.path.abspath(args[2]) if len(args) > 2 else paths(face)[2]
    img, raw_out = relay(face, new_paint, out)
    try:
        import bpy  # noqa: F401
        in_blender = True
    except ImportError:
        in_blender = False
    if in_blender:
        import bpy
        sys.path.insert(0, HERE)
        import heroine_face_fixes as fx
        head = bpy.data.objects["HeroineHead"]
        fx.fix(head, out, raw=raw_out, key=None if face in ("own", "") else f"face_{face}")
        print("RELAY %s: fixed and written %s" % (face, out))
    else:
        Image.fromarray((img + 0.5).astype(np.uint8)).save(out, quality=95, subsampling=0)
        print("RELAY %s: written %s (no fixes: run in Blender for them)" % (face, out))
