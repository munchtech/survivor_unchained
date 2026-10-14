"""Her lower lip's inner roll painted as one smooth wet band, in a face's paint (solver smile3, 14 October 2026).

With her mouth open (mouth_open .6) the inside of her lower lip shows, from where her lips meet back to her mouth's
inside. Own's paint there (laid from a portrait with her mouth shut) was a patchwork: a flat pale beige-grey patch,
more skin than wet lip, with a wobbly inner edge and a dark brown notch 5-7 mm right of her mouth's middle. This
repaints that roll by her rest mesh, not by the old paint: each texel's place across the roll (s: its rest height
over Y_DRY under her lips' line, on her lower lip, what mouth_open takes down with her jaw; at least S_DEEP1 where
it is hidden at rest, seen from in front) sets its colour. (At rest that band is the top of her lower lip where her
lips meet; with her mouth open it turns up and shows as the roll's inside: own's paint there, 1-5 mm under her
lips' line, measured by a banded test paint.)

  - s under DRY - SOFT/2: her paint as it was (the outer lip);
  - over the dry/wet line (s DRY) (SOFT wide, a smoothstep, not an edge) the wet roll: the outer lip's own colour made deeper
    and more saturated toward rose (WET, linear light), its base darkening smoothly to DEEP of it by S_DEEP;
  - one thin wet shine along the roll's crest (SHINE_S, SHINE_W wide, SHINE brighter), never lighter than the
    outer lip's front;
  - eased out toward her mouth's corners (full to X_FULL off her mouth's middle, none past X_END), symmetric.

No texture is kept on the roll (a smooth field; the shader's pores and sheen give it its surface).

    python tools/assets/heroine_inner_lip.py [--to DIR] [face ...]   (no faces: own; --to: write there)
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lips as hl  # noqa: E402
import heroine_mouth as hmo  # noqa: E402
import heroine_seam as hs  # noqa: E402

Y_DRY = -0.0040     # (m: the dry/wet line's middle, at rest under her lips' line: the meeting's band over it
                    # turns up and shows inside her open mouth (mouth_open .6: 1-5 mm under it))
DRY = 0.0          # (s of the dry/wet line's middle)
SOFT = 0.0010       # (m: the dry/wet line's width)
WET = np.array([0.62, 0.42, 0.48])   # (linear: the wet roll's colour as a share of the outer lip's)
DEEP, S_DEEP0, S_DEEP1 = 0.75, 0.0010, 0.0035   # (the roll darkening to DEEP between these, m up from the line)
SHINE, SHINE_S, SHINE_W = 0.06, 0.0007, 0.00025  # (the crest's shine: share brighter, where, sigma; m)
X_FULL, X_END = 0.016, 0.0205       # (m off her mouth's middle)
OPEN_DOWN = 0.001    # (m: mouth_open's drop that tells her lower lip)
HIDE = 0.0003       # (m: a texel this far behind her face's front, seen from in front at rest, is hidden)


def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return 255.0 * np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def roll(n):
    """Per texel of an n x n paint: (s, m up her lower lip from the dry/wet line (her rest height over Y_DRY under her
    lips' line; past S_DEEP1 where hidden at rest, seen from in front), NaN off her lower lip; |x| off her mouth's
    middle; her lips' line)."""
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
    # (hidden at rest, seen from in front: tucked behind her upper lip, or back in her mouth: all wet and deep)
    F = hl.front(P, UV, T)
    zf = hl.sample(np.nan_to_num(F[..., 2], nan=-1.0), hl.row(np.nan_to_num(y)), hl.col(np.nan_to_num(G[..., 0])))
    hidden = low & (zf - z > HIDE)
    s = (y - line) - Y_DRY
    s = np.where(hidden, np.maximum(s, S_DEEP1), s)
    s[~low | (s < -0.003)] = np.nan
    ax = np.abs(x)
    return s, ax, line


def paint(img, s, ax):
    """img (sRGB 0-255, n x n x 3) with her lower lip's inner roll repainted (s, ax from roll)."""
    L = lin(img.astype(np.float64))
    lip = np.isfinite(s) & (s < -0.001) & (s > -0.003) & (ax < X_FULL)
    base = np.median(L[lip], axis=0)
    t = np.clip((np.nan_to_num(s, nan=-1) - (DRY - SOFT / 2)) / SOFT, 0, 1)
    wet_w = t * t * (3 - 2 * t)
    u = np.clip((np.nan_to_num(s, nan=0) - S_DEEP0) / (S_DEEP1 - S_DEEP0), 0, 1)
    dark = 1 - (1 - DEEP) * u * u * (3 - 2 * u)
    shine = 1 + SHINE * np.exp(-0.5 * ((np.nan_to_num(s, nan=1) - SHINE_S) / SHINE_W) ** 2)
    new = (base * WET)[None, None, :] * (dark * shine)[..., None]
    ax = np.nan_to_num(ax, nan=1.0)
    v = np.clip((ax - X_FULL) / (X_END - X_FULL), 0, 1)
    w = (wet_w * (1 - v * v * (3 - 2 * v)) * np.isfinite(s))[..., None]
    out = L * (1 - w) + new * w
    return srgb(out), base


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
        s, ax, line = cache[n]
        out, base = paint(img, s, ax)
        dst = os.path.join(to, files[f]) if to else src
        Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)
        print("INNER_LIP: %s: the roll repainted on %d texels (outer lip linear %s); written %s"
              % (f, int((np.isfinite(s) & (s > DRY - SOFT / 2) & (ax < X_END)).sum()), np.round(base, 3), dst))


if __name__ == "__main__":
    main()
