"""trims.py TAG [DAMP]: per face, the linear gains that take its rendered cheek to its portrait's chroma and hue, and
its neck to the portrait's neck-to-cheek chroma ratio (hue as the cheek's), each at its own rendered lightness.
Prints body gains (the neck: HerBodyTone) and face gains (on top of the body's: HerFaceTone's multiplier)."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import meas  # noqa  (its spots and Oklab)
M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
def lab2lin(L, C, h):
    lab = np.array([L, C * np.cos(np.radians(h)), C * np.sin(np.radians(h))])
    return np.linalg.inv(M1) @ (np.linalg.inv(M2) @ lab) ** 3
tag = sys.argv[1]; damp = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
faces = ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']
for fc in faces:
    o, _ = meas.spots(os.path.join(meas.S, "%s_%s.png" % (tag, fc)))
    rp = os.path.join(meas.R, ("own_her_23" if fc == "own" else fc + "_11") + ".png")
    r, _ = meas.spots(rp)
    ch, nk = o["cheek"], o["neck"]; pc, pn = r["cheek"], r["neck"]
    tc = (ch[0], ch[1] + damp * (pc[1] - ch[1]), ch[2] + damp * (pc[2] - ch[2]))
    ratio = pn[1] / pc[1]
    tn = (nk[0], nk[1] + damp * (ratio * pc[1] - nk[1]), nk[2] + damp * (pc[2] - nk[2]))
    gb = lab2lin(*tn) / lab2lin(*nk); gc = lab2lin(*tc) / lab2lin(*ch)
    gf = gc / gb
    print("%-9s cheek C%.3f->%.3f h%2.0f->%2.0f | neck C%.3f->%.3f h%2.0f->%2.0f (ratio %.2f) | body (%.3f, %.3f, %.3f) face x(%.3f, %.3f, %.3f)"
          % (fc, ch[1], tc[1], ch[2], tc[2], nk[1], tn[1], nk[2], tn[2], ratio, *gb, *gf))
