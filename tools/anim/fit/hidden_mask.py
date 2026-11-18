"""hidden_mask.py SHOTDIR NLEGS [LEG LO HI]: T4 by pixels (run with --blade-mask). views.log has one `BMASK vis tot` per frame (after that frame's
SCR2): vis = blade pixels still magenta in the full scene render, tot = blade pixels alone. hidden = vis/tot < 0.40; tot < 30 px = blade off screen
or end-on, not hidden. Per leg the hidden runs over -10..+59 (leg k starts at frame 60+60k, as hidden.py); T4 fails on a run > 3 frames.
With LEG LO HI prints per frame vis tot share."""
import sys
TH = 0.40; MINTOT = 30
def load(d):
    R = {}; fi = -1
    for ln in open(d + "/views.log", errors="ignore"):
        if ln.startswith("SCR2 "): fi += 1
        elif ln.startswith("BMASK ") and fi >= 0:
            t = ln.split(); R[fi] = (int(t[1]), int(t[2]))
    return R
def hid(v, t): return t >= MINTOT and v / t < TH
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
        s = 60 + 60 * L; fr = [(k - s, R[k]) for k in range(s + lo, s + hi + 1) if k in R]
        if len(sys.argv) > 3:
            for k, (v, t) in fr: print(f"{k:+d} vis {v} tot {t} share {v / t if t else 0:.2f}")
        ru = runs([(k, hid(v, t)) for k, (v, t) in fr]); bad = [r for r in ru if r[1] - r[0] + 1 > 3]; fails += bool(bad)
        print(f"L{L}: hidden frames {sum(hid(v, t) for _, (v, t) in fr)}/{len(fr)}; runs " + (", ".join(f"{a:+d}..{b:+d}({b-a+1})" for a, b in ru) or "none") + ("  T4 FAIL" if bad else ""))
    print(f"T4 fails: {fails} leg(s)")
