import sys
import numpy as np
from sp import *
name = sys.argv[1]
d = np.load(os.path.join(OUT, "relief", name + ".npz"))
e = d["emit"]
print("emit max", e.max(), "mean", e.mean())
h = d["height"]
print("height range", h.min(), h.max())
em = np.clip(e / max(e.max(), 1e-6), 0, 1) ** (1 / 2.2)
Image.fromarray((em * 255).astype(np.uint8)).resize((464, 464)).save(os.path.join(V, name + "_emit.png"))
hh = (h - h.min()) / (h.max() - h.min() + 1e-6)
Image.fromarray((hh * 255).astype(np.uint8)).resize((464, 464)).save(os.path.join(V, name + "_height.png"))
b = d["base"]
Image.fromarray((np.clip(b, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)).resize((464, 464)).save(os.path.join(V, name + "_base.png"))
