"""plot_profile.py OUT.png A_profile.json [B_profile.json ...]: lips' mid-line profiles (y forward-negative, z up, mm),
dots on a millimetre grid, each file its own colour."""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
cols = [(220, 60, 60), (60, 140, 230), (60, 180, 90), (200, 160, 40)]
S = 24  # px per mm
data = [np.array(json.load(open(p))['profile_yz_mm']) for p in sys.argv[2:]]
allp = np.vstack(data)
y0, y1 = allp[:, 0].min() - 2, allp[:, 0].max() + 2
z0, z1 = allp[:, 1].min() - 2, allp[:, 1].max() + 2
W, H = int((y1 - y0) * S), int((z1 - z0) * S)
im = Image.new('RGB', (W, H), (250, 250, 250))
d = ImageDraw.Draw(im)
for g in np.arange(np.floor(y0), y1, 1):
    x = (g - y0) * S
    d.line([(x, 0), (x, H)], fill=(225, 225, 225) if g % 5 else (180, 180, 180))
for g in np.arange(np.floor(z0), z1, 1):
    y = H - (g - z0) * S
    d.line([(0, y), (W, y)], fill=(225, 225, 225) if g % 5 else (180, 180, 180))
for k, P in enumerate(data):
    for yy, zz in P:
        x, y = (yy - y0) * S, H - (zz - z0) * S
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=cols[k % 4])
im.save(sys.argv[1])
print(sys.argv[1], im.size, 'y %.1f..%.1f z %.1f..%.1f' % (y0, y1, z0, z1))
