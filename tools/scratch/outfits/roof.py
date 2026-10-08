"""Her underside across the strip at rest: for points along the strip (front to back), the
height of her skin seen straight from below at each distance from her midline.
    python roof.py <heroine.glb>"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'legal', 'motioncheck'))
from glbread import Body
from posed import first_hits

b = Body(sys.argv[1])
V, T = b.V, b.T
under = np.array([-0.001853, 0.925378, -0.001549])      # (the check's: lowest point under her crotch)
mons = np.array([0.001155, 0.967127, 0.076012])
crop = T[(np.abs(V[T].mean(1) - under) < [0.08, 0.08, 0.12]).all(1)]
xs = np.array([0.0, 0.004, 0.008, 0.012, 0.014, 0.017, 0.02, 0.025])
print('strip: from z %.3f (rear) to the mons front at z %.3f, y %.3f; under-crotch point y %.3f' % (under[2] - 0.023, mons[2], mons[1], under[1]))
print('height (mm above the under-crotch point) of her skin seen from below, by |x| (mm):')
print('   z(mm)  ' + ' '.join('%6.0f' % (x * 1000) for x in xs))
for z in np.arange(under[2] - 0.035, mons[2] + 0.001, 0.008):
    row = []
    for x in xs:
        hs = []
        for sx in (1, -1):
            o = np.array([sx * x, under[1] - 0.2, z])
            t = first_hits(o, np.array([[0.0, 1.0, 0.0]]), V[crop])[0]
            hs.append(o[1] + t - under[1] if np.isfinite(t) else np.nan)
        row.append(np.nanmean(hs) if not all(np.isnan(hs)) else np.nan)
    print('  %6.1f   ' % ((z - under[2]) * 1000) + ' '.join('%6.1f' % (r * 1000) if np.isfinite(r) else '     -' for r in row))
