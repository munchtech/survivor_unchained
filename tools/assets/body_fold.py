"""Where the body's stepped cel rim falls on an inside fold: body_p1's fold.png, for the skin shader's rim_fold_map.

The skin's stepped rim (cel.gdshaderinc cel_rim_add) lights where the surface turns away from the camera on the
key's side. Against the background that is her outline (kept). Where the turned surface faces more of her own body a
few centimetres away (the breast's underside over the ribs, the buttock's crease, between the thighs), the rim drew a
cream line inside her form (13 Nov, owner: "the cream line under the breast"; elsewhere it "looks good": kept). Per point of
the body: 1 on the breast's underside (in front of her ribs, from her breasts' lowest height to a little past the widest, across their
width, turned down), as a gray map in the body's UV.

    python tools/assets/body_fold.py godot/art/people/body_p1/body.glb godot/art/people/body_p1/fold.png

No Blender: the points, normals and UVs from the glb, as heroine_spark.py.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
from heroine_ao_seam import raster  # noqa: E402
from heroine_thin import ease  # noqa: E402

NEAR, FAR = 0.05, 0.10     # (metres to the facing surface: the breast's underside over her ribs 1-9 cm)
CONE = 0.5                 # (cos of the cone round the normal: within 60 degrees)
MIN_D = 0.006              # (closer is her own surface's next ring or a seam's twin)
Y0, Y1, X1 = 1.29, 1.43, 0.17   # (body_p1, metres: her breasts' crease 1.30-1.31, widest 1.36, outer side 0.15, armpit 0.17 at 1.40; under 1.30 her ribs slope down 0.15-0.3;
                                # the top past the widest: turned down there is still the underside, turned up (ny > 0) the factor drops it)
X2, Z2 = 0.19, 0.08          # (the breast's own outer side, in front of the ribs' side: out to 0.19 where z is 0.04-0.08 or more; judge r2's stub on the
                           # right breast's lower outer side sat at 0.15-0.17, the ribs' side and the outline under the armpit are at z under 0.04)
EASE = 0                   # (no easing over the surface: 3 rings left the map at 0.35-0.95 on the line at the cleavage end and the lower
                           # outer side (V3, lead 4), their points 1-3 cm inside the zone (y 1.34-1.38, turned 0.2-0.45 down); the 3 cm ramps ease it)
SIZE = 1024
BODY = ("Material_0.001", "skin")                        # (the body's own skin surface: body_p1's, heroine.glb's)
SKIN = BODY + ("skin_graft", "skin_head")                # (what can face it: all her skin)


def prims(js, binc, mats_wanted):
    mats = [m.get("name") for m in js["materials"]]
    for p in (p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] in mats_wanted):
        g = lambda k: hs._read(js, binc, p["attributes"][k])
        n = g("NORMAL").astype(np.float64)
        yield (g("POSITION").astype(np.float64), n / np.linalg.norm(n, axis=1, keepdims=True), g("TEXCOORD_0"),
               hs._read(js, binc, p["indices"]).astype(np.int64).reshape(-1, 3))


def fold_dist(P, N, Q, M):
    """Per point of P: the distance to the nearest point of Q in its normal's cone whose normal faces back."""
    tree = cKDTree(Q)
    out = np.full(len(P), np.inf)
    for i0 in range(0, len(P), 4000):
        idx = tree.query_ball_point(P[i0:i0 + 4000], FAR)
        for j, nb in enumerate(idx):
            if not nb:
                continue
            i = i0 + j
            nb = np.asarray(nb)
            d = Q[nb] - P[i]
            r = np.linalg.norm(d, axis=1)
            ok = r > MIN_D
            u = d[ok] / r[ok, None]
            ok2 = ((u @ N[i]) > CONE) & ((M[nb[ok]] * u).sum(1) < 0.0)
            if ok2.any():
                out[i] = r[ok][ok2].min()
    return out


def ramp(v, a, b):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def underbust(P, N):
    """The breast's underside only (the owner, 13 Nov: the cream line elsewhere, on her outline and in her other folds
    (armpit, buttock crease, inner thighs, elbows), looks good and stays): in front of her ribs, from her breasts'
    lowest height to a little past the widest, across their width, the surface turned down."""
    x, y, z = np.abs(P[:, 0]), P[:, 1], P[:, 2]
    side = np.maximum(1 - ramp(x, X1 - 0.03, X1), (1 - ramp(x, X2 - 0.03, X2)) * ramp(z, Z2 - 0.04, Z2))
    return (ramp(y, Y0, Y0 + 0.03) * (1 - ramp(y, Y1 - 0.03, Y1)) * side * ramp(z, 0.0, 0.03)
            * ramp(-N[:, 1], -0.05, 0.10))   # (not turned up: where the underside turns sideways into the cleavage and the outer side, judge r1)


def main(glb, png):
    js, binc = hs._load(glb)
    P, N, UV, T = next(prims(js, binc, BODY))
    # The zone alone, not the facing-surface distance (13 Nov, measured on body_p1: of the underside's points turned
    # 0.1-0.35 down, where the rim draws at a chest camera, the median distance to her ribs in the cone is 24 cm and 20%
    # of the zone has none within 30 cm, the breast's front-lower curve: a distance test left the line under the breast
    # at 0.9 of its strength on V3). fold_dist stays for a later fold beyond the breast.
    x = underbust(P, N)
    x = x * x * (3 - 2 * x)
    if EASE:
        x = ease(x, T, EASE)
    w = raster(UV, T, x, SIZE)
    g = (np.clip(w, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(np.stack([g, g, g], -1), "RGB").save(png)   # (gray in RGB: the shader reads red)
    print("FOLD %s: %d points, %.1f%% fold (over 0.5), %.1f%% of texels over 0.5" %
          (png, len(P), 100 * (x > 0.5).mean(), 100 * (w > 0.5).mean()))
    return P, x


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
