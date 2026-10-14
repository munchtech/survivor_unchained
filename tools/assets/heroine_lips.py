"""Her upper lip's red lifted to her head's own lip border, in each face's paint.

WIP (skin r13a, 12 October 2026): --measure is sound; the warp is a first cut, NOT run on the paints. Tried on Doe
(--to): the red reaches the crease, but stretched 2.5-3x it streaks into vertical bands, her cupid's bow's pale V
was drawn down the red's middle, and the lift stops in a vertical cut at about 16-20 mm out (the crease is found
only to +-16 mm; past it the knots go non-monotonic and the column is skipped). See the hand-back for what's next.

Her head has no normal map: the line of her upper lip is her sculpt's, drawn by her head's shade (heroine_ao.png's
red: a thin crease along the vermilion border and its cupid's bow). Every face's paint puts the red of her upper lip
lower than that border (the portraits' upper lips are thinner than her sculpt's), so at the Look the crease showed
as an outline in skin above her lip (the owner, 12 October 2026). This warps each paint's upper lip upward, down her
face (her head seen from in front, the base shape: her UVs are shared and turned on her face), so its red's top
edge lies on the crease, the cupid's bow following her head's; her lip's own colour and lines kept, stretched in the
red's middle, the edge band moved nearly whole (no softer edge, no doubled one) and the skin above it to the nose
eased up. Texels her mouth hides from the front (her lips' inner sides) are left as they were.

    python tools/assets/heroine_lips.py [face ...]          (no faces: every paint in godot/art/people/head_tex)
    python tools/assets/heroine_lips.py --measure [face ...] (per 2 mm across her: mouth line, crease, red's top)

The chain: heroine_face.py's lay, heroine_jaw_cut.py, heroine_ears.py, then this. Idempotent: it measures the red's
top against the crease each time and moves it only by what's left (a rerun moves it by under LIFT_MIN, so nothing).
The other choice (the owner's, (b)): the paints left as laid and the crease eased instead (heroine_ao_softlip.py,
People.HerSoftLipAo).
"""
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
X0, X1, Y0, Y1, D = -0.035, 0.035, 1.655, 1.725, 0.0001   # (her mouth from in front: metres, a 0.1 mm grid)
LIFT_MIN = 0.0002      # (red's top under this from the crease: left)
EDGE = 0.0008          # (the band either side of the red's top moved nearly whole)
BELOW = 0.0003         # (the red's new top this far under the crease's middle: the crease its edge's shade)


