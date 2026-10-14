"""m10.py SET CLIP: the C# dump vs the C#-at-HEAD replica (M8), worst cm per frame."""
import sys; sys.path[:0] = ["../sv9", "../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from g9 import *
SET = sys.argv[1]; CL = sys.argv[2]; st = CL.split("_")[1]
fr = lg(SET, CL); xs, _ = sim8(fr, st, **per4(H7, st)); cs = today(fr)
e = [np.linalg.norm(p - q, axis=1).max() * 100 for p, q in zip(xs, cs)][:-1]
print("%s %s: worst %.3f cm (k%d); per frame %s" % (SET, CL, max(e), int(np.argmax(e)), " ".join("%.2f" % v for v in e)))
