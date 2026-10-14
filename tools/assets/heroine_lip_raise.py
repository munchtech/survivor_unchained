"""Her upper lip's red raised in each face's paint by stretching the paint's own upper lip up her face (lips B3).

The owner, 14 October 2026: "shouldn't bottom lip be bigger than top lip?", then on lips B3 (her lower lip about 15%
fuller by shape, the lips_lower slider; her upper lip about 2/3 of her lower one): "b3-15 is a clear winner - however
it also clearly needs refinement, it has smudges or missing paint". B3's paints (heroine_lip_color.py --upper-paint)
laid a flat target colour over a band above the paint's red: opaque and rosier than her lip, cut square where her
head's crease stops being found (about +-15 mm), the corners of her mouth left skin, a thin strip with square ends on
Moonlit, and on her own face a 0.7 mm line of skin left under her sculpt's border.

This stretches each paint's own upper lip instead, column by column seen from in front on the face's own shaped head:
its red, from LOW over the mouth line to just under its old top (TOP_IN), is laid from LOW up to the new top, so its
colour, its lines and the run of its shade come along whole and meet the lip under them with no seam (the stretch
eases in over RAMP). The new top is the paint's own red top (found from above by its lipness, Lab a* - b*/2, which
tells lip from skin on every face, Sunborn's too), smoothed, its height over the mouth line scaled by the face's factor
(eased back to 1 at the corners of her mouth, so the red tapers into them as the portrait's did), or taken to her
sculpt's border (k "border": on her own face the border is within a millimetre of the B3 red; on the other faces it
is 2-3 mm over it, and the red stays where the owner's 2/3 puts it). Over the new top the skin is the paint's own,
met in a crisp smoothstep (EDGE wide). Inside the new red, the paint's broad pale or dark patches (a portrait's
highlight stretched with the rest) are evened toward the lip's own colour (EVEN, over EVEN_SIGMA), its fine detail kept.

    python tools/assets/heroine_lip_raise.py [--to DIR] [--k own=border,moonlit=1.3,...] [--glb GLB] [face ...]

Run on the paints fresh from the chain (heroine_face.py's lay, heroine_jaw_cut.py, heroine_ears.py, ...), instead of
heroine_lip_color.py. Not idempotent: it raises whatever red it finds (write with --to, or run once).
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lips as hl  # noqa: E402
import heroine_lipsculpt as ls  # noqa: E402

LOW = 0.0004        # (m: under this over the mouth line nothing moves: the dark of the lips' meeting kept)
RAMP = 0.0008       # (the stretch eases in over this above LOW)
TOP_IN = 0.0005     # (the stretched red ends this far under the paint's old red top: its soft edge left behind)
EDGE = 0.00035      # (the new top's smoothstep, lip to skin: the B3 sheet's crisp border)
UNDER = 0.00015     # (k "border": the new top's middle this far under the border's crease)
CORNER = 0.005      # (the factor eases from 1 at the corners of her mouth to k this far in)
BORDER_K = 2.6      # (k "border": the red's own height scaled so toward the corners, where that is under the border)
EVEN_F = {"own": 0.92}  # (her own paint's red has a dark mark that the stretch would draw out tall)
HEAL = 0.82         # (a mark this much darker than the red about it is healed before the stretch)
FADE = 0.0005       # (the raise fades out where it lifts the red less than this: toward the corners of her mouth)
EVEN = 0.7          # (the broad patches inside the new red evened this much toward the lip's colour)
EVEN_SIGMA = 10.0   # (front-grid px, 1 mm: what counts as broad)
EVEN_FROM = 0.0012  # (evening starts this far over the mouth line: the lips' meeting keeps its shade)
SMOOTH = (31, 12)   # (the old red top's height across her mouth: a median, then a gaussian, front-grid px)
K = {"own": "border"}
LUMA = np.array([0.2126, 0.7152, 0.0722])


def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def lipness(img):
    """Lab a* - b*/2 of an sRGB image (0-255): high on lips, low on skin."""
    c = lin(np.nan_to_num(img))
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return 500 * (f[..., 0] - f[..., 1]) - 0.5 * 200 * (f[..., 1] - f[..., 2])


def red_top(Fi, m, top=0.011, run_mm=0.5):
    """Per column the top of the paint's upper red: coming down from `top` over the mouth line, the first run_mm
    whose lipness is past halfway from the skin's (9.5-12.5 mm over the mouth line) to the lip's (0.5-3 mm)."""
    r = ndimage.uniform_filter(lipness(Fi), (3, 5))
    e = np.full(len(m), np.nan)
    n = int(round(run_mm / 1000 / hl.D))
    for c in np.where(~np.isnan(m))[0]:
        i_m = int(round(hl.row(m[c])))
        lip = np.percentile(r[i_m - 30:i_m - 5, c], 80)
        skin = np.median(r[i_m - 125:i_m - 95, c])
        if lip - skin < 4:
            continue
        mid = 0.5 * (skin + lip)
        run = 0
        for i in range(i_m - int(round(top / hl.D)), i_m - 2):
            run = run + 1 if r[i, c] > mid else 0
            if run >= n:
                e[c] = hl.Y1 - (i - n + 1 + 0.5) * hl.D
                break
    return e


def heights(m, e):
    """The old red top's height over the mouth line, smoothed across her mouth, carried to the corners of her mouth
    (columns where the mouth line is): past the last found, down to 0.4 mm at the corner."""
    x = np.arange(len(m))
    ok = ~np.isnan(m)
    c0, c1 = x[ok].min(), x[ok].max()
    h = e - m
    good = ~np.isnan(h)
    g0, g1 = x[good].min(), x[good].max()
    hf = np.interp(x, x[good], h[good])
    hf[x < g0] = np.interp(x[x < g0], [c0, g0], [0.0004, hf[g0]])
    hf[x > g1] = np.interp(x[x > g1], [g1, c1], [hf[g1], 0.0004])
    hs = ndimage.gaussian_filter1d(ndimage.median_filter(hf, SMOOTH[0]), SMOOTH[1])
    hs[~ok] = np.nan
    return hs


def target(m, t, hs, k):
    """The new red top's height over the mouth line: hs scaled by k (eased to 1 at the corners), or (k "border") the
    border's crease less UNDER where it is found, the scaled red at 2.4 beyond, never past the border."""
    x = np.arange(len(m))
    ok = ~np.isnan(m)
    c0, c1 = x[ok].min(), x[ok].max()
    dist = np.minimum(x - c0, c1 - x) * hl.D
    u = np.clip(dist / CORNER, 0, 1)
    tau = u * u * (3 - 2 * u)
    if k != "border":
        return hs * (1 + (float(k) - 1) * tau)
    import heroine_lip_color as hc                                 # (B3's border: the crease, tapered to the corners)
    b = hc.border(m, t) - m - UNDER
    sc = hs * (1 + (BORDER_K - 1) * tau)
    H = ndimage.gaussian_filter1d(np.nan_to_num(np.minimum(sc, b)), 10)
    H = np.minimum(H, b)
    H[~ok] = np.nan
    return H


