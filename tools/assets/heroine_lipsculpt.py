"""Her upper lip's sculpt brought down to each face's portrait, in her exported glb (heroine.glb).

WIP (solver ls2, 12 October 2026): NOT HOOKED, NOT RUN, no glb changed. Only the loaders and the front raster are
here; the remap below is the plan. Measured inputs: heroine_face/lip_targets.json (per face: portrait upper-lip
height H(u) = height / mouth width, the paint's red top and the sculpt's old border, both over the sculpt's slit,
mouth width and middle in mm). Findings that bear on it: the face keys make the upper lip taller than own's (old
border 0.21 own to 0.31 Doe of mouth width, so squeezes of 0.42-0.82) and smooth its notch away (no sharp border on
any face but own: find it as own's kink loop tracked by UV); each paint's darkest mouth line lies 0.4-2.4 mm under
the sculpt's slit (Wildling 2.4, Sunborn 2.1).

Her head's shared sculpt has a full upper lip: its vermilion border (a sharp ridge at the sides, a notch at the
cupid's bow) sits 9-10 mm over her mouth line, about 0.2 of her mouth's width, while every portrait's upper lip is
0.13-0.15 at its middle and 0.15-0.18 at its peaks. The paints, laid from the portraits, colour the sculpt's top
3.6-7.9 mm as skin, so at the Look the lit ridge and her head's shade drew an outline in skin above a thin red lip
(the owner, 12 October 2026: "a like lip outline above the lip"; fuller painted lips turned down, "it dosnt look so
hot"). This moves her upper lip's surface in depth only (each point keeps its height and side, so the paint does not
slide on her), per face on its own shaped head seen from in front: down each column of her face, a smooth remap of
height brings the border down to the portrait's upper-lip height (scaled by her mouth's width), the lip's profile
squeezed into the new height with its bulge scaled with it, the skin over it eased from the new border to 4.5 mm
over the old one; nothing moves under 0.9 mm over her mouth line, or past the corners of her mouth. Her own face is
her head's base shape; every other face is its whole-face key (face_ID at 1), changed so the face's shaped head
comes out as its own remap says. Expression and slider keys are offsets from the base and are left as they are.
Normals turn with the change; points split along her UVs' seams move as one.

    python tools/assets/heroine_lipsculpt.py godot/art/people/heroine.glb [OUT.glb]
    python tools/assets/heroine_lipsculpt.py --measure [GLB] [face ...]     (per face: mouth line, border, heights)

heroine_seam.py's seam() runs this after the throat (heroine_throat.py), on every glb heroine_head.py and
heroine_outfits.py write. On one already done (its head's extras say lip_sculpt) it does nothing.
"""
import json
import os
import sys

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
FACES = ("own", "highborn", "vixen", "doe", "sunborn", "moonlit", "saffron", "wildling", "hardwon", "fey")
# (her mouth seen from in front, on any face's shaped head: metres, a 0.1 mm grid)
X0, X1, Y0, Y1, D = -0.040, 0.040, 1.640, 1.740, 0.0001


def head(path):
    """Her head's mesh in a glb: (js, binc, chunks, hm, hp, names, P, N, UV, T)."""
    js, binc = hs._load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    mats = [m.get("name") for m in js.get("materials", [])]
    hm, hp = next((m, p) for m in js["meshes"] for p in m["primitives"] if "material" in p and mats[p["material"]] == "skin_head")
    names = hm.get("extras", {}).get("targetNames", [])
    P = hs._read(js, binc, hp["attributes"]["POSITION"])
    N = hs._read(js, binc, hp["attributes"]["NORMAL"])
    UV = hs._read(js, binc, hp["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, hp["indices"]).reshape(-1, 3)
    return js, binc, chunks, hm, hp, names, P, N, UV, T


def key_delta(js, binc, hp, names, name):
    t = hp["targets"][names.index(name)]
    return hs._read(js, binc, t["POSITION"])


def shaped(js, binc, hp, names, P, face):
    return P if face == "own" else P + key_delta(js, binc, hp, names, "face_" + face)


def _scan(pts, size_x, size_y, vals):
    """Triangles (k x 3 x 2 grid coordinates) carrying vals (k x 3 x m, the last being depth z) rasterised, the
    front-most (largest z) kept."""
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
        take = np.isnan(old[:, -1]) | (new[:, -1] > old[:, -1])
        out[yy[take], xx[take]] = new[take]
    return out


def front(S, T, UV=None, box=(X0, X1, Y0, Y1), d=D):
    """Her shaped head S seen from in front on a d grid (row 0 at the box's top): per pixel the front-most surface's
    (u, v,) z."""
    x0, x1, y0, y1 = box
    c = S[T].mean(1)
    sel = np.where((c[:, 0] > x0 - 0.005) & (c[:, 0] < x1 + 0.005) & (c[:, 1] > y0 - 0.005) & (c[:, 1] < y1 + 0.005)
                   & (c[:, 2] > 0.03))[0]
    g = np.stack([(S[T[sel]][..., 0] - x0) / d, (y1 - S[T[sel]][..., 1]) / d], -1)
    vals = S[T[sel]][..., 2:3] if UV is None else np.concatenate([UV[T[sel]], S[T[sel]][..., 2:3]], -1)
    nx, ny = int(round((x1 - x0) / d)), int(round((y1 - y0) / d))
    return _scan(g, nx, ny, vals)


def grid_y(i, box=(X0, X1, Y0, Y1), d=D):
    return box[3] - (np.asarray(i) + 0.5) * d


def grid_x(j, box=(X0, X1, Y0, Y1), d=D):
    return box[0] + (np.asarray(j) + 0.5) * d
