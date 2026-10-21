#!/usr/bin/env python3
"""The town's wall trim sheet (E9b1), made here from noise (no kit, no scan, no photo).

    python tools/assets/env_house_atlas.py [--raw]

One sheet for every wall piece env_house.py builds (look bible 08 "The trick" 2: a modular kit on
trim sheets). 512 px per metre; every region tiles across (u) and down (v) within itself, so a
piece's faces are cut where a region repeats (env_house.py does it) and no seam shows. Painted
near-neutral where the game tints it per house (the plaster and the timber: aux R), then put
through paint_tex.paint (painterly realism, as the props atlas).

Regions (image pixels, x right, y down; metres across x down y):
  rubble   0,0       2048x768   4.0 x 1.5   roughly coursed rubble in lime mortar (stone storeys, plinths)
  plaster  0,768     2048x768   4.0 x 1.5   lime plaster: trowel waves, hairline cracks, a few patched spots
  timber   0,1536    2048x128   4.0 x 0.25  an adzed oak beam's face, grain along x, checks
  ashlar   0,1664    1536x192   3.0 x 0.375 tooled dressed stone (quoins, sills, coping, voussoirs; joints are geometry)
  iron     1536,1664 256x192    0.5 x 0.375 forged black iron, rust
  glass    1792,1664 256x192    0.5 x 0.375 old crown glass, dark, uneven
  planks   0,1856    2048x192   4.0 x 0.375 two weathered boards (a door's, a shutter's), grain along x, their seams

Out (godot/art/world/house/): house_albedo.jpg (sRGB), house_normal.png (OpenGL, green up),
house_aux.png (R tint class: 1 plaster, 0.5 timber and planks, 0 the rest; G roughness;
B a grime and streak noise, tiling with its region), house_atlas.json (the regions in UV 0-1
with v up as glTF/Godot read it flipped: u0, v0 top, u1, v1 bottom in image terms; metres).
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
from env_props_atlas import fbm, ss, srgb, mix, normals  # noqa: E402

OUT = ROOT / "godot" / "art" / "world" / "house"
N = 2048
PPM = 512

# name: (x, y, w, h), painter preset, overrides, tint class
REGIONS = {
    "rubble": ((0, 0, 2048, 768), "stone", {"chroma": 0.85, "warm": "1,3", "pull": "0.08"}, 0.0),
    "plaster": ((0, 768, 2048, 768), "plain", {"detail": 0.25, "chroma": 0.9, "warm": "0,1", "stroke": 0.02}, 1.0),
    "timber": ((0, 1536, 2048, 128), "wood", {"chroma": 0.9, "warm": "1,2", "pull": "0.1"}, 0.5),
    "ashlar": ((0, 1664, 1536, 192), "stone", {"chroma": 0.8, "warm": "1,2", "pull": "0.05"}, 0.0),
    "iron": ((1536, 1664, 256, 192), "plain", {"chroma": 0.9, "warm": "1,3", "stroke": 0.02}, 0.0),
    "glass": ((1792, 1664, 256, 192), "plain", {"detail": 0.6, "stroke": 0.01}, 0.0),
    "planks": ((0, 1856, 2048, 192), "wood", {"chroma": 0.9, "warm": "1,2", "pull": "0.1"}, 0.5),
}


def wrapd(d, p):
    """Periodic signed distance along an axis of period p."""
    return (d + p / 2) % p - p / 2


def rubble(h, w, rng):
    """Roughly coursed rubble: angular stones (a stretched Voronoi, about 0.34 x 0.19 m, a few large and small),
    each its own shade (grey, buff, a few rust-brown), flat-faced with chipped arrises, in thin recessed
    lime mortar. Tiles both ways."""
    from env_props_atlas import cells
    warp = ((fbm(h, w, 6, 16, rng, 3) - 0.5) * 0.06 * PPM, (fbm(h, w, 6, 16, rng, 3) - 0.5) * 0.08 * PPM)
    f1, f2, sid = cells(h, w, 8, 12, rng, warp)
    g1, g2, sid2 = cells(h, w, 16, 26, rng, (warp[0] * 0.5, warp[1] * 0.5))
    gap = f2 - f1
    gap2 = g2 - g1
    width = 0.03 + 0.04 * fbm(h, w, 8, 20, rng, 2)
    inside = ss(width, width + 0.05, gap)
    # small packing stones where the big ones meet
    small = (1 - ss(width * 0.4, width + 0.16, gap)) * ss(0.08, 0.16, gap2) * ss(0.45, 0.6, sid2)
    stone = np.clip(inside + small, 0, 1)
    v = np.where(small > inside, sid2, sid)
    chips = fbm(h, w, 24, 64, rng, 3)
    grit = fbm(h, w, 64, 160, rng, 2)
    big = fbm(h, w, 3, 8, rng, 4)
    hgt = 0.018 * ss(0.0, 0.35, gap) * inside + 0.01 * small + stone * (0.005 * (chips - 0.5) + 0.0008 * grit) - 0.008 * (1 - stone)
    grey = srgb("#8b867d")
    buff = srgb("#a0937c")
    rust = srgb("#7f6753")
    dark = srgb("#6a665f")
    col = mix(grey, buff, ss(0.35, 0.75, v))
    col = mix(col, rust, ss(0.84, 0.94, v) * 0.75)
    col = mix(col, dark, ss(0.22, 0.0, v) * 0.9)
    col = col * (0.9 + 0.2 * big[..., None]) * (0.94 + 0.1 * chips[..., None])
    mortar = mix(srgb("#9d968a"), srgb("#827c71"), fbm(h, w, 16, 40, rng, 3))
    col = mix(mortar, col, stone)
    rough = 0.9 - 0.05 * stone * chips
    return col, hgt, rough


def plaster(h, w, rng):
    """Lime plaster: soft trowel waves, a fine grain, hairline cracks, a few darker patched spots."""
    big = fbm(h, w, 3, 8, rng, 5)
    wave = fbm(h, w, 6, 14, rng, 3)
    grit = fbm(h, w, 48, 120, rng, 2)
    crack = 1 - ss(0.0, 0.006, np.abs(fbm(h, w, 4, 10, rng, 4) - 0.5))
    crack *= ss(0.55, 0.7, fbm(h, w, 3, 6, rng, 2))
    patch = ss(0.74, 0.8, fbm(h, w, 5, 12, rng, 4))
    col = mix(srgb("#c9c2b3"), srgb("#bfb7a8"), ss(0.2, 0.8, big))
    col = mix(col, srgb("#b0a897"), 0.18 * ss(0.3, 0.8, wave))
    col = col * (0.985 + 0.03 * grit[..., None])
    col = mix(col, srgb("#a69d8b"), 0.45 * patch)
    col = mix(col, srgb("#6e665a"), 0.6 * crack)
    hgt = 0.003 * wave + 0.0004 * grit - 0.0015 * crack + 0.0012 * patch
    rough = 0.92 - 0.04 * patch
    return col, hgt, rough


def grain(h, w, rng, base0, base1, dark, checks=1.0):
    """Weathered timber, grain along x (tiles both ways)."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    warp = (fbm(h, w, 3, 6, rng, 3) - 0.5) * 0.02 * PPM
    v = (y + warp) / PPM
    band = np.sin(v * 2 * np.pi * (60 + 20 * fbm(h, w, 6, 2, rng, 2)) + 5 * fbm(h, w, 4, 12, rng, 2))
    late = ss(0.6, 0.98, band) * (0.5 + 0.5 * ss(0.3, 0.7, fbm(h, w, 8, 160, rng, 2)))
    fib = fbm(h, w, 64, 8, rng, 2)
    weather = fbm(h, w, 2, 8, rng, 4)
    split = ss(0.985, 1.0, fbm(h, w, 40, 5, rng, 2) + 0.3 * (fbm(h, w, 4, 40, rng, 1) - 0.5)) * checks
    col = mix(base0, base1, weather)
    col = mix(col, dark, 0.45 * late + 0.25 * (fib - 0.5))
    col = mix(col, srgb("#2a211a"), 0.7 * split)
    hgt = -0.0012 * late - 0.0005 * fib - 0.004 * split + 0.002 * (weather - 0.5)
    return col, hgt, 0.84 + 0.08 * weather


