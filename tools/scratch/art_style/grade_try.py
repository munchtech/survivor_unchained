"""Numpy twin of Atmosphere.GradeTry (godot/src/World/Atmosphere.cs, --grade-try).

  python grade_try.py IN.png OUT.png "vib=0.4,shadow=#2a3550,shadowk=0.6,hi=0.5"
  python grade_try.py IN.png OUT.png "" --lut DUMP.bin      (LUT from the engine's --grade-dump, then the try)
  python grade_try.py --diff A.png B.png

Importable: apply_try(rgb_srgb_float_HxWx3, try_string), apply_lut(rgb, lut_path).
Same constants, order and matrices as Atmosphere.cs. `mute` changes the base grade, which only the engine has.
"""
import sys
import numpy as np
from PIL import Image

KEYS = {"mute", "vib", "skin", "shadow", "shadowk", "lift", "hi"}


def lin(c):
    c = np.asarray(c, np.float32)
    return np.where(c < 0.04045, c * 0.0773993808, np.power(np.maximum(c * 0.9478672986 + 0.0521327014, 0), 2.4)).astype(np.float32)


def srgb(c):
    c = np.asarray(c, np.float32)
    return np.where(c < 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 0.41666) - 0.055).astype(np.float32)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def oklab(c):
    """Linear sRGB (...,3) -> L, chroma, hue degrees."""
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    l = np.cbrt(np.maximum(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b, 0))
    m = np.cbrt(np.maximum(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b, 0))
    s = np.cbrt(np.maximum(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b, 0))
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, np.sqrt(A * A + B * B), np.degrees(np.arctan2(B, A))


def from_oklab(L, A, B):
    l = L + 0.3963377774 * A + 0.2158037573 * B
    m = L - 0.1055613458 * A - 0.0638541728 * B
    s = L - 0.0894841775 * A - 1.2914855480 * B
    l, m, s = l * l * l, m * m * m, s * s * s
    return np.stack([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                     -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                     -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s], -1)


def parse(spec):
    p = dict(mute=None, vib=0.0, skin=1.0, shadow=None, shadowk=0.0, lift=0.0, hi=0.0)
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        k, _, v = part.partition("=")
        k = k.strip().lower(); v = v.strip()
        if k not in KEYS:
            print(f"grade-try: unknown key '{k}' ignored", file=sys.stderr)
            continue
        if k == "shadow":
            if v.startswith("_"):
                v = "#" + v[1:]
            h = v.lstrip("#")
            p[k] = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
        else:
            p[k] = float(v)
    return p


def _inside(rgb):
    return np.all((rgb >= -1e-5) & (rgb <= 1 + 1e-5), -1)


VIB_DARK, VIB_FROM, VIB_TO = 0.2, 0.44, 0.52
HI_SKIN, HI_C0, HI_C1 = 0.85, 0.06, 0.085


def vib_deep(L):
    """Atmosphere.Paint.VibDeep: the vibrance's share by Oklab lightness."""
    return VIB_DARK + (1 - VIB_DARK) * smooth(VIB_FROM, VIB_TO, L)


