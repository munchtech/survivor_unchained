"""neckx.py TAG [faces]: j7's neck lines on the front shots (godot/.shots/TAG_FACE.png). (a) Rows across her neck at
0.15 and 0.3 pupil-chin below her far jaw line, silhouette to silhouette, skin only (a skin mask; 3 px kept off each
silhouette): the most hue off the same shot's lit-neck hue (meas.py's neck spot), the least C as a share of the lit
neck's, the largest L step within 4 px. (b) The far neck's mid-shade (on the 0.3 row, 0.1 pupil-chin inside the far
silhouette, a 0.08 pupil-chin box) against the portrait's shaded neck side (farneck.py's portrait spot). Writes
TAG_neckx.jpg in godot/.shots: each face's neck at 2x, the rows and the box drawn, to prove they lie on skin.
Run with the facefit venv."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "face17"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "face19"))
import meas  # noqa
ff = meas.ff
FAR = [152, 377, 400, 378, 379, 365, 397, 288, 361]     # her jaw line, chin to ear, on her left (image right)
NEAR = [152, 148, 176, 149, 150, 136, 172, 58, 132]


def lab_img(a):
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    c = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return np.cbrt(c @ M1.T) @ M2.T


def skin(lab):
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(A, B); h = np.degrees(np.arctan2(B, A))
    green = (h > 95) & (h < 260) & (C > 0.012)
    return (L > 0.3) & (C < 0.115) & ~green


def run(mask_row, x0, step):
    x = int(x0)
    while 0 < x + step < len(mask_row) - 1 and mask_row[x + step]:
        x += step
    return x


def jaw_y(L, side, x):
    pts = np.array([L[i] for i in (FAR if side > 0 else NEAR)])
    o = np.argsort(pts[:, 0]); xs, ys = pts[o, 0], pts[o, 1]
    return float(np.interp(x, xs, ys))


def measure(path):
    im = Image.open(path).convert("RGB"); a = np.asarray(im, np.float32) / 255
    L = ff.detect((a * 255).astype(np.uint8))[:, :2]
    pc = np.linalg.norm((L[468] + L[473]) / 2 - L[152])
    s = 1 if L[1][0] > (L[234][0] + L[454][0]) / 2 else -1
    lab = lab_img(np.asarray(im.filter(ImageFilter.BoxBlur(1)), np.float32) / 255)
    sk = skin(lab)
    nk = meas.spots(path)[0]["neck"]                        # (lit neck: L, C, h)
    y0 = int(L[152][1] + 0.15 * pc)
    xf = run(sk[y0], L[152][0], s)                          # (far silhouette under her chin)
    jy = jaw_y(L, s, xf - s * 0.05 * pc)
    rows = {}
    for t in (0.15, 0.3):
        y = int(round(jy + t * pc))
        far = run(sk[y], L[152][0], s); near = run(sk[y], L[152][0], -s)
        lo, hi = sorted((far, near)); lo, hi = lo + 3, hi - 3
        seg = lab[y - 1:y + 2, lo:hi + 1].mean(0)
        C = np.hypot(seg[:, 1], seg[:, 2]); h = np.degrees(np.arctan2(seg[:, 2], seg[:, 1]))
        dh = (h - nk[2] + 180) % 360 - 180
        st = np.abs(seg[4:, 0] - seg[:-4, 0]).max() if len(seg) > 4 else 0
        rows[t] = dict(y=y, lo=lo, hi=hi, dh=dh[np.argmax(np.abs(dh))], cmin=C.min() / nk[1], step=st, far=far,
                       hmean=np.degrees(np.arctan2(seg[:, 2].mean(), seg[:, 1].mean())), cmean=C.mean())
    r30 = rows[0.3]; r = max(3, int(0.04 * pc)); cx = int(r30["far"] - s * 0.1 * pc); cy = r30["y"]
    box = (cx - r, cy - r, cx + r, cy + r)
    Lk, A, B = meas.ok(np.median(a[box[1]:box[3], box[0]:box[2]].reshape(-1, 3), 0))
    fn = (Lk, np.hypot(A, B), np.degrees(np.arctan2(B, A)))
    return dict(pc=pc, s=s, nk=nk, rows=rows, box=box, fn=fn, jy=jy, xf=xf), im


if __name__ == "__main__":
    tag = sys.argv[1]
    faces = sys.argv[2:] or ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']
    import farneck_portrait as fp  # noqa
    tiles = []
    print("%-9s %-17s | %-28s | %-28s | %-17s %-17s %s" % ("face", "lit neck", "a: row .15 dh Cmin step", "a: row .30 dh Cmin step", "b: far neck", "portrait shade", "b dC dh"))
    for fc in faces:
        p = os.path.join(meas.S, "%s_%s.png" % (tag, fc))
        if not os.path.exists(p): print(fc, "missing"); continue
        m, im = measure(p)
        (bp, vp), _ = fp.spot(os.path.join(meas.R, ("own_her_23" if fc == "own" else fc + "_11") + ".png"))
        nk, fn = m["nk"], m["fn"]
        dC, dh = (fn[1] / vp[1] - 1) * 100, (fn[2] - vp[2] + 180) % 360 - 180
        ra = []
        for t in (0.15, 0.3):
            q = m["rows"][t]
            ok_ = abs(q["dh"]) <= 6 and q["cmin"] >= 0.75 and q["step"] <= 0.02
            ra.append("%+4.0f %3.0f%% %.3f %s" % (q["dh"], q["cmin"] * 100, q["step"], "ok" if ok_ else "FAIL"))
        print("%-9s L.%02d C.%03d h%3.0f | %-28s | %-28s | L.%02d C.%03d h%3.0f L.%02d C.%03d h%3.0f %+4.0f%% %+4.0f %s" % (
            fc, round(nk[0] * 100), round(nk[1] * 1000), nk[2], ra[0], ra[1], round(fn[0] * 100), round(fn[1] * 1000), fn[2],
            round(vp[0] * 100), round(vp[1] * 1000), vp[2], dC, dh, "PASS" if abs(dC) <= 15 and abs(dh) <= 5 else "FAIL"))
        cx, cy = int(m["rows"][0.3]["far"]), int(m["rows"][0.15]["y"])
        x0, y0 = cx - 150, cy - 110
        c = im.crop((x0, y0, x0 + 200, y0 + 200)).resize((400, 400), Image.LANCZOS)
        d = ImageDraw.Draw(c)
        for t, col in ((0.15, (255, 255, 0)), (0.3, (0, 255, 255))):
            q = m["rows"][t]; yy = (q["y"] - y0) * 2
            d.line(((q["lo"] - x0) * 2, yy, (q["hi"] - x0) * 2, yy), fill=col)
        b = m["box"]; d.rectangle(((b[0] - x0) * 2, (b[1] - y0) * 2, (b[2] - x0) * 2, (b[3] - y0) * 2), outline=(0, 255, 0))
        d.text((4, 4), fc, fill=(255, 255, 255))
        tiles.append(c)
    if tiles:
        sh = Image.new("RGB", (400 * min(5, len(tiles)), 400 * ((len(tiles) + 4) // 5)))
        for i, t in enumerate(tiles): sh.paste(t, ((i % 5) * 400, (i // 5) * 400))
        sh.save(os.path.join(meas.S, tag + "_neckx.jpg"), quality=90)
