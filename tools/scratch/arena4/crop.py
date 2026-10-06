"""Crop a frame: python crop.py NAME x0 y0 x1 y1 [scale] -> scratchpad/arena2/crops/NAME_x0_y0.png"""
import sys, os
from PIL import Image
SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0b61c278bdd5c994\godot\.shots"
HERE = os.path.dirname(os.path.abspath(__file__))
n = sys.argv[1]
x0, y0, x1, y1 = map(int, sys.argv[2:6])
sc = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
p = n if os.path.exists(n) else os.path.join(SHOTS, n + ".png")
im = Image.open(p).convert("RGB").crop((x0, y0, x1, y1))
if sc != 1.0:
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
os.makedirs(os.path.join(HERE, "crops"), exist_ok=True)
out = os.path.join(HERE, "crops", f"{os.path.splitext(os.path.basename(n))[0]}_{x0}_{y0}.png")
im.save(out)
print(out)
