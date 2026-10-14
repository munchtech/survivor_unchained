"""The upper lip's lowest edge shaded as her own face's is (face lead 23, 14 October 2026; judge r1).

Judge r1 saw a pale strip along Saffron's upper lip's lower edge at the Look (fainter on Hard-won): "missing paint".
A debug paint (texels coloured by height over the sculpt's meeting line m, heroine_lips.lines) put the strip in the
upper lip's lowest 0.5 mm, front-facing: from 6 degrees under her that edge faces the camera. Measured in the paints
over the middle third (CIE L*, against the lip's body 1-1.5 mm up): own, which shows no strip, is shaded there like a
real lip's curl (-17 at 0-0.25 mm, -5 at 0.25-0.5, -36 at -0.5-0 mm, the line); Saffron is LIGHTER (+4, +4, -10),
Hard-won about even (-5, -1, -21). So each band's lightness is brought to the target (TARGET, L* under the body) by a
gain on its linear colour (hue, lines and grain kept), only where the paint is lighter than the target, smooth in
height, eased out over the outer fifth toward each corner.

    python tools/assets/heroine_lip_meet.py [--measure] [--to DIR] [--from DIR] [--glb GLB] face ...
--measure prints each band's L* against the body without writing.
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lips as hl  # noqa: E402
import heroine_lipsculpt as ls  # noqa: E402

# (band centre over the meet in m, L* under the lip's body there)
TARGET = [(-0.00075, 32.0), (-0.00025, 30.0), (0.000125, 13.0), (0.000375, 4.0), (0.0006, 0.0)]
BODY = (0.001, 0.0015)
# (judge r3: at the tubercle the lowest edge faces the key and still read as a pale crescent: there the shade goes deeper and
#  higher, L* more under the body by height, weighted by exp(-(x / CENTRE)^2) across her mouth's middle)
EXTRA = [(-0.00025, 6.0), (0.000125, 18.0), (0.000375, 16.0), (0.00075, 9.0), (0.00125, 4.0), (0.00175, 0.0)]
CENTRE = 0.005
BANDS = [(-0.001, -0.0005), (-0.0005, 0.0), (0.0, 0.00025), (0.00025, 0.0005), (0.0005, 0.001)]


def lin(c):
    c = np.clip(c / 255.0, 0, 1)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return 255.0 * np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def L_of_Y(Y):
    Y = np.maximum(Y, 1e-6)
    return np.where(Y > 0.008856, 116 * np.cbrt(Y) - 16, 903.3 * Y)


def Y_of_L(L):
    return np.where(L > 8, ((L + 16) / 116) ** 3, L / 903.3)


def band_Y(Fi, m, lo, hi, a, b):
    """Mean linear luminance of the front image between heights a..b over m, columns lo..hi."""
    Yl = lin(Fi) @ np.array([0.2126, 0.7152, 0.0722])
    v = []
    for c in range(lo, hi):
        r0, r1 = int(hl.row(m[c] + b)), int(hl.row(m[c] + a))
        v.append(Yl[r0:r1 + 1, c])
    return float(np.concatenate(v).mean())


def shade(img, F, m, P, UV, TRI, write=True):
    Fi = hl.at_uv(img, np.nan_to_num(F[..., 0]), np.nan_to_num(F[..., 1]))
    x = np.arange(len(m))
    okm = ~np.isnan(m)
    lo, hi = x[okm].min(), x[okm].max()
    t0, t1 = lo + (hi - lo) // 3, hi - (hi - lo) // 3
    Lb = float(L_of_Y(band_Y(Fi, m, t0, t1, *BODY)))
    got = [float(L_of_Y(band_Y(Fi, m, t0, t1, a, b))) - Lb for a, b in BANDS]
    if not write:
        return None, 0, Lb, got
    # (gain per band centre: to the target where the paint is lighter, else 1; interpolated in height)
    yc = np.array([(a + b) / 2 for a, b in BANDS])
    tl = np.interp(yc, [t[0] for t in TARGET], [t[1] for t in TARGET])
    cur = np.array(got) + Lb
    want = np.minimum(cur, Lb - tl)
    gain = Y_of_L(want) / Y_of_L(cur)
    n = img.shape[0]
    G = hl.in_uv(P, UV, TRI, n, None)
    gx, gy, gz = G[..., 0], G[..., 1], G[..., 2]
    has = ~np.isnan(gx)
    rr, cc = hl.row(np.nan_to_num(gy)), hl.col(np.nan_to_num(gx))
    has &= (rr >= 0) & (rr < F.shape[0] - 1) & (cc >= lo) & (cc <= hi)
    zf = hl.sample(np.nan_to_num(F[..., 2], nan=-1.0), rr[has], cc[has])
    front = np.abs(zf - gz[has]) < 0.001
    ti, tj = (a[front] for a in np.where(has))
    c_s = cc[has][front]
    y = gy[ti, tj] - np.interp(c_s, x[okm], m[okm])
    go = (y > BANDS[0][0] - 0.0002) & (y < EXTRA[-1][0])
    ti, tj, c_s, y = ti[go], tj[go], c_s[go], y[go]
    yy = np.concatenate([[BANDS[0][0] - 0.0002], yc, [BANDS[-1][1]]])
    gg = np.concatenate([[1.0], gain, [1.0]])
    g = np.interp(y, yy, gg)
    tb = np.interp(y, [q[0] for q in TARGET], [q[1] for q in TARGET], right=0.0)
    xm = (c_s - hl.col(0.0)) * hl.D
    te = np.interp(y, [q[0] for q in EXTRA], [q[1] for q in EXTRA], left=0.0, right=0.0) * np.exp(-(xm / CENTRE) ** 2)
    g = g * Y_of_L(Lb - tb - te) / Y_of_L(Lb - tb)
    e = np.clip(np.minimum(c_s - lo, hi - c_s) / (0.2 * (hi - lo)), 0, 1)
    e = e * e * (3 - 2 * e)
    g = 1 + (g - 1) * e
    out = img.copy()
    out[ti, tj] = srgb(lin(img[ti, tj]) * g[:, None])
    return out, len(ti), Lb, got


def main():
    args = sys.argv[1:]
    to, frm, glb, measure = None, hl.TEX, hl.GLB, False
    for flag in ("--to", "--from", "--glb"):
        if flag in args:
            i = args.index(flag)
            v = args[i + 1]
            del args[i:i + 2]
            to, frm, glb = (v, frm, glb) if flag == "--to" else (to, v, glb) if flag == "--from" else (to, frm, v)
    if "--measure" in args:
        args.remove("--measure")
        measure = True
    pp = hl.paints()
    ao = np.asarray(Image.open(os.path.join(hl.TEX, "heroine_ao.png")).convert("RGBA")).astype(np.float64)[..., 0] / 255
    js, binc, chunks, hm, hp, names, P0, N0, UV0, T0 = ls.head(glb)
    UV, TRI = UV0.astype(np.float64), T0.astype(np.int64).reshape(-1, 3)
    for f in args or ls.FACES:
        P = ls.shaped(js, binc, hp, names, P0, f).astype(np.float64)
        F = hl.front(P, UV, TRI)
        m, t, _, _ = hl.lines(F, ao)
        img = np.asarray(Image.open(os.path.join(frm, pp[f])).convert("RGB")).astype(np.float64)
        out, nt, Lb, got = shade(img, F, m, P, UV, TRI, not measure)
        print("LIPMEET %-9s body L*%.1f, bands %s%s" % (f, Lb, " ".join("%+.1f" % g for g in got),
                                                     "" if measure else ", %d texels" % nt))
        if not measure:
            dst = os.path.join(to, pp[f]) if to else os.path.join(frm, pp[f])
            Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)


if __name__ == "__main__":
    main()
