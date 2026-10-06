"""One frame of each run, side by side, for triage: python pick.py OUT COLS WIDTH FRAME run1 run2 ...

Each tile is the middle 1200x700 of `run_FRAME.png` (or the run's brightest-changing frame when
FRAME is 'max': the one furthest from the run's mean), scaled to WIDTH, labelled with the run."""
import sys
import numpy as np
from PIL import Image, ImageDraw
from shots import shot, run

out, cols, width, which = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
tiles = []
for name in sys.argv[5:]:
    if which == "max":
        frames = run(name)
        if not frames:
            continue
        arrs = [np.asarray(Image.open(f).convert("L").resize((240, 135))).astype(np.float32) for f in frames]
        mean = np.mean(arrs, axis=0)
        k = int(np.argmax([np.abs(a - mean).sum() for a in arrs]))
        path = frames[k]
    else:
        path = shot(f"{name}_{which}.png")
    im = Image.open(path).convert("RGB").crop((360, 190, 1560, 890))
    im = im.resize((width, int(width * 700 / 1200)))
    ImageDraw.Draw(im).text((4, 2), name.split("_", 1)[1], fill=(255, 255, 0))
    tiles.append(im)
rows = (len(tiles) + cols - 1) // cols
h = tiles[0].height
sheet = Image.new("RGB", (cols * width + (cols - 1) * 3, rows * h + (rows - 1) * 3), (10, 10, 10))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * (width + 3), (i // cols) * (h + 3)))
sheet.save(out)
print(out, sheet.size)
