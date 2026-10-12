"""ev15.py BASE KEY V1;V2;.. [STYLE]: get_up review dump, the ponytail (default) at BASE with KEY set to each value (KEY '-'
for BASE alone): segs 4-7 worst k40-52 (the line) and k28-60 (wide), per outfit (mw warden, mr reaver); when the carry ends
(first frame with nothing carried); the largest Godot-like move (HAIRMOVE, neck frame) k40-60 and k28-60; and the largest
change from HEAD over k0-27 (cm)."""
import sys; sys.path[:0] = ["../sv14"]
import hs15
from ev14 import *


def full(st, o):
    fr, xs, m = run14(st, o)
    res = {md: {k: clear(xs[k], "s12/" + md, k) for k in range(28, 61)} for md in ("mw", "mr")}
    w = lambda md, a, b: min(min(res[md][k][3:]) for k in range(a, b + 1))
    end = max((k for k in range(len(m.rlog)) if m.rlog[k].any()), default=-2) + 1
    g = gx(xs, m); mv, mvk = gmove(fr, g, 40, 60); mvw, mvkw = gmove(fr, g, 28, 60)
    return dict(fr=fr, xs=xs, m=m, res=res, line=(w("mw", 40, 52), w("mr", 40, 52)), wide=(w("mw", 28, 60), w("mr", 28, 60)),
                end=end, mv=mv, mvw=mvw, mvk=mvk, mvkw=mvkw)


def fmt(r, h=None, name=""):
    d = "" if h is None else " | k0-27 %.2f" % (max(np.linalg.norm(r["xs"][k] - h["xs"][k], axis=1).max() for k in range(28)) * 100)
    return "%-22s line mw %5.1f mr %5.1f | wide mw %5.1f mr %5.1f | ends k%d | move %4.1f k%d p%d | wide %4.1f k%d p%d%s" % (
        name, r["line"][0], r["line"][1], r["wide"][0], r["wide"][1], r["end"], r["mv"][0], r["mv"][1], r["mv"][2],
        r["mvw"][0], r["mvw"][1], r["mvw"][2], d)


if __name__ == "__main__":
    base = eval(sys.argv[1]); key = sys.argv[2]; vals = [eval(v) for v in sys.argv[3].split(";")] if len(sys.argv) > 3 else [None]
    st = sys.argv[4] if len(sys.argv) > 4 else "ponytail"
    h = full(st, {})
    if "nohead" not in sys.argv: print(fmt(h, None, st + " HEAD"), flush=True)
    for v in vals:
        o = dict(base)
        if key != "-": o[key] = v
        print(fmt(full(st, o), h, "%s=%s" % (key, v)), flush=True)
