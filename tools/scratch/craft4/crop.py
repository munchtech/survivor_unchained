"""crop.py SHOT x0 y0 x1 y1 OUT [scale]: a region of a frame in godot/.shots, for a close look.
SHOT may be a list joined by '+': the crops are laid side by side (a strip of moments)."""
import sys
from PIL import Image
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\godot\.shots"
names, (x0, y0, x1, y1), out = sys.argv[1].split("+"), map(int, sys.argv[2:6]), sys.argv[6]
sc = float(sys.argv[7]) if len(sys.argv) > 7 else 1
ims = [Image.open(f"{S}\\{n}.png").crop((x0, y0, x1, y1)) for n in names]
if sc != 1: ims = [im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS) for im in ims]
w = sum(im.width for im in ims) + 6 * (len(ims) - 1)
strip = Image.new("RGB", (w, ims[0].height), (255, 0, 255))
x = 0
for im in ims:
    strip.paste(im, (x, 0)); x += im.width + 6
strip.save(out)
