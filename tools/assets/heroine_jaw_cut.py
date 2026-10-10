"""A face's paint taken off her neck under her jaw on a head already built, without building her again.

The portraits' necks lie in their jaws' shadow; laid on her (the lay's cut below her chin missed her neck: its
chin, the lowest point turned forward down her middle, was her neck's), that shadow showed as a grey-violet patch
with a stepped edge down the front and sides of her neck on every face (the owner, 10 October 2026).
heroine_face.py's lay now leaves her neck to her head's own skin (under_jaw); this puts the heads already built
right the same way:

    FACE_JAW_ONLY=1 FACE_SHAPE=<the face's sliders> FACE_JAW_MARKS=<its drawing's landmarks> \
    FACE_JAW_HEAD=godot/art/people/head_tex/heroine_head[_ID].jpg \
        blender -b tools/comfy/out/heroes/heroine_unpainted.blend --python tools/assets/heroine_face.py -- DIR
    python tools/assets/heroine_jaw_cut.py ID DIR [OUT_DIR]           # ID: own, doe, sunborn, ...

The first writes DIR/jaw_cut.png (under_jaw, 0 to 1 a texel), DIR/base_skin.png (her head's own skin, MakeHuman's
in her colouring, eased into her body's at her neck) and DIR/jaw_field.npz (what her own skin is brought by where
the paint comes off: a smooth field over her head's points, held to the head's paint where nothing is cut and to
her body's skin over the 6 mm above SPLIT, as heroine_head.py's matched_base brings it). This lays her own skin
and that field over the head's paint by the cut, in her head's paint and its raw copy (before heroine_face_fixes,
which touch only her lids, nostrils and lips), and writes the face paint's alpha as cut, so a build or a relay
after lays it as the head now has it. (OUT_DIR: all three written there by their own names, for a look first.)
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heroine_face_relay import paths  # noqa: E402


def cut(face, d, out_dir=None, head_in=None):
    """(head_in: that head's paint alone, written into out_dir: a paint laid since, not yet relayed onto her head)"""
    paint_p, raw_p, tex_p = paths(face)
    fp = np.asarray(Image.open(paint_p).convert("RGBA"), np.float32) / 255
    c = np.asarray(Image.open(os.path.join(d, "jaw_cut.png")).convert("L"), np.float32) / 255
    bs = np.asarray(Image.open(os.path.join(d, "base_skin.png")).convert("RGB"), np.float32) / 255
    f = np.load(os.path.join(d, "jaw_field.npz"))
    base = bs.copy()
    base[f["rows"], f["cols"]] = f["colour"]
    print("JAW CUT %s: her neck's own colour laid over %.2f%% of her head" % (face, 100 * (c > 0.5).mean()))
    for p in ((head_in,) if head_in else (raw_p, tex_p)):
        h = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255
        h2 = h * (1 - c[..., None]) + base * c[..., None]
        q = os.path.join(out_dir, os.path.basename(p)) if out_dir else p
        Image.fromarray((h2 * 255 + 0.5).astype(np.uint8)).save(q, quality=95, subsampling=0)
        print("  written", q)
    if head_in:
        return
    fp2 = fp.copy()
    fp2[..., 3] = fp[..., 3] * (1 - c)
    q = os.path.join(out_dir, os.path.basename(paint_p)) if out_dir else paint_p
    Image.fromarray((fp2 * 255 + 0.5).astype(np.uint8)).save(q)
    print("  written", q)


if __name__ == "__main__":
    cut(*sys.argv[1:5])
