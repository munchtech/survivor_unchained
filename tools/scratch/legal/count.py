"""Counts the legal check's marks in each motion frame (MARKS=1 renders). Marks are unlit cyan:
bright for the areolas (value 160-200 after the tonemapper), dim for the genital area
(100-140), calibrated on 4 Oct 2026; no outfit has cyan (253 unmarked frames, none over 5 px).
A frame with MIN or more pixels of either is flagged, and a crop round the marks is saved as
flag_<frame>.png for a look.
    python count.py <folder> [MIN=6] [only-prefix]"""
import glob
import os
import sys

import numpy as np
from PIL import Image

folder = sys.argv[1]
least = int(sys.argv[2]) if len(sys.argv) > 2 else 6
only = sys.argv[3] if len(sys.argv) > 3 else ''
SPLIT = 150

rows, flagged = [], []
for f in sorted(glob.glob(os.path.join(folder, only + '*_[0-9][0-9].png'))):
    name = os.path.basename(f)
    if name.startswith('flag_'):
        continue
    im = Image.open(f).convert('RGB')
    hsv = np.asarray(im.convert('HSV')).astype(np.int32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    cy = (s > 50) & (v > 60) & (np.abs(h - 127) < 9)
    areola = int((cy & (v >= SPLIT)).sum())
    genital = int((cy & (v < SPLIT)).sum())
    rows.append((name, areola, genital))
    if areola >= least or genital >= least:
        ys, xs = np.nonzero(cy)
        x0, x1 = max(xs.min() - 60, 0), min(xs.max() + 60, im.width)
        y0, y1 = max(ys.min() - 60, 0), min(ys.max() + 60, im.height)
        im.crop((x0, y0, x1, y1)).save(os.path.join(folder, 'flag_' + name))
        flagged.append((name, areola, genital))
with open(os.path.join(folder, 'counts%s.csv' % ('_' + only if only else '')), 'w') as out:
    out.write('frame,areola_px,genital_px\n')
    for r in rows:
        out.write('%s,%d,%d\n' % r)
print('frames', len(rows), 'flagged', len(flagged),
      'areola-flagged', sum(1 for r in flagged if r[1] >= least),
      'genital-flagged', sum(1 for r in flagged if r[2] >= least))
for r in flagged:
    print('  %s areola=%d genital=%d' % r)
