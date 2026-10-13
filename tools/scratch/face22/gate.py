"""gate.py REF DBG: the debug view (dbg_gate) sampled where meas.py and neckx.py measure on REF (same pose): linear R
(key path in front), G (soft lamps), B (lamps behind) at the lit neck, the near jaw, the far-neck box, and along the rows."""
import sys, os
import numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__))
for d in ("face17", "face19", "face21"): sys.path.insert(0, os.path.join(H, "..", d))
import meas, neckx  # noqa
ref, dbg = [os.path.join(meas.S, x + ".png") for x in sys.argv[1:3]]
m, _ = neckx.measure(ref)
a = np.asarray(Image.open(ref).convert("RGB"), np.float32) / 255
L = meas.ff.detect((a * 255).astype(np.uint8))[:, :2]
h = np.linalg.norm(L[152] - L[10]); r = max(3, int(0.025 * h))
d = np.asarray(Image.open(dbg).convert("RGB"), np.float32) / 255
d = np.where(d <= 0.04045, d / 12.92, ((d + 0.055) / 1.055) ** 2.4)
def at(x, y, rr=r): return d[int(y - rr):int(y + rr), int(x - rr):int(x + rr)].reshape(-1, 3).mean(0)
fmt = lambda v: "%.3f/%.3f/%.3f" % tuple(v)
print("neck", fmt(at(*(L[152] + [0, 0.35 * h]))), "jaw", fmt(at(*(L[136] + [0, 0.07 * h]))), "cheek", fmt(at(*L[205])))
b = m["box"]; print("far box", fmt(d[b[1]:b[3], b[0]:b[2]].reshape(-1, 3).mean(0)))
for t in (0.15, 0.3):
    q = m["rows"][t]; xs = np.linspace(q["lo"], q["hi"], 12).astype(int)
    print("row", t, " ".join("%d:%.2f/%.2f/%.2f" % ((x,) + tuple(d[q["y"] - 1:q["y"] + 2, x].mean(0))) for x in xs))
