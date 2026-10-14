"""geo14.py STYLE OPTS [K0 K1] [MD]: per frame: carried flags, capsule on, HAIRCLEAR 7 segments (MD), and the chain in her
neck frame (a: to her right, h up, b behind; cm), plus the move (Godot-like) into that frame."""
from ev14 import *
st = sys.argv[1]; o = eval(sys.argv[2]); K0, K1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (40, 52)
md = sys.argv[5] if len(sys.argv) > 5 else "mr"
fr, xs, m = run14(st, o); g = gx(xs, m); _, mv = gmove(fr, g, K0, K1)
for k in range(K0, K1 + 1):
    d = fr[k]; at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up)
    R = np.c_[np.cross(up, bk), up, bk]; P = (xs[k] - neck) @ R * 100
    c = clear(xs[k], "s12/" + md, k)
    print("k%d %s c%d w%.2f mv%4.1f | %s | %s" % (k, "".join("1" if r else "." for r in m.rlog[k]), m.caplog[k], m.wlog[k], mv.get(k, 0),
          " ".join("%5.1f" % v for v in c) if c else "-", " ".join("(%.0f,%.0f,%.0f)" % tuple(P[i]) for i in range(1, 8))))
