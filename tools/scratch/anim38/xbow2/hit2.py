"""Where the left arm goes into her: python hit.py clip tag f..."""
import sys; from pathlib import Path
W = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(W / "tools/anim"))
import numpy as np
from skin import Body
from motion import Measure
SIDE = "r" if "--r" in sys.argv else "l"; sys.argv = [a for a in sys.argv if a != "--r"]
b = Body.heroine(jiggle=True); m = Measure(b)
c = b.clip(sys.argv[1], W / "tools/anim/out" / ("anim38_her" + sys.argv[2])); Gs = b.frames(c)
nm = np.array(b.sk.names)
for f in map(int, sys.argv[3:]):
    P = b.pose(Gs[f]); dist, along, hit, brst, near = m.contact(P)[SIDE]
    pts = m.arm[SIDE][0]
    ok = np.isfinite(dist) & (along >= 0.35)
    i = np.nonzero(ok)[0][np.argmin(dist[ok])]
    v = pts[i]; n = near[i]
    print(f"f{f}: {-dist[i]*1000:.1f} mm, arm vert along {along[i]:.2f} ({nm[b.J[v, b.W[v].argmax()]]}) at {np.round(P[v]*100,1)} into {nm[b.J[n, b.W[n].argmax()]]} breast={bool(m.breast[n])} at {np.round(P[n]*100,1)}")
