"""The medallion ring as Ornate.Medallion draws it, at several sizes, over a plate-coloured
ground: core (lit upper left), hairline in the ring colour at 76%, the ring art, a progress
arc at 88%, and a number."""
import sys
from sp import *
from PIL import ImageFont

src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "relief", "medal_ring_file.png")
ring = Image.open(src).convert("RGBA")
font_path = r"C:\Windows\Fonts\georgiab.ttf"
K = 4  # supersample


def medal(size, text="", ring_col=(201, 162, 86), core=(58, 34, 16), arc=0.0, arc_col=(255, 138, 42)):
    s = size * K
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    r = s / 2 - 3 * K
    def circ(cx, cy, rr, fill):
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=fill)
    circ(c, c + 3 * K, r + 2 * K, (0, 0, 0, 128))
    circ(c, c, r + K, (6, 5, 8, 255))
    dk = tuple(int(v * 0.65) for v in core)
    circ(c, c, r - 4 * K, dk + (255,))
    circ(c - r * 0.15, c - r * 0.15, r * 0.72, core + (255,))
    rr = r * 0.76
    d.ellipse((c - rr, c - rr, c + rr, c + rr), outline=ring_col + (204,), width=2 * K)
    rg = ring.resize((s, s), Image.LANCZOS)
    im.alpha_composite(rg)
    if arc > 0:
        ra = r * 0.88
        d2 = ImageDraw.Draw(im)
        d2.arc((c - ra, c - ra, c + ra, c + ra), -90, -90 + 360 * arc, fill=arc_col + (255,), width=4 * K)
    if text:
        fs = int(size * (0.32 if len(text) > 2 else 0.44)) * K
        f = ImageFont.truetype(font_path, fs)
        d3 = ImageDraw.Draw(im)
        d3.text((c + K, c + K), text, font=f, fill=(0, 0, 0, 204), anchor="mm")
        d3.text((c, c), text, font=f, fill=(255, 216, 140, 255), anchor="mm")
    return im.resize((size, size), Image.LANCZOS)


ground = (22, 19, 26)
items = [
    medal(44, "II"), medal(54, "", ring_col=(204, 136, 255), core=(40, 20, 56)),
    medal(64, "7", arc=0.6), medal(76, "12", ring_col=(134, 176, 216), core=(28, 42, 58), arc=0.45, arc_col=(134, 176, 216)),
    medal(120, "14"), medal(160, "", ring_col=(255, 138, 74), core=(60, 24, 10), arc=0.3), medal(220, "5", arc=0.75),
]
w = sum(i.width for i in items) + 10 * (len(items) + 1)
h = max(i.height for i in items) + 20
out = Image.new("RGBA", (w, h), ground + (255,))
x = 10
for i in items:
    out.alpha_composite(i, (x, (h - i.height) // 2))
    x += i.width + 10
out.convert("RGB").save(os.path.join(V, "ring_look.png"))
zoom(out.crop((0, 0, 10 + 44 + 10 + 54 + 10 + 64 + 10 + 76 + 10, h)).convert("RGB"), 3).save(os.path.join(V, "ring_look_small_z3.png"))
