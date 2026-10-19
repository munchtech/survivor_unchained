"""The shared trim strip (docs/handoff/armor.md 1.5, look bible 01 item 5): one procedural atlas every
armor piece's rims are UV-mapped along. No third-party art: every band is drawn here from formulas.

    python tools/armor/trim_strip.py            -> godot/art/armor/trim_strip.png, trim_strip_nor.png, trim_strip.json

1024 x 256, four bands 64 px tall, top to bottom: rolled_edge, rivet_row, rope, filigree. u runs along a rim
(the strip repeats along it every `metres_u`), v across it. trim_strip.png: R height (0 low, 1 high), G cavity
(1 open, darker in the gaps: the dark gap beside raised trim), B relief mask (1 where the band's relief stands),
A 255. trim_strip_nor.png: a tangent-space normal map from the height (OpenGL, +Y up the image, as Godot reads).
"""
import json
import os

import numpy as np
from PIL import Image

W, H, BAND = 1024, 256, 64
METRES_U = 0.128                     # (the strip's width along a rim: 8 px a millimetre)
RELIEF_M = 0.0015                    # (height 1.0 = 1.5 mm: the trim raised 1-2 mm)
BANDS = ["rolled_edge", "rivet_row", "rope", "filigree"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "armor")


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def rolled_edge(u, v):
    """A rolled bead across the band: a half-round section, brushed along its length."""
    s = 2 * v - 1
    h = np.sqrt(np.clip(1 - s * s, 0, 1))
    rng = np.random.default_rng(7)
    streak = np.interp(v, np.linspace(0, 1, 97), rng.normal(0, 1, 97))
    h = h + 0.015 * streak
    cav = 0.55 + 0.45 * smooth((1 - np.abs(s)) / 0.3)
    return h, cav, (np.abs(s) < 0.98).astype(float)


def rivet_row(u, v):
    """Domed rivets every 8 mm, 5.5 mm across, each with its ring of shadow on the plate."""
    pitch = 64
    cu = (np.floor(u / pitch) + 0.5) * pitch
    r = np.hypot(u - cu, (v - 0.5) * BAND) / 22.0
    dome = np.sqrt(np.clip(1 - r * r, 0, 1)) * 0.75
    ring = np.exp(-((r - 1.08) / 0.09) ** 2)
    cav = 1 - 0.6 * ring - 0.25 * smooth((r - 1.0) / 0.05) * (r < 1.3) * (1 - smooth((r - 1.15) / 0.15))
    return dome, np.clip(cav, 0, 1), (r < 1.0).astype(float)


def rope(u, v):
    """A three-strand twisted rope: strands at 40 degrees, each a rounded section with a groove between."""
    k = 3.0 / BAND
    ph = (u * np.tan(np.radians(50)) + v * BAND) * k
    f = ph - np.floor(ph)
    strand = np.sqrt(np.clip(1 - (2 * f - 1) ** 2, 0, 1))
    s = 2 * v - 1
    body = np.sqrt(np.clip(1 - (s / 0.86) ** 2, 0, 1))
    h = strand * body
    cav = (0.35 + 0.65 * smooth(strand / 0.5)) * (0.5 + 0.5 * smooth(body / 0.3))
    return h, cav, (body > 0).astype(float)


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-12), 0, 1)
    return np.hypot(px - ax - t * dx, py - ay - t * dy)