def mesh():
    js, binc = hs._load(GLB)
    mats = [m.get("name") for m in js["materials"]]
    prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
    P = hs._read(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"]).astype(np.float64)
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    return P, UV, T


def _tris(P, T, box):
    c = P[T].mean(1)
    return np.where((np.abs(c[:, 0]) < box[0]) & (c[:, 1] > box[1]) & (c[:, 1] < box[2]) & (c[:, 2] > 0.03))[0]


def _scan(pts, size_x, size_y, vals, keep):
    """Rasterise triangles (pts: k x 3 x 2 grid coordinates) carrying vals (k x 3 x m); keep(new, old) picks."""
    out = np.full((size_y, size_x, vals.shape[2]), np.nan)
    for t, v in zip(pts, vals):
        x0, x1 = max(int(np.floor(t[:, 0].min())), 0), min(int(np.ceil(t[:, 0].max())), size_x - 1)
        y0, y1 = max(int(np.floor(t[:, 1].min())), 0), min(int(np.ceil(t[:, 1].max())), size_y - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        a, v0, v1 = t[0], t[1] - t[0], t[2] - t[0]
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-14:
            continue
        qx, qy = xs.ravel() + 0.5 - a[0], ys.ravel() + 0.5 - a[1]
        b1 = (qx * v1[1] - v1[0] * qy) / den
        b2 = (v0[0] * qy - qx * v0[1]) / den
        bb = np.stack([1 - b1 - b2, b1, b2], 1)
        m = (bb > -1e-4).all(1)
        if not m.any():
            continue
        new = bb[m] @ v
        yy, xx = ys.ravel()[m], xs.ravel()[m]
        old = out[yy, xx]
        take = np.isnan(old[:, 0]) | keep(new, old)
        out[yy[take], xx[take]] = new[take]
    return out


def front(P, UV, T):
    """Per pixel of the front grid (row 0 at Y1) the front-most surface's u, v, z."""
    sel = _tris(P, T, (X1 + 0.005, Y0 - 0.005, Y1 + 0.005))
    g = np.stack([(P[T[sel]][..., 0] - X0) / D, (Y1 - P[T[sel]][..., 1]) / D], -1)
    vals = np.concatenate([UV[T[sel]], P[T[sel]][..., 2:3]], -1)
    nx, ny = int(round((X1 - X0) / D)), int(round((Y1 - Y0) / D))
    return _scan(g, nx, ny, vals, lambda new, old: new[:, 2] > old[:, 2])


def in_uv(P, UV, T, n, box):
    """Per texel of an n x n map (inside box's UV bounds) its point's x, y, z; NaN where no face of the box is."""
    sel = _tris(P, T, (X1 + 0.005, Y0 - 0.005, Y1 + 0.005))
    g = UV[T[sel]] * n
    return _scan(g, n, n, P[T[sel]], lambda new, old: np.zeros(len(new), bool))


def sample(img, rows, cols):
    if img.ndim == 2:
        return ndimage.map_coordinates(img, [rows, cols], order=1, mode="nearest")
    return np.stack([ndimage.map_coordinates(img[..., c], [rows, cols], order=1, mode="nearest")
                     for c in range(img.shape[2])], -1)


def at_uv(img, u, v):
    return sample(img, v * img.shape[0] - 0.5, u * img.shape[1] - 0.5)


def row(y): return (Y1 - y) / D - 0.5
def col(x): return (x - X0) / D - 0.5


def lines(F, ao_r):
    """Per column of the front grid: her mouth line (the AO's deepest, 1.680-1.692) and her upper lip's crease
    (the AO's least above it, 3.5-12 mm up, on columns where it is a crease: 6 or more under its surround)."""
    a = at_uv(ao_r, np.nan_to_num(F[..., 0]), np.nan_to_num(F[..., 1]))
    a = ndimage.uniform_filter1d(a, 5, axis=1)
    ys = Y1 - (np.arange(a.shape[0]) + 0.5) * D
    m = np.full(a.shape[1], np.nan); t = np.full(a.shape[1], np.nan); depth = np.zeros(a.shape[1])
    for c in range(a.shape[1]):
        band = (ys > 1.680) & (ys < 1.692)
        i = np.where(band)[0][np.argmin(a[band, c])]
        if a[i, c] > 0.6:
            continue
        m[c] = ys[i]
        up = (ys > ys[i] + 0.0035) & (ys < ys[i] + 0.012)
        j = np.where(up)[0][np.argmin(a[up, c])]
        sur = np.median(a[max(j - 15, 0):j - 6, c].tolist() + a[j + 7:j + 16, c].tolist())
        depth[c] = (sur - a[j, c]) * 255
        if depth[c] >= 6:
            t[c] = ys[j]
    return m, t, depth, a


def redness(img):
    return img[..., 0] - img[..., 1]


def red_top(Fimg, m, t):
    """Per column the top of the paint's red: going down from 1 mm over the crease, the first point the redness
    (smoothed) is past halfway from the skin's (over the crease) to the lip's (just over the mouth line) for 0.6 mm."""
    r = ndimage.uniform_filter(redness(Fimg), (3, 5))
    e = np.full(len(m), np.nan)
    for c in range(len(m)):
        if np.isnan(m[c]) or np.isnan(t[c]):
            continue
        i_t, i_m = int(round(row(t[c]))), int(round(row(m[c])))
        skin = np.median(r[i_t - 40:i_t - 10, c])
        lip = np.percentile(r[i_m - 30:i_m - 5, c], 80)
        if lip - skin < 6:
            continue
        mid = 0.5 * (skin + lip)
        run = 0
        for i in range(i_t - 10, i_m - 4):
            run = run + 1 if r[i, c] > mid else 0
            if run >= 6:
                e[c] = Y1 - (i - 5 + 0.5) * D
                break
    return e


def smooth_cols(v, sigma=25):
    ok = ~np.isnan(v)
    if ok.sum() < 3:
        return v
    x = np.arange(len(v))
    f = np.interp(x, x[ok], v[ok])
    med = ndimage.median_filter(f, 31)
    s = ndimage.gaussian_filter1d(med, sigma)
    s[~ok] = np.nan
    return s


def paints():
    out = {"own": "heroine_head.jpg"}
    for f in os.listdir(TEX):
        mm = re.fullmatch(r"heroine_head_(\w+)\.jpg", f)
        if mm:
            out[mm.group(1)] = f
    return out


def measure(faces):
    P, UV, T = mesh()
    F = front(P, UV, T)
    ao = np.asarray(Image.open(os.path.join(TEX, "heroine_ao.png")).convert("RGBA")).astype(np.float64)[..., 0] / 255
    m, t, depth, _ = lines(F, ao)
    pp = paints()
    es = {}
    for f in faces or sorted(pp):
        im = np.asarray(Image.open(os.path.join(TEX, pp[f])).convert("RGB")).astype(np.float64)
        es[f] = red_top(at_uv(im, np.nan_to_num(F[..., 0]), np.nan_to_num(F[..., 1])), m, t)
    print("x mm  mouth   crease  depth " + " ".join("%7s" % f[:7] for f in es) + "   (crease - red top, mm)")
    for xmm in range(-26, 27, 2):
        c = int(round(col(xmm / 1000)))
        print("%+4d  %s  %s  %4.0f  " % (xmm, "%.4f" % m[c] if not np.isnan(m[c]) else "  --  ",
              "%.4f" % t[c] if not np.isnan(t[c]) else "  --  ", depth[c]) +
              " ".join("%7s" % ("%.1f" % ((t[c] - e[c]) * 1000) if not np.isnan(e[c]) and not np.isnan(t[c]) else "--")
                       for e in es.values()))
    return F, m, t, es


def fill_cols(v, ok_span):
    """v's NaNs inside ok_span (a boolean per column) filled by interpolation; outside, the nearest end's."""
    x = np.arange(len(v)); ok = ~np.isnan(v)
    return np.interp(x, x[ok], v[ok]) if ok.any() else np.zeros(len(v))


def warp_field(F, m, t, e):
    """Per pixel of the front grid, where down her face its colour comes from (y, metres): the red's top e
    lifted to t (under the crease), the band about it moved nearly whole (slope 1 + 0.25 of the lift's share), the
    red under it stretched to the mouth line's band (kept), the skin over it eased up to N (under her nose: the
    first point over the crease her face comes 2 mm forward of its least, at most 7 mm over it)."""
    ny, nx = F.shape[:2]
    ys = Y1 - (np.arange(ny) + 0.5) * D
    have = ~np.isnan(m)
    meas = ~np.isnan(t) & ~np.isnan(e)
    L = smooth_cols(np.where(meas, t - e, np.nan))
    h = smooth_cols(np.where(meas, e - m, np.nan))
    ms = smooth_cols(np.where(have, m, np.nan))
    cs = np.where(meas)[0]
    corner = np.where(have)[0]
    lo, hi = cs.min(), cs.max()
    c0, c1 = corner.min(), corner.max()
    x = np.arange(nx)
    Lf, hf, mf = fill_cols(L, meas), fill_cols(h, meas), fill_cols(ms, have)
    # (past the crease's ends the lift tapers to nothing at her mouth's corners, the red's height to 0.5 mm)
    tap = np.ones(nx)
    tap[x > hi] = 1 - np.clip((x[x > hi] - hi) / max(c1 - hi, 1), 0, 1)
    tap[x < lo] = 1 - np.clip((lo - x[x < lo]) / max(lo - c0, 1), 0, 1)
    tap = tap * tap * (3 - 2 * tap)
    Lf = Lf * tap
    hf = 0.0005 + (hf - 0.0005) * tap
    S = np.repeat(ys[:, None], nx, 1)
    z = F[..., 2]
    for c in range(nx):
        if Lf[c] < LIFT_MIN or not (c0 <= c <= c1):
            continue
        mm = mf[c]; ee = mm + hf[c]; tt = ee + Lf[c]
        i_t = int(round(row(tt)))
        zc = z[:, c]
        zr = np.nanmin(zc[max(i_t - 30, 0):i_t + 1])
        up = np.where((ys > tt) & (ys < tt + 0.007) & (zc > zr + 0.002))[0]
        N = min(ys[up].min() - 0.0003 if len(up) else tt + 0.007, tt + 0.007)
        N = max(N, tt + 0.003)
        k = 1 + 0.25 * (Lf[c] / max(hf[c], 1e-4))
        kx = [mm - 0.002, mm + 0.0008, tt - EDGE, tt + EDGE, N, N + 0.002]
        ky = [mm - 0.002, mm + 0.0008, ee - EDGE / k, ee + EDGE / k, N, N + 0.002]
        if not (np.all(np.diff(kx) > 0) and np.all(np.diff(ky) > 0)):
            continue
        f = PchipInterpolator(kx, ky)
        band = (ys > kx[0]) & (ys < kx[-1])
        S[band, c] = f(ys[band])
    return S, Lf


def apply(faces, dry=False):
    P, UV, T = mesh()
    F = front(P, UV, T)
    # (her mouth's grid filled out to its edges, for sampling)
    bad = np.isnan(F[..., 0])
    _, (iy, ix) = ndimage.distance_transform_edt(bad, return_indices=True)
    F = F[iy, ix]
    ao = np.asarray(Image.open(os.path.join(TEX, "heroine_ao.png")).convert("RGBA")).astype(np.float64)[..., 0] / 255
    m, t_c, depth, _ = lines(F, ao)
    t = t_c - BELOW
    pp = paints()
    pos = None
    for face in faces or sorted(pp):
        path = os.path.join(TEX, pp[face])
        im = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
        n = im.shape[0]
        if pos is None or pos.shape[0] != n:
            pos = in_uv(P, UV, T, n, None)
            rr, cc = np.where(~np.isnan(pos[..., 0]) & (np.abs(pos[..., 0]) < X1) & (pos[..., 1] > Y0) & (pos[..., 1] < Y1))
            px, py, pz = pos[rr, cc, 0], pos[rr, cc, 1], pos[rr, cc, 2]
            fr, fc = row(py), np.clip(np.round(col(px)).astype(int), 0, F.shape[1] - 1)
            zf = sample(F[..., 2], fr, fc.astype(float))
            vis = np.clip((pz - zf + 0.0006) / 0.0003, 0, 1)
        Fimg = at_uv(im, F[..., 0], F[..., 1])
        e = red_top(Fimg, m, t_c)
        S, Lf = warp_field(F, m, t, e)
        sy = sample(S, fr, fc.astype(float))
        moved = np.clip(np.abs(sy - py) / 0.00005, 0, 1) * vis
        go = moved > 0
        sr = row(sy[go])
        su = sample(F[..., 0], sr, fc[go].astype(float)); sv = sample(F[..., 1], sr, fc[go].astype(float))
        src = np.stack([ndimage.map_coordinates(im[..., ch], [sv * n - 0.5, su * n - 0.5], order=3, mode="nearest")
                        for ch in range(3)], -1)
        out = im.copy()
        w = moved[go][:, None]
        out[rr[go], cc[go]] = im[rr[go], cc[go]] * (1 - w) + src * w
        left = np.nanmax(np.where(np.isnan(e) | np.isnan(t), np.nan, t - e))
        print("LIPS %-9s lift up to %.1f mm (centre %.1f), %d texels moved%s" % (
            face, 1000 * np.nanmax(Lf), 1000 * Lf[int(round(col(0)))], go.sum(), " (dry)" if dry else ""))
        if not dry:
            Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(path, quality=95, subsampling=0)
        else:
            Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(dry if isinstance(dry, str) and len(faces) == 1 else path + ".dry.jpg", quality=95, subsampling=0)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--measure"]:
        measure(sys.argv[2:])
    elif sys.argv[1:2] == ["--to"]:
        apply(sys.argv[3:], dry=sys.argv[2])     # (--to OUT FACE: one face's lifted paint written to OUT, for a look)
    else:
        apply(sys.argv[1:])
