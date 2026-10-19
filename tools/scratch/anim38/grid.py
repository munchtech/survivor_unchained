# grid.py DIR LIST OUT: 6-column contact grid of the shot list, 480x270 tiles, labelled (a working look only, not for judges).
import sys, os
from PIL import Image, ImageDraw
d, lst, out = sys.argv[1:4]
names = [l.split('|')[0] for l in open(lst) if l.strip() and not l.startswith('#')]
C, W, H, L = 6, 480, 270, 16
R = (len(names)+C-1)//C
g = Image.new('RGB', (C*W, R*(H+L)), (20,20,20)); dr = ImageDraw.Draw(g)
for k, n in enumerate(names):
    x, y = (k % C)*W, (k//C)*(H+L)
    p = os.path.join(d, n+'.png')
    if os.path.exists(p): g.paste(Image.open(p).convert('RGB').resize((W, H)), (x, y+L))
    dr.text((x+3, y+2), n if os.path.exists(p) else n+' MISSING', fill=(230,230,230))
g.save(out, quality=85); print(out, g.size)
