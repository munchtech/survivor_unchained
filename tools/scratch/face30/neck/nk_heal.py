"""Face 30 neck: the dark grey-violet blob in own's and Highborn's head paint, under her jaw on the side of her neck
(UV about 0.547, 0.122; core 100 against 142 round it, out to r 160 texels; came in with the face ship 096c7a8c, the
other eight faces' paints have none there), healed: inside a soft disc the paint's broad shade (gaussian sigma S) is
replaced by a smooth fill from the ring round it (Laplace, solved at a quarter size), its fine grain kept.

    python nk_heal.py OUT_DIR [face ...]      # faces: own highborn (default both); writes OUT_DIR/<name> for paint and raw
    python nk_heal.py --write [face ...]      # in place: godot/art/people/head_tex and tools/comfy/out/heroes (raw)"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
W = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TEX = os.path.join(W, "godot", "art", "people", "head_tex"); RAW = os.path.join(W, "tools", "comfy", "out", "heroes")
R0, R1, S = 200, 250, 4            # the disc filled to R0, eased back to the paint by R1; the broad shade's sigma
def files(face):
    sfx = "" if face == "own" else "_" + face
    return [os.path.join(TEX, f"heroine_head{sfx}.jpg"), os.path.join(RAW, f"heroine_head_raw{sfx}.jpg")]
def centre(a):
    """the blob's darkest point (luma, blurred) near UV (0.547, 0.122)"""
    y0, x0 = 300, 2050
    sub = ndimage.gaussian_filter(a[y0:y0 + 420, x0:x0 + 420].mean(2), 6)
    cy, cx = np.unravel_index(np.argmin(sub), sub.shape)
    return cy + y0, cx + x0
def laplace_fill(img, hole, iters=3000):
    """img (h, w, c) with hole (bool) filled smoothly from its edge (Jacobi on the 4-neighbour Laplacian)"""
    out = img.copy(); out[hole] = img[~hole].mean(0)
    for _ in range(iters):
        nb = 0.25 * (np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1))
        out[hole] = nb[hole]
    return out
def heal(a, cy, cx):
    h, w, _ = a.shape; m = R1 + 60
    y0, y1, x0, x1 = max(cy - m, 0), min(cy + m, h), max(cx - m, 0), min(cx + m, w)
    c = a[y0:y1, x0:x1].astype(float)
    low = np.stack([ndimage.gaussian_filter(c[..., k], S) for k in range(3)], -1); high = c - low
    q = 4; lo_s = low[::q, ::q]
    yy, xx = np.mgrid[y0:y1, x0:x1]; r = np.hypot(yy - cy, xx - cx)
    hole_s = r[::q, ::q] < R1
    fill_s = laplace_fill(lo_s, hole_s)
    fill = np.stack([ndimage.zoom(fill_s[..., k], (c.shape[0] / fill_s.shape[0], c.shape[1] / fill_s.shape[1]), order=1) for k in range(3)], -1)
    wgt = (1 - np.clip((r - R0) / (R1 - R0), 0, 1))[..., None]
    wgt = wgt * wgt * (3 - 2 * wgt)
    new = c * (1 - wgt) + (fill + high) * wgt
    out = a.copy(); out[y0:y1, x0:x1] = np.clip(np.round(new), 0, 255).astype(np.uint8)
    return out
if __name__ == "__main__":
    args = sys.argv[1:]; write = args[0] == "--write"; out_dir = None if write else args[0]
    faces = args[1:] or ["own", "highborn"]
    for face in faces:
        for p in files(face):
            im = Image.open(p); qt = im.quantization; a = np.asarray(im.convert("RGB"))
            cy, cx = centre(a.astype(float))
            b = heal(a, cy, cx)
            lum = lambda x: x.astype(float).mean(2)
            yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
            print(f"{os.path.basename(p)}: blob at {cx},{cy}; core {lum(a)[cy-15:cy+15, cx-15:cx+15].mean():.1f} -> {lum(b)[cy-15:cy+15, cx-15:cx+15].mean():.1f}, "
                  f"ring {lum(a)[cy+R1:cy+R1+30, cx-15:cx+15].mean():.1f}")
            dst = p if write else os.path.join(out_dir, os.path.basename(p))
            Image.fromarray(b).save(dst, qtables=qt, subsampling=0)   # (its own tables, so the rest barely moves)
