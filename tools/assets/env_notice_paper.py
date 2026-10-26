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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "godot" / "art" / "world" / "props" / "notice_paper.png"
C = 256
TONES = [(226, 214, 184), (214, 196, 150), (200, 194, 178), (220, 206, 170), (190, 168, 128), (228, 220, 196), (206, 186, 146), (218, 204, 176)]
KIND = ["hand", "bounty", "hand", "bill", "hand", "seal", "hand", "bill"]
INK = (38, 30, 26)
# (E9d r3) the printed headings in real words (the judge read the block glyphs as misspelt capitals): Cinzel (SIL OFL),
# the repo's own roman capitals
FONT = ROOT / "tools" / "uiforge" / "fonts" / "Cinzel-wght.ttf"
HEADS = {1: "REWARD", 3: "NOTICE", 7: "BY ORDER"}


def heading(dr, text, x0, x1, y0, y1, rnd, weight="Black"):
    """Block capitals centred in the box, as large as fit, the press's ink a little uneven."""
    size = y1 - y0
    while size > 8:
        f = ImageFont.truetype(str(FONT), size)
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
        l, t, r, b = dr.textbbox((0, 0), text, font=f)
        if r - l <= x1 - x0 and b - t <= y1 - y0:
            break
        size -= 1
    x = (x0 + x1 - (r - l)) // 2 - l
    y = (y0 + y1 - (b - t)) // 2 - t
    dr.text((x, y), text, font=f, fill=INK)


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
        heading(dr, HEADS[1], m + 14, C - m - 14, 18, 48, rnd)
        bx0, by0, bx1, by1 = 58, 54, C - 58, 170
        # (E9d r2: a woodcut print, not an icon) a cut block: the ground cut away in close hatching, the head and shoulders
        # left standing light, shaded down one side in cross-hatching, the features gouged in short uneven strokes.
        cx, cy = (bx0 + bx1) // 2, (by0 + by1) // 2 + 4
        S = 3
        bw, bh = (bx1 - bx0) * S, (by1 - by0) * S
        fig = Image.new("L", (bw, bh), 0)
        fd = ImageDraw.Draw(fig)
        hx, hy = (cx - bx0) * S, (cy - by0) * S
        fd.ellipse((hx - 26 * S, hy - 40 * S, hx + 25 * S, hy + 22 * S), fill=255)
        fd.rectangle((hx - 12 * S, hy + 8 * S, hx + 11 * S, hy + 30 * S), fill=255)
        fd.ellipse((hx - 56 * S, hy + 26 * S, hx + 54 * S, hy + 110 * S), fill=255)
        figa = np.asarray(fig) > 0
        blk = Image.new("L", (bw, bh), 255)
        bd = ImageDraw.Draw(blk)
        for t in range(-bh, bw, 5 * S // 2):
            bd.line([(t, bh), (t + bh, 0)], fill=0, width=S + rnd.randint(0, 1))
        shade = Image.new("L", (bw, bh), 255)
        sd = ImageDraw.Draw(shade)
        for t in range(-bh, bw, 3 * S):
            sd.line([(t, 0), (t + bh * 0.6, bh)], fill=0, width=S)
        yy, xx = np.mgrid[0:bh, 0:bw]
        side = (xx > hx + 6 * S + 0.25 * (yy - hy)) | (yy > hy + 34 * S)
        out = np.where(figa, np.where(side, np.asarray(shade), 255), np.asarray(blk)).astype(np.uint8)
        po = Image.fromarray(out)
        pd = ImageDraw.Draw(po)
        def g(pts, w):
            pd.line([(x * S + rnd.uniform(-1, 1), y * S + rnd.uniform(-1, 1)) for x, y in pts], fill=0, width=w * S)
        ox, oy = hx / S, hy / S
        g([(ox - 26, oy - 12), (ox - 20, oy - 42), (ox + 6, oy - 46), (ox + 24, oy - 20)], 3)   # hood's edge
        g([(ox - 15, oy - 10), (ox - 5, oy - 8)], 3)
        g([(ox + 5, oy - 8), (ox + 14, oy - 11)], 3)
        g([(ox - 16, oy - 15), (ox - 4, oy - 16)], 1)
        g([(ox + 1, oy - 4), (ox - 3, oy + 7), (ox + 3, oy + 8)], 2)
        g([(ox - 9, oy + 15), (ox + 1, oy + 13), (ox + 9, oy + 15)], 2)
        g([(ox + 10, oy - 22), (ox + 20, oy + 2)], 2)  # the scar
        g([(ox - 24, oy + 2), (ox - 12, oy + 22), (ox + 10, oy + 22), (ox + 22, oy + 4)], 1)  # jaw, beard line
        po = po.resize((bx1 - bx0, by1 - by0), Image.LANCZOS)
        ink = np.asarray(po, np.float32) / 255.0
        cellv = np.asarray(im, np.float32)
        reg = cellv[by0:by1, bx0:bx1]
        inkc = np.array(INK, np.float32)
        reg[:] = reg * ink[..., None] + inkc * (1 - ink[..., None]) * (0.85 + 0.15 * noise(by1 - by0, bx1 - bx0, 4, rng))[..., None]
        im = Image.fromarray(np.clip(cellv, 0, 255).astype(np.uint8))
        dr = ImageDraw.Draw(im)
        dr.rectangle((bx0 - 3, by0 - 3, bx1 + 2, by1 + 2), outline=INK, width=2)
        for y in (188, 208, 228):
            hand_line(dr, m + 6, C - m - 6, y, rnd, 2, 8)
    elif k == "bill":
        # (E9d r2: printed words, not black bars) a heading in big block capitals, a rule, then two columns of small type,
        # each line words of letters with gaps, a ragged right edge
        heading(dr, HEADS.get(i, "NOTICE"), m + 6, C - m - 6, 22, 52, rnd)
        dr.line([(m, 56), (C - m, 56)], fill=INK, width=2)
        dr.line([(m + 20, 60), (C - m - 20, 60)], fill=INK, width=1)
        for col in range(2):
            x0 = m + col * (C - 2 * m) // 2 + 4
            xe = x0 + (C - 2 * m) // 2 - 12
            for y in range(72, C - m - 6, 12):
                x = x0 + (8 if rnd.random() < 0.15 else 0)
                end = xe - rnd.randint(0, 30)
                while x < end - 6:
                    for _ in range(rnd.randint(2, 7)):
                        lw = rnd.randint(2, 4)
                        tall = rnd.random() < 0.25
                        dr.rectangle((x, y - (3 if tall else 0), x + lw, y + 4), fill=INK)
                        x += lw + 2
                        if x >= end:
                            break
                    x += 5
        dr.line([(C // 2, 66), (C // 2, C - m - 6)], fill=INK, width=1)
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
