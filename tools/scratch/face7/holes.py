"""holes.py paint.png ... : holes in a face's paint (unpainted islands inside it), largest first: v7 had them under
Saffron's eyes where her mouth's inside came through her cheeks."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

for p in sys.argv[1:]:
    a = np.asarray(Image.open(p))[..., 3] > 127
    holes = ndimage.binary_fill_holes(a) & ~a
    lab, n = ndimage.label(holes)
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    print("%-60s %d holes; largest %s" % (p[-60:], n, sizes[:12].tolist()))
