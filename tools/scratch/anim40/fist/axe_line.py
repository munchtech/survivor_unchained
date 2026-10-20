import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools" / "assets"))
import grip_conform as gc
pc = gc.load("viking_axe")
t0, t1 = pc.band(gc.piece_cfg(gc.spec(), pc.row, pc.id))
m, cl, e1, e2, t, R = pc.frame(t0, t1)
a = cl(np.array([-80.0]))[0]; b = cl(np.array([150.0]))[0]
P0 = pc.G + a + pc.D * (-80 / pc.mm); P1 = pc.G + b + pc.D * (150 / pc.mm)
d = (P1 - P0) / np.linalg.norm(P1 - P0)
print("tilt deg", np.degrees(np.arccos(d @ pc.D)))
print("centre off at t=0 mm", np.linalg.norm(cl(np.array([0.0]))[0]) * pc.mm)
print("e1 vs piece X", e1 @ pc.turn[0], "e2 vs Z", e2 @ pc.turn[2], "D", pc.D, "turn", pc.turn)
# the haft line's direction components in piece frame
print("haft dir in piece frame (X mid, Y long, Z short):", pc.turn @ d)
# extents along d vs D
P = pc.P
print("extent D", np.ptp(P @ pc.D) * pc.mm, "extent d", np.ptp(P @ d) * pc.mm)
