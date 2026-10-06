"""Landmarks against the code's minimum (the posed nipple tip as drawn), per picture.
    python lmcheck.py <png> [<png> ...]"""
import json
import sys

import numpy as np
from PIL import Image

for f in sys.argv[1:]:
    j = json.load(open(f[:-4] + '.json'))
    a = np.asarray(Image.open(f).convert('RGB')).astype(int)
    sw, sh = j['size']['xy']
    sx, sy = a.shape[1] / sw, a.shape[0] / sh
    print(f.split('/')[-1].split('\\')[-1], 'scale', round(sx, 3), round(sy, 3))
    for k, v in j.items():
        if k != 'size':
            print('   %-14s (%4d, %4d)%s' % (k, v['xy'][0] * sx, v['xy'][1] * sy, ' behind' if v['behind'] else ''))
    near = (a[..., 2] >= 250) & (a[..., 1] <= 8)
    r = np.where(near, a[..., 0], 999)
    for x0, x1 in [(0, a.shape[1] // 2), (a.shape[1] // 2, a.shape[1])]:
        rr = r.copy()
        rr[:, :x0] = 999
        rr[:, x1:] = 999
        if rr.min() < 999:
            y, x = np.unravel_index(np.argmin(rr), rr.shape)
            print('   code minimum at (%4d, %4d), red %d' % (x, y, rr[y, x]))
