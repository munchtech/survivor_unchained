import sys
import numpy as np
from PIL import Image
# uvover.py PAINT OUT [x0 y0 x1 y1]: a paint (her UV layout) over her head's paint, cropped.
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a69858664f1d3dd29\godot\art\people'
head = np.asarray(Image.open(W + r'\head_tex\heroine_head.jpg').convert('RGB').resize((2048, 2048)), np.float32) / 255
p = np.asarray(Image.open(W + '\\paint\\' + sys.argv[1] + '.png').convert('RGBA'), np.float32) / 255
a = p[..., 3:4]
out = head * (1 - a) + p[..., :3] * a
img = Image.fromarray((out * 255).astype(np.uint8))
if len(sys.argv) > 3:
    img = img.crop(tuple(int(v) for v in sys.argv[3:7]))
img.save(sys.argv[2], quality=92)
