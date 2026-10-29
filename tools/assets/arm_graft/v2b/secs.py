# Sections of the right (or left) arm at rest: girth (hull), front width (extent along 'top'), depth (along 'fr').
#   python secs.py <dump.npz> [side]
import sys, numpy as np
from lib import *
d = load(sys.argv[1]); sd = sys.argv[2] if len(sys.argv) > 2 else "r"
P = d["P"]; T, _, _ = tri_split(d["polys"]); nm = d["names"]; VG = d["VG"]
F = Frame(d, sd); S = 1.654
arm = VG[:, nm.index("upperarm_" + sd)] + VG[:, nm.index("lowerarm_" + sd)] + VG[:, nm.index("hand_" + sd)] > 0.5
print(" seg   t   girth(mm) /S   front  depth  w:d")
for seg, ts in (("up", [0.15, 0.3, 0.46, 0.5, 0.6, 0.75, 0.9, 1.0]), ("fo", [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.85, 0.9, 0.95])):
    for t in ts:
        if seg == "up": o = F.A + t * F.Lu * F.nu; n = F.nu
        else: o = F.E + t * F.Lf * F.nf; n = F.nf
        top, fr = F.axes(n)
        q = section(P, T, o, n, top, fr, arm)
        if len(q) < 5: print(seg, t, "none"); continue
        # keep the component near the bone
        q = q[np.linalg.norm(q, axis=1) < 0.08]
        g = girth(q) * 1e3; w = np.ptp(q[:, 0]) * 1e3; dp = np.ptp(q[:, 1]) * 1e3
        print("%s %5.2f %6.0f %.3f %6.0f %6.0f %5.2f" % (seg, t, g, g / 1e3 / S, w, dp, w / dp))
