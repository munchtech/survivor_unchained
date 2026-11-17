"""hidden.py SHOTDIR NLEGS [LEG LO HI]: T4, "is the blade hidden behind her legs". METHOD: geometric, from views.log (BLADE gw/tw world,
kn knees, BODY2 hips [0,1] and ankles [2,3]; camera from SCR2 via simlog.proj). Per frame, 20 points along the blade; a point is occluded
when its screen position is within 12 px (tuned: 9 missed the judged 45..51 window, 14 over-flags) of either leg's hip->knee->ankle screen polyline AND the blade point is farther from the camera
(zc) than the nearest leg point minus TOL=0.15 m (leg thickness; the line is the bone, not the surface). hidden = occluded fraction >= 0.6. T4 fails on a run of > 3 consecutive hidden frames in -10..+59.
Prints per leg the hidden runs; with LEG LO HI prints per-frame fractions."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from simlog import load, proj, CZ
PX = 12.0; NS = 20; FR = 0.6; TOL = 0.15  # TOL m: legs are ~0.15 m thick, so the leg surface is that much nearer the camera than the skeleton line
def zc(p, O): return -((p - O) @ CZ)
def frac(r):
    O = r["O"]; b = r["body"]
    legs = [np.array([b[0], r["kn"][0], b[2]]), np.array([b[1], r["kn"][1], b[3]])]
    # dense world samples along each leg polyline (screen proximity is tested per sample point)
    lp = []
    for l in legs:
        for a, c in zip(l[:-1], l[1:]):
            for t in np.linspace(0, 1, 25): lp.append(a + (c - a) * t)
    lp = np.array(lp); ls = np.array([proj(p, O) for p in lp]); lz = np.array([zc(p, O) for p in lp])
    occ = 0
    for s in np.linspace(0.05, 1.0, NS):
        w = r["gw"] + (r["tw"] - r["gw"]) * s; sp = proj(w, O); d = np.hypot(*(ls - sp).T)
        near = d <= PX
        if near.any() and zc(w, O) > lz[near].min() - TOL: occ += 1
    return occ / NS
def runs(h):
    out = []; i = 0
    while i < len(h):
        if h[i][1]:
            j = i
            while j + 1 < len(h) and h[j + 1][1] and h[j + 1][0] == h[j][0] + 1: j += 1
            out.append((h[i][0], h[j][0])); i = j + 1
        else: i += 1
    return out
if __name__ == "__main__":
    R = load(sys.argv[1]); n = int(sys.argv[2]); legs = [int(sys.argv[3])] if len(sys.argv) > 3 else range(n)
    lo, hi = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (-10, 59)
    fails = 0
    for L in legs:
        s = 60 + 60 * L; fr = [(k - s, frac(R[k])) for k in range(s + lo, s + hi + 1) if k in R]
        if len(sys.argv) > 3: print(" ".join(f"{k:+d}:{f:.2f}" for k, f in fr))
        ru = runs([(k, f >= FR) for k, f in fr]); bad = [r for r in ru if r[1] - r[0] + 1 > 3]; fails += bool(bad)
        print(f"L{L}: hidden frames {sum(f >= FR for _, f in fr)}/{len(fr)}; runs " + (", ".join(f"{a:+d}..{b:+d}({b-a+1})" for a, b in ru) or "none") + ("  T4 FAIL" if bad else ""))
    print(f"T4 fails: {fails} leg(s)")
