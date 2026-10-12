"""A crop of the review's frame drawn here, her faces coloured by where
their points lay at rest (hue: across the knee, x; light: shaded), with the
mesh's edges: to see which of her skin shows at a fold.

    python tickview.py <out.png> <deg> <x> <y> <half> <variant> ... [VIEW=side]
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import colorsys  # noqa: E402
import tick  # noqa: E402
from sweep import pose, knee, elbow  # noqa: E402

out, deg, px, py, half = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
view = os.environ.get("VIEW", "side")
joint = os.environ.get("JOINT", "knee")
SC = int(os.environ.get("SC", "8"))
tick.RES = SC
tiles = []
for v in sys.argv[6:]:
    b = tick.variant_body(v)
    edits = [knee("l", deg), knee("r", deg)] if joint == "knee" else [elbow("l", deg), elbow("r", deg)]
    G = pose(b, edits)
    bone, zoom = ("calf_l", 4.5) if joint == "knee" else ("lowerarm_l", 5.0)
    j = b.sk.index[bone]
    target = G[j][:3, 3]
    P = b.pose(G)
    near = np.linalg.norm(P - target, axis=1) < 0.17
    T = b.T[near[b.T].all(1)]
    E, f, r, u = tick.camera(target, view, zoom)
    ids, depth, bary = tick.raster(P, T, E, f, r, u, size=400 * SC)
    x0, x1 = int((px - half) * SC), int((px + half) * SC)
    y0, y1 = int((py - half) * SC), int((py + half) * SC)
    ids, bary = ids[y0:y1, x0:x1], bary[y0:y1, x0:x1]
    vis = ids >= 0
    tri = np.where(vis, ids, 0)
    rest_knee = b.rest[j][:3, 3]
    lat = (b.P[:, 0] - rest_knee[0]) * 100        # cm across (her left +)
    ln = bary[..., 0] * lat[T[tri, 0]] + bary[..., 1] * lat[T[tri, 1]] + bary[..., 2] * lat[T[tri, 2]]
    gn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    gn /= np.linalg.norm(gn, axis=1, keepdims=True) + 1e-12
    sh = np.clip(gn[tri] @ tick.KEY, 0, 1) * 0.6 + 0.4
    img = np.zeros(ids.shape + (3,))
    hue = np.clip((ln + 2) / 10, 0, 1) * 0.8        # x from -2 (red) to 8 cm (violet)
    for yy, xx in zip(*np.nonzero(vis)):
        pass
    H = hue[vis]
    rgb = np.array([colorsys.hsv_to_rgb(h, 0.7, 1.0) for h in H])
    img[vis] = rgb * sh[vis][:, None]
    # edges: where the face changes and both are hers
    e = np.zeros(vis.shape, bool)
    e[:-1, :] |= (ids[:-1, :] != ids[1:, :])
    e[:, :-1] |= (ids[:, :-1] != ids[:, 1:])
    img[e & vis] *= 0.55
    tiles.append((img * 255).astype(np.uint8))
    print(v, "done", flush=True)
W = sum(t.shape[1] for t in tiles) + 4 * (len(tiles) - 1)
o = np.full((tiles[0].shape[0], W, 3), 255, np.uint8)
x = 0
for t in tiles:
    o[:, x:x + t.shape[1]] = t
    x += t.shape[1] + 4
Image.fromarray(o).save(out)
print("wrote", out)
