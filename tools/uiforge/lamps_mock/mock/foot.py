"""The HUD foot over a graded world, exactly as the game draws it.
alpha = the art layers at their 1080 rects (girl, keeper, keeper_lip, panel; as UI 24's comp.py places them) + discs
for the dynamic parts, dilated 1 px. out = foot + (1 - alpha) (graded - nofoot): exact for alpha-over art and for
additive glows, and = graded where alpha = 0 and the frames agree.
Geometry is hud_a_geo.json (the live HUD A the frames show), not river_geo.json."""
import os, sys, json
from functools import lru_cache
import numpy as np
import cv2
import draw as D

# UI 26: the HUD foot is swappable. LAMPS_HUD_WT = the checkout whose HUD art and hud_a_geo.json to use (e.g. ui-27's);
# LAMPS_FOOT_TAG = the shot prefix in shoot/out (<tag>_<name>_foot.png / _nofoot.png), shot with that same HUD.
WT = os.environ.get('LAMPS_HUD_WT', r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\ui-25')
sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
import dg_keeper_hud as H

UI = os.path.join(WT, 'godot', 'art', 'ui')
GEO = json.load(open(os.path.join(UI, 'dg_keeper', 'hud_a_geo.json'), encoding='utf8'))
P = GEO['panel']
SEATS = [tuple(s) for s in P['seats']]          # (x, y), seat_r 35
SEAT_R = P['seat_r']
COIN = (*P['coin']['center'], P['coin']['arch_r'])
FLASK = tuple(P['flask']['center'])
DASH = tuple(P['dash']['center'])
GLASS = (*GEO['glass']['center'], GEO['glass']['bezel_outer'])
GLOBE = tuple(GEO['girl']['globe'])
KEYTAGS = {k: v for k, v in P['key_tags'].items() if k != 'note'}


def _disc(m, cx, cy, r):
    Y, X = np.mgrid[0:1080, 0:1920].astype(np.float32)
    d = np.hypot(X + 0.5 - cx, Y + 0.5 - cy) - r
    np.maximum(m, np.clip(0.5 - d, 0, 1), out=m)


def _box(m, x0, y0, x1, y1):
    m[int(y0):int(np.ceil(y1)), int(x0):int(np.ceil(x1))] = 1


@lru_cache(None)
def alpha():
    a = np.zeros((1080, 1920), np.float32)
    gx0, gy0, gw, gh = H.girl_screen_rect()
    girl = H.place(H.load_rgba(os.path.join(UI, 'lamp_life/drowned/lamp_cold.png')), gx0, gy0, gw, gh, (1920, 1080))
    a = np.maximum(a, girl[..., 3])
    for f, (x0, y0, w, h) in (('dg_keeper/keeper.png', (1254, 873, 341, 207)), ('dg_keeper/keeper_lip.png', (1254, 873, 341, 207)),
                              ('dg_panel/panel.png', (576, 988, 768, 92))):
        art = H.load_rgba(os.path.join(UI, f))[..., 3]
        hh, ww = art.shape
        a[y0:y0 + h, x0:x0 + w] = np.maximum(a[y0:y0 + h, x0:x0 + w], art.reshape(hh // 2, 2, ww // 2, 2).mean((1, 3)))
    dyn = np.zeros_like(a)
    _disc(dyn, *GLOBE[:2], GLOBE[2] + 1)
    for (x, y) in SEATS:
        _disc(dyn, x, y, SEAT_R + 1)
    _disc(dyn, *COIN)
    _disc(dyn, *GLASS)
    _disc(dyn, FLASK[0], FLASK[1], 27); _disc(dyn, 688, 1014, 10)                 # the draught and its count badge
    _box(dyn, FLASK[0] - 12, FLASK[1] - 34, FLASK[0] + 12, FLASK[1])              # the bottle's neck and cork
    _disc(dyn, DASH[0], DASH[1], 26)
    for x, y, _r in P["rank_chips"]:
        _disc(dyn, x, y, 10)
    for k, (x, y) in KEYTAGS.items():                                            # key caps: 16 px high
        w = 22 if len(k) == 1 else 64
        _box(dyn, x - w / 2, y - 1, x + w / 2, y + 17)
    a = np.maximum(a, dyn)
    a = np.maximum(a, cv2.dilate(a, np.ones((3, 3), np.uint8)))                   # the 1 px dilation
    return np.clip(a, 0, 1)


@lru_cache(None)
def glow_zone():
    """where the foot's additive light may spill past its alpha (the keeper's fire, her globe): the diff is trusted here"""
    z = np.zeros((1080, 1920), np.float32)
    _disc(z, GLASS[0], GLASS[1] - 6, GLASS[2] + 14)
    _disc(z, GLOBE[0], GLOBE[1], GLOBE[2] + 8)
    return z


def composite(graded, foot, nofoot, dim_draught=0.45):
    a = alpha()
    diff = foot - nofoot
    # outside the art, trust the frames' difference only inside the glow zone (night: enemies move between frames)
    keep = np.maximum(a, glow_zone())[..., None]
    A = a[..., None]
    out = graded + keep * (A * (foot - graded) + (1 - A) * diff)    # = A art + (1 - A) graded (+ additive light)
    m = np.zeros((1080, 1920), np.float32)
    _disc(m, FLASK[0], FLASK[1] - 3, 26); _box(m, FLASK[0] - 11, FLASK[1] - 34, FLASK[0] + 11, FLASK[1])
    _disc(m, 688, 1014, 10)
    _disc(m, DASH[0], DASH[1], 25)
    m = D.gauss(m, 0.6)
    out = out * (1 - m[..., None] * (1 - dim_draught))
    return np.clip(out, 0, 1)


def foot_rgb(name):
    """the shot pair for a backdrop name: town_day | ford_night"""
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shoot', 'out', os.environ.get('LAMPS_FOOT_TAG', 'u25') + '_%s_' % name)
    return D.load_rgb(base + 'foot.png'), D.load_rgb(base + 'nofoot.png')


def paint_seat(rgb, idx, glyph='glyph/sword', tint=(0.43, 0.25, 0.19), px=42):
    """repaint a seat's pinned skill art (the inner disc, r 30.5) as another skill: a tinted radial disc and its glyph in
    the seats' cream, with the seats' dark outline; the rank chip stays the shot's own pixels"""
    from PIL import Image
    x, y = SEATS[idx]
    r0 = 30.5
    out = rgb.copy()
    x0, y0 = int(x - 34), int(y - 34)
    ss = 3
    gy, gx = np.mgrid[0:68 * ss, 0:68 * ss].astype(np.float32)
    X, Y = x0 + (gx + 0.5) / ss, y0 + (gy + 0.5) / ss
    d = np.hypot(X - x, Y - y)
    cov = np.clip(r0 - d + 0.5 / ss, 0, 1 / ss) * ss
    t = np.clip(np.hypot(X - (x - 4), Y - (y - 5)) / 33.0, 0, 1)[..., None]
    edge = np.array([0.035, 0.047, 0.055], np.float32)
    col = np.asarray(tint, np.float32) * (1 - t) ** 1.2 + edge * (1 - (1 - t) ** 1.2)
    cov = cov.reshape(68, ss, 68, ss).mean((1, 3))[..., None]
    col = col.reshape(68, ss, 68, ss, 3).mean((1, 3))
    reg = out[y0:y0 + 68, x0:x0 + 68]
    reg[:] = col * cov + reg * (1 - cov)
    a = np.asarray(Image.open(os.path.join(UI, 'icons', glyph + '.png')).convert('RGBA'), np.float32)[..., 3] / 255
    a = np.clip(cv2.resize(a, (px, px), interpolation=cv2.INTER_AREA) * 1.15, 0, 1)
    gx0, gy0 = int(round(x - px / 2)), int(round(y - px / 2))
    o = np.clip(D.gauss(cv2.dilate(a, np.ones((3, 3), np.uint8)), 0.6) * 1.2, 0, 1)[..., None] * 0.7
    reg = out[gy0:gy0 + px, gx0:gx0 + px]
    reg[:] = reg * (1 - o) + np.array([0.12, 0.08, 0.06], np.float32) * o
    A = a[..., None]
    reg[:] = reg * (1 - A) + np.array([0.918, 0.792, 0.608], np.float32) * A
    cx, cy, cr = P['rank_chips'][idx]
    m = np.zeros((1080, 1920), np.float32); _disc(m, cx, cy, cr + 1.5)
    m = m[..., None]
    return out * (1 - m) + rgb * m
