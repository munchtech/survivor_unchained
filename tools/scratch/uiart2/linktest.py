import math
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge")
import valueglyphs as V  # noqa: E402

S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uiart2"


def variant(S_, cA, cB, st, R, bar, g, ang=45, pad=1.2):
    scale = S_ / (24 + 2 * pad)
    yy, xx = np.mgrid[0:S_, 0:S_].astype(np.float32)
    X, Y = (xx + 0.5) / scale - pad, (yy + 0.5) / scale - pad
    a = math.radians(ang)
    u = (math.cos(a), -math.sin(a))

    def cov(d):
        return np.clip(0.5 - d * scale, 0, 1)
    dA, _, _ = V._link_sd(X, Y, cA, u, st, R)
    dB, _, _ = V._link_sd(X, Y, cB, u, st, R)
    ringA, ringB = cov(np.abs(dA) - bar), cov(np.abs(dB) - bar)
    fill = np.maximum(ringA, ringB)
    side = -(X - 12) * u[1] + (Y - 12) * u[0]
    cut = np.maximum(np.clip(cov(np.abs(dB) - bar - g) - ringB, 0, 1) * ringA * (side < 0),
                     np.clip(cov(np.abs(dA) - bar - g) - ringA, 0, 1) * ringB * (side > 0))
    return np.clip(fill - cut, 0, 1)


vs = [
    ("a", dict(cA=(8.6, 15.4), cB=(15.4, 8.6), st=2.4, R=3.6, bar=1.45, g=0.85)),
    ("b", dict(cA=(8.0, 16.0), cB=(16.0, 8.0), st=2.0, R=3.9, bar=1.9, g=1.1)),
    ("c", dict(cA=(7.6, 16.4), cB=(16.4, 7.6), st=1.6, R=4.2, bar=2.0, g=1.2)),
    ("d_h", dict(cA=(7.0, 12.0), cB=(17.0, 12.0), st=1.4, R=4.4, bar=2.0, g=1.2, ang=0)),
]
row = []
for name, kw in vs:
    tiles = []
    for px in (14, 24, 64):
        m = variant(px * 4, **kw)
        small = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((px, px), Image.LANCZOS)).astype(np.float32) / 255
        col = np.array([0x3f, 0xd6, 0xc0], np.float32) / 255
        bg = np.ones((px, px, 3), np.float32) * np.array([0.12, 0.10, 0.11])
        img = bg * (1 - small[..., None]) + col * small[..., None]
        big = Image.fromarray((img * 255).astype(np.uint8)).resize((px * (8 if px < 64 else 2), px * (8 if px < 64 else 2)), Image.NEAREST)
        tiles.append(big)
    h = max(t.height for t in tiles)
    strip = Image.new("RGB", (sum(t.width for t in tiles) + 40, h + 10), (40, 40, 40))
    x = 5
    for t in tiles:
        strip.paste(t, (x, 5))
        x += t.width + 15
    row.append(strip)
W = max(r.width for r in row)
out = Image.new("RGB", (W, sum(r.height for r in row)), (40, 40, 40))
y = 0
for r in row:
    out.paste(r, (0, y))
    y += r.height
out.save(S + r"\linktest.png")
print(out.size)
