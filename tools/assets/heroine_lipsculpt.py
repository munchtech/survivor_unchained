"""Her upper lip's sculpt brought down to each face's portrait, in her exported glb (heroine.glb).

WIP (solver ls3, 12 October 2026): BUILT AND HOOKED BUT OFF (HEROINE_LIPSCULPT=1 turns it on in heroine_seam.py's
seam(), on both its paths; marker lip_sculpt), NOT ACCEPTED, heroine.glb not changed. --dry measures it offline:
own lands within 1% of its portrait (crease, the strongest concave bend), the cupid's bow's peaks on Doe within
10%, but Doe's middle (and likely other big squeezes) keeps no crease: the squeezed lip ends ~3 mm short of the old
border's depth, and making that up (TILT) flattens the top step there. What changed from the plan below: the
squeeze keeps the lip's slopes (lip_profile: its top step TOP_L squeezed no more than TOP_S, the rest more), the
old border is refined to the face's own strongest concave bend (+PAD), and the depth deficit is a separate tilt
(TILT over the lip, eased; the rest a ramp over the skin). Next: try TILT 0.5 or less (more of the deficit into
the skin's ramp, the border's depth going back), or keep the border's crease explicitly; then shoot.
Plan as solver ls2 left it (solver ls2: the loaders and the front raster). Measured inputs: heroine_face/lip_targets.json (per face: portrait upper-lip
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


# ---- her mouth's features on the front raster (solver ls2's finders: scratch face/ls2 feat.py, trackf.py) ----

def narrow_depth(Z, half=0.0015, d=D):
    """How far each pixel lies under the nearer of the highest points within `half` above and below it: deep in a
    narrow valley across her face (her mouth's slit)."""
    k = int(round(half / d))
    Zf = np.where(np.isnan(Z), -1.0, Z)
    up = ndimage.maximum_filter1d(Zf, k + 1, axis=0, origin=k // 2)
    dn = ndimage.maximum_filter1d(Zf, k + 1, axis=0, origin=-(k // 2))
    return np.minimum(up, dn) - Zf


def track(score, i0, c0, win, stop):
    """Per column, the row of the best score within win rows of the last column's, out from column c0 both ways;
    NaN past where the best is under stop."""
    ny, nx = score.shape
    r = np.full(nx, np.nan)
    for step in (1, -1):
        i = i0
        for c in range(c0, nx if step > 0 else -1, step):
            lo, hi = max(i - win, 0), min(i + win + 1, ny)
            j = lo + int(np.argmax(score[lo:hi, c]))
            if score[j, c] < stop:
                break
            r[c], i = j, j
    return r


def kink(Z, h=0.0008, d=D):
    """The change in her surface's slope (depth over height) going up through each pixel, over h each side."""
    k = int(round(h / d))
    return (np.roll(Z, k, 0) - Z) / (k * d) - (Z - np.roll(Z, -k, 0)) / (k * d)


def own_features(F):
    """Her own face's slit and vermilion border (rows per column of the front raster F): the slit is the deepest
    narrow valley, tracked out from the middle; the border is the sharpest bend 8-12 mm over the slit at the middle
    (the cupid's bow's notch), tracked out."""
    Z = F[..., 2]
    ny, nx = Z.shape
    ys, c0 = grid_y(np.arange(ny)), nx // 2
    nd = np.nan_to_num(narrow_depth(Z), nan=-1)
    band = np.where((ys > 1.680) & (ys < 1.695))[0]
    i0 = band[np.argmax(nd[band, c0])]
    slit = track(nd, i0, c0, 6, 0.0003)
    K = np.abs(np.nan_to_num(kink(Z)))
    sel = np.where((ys > ys[i0] + 0.008) & (ys < ys[i0] + 0.012))[0]
    border = track(K, sel[np.argmax(K[sel, c0])], c0, 4, 0.15)
    return slit, border


def face_features(F, Fo, slit_o, border_o):
    """A face's slit and old border (rows per column of its front raster F): her own face's (on Fo) found on this
    face by their UVs, the slit then refined to the deepest narrow valley within 1.5 mm."""
    ny, nx = F.shape[:2]
    ok = ~np.isnan(F[..., 0])
    rr, cc = np.where(ok)
    tree = cKDTree(F[rr, cc, :2])
    out = []
    for rows in (slit_o, border_o):
        c = np.where(~np.isnan(rows))[0]
        _, i = tree.query(Fo[rows[c].astype(int), c, :2])
        r2, c2 = rr[i], cc[i]
        o = np.argsort(c2)
        prior = np.full(nx, np.nan)
        cols = np.arange(nx)
        inside = (cols >= c2.min()) & (cols <= c2.max())
        prior[inside] = np.interp(cols[inside], c2[o], r2[o].astype(float))
        out.append(prior)
    nd = np.nan_to_num(narrow_depth(F[..., 2]), nan=-1)
    slit = np.full(nx, np.nan)
    for c in np.where(~np.isnan(out[0]))[0]:
        p = int(round(out[0][c]))
        lo, hi = max(p - 15, 0), min(p + 16, ny)
        slit[c] = lo + np.argmax(nd[lo:hi, c])
    return slit, out[1]


# ---- the remap ----

TARGETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_face", "lip_targets.json")
BORDERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_face", "lip_borders.json")
# (the portraits presets.json lays a face from, where they differ from lip_targets.json's *_23: its middle height
#  over the _23's, solver ls3's brief)
LAYING = {"fey": 0.158 / 0.135, "moonlit": 0.163 / 0.153}
ANCHOR = 0.0009      # (nothing moves under this over her slit)
SKIN = 0.0045        # (the skin from the old border to this over it eased up from the new border)
NOSE_SLOPE = 0.6     # (her profile rising toward her nose faster than this, depth over height, is the nose's jump)
NOSE_GAP = 0.0005    # (the eased skin's top kept this under the jump)
SIG_Y, SIG_X = 0.00045, 0.0005   # (the new surface smoothed so: the new border's bend over 1.2 mm or more)
RAMP_A, RAMP_T = 0.0010, 0.0006  # (the change eased in over RAMP_A from the anchor, out over +-RAMP_T at the top)
U_IN, U_OUT = 0.36, 0.47         # (the change tapered out between these, fractions of her mouth's width from its middle)
FRONT = 0.0003       # (only points this near the front-most surface move)
TOP_L, TOP_B, TOP_S, TOP_LOW = 0.0025, 0.002, 0.75, 0.2  # (the lip's top step: see lip_profile)
# (the squeezed lip ends short of the old border's depth: TILT of that made up over the lip, eased in and out
#  (TILT_EASED) or even (the brief's chord), the rest over the skin, eased out up to its top)
TILT, TILT_EASED = 0.4, True
PAD = 0.0005         # (the old border taken this over the old crease, so all its bend squeezes with the lip)


def target(face, path=TARGETS):
    """A face's portrait upper-lip height H(u) (over its mouth's width; u its fraction from the mouth's middle, held
    past the measured ends, smoothed over 0.02), its mouth's width and middle (metres)."""
    t = json.load(open(path))
    us = np.asarray(t["u"], float)
    H = np.asarray(t[face]["portrait"], float) * LAYING.get(face, 1.0)
    fine = np.linspace(-0.6, 0.6, 1201)
    Hs = ndimage.gaussian_filter1d(np.interp(fine, us, H), 20, mode="nearest")
    return (lambda u: np.interp(u, fine, Hs)), t[face]["w_mm"] / 1000, t[face]["cx_mm"] / 1000


def _nan_smooth(v, sigma):
    """A per-column curve (NaN where absent) smoothed over sigma columns, NaN kept."""
    m = ~np.isnan(v)
    a = ndimage.gaussian_filter1d(np.where(m, v, 0.0), sigma, mode="nearest")
    b = ndimage.gaussian_filter1d(m.astype(float), sigma, mode="nearest")
    out = a / np.maximum(b, 1e-9)
    out[~m] = np.nan
    return out


def _held(v, cols):
    """A per-column curve held at its end values over the columns cols past where it is measured."""
    m = np.where(~np.isnan(v))[0]
    out = v.copy()
    out[cols[cols < m.min()]] = v[m.min()]
    out[cols[cols > m.max()]] = v[m.max()]
    return out


def plan(F, slit, border, face):
    """Per column of the front raster F: the face's slit, anchor, new border, old border and eased skin's top
    heights (metres) and the lip's squeeze, NaN outside her mouth (|u| >= U_OUT); and u."""
    Hf, w, cx = target(face)
    Z = F[..., 2]
    ny, nx = Z.shape
    xs, ys = grid_x(np.arange(nx)), grid_y(np.arange(ny))
    u = (xs - cx) / w
    cols = np.where(~np.isnan(slit) & (np.abs(u) < U_OUT))[0]
    ysl = _nan_smooth(np.where(np.isnan(slit), np.nan, grid_y(np.nan_to_num(slit))), 10)
    K = ndimage.gaussian_filter1d(np.nan_to_num(kink(Z, 0.0006)), 1.5, axis=0)
    cr = np.full(nx, np.nan)
    for c in np.where(~np.isnan(border))[0]:
        r0 = int(round(border[c]))
        rows = np.arange(max(r0 - 20, 1), min(r0 + 21, ny - 1))
        cr[c] = rows[np.argmax(K[rows, c])]
    hb = _nan_smooth(np.where(np.isnan(cr) | np.isnan(slit), np.nan, grid_y(np.nan_to_num(cr)) - ysl), 5) + PAD
    hb = _held(hb, cols)
    p = {k: np.full(nx, np.nan) for k in ("slit", "anchor", "new", "old", "top", "s", "jump")}
    p["u"] = u
    for c in cols:
        y_s = ysl[c]
        y_b = y_s + hb[c]
        y_a = y_s + ANCHOR
        y_n = min(y_s + float(Hf(u[c])) * w, y_b)
        z = Z[:, c]
        ok = ~np.isnan(z)
        zf = lambda y: np.interp(y, ys[ok][::-1], z[ok][::-1])
        # (the nose's jump: from 1 mm over the old border up, where her profile first rises faster than NOSE_SLOPE)
        hh = np.arange(y_b + 0.001, y_b + 0.012, D)
        sl = (zf(hh + 0.0005) - zf(hh - 0.0005)) / 0.001
        jump = hh[np.argmax(sl > NOSE_SLOPE)] if (sl > NOSE_SLOPE).any() else y_b + 0.012
        p["slit"][c], p["anchor"][c], p["new"][c], p["old"][c], p["jump"][c] = y_s, y_a, y_n, y_b, jump
    # (the eased skin's top: SKIN over the old border, under the nose's jump within 2 mm either side; smooth along x)
    jm = ndimage.minimum_filter1d(np.where(np.isnan(p["jump"]), np.inf, p["jump"]), 41, mode="nearest")
    top = np.minimum(p["old"] + SKIN, jm - NOSE_GAP)
    top = np.maximum(top, p["old"] + 0.001)
    p["top"] = _nan_smooth(top, 10)
    p["s"] = (p["new"] - p["anchor"]) / (p["old"] - p["anchor"])
    return p


def lip_profile(zf, y_a, y_b, y_n, s, dv=2e-5):
    """A column's lip from the anchor to the old border squeezed into the anchor to the new border, its slopes kept
    (so its bulge shrinks with its height) and its top step (TOP_L under the border) squeezed no more than to
    TOP_S, the rest more, eased between over TOP_B. Returns (new heights, new depths, untilted) along the old lip,
    and how far short of the old border's depth it ends."""
    v = np.arange(y_a, y_b + dv / 2, dv)
    st = max(s, TOP_S)
    sm = _smooth01((v - (y_b - TOP_L - TOP_B)) / TOP_B)
    i1, i2 = np.trapezoid(1 - sm, v), np.trapezoid(sm, v)
    lo = (y_n - y_a - st * i2) / max(i1, 1e-9)
    if lo < TOP_LOW:
        # (too short a lip for its step: squeezed evenly)
        st, lo = s, s
    sig = lo + (st - lo) * sm
    Y = y_a + np.concatenate([[0.0], np.cumsum(0.5 * (sig[1:] + sig[:-1]) * np.diff(v))])
    zv = zf(v)
    A = np.concatenate([[0.0], np.cumsum(0.5 * (sig[1:] + sig[:-1]) * np.diff(zv))])
    return Y, zv[0] + A, zf(y_b) - zv[0] - A[-1]


def new_surface(F, p):
    """The remapped surface on the front raster (her depth per pixel), smoothed, and the weight of the change per
    pixel (0 where nothing moves)."""
    Z = F[..., 2]
    ny, nx = Z.shape
    ys = grid_y(np.arange(ny))
    Zn = Z.copy()
    W = np.zeros_like(Z)
    for c in np.where(~np.isnan(p["s"]))[0]:
        y_a, y_n, y_b, y_t, s = p["anchor"][c], p["new"][c], p["old"][c], p["top"][c], p["s"][c]
        z = Z[:, c]
        ok = ~np.isnan(z)
        zf = lambda y: np.interp(y, ys[ok][::-1], z[ok][::-1])
        lip = (ys >= y_a) & (ys <= y_n)
        Yv, Zv, short = lip_profile(zf, y_a, y_b, y_n, s)
        t = (Yv - y_a) / max(y_n - y_a, 1e-9)
        Zv = Zv + TILT * short * (_smooth01(t) if TILT_EASED else t)
        Zn[lip, c] = np.interp(ys[lip], Yv, Zv)
        sk = (ys > y_n) & (ys <= y_t)
        y = ys[sk]
        Zn[sk, c] = (zf(y_t - (y_t - y) * (y_t - y_b) / (y_t - y_n))
                     - (1 - TILT) * short * (1 - _smooth01((y - y_n) / (y_t - y_n))))
        W[:, c] = (_smooth01((ys - y_a) / RAMP_A) * _smooth01((y_t + RAMP_T - ys) / (2 * RAMP_T))
                   * (1 - _smooth01((abs(p["u"][c]) - U_IN) / (U_OUT - U_IN))))
    Zf = np.where(np.isnan(Zn), np.nanmean(Zn), Zn)
    Zs = ndimage.gaussian_filter(Zf, (SIG_Y / D, SIG_X / D))
    Zs[np.isnan(Z)] = np.nan
    return Zs, W


def _smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _sample(G, X, Y, box=(X0, X1, Y0, Y1), d=D):
    """A front-raster grid G sampled (bilinear) at heights Y and sides X (metres)."""
    r = (box[3] - Y) / d - 0.5
    c = (X - box[0]) / d - 0.5
    return ndimage.map_coordinates(G, [r, c], order=1, mode="constant", cval=np.nan)


def face_change(S, F, p):
    """Each point of the shaped head S moved in depth (metres, per point): the front-most points, toward the
    remapped surface, by its weight."""
    Zs, W = new_surface(F, p)
    zfront = _sample(np.nan_to_num(F[..., 2], nan=-1.0), S[:, 0], S[:, 1])
    on = np.abs(S[:, 2] - zfront) < FRONT
    w = np.nan_to_num(_sample(W, S[:, 0], S[:, 1]))
    zn = _sample(np.nan_to_num(Zs, nan=0.0), S[:, 0], S[:, 1])
    dz = np.where(on & (w > 0), w * (zn - S[:, 2]), 0.0)
    return np.nan_to_num(dz)


def crease(F, p, lo=0.002, h=0.0006):
    """The geometric border per column: the strongest concave bend (slope over h above minus below) of the front
    profile between lo over the slit and 1 mm under the eased skin's top, sub-pixel. Heights (metres), NaN where
    not looked."""
    Z = F[..., 2]
    ny, nx = Z.shape
    ys = grid_y(np.arange(ny))
    K = ndimage.gaussian_filter1d(np.nan_to_num(kink(Z, h)), 1.5, axis=0)
    out = np.full(nx, np.nan)
    for c in np.where(~np.isnan(p["s"]))[0]:
        rows = np.where((ys > p["slit"][c] + lo) & (ys < p["top"][c] - 0.001))[0]
        if len(rows) < 3:
            continue
        i = rows[np.argmax(K[rows, c])]
        a, b, e = K[i - 1, c], K[i, c], K[i + 1, c]
        den = a - 2 * b + e
        out[c] = grid_y(i + (0.5 * (a - e) / den if abs(den) > 1e-12 else 0.0))
    return out


def _vertex_normals(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    n = np.zeros_like(V)
    for k in range(3):
        np.add.at(n, T[:, k], fn)
    return n / (np.linalg.norm(n, axis=1)[:, None] + 1e-12)


def _welded_mean(v, inv, n):
    s = np.zeros((n,) + v.shape[1:])
    np.add.at(s, inv, v)
    return (s / np.maximum(np.bincount(inv, minlength=n), 1).reshape((-1,) + (1,) * (v.ndim - 1)))[inv]


def changes(js, binc, hp, names, P, UV, T, faces=FACES, inv=None):
    """Per face its points' depth change on its own shaped head (welded by place), and its plan and front raster."""
    if inv is None:
        _, inv = np.unique(np.round(P / 1e-6).astype(np.int64), axis=0, return_inverse=True)
        inv = inv.ravel()
    n = inv.max() + 1
    Fo = front(P, T, UV)
    so, bo = own_features(Fo)
    out = {}
    for f in faces:
        S = shaped(js, binc, hp, names, P, f)
        F = Fo if f == "own" else front(S, T, UV)
        slit, border = face_features(F, Fo, so, bo)
        p = plan(F, slit, border, f)
        dz = _welded_mean(face_change(S, F, p), inv, n)
        out[f] = (dz, p, F, S)
    return out


def lip_sculpt(js, binc, chunks, hm, hp):
    """Her upper lip remapped on every face: her head's base (her own face) and each face key changed, normals turned
    with the change. Returns the per-face changes, or None where done already."""
    if "lip_sculpt" in hm.get("extras", {}):
        print("LIPSCULPT: already done - nothing done")
        return None
    names = hm.get("extras", {}).get("targetNames", [])
    P = hs._read(js, binc, hp["attributes"]["POSITION"])
    N = hs._read(js, binc, hp["attributes"]["NORMAL"])
    UV = hs._read(js, binc, hp["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, hp["indices"]).reshape(-1, 3)
    _, inv = np.unique(np.round(P / 1e-6).astype(np.int64), axis=0, return_inverse=True)
    inv = inv.ravel()
    n = inv.max() + 1
    ch = changes(js, binc, hp, names, P, UV, T, inv=inv)
    d_own = ch["own"][0]
    P2 = P.copy()
    P2[:, 2] += d_own
    turn0 = _welded_mean(_vertex_normals(P2, T) - _vertex_normals(P, T), inv, n)
    rows0 = np.abs(turn0).max(1) > 1e-9
    N2 = N.copy()
    a = N[rows0] + turn0[rows0]
    N2[rows0] = a / np.linalg.norm(a, axis=1)[:, None]
    hs._set(js, chunks, hp["attributes"]["POSITION"], P2, minmax=True)
    hs._set(js, chunks, hp["attributes"]["NORMAL"], N2)
    keys_moved, keys_turned = [], 0
    for k, t in enumerate(hp.get("targets", [])):
        nm = names[k] if k < len(names) else str(k)
        D = hs._read(js, binc, t["POSITION"]) if "POSITION" in t else np.zeros_like(P)
        D2 = D
        if nm.startswith("face_") and nm[5:] in ch:
            D2 = D.copy()
            D2[:, 2] += ch[nm[5:]][0] - d_own
            hs._set(js, chunks, t["POSITION"], D2, minmax=True)
            keys_moved.append(nm)
        if "NORMAL" in t:
            turn = _welded_mean(_vertex_normals(P2 + D2, T) - _vertex_normals(P + D, T), inv, n)
            rows = rows0 | (np.abs(turn).max(1) > 1e-9)
            if rows.any():
                dn = hs._read(js, binc, t["NORMAL"])
                a = N[rows] + dn[rows] + turn[rows]
                dn2 = dn.copy()
                dn2[rows] = a / np.linalg.norm(a, axis=1)[:, None] - N2[rows]
                hs._set(js, chunks, t["NORMAL"], dn2)
                keys_turned += 1
    hm.setdefault("extras", {})["lip_sculpt"] = "ls3"
    print("LIPSCULPT: her upper lip remapped on %d faces (own's base by up to %.2f mm; keys %s), %d keys' normals "
          "turned" % (len(ch), np.abs(d_own).max() * 1000, ", ".join(keys_moved), keys_turned))
    return ch


def enabled():
    """WIP (solver ls3): off unless HEROINE_LIPSCULPT=1 (unjudged; see the
    header). Once accepted, make it on by default with HEROINE_LIPSCULPT=0 to build without."""
    return os.environ.get("HEROINE_LIPSCULPT", "0") == "1"


def run(path, out=None):
    """The remap on a glb, written to out or in place. True where written."""
    if not enabled():
        print("LIPSCULPT: off (HEROINE_LIPSCULPT=1 turns it on) - nothing done")
        return False
    js, binc, chunks, hm, hp, names, P, N, UV, T = head(path)
    if not hp.get("targets"):
        print("LIPSCULPT: no head with keys in", path, "- nothing done")
        return False
    if lip_sculpt(js, binc, chunks, hm, hp) is None:
        return False
    hs._save(out or path, js, chunks)
    print("LIPSCULPT: written", out or path)
    return True


# ---- numbers ----

KNOTS = [round(u, 2) for u in np.arange(-0.35, 0.351, 0.05)]


def _at_knots(v, p, face):
    """A per-column height (metres) over the slit as a fraction of the mouth's width, at the knots."""
    _, w, cx = target(face)
    out = []
    for u in KNOTS:
        c = int(round((cx + u * w - X0) / D - 0.5))
        out.append(None if np.isnan(v[c]) or np.isnan(p["slit"][c]) else float((v[c] - p["slit"][c]) / w))
    return out


def _mid_peaks(h):
    H = dict(zip(KNOTS, [np.nan if v is None else v for v in h]))
    return (np.nanmean([H[-0.05], H[0.0], H[0.05]]), np.nanmax([H[-0.1], H[-0.15], H[-0.2]]),
            np.nanmax([H[0.1], H[0.15], H[0.2]]))


def report(ch, glb_changed=True, borders=None):
    """Per face: target, crease before and after (geometric, the strongest concave bend), and the movement outside
    her upper lip; borders: a JSON path for the new borders (for the paint step)."""
    tg = json.load(open(TARGETS))
    out = {"_note": "Solver ls3, 12 Oct 2026: her upper lip's sculpt brought down (heroine_lipsculpt.py). Per face at "
                    "u (fraction of mouth width from its middle): slit_mm, the sculpt's geometric slit's height (her "
                    "head's y, mm, on the face's shaped head); new, the new border's target over the slit (the laying "
                    "portrait's, fraction of w); crease, the geometric border after (strongest concave bend), same "
                    "units; paint, the paint's red top (lip_targets.json); band = new - paint, the skin band the "
                    "paint step fills (mm too).", "u": KNOTS}
    for f, (dz, p, F, S) in ch.items():
        Hf, w, cx = target(f)
        before = crease(F, p)
        after = crease(front(S + np.c_[np.zeros((len(S), 2)), dz], T_HEAD[0], UV_HEAD[0]), p) if glb_changed else before
        new = _at_knots(p["new"], p, f)
        cb, ca = _at_knots(before, p, f), _at_knots(after, p, f)
        paint = tg[f]["paint"]
        # (movement outside her upper lip: under the anchor, over the eased skin's top, past the taper's end)
        cols = np.clip(np.round((S[:, 0] - X0) / D - 0.5).astype(int), 0, len(p["s"]) - 1)
        a, tp = p["anchor"][cols], p["top"][cols]
        inside = ~np.isnan(a) & (S[:, 1] >= a) & (S[:, 1] <= tp + RAMP_T)
        moved = np.abs(dz) > 1e-7
        tn, an_, mn = _mid_peaks(new), _mid_peaks(ca), _mid_peaks(cb)
        err = [abs(x - y) / y for x, y in zip(an_, tn)]
        print("%-9s s %.2f | target %.3f %.3f/%.3f | crease before %.3f %.3f/%.3f after %.3f %.3f/%.3f (err %2.0f%% "
              "%2.0f%% %2.0f%%) | moved %d, up to %.2f mm; outside %.3f mm" % (
                  f, np.nanmedian(p["s"][np.abs(p["u"]) < 0.2]), tn[0], tn[1], tn[2], mn[0], mn[1], mn[2], an_[0],
                  an_[1], an_[2], err[0] * 100, err[1] * 100, err[2] * 100, moved.sum(), np.abs(dz).max() * 1000,
                  np.abs(dz[~inside]).max() * 1000 if (~inside).any() else 0))
        slit_mm = [None if np.isnan(p["slit"][int(round((cx + u * w - X0) / D - 0.5))]) else
                   round(float(p["slit"][int(round((cx + u * w - X0) / D - 0.5))]) * 1000, 2) for u in KNOTS]
        band = [None if (n is None or q is None) else round(n - q, 4) for n, q in zip(new, paint)]
        out[f] = {"w_mm": round(w * 1000, 2), "cx_mm": round(cx * 1000, 2), "slit_mm": slit_mm,
                  "new": [None if v is None else round(v, 4) for v in new],
                  "crease": [None if v is None else round(v, 4) for v in ca], "paint": paint, "band": band,
                  "band_mm": [None if v is None else round(v * w * 1000, 2) for v in band]}
    if borders:
        json.dump(out, open(borders, "w"), indent=1)
        print("LIPSCULPT: new borders written", borders)
    return out


T_HEAD, UV_HEAD = [None], [None]


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] in ("--measure", "--dry"):
        dry = args[0] == "--dry"
        glb = args[1] if len(args) > 1 and args[1].endswith(".glb") else GLB
        faces = [a for a in args[1:] if not a.endswith(".glb")] or list(FACES)
        if "own" not in faces:
            faces = ["own"] + faces
        js, binc, chunks, hm, hp, names, P, N, UV, T = head(glb)
        T_HEAD[0], UV_HEAD[0] = T, UV
        ch = changes(js, binc, hp, names, P, UV, T, faces)
        if not dry:
            ch = {f: (np.zeros_like(v[0]),) + v[1:] for f, v in ch.items()}
        report(ch, glb_changed=dry, borders=BORDERS if dry and len(faces) == len(FACES) else None)
    elif args:
        run(args[0], args[1] if len(args) > 1 else None)
    else:
        print(__doc__)
