"""sheet.py OUT SIZE IMG...: the images side by side at SIZE px square, for one look."""
import sys
from PIL import Image
out, size, paths = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
def flat(p):
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGBA", im.size, (20, 17, 24, 255))
    bg.alpha_composite(im)
    return bg.convert("RGB")
ims = [flat(p).resize((size, size)) for p in paths]
s = Image.new("RGB", (len(ims) * (size + 2) - 2, size), (255, 0, 255))
for i, im in enumerate(ims):
    s.paste(im, (i * (size + 2), 0))
s.save(out)