def source_height(y, H, S):
    """Where in the old paint (height over the mouth line) the new paint at height y takes its colour from, per
    column (y, H, S broadcast): identity under LOW, easing over RAMP into a stretch that brings S (the old red's top
    less TOP_IN) up to H - EDGE/2."""
    Ht = H - EDGE / 2
    rho = 1 - (Ht - S) / np.maximum(Ht - LOW - RAMP / 2, 1e-5)      # (source per target, over the ramp)
    rho = np.clip(rho, 0.15, 1.0)
    v = np.clip((y - LOW) / RAMP, 0, 1)
    sig_int = np.where(y < LOW, 0.0, np.where(y < LOW + RAMP, RAMP * (v ** 3 - v ** 4 / 2), y - LOW - RAMP / 2))
    return y + (rho - 1) * sig_int


def raise_face(face, img, F, m, t, k, log=True):
    """The face's paint (n x n x 3, sRGB 0-255) with its upper lip raised; also the front-grid fields for a look."""
    Fi = hl.at_uv(img, np.nan_to_num(F[..., 0]), np.nan_to_num(F[..., 1]))
    e = red_top(Fi, m)
    hs = heights(m, e)
    H = target(m, t, hs, k)
    S = np.maximum(hs - TOP_IN, LOW + 0.0001)
    beta = np.clip(np.nan_to_num(H - hs) / FADE, 0, 1)
    beta = beta * beta * (3 - 2 * beta)                            # (the raise's strength: none where it lifts nothing)
    act = beta > 0
    ny, nx = Fi.shape[:2]
    ys = hl.Y1 - (np.arange(ny) + 0.5) * hl.D
    Y = ys[:, None] - m[None, :]
    # (marks in the red that the stretch would draw out tall (her own face's dark spot): darker than the red about
    #  them by HEAL, wider than a lip line, lifted to it)
    lum = lin(Fi) @ LUMA
    bg = ndimage.median_filter(lum, (15, 31))
    rel = lum / np.maximum(bg, 1e-5)
    zone = act[None, :] & (Y > 0.0003) & (Y < hs[None, :])
    mk = ndimage.binary_opening(zone & (rel < HEAL), np.ones((3, 5)))
    mk = ndimage.gaussian_filter(ndimage.binary_dilation(mk, iterations=3).astype(float), 1.5)
    Fi = Fi * (1 - mk[..., None]) + srgb(lin(Fi) * np.clip(bg / np.maximum(lum, 1e-5), 1, 2)[..., None]) * mk[..., None]
    # (front grid: every column's new paint, for the evening and a look)
    sy = source_height(Y, H[None, :], S[None, :])
    src_rows = hl.row(m[None, :] + sy)
    cols = np.repeat(np.arange(nx)[None, :], ny, 0).astype(float)
    good = act[None, :] & ~np.isnan(Y)
    Wp = np.zeros((ny, nx, 3))
    rr, cc = np.where(good)
    Wp[rr, cc] = hl.sample(Fi, src_rows[rr, cc], cols[rr, cc])
    Lw = lin(Wp)
    # (the broad patches: the stretched red's colour smoothed inside its own bounds, against the lip's colour, a
    #  per-column median smoothed across her mouth)
    inside = good & (Y > EVEN_FROM) & (Y < H[None, :] - EDGE)
    wm = inside.astype(float)
    den = ndimage.gaussian_filter(wm, EVEN_SIGMA)
    G = np.stack([ndimage.gaussian_filter(Lw[..., c] * wm, EVEN_SIGMA) for c in range(3)], -1) / np.maximum(den, 1e-6)[..., None]
    ref = np.full((nx, 3), np.nan)
    for c in np.where(act)[0]:
        sel = inside[:, c]
        if sel.sum() > 5:
            ref[c] = np.median(Lw[sel, c], 0)
    x = np.arange(nx)
    for ch in range(3):
        okr = ~np.isnan(ref[:, ch])
        if okr.sum() > 3:
            ref[:, ch] = ndimage.gaussian_filter1d(ndimage.median_filter(np.interp(x, x[okr], ref[okr, ch]), 31), 30)
    ramp = np.clip((Y - EVEN_FROM) / 0.0008, 0, 1)
    ramp = np.where(good, ramp * ramp * (3 - 2 * ramp), 0)
    tgt = G + EVEN_F.get(face, EVEN) * (ref[None, :, :] - G) * ramp[..., None]
    gain = np.where(good[..., None], tgt / np.maximum(G, 1e-5), 1.0)
    gain = np.nan_to_num(gain, nan=1.0)
    return Fi, Wp, gain, dict(e=e, hs=hs, H=H, S=S, act=act, beta=beta, heal=mk, healed=Fi)


