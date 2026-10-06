"""Every painting of a key fitted and shown at the HUD's sizes on the medallion's dark disc:
at_size.py KEY PATTERN"""
import glob
import os
import sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
import emblems  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SCR = os.path.dirname(os.path.abspath(__file__))
key, pat = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(emblems.RAW, pat)))
tiles = []
for f in files:
    dst = os.path.join(SCR, "fit", os.path.basename(f))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    emblems.fit(key, f, dst)
    tiles.append((os.path.basename(f), Image.open(dst).convert("RGBA")))
W = len(tiles) * 160
img = Image.new("RGB", (W, 190), (12, 10, 8))
d = ImageDraw.Draw(img)
for i, (n, t) in enumerate(tiles):
    x = i * 160
    d.ellipse((x + 4, 4, x + 104, 104), fill=(52, 30, 18))
    disc = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    disc.alpha_composite(t.resize((80, 80), Image.LANCZOS), (10, 10))
    img.paste(disc.convert("RGB"), (x + 4, 4), disc)
    d.rectangle((x + 112, 60, x + 156, 104), fill=(30, 26, 24))
    img.paste(t.resize((40, 40), Image.LANCZOS), (x + 114, 62), t.resize((40, 40), Image.LANCZOS))
    d.text((x + 2, 150), n.replace("em_" + key + "_", "")[:22], fill=(220, 200, 160))
out = os.path.join(SCR, f"size_{key}.png")
img.save(out)
print(out)
