"""Which frame of each run pick.py's 'max' takes: python maxf.py run1 run2 ..."""
import sys
import numpy as np
from PIL import Image
from shots import run

for name in sys.argv[1:]:
    frames = run(name)
    arrs = [np.asarray(Image.open(f).convert("L").resize((240, 135))).astype(np.float32) for f in frames]
    mean = np.mean(arrs, axis=0)
    d = [np.abs(a - mean).sum() for a in arrs]
    order = np.argsort(d)[::-1]
    print(name, [frames[k].split("_")[-1][:2] for k in order[:4]])
