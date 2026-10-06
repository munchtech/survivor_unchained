import sys
from sp import *
from PIL import ImageFont
sys.path.insert(0, os.path.join(W, "tools", "uiforge"))
import svgglyph as G
import numpy as np
keys = sorted(G.glyphs())
cols = 15
cw, ch = 74, 80
out = Image.new("RGB", (cols * cw, ((len(keys) + cols - 1) // cols) * ch), (24, 20, 20))
d = ImageDraw.Draw(out)
font = ImageFont.truetype("arial.ttf", 10)
for i, k in enumerate(keys):
    body, cut = G.bold(k, 56, stroke=2.3)
    m = np.clip(body - cut, 0, 1)
    im = Image.fromarray((m * 230).astype(np.uint8))
    x, y = (i % cols) * cw + 8, (i // cols) * ch + 2
    out.paste(Image.new("RGB", (56, 56), (230, 220, 200)), (x, y), im)
    d.text((x, y + 60), k, fill=(200, 190, 170), font=font)
out.save(os.path.join(V, "glyphs_bold.png"))
