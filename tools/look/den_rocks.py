#!/usr/bin/env python3
"""The den's round open-floor boulders (den r15, sheet O1r): the O1 painting (set_src/O1.png, the ChatGPT imaging route,
set_src/PROVENANCE.txt) rebuilt in the target's hand and value band, at twice O1's texels, in O1's exact layout (the same
normalised rects, so set.json's O1 pieces place it unchanged: DungeonDress.Set.cs loads O1r.png for the "O1r" key).

  python tools/look/den_rocks.py build    set_src/O1.png -> art/dungeon/den/set/O1r.png (+ .import, lossless, mipmaps)
  python tools/look/den_rocks.py check    O1r's size against set.json's O1, its value/hue ramp, its ink

Why (R14 judge item 1): r14 drew these stones by blurring O1 to a high mip and painting a procedural lit top over it
(den_set.gdshaderinc rock_k): 24 px texel blocks at the play camera, no ink, no planes, no moss detail, an olive cast
h 70-72. The targets' (den_room.png) round stones: grey shade (L .20-.30, C < .01), warm ochre lit planes (L .40-.60,
h 58-63, C rising with L to .07-.10), dark moss on the crown, a dark ink line round the silhouette and down the cracks.

The rules (no hand fixes on the output; every number here):
- LAYOUT: den_set's own key, scale and piece cut (its functions), resampled at S x OBJ_PPM, each piece pasted at S x its
  O1 rect, so O1r's UVs are O1's to the texel.
- RAMP: the painting's own value (OKLab L) keeps every stroke: stretched from its 2nd-98th percentiles to RAMP_L with a
  gamma (more of the stone in shade, as the target's 60 % under L .35), then hue and chroma by value (RAMP_*), the
  painting's mauve shade gone.
- MOSS: where the painting is yellow-green (h 75-150, C > .035, soft-edged), a darker, cooler olive (MOSS_*), its strokes kept.
- FORM: an unsharp mask on L (the facets' planes and edges), the piece's lower part darkened (the belly in its own shadow).
- INK: a dark line INK_W texels inside the alpha edge (soft inner edge), the painting's cracks (L under its own blur by
  more than CRACK_T) darkened toward the ink.
"""
import json, os, sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import den_set as ds  # noqa: E402

S = 2                                   # O1r texels per O1 texel (O1 is 96 px/m: the boulders draw 0.7-1 texel per screen px)
RAMP_L = (0.22, 0.66, 1.0)             # stone L from, to, gamma (t ** gamma: the mass into shade)
RAMP_C0, RAMP_CK, RAMP_CMAX = 0.28, 0.17, 0.075   # chroma = (L - C0) * CK, at most CMAX (grey under C0)
RAMP_H_LIT, RAMP_H_SHADE = 63.0, 55.0   # hue of the lit planes, of the grey shade (its chroma ~.006)
SHADE_C = 0.006
MOSS_H, MOSS_C, MOSS_LK, MOSS_L0 = 110.0, 0.038, 0.5, 0.04   # moss: hue, chroma, L = LK * L_src + L0
MOSS_CORE = (0.5, 0.85)                 # the moss kept where its blurred mask is over this: its fringe goes back to stone
SHARP_R, SHARP_K = 2.0 * S, 0.7         # unsharp mask radius (texels) and amount on L
BELLY = (0.62, 0.18)                    # from this share of the piece's height down, darken to (1 - this) at its foot
INK_W, INK_SOFT, INK_L, INK_C, INK_H = 2.6 * S, 1.2 * S, 0.11, 0.012, 40.0
CRACK_R, CRACK_T, CRACK_K = 3.0 * S, 0.035, 0.75


def to_oklab(rgb):
    c = rgb / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    l = lin @ np.array([0.4122214708, 0.5363325363, 0.0514459929])
    m = lin @ np.array([0.2119034982, 0.6806995451, 0.1073969566])
    s = lin @ np.array([0.0883024619, 0.2817188376, 0.6299787005])
    l_, m_, s_ = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, A, B


def from_oklab(L, A, B):
    l_ = L + 0.3963377774 * A + 0.2158037573 * B
    m_ = L - 0.1055613458 * A - 0.0638541728 * B
    s_ = L - 0.0894841775 * A - 1.2914855480 * B
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    lin = np.clip(np.dstack([r, g, b]), 0.0, 1.0)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055) * 255.0


