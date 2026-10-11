"""Which of her points make the tick: the faces drawn round a pixel of the
review's frame (400 px) at a knee bend, their points' weights and where
they lie at rest in the knee's frame (x across, y down the calf, z back).

    python tickprobe.py <variant> <deg> <x> <y> [half px] [view]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import tick  # noqa: E402
from sweep import pose, knee  # noqa: E402

v, deg, px, py = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
half = float(sys.argv[5]) if len(sys.argv) > 5 else 3
view = sys.argv[6] if len(sys.argv) > 6 else "side"
b = tick.variant_body(v)
b._ring2 = tick.ring_neighbours(b.T, len(b.P))
G = pose(b, [knee("l", deg), knee("r", deg)])
m = tick.measure(b, G, "calf_l", view, 4.5)
flip_px, notch_px, edge, ids, T = m["_pix"]
R = tick.RES
win = ids[int((py - half) * R):int((py + half) * R), int((px - half) * R):int((px + half) * R)]
faces = np.unique(win[win >= 0])
pts = np.unique(T[faces].ravel())
I = b.sk.index
th, ca, sh = I["thigh_l"], I["calf_l"], I.get("calf_share_l", -1)
rest = b.rest
kn = rest[ca][:3, 3]
R0 = rest[ca][:3, :3]       # the calf's rest frame
P = b.pose(G)
print(f"{len(faces)} faces, {len(pts)} points round ({px},{py})")
print("  pt     thigh  calf  share other |  rest from the knee (cm) x y z  | posed (cm)")
for p in pts:
    w = {I_: 0.0 for I_ in (th, ca, sh)}
    other = 0.0
    for k in range(4):
        j = b.J[p, k]
        if j in w:
            w[j] += b.W[p, k]
        else:
            other += b.W[p, k]
    loc = (b.P[p] - kn) * 100
    pl = (P[p] - kn) * 100
    print(f"{p:6d}  {w[th]:.3f} {w[ca]:.3f} {w.get(sh, 0):.3f} {other:.3f} | {loc[0]:+6.2f} {loc[1]:+6.2f} {loc[2]:+6.2f} | {pl[0]:+6.2f} {pl[1]:+6.2f} {pl[2]:+6.2f}")
