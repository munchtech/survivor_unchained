#!/usr/bin/env python3
"""The shared painted props atlas (E7a), made here from noise (no kit, no scan).

    python tools/assets/env_props_atlas.py [--size 2048]

One sheet for every set-dressing prop env_props.py builds (look bible 11: "one prop
atlas"). Each region is a material, painted near-neutral where a palette tints it
(the props' vertex colours carry the palette: tools/assets/env_props.json), then put
through paint_tex.paint (painterly realism: simplified surfaces, strokes along the
grain, cavity and lit edges from the region's own height).

Regions (image pixels at 2048, x right, y down; the metres each spans across):
  wood     0,0      1024x2048  1.0 m x 2.0 m   weathered boards, grain down y, knots
  bark     1024,0   512x1024   0.6 m x 1.2 m   fissured plates, grain down y
  endgrain 1536,0   512x512    0.5 m           rings, pith, radial checks, a bark rim
  iron     1536,512 512x512    0.4 m           forged black iron, rust in patches
  cloth    1024,1024 512x512   0.4 m           wool weave, pale (tinted per prop)
  canvas   1536,1024 512x512   0.4 m           coarse sacking, oat, stains
  leather  1024,1536 512x512   0.4 m           creased hide, scuffs
  rollend  1536,1536 256x256   0.3 m           a rolled blanket's end: a spiral of layers
  stone    1536,1792 512x256   1.0 m x 0.5 m   dressed stone, warm grey
  (1792,1536 256x256 free)

Out (godot/art/world/props/): props_albedo.jpg (sRGB), props_normal.png (OpenGL,
green up), props_orm.png (R ao=1, G roughness, B metal), props_atlas.json (the
regions, in UV 0-1 with v up as Blender writes it, and their metres).
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "assets"))
import paint_tex  # noqa: E402

OUT = ROOT / "godot" / "art" / "world" / "props"
N = 2048
# name: (x, y, w, h) in pixels at N, metres across w, paint_tex preset and overrides
REGIONS = {
    "wood": ((0, 0, 1024, 2048), 1.0, "wood", {"knee": 64.0, "value": 0.95, "chroma": 0.9, "warm": "1,3", "pull": "0.1"}),
    "bark": ((1024, 0, 512, 1024), 0.6, "bark", {"chroma": 0.85, "warm": "1,2"}),
    "endgrain": ((1536, 0, 512, 512), 0.5, "wood", {"stroke": 0.02, "chroma": 0.95, "warm": "1,3", "pull": "0.1"}),
    "iron": ((1536, 512, 512, 512), 0.4, "plain", {"chroma": 0.9, "warm": "1,3", "stroke": 0.02}),
    "cloth": ((1024, 1024, 512, 512), 0.4, "plain", {"detail": 0.45, "warm": "0,0", "chroma": 1.0, "stroke": 0.02}),
    "canvas": ((1536, 1024, 512, 512), 0.4, "plain", {"detail": 0.4, "stroke": 0.025}),
    "leather": ((1024, 1536, 512, 512), 0.4, "plain", {"detail": 0.35, "hue": "12,22", "pull": "0.15"}),
    "rollend": ((1536, 1536, 256, 256), 0.3, "plain", {"detail": 0.5, "warm": "0,0", "stroke": 0.015}),
    "stone": ((1536, 1792, 512, 256), 1.0, "stone", {"chroma": 0.8, "warm": "1,2", "pull": "0.05"}),
}


# ---------------------------------------------------------------- noise --
def vnoise(h, w, cy, cx, rng):
    """Smooth periodic value noise: cy x cx cells over h x w pixels."""
    r = rng.random((cy, cx)).astype(np.float32)
    r = np.pad(r, ((0, 1), (0, 1)), mode="wrap")
    big = cv2.resize(r, (w + w // cx, h + h // cy), interpolation=cv2.INTER_CUBIC)
    return big[:h, :w]


def fbm(h, w, cy, cx, rng, octs=4, gain=0.5):
    s, a, t = np.zeros((h, w), np.float32), 1.0, 0.0
    for _ in range(octs):
        s += a * vnoise(h, w, max(1, cy), max(1, cx), rng)
        t += a
        a *= gain
        cy, cx = cy * 2, cx * 2
    return s / t


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def srgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def mix(a, b, t):
    t = np.asarray(t, np.float32)[..., None]
    return a * (1 - t) + b * t


# -------------------------------------------------------------- regions --
# Each returns albedo (h, w, 3, sRGB 0-1), height (h, w, metres), rough (h, w), metal (h, w).

def wood(h, w, m, rng):
    ppm = w / m
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    # Grain: lines down y, warped, with growth-ring bands of uneven width.
    # (round 2: the warp a third of what it was, so the grain runs straight with a lean, not in noodles)
    warp = (fbm(h, w, 6, 3, rng, 3) - 0.5) * 0.03 * ppm + (fbm(h, w, 24, 8, rng, 2) - 0.5) * 0.006 * ppm
    u = (x + warp) / ppm  # metres across
    # Ring spacing uneven across the board (a log's fast and slow years), lines thin and soft.
    freq = 34 + 18 * fbm(h, w, 2, 6, rng, 2)
    band = np.sin(u * 2 * np.pi * freq + 4 * fbm(h, w, 3, 10, rng, 2))
    late = ss(0.72, 0.98, band) * (0.6 + 0.4 * fbm(h, w, 12, 30, rng, 2))
    fine = fbm(h, w, 48, 400, rng, 2)  # pores and fibres, stretched down the grain
    streak = fbm(h, w, 2, 28, rng, 3)  # long colour streaks down the grain
    # Knots: a few dark eyes with a soft ring.
    kn = np.zeros((h, w), np.float32)
    for _ in range(int(m * h / w * 3)):
        cx, cy = rng.random() * w, rng.random() * h
        r = (0.01 + rng.random() * 0.016) * ppm
        d = np.sqrt(((x - cx) / r) ** 2 + ((y - cy) / (r * 1.6)) ** 2)
        kn = np.maximum(kn, np.exp(-d * d) * 0.9 + 0.3 * np.exp(-((d - 1.5) ** 2) * 4))
    weather = fbm(h, w, 8, 4, rng, 4)  # silvered and darker patches
    split = ss(0.985, 1.0, fbm(h, w, 6, 160, rng, 2) + 0.35 * (fbm(h, w, 40, 6, rng, 1) - 0.5))  # checks along the grain
    # Round 2 (the judge at the close view: bold black grain read as drawn lines): the late wood only
    # ~15% darker than the early, broken up by the fibres so it reads as streaks, not lines; the base
    # less orange (weathered brown-grey); knots and checks softer.
    fib = fbm(h, w, 160, 10, rng, 2)  # long fibrous streaks down the grain
    late = late * (0.45 + 0.55 * ss(0.35, 0.7, fib))
    base = mix(srgb("#76624f"), srgb("#968774"), 0.6 * weather + 0.4 * streak)
    col = mix(base, srgb("#5e4c3c"), 0.42 * late + 0.25 * (fine - 0.5) + 0.2 * (fib - 0.5))
    col = mix(col, srgb("#3a2c22"), 0.6 * kn)
    col = mix(col, srgb("#2e231b"), 0.7 * split)
    hgt = -0.0012 * late - 0.0006 * fine - 0.004 * split + 0.0008 * kn
    rough = 0.82 + 0.1 * weather
    return col, hgt, rough, np.zeros_like(rough)


def cells(h, w, gy, gx, rng, warp):
    """Periodic jittered-grid Voronoi over h x w px (gy x gx cells): F1, F2 (in cell units)
    and each pixel's cell value (0-1). warp: (dy, dx) pixel offsets bending the cells."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    v = (y + warp[0]) * gy / h
    u = (x + warp[1]) * gx / w
    jy, jx, val = rng.random((gy, gx)), rng.random((gy, gx)), rng.random((gy, gx))
    ci, cj = np.floor(v).astype(int), np.floor(u).astype(int)
    f1 = np.full((h, w), 9.0, np.float32)
    f2 = np.full((h, w), 9.0, np.float32)
    idv = np.zeros((h, w), np.float32)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ii, jj = ci + di, cj + dj
            py = ii + 0.1 + 0.8 * jy[ii % gy, jj % gx]
            px = jj + 0.1 + 0.8 * jx[ii % gy, jj % gx]
            d = np.sqrt((v - py) ** 2 + (u - px) ** 2)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            idv = np.where(closer, val[ii % gy, jj % gx], idv)
            f1 = np.minimum(f1, d)
    return f1, f2, idv


