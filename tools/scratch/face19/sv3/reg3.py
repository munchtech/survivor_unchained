from cfg3 import *
CLIPS = ["run", "stop", "throw", "getup", "getupback"]
def reg(cfgs, styles=("braid", "ponytail", "long"), clips=CLIPS, ref=None, d="hair9"):
    out = {}
    for st in styles:
        for cl in clips:
            fr = lg(d, cl + "_" + st); b = sim(fr, st, **(ref or FIX)); sw0 = swing(fr, b)
            line = "%-9s %-8s amp %.3f |" % (cl, st, np.abs(sw0 - sw0[0]).max())
            for name, o in cfgs:
                xs = sim(fr, st, **per(o, st)); sw = swing(fr, xs)
                dev = np.linalg.norm(sw - sw0, axis=1); out[(st, cl, name)] = (dev, xs, b)
                allp = max(np.linalg.norm(xs[i] - b[i], axis=1).max() for i in range(len(xs)))
                line += " %s %.3f/%.3f@c%d" % (name, dev.max(), allp, int(np.argmax(dev)) // (3 if cl == "death" else 4 if cl.startswith("getup") else 2))
            print(line)
    return out
if __name__ == "__main__":
    import sys
    clips = sys.argv[1].split(",") if len(sys.argv) > 1 else CLIPS
    reg([("G0", G0), ("G1", G1)], clips=clips)
