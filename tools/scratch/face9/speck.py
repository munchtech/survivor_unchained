"""speck.py x0,y0,x1,y1 img ...: speckle over a stretch of skin. Within the box, skin only (pixels near the box's
median colour, not the outfit or the background): `dots` how much small dark specks stand out (a 1.5-px blur against a
6-px blur, its darker side, mean in per cent of the skin's lightness), `spots per 1000 px` how many specks are past 4%,
`mottle` the spread at 3 to 12 px (per cent), and `fine` at 0.8 px."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

box = [int(v) for v in sys.argv[1].split(',')]
for p in sys.argv[2:]:
    a = np.asarray(Image.open(p).convert('RGB').crop(box)).astype(np.float32) / 255
    li = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    L = li @ np.array([0.2126, 0.7152, 0.0722])
    med = np.median(li.reshape(-1, 3), 0)
    skin = (np.abs(li - med).max(2) < 0.35 * med.max()) & (L > 0.25 * np.median(L))
    skin = ndimage.binary_erosion(skin, iterations=6)
    s1 = ndimage.gaussian_filter(L, 1.5)
    s6 = ndimage.gaussian_filter(L, 6)
    s12 = ndimage.gaussian_filter(L, 12)
    s3 = ndimage.gaussian_filter(L, 3)
    d = (s1 - s6) / np.maximum(s6, 1e-4)
    dark = np.clip(-d, 0, None)
    # (a speck: a local minimum of the 1.5-px blur, 4% under its surround)
    mins = (s1 == ndimage.minimum_filter(s1, size=5)) & (d < -0.04) & skin
    fine = (L - ndimage.gaussian_filter(L, 0.8)) / np.maximum(s6, 1e-4)
    mot = (s3 - s12) / np.maximum(s12, 1e-4)
    n = skin.sum()
    name = p.replace('\\', '/').split('/')[-1]
    print('%-26s skin %6d px  dots %.2f%%  spots/1000px %.2f  mottle %.2f%%  fine %.2f%%' % (
        name, n, 100 * dark[skin].mean(), 1000 * mins.sum() / max(n, 1), 100 * mot[skin].std(), 100 * fine[skin].std()))
