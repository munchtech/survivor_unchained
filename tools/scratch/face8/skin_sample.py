"""skin_sample.py img[@x0,y0,x1,y1] ... : each face's skin (its oval less eyes, brows, lips and nostrils): median and
its 25th/75th percentiles of lightness, in linear light, as sRGB hex; and its spread (texture: the std of fine
detail). JSON with --json."""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\tools\assets")
import face_fit as ff  # noqa: E402
from iris_sample import lin, hexc, EYE_R, EYE_L  # noqa: E402

BROW_A = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
BROW_B = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
LIPS = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]
NOSE = [98, 64, 48, 115, 220, 45, 4, 275, 440, 344, 278, 294, 327, 2]


def poly(shape, pts, grow=0):
    m = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=1)
    m = np.asarray(m, bool)
    return ndimage.binary_dilation(m, iterations=grow) if grow else m


def measure(path, crop=None):
    img = np.asarray(Image.open(path).convert("RGB"))
    if crop:
        img = img[crop[1]:crop[3], crop[0]:crop[2]]
    if img.shape[0] < 900:
        img = np.asarray(Image.fromarray(img).resize((img.shape[1] * 2, img.shape[0] * 2), Image.LANCZOS))
    L = ff.detect(img)
    if L is None:
        return None
    L = L[:, :2]
    oval = poly(img.shape, L[ff.OVAL])
    # (the oval shrunk a little: its edge is soft, and past it is hair or the room)
    oval = ndimage.binary_erosion(oval, iterations=max(2, img.shape[0] // 150))
    feat = np.zeros_like(oval)
    g = max(2, img.shape[0] // 120)
    for ring in (EYE_R, EYE_L, BROW_A, BROW_B, LIPS, NOSE):
        feat |= poly(img.shape, L[ring], g)
    # (and her forehead above her brows' tops only to a third: hair may hang there)
    top = L[[105, 334], 1].min() - 0.35 * (L[152, 1] - L[10, 1]) * 0.25
    rows = np.arange(img.shape[0])[:, None] * np.ones(img.shape[1])[None]
    m = oval & ~feat & (rows > top)
    li = lin(img)
    px = li[m]
    lum = px @ [0.2126, 0.7152, 0.0722]
    keep = (lum > np.percentile(lum, 10)) & (lum < np.percentile(lum, 90))
    med = np.median(px[keep], 0)
    fine = li @ [0.2126, 0.7152, 0.0722] - ndimage.gaussian_filter(li @ [0.2126, 0.7152, 0.0722], img.shape[0] / 300)
    return {"skin": hexc(med), "lin": med.tolist(), "p25": hexc(np.percentile(px, 25, 0)), "p75": hexc(np.percentile(px, 75, 0)),
            "grain": float(fine[m].std() / (med @ [0.2126, 0.7152, 0.0722] + 1e-6)), "n": int(m.sum())}


if __name__ == "__main__":
    args = sys.argv[1:]
    js = None
    if "--json" in args:
        i = args.index("--json")
        js = args[i + 1]
        del args[i:i + 2]
    res = {}
    for p in args:
        crop = None
        if "@" in p:
            p, c = p.split("@")
            crop = [int(v) for v in c.split(",")]
        r = measure(p, crop)
        res[p] = r
        name = p.replace("\\", "/").split("/")[-1]
        print("%-22s %s" % (name[:22], "no face" if r is None else "skin %s (%s..%s) grain %.3f" % (r["skin"], r["p25"], r["p75"], r["grain"])))
    if js:
        json.dump(res, open(js, "w"), indent=1)