def bark(h, w, m, rng):
    """Fissured bark (round 2): long irregular plates split by deep fissures that wander and
    branch (no drawn wavy lines), each plate its own value (15-25% across them), short cross
    cracks in the plates; dark warm grey-brown, about #4e4236 overall (sRGB luma under 0.35:
    a pale grey went pink under the fire and the moon)."""
    ppm = w / m
    warp = ((fbm(h, w, 6, 4, rng, 3) - 0.5) * 0.10 * ppm,
            (fbm(h, w, 8, 4, rng, 3) - 0.5) * 0.05 * ppm + (fbm(h, w, 60, 30, rng, 2) - 0.5) * 0.008 * ppm)
    # plates about 4-5 cm across and 20-30 cm down the trunk (a dead pine's long plates)
    f1, f2, pv = cells(h, w, int(round(m * h / w / 0.17)), int(round(m / 0.055)), rng, warp)
    edge = f2 - f1
    wid = 0.06 + 0.16 * fbm(h, w, 10, 6, rng, 2)  # fissures wide and narrow by turns
    fis = 1 - ss(0.0, 1.0, edge / wid)  # 1 in the crack
    lip = ss(0.0, 1.0, edge / (wid * 2.6))  # 0 at the crack's lip, 1 on the plate's back
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    # short cross cracks on the plates (across the grain), broken
    cx = np.abs(np.sin((y + warp[0] * 0.6) / ppm * 2 * np.pi * 26 + 6 * fbm(h, w, 12, 8, rng, 2)))
    cross = (1 - ss(0.0, 0.12, cx)) * ss(0.55, 0.75, fbm(h, w, 20, 14, rng, 2)) * lip
    mott = fbm(h, w, 24, 16, rng, 3)
    fibre = fbm(h, w, 90, 16, rng, 2)  # fine fibres down the trunk
    col = mix(srgb("#4a3f34"), srgb("#5e5142"), 0.65 * pv + 0.35 * mott)  # plate to plate
    col = col * (0.92 + 0.12 * fibre[..., None])
    col = mix(col, srgb("#6a5d4e"), 0.35 * ss(0.6, 1.0, lip) * ss(0.45, 0.8, mott))  # weathered plate backs
    flake = ss(0.58, 0.72, fbm(h, w, 36, 18, rng, 3)) * lip  # outer scales lifted off: the warmer bark under
    col = mix(col, srgb("#5c4535"), 0.45 * flake)
    rough = fbm(h, w, 140, 70, rng, 2)  # a scaly tooth at one scale
    col = col * (0.94 + 0.1 * rough[..., None])
    col = mix(col, srgb("#3a3026"), 0.35 * (1 - lip) * (1 - fis))  # into the crack
    col = mix(col, srgb("#1f1813"), 0.9 * fis)
    col = mix(col, srgb("#2f261e"), 0.6 * cross)
    hgt = 0.004 * lip - 0.003 * fis + 0.0015 * pv + 0.0012 * mott - 0.0015 * cross - 0.001 * flake + 0.0005 * rough
    return col, hgt, 0.88 + 0.1 * pv, np.zeros((h, w), np.float32)


