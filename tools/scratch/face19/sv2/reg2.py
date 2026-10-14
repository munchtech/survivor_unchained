"""Regression against today's with the scale fix (FIX): tip deviation max over the clip, per config."""
from hs import *
import sys
CLIPS = ["run", "stop", "throw", "getup", "getupback"]
def reg(cfgs, styles=("braid", "ponytail", "long"), clips=CLIPS, ref=None):
    out = {}
    for st in styles:
        for cl in clips:
            fr = runlog(cl + "_" + st); b = sim(fr, st, **(ref or FIX)); sw0 = swing(fr, b)
            line = "%-9s %-8s amp %.3f |" % (cl, st, np.abs(sw0 - sw0[0]).max())
            for name, o in cfgs:
                xs = sim(fr, st, **o); sw = swing(fr, xs)
                dev = np.linalg.norm(sw - sw0, axis=1); out[(st, cl, name)] = dev
                line += " %s %.3f" % (name, dev.max())
            print(line)
    return out
if __name__ == "__main__":
    reg([("today", dict(BASE)), ("new", NEW)])
