"""capq.py: the long hair's card-turn cap as C# does it (hair solver 7: axis scaled by hand), on (8, 4) [w,x,y,z] quaternions."""
import numpy as np, math
def capq(q, deg=20):
    q = q.copy()
    for i in range(len(q)):
        if q[i][0] < 0: q[i] = -q[i]
        a = 2 * math.acos(min(1, q[i][0]))
        if a > math.radians(deg):
            v = q[i][1:]; q[i] = np.r_[math.cos(math.radians(deg) / 2), v * math.sin(math.radians(deg) / 2) / np.linalg.norm(v)]
    return q
