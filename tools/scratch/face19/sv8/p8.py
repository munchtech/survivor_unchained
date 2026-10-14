"""p8.py CLIP [STYLE]: per frame: cell, head height, upper-back height, spine up-dot (hair15)."""
import sys; sys.path[:0] = ["../sv6", "../sv5", "../sv4", "../sv3"]
from hs6 import *
STEP = dict(death=3, getup=4, getupback=4, throw=2, run=2, stop=2)
cl = sys.argv[1]; st = sys.argv[2] if len(sys.argv) > 2 else "braid"
fr = lg("hair15", cl + "_" + st)
rows = []
for j, d in enumerate(fr):
    g = d["ground"]; at = d["at"]; up = nz((at[1] + at[2]) / 2 - at[10])[1]
    rows.append("c%.2f h%.2f b%.2f u%+.2f" % (j / STEP[cl], d["head"][0][1] - g, at[3:8].mean(0)[1] - g, up))
for k in range(0, len(rows), 4): print(" | ".join(rows[k:k + 4]))
