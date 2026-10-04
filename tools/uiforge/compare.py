"""Before and after, side by side: the game's screens with the drawn look (before) and
with the painted art (after), from pictures taken by shots.py with the art folder moved
away and back. Written to docs/concepts/ui/style/ as JPEGs (kept small for the repo).

    python tools/uiforge/compare.py BEFORE_PREFIX AFTER_PREFIX [NAME ...]
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SHOTS = os.path.join(ROOT, "godot", ".shots")
OUT = os.path.join(ROOT, "docs", "concepts", "ui", "style")
FONT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "fonts", "alegreya-sans-700.ttf")


def pair(before, after, name, width=1920):
    a = Image.open(os.path.join(SHOTS, f"{before}_{name}.png")).convert("RGB")
    b = Image.open(os.path.join(SHOTS, f"{after}_{name}.png")).convert("RGB")
    half = width // 2
    h = int(a.height * half / a.width)
    out = Image.new("RGB", (width, h + 34), (12, 10, 14))
    out.paste(a.resize((half, h), Image.LANCZOS), (0, 34))
    out.paste(b.resize((half, h), Image.LANCZOS), (half, 34))
    d = ImageDraw.Draw(out)
    try:
        f = ImageFont.truetype(FONT, 20)
    except OSError:
        f = None
    d.text((12, 6), f"{name}: before (drawn placeholder)", fill=(200, 190, 170), font=f)
    d.text((half + 12, 6), f"{name}: after (painted art)", fill=(243, 217, 160), font=f)
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, f"{name}.jpg"), quality=86, optimize=True)


def main():
    before, after = sys.argv[1], sys.argv[2]
    names = sys.argv[3:] or sorted({f[len(after) + 1:-4] for f in os.listdir(SHOTS) if f.startswith(after + "_")})
    for n in names:
        if os.path.exists(os.path.join(SHOTS, f"{before}_{n}.png")):
            pair(before, after, n)
            print(n)


if __name__ == "__main__":
    main()