def apply_lin(out_lin, p):
    """The Apply step on linear sRGB (...,3)."""
    L, C, h = oklab(out_lin.astype(np.float32))
    skin_hue = smooth(15, 30, h) * (1 - smooth(75, 90, h))
    skin_w = p["skin"] * skin_hue * smooth(0.025, 0.05, C) * smooth(0.30, 0.45, L)
    if p["vib"] != 0:
        dull = 1 - smooth(0.02, 0.20, C)
        light = smooth(0.04, 0.18, L) * vib_deep(L)
        C = C * (1 + p["vib"] * dull * light * (1 - skin_w))
    if p["hi"] != 0:
        skin_hi = HI_SKIN * p["skin"] * skin_hue * smooth(HI_C0, HI_C1, C) * smooth(0.30, 0.45, L)
        C = C * (1 + p["hi"] * smooth(0.55, 0.90, L) * smooth(0.008, 0.03, C) * (1 - skin_hi))
    hr = np.radians(h)
    a, b = C * np.cos(hr), C * np.sin(hr)
    if p["lift"] != 0:
        L = np.minimum(L + p["lift"] * (1 - smooth(0, 0.35, L)), 1)
    if p["shadow"] is not None and p["shadowk"] != 0:
        ls, cs, hs = oklab(lin(p["shadow"]))
        dark = 1 - smooth(0.12, 0.45, L)
        fade_black = smooth(0, 0.08, L)
        own = 1 - smooth(0.02, 0.07, C)
        w = np.clip(p["shadowk"] * dark * own * fade_black, 0, 1)
        ct = cs * np.minimum(L / max(float(ls), 0.05), 1)
        hsr = np.radians(hs)
        a = a + (ct * np.cos(hsr) - a) * w
        b = b + (ct * np.sin(hsr) - b) * w
    rgb = from_oklab(L, a, b)
    bad = ~_inside(rgb)
    if bad.any():
        lo = np.zeros(L.shape, np.float32)
        hi = np.ones(L.shape, np.float32)
        for _ in range(12):
            mid = (lo + hi) * 0.5
            ok = _inside(from_oklab(L, a * mid, b * mid))
            lo = np.where(ok, mid, lo)
            hi = np.where(ok, hi, mid)
        rgb = np.where(bad[..., None], from_oklab(L, a * lo, b * lo), rgb)
    return np.clip(rgb, 0, 1).astype(np.float32)


def apply_try(rgb, try_string):
    """sRGB float HxWx3 (0..1) -> sRGB float, with the try applied (linear in the middle)."""
    p = parse(try_string)
    if p["mute"] is not None:
        print("note: mute changes the base grade, which only the engine has; ignored here")
    if p["vib"] == 0 and p["hi"] == 0 and p["lift"] == 0 and (p["shadow"] is None or p["shadowk"] == 0):
        return np.asarray(rgb, np.float32)
    return srgb(apply_lin(lin(rgb), p))


def apply_lut(rgb, lut_path):
    """Trilinear lookup in an engine --grade-dump table (32^3 RGB8, blue-major), sRGB in and out."""
    n = 32
    lut = np.fromfile(lut_path, np.uint8)
    if lut.size != n * n * n * 3:
        raise SystemExit(f"{lut_path}: expected {n*n*n*3} bytes, got {lut.size}")
    lut = lut.reshape(n, n, n, 3).astype(np.float32) / 255  # [b, g, r, ch]
    x = np.clip(np.asarray(rgb, np.float32) * n - 0.5, 0, n - 1)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    r0, g0, b0 = (np.minimum(np.floor(v).astype(np.int32), n - 2) for v in (r, g, b))
    fr, fg, fb = (r - r0)[..., None], (g - g0)[..., None], (b - b0)[..., None]
    out = 0
    for db, wb in ((0, 1 - fb), (1, fb)):
        for dg, wg in ((0, 1 - fg), (1, fg)):
            for dr, wr in ((0, 1 - fr), (1, fr)):
                out = out + lut[b0 + db, g0 + dg, r0 + dr] * (wb * wg * wr)
    return out.astype(np.float32)


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), np.float32) / 255


def save(rgb, path):
    Image.fromarray(np.clip(np.rint(rgb * 255), 0, 255).astype(np.uint8)).save(path)


def diff(a_path, b_path):
    a = np.asarray(Image.open(a_path).convert("RGB"), np.int16)
    b = np.asarray(Image.open(b_path).convert("RGB"), np.int16)
    d = np.abs(a - b)
    for i, n in enumerate("RGB"):
        print(f"{n}: mean {d[..., i].mean():.3f}  p99 {np.percentile(d[..., i], 99):.1f}")
    print(f"share of pixels differing by > 8 in any channel: {100 * (d.max(-1) > 8).mean():.3f}%")


def main(argv):
    if argv and argv[0] == "--diff":
        return diff(argv[1], argv[2])
    lut = None
    if "--lut" in argv:
        i = argv.index("--lut")
        lut = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) < 2:
        raise SystemExit(__doc__)
    img = load(argv[0])
    if lut:
        img = apply_lut(img, lut)
    if len(argv) > 2:
        img = apply_try(img, argv[2])
    save(img, argv[1])


if __name__ == "__main__":
    main(sys.argv[1:])
