"""Every shipped icon on one sheet per set, named, for the legal lead's pre-launch check (each
icon laid beside the named commercial sets, and any close to a specific one remade).

    python tools/uiforge/iconsheet.py [OUTDIR]     # default docs/legal/icon_check/
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ICONS = os.path.join(ROOT, "godot", "art", "ui", "icons")


def sheet(dirpath, out, cell=112, cols=12, bg=(22, 19, 21)):
    files = sorted(f for f in os.listdir(dirpath) if f.endswith(".png"))
    rows = (len(files) + cols - 1) // cols
    lab = 16
    im = Image.new("RGB", (cols * cell, rows * (cell + lab) + 40), bg)
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("arial.ttf", 11)
        big = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        fnt = big = ImageFont.load_default()
    d.text((8, 10), f"{os.path.relpath(dirpath, ROOT)}  ({len(files)})", fill=(220, 210, 190), font=big)
    for i, f in enumerate(files):
        x, y = (i % cols) * cell, 40 + (i // cols) * (cell + lab)
        ic = Image.open(os.path.join(dirpath, f)).convert("RGBA")
        ic.thumbnail((cell - 12, cell - 12), Image.LANCZOS)
        tile = Image.new("RGBA", (cell, cell), bg + (255,))
        tile.alpha_composite(ic, ((cell - ic.width) // 2, (cell - ic.height) // 2))
        im.paste(tile.convert("RGB"), (x, y))
        d.text((x + 4, y + cell), f[:-4][:18], fill=(170, 160, 145), font=fnt)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, quality=88)
    return out, len(files)


def main(outdir=None):
    outdir = outdir or os.path.join(ROOT, "docs", "legal", "icon_check")
    for s in sorted(os.listdir(ICONS)):
        p = os.path.join(ICONS, s)
        if os.path.isdir(p):
            print(*sheet(p, os.path.join(outdir, f"icons_{s}.jpg")))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
