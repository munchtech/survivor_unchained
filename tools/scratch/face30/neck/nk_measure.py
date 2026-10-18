"""Face 30 neck: python nk_measure.py <glob of shots> [--ref TAG]. Per frame: the jaw/neck shade (darkest half of the
shade box's skin) against her lit cheek: Oklab hue (deg), chroma, HSV sat, luma; ratio of chroma and sat; the largest
luma step between adjacent 4-px rows down the neck strip. --ref TAG: also the face box's mean |luma| change outside the
jaw/neck box against the frame of the same name with TAG in place of this one's."""
import sys, glob, os, re, colorsys
import numpy as np
from PIL import Image
BOX = {  # turn: (shade box, lit cheek box, neck strip, face box) as x0,y0,x1,y1 at 1920x1080
    0: ((1000, 440, 1075, 505), (960, 370, 1000, 410), (1070, 440, 1100, 532), (900, 200, 1120, 520)),
    45: ((1020, 440, 1080, 510), (950, 375, 990, 410), (990, 470, 1010, 560), (900, 200, 1120, 560)),
}
NECK = {0: (1080, 470, 1110, 520), 45: (1035, 540, 1075, 575)}   # her lit neck below (the graft), at 1920x1080
def oklab(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(c @ M1.T)
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    return lms @ M2.T
def stats(px):
    lab = oklab(px.astype(float)).mean(0)
    hue = np.degrees(np.arctan2(lab[2], lab[1])); ch = np.hypot(lab[1], lab[2])
    m = px.mean(0) / 255.0; h, s, v = colorsys.rgb_to_hsv(*m)
    luma = (px.astype(float) @ [0.2126, 0.7152, 0.0722]).mean()
    return hue, ch, s, h * 360, luma
def skin(px):  # drop hair (very red-orange saturated and dark), armour/background (blue > red)
    r, g, b = px[:, 0].astype(int), px[:, 1].astype(int), px[:, 2].astype(int)
    return px[(r >= b) & (r > 40) & ~((r - g > 70) & (g < 110))]
def turn_of(n): return int(re.search(r"_t(\d{3})", n).group(1))
def measure(path):
    a = np.asarray(Image.open(path).convert("RGB")); t = turn_of(os.path.basename(path))
    sb, lb, ns, fb = BOX[t]
    sp = skin(a[sb[1]:sb[3], sb[0]:sb[2]].reshape(-1, 3))
    lum = sp.astype(float) @ [0.2126, 0.7152, 0.0722]
    sh = sp[lum <= np.percentile(lum, 50)]
    lp = skin(a[lb[1]:lb[3], lb[0]:lb[2]].reshape(-1, 3))
    S, L = stats(sh), stats(lp)
    nb = NECK[t]; N = stats(skin(a[nb[1]:nb[3], nb[0]:nb[2]].reshape(-1, 3)))
    col = a[ns[1]:ns[3], ns[0]:ns[2]].astype(float) @ [0.2126, 0.7152, 0.0722]
    rows = col.reshape(-1, 4, col.shape[1]).mean((1, 2)) if col.shape[0] % 4 == 0 else col[: col.shape[0] // 4 * 4].reshape(-1, 4, col.shape[1]).mean((1, 2))
    rows = rows[int(np.argmin(rows[:10])) + 2:]   # (from below the jaw's own shadow edge)
    step = np.abs(np.diff(rows)).max()
    dh = (S[0] - L[0] + 180) % 360 - 180
    # (a blotch: the box's chroma, blurred, its 5th percentile against its median; the hue of its 10% greyest against the box's)
    from scipy import ndimage
    lab = oklab(a[sb[1]:sb[3], sb[0]:sb[2]].astype(float))
    lab = np.stack([ndimage.gaussian_filter(lab[..., k], 3) for k in range(3)], -1).reshape(-1, 3)
    cc = np.hypot(lab[:, 1], lab[:, 2]); keep = (lab[:, 1] > 0) & (lab[:, 0] > 0.3)
    cc, lk = cc[keep], lab[keep]
    lo = cc <= np.percentile(cc, 10)
    hb = np.degrees(np.arctan2(lk[lo, 2].mean(), lk[lo, 1].mean())) - np.degrees(np.arctan2(lk[:, 2].mean(), lk[:, 1].mean()))
    return dict(nk_sat=S[2] / N[2], nk_dh=(S[0] - N[0] + 180) % 360 - 180, blot=np.percentile(cc, 5) / np.median(cc), blot_h=hb,sh_hue=S[0], lit_hue=L[0], dhue=dh, ch_ratio=S[1] / L[1], sat_ratio=S[2] / L[2], sh_luma=S[4], lit_luma=L[4], step=step)
def facediff(p, q):
    t = turn_of(os.path.basename(p)); sb, lb, ns, fb = BOX[t]
    A = np.asarray(Image.open(p).convert("RGB")).astype(float) @ [0.2126, 0.7152, 0.0722]
    B = np.asarray(Image.open(q).convert("RGB")).astype(float) @ [0.2126, 0.7152, 0.0722]
    m = np.zeros(A.shape, bool); m[fb[1]:fb[3], fb[0]:fb[2]] = True
    jx0, jy0 = min(sb[0], ns[0]) - 20, sb[1] - 25; m[jy0:, jx0:max(sb[2], ns[2]) + 30] = False
    return np.abs(A - B)[m].mean(), (A - B)[m].mean()
if __name__ == "__main__":
    args = sys.argv[1:]; ref = None
    if "--ref" in args: i = args.index("--ref"); ref = args[i + 1]; args = args[:i] + args[i + 2:]
    files = sorted(set(sum((glob.glob(g) for g in args), [])))
    print(f"{'frame':52s} dhue  chR  satR shL  litL step    blot blotH nkSat nkdh" + ("  face|d| face d" if ref else ""))
    for f in files:
        if "_half" in f: continue
        r = measure(f); n = os.path.basename(f)[:-4]
        ok = abs(r['dhue']) <= 10 and r['sat_ratio'] >= 0.8
        line = f"{n:52s} {r['dhue']:+5.1f} {r['ch_ratio']:.2f} {r['sat_ratio']:.2f} {r['sh_luma']:4.0f} {r['lit_luma']:4.0f} {r['step']:4.1f} {'OK' if ok else '--'} {r['blot']:.2f} {r['blot_h']:+5.1f} {r['nk_sat']:.2f} {r['nk_dh']:+5.1f}"
        if ref:
            tag = re.match(r"nk_([^_]+)_", n).group(1); q = f.replace(f"nk_{tag}_", f"nk_{ref}_")
            if os.path.exists(q): d = facediff(f, q); line += f"  {d[0]:5.2f} {d[1]:+5.2f}"
        print(line)
