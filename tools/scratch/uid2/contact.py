import sys, os, math
from PIL import Image, ImageDraw
d = sys.argv[1]
fs = sorted(f for f in os.listdir(d) if f.endswith('.png') and not f.startswith('_'))
ims = [Image.open(os.path.join(d, f)).convert('RGB') for f in fs]
if not ims:
    sys.exit()
w = int(sys.argv[2]) if len(sys.argv) > 2 else 420
cols = min(len(ims), 5)
rows = math.ceil(len(ims) / cols)
h = int(w * ims[0].height / ims[0].width)
sheet = Image.new('RGB', (cols * w, rows * (h + 24)), (20, 20, 20))
dr = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * (h + 24)
    sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y + 24))
    dr.text((x + 6, y + 6), f[:-4], fill=(230, 220, 200))
sheet.save(os.path.join(d, '_sheet.jpg'), quality=90)
print('sheet', sheet.size)
