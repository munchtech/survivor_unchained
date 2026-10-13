"""a2.py SET CLIP [frames]: per frame, each point's hold share u, its target and chain in ball b3's frame (across, up, back; cm),
which balls its target is inside (and how deep), for the C# dump (x after the frame)."""
from g9 import *
SET = sys.argv[1]; CL = sys.argv[2]
fr = lg(SET, CL); cs = today(fr)
ks = eval(sys.argv[3]) if len(sys.argv) > 3 else range(len(fr))
for k in ks:
    d = fr[k]; tg = d["target"]
    print("k%2d f%d ang %s" % (k, d["f"], " ".join("%3.0f" % v for v in angles(cs[k]))))
    for i in range(1, 6):
        dn = nz(tg[i] - tg[0]) @ [0, -1, 0]
        u = smooth(0.35, 0.85, dn) * smooth(0.55, 0.77, dn)
        print("   p%d u %.2f tgt(%+5.1f,%+5.1f,%+5.1f) in[%s]  x(%+5.1f,%+5.1f,%+5.1f) in[%s]" % ((i, u) + tuple(F(d, tg[i])) + (inside(d, tg[i]),) + tuple(F(d, cs[k][i])) + (inside(d, cs[k][i]),)))