def filigree(u, v):
    """A scrolling vine between two raised fillets: a wave stem, a curl off each crest and trough, all one
    raised 1-1.5 mm wire with a dark gap beside it."""
    y = v * BAND
    period = 256.0
    d = np.full(u.shape, 1e9)
    # (the stem: a sine between the fillets)
    t = np.linspace(0, W, 1025)
    sy = 32 + 11 * np.sin(2 * np.pi * t / period)
    pts = np.stack([t, sy], 1)
    curls = []
    for k in range(int(W / period) * 2):
        cx = k * period / 2 + period / 4
        up = k % 2 == 0
        cy = 32 + (11 if up else -11)
        # (a curl: an Archimedean spiral off the crest, turning back toward the stem)
        a = np.linspace(0, 2.6 * np.pi, 80)
        rr = 17 * (1 - a / (3.2 * np.pi))
        sgn = -1 if up else 1
        x0 = cx + 18
        y0 = cy + sgn * 4
        curls.append(np.stack([x0 + rr * np.cos(a + np.pi), y0 + sgn * rr * np.sin(a + np.pi)], 1))
    for poly in [pts] + curls:
        for (ax, ay), (bx, by) in zip(poly[:-1], poly[1:]):
            lo, hi = min(ax, bx) - 6, max(ax, bx) + 6
            m = (u >= lo) & (u <= hi)
            if m.any():
                d[m] = np.minimum(d[m], _seg_dist(u[m], y[m], ax, ay, bx, by))
    wire = np.sqrt(np.clip(1 - (d / 3.2) ** 2, 0, 1))
    # (the fillets along each side of the band)
    fd = np.minimum(np.abs(y - 4.5), np.abs(y - (BAND - 4.5)))
    fillet = np.sqrt(np.clip(1 - (fd / 3.0) ** 2, 0, 1))
    h = np.maximum(wire, fillet)
    near = np.minimum(d, fd)
    cav = 1 - 0.55 * np.exp(-((near - 4.2) / 1.0) ** 2) * (h < 0.05)
    return h, np.clip(cav, 0, 1), (h > 0.02).astype(float)


def build():
    os.makedirs(OUT, exist_ok=True)
    u, vv = np.meshgrid(np.arange(W, dtype=float) + 0.5, (np.arange(BAND, dtype=float) + 0.5) / BAND)
    hs, cs, ms = [], [], []
    for fn in (rolled_edge, rivet_row, rope, filigree):
        h, c, m = fn(u, vv)
        hs.append(np.clip(h, 0, 1))
        cs.append(c)
        ms.append(m)
    # (image rows top to bottom = band 0 first; v in UV space is 1 at the top row)
    Hh, Cc, Mm = np.vstack(hs), np.vstack(cs), np.vstack(ms)
    rgba = np.stack([Hh, Cc, Mm, np.ones_like(Hh)], 2)
    Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, "trim_strip.png"))
    # (normals from the height, per band so no band's edge leans on its neighbour)
    px_m = METRES_U / W
    nor = []
    for h in hs:
        hp = np.pad(h * RELIEF_M, ((1, 1), (0, 0)), mode="edge")
        dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * RELIEF_M / (2 * px_m)
        dy = (hp[2:] - hp[:-2]) / (2 * px_m)
        # (image row down = -v: the +Y of the map points up the image)
        n = np.stack([-dx, dy, np.ones_like(h)], 2)
        n /= np.linalg.norm(n, axis=2, keepdims=True)
        nor.append(n)
    n = np.vstack(nor)
    Image.fromarray((np.clip(n * 0.5 + 0.5, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(OUT, "trim_strip_nor.png"))
    meta = {"size": [W, H], "metres_u": METRES_U, "relief_m": RELIEF_M,
            "channels": {"png": "R height, G cavity, B relief mask", "nor": "tangent-space normal, OpenGL (+Y up)"},
            "bands": {b: {"v0": round(1 - (i + 1) * BAND / H, 6), "v1": round(1 - i * BAND / H, 6)} for i, b in enumerate(BANDS)},
            "note": "u along the rim in metres / metres_u (repeats); v = band v0 + (across the profile 0..1) * (v1 - v0). "
                    "Made by tools/armor/trim_strip.py from formulas: no third-party art."}
    json.dump(meta, open(os.path.join(OUT, "trim_strip.json"), "w", encoding="utf-8"), indent=1)
    print("TRIM STRIP", W, "x", H, "->", os.path.abspath(OUT))
    return meta


if __name__ == "__main__":
    build()
