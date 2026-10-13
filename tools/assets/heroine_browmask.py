"""Trim Own's brow dye mask (art/people/paint/brows.png, alpha) to her brows as heroine_browtail.py left them: zero it
where that script refilled her paint (the ghost tail and the trimmed tips), feathered. Run once, after it: ORIG_PAINT = own paint before it (git show b981ed50:godot/art/people/head_tex/heroine_head.jpg). python heroine_browmask.py ORIG_PAINT REPO"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
orig, wt = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(orig).convert('RGB')).astype(float)
b = np.asarray(Image.open(wt + '/godot/art/people/head_tex/heroine_head.jpg').convert('RGB')).astype(float)
m = np.asarray(Image.open(wt + '/godot/art/people/paint/brows.png')).copy()
d = np.abs(a - b).max(-1) > 6                                  # refilled texels (4096)
d = ndimage.binary_closing(ndimage.binary_opening(d, iterations=1), iterations=3)
d2 = np.asarray(Image.fromarray((d * 255).astype(np.uint8)).resize((2048, 2048), Image.BILINEAR)).astype(float) / 255
inm = m[..., 3] > 0
d2 = d2 * inm                                                  # only where the dye mask is (not the ears)
cut = np.clip(ndimage.gaussian_filter(ndimage.binary_dilation(d2 > 0.3, iterations=2).astype(float), 1.5), 0, 1)
before = (m[..., 3] > 8).sum()
m[..., 3] = (m[..., 3] * (1 - cut)).astype(np.uint8)
print('mask texels', before, '->', (m[..., 3] > 8).sum(), '; cut', int((cut > 0.5).sum()))
Image.fromarray(m).save(wt + '/godot/art/people/paint/brows.png')
