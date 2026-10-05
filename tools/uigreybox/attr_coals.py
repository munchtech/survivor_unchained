"""Self's attributes as a ledger line with the points as coals (the owner, 5 October: "the stat
stuff in blocks still dosn't work for me even though you made them much shorter they are still
ai boxes"; the coordinator: no containers; a point to spend is an ember in an iron dish).

At 1:1 on the panel's real ground (cut from a game shot), two states: at rest with two points
to spend, and mid-spend with one sent to Might.

    python tools/uigreybox/attr_coals.py SHOTS_DIR OUT_DIR

The coal and the dish are drawn here as stand-ins; UI art paints the real ones."""
import math
import os
import random
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from gb import font, DISPLAY, DISPLAY_L, UI, UI_B, UI_H, TEXT_I

INK = (236, 230, 218)
INK2 = (198, 192, 180)
DIM = (140, 134, 124)
HEAD = (201, 186, 148)
EMBER = (255, 138, 58)
EMBER_HI = (255, 208, 122)
RULE = (70, 64, 68)
W = 900


def ground(shots, h):
    """The panel's ground as measured in the game (27, 22, 23, its grain a couple of levels deep)."""
    noise = Image.effect_noise((W, h), 3).filter(ImageFilter.GaussianBlur(0.6))
    base = Image.new('RGB', (W, h), (27, 22, 23))
    return ImageChops.add(base, Image.merge('RGB', [noise.point(lambda v: max(0, v - 126))] * 3))


def glow(layer, xy, r, colour, strength):
    """An additive soft light."""
    g = Image.new('RGB', layer.size, (0, 0, 0))
    d = ImageDraw.Draw(g)
    x, y = xy
    d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=tuple(int(c * strength) for c in colour))
    g = g.filter(ImageFilter.GaussianBlur(r * 0.45))
    return ImageChops.add(layer, g)


def coal(im, cx, cy, s, seed, heat=1.0):
    """A live coal: a rough dark lump, its cracks and heart glowing."""
    rnd = random.Random(seed)
    im2 = glow(im, (cx, cy), s * 2.2, EMBER, 0.35 * heat)
    d = ImageDraw.Draw(im2)
    pts = []
    for k in range(9):
        a = k / 9 * math.tau
        rr = s * (0.82 + 0.3 * rnd.random())
        pts.append((cx + math.cos(a) * rr * 1.15, cy + math.sin(a) * rr * 0.8))
    d.polygon(pts, fill=(38, 20, 16))
    # the heart showing through the crust
    hot = Image.new('L', im2.size, 0)
    hd = ImageDraw.Draw(hot)
    for k in range(4):
        a = rnd.random() * math.tau
        x0, y0 = cx + math.cos(a) * s * 0.25, cy + math.sin(a) * s * 0.2
        x1, y1 = cx + math.cos(a + 2.2) * s * 0.7, cy + math.sin(a + 2.2) * s * 0.45
        hd.line((x0, y0, x1, y1), fill=255, width=max(1, int(s * 0.16)))
    hd.ellipse((cx - s * 0.35, cy - s * 0.25, cx + s * 0.35, cy + s * 0.25), fill=200)
    hot = hot.filter(ImageFilter.GaussianBlur(1.2))
    mask = Image.new('L', im2.size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    hot = ImageChops.multiply(hot, mask)
    col = Image.new('RGB', im2.size, tuple(int(c * heat) for c in (255, 150, 60)))
    im2.paste(col, (0, 0), hot)
    core = hot.point(lambda v: max(0, v - 150) * 2)
    im2.paste(Image.new('RGB', im2.size, EMBER_HI), (0, 0), core)
    return im2


def dish(im, cx, cy, coals):
    """A small iron dish seen from above and a little in front, its coals in it."""
    d = ImageDraw.Draw(im)
    rx, ry = 34, 13
    d.ellipse((cx - rx - 2, cy - ry + 3, cx + rx + 2, cy + ry + 7), fill=(10, 8, 9))       # its shadow
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(58, 54, 56))                   # the rim
    d.ellipse((cx - rx + 4, cy - ry + 3, cx + rx - 4, cy + ry - 2), fill=(22, 19, 20))    # the bowl
    d.arc((cx - rx, cy - ry, cx + rx, cy + ry), 200, 340, fill=(120, 112, 104), width=1)  # light on the far rim
    for i, (ox, oy) in enumerate(coals):
        im = coal(im, cx + ox, cy + oy, 7.5, 11 + i)
    # the near rim over the coals' feet
    d = ImageDraw.Draw(im)
    d.arc((cx - rx, cy - ry, cx + rx, cy + ry), 15, 165, fill=(74, 68, 70), width=3)
    return im


