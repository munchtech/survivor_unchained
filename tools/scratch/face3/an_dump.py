import sys
import numpy as np
d = np.load(sys.argv[1])
Lr, L0, hit = d["Lr"], d["L0"], d["hit"]
OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
        172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 185, 40, 39, 37, 0, 267, 269, 270, 409, 78, 95, 88, 178, 87, 14, 317,
        402, 318, 324, 308, 191, 80, 81, 82, 13, 312, 311, 310, 415]
EYE = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7, 263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249]
NOSE = [1, 2, 98, 327, 4, 5, 195, 197, 6, 168, 48, 278, 64, 294, 129, 358, 49, 279, 115, 344, 220, 440]
print("Lr range", Lr.min(0), Lr.max(0))
print("L0 range", L0[hit].min(0), L0[hit].max(0))
# key points: nose tip 1, eye corners 33,263, chin 152, mouth corners 61,291, forehead 10, cheeks 234,454
for nm, i in (("nose tip", 1), ("nasion 168", 168), ("eye out 33", 33), ("eye out 263", 263), ("eye in 133", 133), ("mouth 61", 61),
              ("upper lip 0", 0), ("lower lip 17", 17), ("chin 152", 152), ("forehead 10", 10), ("cheek 234", 234), ("cheek 454", 454),
              ("cheekbone 50", 50), ("cheekbone 280", 280)):
    print("%-14s Lr %s   L0 %s" % (nm, np.round(Lr[i] * 1000, 1), np.round(L0[i] * 1000, 1)))
# relief: depth differences relative to nose tip, scaled lateral by eye distance
er = np.linalg.norm(Lr[33] - Lr[263]); e0 = np.linalg.norm(L0[33] - L0[263])
print("eye width ratio (outer corners)", er, e0)
for nm, i in (("nasion", 168), ("eye out", 33), ("mouth corner", 61), ("chin", 152), ("cheek 234", 234), ("forehead", 10), ("upper lip", 0)):
    print("%-12s depth behind nose tip: ref %.1f  her %.1f (in eye widths x100: ref %.1f her %.1f)" % (
        nm, 1000 * (Lr[i, 1] - Lr[1, 1]), 1000 * (L0[i, 1] - L0[1, 1]), 100 * (Lr[i, 1] - Lr[1, 1]) / er, 100 * (L0[i, 1] - L0[1, 1]) / e0))