def smooth(x0, x1, v):
    t = np.clip((v - x0) / (x1 - x0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def layout():
    """O1's pieces at S x: (colour, alpha) sheet of S x O1's size, each piece at S x its set.json rect."""
    meta = json.load(open(os.path.join(ds.OUT, "set.json"), encoding="utf-8"))
    o1 = next(s for s in meta["sheets"] if s["name"] == "O1")
    _, widest = ds.SHEETS["O1"]
    f, a = ds.key(ds.load("O1"))
    ps, _ = ds.pieces(a)
    k = ds.OBJ_PPM / (max(p[2] - p[0] for p in ps) / widest)
    f1, a1 = ds.resample(f, a, k)
    ps1, _ = ds.pieces(a1, join=max(4, round(20 * k)))
    f2, a2 = ds.resample(f, a, k * S)
    _, lab2 = ds.pieces(a2, join=max(4, round(20 * k * S)))
    W, H = o1["px"]
    F, A_ = np.zeros((H * S, W * S, 3)), np.zeros((H * S, W * S))
    assert len(ps1) == len(o1["pieces"]), "O1's pieces changed: rebuild den_set first"
    for (x0, y0, x1, y1, _), pe in zip(ps1, o1["pieces"]):
        rx, ry, cw, ch = pe["rect"]
        assert (x1 - x0, y1 - y0) == (cw, ch), f"O1 piece {pe['rect']} is not den_set's cut {(x0, y0, x1, y1)}"
        X0, Y0 = x0 * S, y0 * S
        cf, ca = f2[Y0:Y0 + ch * S, X0:X0 + cw * S], a2[Y0:Y0 + ch * S, X0:X0 + cw * S]
        cl = lab2[Y0:Y0 + ch * S, X0:X0 + cw * S]
        ids, n = np.unique(cl[ca > 0.5], return_counts=True)
        ca = ca * (cl == ids[np.argmax(n)])
        hh, ww = ca.shape
        F[ry * S:ry * S + hh, rx * S:rx * S + ww] = cf
        A_[ry * S:ry * S + hh, rx * S:rx * S + ww] = ca
    return F, A_, o1


def paint(F, A_, o1):
    L, Aa, Bb = to_oklab(F)
    C = np.hypot(Aa, Bb)
    h = np.degrees(np.arctan2(Bb, Aa)) % 360
    solid = A_ > 0.5
    moss = ((h > 75) & (h < 150) & (C > 0.035) & solid).astype(float)
    moss = smooth(MOSS_CORE[0], MOSS_CORE[1], ndimage.gaussian_filter(moss, 1.5 * S)) * solid
    stone = solid & (moss < 0.5)
    lo, hi = np.percentile(L[stone], [2, 98])
    t = np.clip((L - lo) / (hi - lo), 0, 1) ** RAMP_L[2]
    Ls = RAMP_L[0] + (RAMP_L[1] - RAMP_L[0]) * t
    # the lower part of each piece in its own shadow
    belly = np.ones_like(L)
    for pe in o1["pieces"]:
        rx, ry, cw, ch = [v * S for v in pe["rect"]]
        v = (np.arange(ch) / max(ch - 1, 1))[:, None]
        belly[ry:ry + ch, rx:rx + cw] = 1.0 - BELLY[1] * smooth(BELLY[0], 1.0, v)
    # the moss: a darker, cooler olive, its strokes kept
    Lm = MOSS_LK * L + MOSS_L0
    Lv = (Ls * (1 - moss) + Lm * moss) * belly
    # the facets: unsharp mask on the value
    Lv = Lv + SHARP_K * (Lv - ndimage.gaussian_filter(Lv, SHARP_R))
    # the cracks: the painting's own dark lines, inked
    crack = smooth(CRACK_T, 2.5 * CRACK_T, ndimage.gaussian_filter(L, CRACK_R) - L) * solid
    Lv = Lv * (1 - CRACK_K * crack) + INK_L * CRACK_K * crack
    Lv = np.clip(Lv, 0.04, 0.85)
    Cs = np.clip((Lv - RAMP_C0) * RAMP_CK, 0, RAMP_CMAX) + SHADE_C
    hs = RAMP_H_SHADE + (RAMP_H_LIT - RAMP_H_SHADE) * smooth(RAMP_C0 - 0.05, RAMP_C0 + 0.12, Lv)
    hh = hs * (1 - moss) + MOSS_H * moss
    Cc = Cs * (1 - moss) + MOSS_C * smooth(0.12, 0.4, Lv) * moss
    # the ink round the silhouette
    d = ndimage.distance_transform_edt(solid)
    ink = 1.0 - smooth(INK_W, INK_W + INK_SOFT, d)
    Lv = Lv * (1 - ink) + INK_L * ink
    Cc = Cc * (1 - ink) + INK_C * ink
    hh = np.where(ink > 0.5, INK_H, hh)
    hr = np.radians(hh)
    out = from_oklab(Lv, Cc * np.cos(hr), Cc * np.sin(hr))
    out[A_ < 1e-3] = 0.0
    return out


def build():
    F, A_, o1 = layout()
    out = paint(F, A_, o1)
    path = os.path.join(ds.OUT, "O1r.png")
    ds.save_rgba(path, out, A_)
    ds.write_import(path)
    print(f"O1r: {A_.shape[1]}x{A_.shape[0]} px ({S} x O1's {o1['px']}), {len(o1['pieces'])} stones -> {path}")


def check():
    meta = json.load(open(os.path.join(ds.OUT, "set.json"), encoding="utf-8"))
    o1 = next(s for s in meta["sheets"] if s["name"] == "O1")
    im = Image.open(os.path.join(ds.OUT, "O1r.png"))
    assert im.size == (o1["px"][0] * S, o1["px"][1] * S), f"O1r {im.size} is not {S} x O1 {o1['px']}"
    arr = np.asarray(im, dtype=np.float64)
    L, Aa, Bb = to_oklab(arr[..., :3])
    C = np.hypot(Aa, Bb)
    sel = arr[..., 3] > 250
    for lo in np.arange(0.05, 0.8, 0.1):
        m = sel & (L >= lo) & (L < lo + 0.1)
        if m.sum() > 50:
            print(f"  L {lo:.2f}-{lo + 0.1:.2f} {100 * m.sum() / sel.sum():5.1f}%  C {np.median(C[m]):.3f}  h {np.degrees(np.arctan2(Bb[m].mean(), Aa[m].mean())) % 360:5.1f}")
    print("O1r ok")


if __name__ == "__main__":
    {"build": build, "check": check}[sys.argv[1] if len(sys.argv) > 1 else "build"]()
