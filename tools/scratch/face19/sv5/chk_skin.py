import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
from skin import Hair
H = Hair("long"); fr = lg("hair12", "death_long")
for j in (0, 15, 30):
    d = fr[j]; T = H.bones(d)
    tb = T[H.bone]; tr = (np.c_[H.rest, np.ones(8)] @ tb.T)[:, :3]
    hb = T["Head"] @ np.r_[H.balls[0][1], 1]
    print(j, "chain target err %.4f m" % np.abs(tr - d["target"]).max(), "head ball err %.4f" % np.abs(hb[:3] - d["at"][0]).max(),
          "neck ball2 err %.4f" % np.abs((T["neck_01"] @ np.r_[H.balls[2][1], 1])[:3] - d["at"][2]).max())
