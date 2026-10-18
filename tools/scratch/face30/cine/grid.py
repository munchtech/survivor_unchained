"""python grid.py FILE.png OUTNAME [scale]: a copy with a 100-px grid labelled in full-res pixels"""
import sys
from PIL import Image, ImageDraw
OUT = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\463a4243-9324-49b0-bda9-b9fb9a9d68b1\scratchpad\f30" + "\\"
im = Image.open(sys.argv[1]).convert('RGB'); s = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
d = ImageDraw.Draw(im)
for x in range(0, im.width, 100): d.line([(x, 0), (x, im.height)], fill=(0, 255, 0) if x % 500 else (255, 0, 255)); d.text((x + 2, 2), str(x), fill=(0, 255, 0))
for y in range(0, im.height, 100): d.line([(0, y), (im.width, y)], fill=(0, 255, 0) if y % 500 else (255, 0, 255)); d.text((2, y + 2), str(y), fill=(0, 255, 0))
im.resize((int(im.width * s), int(im.height * s))).save(OUT + sys.argv[2] + '.jpg', quality=85)
