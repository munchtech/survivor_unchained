"""pd2.py STYLE CLIP STEP CELLS VIEW SPAN [src:dir | cfg]...: plot chains of C# logs (src:hair10) or configs over the hair9 log."""
import sys
from cfg3 import *
import pl
st, clip, step = sys.argv[1], sys.argv[2], int(sys.argv[3]); cells = [int(c) for c in sys.argv[4].split(",")]; view = sys.argv[5]; span = float(sys.argv[6])
fr = lg("hair9", clip + "_" + st); runs = []
cols = ["gray", "blue", "red", "green", "orange", "purple"]
for k, n in enumerate(sys.argv[7:]):
    xs = today(lg(n[4:], clip + "_" + st)) if n.startswith("src:") else sim(fr, st, **per(eval(n), st))
    runs.append((cols[k], xs))
pl.rows([(st, fr, runs)], cells, step, "p_%s_%s_%s.png" % (clip, st, view), view=view, span=span, size=3.0)
