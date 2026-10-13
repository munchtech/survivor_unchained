"""pos10.py OPTS FRAMES [SET]: throw braid chain in b3's frame (across, up, back; cm) per frame, HEAD over OPTS."""
from hs10 import *
o = eval(sys.argv[1]); ks = eval(sys.argv[2]); SET = sys.argv[3] if len(sys.argv) > 3 else "hair17d"
fr = lg(SET, "throw_braid")
a, _ = sim10(fr, "braid", orig=1); b, _ = sim10(fr, "braid", **o)
for k in ks:
    for tag, xs in (("HEAD", a), ("NEW ", b)):
        print("k%2d %s %s | 3d %s" % (k, tag, " ".join("p%d(%+5.1f,%+5.1f,%+5.1f)" % ((i,) + tuple(F(fr[k], xs[k][i]))) for i in range(1, 8)), " ".join("%3.0f" % v for v in angles(xs[k]))))