def endgrain(h, w, m, rng):
    ppm = w / m
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx = cy = w / 2
    dx, dy = (x - cx) / ppm, (y - cy) / ppm
    r = np.sqrt(dx * dx + dy * dy) + 0.004 * (fbm(h, w, 6, 6, rng, 2) - 0.5)
    ang = np.arctan2(dy, dx)
    # (round 2: the rings out of round and uneven, the log's lean and its fast and slow years)
    r = r * (1 + 0.06 * np.cos(ang - 0.7) + 0.03 * np.sin(3 * ang + 1.3))
    rings = ss(0.5, 0.95, np.sin(r * 2 * np.pi * 70 + 9 * r + 2 * fbm(h, w, 4, 4, rng, 2))) * (0.6 + 0.4 * fbm(h, w, 3, 3, rng, 2))
    checks = np.zeros((h, w), np.float32)
    for _ in range(5):
        a0 = rng.random() * 2 * np.pi
        da = np.abs(np.angle(np.exp(1j * (ang - a0))))
        checks = np.maximum(checks, ss(0.02, 0.0, da * r * 8) * ss(0.05, 0.2, r))
    col = mix(srgb("#a88a66"), srgb("#86684a"), 0.5 * rings + 0.3 * ss(0.0, 0.24, r))
    col = mix(col, srgb("#3a2a1e"), 0.9 * checks)
    # Outside r 0.24 m: the bark rim (a log's cap is mapped so its edge lands here).
    rim = ss(0.225, 0.235, r)
    col = mix(col, srgb("#3c2f25"), rim)
    pith = np.exp(-(r / 0.006) ** 2)
    col = mix(col, srgb("#5a4030"), pith)
    hgt = -0.0008 * rings - 0.003 * checks + 0.002 * rim
    return col, hgt, np.full((h, w), 0.86, np.float32), np.zeros((h, w), np.float32)


