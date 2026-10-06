"""Game shots tiled: shots.py <prefix> <out.png> [cols] [crop w h] [scale]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

pre, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
cw, ch = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (640, 480)
sc = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
d = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\godot\.shots')
files = sorted(d.glob(f'{pre}_*.png'))
ims = []
for f in files:
    im = Image.open(f)
    W, H = im.size
    box = ((W - cw) // 2, (H - ch) // 2, (W + cw) // 2, (H + ch) // 2)
    im = im.crop(box).resize((int(cw * sc), int(ch * sc)))
    ImageDraw.Draw(im).text((4, 4), f.stem.split('_')[-1], fill=(255, 255, 0))
    ims.append(im)
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
b = Image.new('RGB', (w * cols, h * rows))
for i, im in enumerate(ims):
    b.paste(im, ((i % cols) * w, (i // cols) * h))
b.save(out)
print(out, b.size, len(ims))
