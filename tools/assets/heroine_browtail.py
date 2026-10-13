"""Her brows' ghost tails painted out of each face's paint (the owner's "double eyebrow", 12-13 October 2026).

Each face's paint carries a second, smooth brow tail: an arc 2-3 mm wide that rises off the outer third of her brow
and runs on past its end, down toward the temple, apart from the brow's hairs (the side paintings' brows, painted
higher than the portrait's and showing past the front's brow outline: heroine_face.py). In the Look it reads as a
hard dark stroke from each brow's outer end (judge rj3: strong on Doe, Vixen, Saffron, Moonlit and Hard-won).

Per face and side, on a flat front view of her face's own shape (PX px per mm): her brow's body is found (dark at
the broad scale and hairy: each hair's light and dark), and the ghost is what is dark against the skin round it
(band-passed, so the temple's broad shade is not) above that body or past its outer end, away from the lid's
crease. Its mask is taken back to the paint by each texel's place on her head, and there the skin is made again:
its broad colour filled in from the clean skin round it (the brow's body and the ghost left out), its grain and
pores copied from clean forehead skin nearby (the nearest spot where the mask's shape lands on no feature), scaled
to the colour it lands on. The brow's body is never touched; the paint is written again at the chain's 95, 4:4:4.

    python tools/assets/heroine_browtail.py [face ...]             (no faces: all ten; own is heroine_head.jpg)
    python tools/assets/heroine_browtail.py --measure [face ...]   (the ghost found per side, nothing written)

Idempotent: a side whose ghost is under TOL (as after this has run) is left, so running it again changes nothing.
The chain: after heroine_browpaint.py (it touches only the skin above and beyond each brow, not the ears).
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter, map_coordinates

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
import heroine_browfold as bf  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
FACES = ["own", "doe", "fey", "hardwon", "highborn", "moonlit", "saffron", "sunborn", "vixen", "wildling"]
PX = 8.0                       # (the flat view's pixels per mm)
BOX = (0.024, 0.076, 1.744, 1.800)  # (m: |x| from, to; y from, to: each brow's outer two thirds and the temple)
SKIN, K = 2.0, 0.035           # (mm: the skin's local level, texels this much darker than it left out of it)
FINE, HAIR, DB = 0.15, 0.4, 0.5  # (mm: a hair's blur, its energy's blur, the darkness's blur)
BROW_D, BROW_H, BROW_CLOSE = 0.35, 0.4, 0.8  # (the brow's body: this share of its darkest and hairiest, closed over mm)
BROW_LID, OUTER = 4.0, 0.5     # (mm: a brow is looked for this far from the lash line; "above" only over its outer half)
NEAR, LID, XMAX, YMAX = 9.0, 6.5, 0.070, 1.795  # (mm from the brow's body, at least mm from the lash line; m limits)
SEED, LOW, AREA = 0.06, 0.03, 3.0   # (the ghost: this dark seeds it, it grows to this; pieces of at least AREA mm2)
GROW, FEATHER = 0.45, 0.45     # (mm: its mask grown and feathered)
TOL = 4.0                      # (mm2: a side with less ghost than this, at SEED, is clean already)
SPLIT, LF1, LF2 = 4.0, 9.0, 24.0  # (texels: the grain's split; the broad colour's fill blurs, near and far)


def paint_path(face):
    return os.path.join(TEX, "heroine_head%s.jpg" % ("" if face == "own" else "_" + face))


def disk(r):
    r = max(1, int(round(r)))
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def raster_view(P, F, UV, box):
    """Her face seen square on (orthographic, her right on the left): per pixel the paint's (u, v), NaN where none."""
    x0, x1, y0, y1 = box
    W, H = int(round((x1 - x0) * 1000 * PX)), int(round((y1 - y0) * 1000 * PX))
    zb, out = np.full((H, W), -np.inf), np.full((H, W, 2), np.nan)
    sx, sy = (P[:, 0] - x0) * 1000 * PX, (y1 - P[:, 1]) * 1000 * PX
    xs, ys, zs = sx[F], sy[F], P[F, 2]
    keep = (xs.max(1) >= 0) & (xs.min(1) < W) & (ys.max(1) >= 0) & (ys.min(1) < H)
    for t in np.where(keep)[0]:
        X, Y, Z = xs[t], ys[t], zs[t]
        den = (Y[1] - Y[2]) * (X[0] - X[2]) + (X[2] - X[1]) * (Y[0] - Y[2])
        if abs(den) < 1e-9:
            continue
        a, b = int(max(0, np.floor(X.min()))), int(min(W - 1, np.ceil(X.max())))
        c, d = int(max(0, np.floor(Y.min()))), int(min(H - 1, np.ceil(Y.max())))
        if a > b or c > d:
            continue
        gx, gy = np.meshgrid(np.arange(a, b + 1) + 0.5, np.arange(c, d + 1) + 0.5)
        l0 = ((Y[1] - Y[2]) * (gx - X[2]) + (X[2] - X[1]) * (gy - Y[2])) / den
        l1 = ((Y[2] - Y[0]) * (gx - X[2]) + (X[0] - X[2]) * (gy - Y[2])) / den
        l2 = 1 - l0 - l1
        z = l0 * Z[0] + l1 * Z[1] + l2 * Z[2]
        sl = (slice(c, d + 1), slice(a, b + 1))
        upd = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6) & (z > zb[sl])
        if upd.any():
            uvt = UV[F[t]]
            zb[sl][upd] = z[upd]
            out[sl + (0,)][upd] = (l0 * uvt[0, 0] + l1 * uvt[1, 0] + l2 * uvt[2, 0])[upd]
            out[sl + (1,)][upd] = (l0 * uvt[0, 1] + l1 * uvt[1, 1] + l2 * uvt[2, 1])[upd]
    return out