def text(d, xy, s, face, size, fill, anchor='ls'):
    d.text(xy, s, font=font(face, size), fill=fill, anchor=anchor)
    return d.textlength(s, font=font(face, size))


def numeral_glow(im, xy, s, size):
    """The numeral of an attribute a coal was sent to: lit from within, as iron in the fire."""
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).text(xy, s, font=font(DISPLAY, size), fill=255, anchor='ls')
    halo = m.filter(ImageFilter.GaussianBlur(7))
    im = Image.composite(Image.new('RGB', im.size, EMBER), im, halo.point(lambda v: int(v * 0.55)))
    im.paste(Image.new('RGB', im.size, (255, 196, 120)), (0, 0), m)
    return im


def line(shots, state):
    im = ground(shots, 150)
    d = ImageDraw.Draw(im)
    X, Wd = 32, W - 64
    # the head: its name, a note, a rule running on to what is spent
    y = 34
    tw = text(d, (X, y), 'ATTRIBUTES', UI_H, 14, HEAD)
    nw = text(d, (X + tw + 10, y), 'hover: what a point gives', TEXT_I, 15, DIM)
    end = X + Wd
    if state == 'spend':
        rx = end
        rx -= text(d, (rx, y), 'KEEP', UI_H, 14, EMBER, anchor='rs') + 22
        rx -= text(d, (rx, y), 'UNDO', UI_H, 14, DIM, anchor='rs') + 22
        rx -= text(d, (rx, y), '1 of 2 spent', TEXT_I, 15, EMBER, anchor='rs') + 14
        end = rx
    d.line((X + tw + 10 + nw + 12, y - 5, end, y - 5), fill=RULE)
    # the line itself: four attributes as type on a shared baseline, fine rules between, the dish at its end
    base = 98
    attrs = [('6', 'MIGHT'), ('3', 'FINESSE'), ('3', 'WITS'), ('6', 'RESOLVE')]
    dish_w = 110
    col = (Wd - dish_w) / 4
    for i, (n, name) in enumerate(attrs):
        x = X + i * col
        if i > 0:
            for yy in range(base - 40, base + 4):
                a = 1 - abs(yy - (base - 18)) / 24
                d.point((x - 14, yy), fill=tuple(int(RULE[j] * a + 30 * (1 - a)) for j in range(3)))
        spent = state == 'spend' and i == 0
        num = '7' if spent else n
        if spent:
            im = numeral_glow(im, (x, base), num, 44)
            d = ImageDraw.Draw(im)
            nw2 = d.textlength(num, font=font(DISPLAY, 44))
            # the coal it took lies at the numeral's foot
            im = coal(im, x + nw2 + 9, base - 6, 6.5, 3)
            d = ImageDraw.Draw(im)
            text(d, (x + nw2 + 24, base), name, DISPLAY_L, 17, (232, 196, 150))
        else:
            nw2 = text(d, (x, base), num, DISPLAY, 44, INK)
            text(d, (x + nw2 + 12, base), name, DISPLAY_L, 17, HEAD)
    # the dish at the line's end: as many live coals as points to spend
    coals = [(-9, -1), (9, 1)] if state == 'rest' else [(2, 0)]
    im = dish(im, X + Wd - 48, base - 14, coals)
    d = ImageDraw.Draw(im)
    text(d, (X + Wd - 48, base + 22), '2 to spend' if state == 'rest' else '1 left', UI_B, 13, DIM, anchor='ms')
    return im


def hover(shots):
    """At rest, Might hovered: what a point gives, beside it on the world's side (a world crop)."""
    im = line(shots, 'rest')
    return im


if __name__ == '__main__':
    shots, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    rest, spend = line(shots, 'rest'), line(shots, 'spend')
    rest.save(os.path.join(out, 'attr_ledger_rest.png'))
    spend.save(os.path.join(out, 'attr_ledger_spend.png'))
    both = Image.new('RGB', (W, 330), (8, 7, 8))
    both.paste(rest, (0, 0))
    both.paste(spend, (0, 170))
    d = ImageDraw.Draw(both)
    d.text((8, 152), 'at rest: two points to spend, two coals in the dish', font=font(UI_B, 13), fill=(120, 116, 110))
    both.save(os.path.join(out, 'attr_ledger_both.png'))
    print('drew the ledger line')
