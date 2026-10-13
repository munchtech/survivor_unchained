"""val.py STYLE LOG MESHDIR [OFF]: offline HAIRCLEAR of the replica's chain at HEAD vs the log's own HAIRCLEAR, per k
(replica frame k+OFF), to check the alignment of frames and the metric."""
from h12 import *
st, log, md = sys.argv[1:4]; off = int(sys.argv[4]) if len(sys.argv) > 4 else 0
fr = lg(*log.split("/")); xs, m = run12(fr, st); hc = hclog(log + ".log"); worst = 0
for k in sorted(hc):
    if k + off >= len(xs): continue
    c = clear(xs[k + off], md, k)
    if c is None: continue
    dd = max(abs(a - b) for a, b in zip(c, hc[k])); worst = max(worst, dd)
    if k % 6 == 0 or dd > 0.2: print("k%d log %s | off %s | diff %.2f" % (k, " ".join("%.1f" % v for v in hc[k]), " ".join("%.1f" % v for v in c), dd))
print("frames", len(fr), "worst diff %.2f" % worst)
