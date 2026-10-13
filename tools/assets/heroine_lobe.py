"""Her ear lobes in each face's paint: the lobe in the ear's own tone, and the second lobe painted on her neck under
it taken out.

Her head's lobe is a solid one, fused to her neck: a rounded lower edge and a flat underside about 1.5 cm deep over
her neck (y 1.703 m). heroine_ears.py brought her ears to her cheek's tone, but its reach (EAR_R about the ear's
middle) stops above the lobe's lower half and underside, which kept the base head's paint, pale and grey: at 40
degrees and in play every face's lobe read as a flat cream-white tab with a hard edge (the owner, 13 October 2026).
And five faces' paints (Sunborn, Moonlit, Saffron, Fey, Vixen) carry their portrait's own lobe, drawn 1-2 cm lower
than her head's, as a crescent on her neck under the real one (a ghost lobe).

This works on her head's surface, not its UV islands: each texel near her ears is given its point on her head (the
glb's skin_head), and its tone is smoothed over her surface in 3D (normalized convolution on a 0.3 mm grid), so no
seam of the UV layout shows. Per face, per ear, in linear light:
  lobe:  the texel's fine grain (its paint over the 3D smoothing at SIGMA) laid on the median tone of the ear just
         above the lobe (fully inside heroine_ears.py's reach), a little deeper on its underside where it turns down
         into the crease over her neck (UNDER), eased in over the lobe's edges;
  neck:  the same grain laid on a smooth fill (a quadratic in height and depth fitted, robustly, to the neck round the
         patch), over the neck under the lobe.
Idempotent: a rerun finds the tone already laid and the change under 1/255, and writes nothing.

    python tools/assets/heroine_lobe.py [face ...]     (no faces: all ten paints in godot/art/people/head_tex)

Run after heroine_ears.py (and its --render pass), which sets the ear's tone this takes. Touches nothing above the
lobe (y 1.718 m) nor in front of the ear (z 0.012 m).
"""
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
LOBE_C = np.array([0.070, 1.709, -0.008])   # (each lobe's middle, metres, glTF axes with x as |x|)
VOX = 0.0003                                # (the 3D grid, metres)
SIGMA = 0.0006                              # (grain finer than this is kept, coarser is the tone laid)
UNDER = 0.15                                # (the lobe's underside this much deeper where it faces straight down)
PAD = 12                                    # (texels of the UV islands' padding given their island's change)
EAR = (0.076, 1.735, -0.018)                # (heroine_ears.py's)
EAR_R = (0.026, 0.034)


def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def head():
    js, binc = hs._load(GLB)
    mats = [m.get("name") for m in js["materials"]]
    prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
    P = hs._read(js, binc, prim["attributes"]["POSITION"])
    N = hs._read(js, binc, prim["attributes"]["NORMAL"])
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    return P, N, UV, T


