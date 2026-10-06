import sys
from PIL import Image
# c1.py IN x0 y0 x1 y1 OUT [scale]: one region of a picture, at full size (or scaled).
# IN may be a bare name: then it is the worktree's godot/.shots/NAME.png; OUT lands in uid3.
SH = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a69858664f1d3dd29\godot\.shots'
D = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3'
src = sys.argv[1] if ('\\' in sys.argv[1] or '/' in sys.argv[1]) else SH + '\\' + sys.argv[1] + '.png'
im = Image.open(src).convert('RGB').crop(tuple(int(v) for v in sys.argv[2:6]))
if len(sys.argv) > 7:
    s = float(sys.argv[7]); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
out = sys.argv[6] if ('\\' in sys.argv[6] or '/' in sys.argv[6]) else D + '\\' + sys.argv[6]
im.save(out, quality=92)
print(out)