def raster_uv(UV, F, vals, tris, win):
    """Per-point values drawn by her UVs over tris into the texel window (x0, y0, x1, y1); NaN where none."""
    n = 4096
    x0w, y0w, x1w, y1w = win
    out = np.full((y1w - y0w, x1w - x0w, vals.shape[1]), np.nan)
    for t in tris:
        U = UV[F[t]] * n
        x0, x1 = max(int(np.floor(U[:, 0].min())), x0w), min(int(np.ceil(U[:, 0].max())), x1w - 1)
        y0, y1 = max(int(np.floor(U[:, 1].min())), y0w), min(int(np.ceil(U[:, 1].max())), y1w - 1)
        if x0 > x1 or y0 > y1:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        a, v0, v1 = U[0], U[1] - U[0], U[2] - U[0]
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        qx, qy = xs + 0.5 - a[0], ys + 0.5 - a[1]
        b1 = (qx * v1[1] - v1[0] * qy) / den
        b2 = (v0[0] * qy - qx * v0[1]) / den
        m = (b1 >= -1e-3) & (b2 >= -1e-3) & (b1 + b2 <= 1 + 1e-3)
        val = vals[F[t]]
        out[ys[m] - y0w, xs[m] - x0w] = (1 - b1 - b2)[m, None] * val[0] + b1[m, None] * val[1] + b2[m, None] * val[2]
    return out


def sample(img, uvm):
    n = img.shape[0]
    ok = np.isfinite(uvm[..., 0])
    yy, xx = np.nan_to_num(uvm[..., 1]) * n - 0.5, np.nan_to_num(uvm[..., 0]) * n - 0.5
    res = np.stack([map_coordinates(img[..., c], [yy, xx], order=1, mode="nearest") for c in range(3)], -1)
    res[~ok] = 0
    return res, ok


