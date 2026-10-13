from vlift import *
import math
def cap(deg):
    def f(d, x, q):
        q = q.copy()
        for i in range(8):
            a = 2 * math.acos(min(1, abs(q[i][0])))
            if a > math.radians(deg):
                s = math.sin(math.radians(deg) / 2) / math.sin(a / 2); q[i] = np.r_[math.cos(math.radians(deg) / 2) * np.sign(q[i][0] or 1), q[i][1:] * s * np.sign(q[i][0] or 1)]
        return (q,)
    return f
H = Hair("long"); fr = lg("hair12", "death_long"); x = today(fr)
for j in range(27, 37):
    d = fr[j]; q, _ = turns(d["target"], x[j]); base = None; row = []
    for name, fn in (("none", lambda d, x, q: (None,)), ("turn", lambda d, x, q: (q,)), ("c30", cap(30)), ("c20", cap(20))):
        P, _ = H.drawn(d, x[j], *fn(d, x[j], q)); g = gaps(d, P) * 100
        if base is None: base = g
        ex = g - base; m = g > 2
        row.append("%s +%4.1f" % (name, ex[m].max() if m.any() else 0))
    print("f%d c%.1f extra lift max (cm): " % (j, j / 3) + " ".join(row))