def apply(img, F, m, P, UV, TRI, fields):
    """The raise laid on the paint's own texels (each sampled from its source in the paint, bicubic)."""
    n = img.shape[0]
    hs, H, S, act, gain = fields["hs"], fields["H"], fields["S"], fields["act"], fields["gain"]
    G = hl.in_uv(P, UV, TRI, n, None)
    gx, gy, gz = G[..., 0], G[..., 1], G[..., 2]
    has = ~np.isnan(gx)
    rr, cc = hl.row(np.nan_to_num(gy)), hl.col(np.nan_to_num(gx))
    has &= (rr >= 0) & (rr < F.shape[0] - 1) & (cc >= 0) & (cc < F.shape[1] - 1)
    zf = hl.sample(np.nan_to_num(F[..., 2], nan=-1.0), rr[has], cc[has])
    front = np.abs(zf - gz[has]) < 0.001
    ti, tj = (a[front] for a in np.where(has))
    r_s, c_s = rr[has][front], cc[has][front]
    x = np.arange(len(m))
    okm = ~np.isnan(m)
    mi = np.interp(c_s, x[okm], m[okm])
    Hi = np.interp(c_s, x, np.nan_to_num(H, nan=-1.0))
    hi = np.interp(c_s, x, np.nan_to_num(hs, nan=-1.0))
    Si = np.interp(c_s, x, np.nan_to_num(S, nan=0.0))
    bi = np.interp(c_s, x, fields["beta"])
    y = gy[ti, tj] - mi
    go = (bi > 0) & (y > LOW) & (y < Hi + EDGE) & (c_s >= x[okm].min()) & (c_s <= x[okm].max())
    ti, tj, c_s, r_s, y, mi, Hi, Si, bi = ti[go], tj[go], c_s[go], r_s[go], y[go], mi[go], Hi[go], Si[go], bi[go]
    sy = source_height(y, Hi, Si)
    sr = hl.row(mi + sy)
    su = hl.sample(np.nan_to_num(F[..., 0]), sr, c_s)
    sv = hl.sample(np.nan_to_num(F[..., 1]), sr, c_s)
    src = np.stack([ndimage.map_coordinates(img[..., ch], [sv * n - 0.5, su * n - 0.5], order=3, mode="nearest")
                    for ch in range(3)], -1)
    hk = np.clip(hl.sample(fields["heal"], sr, c_s), 0, 1)[:, None]
    src = src * (1 - hk) + hl.sample(fields["healed"], sr, c_s) * hk
    g = hl.sample(gain, r_s, c_s)
    lip = lin(src) * g
    u = np.clip((y - (Hi - EDGE / 2)) / EDGE, 0, 1)
    w = 1 - u * u * (3 - 2 * u)                                    # (1 lip under the new top, 0 skin over it)
    out = img.copy()
    old = lin(img[ti, tj])
    new = lip * w[:, None] + old * (1 - w[:, None])
    out[ti, tj] = srgb(old + bi[:, None] * (new - old))
    return out, len(ti)


