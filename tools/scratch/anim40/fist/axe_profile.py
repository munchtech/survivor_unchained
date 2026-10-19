"""The viking_axe's haft profile along its line (as Arms.Make lays it): per 10 mm slice, half-extents in the grip's frame."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools" / "assets"))
import grip_conform as gc
pc = gc.load(sys.argv[1] if len(sys.argv) > 1 else "viking_axe", path=sys.argv[2] if len(sys.argv) > 2 else None)
sp = gc.spec(); t0, t1 = pc.band(gc.piece_cfg(sp, pc.row, pc.id))
m, cl, e1, e2, t, R = pc.frame(t0, t1)
print("mm/unit", pc.mm, "band", t0, t1, "t range", t.min(), t.max(), "anchor", pc.anchor is not None)
Rl = pc.local()[1]
for a in np.arange(np.floor(t.min() / 10) * 10, t.max(), 10):
    s = (t >= a) & (t < a + 10)
    if s.sum() < 3: continue
    c = cl(np.array([min(max(a + 5, t0), t1)]))[0]
    Q = Rl[s] - c
    u, v = (Q @ e1) * pc.mm, (Q @ e2) * pc.mm
    print(f"{a:7.0f} n{s.sum():5d}  u {u.min():7.1f}..{u.max():6.1f}  v {v.min():7.1f}..{v.max():6.1f}")
