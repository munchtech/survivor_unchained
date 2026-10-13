"""The pale lines left along her old brow tails, and Wildling's pencil-line tail, painted out (judge rj4, 13 October 2026).

heroine_browtail.py painted out each face's ghost brow tail, but the original paint's light rim along the ghost's inner
edge (between the ghost and the brow's lower tail) was not in its mask: alone, it read as a thin pale-cream line from
each brow's end toward the temple (Doe clearly; Vixen, Saffron, Wildling and Highborn at 4x). Wildling's right tail
(image-left) kept a smooth dark wedge past its hairs (a crisp pencil line).

Per face and side, in heroine_browtail's flat front view: the lines are light ridges (Hessian at 0.3 mm, against the
skin's own level) at least 3 mm long within 1 mm of the old ghost's mask, kept 0.8 mm off the brow's body and
reaching 2 mm from it (so never the brow's own rim). They were found once,
from the paint before heroine_browtail (git 706481ff^) and the paint after it, and are kept in heroine_face/
browline_masks.npz (view-space masks, packed). Under each (grown 0.35 mm, feathered) the skin is made again as
heroine_browtail.fill does: broad colour from the clean skin round it, grain and pores from clean skin nearby. On
Wildling's right the last 2 mm of the kept tail fade into the skin, so the brow ends in its hairs.

    python tools/assets/heroine_browline.py [face ...]          (no faces: all ten; run once, after heroine_browtail)
    python tools/assets/heroine_browline.py --plan PRE_DIR      (the masks found again: PRE_DIR holds the paints
                                                                 before heroine_browtail, git 706481ff^)

Run-once: heroine_face/browline_done.json keeps probes per side (as heroine_browtail's); a side whose probes read as
the result is left, so a second run changes nothing. Touches only the brow-temple windows, never the ears.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter, map_coordinates

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_browtail as bt  # noqa: E402

HF = os.path.join(bt.ROOT, "tools", "assets", "heroine_face")
MASKS = os.path.join(HF, "browline_masks.npz")
DONE = os.path.join(HF, "browline_done.json")
SIG, R_HI, R_LO, LEN_MIN, NEAR, BROW_X, FAR = 0.3, 0.035, 0.015, 3.0, 1.0, 0.8, 2.0   # (mm; ridge in Y/level)
GROW, FEATHER = 0.35, 0.25         # (mm: a line's mask grown, then feathered)
PENCIL = {"wildling_R": 2.0}       # (mm of the kept tail, in from its tip, faded into the skin)
mm = bt.PX


def geom(P, F, UV, T, fm, side):
    """The flat view's (u, v) per pixel and its lid distances; the paint's window and each texel's place in the view."""
    box = (-bt.BOX[1], -bt.BOX[0], bt.BOX[2], bt.BOX[3]) if side < 0 else tuple(bt.BOX)
    uvm = bt.raster_view(P, F, UV, box)
    ok = np.isfinite(uvm[..., 0])
    lid = np.zeros(ok.shape, bool)
    for o in T.upper:
        Q = P[T.pick[o]]
        if np.sign(Q[:, 0].mean()) != side:
            continue
        c, r = ((Q[:, 0] - box[0]) * 1000 * mm).astype(int), ((box[3] - Q[:, 1]) * 1000 * mm).astype(int)
        inb = (c >= 0) & (c < ok.shape[1]) & (r >= 0) & (r < ok.shape[0])
        lid[r[inb], c[inb]] = True
    lid_px = ndi.distance_transform_edt(~lid) if lid.any() else np.full(ok.shape, 1e9)
    x = P[:, 0] * side
    inr = (x >= bt.BOX[0] - 0.004) & (x <= bt.BOX[1] + 0.004) & (P[:, 1] >= bt.BOX[2] - 0.004) & (P[:, 1] <= bt.BOX[3] + 0.004)
    tris = np.where(inr[F].any(1) & fm)[0]
    U = UV[F[tris].ravel()] * 4096
    win = (int(U[:, 0].min()) - 4, int(U[:, 1].min()) - 4, int(U[:, 0].max()) + 5, int(U[:, 1].max()) + 5)
    pos = bt.raster_uv(UV, F, P, tris, win)
    okp = np.isfinite(pos[..., 0])
    cx = (np.nan_to_num(pos[..., 0]) - box[0]) * 1000 * mm - 0.5
    cy = (box[3] - np.nan_to_num(pos[..., 1])) * 1000 * mm - 0.5
    return uvm, ok, lid_px, win, okp, cx, cy


def level2(Y, w0, sig, k, it=3):
    w = w0.astype(float)
    for _ in range(it):
        S = gaussian_filter(Y * w, sig) / np.maximum(gaussian_filter(w, sig), 1e-3)
        w = (w0 & (np.abs(Y - S) < k * S)).astype(float)
    return S


def ridge(Yn, sig):
    s = sig * mm
    Hxx, Hyy, Hxy = (gaussian_filter(Yn, s, order=o) for o in ((0, 2), (2, 0), (1, 1)))
    tr, det = Hxx + Hyy, Hxx * Hyy - Hxy ** 2
    disc = np.sqrt(np.maximum(tr * tr / 4 - det, 0))
    l1, l2 = tr / 2 - disc, tr / 2 + disc
    return np.maximum(0, -l1 - np.abs(l2)) * s * s     # (a light line: curved down across it, flat along it)


