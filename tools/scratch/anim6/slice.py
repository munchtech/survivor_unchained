"""Her posed skin cut across the knee (planes square to the hinge, at set
distances across it, in the posed space), a row a variant, coloured by each
point's blend toward the bone below (blue 0, green 0.5, red 1): a fold's
shape and which of her skin makes it. The back of the knee to the right.

    python slice.py <out.png> <deg> <x cm,...> <variant> ...
    (CENTRE=y,z cm and SCALE=px a cm frame it; JOINT=elbow for an elbow)
"""
import colorsys
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
import tick  # noqa: E402
from sweep import pose, knee, elbow  # noqa: E402

out, deg = sys.argv[1], int(sys.argv[2])
xs = [float(v) for v in sys.argv[3].split(",")]
variants = sys.argv[4:]
joint = os.environ.get("JOINT", "knee")
SZ, SCALE = int(os.environ.get("SZ", "420")), float(os.environ.get("SCALE", "26"))
CY, CZ = [float(v) for v in os.environ.get("CENTRE", "0,0").split(",")]
grid = Image.new("RGB", (len(xs) * (SZ + 4), len(variants) * (SZ + 4)), (255, 0, 255))
for vi, v in enumerate(variants):
    b = tick.variant_body(v)
    top, bone = ("thigh_l", "calf_l") if joint == "knee" else ("upperarm_l", "lowerarm_l")
    share = bone.split("_")[0] + "_share_l"
    edits = [knee("l", deg), knee("r", deg)] if joint == "knee" else [elbow("l", deg), elbow("r", deg)]
    G = pose(b, edits)
    I = b.sk.index
    j = I[bone]
    c = G[j][:3, 3]
    P = (b.pose(G) - c) * 100
    # each point's blend toward the bone below: (below + share / 2) / (above + below + share)
    w = np.zeros((len(b.P), 3))
    for k in range(4):
        for col, n in enumerate((top, bone, share)):
            if n in I:
                w[:, col] += np.where(b.J[:, k] == I[n], b.W[:, k], 0)
    tot = w.sum(1)
    xb = np.where(tot > 1e-6, (w[:, 1] + w[:, 2] / 2) / np.maximum(tot, 1e-6), -1)
    near = np.linalg.norm(P, axis=1) < 16
    T = b.T[near[b.T].all(1)]
    for pi, x0 in enumerate(xs):
        panel = Image.new("RGB", (SZ, SZ), (20, 20, 24))
        dr = ImageDraw.Draw(panel)
        d = P[:, 0] - x0
        for t in T:
            pts, bl = [], []
            for a, bb in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                if (d[a] > 0) != (d[bb] > 0):
                    s = d[a] / (d[a] - d[bb])
                    pts.append(P[a] + s * (P[bb] - P[a]))
                    bl.append(xb[a] + s * (xb[bb] - xb[a]))
            if len(pts) == 2:
                m = (bl[0] + bl[1]) / 2
                col = (128, 128, 128) if m < 0 else tuple(int(255 * u) for u in colorsys.hsv_to_rgb(0.66 * (1 - np.clip(m, 0, 1)), 0.85, 1.0))
                p, q = pts
                dr.line([(SZ / 2 - (p[2] - CZ) * SCALE, SZ / 2 - (p[1] - CY) * SCALE),
                         (SZ / 2 - (q[2] - CZ) * SCALE, SZ / 2 - (q[1] - CY) * SCALE)], fill=col, width=2)
        dr.text((6, 6), f"{v}  x={x0:+.1f}cm", fill=(230, 230, 230))
        oz = SZ / 2 + CZ * SCALE
        oy = SZ / 2 + CY * SCALE
        dr.line([(oz - 4, oy), (oz + 4, oy)], fill=(255, 255, 0))
        dr.line([(oz, oy - 4), (oz, oy + 4)], fill=(255, 255, 0))
        grid.paste(panel, (pi * (SZ + 4), vi * (SZ + 4)))
    print(v, "done", flush=True)
grid.save(out)
print("wrote", out)
