"""a3.py SET CLIP [frames]: root, ball centres and radii, and the chain, in ball b3's frame (cm)."""
from g9 import *
SET = sys.argv[1]; CL = sys.argv[2]
fr = lg(SET, CL); cs = today(fr)
ks = eval(sys.argv[3]) if len(sys.argv) > 3 else range(len(fr))
for k in ks:
    d = fr[k]
    print("k%2d world-up in b3 frame %s" % (k, np.round(F(d, d["at"][3] + np.array([0, 0.01, 0])), 2)))
    print("    balls " + " ".join("b%d(%+.1f,%+.1f,%+.1f r%.1f)" % ((b,) + tuple(F(d, d["at"][b])) + (d["r"][b] * 104,)) for b in range(0, 7)))
    print("    tgt " + " ".join("p%d(%+.1f,%+.1f,%+.1f)" % ((i,) + tuple(F(d, d["target"][i]))) for i in range(0, 8)))
    print("    x   " + " ".join("p%d(%+.1f,%+.1f,%+.1f)" % ((i,) + tuple(F(d, cs[k][i]))) for i in range(0, 8)))