def lines(vcur, ok, lid_px, old, brow):
    """Light ridges at least LEN_MIN long within NEAR of the old ghost's mask, BROW_X off the kept brow, reaching FAR."""
    Y = bt.luma(vcur)
    L = level2(gaussian_filter(Y, 0.3 * mm), ok & ~ndi.binary_dilation(brow, bt.disk(0.4 * mm)), 1.5 * mm, 0.025)
    rg = ridge(np.where(ok, Y / np.maximum(L, 1), 1.0), SIG)
    zone = ok & ndi.binary_dilation(old, bt.disk(NEAR * mm)) & (lid_px > 2.5 * mm)
    z1 = zone & ~ndi.binary_dilation(brow, bt.disk(BROW_X * mm))
    lab, n = ndi.label(z1 & (rg > R_LO))
    hit = np.unique(lab[z1 & (rg > R_HI)])
    g = np.isin(lab, hit[hit > 0])
    lab, n = ndi.label(g)
    far = ndi.distance_transform_edt(~brow) / mm   # (a line reaches at least FAR from the brow: not its own rim)
    keep = [i for i in range(1, n + 1) if (lambda rc: len(rc[0]) >= 3 and far[rc].max() >= FAR and
            np.hypot(np.ptp(rc[0]), np.ptp(rc[1])) / mm >= LEN_MIN)(np.nonzero(lab == i))]
    g = np.isin(lab, keep)
    return g


def plan(pre_dir):
    V, UV, F, T, shapes = bt.plan(bt.FACES)
    fm = T.main_v[F[:, 0]]
    out = {}
    for face in bt.FACES:
        n = os.path.basename(bt.paint_path(face))
        pre = np.asarray(Image.open(os.path.join(pre_dir, n)).convert("RGB")).astype(np.float64)
        cur = np.asarray(Image.open(bt.paint_path(face)).convert("RGB")).astype(np.float64)
        for side in (-1, 1):
            key = "%s_%s" % (face, "R" if side < 0 else "L")
            uvm, ok, lid_px, win, okp, cx, cy = geom(shapes[face], F, UV, T, fm, side)
            vpre, _ = bt.sample(pre, uvm)
            vcur, _ = bt.sample(cur, uvm)
            fv = bt.find(vpre, ok, lid_px, side)
            brow = fv["brow"] & (fv["tp"]["keep"] > 0.5)
            m = lines(vcur, ok, lid_px, fv["ghost"] | (fv["soft"] > 0.02), brow)
            if key in PENCIL:   # (the kept tail's last mm, by columns in from its tip)
                o = -1 if side < 0 else 1
                s = (fv["tp"]["tip"] - np.arange(ok.shape[1])[None, :]) * o
                m |= brow & (s < PENCIL[key] * mm)
            out[key] = np.packbits(m)
            out[key + "_brow"] = np.packbits(brow)
            out["shape"] = np.array(ok.shape)
            print("BROWLINE plan %-11s: %.1f mm2 of line" % (key, m.sum() / mm ** 2))
    np.savez_compressed(MASKS, **out)
    print("BROWLINE: masks written", MASKS)


def apply(faces):
    Mk = np.load(MASKS)
    shp = tuple(Mk["shape"])
    unpack = lambda k: np.unpackbits(Mk[k])[:shp[0] * shp[1]].reshape(shp).astype(bool)
    done = json.load(open(DONE)) if os.path.exists(DONE) else {}
    V, UV, F, T, shapes = bt.plan(faces)
    fm = T.main_v[F[:, 0]]
    for face in faces:
        path = bt.paint_path(face)
        img = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
        out, changed = img.copy(), False
        for side in (-1, 1):
            key = "%s_%s" % (face, "R" if side < 0 else "L")
            m = unpack(key)
            if not m.any():
                print("BROWLINE %-11s: no line - left" % key)
                continue
            if bt.is_done(img, done.get(key)):
                print("BROWLINE %-11s: made already - left" % key)
                continue
            uvm, ok, lid_px, win, okp, cx, cy = geom(shapes[face], F, UV, T, fm, side)
            brow = unpack(key + "_brow") & ~m          # (the pencil tail is not kept out)
            soft = np.clip(gaussian_filter(ndi.binary_dilation(m, bt.disk(GROW * mm)).astype(float),
                                           FEATHER * mm * 0.5) * 1.3, 0, 1) * ok
            soft *= 1 - ndi.binary_dilation(brow, bt.disk(0.1 * mm))
            M = np.where(okp, map_coordinates(soft, [cy, cx], order=1, mode="constant", cval=0.0), 0)
            keep = okp & (map_coordinates(brow.astype(float), [cy, cx], order=1, mode="constant") > 0.3)
            neww, off, cost = bt.fill(out, M, keep, win)
            x0, y0, x1, y1 = win
            dl = bt.luma(img[y0:y1, x0:x1]) - bt.luma(neww)
            py, px = np.nonzero(M > 0.95)
            order = np.argsort(np.abs(dl[py, px]))[::-1][:bt.NPROBE * 4:4]
            done[key] = [[int(px[i] + x0), int(py[i] + y0), round(float(bt.probe(img, px[i] + x0, py[i] + y0)), 2),
                          round(float(bt.probe(neww, px[i], py[i])), 2)] for i in order]
            out[y0:y1, x0:x1] = neww
            changed = True
            print("BROWLINE %-11s: %d texels made again (%d at full), grain from %s off (cost %.3f)" % (
                key, (M > 0.02).sum(), (M > 0.98).sum(), off, cost))
        if changed:
            Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(path, quality=95, subsampling=0)
            print("BROWLINE: written", path)
            with open(DONE, "w") as fh:
                json.dump(done, fh, indent=0)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--plan"]:
        plan(a[1])
    else:
        apply(a or bt.FACES)
