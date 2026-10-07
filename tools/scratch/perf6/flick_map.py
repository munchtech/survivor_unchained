"""Per-tile flicker (|a - 2b + c| after alignment) as a grid, for one triple of a run, with the shifts."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402
from mres import T, shift_of, fshift  # noqa: E402

tag, i = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2
fs = C.frames(tag)
a, b, c = [C.load(f).mean(axis=2) for f in fs[i:i + 3]]
H, W = a.shape
m = 16
for y in range(0, H - T, T):
    row = []
    for x in range(0, W - T, T):
        ta, tb, tc = a[y:y + T, x:x + T], b[y:y + T, x:x + T], c[y:y + T, x:x + T]
        d1, d2 = shift_of(ta, tb), shift_of(ta, tc)
        dd = np.abs(ta - fshift(tb, -d1[0], -d1[1]) * 2 + fshift(tc, -d2[0], -d2[1]))[m:-m, m:-m].mean()
        raw = np.abs(ta - tb)[m:-m, m:-m].mean()
        row.append(f"{dd:5.1f}/{raw:4.1f}/{d1[1]:+4.1f},{d1[0]:+4.1f}")
    print(f"y{y:5d} " + " ".join(row))
