#!/usr/bin/env python3
"""The notice board's notices (E9d): one sheet, 4 x 2 cells of 256 px, drawn here from noise and strokes.

    python tools/assets/env_notice_paper.py     ->  godot/art/world/props/notice_paper.png

Each cell a notice in its own aged tone (cream, yellowed, a grey rag, a browned one), foxed and darker at its edges,
inked by hand: a heading in heavier strokes, lines of a running hand (words as wiggles with gaps), one with a woodcut
face in a ruled box (a bounty), one a printed bill in columns, one sealed in red wax. env_props.py's NOTICES puts each
cell on the board (notice_board_paper), OwnProps gives the mesh this sheet.
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "godot" / "art" / "world" / "props" / "notice_paper.png"
C = 256
TONES = [(226, 214, 184), (214, 196, 150), (200, 194, 178), (220, 206, 170), (190, 168, 128), (228, 220, 196), (206, 186, 146), (218, 204, 176)]
KIND = ["hand", "bounty", "hand", "bill", "hand", "seal", "hand", "bill"]
INK = (38, 30, 26)


def noise(h, w, scale, rng):
    a = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((w + 2 * scale, h + 2 * scale), Image.BICUBIC)
    return np.asarray(im, np.float32)[scale:scale + h, scale:scale + w] / 255.0


def paper(tone, rng):
    h = w = C
    base = np.ones((h, w, 3), np.float32) * np.array(tone, np.float32) / 255.0
    n = 0.6 * noise(h, w, 32, rng) + 0.3 * noise(h, w, 8, rng) + 0.1 * noise(h, w, 2, rng)
    base *= (0.9 + 0.16 * n)[..., None]
    yy, xx = np.mgrid[0:h, 0:w] / (C - 1.0)
    edge = np.minimum(np.minimum(xx, 1 - xx), np.minimum(yy, 1 - yy))
    e = np.clip(1 - edge / 0.12, 0, 1) ** 2 * (0.6 + 0.5 * noise(h, w, 16, rng))
    base *= (1 - 0.3 * e)[..., None]
    base[..., 2] *= (1 - 0.12 * e)
    # foxing: small brown spots, a water stain
    for _ in range(rng.integers(6, 16)):
        cx, cy, r = rng.integers(0, w), rng.integers(0, h), rng.uniform(1.5, 5)
        d = np.sqrt((xx * (w - 1) - cx) ** 2 + (yy * (h - 1) - cy) ** 2)
        base *= (1 - 0.18 * np.clip(1 - d / r, 0, 1))[..., None]
    if rng.random() < 0.6:
        cx, cy, r = rng.integers(40, w - 40), rng.integers(40, h - 40), rng.uniform(30, 70)
        d = np.sqrt((xx * (w - 1) - cx) ** 2 + (yy * (h - 1) - cy) ** 2) + 10 * noise(h, w, 16, rng)
        ring = np.exp(-((d - r) / 3.0) ** 2) * 0.16 + np.clip(1 - d / r, 0, 1) * 0.05
        base *= (1 - ring)[..., None]
    return Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8))


def hand_line(dr, x0, x1, y, rnd, wgt=2, size=7):
    x = x0
    while x < x1 - 10:
        wl = rnd.randint(14, 46)
        wl = min(wl, x1 - x)
        pts = []
        steps = max(4, wl // 3)
        for k in range(steps + 1):
            t = k / steps
            px = x + t * wl
            py = y + math.sin(t * steps * 1.9 + rnd.random() * 2) * size * 0.45 * rnd.uniform(0.6, 1.0) - (size * 0.5 if rnd.random() < 0.12 else 0)
            pts.append((px, py))
        dr.line(pts, fill=INK, width=wgt)
        if rnd.random() < 0.25:
            dr.line([(x + rnd.uniform(0, wl), y - size * 0.9), (x + rnd.uniform(0, wl) + 2, y - size * 0.2)], fill=INK, width=wgt)
        x += wl + rnd.randint(6, 11)


def cell(i, rng, rnd):
    im = paper(TONES[i], rng)
    dr = ImageDraw.Draw(im)
    k = KIND[i]
    m = 22
    if k == "hand":
        hand_line(dr, m + 20, C - m - 20, 40, rnd, 4, 14)
        y = 72
        while y < C - m - 10:
            hand_line(dr, m, C - m - rnd.randint(0, 50), y, rnd, 2, 8)
            y += rnd.randint(17, 21)
        if rnd.random() < 0.6:
            dr.line([(C - 110, C - 36), (C - 40, C - 40)], fill=INK, width=2)
    elif k == "bounty":
        hand_line(dr, m + 10, C - m - 10, 34, rnd, 5, 16)
        bx0, by0, bx1, by1 = 58, 56, C - 58, 168
        dr.rectangle((bx0, by0, bx1, by1), outline=INK, width=3)
        # a woodcut face: head, hood, eyes, a scar, hatching
        cx, cy = (bx0 + bx1) // 2, (by0 + by1) // 2 + 6
        dr.ellipse((cx - 34, cy - 44, cx + 34, cy + 40), outline=INK, width=3)
        dr.pieslice((cx - 50, cy - 60, cx + 50, cy + 70), 180, 360, outline=INK, width=4)
        dr.line([(cx - 18, cy - 8), (cx - 6, cy - 6)], fill=INK, width=4)
        dr.line([(cx + 6, cy - 6), (cx + 18, cy - 8)], fill=INK, width=4)
        dr.line([(cx, cy - 2), (cx - 4, cy + 14), (cx + 3, cy + 15)], fill=INK, width=2)
        dr.line([(cx - 12, cy + 26), (cx + 12, cy + 24)], fill=INK, width=3)
        dr.line([(cx + 14, cy - 22), (cx + 26, cy + 6)], fill=INK, width=2)
        for k2 in range(14):
            dr.line([(bx0 + 4 + k2 * 4, by1 - 4), (bx0 + 4 + k2 * 4 + 14, by1 - 30)], fill=INK, width=1)
        for y in (186, 206, 226):
            hand_line(dr, m + 6, C - m - 6, y, rnd, 2, 8)
    elif k == "bill":
        dr.rectangle((m, m, C - m, 52), fill=INK)
        for x in range(m + 8, C - m - 10, 22):
            dr.rectangle((x, 30, x + 14, 44), fill=TONES[i])
        for col in range(2):
            x0 = m + col * (C - 2 * m) // 2 + 4
            for y in range(70, C - m - 6, 13):
                w = rnd.randint(60, (C - 2 * m) // 2 - 12)
                dr.rectangle((x0, y, x0 + w, y + 5), fill=INK)
        dr.line([(C // 2, 64), (C // 2, C - m - 6)], fill=INK, width=1)
    elif k == "seal":
        hand_line(dr, m + 26, C - m - 26, 40, rnd, 4, 13)
        y = 70
        while y < C - 80:
            hand_line(dr, m, C - m - rnd.randint(0, 40), y, rnd, 2, 8)
            y += 19
        cx, cy = C - 70, C - 50
        dr.ellipse((cx - 24, cy - 22, cx + 24, cy + 24), fill=(140, 34, 28))
        dr.ellipse((cx - 14, cy - 12, cx + 14, cy + 14), outline=(96, 20, 18), width=3)
        dr.polygon([(cx - 8, cy + 20), (cx - 20, cy + 52), (cx - 2, cy + 44)], fill=(150, 40, 32))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    return im


def main():
    rng = np.random.default_rng(9)
    rnd = random.Random(9)
    sheet = Image.new("RGB", (4 * C, 2 * C))
    for i in range(8):
        sheet.paste(cell(i, rng, rnd), ((i % 4) * C, (i // 4) * C))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
