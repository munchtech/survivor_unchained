"""Images in a row at one height, aspect kept: row.py OUT HEIGHT file..."""
import sys

from PIL import Image

out, h = sys.argv[1], int(sys.argv[2])
ims = []
for f in sys.argv[3:]:
    im = Image.open(f).convert("RGBA")
    ims.append(im.resize((int(im.width * h / im.height), h), Image.LANCZOS))
W = sum(i.width for i in ims) + 8 * len(ims)
img = Image.new("RGBA", (W, h), (24, 20, 16, 255))
x = 0
for i in ims:
    img.alpha_composite(i, (x, 0))
    x += i.width + 8
img.convert("RGB").save(out)
print(out)
