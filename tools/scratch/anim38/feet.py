import sys, math
sys.argv = [sys.argv[0]] + sys.argv[1:]
exec(open(__file__.replace("feet.py", "stance.py")).read().split("if args and")[0])
for n in args:
    rot, pos = load(n)
    g, p = sk.fk(rot, pos)
    a = {s: p[:, sk.i(f"foot_{s}")] for s in "lr"}
    b = {s: p[:, sk.i(f"ball_{s}")] for s in "lr"}
    w = abs(a["l"][:, 0] - a["r"][:, 0]).mean()
    stag = (a["l"][:, 2] - a["r"][:, 2]).mean()
    out = [math.degrees(math.atan2(*(b[s] - a[s])[:, [0, 2]].mean(0))) for s in "lr"]
    print(f"{n:22s} ankle width {w:.3f} stagger(l-r z) {stag:+.3f} toe yaw l {out[0]:+.1f} r {out[1]:+.1f} hip width {abs(p[0, sk.i('thigh_l'), 0] - p[0, sk.i('thigh_r'), 0]):.3f}")
