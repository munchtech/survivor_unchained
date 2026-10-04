"""The interface's own marks as value art (icons/glyph/KEY.png): white and
greys on transparent, which the code tints (a quest's gold, a warning's red,
grey when not known). Made from the designer's line glyphs, made bold: closed
shapes filled, inner lines cut in as grooves, then struck like a smith's
punch: a soft bevel lit from the upper left, so a mark at 15 px is a solid
shape with a little metal in it, not a hairline.
"""
from __future__ import annotations

import os

import cv2
import numpy as np

import forge as F
import svgglyph as G

# Marks the code asks for that are not skills (those are painted in colour).
KEYS = ["amulet", "armor", "bow", "campfire", "censer", "cleaver", "cloak", "compass", "dash", "drop", "eye", "helm",
        "hood", "key", "lock", "map", "mask", "next", "quest", "relic", "ring", "scroll", "sigil", "slash", "staff", "sun",
        "sword", "talk", "totem", "wand", "frost", "bolt_bone", "crescent_holy", "firepot", "frost_orb", "venom_smoke",
        "zone", "zone_fire_enemy", "zone_venom"]

# Where the line glyph does not make a good solid (it would read as a letter), a
# shape of our own: 24-unit SVG paths, each filled or cut.
CUSTOM = {
    "helm": [("fill", "M4 21 L4 11 C4 5 8 2.5 12 2.5 C16 2.5 20 5 20 11 L20 21 Z"),
             ("cut", "M6 10 L10.6 10 L10.6 12.6 L6 12.6 Z"), ("cut", "M13.4 10 L18 10 L18 12.6 L13.4 12.6 Z"),
             ("cut", "M7 15 L10.6 15 L10.6 21.5 L7 21.5 Z"), ("cut", "M13.4 15 L17 15 L17 21.5 L13.4 21.5 Z")],
    "hood": [("fill", "M3 21.5 C3 13 6.5 5.5 12 1.8 C17.5 5.5 21 13 21 21.5 Z"),
             ("cut", "M8 21.5 C8 14 9.5 9.5 12 9.5 C14.5 9.5 16 14 16 21.5 Z")],
    "scroll": [("fill", "M7 5 L18 5 L18 19 L7 19 Z"), ("fill", "M5 2.5 L18 2.5 C21 2.5 21 7.5 18 7.5 L5 7.5 C2 7.5 2 2.5 5 2.5 Z"),
               ("fill", "M6 16.5 L19 16.5 C22 16.5 22 21.5 19 21.5 L6 21.5 C3 21.5 3 16.5 6 16.5 Z"),
               ("cut", "M9 10 L16 10 L16 11.2 L9 11.2 Z"), ("cut", "M9 13 L16 13 L16 14.2 L9 14.2 Z")],
    "totem": [("fill", "M8 2 L16 2 L16 22 L8 22 Z"), ("fill", "M2.5 8.5 L8 6.5 L8 10.5 Z"), ("fill", "M21.5 8.5 L16 6.5 L16 10.5 Z"),
              ("cut", "M9.6 4.2 L11.2 4.2 L11.2 5.8 L9.6 5.8 Z"), ("cut", "M12.8 4.2 L14.4 4.2 L14.4 5.8 L12.8 5.8 Z"),
              ("cut", "M10 8 L14 8 L14 9 L10 9 Z"), ("cut", "M8 11.2 L16 11.2 L16 12 L8 12 Z"),
              ("cut", "M9.6 13.6 L11.2 13.6 L11.2 15.2 L9.6 15.2 Z"), ("cut", "M12.8 13.6 L14.4 13.6 L14.4 15.2 L12.8 15.2 Z"),
              ("cut", "M10 17.4 L14 17.4 L14 18.4 L10 18.4 Z")],
}


def custom_mask(parts, S, pad=1.2):
    scale = S / (24 + 2 * pad)
    fill = np.zeros((S, S), np.uint8)
    cut = np.zeros((S, S), np.uint8)
    for mode, d in parts:
        for pts, closed in G.subpaths(d):
            P = np.round((np.asarray(pts) + pad) * scale * 16).astype(np.int32)
            cv2.fillPoly(fill if mode == "fill" else cut, [P], 255, cv2.LINE_AA, shift=4)
    return fill.astype(np.float32) / 255, cut.astype(np.float32) / 255


def mark(key, size=256, ss=2, stroke=2.3):
    S = size * ss
    if key in CUSTOM:
        body, cut = custom_mask(CUSTOM[key], S)
    elif key in G.glyphs():
        body, cut = G.bold(key, S, stroke=stroke)
    else:
        # A key with no line glyph of its own uses its family's (as the code does).
        import re
        fam = {"bolt_bone": "skull", "crescent_holy": "sun", "firepot": "flame", "frost_orb": "frost",
               "venom_smoke": "smoke", "zone": "retaura", "zone_fire_enemy": "flame", "zone_venom": "plague"}[key]
        body, cut = G.bold(fam, S, stroke=stroke)
    m = np.clip(body - cut, 0, 1)
    # Struck: a bevel from the distance to the edge.
    d = cv2.distanceTransform((m > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    h = np.sqrt(np.clip(d / (S * 0.035), 0, 1)) * S * 0.02
    s = F.Surface(S, S)
    s.height = h.astype(np.float32)
    s.albedo[:] = 0.92
    s.metal[:] = 0.0
    s.rough[:] = 0.5
    lin = s.shade(normal_strength=1.0, ao=0.3, shadow=0.0)
    v = F.lin_to_srgb(np.clip(lin.mean(axis=2), 0, 1))
    # Keep it light (the tint must read): shading only between 0.62 and 1.
    v = 0.62 + 0.38 * np.clip((v - v[m > 0.5].min()) / max(1e-3, np.ptp(v[m > 0.5])), 0, 1) if (m > 0.5).any() else v
    img = np.dstack([v, v, v, m])
    return F.to_pil(F.downsample(img, (size, size)))


def build(out_dir, keys=KEYS):
    os.makedirs(out_dir, exist_ok=True)
    made = {}
    for k in keys:
        made[k] = mark(k)
        F.save(made[k], os.path.join(out_dir, k + ".png"))
    return made