def iron(h, w, m, rng):
    hammer = fbm(h, w, 24, 24, rng, 3)
    rust = ss(0.58, 0.75, fbm(h, w, 6, 6, rng, 5))
    pits = ss(0.7, 0.85, fbm(h, w, 64, 64, rng, 2))
    col = mix(srgb("#2b2826"), srgb("#3a3532"), hammer)
    col = mix(col, srgb("#6a3a1e"), 0.8 * rust)
    col = mix(col, srgb("#1c1816"), 0.5 * pits)
    hgt = 0.0005 * hammer + 0.0008 * rust - 0.0005 * pits
    rough = 0.5 + 0.35 * rust + 0.1 * hammer
    return col, hgt, rough, 0.75 * (1 - rust)


def weave(h, w, m, rng, threads, slub):
    ppm = w / m
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    ww = (fbm(h, w, 8, 8, rng, 2) - 0.5) * 0.003 * ppm
    a = np.sin((x + ww) / ppm * np.pi * threads)
    b = np.sin((y + ww) / ppm * np.pi * threads)
    # Plain weave: warp over weft where the checkerboard says.
    chk = np.sign(np.sin((x + ww) / ppm * np.pi * threads / 2) * np.sin((y + ww) / ppm * np.pi * threads / 2))
    over = np.where(chk > 0, np.abs(a), np.abs(b))
    s = fbm(h, w, 6, 6 * slub, rng, 3)
    return over, s


def cloth(h, w, m, rng):
    over, s = weave(h, w, m, rng, 520, 4)
    fuzz = fbm(h, w, 96, 96, rng, 2)
    stains = ss(0.62, 0.8, fbm(h, w, 4, 4, rng, 4))
    col = mix(srgb("#d6cfc3"), srgb("#bdb4a6"), 0.6 * s + 0.15 * (1 - over))
    col = mix(col, srgb("#9a8f80"), 0.25 * fuzz + 0.35 * stains)
    hgt = 0.0006 * over + 0.0003 * fuzz
    return col, hgt, np.full((h, w), 0.97, np.float32), np.zeros((h, w), np.float32)


def canvas(h, w, m, rng):
    # Round 2: burlap, not oat cloth: a coarse open weave (about 4 threads a cm), a dull grey-brown
    # (~#9a8466), slubs in the threads and dark gaps between them.
    over, s = weave(h, w, m, rng, 170, 3)
    stains = ss(0.55, 0.8, fbm(h, w, 5, 5, rng, 4))
    col = mix(srgb("#a69a86"), srgb("#867b68"), 0.55 * s + 0.2 * (1 - over))
    col = mix(col, srgb("#4a3f32"), 0.55 * ss(0.35, 0.0, over))  # the gaps between threads
    col = mix(col, srgb("#6a5b46"), 0.4 * stains)
    hgt = 0.0012 * over
    return col, hgt, np.full((h, w), 0.95, np.float32), np.zeros((h, w), np.float32)


def leather(h, w, m, rng):
    grain = fbm(h, w, 80, 80, rng, 2)
    crease = 1 - ss(0.0, 0.03, np.abs(fbm(h, w, 6, 10, rng, 3) - 0.5))
    scuff = ss(0.6, 0.8, fbm(h, w, 8, 8, rng, 4))
    col = mix(srgb("#6a4630"), srgb("#4c3122"), 0.4 * grain + 0.22 * crease)
    col = mix(col, srgb("#8c6a4c"), 0.5 * scuff)
    hgt = 0.0004 * grain - 0.001 * crease
    rough = 0.62 + 0.25 * scuff
    return col, hgt, rough, np.zeros((h, w), np.float32)


