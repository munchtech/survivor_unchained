"""a7.py: root speed and acceleration per clip (hair12 inputs): max |v|, max |a|, and frames with |a| > 1.5 g."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
for st in ("braid", "long"):
    for cl in ("run", "stop", "throw", "getup", "getupback", "death"):
        fr = lg("hair12", cl + "_" + st)
        r = np.array([d["target"][0] for d in fr]); dt = np.array([d["dt"] for d in fr])
        v = np.r_[[np.zeros(3)], np.diff(r, axis=0) / dt[1:, None]]; a = np.r_[[np.zeros(3)], np.diff(v, axis=0) / dt[1:, None]]
        a[1] = 0
        sp = np.linalg.norm(v, axis=1); ac = np.linalg.norm(a, axis=1)
        big = [(j, round(ac[j] / 9.8, 1)) for j in range(len(fr)) if ac[j] > 1.5 * 9.8]
        print("%-6s %-9s dt %.4f vmax %.1f@f%d amax %.1f g@f%d  >1.5g: %s" % (st, cl, dt[1], sp.max(), sp.argmax(), ac.max() / 9.8, ac.argmax(), big[:12]))
