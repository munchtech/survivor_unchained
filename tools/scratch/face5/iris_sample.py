"""iris_sample.py img ... : each eye's iris colour (median, linear -> sRGB hex), its lightness against the cheek's,
and how open each eye is (lid gap over eye width), from MediaPipe's landmarks. JSON with --json out.json."""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d\tools\assets")
import face_fit as ff  # noqa: E402

# MediaPipe's eye outlines (each eye's ring of landmarks) and lids
EYE_R = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
EYE_L = [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466]


def lin(c):
    c = np.asarray(c, float) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(l):
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055) * 255


def hexc(l):
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in srgb(l))


def poly_mask(shape, pts):
    m = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=1)
    return np.asarray(m, bool)


def measure(path, crop=None):
    img = np.asarray(Image.open(path).convert("RGB"))
    if crop:
        img = img[crop[1]:crop[3], crop[0]:crop[2]]
    # (small faces found more surely enlarged)
    k = 1
    if img.shape[0] < 900:
        k = 2
        img = np.asarray(Image.fromarray(img).resize((img.shape[1] * 2, img.shape[0] * 2), Image.LANCZOS))
    L = ff.detect(img)
    if L is None:
        return None
    L = L[:, :2]
    out = {}
    lim = lin(img)
    lum = lim @ [0.2126, 0.7152, 0.0722]
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    # cheek skin: under each eye, between it and the mouth's corner
    cheek = []
    for a, b in ((118, 50), (347, 280)):
        c = (L[a] + L[b]) / 2
        r = np.linalg.norm(L[a] - L[b]) * 0.4
        cheek.append(lim[np.hypot(xx - c[0], yy - c[1]) < r])
    cheek = np.median(np.vstack(cheek), 0)
    out["cheek"] = hexc(cheek)
    for side, ci, ring, ring_ids in (("r", 468, range(469, 473), EYE_R), ("l", 473, range(474, 478), EYE_L)):
        c = L[ci]
        R = np.mean([np.linalg.norm(L[i] - c) for i in ring])
        eye = poly_mask(img.shape, L[ring_ids])
        d = np.hypot(xx - c[0], yy - c[1]) / R
        m = eye & (d > 0.45) & (d < 0.85)
        if m.sum() < 8:
            out[side] = None
            continue
        px = lim[m]
        pl = lum[m]
        keep = (pl < np.percentile(pl, 85)) & (pl > np.percentile(pl, 5))
        iris = np.median(px[keep], 0)
        w = np.linalg.norm(L[ring_ids[0]] - L[ring_ids[8]])
        gap = np.linalg.norm(L[ring_ids[12]] - L[ring_ids[4]])
        out[side] = {"iris": hexc(iris), "iris_vs_cheek": float(iris @ [0.2126, 0.7152, 0.0722] / (cheek @ [0.2126, 0.7152, 0.0722])),
                     "open": float(gap / w), "iris_px": float(R / k)}
    return out


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
        if r is None:
            print("%-22s no face" % name)
            continue
        f = lambda s: ("%s %4.2f open %.2f" % (r[s]["iris"], r[s]["iris_vs_cheek"], r[s]["open"])) if r[s] else "--"
        print("%-22s cheek %s | R %s | L %s" % (name[:22], r["cheek"], f("r"), f("l")))
    if js:
        json.dump(res, open(js, "w"), indent=1)
