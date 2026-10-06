"""python nbgrad.py nb.png out.png : where the normals step (the NormalBuffer's colour gradient, brightened), so creases,
seams and shards stand out from the smooth turning of her form."""
import os
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

D = os.path.dirname(os.path.abspath(__file__))
a = np.asarray(Image.open(os.path.join(D, sys.argv[1])).convert('RGB')).astype(float) / 255.0
a = ndimage.gaussian_filter(a, (0.7, 0.7, 0))
g = np.zeros(a.shape[:2])
for c in range(3):
    gx = ndimage.sobel(a[..., c], 1)
    gy = ndimage.sobel(a[..., c], 0)
    g += gx * gx + gy * gy
g = np.sqrt(g)
# the smooth turning of a form is a low, even gradient; a step is a ridge: the gradient less its own blur
r = np.clip(g - ndimage.gaussian_filter(g, 6), 0, None)
img = np.clip(r * 6.0, 0, 1)
Image.fromarray((img * 255).astype(np.uint8)).save(os.path.join(D, sys.argv[2]))
