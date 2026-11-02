"""Storybook 4, sb00-prejudge-fixes: p4's smoke curl and the pale wisp above the post lamp (left where the second
Watchman was painted out) inpainted to plain sky. Shows once p4's pan rises (sb_wire_ink.plate_p4).

    python tools/storybook/ink_p4_wisp.py      # gpu turn; writes out/ink_layers/p4/_base_nowisp.png (cached)

plate_p4 uses that file for base.png when it exists (Plate.made), so an ink_build re-run of p4 doesn't lose it.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_recarve as RC  # noqa: E402

DIR = os.path.join(HERE, "out", "ink_layers", "p4")
DST = os.path.join(DIR, "_base_nowisp.png")
BOX = (4000, 0, 4704, 400)                          # base px (p4 is 1 unit a px)
ELLS = [(4340, 100, 195, 120), (4474, 240, 32, 46)]  # the smoke curl; the pale wisp over the spout (lamp left out)
PROMPT = ("Woodcut print. A bright sunset sky carved in long sweeping gouge lines, orange strokes over pale yellow light, clear open sky. "
          "No smoke, no clouds, no black shapes, no flame, no figure.")


def main(dn=0.8, seed=11):
    import ink_comfy as C
    if os.path.exists(DST):
        return DST
    tmp = os.path.join(DIR, "_wisp")
    os.makedirs(tmp, exist_ok=True)
    rgba = np.asarray(Image.open(os.path.join(DIR, "base.png")).convert("RGBA")).astype(np.float32)
    img = rgba[..., :3]
    m = Image.new("L", (img.shape[1], img.shape[0]), 0)
    d = ImageDraw.Draw(m)
    for cx, cy, rx, ry in ELLS:
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    m = np.asarray(m) > 127
    w = np.clip(nd.distance_transform_edt(m) / 14, 0, 1)
    x0, y0, x1, y1 = BOX
    k = 2
    cw, ch = (x1 - x0) * k // 16 * 16, (y1 - y0) * k // 16 * 16
    ci, mi, raw = (os.path.join(tmp, f) for f in ("crop.png", "mask.png", "raw.png"))
    Image.fromarray(img[y0:y1, x0:x1].astype(np.uint8)).resize((cw, ch), Image.LANCZOS).save(ci)
    Image.fromarray((m[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((cw, ch), Image.NEAREST).save(mi)
    C.krea(f"{PROMPT} {RC.R2['style']}", cw, ch, seed, raw, init=ci, denoise=dn, mask=mi)
    back = np.asarray(Image.open(raw).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.float32) / 255
    import ink_post as IP
    back = IP.post(back, offset=(x0, y0)) * 255   # the plate's palette and paper, registered
    ww = w[y0:y1, x0:x1, None]
    rgba[y0:y1, x0:x1, :3] = img[y0:y1, x0:x1] * (1 - ww) + back * ww
    Image.fromarray((rgba + 0.5).astype(np.uint8), "RGBA").save(DST)
    return DST


if __name__ == "__main__":
    print(main())
