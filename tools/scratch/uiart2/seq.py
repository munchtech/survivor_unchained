"""Consecutive frames at an eyelet, zoomed, to check the threading for pops (60 fps)."""
import os
import sys

from PIL import Image, ImageDraw

D = sys.argv[5] if len(sys.argv) > 5 else r'C:SERSMUNCHDESKTOPSURVIVORSUNCHAINED.CLAUDEWORKTREESGENT-A0BFF3FFE4D3AD748	OOLSMFYOUTIFORGEAINIDEO'
S = os.path.dirname(os.path.abspath(__file__))
x0, x1 = int(sys.argv[1]), int(sys.argv[2])
first, n = int(sys.argv[3]), int(sys.argv[4])
z = 4
tiles = []
for i in range(first, first + n):
    im = Image.open(os.path.join(D, (f'f{i:03d}.png' if len(sys.argv) > 5 else f'f{i:04d}.png'))).convert('RGB').crop((x0, 36, x1, 82))
    im = im.resize((im.width * z, im.height * z), Image.NEAREST)
    ImageDraw.Draw(im).text((4, 2), str(i), fill=(255, 255, 0))
    tiles.append(im)
cols = 4
W, H = tiles[0].size
out = Image.new('RGB', (cols * (W + 4), ((len(tiles) + cols - 1) // cols) * (H + 4)))
for j, t in enumerate(tiles):
    out.paste(t, ((j % cols) * (W + 4), (j // cols) * (H + 4)))
out.save(os.path.join(S, 'seq.png'))
print(out.size)