def rollend(h, w, m, rng):
    ppm = w / m
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = (x - w / 2) / ppm, (y - h / 2) / ppm
    r = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)
    # An Archimedean spiral of layers 1.4 cm apart: the blanket wound on itself.
    ph = (r / 0.012 - ang / (2 * np.pi) + 0.25 * fbm(h, w, 5, 5, rng, 2)) % 1.0
    gap = 1 - ss(0.0, 0.2, np.minimum(ph, 1 - ph))
    s = fbm(h, w, 8, 8, rng, 3)
    col = mix(srgb("#d6cfc3"), srgb("#a89c8c"), 0.3 * s)
    col = mix(col, srgb("#2a2420"), 0.85 * gap * ss(0.0, 0.01, r))
    hgt = -0.003 * gap
    return col, hgt, np.full((h, w), 0.97, np.float32), np.zeros((h, w), np.float32)


def stone(h, w, m, rng):
    ppm = w / m
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    big = fbm(h, w, 4, 8, rng, 4)
    grit = fbm(h, w, 64, 128, rng, 2)
    cracks = 1 - ss(0.0, 0.012, np.abs(fbm(h, w, 5, 10, rng, 3) - 0.5))
    lichen = ss(0.66, 0.8, fbm(h, w, 6, 12, rng, 4))
    col = mix(srgb("#8a8378"), srgb("#a39b8c"), big)
    col = mix(col, srgb("#6c665e"), 0.35 * grit)
    col = mix(col, srgb("#4a453e"), 0.5 * cracks)
    col = mix(col, srgb("#8e9168"), 0.45 * lichen)
    hgt = 0.004 * big + 0.0008 * grit - 0.004 * cracks
    return col, hgt, 0.88 + 0.08 * grit, np.zeros((h, w), np.float32)


MAKERS = {"wood": wood, "bark": bark, "endgrain": endgrain, "iron": iron, "cloth": cloth, "canvas": canvas,
          "leather": leather, "rollend": rollend, "stone": stone}


def normals(hgt, ppm):
    gy, gx = np.gradient(hgt * ppm)  # dh per pixel in metres -> slope
    n = np.dstack([-gx, gy, np.ones_like(hgt)])  # OpenGL: green up (rows run down)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=2048, help="stored size (painted at 2048)")
    ap.add_argument("--raw", action="store_true", help="skip the painter (to compare)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    alb = np.zeros((N, N, 3), np.float32)
    nrm = np.zeros((N, N, 3), np.float32)
    nrm[..., 2] = 1.0
    nrm = nrm * 0.5 + 0.5
    orm = np.zeros((N, N, 3), np.float32)
    orm[..., 0] = 1
    orm[..., 1] = 0.9
    meta = {"size": N, "regions": {}}
    for i, (name, ((x0, y0, w, h), m, pre, over)) in enumerate(REGIONS.items()):
        rng = np.random.default_rng(100 + i)
        col, hgt, rough, metal = MAKERS[name](h, w, m, rng)
        n = normals(hgt, w / m)
        if not a.raw:
            col = paint_tex.paint(np.clip(col, 0, 1), n, paint_tex.preset(pre, over))
        alb[y0:y0 + h, x0:x0 + w] = col
        nrm[y0:y0 + h, x0:x0 + w] = n
        orm[y0:y0 + h, x0:x0 + w, 1] = np.clip(rough, 0, 1)
        orm[y0:y0 + h, x0:x0 + w, 2] = np.clip(metal, 0, 1)
        # UV with v up (Blender's): u0, v0 (bottom), u1, v1; metres across u and down v
        meta["regions"][name] = {"uv": [x0 / N, 1 - (y0 + h) / N, (x0 + w) / N, 1 - y0 / N], "m": [m, m * h / w]}
        print(f"region {name}: {w}x{h} px, {m} m across, mean albedo {col.reshape(-1, 3).mean(0).round(3)}")

    def save(img, name, q=None):
        im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
        if a.size != N:
            im = im.resize((a.size, a.size), Image.LANCZOS)
        p = OUT / name
        im.save(p, quality=q) if q else im.save(p, optimize=True)
        print(p)

    save(alb, "props_albedo.jpg", 92)
    save(nrm, "props_normal.png")
    save(orm, "props_orm.png")
    (OUT / "props_atlas.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
