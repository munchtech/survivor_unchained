"""Crop a shot: python crop.py NAME x0,y0,x1,y1 OUT [scale]"""
import sys
from PIL import Image

S = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa1f430bd64b8d1ce\godot\.shots'
name, box, out = sys.argv[1], tuple(int(v) for v in sys.argv[2].split(',')), sys.argv[3]
k = float(sys.argv[4]) if len(sys.argv) > 4 else 1
im = Image.open(f'{S}\\{name}.png').convert('RGB').crop(box)
if k != 1:
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
im.save(out)