def luma(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def level(Y, ok, sig, k, it=3):
    """The skin's own level round each pixel, its darker features (k darker) left out."""
    w = ok.astype(float)
    for _ in range(it):
        S = gaussian_filter(Y * w, sig) / np.maximum(gaussian_filter(w, sig), 1e-3)
        w = (ok & (Y > S * (1 - k))).astype(float)
    return S


def find(view, ok, lid_px, side):
    """In one flat view: her brow's body and the ghost's soft mask, and its numbers."""
    mm = PX
    Y = luma(view)
    Sb = level(Y, ok, 4 * mm, 0.04)
    Yf = gaussian_filter(Y, FINE * mm)
    Db = gaussian_filter(np.where(ok, (Sb - Yf) / np.maximum(Sb, 1), 0), DB * mm)
    Hb = gaussian_filter(gaussian_filter(np.abs(Y - Yf), HAIR * mm) / np.maximum(Sb, 1), DB * mm)
    # (each face's brow by its own darkness and hairs: a fair, fine brow is a third as dark as a black one; never
    # her lids' lash lines)
    H0, W0 = Y.shape
    r0 = np.mgrid[0:H0, 0:W0][0]
    look = ok & (lid_px > BROW_LID * mm) & (r0 < H0 - 1)
    d_hi, h_hi = np.percentile(Db[look], 99.5), np.percentile(Hb[look], 99.5)
    brow = look & (Db > max(0.07, BROW_D * d_hi)) & (Hb > max(0.010, BROW_H * h_hi))
    brow = ndi.binary_closing(brow, disk(BROW_CLOSE * mm))
    lab, n = ndi.label(brow)
    if not n:
        return None
    sizes = ndi.sum(brow, lab, range(1, n + 1))
    brow = ndi.binary_fill_holes(np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= 0.25 * sizes.max()]))
    # (dark against the skin round it at the stroke's own breadth: the temple's broad shade is not)
    S = level(Y, ok, SKIN * mm, K)
    D = gaussian_filter(np.where(ok, (S - Yf) / np.maximum(S, 1), 0), 0.4 * mm)
    H, W = Y.shape
    rows, cols = np.mgrid[0:H, 0:W]
    # (above the brow's body where it is; past its outer end anywhere; never near the lid's crease)
    bc = np.where(brow.any(0))[0]
    top = np.where(brow.any(0), np.argmax(brow, 0), -1)
    outer = bc.min() if side < 0 else bc.max()
    inner = bc.max() if side < 0 else bc.min()
    beyond = (cols < outer) if side < 0 else (cols > outer)
    half = outer + OUTER * (inner - outer)
    outerhalf = (cols <= half) if side < 0 else (cols >= half)
    above = (top >= 0)[None, :] & (rows < top[None, :] + 0.3 * mm) & outerhalf
    near = ndi.distance_transform_edt(~brow) < NEAR * mm
    xm = (BOX[0] + cols / (1000 * PX)) if side > 0 else -(-BOX[1] + cols / (1000 * PX))
    ym = BOX[3] - rows / (1000 * PX)
    zone = ok & near & (above | beyond) & (lid_px > LID * mm) & (np.abs(xm) < XMAX) & (ym < YMAX)
    zone &= ~ndi.binary_dilation(brow, disk(0.25 * mm))
    seed, low = zone & (D > SEED), zone & (D > LOW)
    lab, n = ndi.label(low)
    hit = np.unique(lab[seed])
    g = np.isin(lab, hit[hit > 0])
    lab, n = ndi.label(g)
    if n:
        a = ndi.sum(g, lab, range(1, n + 1)) / mm ** 2
        g = np.isin(lab, [i + 1 for i in range(n) if a[i] >= AREA])
    area = (g & seed).sum() / mm ** 2
    m = ndi.binary_dilation(g, disk(GROW * mm)) & ok
    soft = gaussian_filter(m.astype(float), FEATHER * mm * 0.5)
    soft = np.where(ndi.binary_dilation(brow, disk(0.15 * mm)), 0, soft)  # (never on the brow's body)
    return dict(brow=brow, ghost=g, soft=np.clip(soft * 1.3, 0, 1), area=area,
                peak=float(D[g].max()) if g.any() else 0.0, D=D)


