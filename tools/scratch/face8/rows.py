"""python rows.py img_lit img_nb y0,y1,... x0 x1 : along rows of the lit picture and the NormalBuffer, the brightness
and the normal's colour every 6 px, to find where the band and any step in the normals are."""
import os
import sys
import numpy as np
from PIL import Image

D = os.path.dirname(os.path.abspath(__file__))
lit = np.asarray(Image.open(os.path.join(D, sys.argv[1])).convert('RGB')).astype(float)
nb = np.asarray(Image.open(os.path.join(D, sys.argv[2])).convert('RGB')).astype(float)
ys = [int(v) for v in sys.argv[3].split(',')]
x0, x1 = int(sys.argv[4]), int(sys.argv[5])
for y in ys:
    L = lit[y - 2:y + 3].mean(0).mean(1)
    N = nb[y - 2:y + 3].mean(0)
    print("row", y)
    print("  x:   " + " ".join("%4d" % x for x in range(x0, x1, 6)))
    print("  lit: " + " ".join("%4d" % L[x] for x in range(x0, x1, 6)))
    for c, nm in enumerate("RGB"):
        print("  nb%s: " % nm + " ".join("%4d" % N[x, c] for x in range(x0, x1, 6)))
