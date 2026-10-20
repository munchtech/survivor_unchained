"""Working-look sheet: crop each named frame around her and tile. sheet.py OUT.jpg SCALE BOX file1.png file2.png ...
BOX = x0,y0,x1,y1 crop in the 1920x1080 frame."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, scale, box = sys.argv[1], float(sys.argv[2]), tuple(int(v) for v in sys.argv[3].split(','))
files = sys.argv[4:]
cw, ch = round((box[2]-box[0])*scale), round((box[3]-box[1])*scale)
cols = min(len(files), 4); rows = (len(files)+cols-1)//cols
sheet = Image.new('RGB', (cw*cols, ch*rows))
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').crop(box).resize((cw, ch), Image.LANCZOS)
    d = ImageDraw.Draw(im); d.text((4, 2), Path(f).stem, fill=(255, 255, 0))
    sheet.paste(im, ((i % cols)*cw, (i//cols)*ch))
sheet.save(out, quality=88); print(out, sheet.size)
