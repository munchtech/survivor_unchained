"""a1.py SET CLIP: M8 replica vs the C# dump (cm per frame), joint angles, and the chain in ball b3's frame."""
import sys; sys.path[:0] = ["../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from hs8 import *
SET = sys.argv[1] if len(sys.argv) > 1 else "hair17d"; CL = sys.argv[2] if len(sys.argv) > 2 else "throw_braid"
st = CL.split("_")[1]
fr = lg(SET, CL)
xs, m = sim8(fr, st, **per4(H7, st))
cs = today(fr)
print("frames", len(fr), "first f", fr[0]["f"])
def b3frame(d, p):
    at = d["at"][3]; bk = d["back"][3]; ac = nz(d["across"][3]); up = np.cross(bk, ac)
    return np.array([(p - at) @ ac, (p - at) @ up, (p - at) @ bk]) * 100
for k in range(len(fr)):
    err = np.linalg.norm(xs[k] - cs[k], axis=1).max() * 100
    a = angles(cs[k])
    pts = " ".join("p%d(%+.0f,%+.0f,%+.0f)" % ((i,) + tuple(b3frame(fr[k], cs[k][i]))) for i in range(1, 6))
    print("k%2d c%4.1f err %.2f ang %s | %s" % (k, k / 2, err, " ".join("%3.0f" % v for v in a), pts))
