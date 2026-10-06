"""The health globe as Ornate.Globe draws it (144 shown, liquid radius 66) with the rim and
glass art, at a few levels, over the night HUD; and big."""
import sys
import numpy as np
from sp import *
from PIL import ImageFont

rim_p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "relief", "globe_rim_file.png")
glass_p = sys.argv[2] if len(sys.argv) > 2 else ""
rim = Image.open(rim_p).convert("RGBA")
glass = Image.open(glass_p).convert("RGBA") if glass_p and os.path.exists(glass_p) else None
K = 4


def globe(level, number="153", scale=1):
    S = 144 * K * scale
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    r = 66 * K * scale
    def circ(cx, cy, rr, fill):
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=fill)
    circ(c, c + 4 * K * scale, r + 6 * K * scale, (0, 0, 0, 140))
    circ(c, c, r + 5 * K * scale, (6, 5, 8, 255))
    circ(c, c, r, (20, 6, 8, 255))
    # Liquid below the level, darker toward the foot.
    y = c + r - 2 * r * level
    liq = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    yy = np.arange(S)[:, None] * np.ones((1, S))
    t = np.clip((yy - (c - r)) / (2 * r), 0, 1)
    col = np.array([200, 38, 44], np.float32)
    rgb = col[None, None, :] * (1 - 0.55 * t[..., None])
    xx = np.arange(S)[None, :] * np.ones((S, 1))
    inside = (np.hypot(xx - c, yy - c) < r) & (yy > y)
    a = inside.astype(np.uint8) * 255
    liq = Image.fromarray(np.dstack([rgb.astype(np.uint8), a]), "RGBA")
    im.alpha_composite(liq)
    if glass is not None:
        im.alpha_composite(glass.resize((S, S), Image.LANCZOS))
    im.alpha_composite(rim.resize((S, S), Image.LANCZOS))
    if number:
        f = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", int(r * 0.36))
        d2 = ImageDraw.Draw(im)
        d2.text((c + K, c + 2 * K), number, font=f, fill=(0, 0, 0, 230), anchor="mm")
        d2.text((c, c), number, font=f, fill=(255, 244, 234, 255), anchor="mm")
    return im.resize((144 * scale, 144 * scale), Image.LANCZOS)


ground = Image.open(os.path.join(W, "godot", ".shots", "m1_hud_night.png")).convert("RGBA").crop((430, 880, 1000, 1080))
for i, lv in enumerate((1.0, 0.55, 0.2)):
    ground.alpha_composite(globe(lv), (10 + i * 180, 40))
big = globe(0.6, scale=3)
canvas = Image.new("RGB", (big.width + 20 + ground.width, max(big.height, ground.height)), (28, 24, 22))
canvas.paste(on_bg(big), (0, 0))
canvas.paste(ground.convert("RGB"), (big.width + 20, 0))
canvas.save(os.path.join(V, "globe_look.png"))
