import sys, os, math
from PIL import Image, ImageDraw
# crop.py DIR x0 y0 x1 y1 [width] [cols]: the same region of every picture, side by side.
d = sys.argv[1]
box = tuple(int(v) for v in sys.argv[2:6])
w = int(sys.argv[6]) if len(sys.argv) > 6 else 600
cols = int(sys.argv[7]) if len(sys.argv) > 7 else 3
fs = sorted(f for f in os.listdir(d) if f.endswith('.png') and not f.startswith('_'))
ims = [Image.open(os.path.join(d, f)).convert('RGB').crop(box) for f in fs]
h = int(w * ims[0].height / ims[0].width)
rows = math.ceil(len(ims) / cols)
sheet = Image.new('RGB', (cols * w, rows * (h + 22)), (20, 20, 20))
dr = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * (h + 22)
    sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y + 22))
    dr.text((x + 6, y + 5), f[:-4], fill=(230, 220, 200))
sheet.save(os.path.join(d, '_crop.jpg'), quality=92)
print('crop', sheet.size)
