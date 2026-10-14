"""nk.py: per frame, in spine_03's rest space (cm): the upper neck ball's and the head bone's moves from rest, the head's
pitch (its up axis tilted forward, deg), and her spine's lean (up axis vs world up, deg)."""
from ridge import *
H0 = None
for k in range(28, 61, 2):
    d = fr[k]; f = rest_of(d); ex = nz(d["across"][3]); ez = -nz(d["back"][3]); ey = np.cross(ez, ex); R = np.c_[ex, ey, ez]
    hu = d["head"][2] @ R; hu = hu / np.linalg.norm(hu); hp = f(d["head"][0])
    if H0 is None: H0 = hp
    print("k%d neck1 %s head %s pitch %.0f lean %.0f" % (k, np.round((f(d["at"][1]) - np.array([0, 1.6240698, -0.0467118])) * 100, 1), np.round(hp * 100, 1), math.degrees(math.atan2(hu[2], hu[1])), math.degrees(math.acos(ey[1]))))
