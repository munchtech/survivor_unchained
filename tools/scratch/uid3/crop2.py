import sys, os, math, re
from PIL import Image, ImageDraw
# crop2.py DIR OUT x0 y0 x1 y1 width cols PATTERN: the region of the pictures whose names match, side by side.
d, outname = sys.argv[1], sys.argv[2]
box = tuple(int(v) for v in sys.argv[3:7])
w, cols = int(sys.argv[7]), int(sys.argv[8])
pat = re.compile(sys.argv[9]) if len(sys.argv) > 9 else re.compile('.')
order = {'m1': 0, 'm0p5': 1, '0p5': 2, '1': 3}
def key(f):
    m = re.match(r'(.*)_(m?[0-9p]+)\.png$', f)
    return (m.group(1), order.get(m.group(2), 9)) if m else (f, 0)
fs = sorted((f for f in os.listdir(d) if f.endswith('.png') and not f.startswith('_') and pat.search(f)), key=key)
ims = [Image.open(os.path.join(d, f)).convert('RGB').crop(box) for f in fs]
h = int(w * ims[0].height / ims[0].width)
rows = math.ceil(len(ims) / cols)
sheet = Image.new('RGB', (cols * w, rows * (h + 20)), (20, 20, 20))
dr = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * (h + 20)
    sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y + 20))
    dr.text((x + 6, y + 4), f[:-4], fill=(230, 220, 200))
sheet.save(os.path.join(d, outname), quality=92)
print(outname, sheet.size)