def timber(h, w, rng):
    return grain(h, w, rng, srgb("#7a6857"), srgb("#958877"), srgb("#5a4a3c"), 1.2)


def planks(h, w, rng):
    col, hgt, rough = grain(h, w, rng, srgb("#80705e"), srgb("#9b8f7d"), srgb("#5e4e40"), 0.8)
    y = np.mgrid[0:h, 0:w][0].astype(np.float32)
    # two boards: seams at the region's top (its wrap) and middle, a dark gap with rounded arrises
    sd = np.minimum(np.abs(y - 0), np.minimum(np.abs(y - h / 2), np.abs(y - h)))
    seam = ss(5.0, 1.0, sd)
    tone = np.where(y < h / 2, 1.0, 0.93)[..., None]
    col = mix(col * tone, srgb("#241c16"), 0.85 * seam)
    hgt = hgt - 0.004 * ss(9.0, 0.0, sd)
    return col, hgt, rough


def ashlar(h, w, rng):
    big = fbm(h, w, 2, 12, rng, 4)
    tool = fbm(h, w, 24, 10, rng, 2)  # claw-tooling strokes
    grit = fbm(h, w, 24, 96, rng, 2)
    lichen = ss(0.7, 0.82, fbm(h, w, 4, 24, rng, 4))
    col = mix(srgb("#a69d8d"), srgb("#958b7b"), big)
    col = col * (0.97 + 0.05 * tool[..., None] + 0.02 * grit[..., None])
    col = mix(col, srgb("#8f9070"), 0.35 * lichen)
    hgt = 0.002 * big + 0.0008 * tool + 0.0005 * grit
    return col, hgt, 0.86 + 0.06 * grit


