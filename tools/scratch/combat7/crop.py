"""Crop a frame: python crop.py OUT NAME X0 Y0 X1 Y1 [SCALE] (NAME in .shots, .png optional)."""
import sys, os
from PIL import Image

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\.shots"
HERE = os.path.dirname(os.path.abspath(__file__))
out, name = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 1
im = Image.open(os.path.join(SHOTS, name if name.endswith(".png") else name + ".png")).crop((x0, y0, x1, y1))
if scale != 1:
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
im.save(os.path.join(HERE, out))
print(out, im.size)