def main():
    args = sys.argv[1:]
    to, glb = None, hl.GLB
    if "--to" in args:
        i = args.index("--to")
        to = args[i + 1]
        del args[i:i + 2]
    frm = hl.TEX
    if "--from" in args:                                           # (the paints read from there: default head_tex)
        i = args.index("--from")
        frm = args[i + 1]
        del args[i:i + 2]
    if "--glb" in args:
        i = args.index("--glb")
        glb = args[i + 1]
        del args[i:i + 2]
    if "--k" in args:
        i = args.index("--k")
        K.update({kk: (v if v == "border" else float(v)) for kk, v in (kv.split("=") for kv in args[i + 1].split(","))})
        del args[i:i + 2]
    pp = hl.paints()
    faces = args or [f for f in ls.FACES if f in K]
    ao = np.asarray(Image.open(os.path.join(hl.TEX, "heroine_ao.png")).convert("RGBA")).astype(np.float64)[..., 0] / 255
    js, binc, chunks, hm, hp, names, P0, N0, UV0, T0 = ls.head(glb)
    UV, TRI = UV0.astype(np.float64), T0.astype(np.int64).reshape(-1, 3)
    for f in faces:
        if f not in K:
            print("LIPRAISE %s: no factor (--k), skipped" % f)
            continue
        P = ls.shaped(js, binc, hp, names, P0, f).astype(np.float64)
        F = hl.front(P, UV, TRI)
        m, t, _, _ = hl.lines(F, ao)
        bad = np.isnan(F[..., 0])
        _, (iy, ix) = ndimage.distance_transform_edt(bad, return_indices=True)
        Ff = F[iy, ix]
        src = os.path.join(frm, pp[f])
        img = np.asarray(Image.open(src).convert("RGB")).astype(np.float64)
        Fi, Wp, gain, fl = raise_face(f, img, Ff, m, t, K[f])
        fl["gain"] = gain
        out, nt = apply(img, Ff, m, P, UV, TRI, fl)
        dst = os.path.join(to, pp[f]) if to else src
        Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)
        mid = int(round(hl.col(0.0)))
        print("LIPRAISE %-9s k %-6s red top %.1f -> %.1f mm at the middle (border %.1f), stretch %.2f, %d texels -> %s" % (
            f, K[f], fl["hs"][mid] * 1000, fl["H"][mid] * 1000, (t[mid] - m[mid]) * 1000 if not np.isnan(t[mid]) else -1,
            (fl["H"][mid] - EDGE / 2 - LOW) / max(fl["S"][mid] - LOW, 1e-5), nt, dst))


if __name__ == "__main__":
    main()
