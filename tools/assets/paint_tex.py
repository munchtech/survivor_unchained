#!/usr/bin/env python3
"""The kit-sheet painter: a kit's BaseColor and its normal map in, a painted albedo out
(style r2, painterly realism: forms stay real, surfaces read as painted).

    python tools/assets/paint_tex.py sheet ALBEDO NORMAL OUT [--preset stone|rock|wood|tiles|plain] [--k v ...]
    python tools/assets/paint_tex.py village [--out godot/art/kit_paint] [--decode]
    python tools/assets/paint_tex.py stall [--out godot/art/kit_paint]
    python tools/assets/paint_tex.py props [--out godot/art/kit_paint] [--decode]

What one sheet goes through (all at texel scale, wrapped so tiling sheets stay seamless):
  1. Simplify: mean-shift patches blended with a bilateral pass, so flat patches follow the
     forms; --detail keeps that much of the original micro-detail (0 none, 1 all).
  2. Cavity and edges from the normal map: the height integrated from the normals
     (Frankot-Chellappa), minus its blur, darkens the crevices (--cavity); the normals'
     convexity and their up-facing part light the top edges (--edge, --top).
  3. Palette: in Lab, a warm shift (--warm a,b) weighted to the midtones, the dull ones
     gaining most (--dull), a chroma gain (--chroma) and a pull toward the preset's hue
     (--hue a,b --pull), and a soft knee over Lab L (--knee: pale paint ages to cream, not white).
  4. Strokes: white noise smeared along the dominant direction (perpendicular to the
     structure tensor's main axis: a plank's grain, a stone's long axis), low contrast
     (--stroke); a screen-space brush filter adds the hand on top.

Sheets are read as images (PNG/WebP/JPEG). The village kit's colour sheets are kept as
WebP in godot/art/srgb; their normals are KTX2 only, so `village --decode` first has
Godot decode them to godot/.kit_paint_src (tools/assets/ktx_decode.gd; it takes the
godot turn). Output: WebP (q92) at the input's size, with a Godot .import beside it
(VRAM compressed, mipmaps: the same BC7/ASTC sheets as today, so no runtime cost), and
DIR/kit_paint.json, the shader weather each painted sheet is drawn with (KitLook).

`stall` paints the market stall's canvas (sun-faded stripes, soft folds, a darker
valance edge) and its wood (a strip of the painted WoodTrim), for --kit-paint's stall.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TURN = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"

# Per material family. weather: the kit shader's saturation kept and colour multiply
# (KitLook's table) once the sheet is painted: the paint carries the warmth, so the
# weathering is lighter than the plain sheets'.
PRESETS = {
    "plain": dict(detail=0.3, cavity=0.35, edge=0.25, top=0.12, warm=(2.0, 5.0), dull=1.0, chroma=1.1, hue=(0, 0), pull=0.0,
                  stroke=0.028, value=1.0, ms=(5, 12), weather=(0.82, (0.88, 0.87, 0.85))),
    # rough stone ring and walls: warm ochre-grey stones, dark gaps, light tops
    "stone": dict(detail=0.22, cavity=0.75, edge=0.4, top=0.3, warm=(3.0, 9.0), dull=1.4, chroma=1.15, hue=(6, 16), pull=0.22,
                  stroke=0.028, value=0.97, ms=(6, 14), weather=(0.86, (0.9, 0.87, 0.82))),
    "rock": dict(detail=0.22, cavity=0.75, edge=0.4, top=0.3, warm=(3.0, 9.0), dull=1.4, chroma=1.15, hue=(6, 16), pull=0.22,
                 stroke=0.028, value=0.97, ms=(6, 14), weather=(0.86, (0.9, 0.87, 0.82))),
    # warm painted wood: honey and umber, grain as long strokes
    "wood": dict(detail=0.3, cavity=0.45, edge=0.25, top=0.15, warm=(4.0, 8.0), dull=1.2, chroma=1.18, hue=(14, 30), pull=0.18,
                 stroke=0.045, value=1.06, ms=(5, 12), weather=(0.88, (0.86, 0.82, 0.76))),
    # terracotta round tiles: warm, varied, sun-baked tops, dark undersides
    "tiles": dict(detail=0.25, cavity=0.6, edge=0.3, top=0.25, warm=(2.0, 6.0), dull=1.0, chroma=0.92, hue=(22, 28), pull=0.2,
                  stroke=0.025, value=0.9, ms=(6, 14), weather=(0.76, (0.84, 0.77, 0.7))),
    # E4 bark (env_trees.py): grey-brown scales simplified to plates, deep crevices, the lichen kept cool
    "bark": dict(detail=0.25, cavity=0.7, edge=0.35, top=0.1, warm=(2.0, 6.0), dull=1.2, chroma=1.1, hue=(6, 12), pull=0.15,
                 stroke=0.035, value=1.0, ms=(6, 14), weather=(0.92, (0.92, 0.9, 0.87))),
    # E4 needles and leaves (env_trees.py): clumps kept as flat painted masses, a pull toward a cool
    # spruce green (never gold: the warmth comes from the light), little warm shift
    "foliage": dict(detail=0.1, cavity=0.45, edge=0.3, top=0.12, warm=(0.0, 1.0), dull=0.5, chroma=1.05, hue=(-14, 4), pull=0.2,
                    stroke=0.03, value=1.0, ms=(6, 12), weather=(0.94, (0.93, 0.95, 0.92))),
}
VILLAGE = {"T_UnevenBrick": "stone", "T_RockTrim": "rock", "T_WoodTrim": "wood", "T_RoundTiles": "tiles"}
# The set dressing's shared trims (env/props: 41 props use the furniture trim, the camp's chest among them): its pale
# painted bands aged to cream under the knee, so the chest reads as painted wood, not a white toy.
PROPS = {"T_Trim_Furniture": ("wood", {"knee": 62.0, "value": 0.95})}
SRGB = ROOT / "godot/art/srgb/env/village"
SRC = ROOT / "godot/.kit_paint_src"


def wrap(f, img, pad):
    """f on img with a wrapped border (seamless sheets)."""
    p = np.pad(img, ((pad, pad), (pad, pad)) + ((0, 0),) * (img.ndim - 2), mode="wrap")
    r = f(p)
    return r[pad:-pad, pad:-pad]


def blur(img, s):
    k = int(s * 3) | 1
    return wrap(lambda p: cv2.GaussianBlur(p, (k, k), s), img, k)


def height_from_normals(n):
    """Frankot-Chellappa: the height whose gradients the (OpenGL, green-up) normals give."""
    nz = np.clip(n[..., 2], 0.2, 1)
    gx = -n[..., 0] / nz                  # dh/dcol
    gy = n[..., 1] / nz                   # dh/drow (rows run down, green points up)
    h, w = gx.shape
    wx = np.fft.fftfreq(w) * 2 * np.pi
    wy = np.fft.fftfreq(h) * 2 * np.pi
    WX, WY = np.meshgrid(wx, wy)
    d = WX ** 2 + WY ** 2
    d[0, 0] = 1
    H = (-1j * WX * np.fft.fft2(gx) - 1j * WY * np.fft.fft2(gy)) / d
    H[0, 0] = 0
    return np.real(np.fft.ifft2(H)).astype(np.float32)


def norm(x, lo=2, hi=98):
    a, b = np.percentile(x, [lo, hi])
    s = max(abs(a), abs(b), 1e-6)
    return np.clip(x / s, -1, 1).astype(np.float32)


def lic(direction, steps=12, step=2.2, seed=7, grain=1.8):
    """Line-integral convolution of white noise along a unit direction field."""
    h, w = direction.shape[:2]
    rng = np.random.default_rng(seed)
    noise = blur(rng.random((h, w), dtype=np.float32), grain)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    acc = noise.copy()
    tot = 1.0
    for sgn in (1, -1):
        px, py = xs.copy(), ys.copy()
        for i in range(steps):
            dx = cv2.remap(direction[..., 0], px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            dy = cv2.remap(direction[..., 1], px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            px = (px + sgn * step * dx) % w
            py = (py + sgn * step * dy) % h
            wgt = 1 - i / steps
            acc += wgt * cv2.remap(noise, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            tot += wgt
    s = acc / tot
    return norm(s - blur(s, 8))


def paint(albedo, normal, p):
    """albedo: HxWx3 sRGB 0..1; normal: HxWx3 0..1 (OpenGL). Returns painted sRGB 0..1."""
    a = albedo.astype(np.float32)
    n = normal.astype(np.float32) * 2 - 1
    n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-6)
    h, w = a.shape[:2]
    # 1. simplify: mean-shift patches at half size (flat value shapes), bilateral at full
    small = cv2.resize(a, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    sp, sr = p["ms"]
    ms8 = wrap(lambda q: cv2.pyrMeanShiftFiltering(q, sp, sr), (small * 255).astype(np.uint8), 16)
    ms = cv2.resize(ms8.astype(np.float32) / 255, (w, h), interpolation=cv2.INTER_LINEAR)
    bil = a
    for _ in range(2):
        bil = wrap(lambda q: cv2.bilateralFilter(q, 9, 0.08, 4), bil, 8)
    simp = 0.6 * ms + 0.4 * bil
    out = simp + p["detail"] * (a - bil)
    # 2. cavity (integrated height minus its blur) and lit top edges (convexity, up-facing)
    hgt = height_from_normals(n)
    if np.corrcoef(hgt.ravel()[::97], cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).ravel()[::97])[0, 1] < -0.5:
        hgt = -hgt  # (a sheet whose green runs the other way)
    cav = norm(hgt - blur(hgt, 18))
    cav_fine = norm(hgt - blur(hgt, 4))
    div = norm(-(np.gradient(blur(n[..., 0], 1.5), axis=1) - np.gradient(blur(n[..., 1], 1.5), axis=0)))
    up = np.clip(n[..., 1], 0, 1) * np.clip(div * 2, 0, 1)
    shade = 1 + p["cavity"] * np.minimum(0.65 * cav + 0.35 * cav_fine, 0.25) \
        + p["edge"] * np.clip(div, 0, 1) * 0.5 + p["top"] * up
    out = out * shade[..., None]
    # 3. palette in Lab: warm midtones, dull ones most; a pull toward the family's hue
    lab = cv2.cvtColor(np.clip(out, 0, 1).astype(np.float32), cv2.COLOR_RGB2Lab)
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.sqrt(A ** 2 + B ** 2)
    mid = np.clip(1 - np.abs(L - 52) / 48, 0, 1) ** 0.8
    wgt = mid * (1 + p["dull"] * np.clip(1 - C / 28, 0, 1))
    A = A * p["chroma"] + p["warm"][0] * wgt
    B = B * p["chroma"] + p["warm"][1] * wgt
    t = p["pull"] * mid
    A = A + (p["hue"][0] - A) * t
    B = B + (p["hue"][1] - B) * t
    L = np.clip(L * p["value"], 0, 100)
    kn = p.get("knee", 100.0)
    L = np.where(L > kn, kn + (L - kn) * 0.45, L)
    out = cv2.cvtColor(np.dstack([L, A, B]).astype(np.float32), cv2.COLOR_Lab2RGB)
    # 4. strokes along the dominant direction (perpendicular to the structure's main axis)
    g = cv2.cvtColor(np.clip(simp, 0, 1).astype(np.float32), cv2.COLOR_RGB2GRAY) + 0.5 * hgt / (np.abs(hgt).max() + 1e-6)
    gx, gy = np.gradient(g, axis=1), np.gradient(g, axis=0)
    jxx, jyy, jxy = blur(gx * gx, 28), blur(gy * gy, 28), blur(gx * gy, 28)
    ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2
    direction = np.dstack([np.cos(ang), np.sin(ang)]).astype(np.float32)
    s = lic(direction)
    out = out * (1 + p["stroke"] * s)[..., None]
    return np.clip(out, 0, 1)


IMPORT = """[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="{src}"

[params]

compress/mode=2
compress/high_quality=true
compress/lossy_quality=0.7
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map=2
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=0
"""


def save(img, out: Path, mode="RGB"):
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), mode).save(out, quality=92, method=6)
    imp = Path(str(out) + ".import")
    try:
        rel = "res://" + out.resolve().relative_to((ROOT / "godot").resolve()).as_posix()
        if not imp.exists():
            imp.write_text(IMPORT.format(src=rel), encoding="utf-8")
    except ValueError:
        pass  # outside the project: no import file
    print(f"{out} {img.shape[1]}x{img.shape[0]}")


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255


def preset(name, over):
    p = dict(PRESETS[name])
    for k, v in over.items():
        if v is None: continue
        p[k] = tuple(float(x) for x in v.split(",")) if k in ("warm", "hue", "ms") else float(v)
    if "ms" in over and over["ms"]: p["ms"] = tuple(int(x) for x in p["ms"])
    return p


def decode(names, kit="village"):
    """The normals as PNG through Godot (KTX2 is all there is of them)."""
    need = [f"res://assets/env/{kit}/{n}_Normal.ktx2" for n in names if not (SRC / f"{n}_Normal.png").exists()]
    if not need: return
    tag = "art-style: kit paint decode"
    subprocess.run([sys.executable, TURN, "take", "godot", tag, "--wait", "1800", "--stale-ok"], check=True)
    try:
        subprocess.run([GODOT, "--headless", "--path", str(ROOT / "godot"), "-s", str(ROOT / "tools/assets/ktx_decode.gd"), "--", str(SRC)] + need, check=True, timeout=600)
    finally:
        subprocess.run([sys.executable, TURN, "give", "godot", tag])


def stall(out: Path):
    """The cloth stall's canvas (u across the awning: 8 stripes; v front 0 to back 1) and wood."""
    W, H = 1024, 512
    rng = np.random.default_rng(3)
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    U, V = np.meshgrid(u, v)
    blue = np.array([0.20, 0.42, 0.62]); cream = np.array([0.90, 0.85, 0.72])
    # stripes with soft painted edges and a wobble
    x = U * 8 + 0.06 * np.sin(V * 9 + 1.3) + 0.03 * np.sin(V * 23)
    edge = np.clip((np.abs((x % 2) - 1) - 0.5) * 9 + 0.5, 0, 1)  # 1 inside a blue stripe
    col = cream * (1 - edge[..., None]) + blue * edge[..., None]
    # per-stripe variation (dye laid by hand), sun-fading toward the back and up top
    k = np.floor(x).astype(int) % 8
    var = rng.normal(0, 0.035, 8)[k][..., None]
    col = col * (1 + var)
    fade = 0.28 * np.clip(V * 0.9 + 0.1, 0, 1)
    lum = col.mean(axis=2, keepdims=True)
    col = col + (np.clip(lum * 1.15 + 0.06, 0, 1) - col) * fade[..., None] * np.array([1, 0.95, 0.85])
    # soft folds: long sags along the stripes (between the poles), light on their crests
    fold = 0.06 * np.sin(U * np.pi * 6 + 0.4) + 0.035 * np.sin(U * np.pi * 17 + V * 2) + 0.02 * np.sin(U * 41 + V * 5)
    col = col * (1 + fold[..., None])
    # the valance edge (front, v=0): the canvas folds over, darker; a little grime at the hem
    val = np.clip(1 - V / 0.14, 0, 1) ** 1.5
    col = col * (1 - 0.32 * val[..., None])
    hem = np.clip(1 - V / 0.03, 0, 1)
    col = col * (1 - 0.15 * hem[..., None])
    # weave and brush: low-contrast noise smeared along the stripes
    direction = np.dstack([np.zeros((H, W)), np.ones((H, W))]).astype(np.float32)
    s = lic(direction, steps=14, step=2.0, seed=11)
    col = col * (1 + 0.05 * s[..., None])
    save(np.clip(col, 0, 1).astype(np.float32), out / "stall_canvas.webp")
    # wood: the painted WoodTrim's dark plank band (rows ~31-47 % of the sheet), tiled square
    wood = out / "T_WoodTrim_BaseColor.webp"
    if wood.exists():
        wd = load(wood)
        h = wd.shape[0]
        band = wd[int(h * 0.322):int(h * 0.46)]
        band = cv2.resize(band, (1024, max(8, band.shape[0] * 1024 // band.shape[1])), interpolation=cv2.INTER_AREA)
        # boards: the band stacked with offsets (u runs along the grain), each a shade apart
        rows, y = [], 0
        while y < 512:
            r = np.roll(band, int(rng.integers(0, 1024)), axis=1) * (1 + rng.normal(0, 0.05))
            r[:2] *= 0.6  # the gap between boards
            rows.append(r); y += r.shape[0]
        boards = cv2.resize(np.vstack(rows)[:512], (512, 512), interpolation=cv2.INTER_AREA)
        save(boards, out / "stall_wood.webp")
        save(np.ascontiguousarray(np.rot90(boards)), out / "stall_post.webp")  # grain along v (a post's length)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("sheet", help="paint one sheet")
    one.add_argument("albedo"); one.add_argument("normal"); one.add_argument("out")
    one.add_argument("--preset", default="plain", choices=sorted(PRESETS))
    for k in ("detail", "cavity", "edge", "top", "warm", "dull", "chroma", "hue", "pull", "stroke", "value", "ms", "knee"):
        one.add_argument("--" + k)
    vil = sub.add_parser("village", help="paint the well's four village sheets")
    vil.add_argument("--out", default=str(ROOT / "godot/art/kit_paint"))
    vil.add_argument("--decode", action="store_true", help="decode missing normals through Godot first")
    vil.add_argument("--only", help="comma-separated sheet names (T_RoundTiles,...)")
    st = sub.add_parser("stall", help="paint the cloth stall's canvas and wood")
    st.add_argument("--out", default=str(ROOT / "godot/art/kit_paint"))
    pr = sub.add_parser("props", help="paint the set dressing's shared trims (PROPS)")
    pr.add_argument("--out", default=str(ROOT / "godot/art/kit_paint"))
    pr.add_argument("--decode", action="store_true", help="decode missing normals through Godot first")
    a = ap.parse_args()
    if a.cmd == "sheet":
        p = preset(a.preset, {k: getattr(a, k) for k in ("detail", "cavity", "edge", "top", "warm", "dull", "chroma", "hue", "pull", "stroke", "value", "ms", "knee")})
        save(paint(load(a.albedo), load(a.normal), p), Path(a.out))
    elif a.cmd == "village":
        out = Path(a.out)
        names = [n for n in VILLAGE if not a.only or n in a.only.split(",")]
        if a.decode: decode(names)
        meta_path = out / "kit_paint.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        for n in names:
            p = PRESETS[VILLAGE[n]]
            save(paint(load(SRGB / f"{n}_BaseColor.webp"), load(SRC / f"{n}_Normal.png"), p), out / f"{n}_BaseColor.webp")
            meta[f"{n}_BaseColor"] = {"weather_sat": p["weather"][0], "weather_tint": list(p["weather"][1])}
        meta_path.write_text(json.dumps(meta, indent=1) + "\n")
    elif a.cmd == "props":
        out = Path(a.out)
        if a.decode: decode(list(PROPS), "props")
        meta_path = out / "kit_paint.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        for n, (pre, over) in PROPS.items():
            p = dict(PRESETS[pre], **over)
            save(paint(load(SRGB.parent / "props" / f"{n}_BaseColor.webp"), load(SRC / f"{n}_Normal.png"), p), out / f"{n}_BaseColor.webp")
            meta[f"{n}_BaseColor"] = {"weather_sat": p["weather"][0], "weather_tint": list(p["weather"][1])}
        meta_path.write_text(json.dumps(meta, indent=1) + "\n")
    else:
        stall(Path(a.out))


if __name__ == "__main__":
    main()
