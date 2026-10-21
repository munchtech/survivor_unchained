#!/usr/bin/env python3
"""The town's roof trim sheet (E9b2), made here from noise (no kit, no scan, no photo).

    python tools/assets/env_roof_atlas.py [--raw]

The second trim sheet beside the walls' (env_house_atlas.py): every roof, ridge, barge board, rafter end
and chimney env_roof.py builds. 512 px per metre; every region tiles across (u) and down (v) within
itself (env_roof.py cuts its faces where a region repeats). The tiles and shingles are painted
near-neutral and value-varied tile to tile; the game tints them per house (aux R: the class; kit.gdshader
OWN_ROOF, godot/data/house_look.json) and varies each tile again by its id (aux B) and its face's hash.

Regions (image pixels, x right, y down; metres across x down y; image up is up the slope):
  pantile   0,0       2048x640  4.0 x 1.25   clay pantiles, 12 across (0.33 m), 4 courses of 0.3125 m (env_roof.py's course)
  shingle   0,640     2048x640  4.0 x 1.25   split oak shingles, 5 courses of 0.25 m, random widths, staggered
  ridge     0,1280    2048x192  4.0 x 0.375  half-round clay ridge caps, 10 across (0.4 m), lime mortar at both edges (v)
  boards    0,1472    2048x128  4.0 x 0.25   weathered timber, grain along x (barge boards, fascias, rafters, ridge boards)
  soffit    0,1600    2048x128  4.0 x 0.25   the eaves' underside boarding, two boards
  brick     0,1728    1024x320  2.0 x 0.625  chimney brick, running bond, 8 courses
  stone     1024,1728 768x320   1.5 x 0.625  chimney rubble, coursed
  endgrain  1792,1728 128x128   0.25 x 0.25  a rafter's sawn end
  iron      1920,1728 128x128   0.25 x 0.25  a finial's forged iron
  lead      1792,1856 128x128   0.25 x 0.25  lead (flashing, a spire's cap)
  pot       1920,1856 128x128   0.25 x 0.25  a chimney pot's clay (untinted)

Out (godot/art/world/house/): roof_albedo.jpg (sRGB), roof_normal.png (OpenGL), roof_aux.png (R class: 1 clay,
0.75 shingle, 0.5 timber that takes the house's timber tint, 0 untinted; G roughness; B each tile's id (32 steps), else
a noise), roof_atlas.json (the regions, as house_atlas.json).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "assets"))
import paint_tex  # noqa: E402
from env_props_atlas import fbm, ss, srgb, mix, normals  # noqa: E402
from env_house_atlas import grain, coursed_cells, iron  # noqa: E402

OUT = ROOT / "godot" / "art" / "world" / "house"
N = 2048
PPM = 512
PANTILE_COURSE = 0.3125
SHINGLE_COURSE = 0.25

# name: (x, y, w, h), painter preset, overrides
REGIONS = {
    "pantile": ((0, 0, 2048, 640), "plain", {"detail": 0.3, "chroma": 0.95, "warm": "1,3", "stroke": 0.02}),
    "shingle": ((0, 640, 2048, 640), "plain", {"detail": 0.35, "chroma": 0.9, "warm": "1,2", "stroke": 0.012}),
    "ridge": ((0, 1280, 2048, 192), "plain", {"detail": 0.3, "chroma": 0.95, "warm": "1,3", "stroke": 0.02}),
    "boards": ((0, 1472, 2048, 128), "wood", {"chroma": 0.9, "warm": "1,2", "pull": "0.1"}),
    "soffit": ((0, 1600, 2048, 128), "wood", {"chroma": 0.9, "warm": "1,2", "pull": "0.1"}),
    "brick": ((0, 1728, 1024, 320), "stone", {"chroma": 0.95, "warm": "1,3", "pull": "0.1", "hue": "2,6"}),
    "stone": ((1024, 1728, 768, 320), "stone", {"chroma": 0.85, "warm": "1,3", "pull": "0.08"}),
    "endgrain": ((1792, 1728, 128, 128), "wood", {"chroma": 0.9, "warm": "1,2"}),
    "iron": ((1920, 1728, 128, 128), "plain", {"chroma": 0.9, "warm": "1,3", "stroke": 0.02}),
    "lead": ((1792, 1856, 128, 128), "plain", {"chroma": 0.8, "stroke": 0.02}),
    "pot": ((1920, 1856, 128, 128), "plain", {"chroma": 0.95, "warm": "1,3", "stroke": 0.02}),
}
LW = np.array([0.2126, 0.7152, 0.0722], np.float32)


def per(ids, vals):
    """Look up a per-cell value array by a per-pixel integer id map."""
    return np.asarray(vals, np.float32)[ids]


def pantile(h, w, rng):
    """Clay pantiles: columns of S-profile tiles (a broad trough, a roll), each course's butt over the next one down
    casting a shadow line; every tile its own value and warmth, a few dark old ones and pale new ones, chipped butts,
    grime in the troughs, a scatter of lichen."""
    rows, cols = round(h / (PANTILE_COURSE * PPM)), 12
    ch, cw = h / rows, w / cols
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    # each row's columns a little off true; each tile's butt a little off its line
    rowoff = rng.normal(0, 3.0, rows)
    r0 = np.floor(y / ch).astype(int) % rows
    xc = x + rowoff[r0]
    c = np.floor(xc / cw).astype(int) % cols
    tile = r0 * cols + c
    nt = rows * cols
    butt = rng.normal(0, 2.5, nt)
    yb = y + per(tile, butt)
    r = np.floor(yb / ch).astype(int) % rows
    tile = r * cols + c
    s = (yb / ch) % 1.0                     # 0 at the course's top (under the butt above), 1 at its own butt
    u = (xc / cw) % 1.0
    k = 0.62
    prof = np.where(u < k, -np.sin(np.pi * u / k), np.sin(np.pi * (u - k) / (1 - k)))
    # the S profile at a real pantile's depth (a 3-4 cm roll over a broad pan), so the normal turns the roll's flanks to and from the sun
    hgt = np.where(u < k, 0.024, 0.034) * prof + 0.014 * s
    hgt -= 0.014 * ss(0.965, 1.0, s)        # the butt's rounded lip
    # chips out of a few butts' corners
    chip = (ss(0.9, 1.0, s) * ss(0.82, 0.95, fbm(h, w, 40, 160, rng, 2)) * per(tile, rng.random(nt) < 0.35)).astype(np.float32)
    hgt -= 0.006 * chip
    # each tile's value and warmth: N(1, .075); 7% old and dark, 4% new and pale
    val = rng.normal(1.0, 0.075, nt)
    old = rng.random(nt)
    val = np.where(old < 0.07, val * 0.78, np.where(old > 0.96, val * 1.12, val))
    warm = rng.random(nt)
    base = mix(srgb("#b9aa9e"), srgb("#c8b098"), per(tile, warm))           # greyer purple-brown .. warmer orange
    big = fbm(h, w, 3, 8, rng, 4)
    grit = fbm(h, w, 60, 200, rng, 2)
    wear = fbm(h, w, 10, 40, rng, 3)
    col = base * (per(tile, val) * (0.95 + 0.1 * big))[..., None]
    col = col * (0.96 + 0.08 * grit[..., None])
    col = mix(col, col * np.array([0.92, 0.9, 0.9], np.float32), ss(0.55, 0.8, wear))  # weathered patches on a tile's face
    trough = ss(0.1, -0.7, prof) * (0.6 + 0.4 * s)
    col = col * (0.8 + 0.3 * ss(-0.5, 0.9, prof))[..., None]                 # the roll's crown lit, its flanks turning away
    col = mix(col, srgb("#3e352e"), 0.5 * trough)                           # grime and shade down the troughs
    col = mix(col, srgb("#2a221d"), 0.78 * (1 - ss(0.06, 0.17, s)))          # the butt above's shadow
    col = mix(col, srgb("#6a5a50"), 0.5 * chip)
    lich = ss(0.8, 0.86, fbm(h, w, 30, 96, rng, 3)) * per(tile, rng.random(nt) < 0.3) * ss(0.2, 0.5, s)
    col = mix(col, srgb("#c4c2ae"), 0.6 * lich)
    hgt += 0.0006 * grit + 0.0008 * lich
    rough = 0.82 + 0.06 * wear - 0.04 * per(tile, old > 0.96)
    tid = per(tile, (rng.permutation(nt) % 32 + 0.5) / 32)
    return col, hgt, rough, tid


def shingle(h, w, rng):
    """Split oak shingles: courses of random widths, staggered course to course, grain and splits down the slope,
    dark gaps between them, butts lifting a little, each shingle its own value and silvering."""
    rows = round(h / (SHINGLE_COURSE * PPM))
    ch = h / rows
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.floor(y / ch).astype(int) % rows
    s = (y / ch) % 1.0
    # each course's shingle edges: random widths summing to the region's width (it tiles)
    edges = []
    for i in range(rows):
        ws = []
        while sum(ws) < w:
            ws.append(rng.uniform(51, 128))      # 10-25 cm
        ws = np.array(ws) * w / sum(ws)
        e = np.concatenate([[0], np.cumsum(ws)]) + rng.uniform(0, w)
        edges.append(e)
    sid = np.zeros((h, w), int)
    u = np.zeros((h, w), np.float32)
    gapd = np.zeros((h, w), np.float32)
    nper = [len(e) - 1 for e in edges]
    base_id = np.concatenate([[0], np.cumsum(nper)])
    for i in range(rows):
        m = r == i
        e = edges[i]
        xs = (x[m] - e[0]) % w + e[0]
        j = np.clip(np.searchsorted(e, xs, side="right") - 1, 0, len(e) - 2)
        a, b = e[j], e[j + 1]
        sid[m] = base_id[i] + j
        u[m] = (xs - a) / (b - a)
        gapd[m] = np.minimum(xs - a, b - xs)
    nt = int(base_id[-1])
    # a shingle split in two here and there: a dark crack down its length
    split_at = rng.uniform(0.25, 0.75, nt)
    has_split = rng.random(nt) < 0.25
    splitd = np.abs(u - per(sid, split_at)) * 60
    split = (per(sid, has_split) * ss(3.0, 0.0, splitd * 3) * ss(0.15, 0.6, s)).astype(np.float32)
    gap = ss(2.6, 0.4, gapd) * (0.55 + 0.45 * ss(0.1, 0.5, s))   # thin dark joints, fainter where the course above laps them
    val = rng.normal(1.0, 0.06, nt)
    silver = rng.random(nt)
    fib = fbm(h, w, 6, 220, rng, 3)          # grain down the slope (fine across x)
    streak = fbm(h, w, 3, 60, rng, 3)
    weather = fbm(h, w, 3, 10, rng, 4)
    base = mix(srgb("#8f877d"), srgb("#a29f99"), per(sid, silver))      # weathered silver-brown oak
    col = base * (per(sid, val) * (0.94 + 0.12 * weather))[..., None]
    col = mix(col, col * 0.8, 0.5 * ss(0.4, 0.8, fib) + 0.2 * streak)
    col = mix(col, col * 1.08, 0.5 * ss(0.85, 1.0, s))                       # sun-bleached butts
    col = mix(col, srgb("#2e2620"), 0.6 * gap + 0.6 * split)
    # under each course's butts: a hard dark line (the butt's shadow, 5 cm), then the lap's shade fading up the face
    col = mix(col, srgb("#1e1813"), 0.88 * (1 - ss(0.13, 0.21, s)))
    col = col * (0.8 + 0.2 * ss(0.2, 0.55, s))[..., None]
    # each shingle a wedge thickening to its butt (1.6 cm), so the slope's normal tilts course by course and the butt's riser catches the sun
    hgt = 0.016 * s + 0.003 * (2 * np.abs(u - 0.5)) ** 2 * s - 0.004 * gap - 0.003 * split - 0.0009 * fib
    hgt -= 0.008 * ss(0.97, 1.0, s)
    rough = 0.86 + 0.06 * weather
    tid = per(sid, (rng.permutation(nt) % 32 + 0.5) / 32)
    return col, hgt, rough, tid


def ridge(h, w, rng):
    """Half-round clay ridge caps (u along the ridge, v round the cap from one bedding edge to the other): each its own
    value, a dark lap where one sits over the next, lime mortar bedding at both edges (untinted)."""
    n = 10
    cl = w / n
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    c = np.floor(x / cl).astype(int) % n
    a = (x / cl) % 1.0
    v = y / h
    val = rng.normal(1.0, 0.08, n)
    warm = rng.random(n)
    base = mix(srgb("#b6a89c"), srgb("#c6ae96"), per(c, warm))
    big = fbm(h, w, 2, 10, rng, 3)
    grit = fbm(h, w, 20, 220, rng, 2)
    col = base * (per(c, val) * (0.95 + 0.1 * big))[..., None] * (0.96 + 0.08 * grit[..., None])
    lap = 1 - ss(0.0, 0.06, a)                                                # the lap under the cap before it
    col = mix(col, srgb("#3a302a"), 0.55 * lap)
    col = col * (0.88 + 0.12 * np.sin(np.pi * v))[..., None]                 # the crown lit, the sides darker
    mort = np.maximum(1 - ss(0.04, 0.09, v), ss(0.91, 0.96, v)) * (0.8 + 0.2 * fbm(h, w, 4, 60, rng, 2))
    col = mix(col, srgb("#a8a294") * (0.9 + 0.1 * grit[..., None]), np.clip(mort, 0, 1))
    cls = np.where(mort > 0.5, 0.0, 1.0)
    hgt = 0.004 * np.sin(np.pi * a) - 0.006 * lap + 0.0006 * grit - 0.002 * mort
    rough = 0.84 + 0.06 * mort
    tid = per(c, (rng.permutation(n) % 32 + 0.5) / 32)
    return col, hgt, rough, tid, cls


def boards(h, w, rng):
    col, hgt, rough = grain(h, w, rng, srgb("#6e5e50"), srgb("#86786a"), srgb("#4e4036"), 1.2)
    return col, hgt, rough


def soffit(h, w, rng):
    col, hgt, rough = grain(h, w, rng, srgb("#6a5a4c"), srgb("#7e7062"), srgb("#4a3e34"), 0.6)
    y = np.mgrid[0:h, 0:w][0].astype(np.float32)
    sd = np.minimum(np.abs(y), np.minimum(np.abs(y - h / 2), np.abs(y - h)))
    col = mix(col, srgb("#211a14"), 0.85 * ss(4.0, 0.5, sd))
    return col, hgt - 0.003 * ss(6.0, 0.0, sd), rough


def brick(h, w, rng):
    """Chimney brick in running bond (0.25 x 0.078 m with the joint), each brick its own red or brown, a few burnt
    dark headers, sooty grime over all (the shader adds the soot by height)."""
    rows, per_row = 8, 8
    bh, bw = h / rows, w / per_row
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.floor(y / bh).astype(int) % rows
    xo = x + (r % 2) * bw / 2
    c = np.floor(xo / bw).astype(int) % per_row
    b = r * per_row + c
    nb = rows * per_row
    jy = np.minimum(y % bh, bh - y % bh)
    jx = np.minimum(xo % bw, bw - xo % bw)
    joint = 1 - ss(2.0, 4.0, np.minimum(jx, jy))
    pick = rng.random(nb)
    reds = [srgb("#94584a"), srgb("#7f4f40"), srgb("#a2684e"), srgb("#5e3c32"), srgb("#9c7a5c")]
    kind = np.select([pick < 0.4, pick < 0.7, pick < 0.85, pick < 0.93], [0, 1, 2, 3], 4)
    pal = np.stack(reds)[kind]
    val = rng.normal(1.0, 0.07, nb)
    big = fbm(h, w, 2, 6, rng, 4)
    grit = fbm(h, w, 30, 100, rng, 2)
    col = pal[b] * (per(b, val) * (0.92 + 0.12 * big) * (0.95 + 0.1 * grit))[..., None]
    col = mix(col, srgb("#8e887c") * (0.9 + 0.15 * grit[..., None]), joint)
    hgt = -0.006 * joint + 0.001 * grit + 0.001 * big
    rough = 0.88 + 0.05 * joint
    return col, hgt, rough


def stone(h, w, rng):
    warp = ((fbm(h, w, 3, 6, rng, 3) - 0.5) * 18, (fbm(h, w, 3, 6, rng, 3) - 0.5) * 18)
    f1, f2, idv = coursed_cells(h, w, 5, 6, rng, warp, aspect=2.0)
    edge = f2 - f1
    joint = 1 - ss(0.03, 0.12, edge)
    big = fbm(h, w, 2, 6, rng, 4)
    grit = fbm(h, w, 24, 80, rng, 2)
    col = mix(srgb("#8a8478"), srgb("#a0947c"), idv) * ((0.92 + 0.12 * big) * (0.95 + 0.1 * grit))[..., None]
    col = mix(col, srgb("#4e4840"), 0.8 * joint)
    hgt = 0.01 * ss(0.0, 0.25, edge) + 0.001 * grit
    return col, hgt, 0.9 - 0.04 * big


def endgrain(h, w, rng):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot(x - w * 0.42, y - h * 0.55) / PPM
    rings = 0.5 + 0.5 * np.sin(d * 2 * np.pi * 90 + 4 * fbm(h, w, 3, 3, rng, 2))
    check = ss(0.985, 1.0, fbm(h, w, 6, 2, rng, 2))
    col = mix(srgb("#7e6c5a"), srgb("#5a4a3c"), 0.5 * rings)
    col = mix(col, srgb("#2a211a"), 0.8 * check)
    return col, -0.001 * rings - 0.003 * check, 0.88 + 0.0 * d


def lead(h, w, rng):
    big = fbm(h, w, 2, 2, rng, 3)
    col = mix(srgb("#5c6264"), srgb("#747a7a"), big)
    return col, 0.001 * big, 0.55 + 0.2 * big


def pot(h, w, rng):
    big = fbm(h, w, 2, 3, rng, 3)
    grit = fbm(h, w, 16, 16, rng, 2)
    col = mix(srgb("#a0624a"), srgb("#b47a5a"), big) * (0.95 + 0.1 * grit[..., None])
    return col, 0.001 * grit, 0.85 + 0.0 * big


MAKERS = {"pantile": pantile, "shingle": shingle, "ridge": ridge, "boards": boards, "soffit": soffit, "brick": brick,
          "stone": stone, "endgrain": endgrain, "iron": iron, "lead": lead, "pot": pot}
CLASS = {"pantile": 1.0, "shingle": 0.75, "ridge": 1.0, "boards": 0.5, "soffit": 0.5, "endgrain": 0.5}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", action="store_true", help="skip the painter (to compare)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    alb = np.zeros((N, N, 3), np.float32)
    nrm = np.full((N, N, 3), 0.5, np.float32)
    nrm[..., 2] = 1.0
    aux = np.zeros((N, N, 3), np.float32)
    meta = {"size": N, "ppm": PPM, "regions": {}, "course": {"pantile": PANTILE_COURSE, "shingle": SHINGLE_COURSE}}
    for i, (name, ((x0, y0, w, h), pre, over)) in enumerate(REGIONS.items()):
        rng = np.random.default_rng(1300 + i)
        out = MAKERS[name](h, w, rng)
        col, hgt, rough = out[:3]
        tid = out[3] if len(out) > 3 else None
        cls = out[4] if len(out) > 4 else np.full((h, w), CLASS.get(name, 0.0), np.float32)
        n = normals(hgt, PPM)
        col = np.clip(col, 0, 1)
        if not a.raw:
            col = paint_tex.paint(col, n, paint_tex.preset(pre, over))
        alb[y0:y0 + h, x0:x0 + w] = col
        nrm[y0:y0 + h, x0:x0 + w] = n
        aux[y0:y0 + h, x0:x0 + w, 0] = cls
        aux[y0:y0 + h, x0:x0 + w, 1] = np.clip(rough, 0, 1)
        if tid is None:
            g = fbm(h, w, max(1, h // 64), max(1, w // 64), rng, 4)
            tid = (g - g.min()) / (np.ptp(g) + 1e-6)
        aux[y0:y0 + h, x0:x0 + w, 2] = tid
        meta["regions"][name] = {"uv": [x0 / N, y0 / N, (x0 + w) / N, (y0 + h) / N], "m": [w / PPM, h / PPM]}
        lum = col @ LW
        print(f"region {name}: {w}x{h} px, {w / PPM} x {h / PPM} m, mean albedo {col.reshape(-1, 3).mean(0).round(3)}, luma std {lum.std():.3f}")

    def save(img, name, q=None):
        im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
        p = OUT / name
        im.save(p, quality=q) if q else im.save(p, optimize=True)
        print(p)

    save(alb, "roof_albedo.jpg", 92)
    save(nrm, "roof_normal.png")
    save(aux, "roof_aux.png")
    (OUT / "roof_atlas.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
