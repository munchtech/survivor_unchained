import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abfa9bb430ec2391e\tools\assets")
import face_fit as ff

img, x0 = ff.load(sys.argv[1], sys.argv[2])
Q = ff.detect(img)
im = Image.fromarray(img).convert("RGB")
d = ImageDraw.Draw(im)
for k in (1, 33, 263, 61, 291, 152, 234, 454, 10):
    x, y = Q[k, :2]
    d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 0, 0))
    d.text((x + 6, y - 6), str(k), fill=(255, 255, 0))
    print(k, np.round(Q[k], 1))
im.save(sys.argv[3])