def texels(P, N, UV, T, side, size):
    """Every texel of the triangles near one lobe: (row, col) and its point and normal on her head."""
    c = LOBE_C * [side, 1, 1]
    tri = T[(np.linalg.norm(P[T] - c, axis=2) < 0.05).any(1)]
    U = UV * size
    rows, cols, pos, nrm = [], [], [], []
    for t in tri:
        a, b, cc = U[t]
        x0, y0 = np.maximum(np.floor(U[t].min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(U[t].max(0)).astype(int), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        v0, v1, v2 = b - a, cc - a, q - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        vv = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        ww = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        bb = np.stack([1 - vv - ww, vv, ww], 1)
        m = (bb > -1e-3).all(1)
        rows.append(ys.ravel()[m]); cols.append(xs.ravel()[m])
        pos.append(bb[m] @ P[t]); nrm.append(bb[m] @ N[t])
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    key = rows * size + cols
    _, first = np.unique(key, return_index=True)
    pos, nrm = np.concatenate(pos)[first], np.concatenate(nrm)[first]
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    # (only what the lobe, the neck under it and their references reach, and the smoothing's margin)
    keep = (pos[:, 0] * side > 0.024) & (pos[:, 1] > 1.650) & (pos[:, 1] < 1.734) & (pos[:, 2] > -0.060) & (pos[:, 2] < 0.022)
    return rows[first][keep], cols[first][keep], pos[keep], nrm[keep]


def covered(UV, T, size, box):
    """Texels any triangle of her head covers, in box (x0, y0, x1, y1): the rest is the islands' padding."""
    x0, y0, x1, y1 = box
    U = UV * size
    lo, hi = U[T].min(1), U[T].max(1)
    sel = T[(hi[:, 0] >= x0) & (lo[:, 0] <= x1) & (hi[:, 1] >= y0) & (lo[:, 1] <= y1)]
    cov = np.zeros((y1 - y0, x1 - x0), bool)
    for t in sel:
        a, b, cc = U[t] - [x0, y0]
        xa, ya = np.maximum(np.floor(np.min([a, b, cc], 0)).astype(int), 0)
        xb, yb = np.minimum(np.ceil(np.max([a, b, cc], 0)).astype(int), [x1 - x0 - 1, y1 - y0 - 1])
        if xb < xa or yb < ya:
            continue
        xs, ys = np.meshgrid(np.arange(xa, xb + 1), np.arange(ya, yb + 1))
        q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        v0, v1, v2 = b - a, cc - a, q - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        vv = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        ww = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        m = (vv > -0.02) & (ww > -0.02) & (vv + ww < 1.02)
        cov[ys.ravel()[m], xs.ravel()[m]] = True
    return cov


def masks(pos, nrm, side):
    ax, y, z = pos[:, 0] * side, pos[:, 1], pos[:, 2]
    zw = smooth(-0.034, -0.026, z) * (1 - smooth(0.004, 0.012, z))
    lobe = (1 - smooth(1.710, 1.718, y)) * smooth(1.697, 1.701, y) * smooth(0.050, 0.055, ax) * zw
    neck = (1 - smooth(1.699, 1.704, y)) * smooth(1.666, 1.674, y) * (1 - smooth(0.0525, 0.0565, ax)) \
        * smooth(0.030, 0.036, ax) * smooth(-0.044, -0.036, z) * (1 - smooth(0.004, 0.012, z)) * (nrm[:, 0] * side > 0.0)
    d = np.linalg.norm(np.c_[ax, y, z] - np.array(EAR), axis=1)
    ear = (1 - smooth(EAR_R[0], EAR_R[1], d)) * smooth(0.062, 0.067, ax)
    ref = (ear > 0.95) & (y > 1.719) & (y < 1.730) & (nrm[:, 0] * side > 0.3)
    ring = (neck == 0) & (lobe == 0) & (ax > 0.028) & (ax < 0.056) & (y > 1.656) & (y < 1.703) & (z > -0.054) \
        & (z < 0.010) & (nrm[:, 0] * side > 0.2)
    return lobe, neck, ref, ring


def smoothed(pos, val):
    """val smoothed over her surface: splat onto a 3D grid, Gaussian SIGMA, normalized, read back (trilinear)."""
    lo = pos.min(0) - 4 * SIGMA
    g = ((pos - lo) / VOX)
    shape = np.ceil(g.max(0)).astype(int) + 2
    idx = np.floor(g).astype(int)
    flat = np.ravel_multi_index(idx.T, shape)
    s = SIGMA / VOX
    out = np.zeros_like(val)
    wgt = ndimage.gaussian_filter(np.bincount(flat, minlength=np.prod(shape)).reshape(shape).astype(np.float32), s)
    wv = ndimage.map_coordinates(wgt, g.T - 0.5, order=1, mode="nearest")
    for ch in range(val.shape[1]):
        acc = ndimage.gaussian_filter(np.bincount(flat, val[:, ch], np.prod(shape)).reshape(shape).astype(np.float32), s)
        out[:, ch] = ndimage.map_coordinates(acc, g.T - 0.5, order=1, mode="nearest") / np.maximum(wv, 1e-6)
    return out


def fill(pos, val, sel, side):
    """A smooth tone for the neck: per channel a quadratic in height and depth, fitted to sel, outliers (moles,
    freckles, the ghost's own edge) reweighted away."""
    y, z = pos[:, 1] - 1.69, pos[:, 2] + 0.01
    A = np.c_[np.ones_like(y), y, z, y * y, y * z, z * z]
    out = np.zeros_like(val)
    for ch in range(val.shape[1]):
        w = np.ones(sel.sum())
        for _ in range(6):
            coef = np.linalg.lstsq(A[sel] * w[:, None], val[sel, ch] * w, rcond=None)[0]
            r = val[sel, ch] - A[sel] @ coef
            sd = 1.4826 * np.median(np.abs(r)) + 1e-6
            w = 1 / np.maximum(1, np.abs(r) / (2 * sd))
        out[:, ch] = A @ coef
    return out


def run(faces):
    P, N, UV, T = head()
    paints = {"own": "heroine_head.jpg"}
    for f in os.listdir(TEX):
        m = re.fullmatch(r"heroine_head_(\w+)\.jpg", f)
        if m: paints[m.group(1)] = f
    cache = {}
    for face in faces or sorted(paints):
        path = os.path.join(TEX, paints[face])
        im = np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255
        size = im.shape[0]
        L = lin(im)
        out = L.copy()
        notes, laid = [], True
        for side in (-1, 1):
            if (side, size) not in cache:
                r, c, pos, nrm = texels(P, N, UV, T, side, size)
                mk = masks(pos, nrm, side)
                ch = (mk[0] > 0) | (mk[1] > 0)
                box = (max(c[ch].min() - PAD - 2, 0), max(r[ch].min() - PAD - 2, 0),
                       min(c[ch].max() + PAD + 3, size), min(r[ch].max() + PAD + 3, size))
                cache[side, size] = (r, c, pos, nrm, mk, box, covered(UV, T, size, box))
            r, c, pos, nrm, (lobe, neck, ref, ring), box, cov = cache[side, size]
            v = L[r, c]
            grain = v / np.maximum(smoothed(pos, v), 1e-4)
            # the lobe: the ear's tone, deeper where it turns down into the crease over her neck
            tone = np.median(v[ref], 0)
            down = smooth(0.25, 0.9, -nrm[:, 1]) * (1 - smooth(0.062, 0.072, pos[:, 0] * side))
            core = (lobe > 0.97) & (down < 0.05)
            laid &= bool(np.all(np.abs(np.median(v[core], 0) / tone - 1) < 0.02))
            lobe_v = tone * (1 - UNDER * down)[:, None] * grain
            # the neck under it: a smooth fill round the patch, its own grain
            neck_v = fill(pos, smoothed(pos, v), ring, side) * grain
            w = np.clip(np.maximum(lobe, neck), 0, 1)[:, None]
            new = np.where(lobe[:, None] >= neck[:, None], lobe_v, neck_v)
            out[r, c] = v + (new - v) * w
            # (the islands' padding round what changed takes its nearest texel's change, so no old tone bleeds
            # back in through the mipmaps at a distance)
            x0, y0, x1, y1 = box
            ratio = np.ones((y1 - y0, x1 - x0, 3))
            ib = (r >= y0) & (r < y1) & (c >= x0) & (c < x1)
            ratio[r[ib] - y0, c[ib] - x0] = out[r[ib], c[ib]] / np.maximum(L[r[ib], c[ib]], 1e-5)
            _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
            dist = ndimage.distance_transform_edt(~cov)
            pad = (~cov) & (dist <= PAD)
            sub = out[y0:y1, x0:x1]
            sub[pad] = L[y0:y1, x0:x1][pad] * ratio[iy[pad], ix[pad]]
            notes.append("ear %+d: tone %s, lobe %d texels, neck %d" % (side, np.round(srgb(tone), 3), (lobe > 0).sum(), (neck > 0).sum()))
        if laid:
            print("LOBE %-9s already laid (its lobe within 2%% of its ear's tone), not written" % face)
            continue
        o8 = (np.clip(srgb(np.clip(out, 0, 1)), 0, 1) * 255 + 0.5).astype(np.uint8)
        diff = np.abs(o8.astype(int) - (im * 255 + 0.5).astype(int)).max()
        Image.fromarray(o8).save(path, quality=95, subsampling=0)
        print("LOBE %-9s max change %d/255; %s" % (face, diff, "; ".join(notes)))


if __name__ == "__main__":
    run(sys.argv[1:])
