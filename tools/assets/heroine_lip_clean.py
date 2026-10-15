"""Her lower lip's paint cleaned of flecks and creases (face lead 26's paint solver, 14 October 2026; UNJUDGED).

A max judge found, at 2x on the Look, a cluster of whitish flecks between the lip lines on Doe's lower lip (centre-left)
and a thin red crease at its middle (the owner's "smudges or missing paint" on B3-15; milder on Saffron). They are the
source portrait's sparkle and a lip crack, baked into the paint. On her lower lip's front (the texels mouth_open takes
down with her jaw, inside heroine_features.png's lip green, from 1 mm under her lips' line down: heroine_inner_lip.roll
places each texel in mm) each texel's difference from its local median (BASE mm across) is soft-limited:

  - lighter than the median: to at most HI (sRGB 0-255 luma, tanh), so sparkle and pale flecks sink into the lip;
  - darker: to at most LO, so the lip lines (her texture) keep their shade but a crack's red line is cut back;
  - the colour of the detail goes with its lightness (a fleck takes its median's colour as it fades).

The region is feathered (FEATHER mm) at the lip's border and its inner edge, so the B3-15 border, shape and colour family
stay; the lips' mean colour moves well under 2%. Nothing outside the region changes.

    python tools/assets/heroine_lip_clean.py [--src DIR] [--to DIR] [--hi HI] [--lo LO] [--wet LIFT] FACE ...   (FACE: doe, saffron, ...; own's paint is
    heroine_head.jpg)

Run after heroine_lip_raise.py / heroine_lip_meet.py (and heroine_inner_lip.py where a face has it).
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_inner_lip as il  # noqa: E402
import heroine_lips as hl  # noqa: E402

FEATURES = os.path.join(hl.TEX, "heroine_features.png")
LUM = np.array([0.299, 0.587, 0.114])
BASE = 2.4        # (mm: the median's window, across)
HI, LO = 3.0, 9.0  # (sRGB luma: the most a texel may sit over / under its median)
TOP, BOTTOM = -1.0, -12.0   # (mm of rest height over her lips' line: the region's top (the lips' meeting line,
#  dark in the paint, sits at -2.5..-3.5 mm and is kept) and bottom)
GUARD = 12.0      # (sRGB luma: texels this much darker than their 4 mm median, in a blob of over GUARD_N texels (the
GUARD_N = 400     #  lips' meeting line, long), are kept, 2 texels round; a crack's short dark line is not kept)
FEATHER = 0.5     # (mm)
LIFT = 1.3        # (the meeting line's band: its smoothed shading times this)
WET_IN = 1.5      # (mm inside the meeting line the band reaches)
KEEP_MEAN = 1.5   # (mm, FWHM: the scale under which the limit's loss of lightness is put back)
FRONT = -5.0      # (mm of rest height: surely the lip's front, to tell it from the inside)
FRONT_SHARE = 0.5 # (a piece of the region is the lip's front if this share of it lies under FRONT)
CUT = 3           # (texels: the meeting line widened by this to cut the front off from the inside, across gaps)


def region(n, x, yl, isl):
    g = np.asarray(Image.open(FEATURES).convert("RGB").resize((n, n), Image.BILINEAR)).astype(float)[..., 1] / 255
    y = np.nan_to_num(yl, nan=99.0)
    m = isl & (g > 0.1) & (y < TOP) & (y > BOTTOM) & (np.abs(np.nan_to_num(x, nan=99.0)) < 25)
    return m


def clean(img, x, yl, isl, hi=HI, lo=LO):
    """img sRGB 0-255 float (n x n x 3) -> cleaned copy, the feathered weight, and the hard region."""
    n = img.shape[0]
    m = region(n, x, yl, isl)
    ys, xs = np.nonzero(m)
    pad = 40
    y0, y1, x0, x1 = ys.min() - pad, ys.max() + pad, xs.min() - pad, xs.max() + pad
    s = img[y0:y1, x0:x1]
    # texel size in mm, from the x map across the region
    gx = np.nanmedian(np.abs(np.diff(x[y0:y1, x0:x1], axis=1))[m[y0:y1, x0:x1][:, 1:]])
    gy = np.nanmedian(np.abs(np.diff(yl[y0:y1, x0:x1], axis=0))[m[y0:y1, x0:x1][1:]])
    mmpt = float(np.hypot(gx, gy))
    k = max(3, int(round(BASE / mmpt)) | 1)
    med = np.dstack([ndimage.median_filter(s[..., c], k) for c in range(3)])
    d = s - med
    dl = d @ LUM
    lim = np.where(dl > 0, hi * np.tanh(dl / hi), -lo * np.tanh(-dl / lo))
    f = np.where(np.abs(dl) > 1e-3, lim / np.where(np.abs(dl) > 1e-3, dl, 1), 1.0)
    out = med + d * f[..., None]
    # (what the limit took, put back as its local mean (KEEP_MEAN mm): the sparkle's speckle goes, its soft highlight
    # and the lip's mean colour stay)
    sg = KEEP_MEAN / 2.355 / mmpt
    out += np.dstack([ndimage.gaussian_filter((d * (1 - f[..., None]))[..., c], sg) for c in range(3)])
    L = s @ LUM
    big = ndimage.median_filter(L, max(3, int(round(4.0 / mmpt)) | 1))
    dark = L < big - GUARD
    lab, nl = ndimage.label(dark, np.ones((3, 3)))
    sz = ndimage.sum(dark, lab, range(1, nl + 1)) if nl else np.zeros(0)
    keep = ndimage.binary_dilation(np.isin(lab, 1 + np.nonzero(sz > GUARD_N)[0]), iterations=2)
    # (the lip's front only: the part of the region the meeting line cuts off from her mouth's inside)
    ms = m[y0:y1, x0:x1]
    lab, nl = ndimage.label(ms & ~ndimage.binary_dilation(keep, iterations=CUT))
    ys_ = np.nan_to_num(yl[y0:y1, x0:x1], nan=99.0)
    idx = range(1, nl + 1)
    front = ndimage.sum(ys_ < FRONT, lab, idx) / np.maximum(ndimage.sum(np.ones_like(ys_), lab, idx), 1)
    big_ = ndimage.sum(np.ones_like(ys_), lab, idx) > 200
    if os.environ.get("LIP_CLEAN_DEBUG"):
        print("  components (size, front share):", [(int(a), round(float(b), 2)) for a, b in zip(ndimage.sum(np.ones_like(ys_), lab, idx), front) if a > 200])
    ms = ndimage.binary_dilation(np.isin(lab, 1 + np.nonzero(big_ & (front > FRONT_SHARE))[0]), iterations=CUT + 1) & ms
    m = np.zeros_like(m)
    m[y0:y1, x0:x1] = ms
    fe = FEATHER / mmpt
    w = ndimage.gaussian_filter(ndimage.binary_erosion(ms, iterations=int(round(fe))).astype(float), fe)
    w = np.where(ms, w, 0.0)
    w *= 1 - (ndimage.gaussian_filter(keep.astype(float), 1.0) * 2).clip(0, 1)
    w = w.clip(0, 1)
    o = img.copy()
    o[y0:y1, x0:x1] = s * (1 - w[..., None]) + out * w[..., None]
    W = np.zeros((n, n))
    W[y0:y1, x0:x1] = w
    return o, W, m, mmpt, k


def wet_line(img, x, yl, isl, lift=LIFT):
    """The lips' meeting line and the 1.5 mm just inside it (what a snarl rolls out under her teeth as a band): its
    paint's brown taken to her lip's own rose (the front's median colour, linear light), at its own shading smoothed
    over 0.4 mm and lifted by LIFT, so the band reads as a shadowed wet lip. At rest that zone is the dark line under
    her upper lip: it keeps its shape and most of its depth."""
    n = img.shape[0]
    y0, y1, x0, x1 = 1450, 1900, 1450, 1950   # (her mouth on the shared UV, at 4096)
    k = n / 4096.0
    y0, y1, x0, x1 = (int(v * k) for v in (y0, y1, x0, x1))
    s = img[y0:y1, x0:x1]
    L = s @ LUM
    big = ndimage.median_filter(L, 31)
    dark = L < big - GUARD
    lab, nl = ndimage.label(dark, np.ones((3, 3)))
    sz = ndimage.sum(dark, lab, range(1, nl + 1))
    I = isl[y0:y1, x0:x1]
    Y = np.nan_to_num(yl[y0:y1, x0:x1], nan=99.0)
    cand = [(ndimage.sum(I & (Y > -4) & (Y < -1.5), lab, i), i) for i in 1 + np.nonzero(sz > GUARD_N)[0]]
    line = lab == max(cand)[1]
    mmpt = 0.131 * 4096 / n
    dist = ndimage.distance_transform_edt(~line)
    ly = np.median(Y[line])
    zone = line | (I & (Y > ly - 0.5) & (dist < WET_IN / mmpt))
    w = ndimage.gaussian_filter(ndimage.binary_dilation(zone, iterations=1).astype(float), 1.5).clip(0, 1)
    lin = np.where(s / 255 <= 0.04045, s / 255 / 12.92, ((s / 255 + 0.055) / 1.055) ** 2.4)
    front = I & (Y < -5) & (Y > -8)
    rose = np.median(lin[front], 0)
    ll = lin @ LUM
    sh = ndimage.gaussian_filter(ll, 0.4 / mmpt / 2.355) * lift
    new = rose[None, None, :] * (sh / (rose @ LUM))[..., None]
    new = np.where(new <= 0.0031308, 12.92 * new, 1.055 * np.clip(new, 0, 1) ** (1 / 2.4) - 0.055) * 255
    o = img.copy()
    o[y0:y1, x0:x1] = s * (1 - w[..., None]) + new * w[..., None]
    W = np.zeros((n, n))
    W[y0:y1, x0:x1] = w
    return o, W, int(zone.sum()), rose



# ---- round 2 (14 October 2026, paint solver; UNJUDGED): what each pose shows, her contact line, her inner lip's band ----

VIEWS = (-25, -17, 0, 17, 25)   # (degrees of yaw at pitch -6, the Look's: a texel counts as seen if any of these sees it)
POSES = {"rest": {}, "smile": {"smile": .8}, "pucker": {"pucker": .8}, "snarl": {"snarl": .8},
         "laugh": {"mouth_open": .6, "smile": .8}, "open": {"mouth_open": .6}}
RES = 0.00004     # (m: the views' pixel)
BOX = (-0.026, 0.026, -0.026, 0.006)   # (m about her mouth's middle and her lips' line)
MMPT = 0.131      # (mm per texel at 4096, on her lips)
WIN = (1560, 1880, 1440, 1880)   # (her mouth's window on the shared UV at 4096: rows, cols)


class Geo:
    """Her head, teeth and tongue from heroine.glb, posed as the game does (face key, lips_lower+ at the face's own
    fullness from looks.json, expression keys; smile with mouth_open adds smile_open and smile_hold)."""

    def __init__(self, path=None):
        import heroine_mouth as hmo
        import heroine_mouth_inner as hmi
        import heroine_seam as hs
        self.hmo = hmo
        js, binc = hs._load(path or hl.GLB)
        self.m = {}
        for mat in ("skin_head", "teeth", "tongue"):
            mm, pp = hmo._prim(js, mat)
            names = mm["extras"]["targetNames"]
            V = hs._read(js, binc, pp["attributes"]["POSITION"]).astype(np.float64)
            T = hs._read(js, binc, pp["indices"]).astype(np.int64).reshape(-1, 3)
            D = {k: hs._read(js, binc, t["POSITION"]).astype(np.float64) for k, t in zip(names, pp["targets"])
                 if k.startswith("face_") or k in ("smile", "mouth_open", "smile_open", "smile_hold", "snarl", "pucker",
                                                    "lips_lower+")}
            self.m[mat] = (V, T, D)
            if mat == "skin_head":
                self.uv = hs._read(js, binc, pp["attributes"]["TEXCOORD_0"]).astype(np.float64)
        self.lips = hmi._lips()

    def pose(self, mat, face, kv):
        V, T, D = self.m[mat]
        kv = dict(kv)
        mo, sm = kv.get("mouth_open", 0), kv.get("smile", 0)
        if sm and mo:
            o = min(mo / 0.3, 1)
            kv["smile_open"], kv["smile_hold"] = sm * o * o * (3 - 2 * o), sm * mo
        P = V.copy()
        if face != "own" and "face_" + face in D:
            P += D["face_" + face]
        if "lips_lower+" in D:
            P += self.lips.get(face, 0.0) * D["lips_lower+"]
        for k, v in kv.items():
            if k in D and v:
                P += v * D[k]
        return P

    def seen(self, face, kv, n=4096):
        """n x n bool: her head's texels any of VIEWS sees in this pose (her teeth and tongue hide what's behind them)."""
        P0 = self.pose("skin_head", face, {})
        line = self.hmo.lips_line(P0, self.m["skin_head"][2]["mouth_open"])
        x0 = np.median(P0[(np.abs(P0[:, 1] - line) < 0.004) & (P0[:, 2] > 0.09), 0])
        zf = P0[(np.abs(P0[:, 1] - line) < 0.003) & (np.abs(P0[:, 0] - x0) < 0.005), 2].max()
        c = np.array([x0, line, zf])
        out = np.zeros((n, n), bool)
        nx, ny = int((BOX[1] - BOX[0]) / RES), int((BOX[3] - BOX[2]) / RES)
        posed = {mat: self.pose(mat, face, kv) for mat in self.m}
        for yaw in VIEWS:
            a, b = np.radians(yaw), np.radians(-6.0)
            R = (np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
                 @ np.array([[np.cos(a), 0, -np.sin(a)], [0, 1, 0], [np.sin(a), 0, np.cos(a)]]))
            Z = np.full((ny, nx), -1e9)
            TR = np.full((ny, nx), -1, np.int64)   # (her head's triangle; -2 teeth or tongue)
            for mat in self.m:
                V, T, D = self.m[mat]
                tri = ((posed[mat] - c) @ R.T)[T]
                lo, hi = tri.min(1), tri.max(1)
                sel = np.where((hi[:, 0] > BOX[0]) & (lo[:, 0] < BOX[1]) & (hi[:, 1] > BOX[2]) & (lo[:, 1] < BOX[3]))[0]
                for i in sel:
                    p, q, r = tri[i]
                    ix0, ix1 = max(int((lo[i, 0] - BOX[0]) / RES), 0), min(int((hi[i, 0] - BOX[0]) / RES) + 1, nx)
                    iy0, iy1 = max(int((lo[i, 1] - BOX[2]) / RES), 0), min(int((hi[i, 1] - BOX[2]) / RES) + 1, ny)
                    if ix1 <= ix0 or iy1 <= iy0:
                        continue
                    d = (q[1] - r[1]) * (p[0] - r[0]) + (r[0] - q[0]) * (p[1] - r[1])
                    if abs(d) < 1e-16:
                        continue
                    X, Y = np.meshgrid(BOX[0] + (np.arange(ix0, ix1) + 0.5) * RES, BOX[2] + (np.arange(iy0, iy1) + 0.5) * RES)
                    l1 = ((q[1] - r[1]) * (X - r[0]) + (r[0] - q[0]) * (Y - r[1])) / d
                    l2 = ((r[1] - p[1]) * (X - r[0]) + (p[0] - r[0]) * (Y - r[1])) / d
                    h = (l1 >= 0) & (l2 >= 0) & (l1 + l2 <= 1)
                    z = l1 * p[2] + l2 * q[2] + (1 - l1 - l2) * r[2]
                    zs = Z[iy0:iy1, ix0:ix1]
                    w = h & (z > zs)
                    if w.any():
                        zs[w] = z[w]
                        TR[iy0:iy1, ix0:ix1][w] = i if mat == "skin_head" else -2
            V, T, D = self.m["skin_head"]
            Q = (posed["skin_head"] - c) @ R.T
            iy, ix = np.nonzero(TR >= 0)
            t = TR[iy, ix]
            px, py = BOX[0] + (ix + 0.5) * RES, BOX[2] + (iy + 0.5) * RES
            p, q, r = Q[T[t, 0], :2], Q[T[t, 1], :2], Q[T[t, 2], :2]
            d = (q[:, 1] - r[:, 1]) * (p[:, 0] - r[:, 0]) + (r[:, 0] - q[:, 0]) * (p[:, 1] - r[:, 1])
            l1 = ((q[:, 1] - r[:, 1]) * (px - r[:, 0]) + (r[:, 0] - q[:, 0]) * (py - r[:, 1])) / d
            l2 = ((r[:, 1] - p[:, 1]) * (px - r[:, 0]) + (p[:, 0] - r[:, 0]) * (py - r[:, 1])) / d
            uv = l1[:, None] * self.uv[T[t, 0]] + l2[:, None] * self.uv[T[t, 1]] + (1 - l1 - l2)[:, None] * self.uv[T[t, 2]]
            tx = np.clip((uv * n).astype(int), 0, n - 1)
            out[tx[:, 1], tx[:, 0]] = True
        return out


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(c, 0, 1)
    return 255.0 * np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def _win(a):
    return a[WIN[0]:WIN[1], WIN[2]:WIN[3]]


def _xprof(xv, vals, sel, step=0.5, sig=1.0, q=50):
    """A per-x profile (percentile q of vals over sel, in step mm bins, smoothed sig mm), read back at xv."""
    bx = np.arange(-20, 20.01, step)
    v = np.array([np.percentile(vals[sel & (np.abs(xv - b) < step / 2)], q) if (sel & (np.abs(xv - b) < step / 2)).sum() > 3
                  else np.nan for b in bx])
    ok = np.isfinite(v)
    v = np.interp(bx, bx[ok], v[ok])
    v = ndimage.gaussian_filter1d(v, sig / step)
    return np.interp(xv, bx, v)


def meeting_line(s, I, Y):
    """The paint's dark meeting line on her lower lip (window crop s): the long dark blob (GUARD under its 31-texel
    median, over GUARD_N texels) lying most at -4..-1.5 mm of rest height."""
    L = s @ LUM
    dark = L < ndimage.median_filter(L, 31) - GUARD
    lab, nl = ndimage.label(dark, np.ones((3, 3)))
    sz = ndimage.sum(dark, lab, range(1, nl + 1))
    cand = [(ndimage.sum(I & (Y > -4) & (Y < -1.5), lab, i), i) for i in 1 + np.nonzero(sz > GUARD_N)[0]]
    return (lab == max(cand)[1]) & I


RF = 1.2          # (mm in front of the meeting line where her lip's front is full colour)
LB = 0.5          # (mm into that front where the move starts)
LINE_IN = 0.1     # (share of the line's width laid past the contact, under her upper lip)
WSCALE = 2.0      # (the line's width, times: the lip's top turns from the eye, so the line shows thinner there)
CX = (11.0, 14.0)  # (mm off her mouth's middle: the move full, none)


def contact(img, x, yl, isl, rest):
    """Her lower lip's dark meeting line moved up to where her lips meet at rest (the edge of what VIEWS see with
    her mouth shut, `rest`), its own width kept; the ramp from it to her lip's front stretched over the gap, so the
    band of paint between the old line and the contact (Saffron: a grey band, then the line: a second line under the
    crease) goes. Sampled along x (mm) and a (mm from the lip's full front) from the paint itself. Under the contact
    (hidden at rest) it holds the line's inner edge; inner_band() then lays the inner lip's colour there."""
    from scipy.interpolate import griddata
    s = _win(img)
    I = _win(isl)
    X, Y = np.nan_to_num(_win(x), nan=99.0), np.nan_to_num(_win(yl), nan=99.0)
    R = ndimage.binary_opening(ndimage.binary_closing(_win(rest) & I, iterations=2), iterations=2)
    line = meeting_line(s, I, Y)
    lab, nl = ndimage.label(I & ~ndimage.binary_dilation(line, iterations=2))
    fr = ndimage.sum(Y < -5, lab, range(1, nl + 1))
    front = (lab == 1 + int(np.argmax(fr))) & I
    dl = ndimage.distance_transform_edt(~line) * MMPT
    F = front & (dl >= RF)
    a = ndimage.distance_transform_edt(~F) * MMPT - ndimage.distance_transform_edt(F) * MMPT
    hid = I & ~R
    b = ndimage.distance_transform_edt(~hid) * MMPT        # (visible texels: mm to the contact)
    dv = ndimage.distance_transform_edt(~(I & R)) * MMPT   # (hidden texels: mm past it)
    zone = I & (a > -LB - 1) & (np.abs(X) < 20)
    S = np.where(hid, a - dv, a + b)
    zs = zone & (a > 0) & (np.where(hid, dv, b) < 4)
    sg = 0.5 / MMPT
    S = ndimage.gaussian_filter(np.where(zs, S, 0), sg) / np.maximum(ndimage.gaussian_filter(zs.astype(float), sg), 1e-6)
    alb = _xprof(X, a, line, q=10)
    alt = _xprof(X, a, line, q=90)
    w = np.maximum(alt - alb, 0.2)
    h1, h2 = (1 - LINE_IN) * w * WSCALE, LINE_IN * w * WSCALE
    n_ = a
    o = np.where(n_ <= -LB, n_,
        np.where(n_ <= S - h1, -LB + (n_ + LB) * (alb + LB) / np.maximum(S - h1 + LB, 1e-3),
        np.where(n_ <= S + h2, alb + (n_ - (S - h1)) * w / (h1 + h2), alt)))
    o = np.where(S - h1 > alb, o, n_)   # (where the line is already at the contact nothing moves)
    src = zone & (a < float(alt.max()) + 0.5)
    K = 3.0   # (a's scale against x in the interpolation)
    tgt = zone & (n_ > -LB) & (np.abs(o - n_) > 1e-3)
    new = griddata(np.c_[X[src], K * a[src]], s[src], np.c_[X[tgt], K * o[tgt]], method="linear")
    bad = ~np.isfinite(new).all(1)
    new[bad] = s[tgt][bad]
    out = s.copy()
    out[tgt] = new
    wx = 1 - _ss((np.abs(X) - CX[0]) / (CX[1] - CX[0]))
    wt = ndimage.gaussian_filter(zone.astype(float), 1.0) * wx
    res = s * (1 - wt[..., None]) + out * wt[..., None]
    o_img = img.copy()
    o_img[WIN[0]:WIN[1], WIN[2]:WIN[3]] = res
    return o_img, dict(moved=int((tgt & (wt > 0.5)).sum()), bad=int(bad.sum())), dict(a=a, S=S, alb=alb, alt=alt, line=line, hid=hid, X=X, o=o)


SAT = 1.15        # (the inner band's saturation against her lip front's, linear)
BRIGHT = 0.9      # (its sRGB brightness against her lip front's)
DETAIL = 0.25     # (share of the paint's own fine shading kept in it)
IN0, IN1 = 0.15, 0.4   # (mm past the contact: the band's colour from none to full, so her rest face doesn't change)
DEEP = 1.0        # (mm: its soft darkening before the deepest point a pose shows, to DEEP_TO)
DEEP_TO = 0.7
INNER_X = (11.0, 14.0)


def inner_band(img, x, yl, isl, rest, shown):
    """Her lower lip's inner band (hidden at rest, `rest` False; shown in a snarl, laugh, open or pucker, `shown`):
    her lip front's own colour (median, linear) a touch more saturated (SAT) at BRIGHT of its brightness, with
    DETAIL of the paint's fine shading, darkening softly (to DEEP_TO) over the last DEEP mm before the deepest point
    the poses show (her teeth). Eased in from IN0 to IN1 mm past the contact."""
    s = _win(img)
    I = _win(isl)
    X, Y = np.nan_to_num(_win(x), nan=99.0), np.nan_to_num(_win(yl), nan=99.0)
    R = ndimage.binary_opening(ndimage.binary_closing(_win(rest) & I, iterations=2), iterations=2)
    Sh = ndimage.binary_closing(_win(shown) & I, iterations=2) & ~R
    dv = ndimage.distance_transform_edt(~R) * MMPT
    L = _lin(s)
    fr = I & R & (Y < -5) & (Y > -8) & (np.abs(X) < 8)
    base = np.median(L[fr], 0)
    m = base.mean()
    col = m + (base - m) * SAT
    col *= (BRIGHT ** 2.2) * (base @ LUM) / (col @ LUM)
    deep = _xprof(X, dv, Sh, q=95)
    f = 1 - (1 - DEEP_TO) * _ss((dv - (deep - DEEP)) / (DEEP + 0.3))
    ll = L @ LUM
    sm = ndimage.gaussian_filter(ll, 0.6 / MMPT)
    det = np.clip(ll / np.maximum(sm, 1e-4), 0.5, 1.6) ** DETAIL
    new = col[None, None, :] * (f * det)[..., None]
    wx = 1 - _ss((np.abs(X) - INNER_X[0]) / (INNER_X[1] - INNER_X[0]))
    w = _ss((dv - IN0) / (IN1 - IN0)) * (I & ~R) * wx
    O = L * (1 - w[..., None]) + new * w[..., None]
    o_img = img.copy()
    o_img[WIN[0]:WIN[1], WIN[2]:WIN[3]] = _srgb(O)
    return o_img, dict(texels=int((w > 0.5).sum()), base=base.round(3), col=col.round(3),
                       deep=round(float(np.median(deep[Sh])), 2) if Sh.any() else 0)

def main():
    a = sys.argv[1:]
    opt = {"--src": hl.TEX, "--to": None, "--hi": HI, "--lo": LO, "--wet": None}
    for flag in list(opt):
        if flag in a:
            i = a.index(flag)
            opt[flag] = a[i + 1]
            del a[i:i + 2]
    src, to, hi, lo = opt["--src"], opt["--to"], float(opt["--hi"]), float(opt["--lo"])
    a = [v for v in a if v not in ("--contact", "--inner")]
    files = hl.paints()
    cache = {}
    for f in a:
        p = os.path.join(src, files[f])
        img = np.asarray(Image.open(p).convert("RGB")).astype(np.float64)
        n = img.shape[0]
        if n not in cache:
            cache[n] = il.roll(n)
        if opt["--wet"] is not None:   # (--wet LIFT: the meeting line's band too, first)
            img0 = img
            img, ww, nz, rose = wet_line(img, *cache[n], lift=float(opt["--wet"]))
            print("LIP_CLEAN %s: meeting line's band %d texels, rose (linear) %s, max change %.1f"
                  % (f, nz, np.round(rose, 3), np.abs(img - img0).max()))
        for flag in ("--contact", "--inner"):   # (round 2: her meeting line to the contact; her inner band's colour)
            if flag not in sys.argv:
                continue
            if "geo" not in cache:
                cache["geo"] = Geo()
                cache["seen"] = {}
            g = cache["geo"]
            for pz in (("rest",) if flag == "--contact" else ("rest", "snarl", "laugh", "open", "pucker")):
                if (f, pz) not in cache["seen"]:
                    cache["seen"][(f, pz)] = g.seen(f, POSES[pz], n)
            sv = cache["seen"]
            img0 = img
            if flag == "--contact":
                img, info, _ = contact(img, *cache[n], sv[(f, "rest")])
            else:
                shown = sv[(f, "snarl")] | sv[(f, "laugh")] | sv[(f, "open")] | sv[(f, "pucker")]
                img, info = inner_band(img, *cache[n], sv[(f, "rest")], shown)
            print("LIP_CLEAN %s %s: %s, max change %.1f" % (f, flag, info, np.abs(img - img0).max()))
        if hi <= 0:   # (--hi 0: the meeting line's band only, no fleck pass)
            dst = os.path.join(to, files[f]) if to else p
            Image.fromarray(np.clip(img + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)
            print("LIP_CLEAN %s: written %s" % (f, dst))
            continue
        out, w, m, mmpt, k = clean(img, *cache[n], hi=hi, lo=lo)
        sel = w > 0.5
        before, after = img[m].mean(0), out[m].mean(0)
        dst = os.path.join(to, files[f]) if to else p
        Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)
        print("LIP_CLEAN %s: %d texels (%.3f mm/texel, median %d); lip mean %s -> %s (%.2f%%); max change %.1f; %s"
              % (f, int(sel.sum()), mmpt, k, np.round(before, 1), np.round(after, 1),
                 100 * np.abs(after - before).max() / before.mean(), np.abs(out - img).max(), dst))


if __name__ == "__main__":
    main()