def iron(h, w, rng):
    big = fbm(h, w, 3, 3, rng, 4)
    rust = ss(0.55, 0.75, fbm(h, w, 6, 6, rng, 4))
    col = mix(srgb("#2f2d2b"), srgb("#3d3a36"), big)
    col = mix(col, srgb("#5c3b26"), 0.7 * rust)
    hgt = 0.001 * big + 0.001 * rust
    return col, hgt, 0.6 + 0.3 * rust


def glass(h, w, rng):
    big = fbm(h, w, 2, 2, rng, 3)
    ripple = fbm(h, w, 6, 6, rng, 3)
    col = mix(srgb("#1f262a"), srgb("#3a4448"), 0.5 * big + 0.5 * ss(0.5, 0.8, ripple))
    hgt = 0.002 * ripple
    return col, hgt, 0.12 + 0.1 * big


MAKERS = {"rubble": rubble, "plaster": plaster, "timber": timber, "ashlar": ashlar, "iron": iron, "glass": glass, "planks": planks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", action="store_true", help="skip the painter (to compare)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    alb = np.zeros((N, N, 3), np.float32)
    nrm = np.full((N, N, 3), 0.5, np.float32)
    nrm[..., 2] = 1.0
    aux = np.zeros((N, N, 3), np.float32)
    meta = {"size": N, "ppm": PPM, "regions": {}}
    for i, (name, ((x0, y0, w, h), pre, over, tint)) in enumerate(REGIONS.items()):
        rng = np.random.default_rng(900 + i)
        col, hgt, rough = MAKERS[name](h, w, rng)
        n = normals(hgt, PPM)
        if not a.raw:
            col = paint_tex.paint(np.clip(col, 0, 1), n, paint_tex.preset(pre, over))
        alb[y0:y0 + h, x0:x0 + w] = col
        nrm[y0:y0 + h, x0:x0 + w] = n
        aux[y0:y0 + h, x0:x0 + w, 0] = tint
        aux[y0:y0 + h, x0:x0 + w, 1] = np.clip(rough, 0, 1)
        # grime and streak noise: blotches with long vertical runs (rain), tiling in the region
        g = 0.6 * fbm(h, w, max(1, h // 96), max(1, w // 96), rng, 4) + 0.4 * fbm(h, w, max(1, h // 256), max(1, w // 24), rng, 3)
        aux[y0:y0 + h, x0:x0 + w, 2] = np.clip((g - g.min()) / (np.ptp(g) + 1e-6), 0, 1)
        # UV as Godot and glTF read it: u right, v down from the image's top
        meta["regions"][name] = {"uv": [x0 / N, y0 / N, (x0 + w) / N, (y0 + h) / N], "m": [w / PPM, h / PPM]}
        print(f"region {name}: {w}x{h} px, {w / PPM} x {h / PPM} m, mean albedo {col.reshape(-1, 3).mean(0).round(3)}")

    def save(img, name, q=None):
        im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
        p = OUT / name
        im.save(p, quality=q) if q else im.save(p, optimize=True)
        print(p)

    save(alb, "house_albedo.jpg", 92)
    save(nrm, "house_normal.png")
    save(aux, "house_aux.png")
    (OUT / "house_atlas.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
