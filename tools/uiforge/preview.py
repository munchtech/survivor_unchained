"""Previews: frames nine-sliced as Godot draws them (stretched or tiled to
fit), at their shown size, over a picture of the game; and contact sheets.
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def halve(img: Image.Image) -> Image.Image:
    return img.resize((max(1, img.width // 2), max(1, img.height // 2)), Image.LANCZOS)


def nine(img: Image.Image, size, margins, tile=False) -> Image.Image:
    """`img` at shown scale (already halved), drawn at `size` with margins (L, T, R, B)."""
    W, H = size
    l, t, r, b = margins
    iw, ih = img.size
    xs = [0, l, iw - r, iw]
    ys = [0, t, ih - b, ih]
    xd = [0, l, W - r, W]
    yd = [0, t, H - b, H]
    out = Image.new("RGBA", (W, H))
    for j in range(3):
        for i in range(3):
            src = img.crop((xs[i], ys[j], xs[i + 1], ys[j + 1]))
            w, h = xd[i + 1] - xd[i], yd[j + 1] - yd[j]
            if w <= 0 or h <= 0 or src.width <= 0 or src.height <= 0:
                continue
            if tile and (i == 1 or j == 1):
                # Tile-fit: a whole number of tiles, scaled to fit.
                nx = max(1, round(w / src.width)) if i == 1 else 1
                ny = max(1, round(h / src.height)) if j == 1 else 1
                tw = src.width * nx if i == 1 else src.width
                th = src.height * ny if j == 1 else src.height
                strip = Image.new("RGBA", (tw, th))
                for yy in range(ny):
                    for xx in range(nx):
                        strip.paste(src, (xx * src.width, yy * src.height))
                part = strip.resize((w, h), Image.LANCZOS)
            else:
                part = src.resize((w, h), Image.LANCZOS)
            out.paste(part, (xd[i], yd[j]))
    return out


def over(bg: Image.Image, fg: Image.Image, at):
    bg = bg.convert("RGBA")
    bg.alpha_composite(fg, at)
    return bg


def sheet(images, cols=4, pad=8, bg=(24, 22, 28), scale=1.0):
    ims = [im if scale == 1 else im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS) for im in images]
    cw = max(i.width for i in ims)
    ch = max(i.height for i in ims)
    rows = (len(ims) + cols - 1) // cols
    out = Image.new("RGBA", (cols * (cw + pad) + pad, rows * (ch + pad) + pad), bg + (255,))
    for n, im in enumerate(ims):
        x = pad + (n % cols) * (cw + pad)
        y = pad + (n // cols) * (ch + pad)
        out.alpha_composite(im.convert("RGBA"), (x, y))
    return out
