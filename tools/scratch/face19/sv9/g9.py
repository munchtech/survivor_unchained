"""g9.py: solver 9's shared helpers: a point in a ball's frame, which balls a point is inside."""
import sys; sys.path[:0] = ["../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from hs8 import *

def F(d, p, b=3):
    """p in ball b's frame (across, up, back; cm)."""
    at = d["at"][b]; bk = d["back"][b]
    ac = nz(d["across"][b]) if np.linalg.norm(d["across"][b]) > 0 else nz(np.cross([0, 1, 0], bk))
    up = np.cross(ac, bk)
    return np.array([(p - at) @ ac, (p - at) @ up, (p - at) @ bk]) * 100

def inside(d, p, sc=1.04):
    out = []
    for b in range(len(d["r"])):
        r = d["r"][b] * sc; w = d["across"][b]; ww = w @ w; at = d["at"][b]
        c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
        dd = r - np.linalg.norm(p - c)
        if dd > 0: out.append("b%d:%.1f" % (b, dd * 100))
    return ",".join(out)

def depth(d, p, sc=1.04, nb=11):
    """How far p is inside the union of balls 0..nb-1 (cm, >0 inside)."""
    best = -1e9
    for b in range(nb):
        r = d["r"][b] * sc; w = d["across"][b]; ww = w @ w; at = d["at"][b]
        c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
        best = max(best, r - np.linalg.norm(p - c))
    return best * 100

def view2(x):
    """The chain as the back-view camera sees it (image x right = world -X, y up; cm)."""
    return np.c_[-x[:, 0], x[:, 1]] * 100

def turns2(x):
    """Signed turn at points 1..6 of the chain as seen from behind (deg), and each link's seen length (cm)."""
    p = view2(x); l = np.diff(p, axis=0); L = np.linalg.norm(l, axis=1)
    t = [math.degrees(math.atan2(l[i, 0] * l[i + 1, 1] - l[i, 1] * l[i + 1, 0], l[i] @ l[i + 1])) for i in range(6)]
    return np.array(t), L
