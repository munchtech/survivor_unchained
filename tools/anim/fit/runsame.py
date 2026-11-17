"""runsame.py SHOTS A B NLEGS [lo hi]: per leg, the largest frame-for-frame difference in the blade's screen angle a,
world pitch, tilt and inward over lo..hi (default the run, +7..+35), from ana10.py's traces (game truth, not pixels)."""
import sys, os, subprocess
S, a, b, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
lo, hi = (sys.argv[5], sys.argv[6]) if len(sys.argv) > 6 else ('7', '35')
here = os.path.dirname(os.path.abspath(__file__))
def tr(t, leg):
    o = subprocess.run([sys.executable, os.path.join(here, 'ana10.py'), str(leg), lo, hi], env={**os.environ, 'LOG': f"{S}/{t}"}, capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout
    rows = []
    for ln in o.splitlines():
        t_ = ln.replace('(', ' ').replace(')', ' ').split()
        if len(t_) < 10 or t_[0] != 'hd': continue
        g = lambda k: float(t_[t_.index(k) + 1])
        rows.append((g('a'), g('pitch'), g('tilt'), g('inw')))
    return rows
worst = 0
for leg in range(n):
    x, y = tr(a, leg), tr(b, leg)
    m = [max((abs(p[i] - q[i]) for p, q in zip(x, y)), default=0) for i in range(4)]
    worst = max(worst, max(m))
    print(f"{leg:2d} frames {min(len(x), len(y))} max|d| a {m[0]:.1f} pitch {m[1]:.1f} tilt {m[2]:.1f} inw {m[3]:.1f}")
print(a, b, "worst", f"{worst:.1f}")
