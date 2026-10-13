"""pose.py: per frame of each clip (braid logs, hair13): cell, head height, neck/upper-back height, spine's up-dot, root speed."""
import sys; sys.path[:0] = ["../sv5", "../sv4", "../sv3"]
from hs5 import *
STEP = dict(death=3, getup=4, getupback=4, throw=2, run=2, stop=2)
def pose(d):
    g = d["ground"]; hd = d["head"][0]; at = d["at"]
    neck = at[1]; up3 = at[5]; low = at[10]
    sp = nz(neck - low)
    return hd[1] - g, up3[1] - g, sp[1]
if __name__ == "__main__":
    for cl in sys.argv[1:]:
        fr = lg("hair13", cl + "_braid")
        print("==", cl, len(fr))
        for j, d in enumerate(fr):
            hh, uh, su = pose(d)
            v = np.linalg.norm(d["target"][0] - fr[j - 1]["target"][0]) / d["dt"] if j else 0
            print("f%2d c%4.1f head %.2f back %.2f spineUp %+.2f rootV %.1f" % (j, j / STEP[cl], hh, uh, su, v))
