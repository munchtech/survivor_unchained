"""Contact sheets of the motion frames: one sheet per outfit and view, frames in a 4 x 2 grid.
    python sheet.py <folder> [scale]"""
import glob
import os
import sys

from PIL import Image

folder = sys.argv[1]
scale = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
groups = {}
for f in sorted(glob.glob(os.path.join(folder, '*_[0-9][0-9].png'))):
    groups.setdefault(os.path.basename(f)[:-7], []).append(f)
for name, files in groups.items():
    ims = [Image.open(f).convert('RGB') for f in files[:8]]
    w, h = int(ims[0].width * scale), int(ims[0].height * scale)
    sheet = Image.new('RGB', (w * 4, h * 2), (0, 0, 0))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((w, h)), ((i % 4) * w, (i // 4) * h))
    out = os.path.join(folder, 'sheet_' + name + '.jpg')
    sheet.save(out, quality=88)
    print(out, len(ims))
