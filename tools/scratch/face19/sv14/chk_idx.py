"""chk_idx.py: which dump index is photographed frame k: Godot HAIRCLEAR segs vs the replica at HEAD (both offsets)."""
import sys; sys.path[:0] = ["../sv13"]
from ev13 import *
st = sys.argv[1] if len(sys.argv) > 1 else "braid"
fr, xs, m = run13(st)
g = hclog("hc/s11_%s_review.log" % st)
print("dumps", len(fr), "godot frames", len(g))
for off in (0, 3, 4):
    err = []
    for k in range(30, 56):
        if k + off >= len(xs) or k not in g: continue
        c = clear(xs[k + off], "s12/mw", k) if False else None
    # compare chain positions instead: Godot's own log has no chain; use HAIRCLEAR against the matching mesh
for off in (0, 3, 4):
    worst = 0
    for k in range(30, 56):
        c = clear(xs[k + off], "s12/mw", k)
        if c is None or k not in g: continue
        worst = max(worst, max(abs(a - b) for a, b in zip(c, g[k])))
    print("offset", off, "max |offline-godot| segs k30-55 (mr mesh vs review log) %.2f" % worst)
