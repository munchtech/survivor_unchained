"""a5.py STYLE CLIP f0 f1 [log]: chain and target in her back's frame (cm, lat/out/along from the root) per point (C# x)."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
st, clip, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); h = sys.argv[5] if len(sys.argv) > 5 else "hair12"
fr = lg(h, clip + "_" + st); x = today(fr)
for j in range(f0, f1 + 1):
    d = fr[j]; b = 5; out = nz(d["back"][b]); lat = nz(d["across"][b]); along = nz(np.cross(out, lat))
    if (d["at"][10] - d["at"][3]) @ along < 0: along = -along
    def bf(p): q = p - x[j][0]; return (q @ lat * 100, q @ out * 100, q @ along * 100)
    print("f%2d x " % j, " ".join("(%+3.0f %+3.0f %+3.0f)" % bf(x[j][i]) for i in range(1, 8)))
    print("    t ", " ".join("(%+3.0f %+3.0f %+3.0f)" % bf(d["target"][i]) for i in range(1, 8)))
