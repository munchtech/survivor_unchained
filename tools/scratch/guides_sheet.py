"""Guides for the named keys (remade), with the old icon beside each, at 160 px."""
import os
import sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
import emblems  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SCR = os.path.dirname(os.path.abspath(__file__))
keys = sys.argv[2:] or list(emblems.DESIGNS)
s = 160
cols = 6
rows = (len(keys) + cols - 1) // cols
img = Image.new("RGB", (cols * (2 * s + 70 + 16), rows * (s + 18)), (8, 8, 8))
d = ImageDraw.Draw(img)
for i, k in enumerate(keys):
    if sys.argv[1] == "1":
        emblems.make_guide(k)
    g = Image.open(os.path.join(emblems.RAW, f"{k}_guide.png")).convert("RGB").resize((s, s), Image.LANCZOS)
    x, y = (i % cols) * (2 * s + 70 + 16), (i // cols) * (s + 18)
    img.paste(g, (x, y))
    old = os.path.join(emblems.UI, k + ".png")
    if os.path.exists(old):
        o = Image.open(old).convert("RGBA").resize((s, s), Image.LANCZOS)
        b = Image.new("RGBA", (s, s), (20, 16, 12, 255))
        b.alpha_composite(o)
        img.paste(b.convert("RGB"), (x + s + 4, y))
        o44 = Image.open(old).convert("RGBA").resize((44, 44), Image.LANCZOS)
        b = Image.new("RGBA", (44, 44), (20, 16, 12, 255))
        b.alpha_composite(o44)
        img.paste(b.convert("RGB"), (x + 2 * s + 8, y))
    d.text((x + 2, y + s + 2), k, fill=(255, 220, 160))
out = os.path.join(SCR, "guides.png")
img.save(out)
print(out)
