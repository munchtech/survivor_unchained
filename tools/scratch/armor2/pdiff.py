# pdiff.py DIR: each eq_<set>_<cam>_old.png against _new.png: max and mean channel difference, pixels over 8/255.
import sys, os, glob
import numpy as np
from PIL import Image
d = sys.argv[1]
for o in sorted(glob.glob(os.path.join(d, "eq_*_old.png"))):
    n = o.replace("_old.png", "_new.png")
    if not os.path.exists(n): print(os.path.basename(o), "no pair"); continue
    a = np.asarray(Image.open(o).convert("RGB"), np.int16); b = np.asarray(Image.open(n).convert("RGB"), np.int16)
    df = np.abs(a - b)
    over = (df.max(2) > 8)
    ys, xs = np.nonzero(over)
    box = (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None
    print("%-22s max %3d mean %.4f px>8: %d box %s" % (os.path.basename(o)[3:-8], df.max(), df.mean(), over.sum(), box))