def fill(img, M, keepout, win):
    """The skin made again under M (soft, the window's texels) in img (float, whole paint): its broad colour from the
    clean skin round it, its grain from the nearest clean spot. Returns the new window and the donor's offset."""
    x0, y0, x1, y1 = win
    pad = 140
    X0, Y0, X1, Y1 = max(x0 - pad, 0), max(y0 - pad, 0), min(x1 + pad, img.shape[1]), min(y1 + pad, img.shape[0])
    A = img[Y0:Y1, X0:X1].astype(np.float64)
    Mw = np.zeros(A.shape[:2])
    Mw[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = M
    Kw = np.zeros(A.shape[:2], bool)
    Kw[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = keepout
    hole = ndi.binary_dilation(Mw > 0.02, disk(3)) | Kw
    Yl = luma(A)
    # (clean skin: off the hole, and not a dark or light feature of its own at the broad scale)
    Sl = level(Yl, ~hole, 12.0, 0.05)
    clean = ~hole & (np.abs(gaussian_filter(Yl, 2.0) - Sl) < 0.06 * Sl)
    w = clean.astype(float)
    LF = np.empty_like(A)
    for c in range(3):
        n1, d1 = gaussian_filter(A[..., c] * w, LF1), gaussian_filter(w, LF1)
        n2, d2 = gaussian_filter(A[..., c] * w, LF2), gaussian_filter(w, LF2)
        t = np.clip(d1 / 0.15, 0, 1)
        LF[..., c] = t * n1 / np.maximum(d1, 1e-6) + (1 - t) * n2 / np.maximum(d2, 1e-6)
    base = np.stack([gaussian_filter(A[..., c], SPLIT) for c in range(3)], -1)
    HFr = A / np.maximum(base, 1.0)      # (the grain as a ratio to the broad colour)
    # (the donor: the nearest offset whose patch is clean skin everywhere the mask is)
    my, mx = np.nonzero(Mw > 0.02)
    best, bd = None, None
    feat = (~clean).astype(float)
    for r in (36, 52, 70, 90, 115):
        for ang in np.arange(0, 2 * np.pi, np.pi / 12):
            dy, dx = int(round(r * np.sin(ang))), int(round(r * np.cos(ang)))
            yy, xx = my + dy, mx + dx
            if yy.min() < 0 or xx.min() < 0 or yy.max() >= A.shape[0] or xx.max() >= A.shape[1]:
                continue
            cost = (feat[yy, xx] * Mw[my, mx]).sum() / max(Mw[my, mx].sum(), 1) + 0.0004 * r
            if bd is None or cost < bd:
                best, bd = (dy, dx), cost
    dy, dx = best
    D_HF = np.ones_like(A)
    sy = slice(max(0, dy), A.shape[0] + min(0, dy))
    ty = slice(max(0, -dy), A.shape[0] + min(0, -dy))
    sx = slice(max(0, dx), A.shape[1] + min(0, dx))
    tx = slice(max(0, -dx), A.shape[1] + min(0, -dx))
    D_HF[ty, tx] = HFr[sy, sx]
    new = LF * D_HF
    out = A * (1 - Mw[..., None]) + new * Mw[..., None]
    return out[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0], best, bd


def plan(faces):
    js, binc = hs._load(GLB)
    hm, hp, names = bf.head(js)
    V = hs._read(js, binc, hp["attributes"]["POSITION"])
    UV = hs._read(js, binc, hp["attributes"]["TEXCOORD_0"])
    F = hs._read(js, binc, hp["indices"]).reshape(-1, 3)
    keys = {n: i for i, n in enumerate(names)}
    T = bf.Topo(V, F, UV)
    shapes = {}
    for f in faces:
        P = V.copy()
        if f != "own":
            P = P + hs._read(js, binc, hp["targets"][keys["face_" + f]]["POSITION"])
        shapes[f] = P
    return V, UV, F, T, shapes


def apply(faces, measure_only=False):
    V, UV, F, T, shapes = plan(faces)
    fm = T.main_v[F[:, 0]]
    for face in faces:
        P = shapes[face]
        path = paint_path(face)
        img = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
        out = img.copy()
        changed = False
        for side in (-1, 1):
            box = (-BOX[1], -BOX[0], BOX[2], BOX[3]) if side < 0 else (BOX[0], BOX[1], BOX[2], BOX[3])
            uvm = raster_view(P, F, UV, box)
            view, ok = sample(img, uvm)
            # (each pixel's distance from her upper lid's lash line on this side, in view pixels)
            lid = np.zeros(ok.shape, bool)
            for o in T.upper:
                Q = P[T.pick[o]]
                if np.sign(Q[:, 0].mean()) != side:
                    continue
                c = ((Q[:, 0] - box[0]) * 1000 * PX).astype(int)
                r = ((box[3] - Q[:, 1]) * 1000 * PX).astype(int)
                inb = (c >= 0) & (c < ok.shape[1]) & (r >= 0) & (r < ok.shape[0])
                lid[r[inb], c[inb]] = True
            lid_px = ndi.distance_transform_edt(~lid) if lid.any() else np.full(ok.shape, 1e9)
            fv = find(view, ok, lid_px, side)
            name = "%-9s %s" % (face, "R" if side < 0 else "L")
            if fv is None:
                print("BROWTAIL %s: no brow found - left" % name)
                continue
            print("BROWTAIL %s: ghost %.1f mm2 (peak %.0f%% darker than the skin round it)" % (name, fv["area"], 100 * fv["peak"]))
            if os.environ.get("BROWTAIL_DEBUG"):  # (the view with the brow's body green and the mask red)
                ov = view * (1 - 0.6 * fv["soft"][..., None]) + np.array([255.0, 0, 0]) * 0.6 * fv["soft"][..., None]
                ov[fv["brow"]] = ov[fv["brow"]] * 0.6 + np.array([0, 255.0, 0]) * 0.4
                Image.fromarray(np.clip(np.concatenate([view, ov], 1), 0, 255).astype(np.uint8)).save(
                    os.path.join(os.environ["BROWTAIL_DEBUG"], "bt_%s_%s.png" % (face, "R" if side < 0 else "L")))
            if measure_only or fv["area"] < TOL:
                if not measure_only:
                    print("BROWTAIL %s: under TOL - left" % name)
                continue
            # (the mask taken back to the paint: each texel's place on her head, seen in the view)
            x = P[:, 0] * side
            inr = (x >= BOX[0] - 0.004) & (x <= BOX[1] + 0.004) & (P[:, 1] >= BOX[2] - 0.004) & (P[:, 1] <= BOX[3] + 0.004)
            tris = np.where(inr[F].any(1) & fm)[0]
            U = UV[F[tris].ravel()] * 4096
            win = (int(U[:, 0].min()) - 4, int(U[:, 1].min()) - 4, int(U[:, 0].max()) + 5, int(U[:, 1].max()) + 5)
            pos = raster_uv(UV, F, P, tris, win)
            okp = np.isfinite(pos[..., 0])
            cx = (np.nan_to_num(pos[..., 0]) - box[0]) * 1000 * PX - 0.5
            cy = (box[3] - np.nan_to_num(pos[..., 1])) * 1000 * PX - 0.5
            M = np.where(okp, map_coordinates(fv["soft"], [cy, cx], order=1, mode="constant", cval=0.0), 0)
            keep = okp & (map_coordinates(fv["brow"].astype(float), [cy, cx], order=1, mode="constant") > 0.3)
            neww, off, cost = fill(out, M, keep, win)
            x0, y0, x1, y1 = win
            out[y0:y1, x0:x1] = neww
            changed = True
            print("BROWTAIL %s: %d texels made again (%d at full), grain from %s texels off (cost %.3f)" % (
                name, (M > 0.02).sum(), (M > 0.98).sum(), off, cost))
        if changed:
            Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(path, quality=95, subsampling=0)
            print("BROWTAIL: written", path)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--measure"]:
        apply(a[1:] or FACES, measure_only=True)
    else:
        apply(a or FACES)
