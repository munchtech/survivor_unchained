"""grid.py BASE KEY V1,V2,..: ev13 summaries (worst seg 4-7 k40-52 mw/mr, neck depth, largest move, carry still on at k60)
for BASE with KEY set to each value."""
from ev13 import *
base = eval(sys.argv[1]); key = sys.argv[2]; vals = [eval(v) for v in sys.argv[3].split(";")]
sts = sys.argv[4].split(",") if len(sys.argv) > 4 else ["ponytail", "braid"]
for v in vals:
    o = dict(base); o[key] = v
    for st in sts:
        out, nk, mv, m = report(st, o)
        end = max(k for k in range(len(m.rlog)) if m.rlog[k].any()) if any(r.any() for r in m.rlog) else -1
        print("%s=%s %-8s mw %5.1f mr %5.1f | neck %.1f k%d | move %.1f k%d | carry ends k%d" % (key, v, st, out[0][1], out[1][1], nk[0], nk[1], mv[0], mv[1], end + 1))
