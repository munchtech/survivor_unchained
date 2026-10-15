"""Her lower lip's inner roll repainted as one smooth wet band, in a face's paint (version C, judged 14 October 2026).

With her mouth open (mouth_open .6) the inside of her lower lip shows, from where her lips meet back to her mouth's
inside. Own's paint there (laid from a portrait with her mouth shut) was a patchwork: a flat pale beige-grey patch,
a wobbly inner edge and a dark brown notch 5-7 mm right of her mouth's middle. Each texel is placed by her rest mesh
(x mm off her mouth's middle, yl mm of rest height over her lips' line, on her lower lip: what mouth_open takes down
with her jaw), and b(x) is the highest rest height at which that texel is seen with her mouth shut (B98, measured
from close-up renders, max over the neighbouring 2 mm stations, mm):

  - the hidden band: from b(x) + M0 up (ramp MW, a smoothstep), the paint is the outer lip's own colour (median of
    the lip front, linear light) times WET (deeper, rose): a smooth wet field, no texture (the shader's pores and
    sheen give it its surface). Eased out between XT0 and XT1 mm off the middle, symmetric.
  - the rest-visible slit just under it (b - SLIT_DEEP .. b + M0 + MW): the paint smoothed along x (gaussian
    SLIT_SIG mm, taken in a straightened x/yl grid at 0.1 mm) at weight SLIT_W, so the slit reads as one clean line,
    not paint noise.

Why C: the slit's texels are shared with the open roll, so any change there also shows with her mouth shut. A max
judge found C's change to the rest face invisible at 2x and a cleaner slit at 4x (smoothed 3 mm wide, 1.5 mm deep)
than the lighter variants (A, B, D).

    python tools/assets/heroine_inner_lip.py [--to DIR] [face ...]   (no faces: own; --to: write there)
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lips as hl  # noqa: E402
import heroine_mouth as hmo  # noqa: E402
import heroine_seam as hs  # noqa: E402

# (mm: the highest rest height over her lips' line seen with her mouth shut, 98th percentile, per 2 mm of x)
B98 = {-14: 1.2, -12: 0.6, -10: -1.1, -8: -0.9, -6: -1.0, -4: -1.0, -2: -0.8, 0: -1.2, 2: -1.2, 4: -0.8, 6: -0.5,
       8: -0.3, 10: -0.8, 12: -0.9, 14: 1.5}
M0, MW = 0.1, 0.4         # (mm over b(x): where the hidden band starts, its ramp)
SLIT_W, SLIT_SIG, SLIT_DEEP = 1.0, 3.0, 1.5   # (the slit's smoothing: weight, sigma along x, mm under b(x) it reaches)
XT0, XT1 = 10.0, 13.0     # (mm off her mouth's middle: full, none)
WET = np.array([0.51, 0.43, 0.45])   # (linear: the hidden band's colour as a share of the outer lip's)
OPEN_DOWN = 0.001    # (m: mouth_open's drop that tells her lower lip)
X_END = 0.0205       # (m off her mouth's middle: the lip's reach)


def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return 255.0 * np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def roll(n):
    """Per texel of an n x n paint: (x mm off her mouth's middle, yl mm of rest height over her lips' line, isl: on the
    lower lip's main island)."""
    js, binc = hs._load(hl.GLB)
    hm, hp = hmo._prim(js, "skin_head")
    names = hm.get("extras", {}).get("targetNames", [])
    a = hp["attributes"]
    P = hs._read(js, binc, a["POSITION"]).astype(np.float64)
    UV = hs._read(js, binc, a["TEXCOORD_0"]).astype(np.float64)
    T = hs._read(js, binc, hp["indices"]).astype(np.int64).reshape(-1, 3)
    D = hs._read(js, binc, hp["targets"][names.index("mouth_open")]["POSITION"]).astype(np.float64)
    line = hmo.lips_line(P, D)
    sel = hl._tris(P, T, (0.04, line - 0.02, line + 0.01))
    G = hl._scan(UV[T[sel]] * n, n, n, np.concatenate([P, D], 1)[T[sel]], lambda new, old: np.zeros(len(new), bool))
    mid = float(np.median(P[(np.abs(P[:, 1] - line - 0.004) < 0.008) & (np.abs(P[:, 0]) < 0.03) & (P[:, 2] > 0.085), 0]))
    x, y, z = G[..., 0] - mid, G[..., 1], G[..., 2]
    # (her lower lip: what mouth_open takes down with her jaw, over 1 mm; her upper lip's inside stays)
    low = ~np.isnan(x) & (G[..., 4] < -OPEN_DOWN) & (y < line + 0.002) & (np.abs(x) < X_END + 0.002) & (z > 0.075)
    lab, _ = ndimage.label(low)
    # (float32 as measured, so the judged paint is reproduced exactly)
    return (x.astype(np.float32) * 1000, (y - line).astype(np.float32) * 1000, lab == 1)


def paint(img, x, yl, isl):
    """img (sRGB 0-255, n x n x 3) with her lower lip's inner roll repainted (x, yl, isl from roll)."""
    L = lin(img.astype(np.float64))
    BX = np.arange(-14, 15, 2.0)
    bv = np.array([B98[int(v)] for v in BX])
    bmax = np.array([max(bv[max(i - 1, 0):i + 2]) for i in range(len(bv))])
    b = np.interp(np.nan_to_num(x, nan=99), BX, bmax, left=3, right=3)
    lipm = isl & (yl > -4.6) & (yl < -3.6) & (np.abs(x) < 8)
    base = np.median(L[lipm], 0)
    band = base * WET
    t = np.clip((np.nan_to_num(yl, nan=-99) - b - M0) / MW, 0, 1)
    w = t * t * (3 - 2 * t)
    ax = np.abs(np.nan_to_num(x, nan=99))
    v = np.clip((ax - XT0) / (XT1 - XT0), 0, 1)
    w *= 1 - v * v * (3 - 2 * v)
    w *= isl
    O = L * (1 - w[..., None]) + band * w[..., None]
    # the slit: straighten into (x, yl) at 0.1 mm, smooth along x, sample back
    NX, NY, X0, Y0 = 400, 60, -20.0, 1.5
    gi = (Y0 - yl) / 0.1
    gj = (x - X0) / 0.1
    ok = isl & np.isfinite(gi) & (gi >= 0) & (gi < NY - 1) & (gj >= 0) & (gj < NX - 1)
    S = np.zeros((NY, NX, 3))
    N = np.zeros((NY, NX))
    np.add.at(S, (gi[ok].astype(int), gj[ok].astype(int)), L[ok])
    np.add.at(N, (gi[ok].astype(int), gj[ok].astype(int)), 1)
    Sm = ndimage.gaussian_filter1d(S, SLIT_SIG / 0.1, axis=1)
    Nm = ndimage.gaussian_filter1d(N, SLIT_SIG / 0.1, axis=1)
    G = Sm / np.maximum(Nm, 1e-6)[..., None]
    sm = np.stack([ndimage.map_coordinates(G[..., k], [gi[ok], gj[ok]], order=1) for k in range(3)], -1)
    ys, bb = yl[ok], b[ok]
    u = np.clip((ys - (bb - SLIT_DEEP)) / 0.4, 0, 1) * np.clip((bb + M0 + MW - ys) / 0.3, 0, 1)
    u = u * u * (3 - 2 * u) * SLIT_W * (1 - v[ok] * v[ok] * (3 - 2 * v[ok]))
    O[ok] = O[ok] * (1 - u[:, None]) + sm * u[:, None]
    return srgb(O), base, w


def main():
    a = sys.argv[1:]
    to = None
    if "--to" in a:
        i = a.index("--to")
        to = a[i + 1]
        del a[i:i + 2]
    faces = a or ["own"]
    files = hl.paints()
    cache = {}
    for f in faces:
        src = os.path.join(hl.TEX, files[f])
        img = np.asarray(Image.open(src).convert("RGB"))
        n = img.shape[0]
        if n not in cache:
            cache[n] = roll(n)
        out, base, w = paint(img, *cache[n])
        dst = os.path.join(to, files[f]) if to else src
        Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)
        print("INNER_LIP: %s: the hidden band painted on %d texels (outer lip linear %s); written %s"
              % (f, int((w > 0.01).sum()), np.round(base, 3), dst))


if __name__ == "__main__":
    main()
