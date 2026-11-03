"""Direction A, Nightfall: light on dark, no frame. Every function here is a skin hook (see ../SKINS.md)."""
import os
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image
import draw as D
import text as T
from draw import hexc, Patch
from view import lamp_d, FLARE_KINDS, FIELD_C

NAME = 'A'
ICONS = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\ui-25\godot\art\ui\icons'

# ---------------------------------------------------------------- palette
INK = hexc('#efe4cc'); INK_BODY = hexc('#d8cfbd'); INK_DIM = hexc('#9b9282'); GOLD = hexc('#e9c27a')
RIM_GOLD = hexc('#cdae72'); RED = hexc('#e0705a'); COBALT_INK = hexc('#8fb0ff'); FIRE_INK = hexc('#ff9a52')
DARK = hexc('#07080b'); EMBER = hexc('#ff9a3c'); FOCUS = hexc('#e8c87a')
GLASS_IN, GLASS_OUT, GLASS_RIM = hexc('#1b1f26'), hexc('#0d1014'), hexc('#9aa4b2')
LIT_STOPS = [(0, hexc('#fff4d6')), (0.6, hexc('#f4c46a')), (1, hexc('#c8822e'))]
LIT_RIM, LIT_HALO = hexc('#ffd98a'), hexc('#ffb04a')
BLUE_STOPS = [(0, hexc('#23459e')), (1, hexc('#0e1c40'))]       # unlit blue near: deep cobalt, no halo
BLUE_LIT = [(0, hexc('#e6f4ff')), (0.55, hexc('#7fb2ff')), (1, hexc('#2a5bd7'))]
COLLET, BLUE_HALO = hexc('#b9c3d6'), hexc('#5d8dff')
FL_RIM, FL_LIT, FL_HALO = hexc('#c9672a'), [(0, hexc('#fff0c0')), (0.6, hexc('#ff9a3a')), (1, hexc('#b8461c'))], hexc('#ff7a2a')
ASLEEP = hexc('#a9b4c2')
ROAD_COLD, ROAD_LIT, FUSE, PREVIEW = hexc('#a7b1c2'), hexc('#f2c06b'), hexc('#ff9a3c'), hexc('#ffc070')
PATH_INK = hexc('#ffd27a')
COBALT_CORE, COBALT_RIM = hexc('#091f52'), hexc('#3b6fd8')


# ================================================================= the world
def grade(rgb, tod):
    """night falls over the live world (by day a dusk)"""
    if tod == 'day':
        sat, mul, tint = 0.40, 0.42, hexc('#14161a')
    else:
        sat, mul, tint = 0.50, 0.62, hexc('#0b0f16')   # r3: x0.38 -> x0.62 (x0.5 measured luma 14; 0.62 -> ~18), then the moon's cool multiply below
    lum = (rgb * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    g = lum + (rgb - lum) * sat
    g = g * mul
    g = g * 0.75 + tint * 0.25
    if tod != 'day':
        g = g * np.array([0.85, 0.93, 1.10], np.float32)
    Y, X = np.mgrid[0:1080, 0:1920].astype(np.float32)
    cx, cy = FIELD_C
    r = np.hypot(X + 0.5 - cx, Y + 0.5 - cy) / np.hypot(960, 540)
    return g * (1 - 0.25 * D.smoothstep(0.55, 1.0, r))[..., None]


def pools(graded, world, pts, stop):
    """each lit lamp gives the world back its own colors around it"""
    sigma = 14.0 if stop == 'valley' else 34.0
    acc = np.zeros(graded.shape[:2], np.float32)
    for (x, y) in pts:
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < 1920 and 0 <= yi < 1080:
            acc[yi, xi] += 1.0
    M = D.gauss(acc, sigma) * (2 * np.pi * sigma * sigma)          # 1.0 at a pool's center: the world at full color
    M = np.clip(M, 0, 1.0)[..., None]
    out = graded * (1 - M) + world * M
    return out + hexc('#ffb04a') * 0.05 * M


# ================================================================= roads
def roads(L, Lglow, segs, stop):
    """segs: dicts a=(x, y), b=(x, y) already trimmed rim to rim; kind cold|lit|fuse|path; phase (px) for dashes"""
    valley = stop == 'valley'
    for s in segs:
        (ax, ay), (bx, by) = s['a'], s['b']
        if np.hypot(bx - ax, by - ay) < 1:
            continue
        k = s['kind']
        w = {'cold': 1.5 if valley else 1.25, 'lit': 1.4 if valley else 2.0, 'fuse': 2.0, 'path': 3.0}[k]
        pad = 4
        P = Patch(min(ax, bx) - pad, min(ay, by) - pad, max(ax, bx) + pad, max(ay, by) + pad)
        d, t, sl = D.segment(P, ax, ay, bx, by)
        dl = d - w / 2
        if k == 'cold':
            P.fill(dl, ROAD_COLD, 0.40 if valley else 0.38 * s.get('fade', 1.0))
            P.stamp(L)
        elif k == 'lit':
            P.fill(dl, ROAD_LIT, 0.95)
            P.stamp(L)
            P.stamp(Lglow)
        else:
            on, period = (4.0, 8.0) if k == 'fuse' else (6.0, 10.0)     # the path: 6 on, 4 off
            u = (sl + s.get('phase', 0.0)) % period
            ddash = np.abs(u - on / 2) - on / 2               # <0 inside a dash, along the road
            dd = np.maximum(dl, ddash)
            col, al = (FUSE, 0.60) if k == 'fuse' else (PATH_INK, 1.0)
            if k == 'path':                                   # the cold road shows faintly between the dashes
                P.fill(d - 0.6, ROAD_COLD, 0.25)
            P.fill(dd, col, al)
            P.stamp(L)
            g = Patch(P.x0, P.y0, P.x1, P.y1); g.a = P.a * 0.6
            g.stamp(Lglow)


def road_glow(rgb, Lglow, stop):
    g = D.gauss(Lglow[..., :3], 1.6 if stop == 'valley' else 2.5) * 0.40 * 1.6
    return D.screen_add(rgb, np.dstack([g, g[..., :1]]))


# ================================================================= glyphs
@lru_cache(None)
def glyph(name, px):
    """a glyph's alpha at px (area-downsampled), as float"""
    a = np.asarray(Image.open(os.path.join(ICONS, name + '.png')).convert('RGBA'), np.float32)[..., 3] / 255
    return cv2.resize(a, (px, px), interpolation=cv2.INTER_AREA)


def stamp_glyph(L, name, cx, cy, px, color, alpha=1.0, gain=1.0):
    a = np.clip(glyph(name, px) * gain, 0, 1) * alpha
    p = np.zeros(a.shape + (4,), np.float32)
    p[..., :3] = a[..., None] * np.asarray(color, np.float32); p[..., 3] = a
    D.stamp(L, int(round(cx - px / 2)), int(round(cy - px / 2)), p)


@lru_cache(None)
def stick_cap(letter, h):
    """a stick-press cap (L3/R3) in the Y/B family: a dark disc, a light-gray rim, the stick's dished top, the letter"""
    r = h / 2 - 0.5
    c = h / 2
    P = Patch(0, 0, h, h)
    d = D.circle(P, c, c, r)
    P.fill(d, hexc('#16161a'), 1.0)
    P.fill(D.ring(d + 0.75, 1.5), hexc('#cfcfcf'), 0.90)
    P.fill(D.ring(D.circle(P, c, c, r - 4), 1.0), hexc('#cfcfcf'), 0.50)
    out = P.down()
    big = np.zeros((h + 48, h + 48, 4), np.float32)
    big[24:24 + h, 24:24 + h] = out
    f = T.font('alegreya-sans-800', max(11, int(round(h * 0.58))))
    T.draw(big, 24 + c + 0.25, 24 + c + f.size * 0.36, letter, f, hexc('#e8e8e8'), 1.0, align='center')
    return big[24:24 + h, 24:24 + h]


@lru_cache(None)
def icon(name, h):
    if name in ('pad_lstick', 'pad_rstick'):
        return stick_cap('L' if name == 'pad_lstick' else 'R', h)
    im = Image.open(os.path.join(ICONS, 'prompt', name + '.png')).convert('RGBA')
    w = max(1, round(im.width * h / im.height))
    a = np.asarray(im, np.float32) / 255
    a = cv2.resize(a, (w, h), interpolation=cv2.INTER_AREA)
    a[..., :3] *= a[..., 3:4]
    return a


def stamp_icon(L, name, x, cy, h=22, alpha=1.0):
    """a pad key cap with its left edge at x, centered on cy; returns its width"""
    p = icon(name, h) * alpha
    D.stamp(L, int(round(x)), int(round(cy - h / 2)), p)
    return p.shape[1]


# ================================================================= lamps
def _shield(P, cx, cy, s):
    """a small heater shield sdf, s = half width"""
    x, y = np.abs(P.X - cx), P.Y - cy
    top = -s * 1.05
    body = np.maximum(x - s, top - y)
    # the lower curve: a circle meeting the point
    R = s * 2.0
    dc = np.hypot(x + (R - s), y - (-s * 0.1)) - R
    lower = np.where(y > -s * 0.1, dc, body)
    return np.maximum(np.maximum(lower, body), y - s * 1.25)


def _crescent(P, x, y, R):
    """a 2 px arc inside the glass's upper left (centered on -135 deg, +-38 deg), round-ended"""
    rr = R * 0.66
    ang = np.arctan2(P.Y - y, P.X - x)
    dang = np.abs(((ang + 0.75 * np.pi) + np.pi) % (2 * np.pi) - np.pi)
    arc = np.abs(np.hypot(P.X - x, P.Y - y) - rr) - 1.0
    return np.maximum(arc, (dang - 0.66) * rr)


def lamp(L, Lhalo, x, y, kind, st, stop, dim=False, focus=False, onpath=False, gate=0, seed=0, breathe=0.85, fade=1.0, near=True, chip=1.0):
    """one lamp at screen (x, y). st: lit|available|unlit|blocked. Halos go to Lhalo (added later)."""
    valley = stop == 'valley'
    D_ = lamp_d(kind, stop) * (1.1 if focus else 1.0)
    R = D_ / 2
    lit = st == 'lit'
    flare = kind in FLARE_KINDS
    blue = kind == 'blue'
    far_blue = blue and not lit and not near            # past 3 steps: the collet stays, the cobalt glow goes
    asleep = lit and dim
    op = (0.5 if dim else 1.0) * fade
    rng = np.random.default_rng(seed)
    flick = 1.0 + (rng.uniform(-0.04, 0.04) if not valley else 0.0)
    pad = R + 8
    P = Patch(x - pad, y - pad, x + pad, y + pad)
    rimw = 1.25 if not valley else 1.0
    rim_a = 0.30 if st == 'blocked' else 0.55

    # ---- the body sdf by kind
    if kind == 'rite':
        body = D.lozenge(P, x, y, R, R * 1.0)
    elif kind == 'attribute':
        body = D.rbox(P, x, y, R, R, R * 0.35)
    elif kind == 'link' and not valley:
        hw, hh = R, R * 14 / 22
        body = D.stadium(P, x, y, hw, hh)
    elif kind == 'ultimate' and not valley:
        body = D.star(P, x, y, R * 0.58, R, 8, -np.pi / 2)
    elif kind == 'ultimateMod' and not valley:
        body = D.teardrop(P, x, y + R * 0.08, R * 2.0, R * 1.25)
    else:
        body = D.circle(P, x, y, R)

    if valley:                                            # dots
        if lit:
            col = BLUE_LIT[1][1] if blue else FL_LIT[1][1] if flare else hexc('#f7cf7f')
            P.fill(body, col, 1.0)
            P.fill(D.circle(P, x, y, R * 0.45), hexc('#fff6e0'), 0.9)
            D.glow_spot(Lhalo, x, y, max(R * 1.4, 2.5), BLUE_HALO if blue else FL_HALO if flare else LIT_HALO, 0.55 * flick)
        else:                                             # unlit: a light dot >= 3 px at 50% (reads on the dark)
            body = D.circle(P, x, y, max(R, 1.5))
            dc = COBALT_RIM if blue else FL_RIM if flare else hexc('#b4bccb')
            P.fill(body, dc, 0.5)
            op = 1.0 if not dim else 0.5
            if st == 'available':
                P.fill(D.ring(body - 0.2, 1.25), EMBER, 0.85 * breathe)
                D.glow_spot(Lhalo, x, y, 3.0, EMBER, 0.35 * breathe)
        if focus:
            P.fill(D.ring(D.circle(P, x, y, R + 4), 1.5), FOCUS, 1.0)
            D.glow_spot(Lhalo, x, y, R + 5, FOCUS, 0.15)
        P.stamp(L, op)
        return

    # ---- the glass
    if kind == 'link':
        ringd = D.ring(body, 2.0)
        if lit:
            P.fill(ringd, LIT_RIM, 1.0)
            P.fill(D.ring(body, 0.8), hexc('#fff4d6'), 0.8)
            D.glow_spot(Lhalo, x, y, R * 0.9, LIT_HALO, 0.45 * flick)
        else:
            P.fill(D.ring(body, 3.2), hexc('#0b0d11'), 0.55)
            P.fill(ringd, GLASS_RIM, 0.75 if st != 'blocked' else 0.40)
        # the chain link: two interlocked ovals' inner edges, 1 px, inside the stadium ring
        ohw, ohh = hw * 0.44, hh * 0.46
        for sx_ in (-1, 1):
            ov = D.stadium(P, x + sx_ * hw * 0.24, y, ohw, ohh)
            P.fill(D.ring(ov, 1.0), hexc('#5a3a12') if lit else GLASS_RIM, 0.75 if lit else (0.55 if st != 'blocked' else 0.32))
    else:
        if lit and not asleep:
            stops = BLUE_LIT if blue else FL_LIT if flare else LIT_STOPS
            P.fill(body, D.radial(P, x, y - R * 0.12, R * 1.05, stops) * flick)
            halo = BLUE_HALO if blue else FL_HALO if flare else LIT_HALO
            D.glow_spot(Lhalo, x, y, 0.9 * R, halo, (0.50 if blue else 0.55) * flick)
            D.glow_spot(Lhalo, x, y, 1.8 * R, halo, 0.10 * flick)
            rc = hexc('#cfe2ff') if blue else hexc('#ffc27a') if flare else LIT_RIM
            P.fill(D.ring(body + rimw / 2, rimw), rc, 0.95)
        else:
            if blue and not far_blue:                     # cobalt glass: a dark core, the light gathering at the rim
                P.fill(body, D.radial(P, x + R * 0.08, y + R * 0.10, R * 1.02,
                                      [(0, COBALT_CORE), (0.55, hexc('#123077')), (0.86, hexc('#2852ad')), (1, COBALT_RIM)]), 0.97)
            else:
                P.fill(body, D.radial(P, x - R * 0.2, y - R * 0.25, R * 1.25, [(0, GLASS_IN), (1, GLASS_OUT)]), 0.94)
            if onpath:                                    # a warm inner glow at 60% (r3: 40% read as nothing)
                gl = np.exp(-((P.X - x) ** 2 + (P.Y - y) ** 2) / (2 * (R * 0.55) ** 2))[..., None] * hexc('#ffb860')
                cov = P.cov(body)[..., None] * 0.60
                P.a[..., :3] = P.a[..., :3] * (1 - cov * 0.0) + gl * cov
            if not asleep and not blue:
                rc = FL_RIM if flare else GLASS_RIM
                ra = (0.70 if flare else rim_a) if st != 'blocked' else 0.30
                if dim:
                    th = np.arctan2(P.Y - y, P.X - x)
                    per = 4.0 / max(R, 1)                    # 2 px on, 2 px off along the rim
                    dots = np.abs(((th / per) % 1.0) - 0.5) * 2 - 0.5
                    P.fill(np.maximum(D.ring(body + rimw / 2, rimw), dots * per * R / 2), hexc('#8c8f95'), 0.9)
                else:
                    P.fill(D.ring(body + rimw / 2, rimw), rc, ra)
            if not blue and not asleep and kind not in ('ultimateMod',):   # the specular dot
                P.fill(D.circle(P, x - 0.35 * R, y - 0.35 * R, 0.18 * R), hexc('#ffffff'), 0.25)
        if blue:                                          # the 4-prong collet
            P.fill(D.ring(D.circle(P, x, y, R + 0.75), 1.5), COLLET, 0.70 if st != 'blocked' else 0.4)
            for k in range(4):
                a = np.pi / 4 + k * np.pi / 2
                ux, uy = np.cos(a), np.sin(a)
                dseg, _, _ = D.segment(P, x + ux * (R + 0.3), y + uy * (R + 0.3), x + ux * (R + 0.35 * R), y + uy * (R + 0.35 * R))
                P.fill(dseg - 1.0, COLLET, 0.70 if st != 'blocked' else 0.4)
            if not lit and not far_blue:                  # one sharp glint (upper left) and a faint return (lower right)
                cres = _crescent(P, x, y, R)                 # r3: the shine is a 2 px crescent at the upper left
                P.fill(cres, hexc('#ffffff'), 0.80, soft=0.3)
                P.fill(cres - 1.2, hexc('#cfe0ff'), 0.14, soft=1.0)
                arc = D.ring(D.circle(P, x, y, R * 0.66), 1.0)
                ang = np.arctan2(P.Y - y, P.X - x)
                arc = np.maximum(arc, (np.abs(ang - np.pi / 4) - 0.42) * R * 0.66)
                P.fill(arc, hexc('#9cc0ff'), 0.30, soft=0.4)
            elif not lit:
                P.fill(D.circle(P, x - 0.32 * R, y - 0.36 * R, 0.16 * R), hexc('#ffffff'), 0.22)
            else:
                P.fill(_crescent(P, x, y, R), hexc('#ffffff'), 0.80, soft=0.3)

    # ---- the kind's marks
    mark_c = hexc('#4a3214') if (lit and not asleep) else GLASS_RIM
    mark_a = 0.85 if lit else 0.65
    if kind == 'notable':
        P.fill(D.ring(D.circle(P, x, y, R * 0.60), 1.0), mark_c, 0.55 if lit else 0.45)
    elif kind == 'entry':
        P.fill(D.ring(D.circle(P, x, y, R - 3.5), 1.0), mark_c if lit else GLASS_RIM, 0.75 if lit else 0.5)
    elif kind == 'start':
        rc = hexc('#ffd98a') if lit else GLASS_RIM
        P.fill(D.ring(body + 1.25, 2.5), rc, 0.95 if lit else 0.6)              # heavy collet
        for k in range(4):
            a = k * np.pi / 2 + np.pi / 4
            ux, uy = np.cos(a), np.sin(a)
            dseg, _, _ = D.segment(P, x + ux * (R + 2.5), y + uy * (R + 2.5), x + ux * (R + 6.5), y + uy * (R + 6.5))
            P.fill(dseg - 0.8, rc, 0.9 if lit else 0.55)
        P.fill(_shield(P, x, y + 0.5, R * 0.36), hexc('#5a3a12') if lit else GLASS_RIM, 0.80)
    elif kind == 'form':
        dch = np.maximum(np.abs(P.Y - y) * 0.9 + (P.X - x) - R * 0.25, -(np.abs(P.Y - y) * 0.9 + (P.X - x) - R * 0.25) - 1.3)
        P.fill(np.maximum(dch, np.abs(P.Y - y) - R * 0.45), mark_c, mark_a)
    elif kind == 'reflex':
        arc = D.ring(D.circle(P, x + R * 0.25, y, R * 0.5), 1.1)
        P.fill(np.maximum(arc, (P.X - (x + R * 0.1)) * 1.0), mark_c, mark_a)

    # ---- the flame / core
    if lit and kind not in ('link',):
        if asleep:
            P.fill(D.teardrop(P, x, y + R * 0.1, R * 0.6, R * 0.34), ASLEEP, 0.9)
        if not asleep and D_ >= 18 and kind in ('notable', 'entry', 'rite', 'flareLamp', 'reflex', 'form'):
            fl = D.teardrop(P, x, y + R * 0.05, R * 0.70, R * 0.36)
            P.fill(fl, hexc('#fffbea'), 0.95, soft=0.25)
        elif not asleep and kind not in ('start', 'hand', 'blue', 'ultimate', 'ultimateMod'):
            P.fill(D.circle(P, x, y, max(R * 0.32, 1.4)), hexc('#fffbea'), 0.95, soft=0.3)
        elif not asleep and kind in ('blue', 'ultimate'):
            P.fill(D.circle(P, x, y, R * 0.22), hexc('#ffffff'), 0.85, soft=0.6)

    # ---- available: the ember rim, breathing
    if st == 'available':
        P.fill(D.ring(body + 0.875, 1.75), EMBER, 0.85 * breathe)
        D.glow_spot(Lhalo, x, y, R + 3.0, EMBER, 0.20 * breathe)

    P.stamp(L, op)
    if kind == 'hand':
        c = hexc('#5a3a12') if lit else GLASS_RIM
        stamp_glyph(L, 'glyph_color/palm', x, y, int(round(D_ * 0.74)), c, (0.9 if lit else 0.7) * op, gain=1.6)
    if st == 'blocked' and gate and stop != 'valley':
        notch(L, x, y, R, gate, fade * chip)       # r3: the chip fades with its lamp (reach and edge), never alone
    if focus:
        focus_ring(L, Lhalo, x, y, R)


def notch(L, x, y, R, gate, a=1.0):
    """the gate numeral in a small dark tab at the lamp's lower right"""
    if a < 0.05:
        return
    cx, cy = x + R * 0.72 + 5, y + R * 0.72 + 4
    P = Patch(cx - 10, cy - 9, cx + 10, cy + 9)
    w = 7.5 if gate >= 10 else 5.5
    tab = D.rbox(P, cx, cy, w, 7, 3.5)
    P.fill(tab, hexc('#0b0c0f'), 0.88)
    P.fill(D.ring(tab, 0.9), hexc('#cdae72'), 0.30)
    P.stamp(L, a)
    T.draw(L, cx + 0.5, cy + 4, str(gate), T.font('alegreya-sans-800', 11), hexc('#cdae72'), a, align='center')


def focus_ring(L, Lhalo, x, y, R):
    P = Patch(x - R - 10, y - R - 10, x + R + 10, y + R + 10)
    P.fill(D.ring(D.circle(P, x, y, R + 5), 1.5), FOCUS, 1.0)
    P.stamp(L)
    D.glow_spot(Lhalo, x, y, R + 6, FOCUS, 0.12)
    G = Patch(x - R - 16, y - R - 16, x + R + 16, y + R + 16)
    G.fill(D.ring(D.circle(G, x, y, R + 5), 1.5), FOCUS, 0.30, soft=3.0)
    G.stamp(Lhalo, 1.0, 'add')


def light(rgb, Lhalo):
    """the halos, added (screen) over what's under them"""
    return D.screen_add(rgb, Lhalo)


# ================================================================= labels
LABEL_INK = hexc('#d8cfbd')


def label_font(stop):
    return T.font('cinzel-600', 16 if stop == 'valley' else 15)


def label_size(s, stop):
    f = label_font(stop)
    return T.width(s, f, 0.16), 11 if stop == 'valley' else 10      # cap height


def label(L, x, y, s, stop):
    """centered at (x, y) (the caps' middle)"""
    f = label_font(stop)
    _, ch = label_size(s, stop)
    if stop == 'valley':                            # r3: valley labels sit on roads: a tight 3 px dark halo at 60% first
        T.draw(L, x, y + ch / 2, s, f, LABEL_INK, 0.0, track=0.16, align='center', halo=(3, 0.6, DARK))
    T.draw(L, x, y + ch / 2, s, f, LABEL_INK, 0.75, track=0.16, align='center', halo=(4, 0.75, DARK))


# ================================================================= panels (smoked glass)
def glass_panel(L, x0, y0, x1, y1, Lbehind=None):
    P = Patch(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    box = D.rbox(P, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, 3)
    P.fill(box, hexc('#0d1015'), 0.86)
    # the 1 px inner top highlight
    top = np.maximum(box + 1.0, np.abs(P.Y - (y0 + 1.5)) - 0.5)
    P.fill(top, hexc('#ffffff'), 0.06)
    P.fill(D.ring(box + 0.5, 1.0), RIM_GOLD, 0.70)
    P.stamp(L)


def rule(L, x0, x1, y, a=0.28):
    P = Patch(x0, y - 1, x1, y + 1)
    d = np.maximum(np.abs(P.Y - (y + 0.5)) - 0.5, np.maximum(x0 - P.X, P.X - x1))
    # fade the ends
    fade = np.clip(np.minimum(P.X - x0, x1 - P.X) / 30, 0, 1)
    c = P.cov(d) * a * fade
    P.a = np.concatenate([RIM_GOLD * c[..., None], c[..., None]], -1)
    P.stamp(L)


def chip(L, xr, y_base, s, color):
    """a kind chip right-aligned at xr: caps in Alegreya Sans 700 12 in a thin rounded outline"""
    f = T.font('alegreya-sans-700', 12)
    w = T.width(s, f, 0.08)
    x0 = xr - w - 14
    P = Patch(x0, y_base - 13, xr, y_base + 4)
    box = D.rbox(P, (x0 + xr) / 2, y_base - 4.5, (xr - x0) / 2, 8, 3)
    P.fill(box, color * 0.25, 0.35)
    P.fill(D.ring(box + 0.5, 1.0), color, 0.55)
    P.stamp(L)
    T.draw(L, x0 + 7, y_base, s, f, color, 0.95, track=0.08)
    return x0


CHIP = {'notable': ('NOTABLE', hexc('#d9c08a')), 'blue': ('BLUE LAMP', COBALT_INK), 'rite': ('RITE', hexc('#d9c08a')),
        'link': ('LINK', hexc('#d9c08a')), 'ultimate': ('FLARE', FIRE_INK), 'ultimateMod': ('FLARE', FIRE_INK),
        'flareLamp': ('FLARE', FIRE_INK), 'turn': ('TURN', GOLD), 'entry': ('ENTRY', hexc('#d9c08a'))}


def card_height(c, w=380):
    return _card(None, 0, 0, c, w)


def card(L, x0, y0, c, w=380):
    return _card(L, x0, y0, c, w)


def _card(L, x0, y0, c, w):
    """c: name, kind, place, line, feeds (list of (glyph, carried)), feeds_text, price, state, prompts [(icon, word)]"""
    pad = 16
    iw = w - 2 * pad
    fn, fp, fl, ff, fpr, fs = (T.font('alegreya-700', 21), T.font('alegreya-sans-500', 13), T.font('alegreya-400', 17),
                               T.font('alegreya-sans-500', 15), T.font('alegreya-400-italic', 16), T.font('alegreya-sans-500', 15))
    lines = T.wrap(c['line'], fl, iw) if c.get('line') else []
    plines = T.wrap(c['price'], fpr, iw) if c.get('price') else []
    y = y0 + pad
    ops = []
    y += 19; ops.append(('name', y))
    y += 20; ops.append(('place', y))
    y += 11; ops.append(('rule', y))
    y += 8
    for ln in lines:
        y += 22; ops.append(('line', y, ln))
    if c.get('feeds_text'):
        y += 27; ops.append(('feeds', y))
    for ln in plines:
        y += 21; ops.append(('price', y, ln))
    y += 13; ops.append(('rule', y))
    y += 22; ops.append(('state', y))
    if c.get('prompts'):
        y += 27; ops.append(('prompts', y))
    y += pad - 2
    h = y - y0
    if L is None:
        return h
    glass_panel(L, x0, y0, x0 + w, y0 + h)
    X0, X1 = x0 + pad, x0 + w - pad
    for op in ops:
        k, yy = op[0], op[1]
        if k == 'name':
            xc = X1
            if c.get('kind') in CHIP:
                s, col = CHIP[c['kind']]
                xc = chip(L, X1, yy - 2, s, col) - 8
            T.draw(L, X0, yy, T.ellipsize(c['name'], fn, xc - X0), fn, INK, 1.0)
        elif k == 'place':
            T.draw(L, X0, yy, c['place'], fp, INK_DIM, 1.0, track=0.08)
        elif k == 'rule':
            rule(L, X0, X1, yy)
        elif k == 'line':
            T.draw(L, X0, yy, op[2], fl, INK_BODY, 1.0)
        elif k == 'feeds':
            x = X0
            for g, carried in c.get('feeds', []):
                stamp_glyph(L, g, x + 8, yy - 5, 16, GOLD if carried else INK_DIM, 1.0, gain=1.2)
                x += 21
            T.draw(L, x + 4, yy, c['feeds_text'], ff, INK_BODY, 0.95)
        elif k == 'price':
            T.draw(L, X0, yy, op[2], fpr, RED, 1.0)
        elif k == 'state':
            T.draw(L, X0, yy, c['state'], fs, c.get('state_color', GOLD), 1.0)
        elif k == 'prompts':
            x = X0
            for i, (ic, word) in enumerate(c['prompts']):
                if i:
                    T.draw(L, x + 6, yy, '\u00b7', ff, INK_DIM, 1.0); x += 20
                x += stamp_icon(L, ic, x, yy - 5, 20) + 6
                x += T.draw(L, x, yy, word, ff, INK_BODY, 0.95)
    return h


# ================================================================= header
def header(L, Lhalo, h):
    """h: count, sub, post (or None), night (or None), coins (active index), layout_name, keys [(icon(s), word)]"""
    halo = (6, 0.70, DARK)
    # center: the count
    fnum, fw = T.font('cinzel-700', 30), T.font('cinzel-600', 16)
    num, words = str(h['count']), 'LAMPS TO LIGHT'
    wn, ww = T.width(num, fnum), T.width(words, fw, 0.16)
    gap = 10
    x0 = 960 - (wn + gap + ww) / 2
    T.draw(L, x0, 50, num, fnum, GOLD, 1.0, halo=halo)
    T.draw(L, x0 + wn + gap, 49, words, fw, GOLD, 0.95, track=0.16, halo=halo)
    T.draw(L, 960, 69, h['sub'], T.font('alegreya-sans-400', 14), INK_DIM, 1.0, align='center', halo=halo)
    if h.get('post'):
        T.draw(L, 960, 88, h['post'], T.font('alegreya-400-italic', 15), hexc('#e8b36a'), 0.95, align='center', halo=halo)
    if h.get('night'):
        T.draw(L, 960, 88, h['night'], T.font('alegreya-400-italic', 15), INK_DIM, 0.85, align='center', halo=halo)
    # left: the layouts
    cy = 46
    for i, n in enumerate(['I', 'II', 'III']):
        cx = 44 + i * 40
        coin(L, Lhalo, cx, cy, n, i == h['coins'])
    T.draw(L, 44 + 2 * 40 + 28, 52, h['layout_name'], T.font('alegreya-700', 17), INK, 0.95, halo=halo)
    # right: the keys
    f = T.font('alegreya-sans-500', 15)
    x = 1896
    for icons, word in reversed(h['keys']):
        x -= T.width(word, f)
        T.draw(L, x, 51, word, f, INK_BODY, 0.95, halo=halo)
        x -= 6
        for ic in reversed(icons if isinstance(icons, (list, tuple)) else [icons]):
            w = icon(ic, 24).shape[1]
            x -= w
            stamp_icon(L, ic, x, 46, 24)
            x -= 2
        x -= 22


def coin(L, Lhalo, cx, cy, numeral, active):
    R = 16
    P = Patch(cx - R - 3, cy - R - 3, cx + R + 3, cy + R + 3)
    d = D.circle(P, cx, cy, R)
    if active:
        P.fill(d, D.radial(P, cx - 4, cy - 5, R * 1.3, [(0, hexc('#5b4526')), (1, hexc('#22180c'))]))
        P.fill(D.ring(d + 0.9, 1.8), hexc('#e8c27a'), 1.0)
        P.fill(D.ring(D.circle(P, cx, cy, R - 3.2), 0.8), hexc('#a8823e'), 0.6)
    else:
        P.fill(d, D.radial(P, cx - 4, cy - 5, R * 1.3, [(0, hexc('#2d2418')), (1, hexc('#14100a'))]), 0.92)
        P.fill(D.ring(d + 0.6, 1.2), hexc('#6b5532'), 0.85)
    P.stamp(L)
    if active:
        D.glow_spot(Lhalo, cx, cy, R * 0.9, hexc('#ffb04a'), 0.16)
    T.draw(L, cx + 0.5, cy + 5, numeral, T.font('cinzel-700', 14), hexc('#ffe2a6') if active else hexc('#7d6a4c'), 1.0, align='center')


# ================================================================= prompts (lower right)
def prompts(L, rows, right=1900, y0=992, step=30):
    """rows: [[(icons, word), ...], ...], right-aligned"""
    f = T.font('alegreya-sans-500', 15)
    halo = (5, 0.65, DARK)
    for r, items in enumerate(rows):
        y = y0 + r * step
        x = right
        for j, (icons, word) in enumerate(reversed(items)):
            x -= T.width(word, f)
            T.draw(L, x, y + 5, word, f, INK_BODY, 0.95, halo=halo)
            x -= 5
            for ic in reversed(icons):
                w = icon(ic, 22).shape[1]
                x -= w
                stamp_icon(L, ic, x, y, 22)
                x -= 1
            x -= 18


# ================================================================= the wick panel
def _cubic(p0, p1, p2, p3, n=60):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, np.float32) for p in (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def _poly_dist(P, pts):
    """distance to a polyline, and the index of the nearest segment"""
    dmin = np.full(P.X.shape, 1e9, np.float32)
    idx = np.zeros(P.X.shape, np.int32)
    for i in range(len(pts) - 1):
        ds, t, _ = D.segment(P, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        m = ds < dmin
        dmin = np.where(m, ds, dmin); idx = np.where(m, i, idx)
    return dmin, idx


STRAND_GOLD, STRAND_PLAN, STRAND_SILVER = hexc('#f2c06b'), hexc('#e2b066'), hexc('#a7b1c2')


def braid(L, Lhalo, kx, ky, length, rows_y, x_end, kinds):
    """the three-ply braid: a plait out of the knot for `length` px, seen from above as a herringbone of strand pieces
    (each outer strand crosses OVER the middle: a piece runs from the rim to past the axis, its head over the last
    piece's tail, its tail tucked under the next), then the three strands part into the rows (cubics to (x_end, ry)).
    kinds[r]: 'lit' | 'planned' | 'cold' for the strand that feeds row r."""
    col_of = {'lit': STRAND_GOLD, 'planned': STRAND_PLAN, 'cold': STRAND_SILVER}
    x0b, x1b = kx + 1.0, kx + length
    A_, step, plen, sw = 3.9, 3.6, 8.0, 3.0        # half height, piece pitch, piece run, strand width (px)
    P = Patch(kx - 6, min(rows_y) - 8, x_end + 4, max(rows_y) + 8)
    # the parting: three strands leave the plait's end (top, middle, bottom) for the rows
    exits = [ky - 2.6, ky, ky + 2.6]
    for r in range(3):
        bez = _cubic((x1b - 2, exits[r]), (x1b + (x_end - x1b) * 0.45, exits[r]),
                     (x_end - (x_end - x1b) * 0.55, rows_y[r]), (x_end, rows_y[r]), 48)
        d, _ = _poly_dist(P, bez)
        P.fill(d - 1.0, col_of[kinds[r]], 0.95 if kinds[r] != 'cold' else 0.75)
    # the plait: pieces alternate from the top rim and the bottom rim, each over the one before
    n = int((x1b - plen - x0b) / step) + 1
    for k in range(n):
        x = x0b + k * step
        up = k % 2 == 0
        ya, yb = (ky - A_, ky + 1.4) if up else (ky + A_, ky - 1.4)
        kind = kinds[[0, 2, 1][k % 3]]
        ds, t, _ = D.segment(P, x, ya, x + plen, yb)
        P.fill(ds - sw / 2 - 0.8, DARK, 0.9)                                # the seam: it sits over the last piece
        shade = (0.55 + 0.45 * np.sin(np.pi * np.clip(t * 0.9 + 0.1, 0, 1)))[..., None]   # tucked ends darker
        rgb = np.clip(col_of[kind] * shade + np.clip(0.9 - ds, 0, 1)[..., None] * 0.18, 0, 1)
        c = P.cov(ds - sw / 2) * (0.97 if kind != 'cold' else 0.8)
        P.a = np.concatenate([rgb * c[..., None], c[..., None]], -1) + P.a * (1 - c[..., None])
    P.fill(D.circle(P, kx, ky, 3.4), LIT_RIM, 1.0)
    P.fill(D.ring(D.circle(P, kx, ky, 3.4), 0.8), hexc('#7a5a26'), 0.6)
    P.stamp(L); P.stamp(Lhalo, 0.22, 'add')


def wick(L, Lhalo, w):
    """w: rect (x0, y0, x1, y1), glyph, name, rank, counts, strands [dict(kind, lamps [state, order], turn
    (name, line, state, order, crossed))], sum; optional: boxless (no glass, no inner rule), lay (layout offsets).
    Returns {'turn0': (x, y, r), ...} lamp positions for the card."""
    x0, y0, x1, y1 = w['rect']
    boxless = w.get('boxless', False)
    lay = dict(kx=140, braid=36, lx0=221, pitch=50, tx=389, row0=50, pitch_y=58, text_gap=22, right=10, sum_cx=None,
               pad=18, sum_dy=12)
    lay.update(w.get('lay', {}))
    if w.get('smoke'):                              # boxless smoke (r3): 88% fading to 0 over 24 px at the edges, no rim
        P = Patch(x0, y0, x1, y1)
        e = np.minimum(np.minimum(P.X - x0, x1 - P.X), np.minimum(P.Y - y0, y1 - P.Y))
        c = (D.smoothstep(0, 24, e) * w['smoke'])[..., None]
        P.a = np.concatenate([hexc('#0d1015') * c, c], -1)
        P.stamp(L)
    elif not boxless:
        glass_panel(L, x0, y0, x1, y1)
    # left block
    ax, ay = x0 + 46, y0 + 50
    P = Patch(ax - 31, ay - 31, ax + 31, ay + 31)
    d = D.circle(P, ax, ay, 28)
    P.fill(d, D.radial(P, ax - 6, ay - 8, 34, [(0, hexc('#1d2026')), (1, hexc('#08090c'))]))
    P.fill(D.ring(d + 0.75, 1.5), RIM_GOLD, 0.85)
    P.fill(D.ring(D.circle(P, ax, ay, 25.5), 0.8), hexc('#6b5532'), 0.6)
    P.stamp(L)
    stamp_glyph(L, w['glyph'], ax, ay, 40, hexc('#d6c4a0'), 0.95, gain=1.1)
    pd = lay['pad']
    T.draw(L, x0 + pd, y0 + 118, w['name'], T.font('cinzel-700', 22), INK, 1.0, track=0.06)
    T.draw(L, x0 + pd, y0 + 140, w['rank'], T.font('alegreya-sans-700', 13), GOLD, 1.0, track=0.12)
    T.draw(L, x0 + pd, y0 + 160, w['counts'], T.font('alegreya-sans-400', 14), INK_DIM, 1.0)
    rows_y = [y0 + lay['row0'] + i * lay['pitch_y'] for i in range(3)]
    kx, ky = x0 + lay['kx'], rows_y[1]
    lx = [x0 + lay['lx0'] + i * lay['pitch'] for i in range(3)]
    tx = x0 + lay['tx']
    pos = {}
    kinds = []
    for r in range(3):
        s0 = w['strands'][r]['lamps'][0][0]
        kinds.append('lit' if s0 == 'lit' else 'planned' if s0 == 'planned' else 'cold')
    braid(L, Lhalo, kx, ky, lay['braid'], rows_y, lx[0] - 13, kinds)
    pos['knot'] = (kx, ky)
    fl = T.font('alegreya-400', 14)
    fs = T.font('alegreya-sans-400', 13)
    txt_x = tx + lay['text_gap']
    txt_w = x1 - lay['right'] - txt_x
    for r, ry in enumerate(rows_y):
        st = w['strands'][r]
        T.draw(L, lx[0] + lay.get('kind_dx', -14), ry - 19, st['kind'], T.font('alegreya-sans-700', 13), INK_DIM, 0.95, track=0.08)
        xs = lx + [tx]
        states = [s for s, _ in st['lamps']] + [st['turn']['state']]
        orders = [o for _, o in st['lamps']] + [st['turn']['order']]
        segs = []
        for i in range(3):
            a, b = xs[i], xs[i + 1]
            ra, rb = 11, (17 if i == 2 else 11)
            k = 'lit' if states[i] == 'lit' and states[i + 1] == 'lit' else \
                'path' if states[i] in ('lit', 'planned') and states[i + 1] == 'planned' else 'cold'
            segs.append(dict(a=(a + ra + 2, ry), b=(b - rb - 2, ry), kind=k, phase=0.0))
        Lg = D.layer()
        roads(L, Lg, segs, 'road')
        Lhalo += Lg * 0.6
        for i in range(4):
            s, o = states[i], orders[i]
            turn = i == 3
            x = xs[i]
            if turn:
                wick_turn(L, Lhalo, x, ry, s, st['turn'].get('crossed', False))
                pos['turn%d' % r] = (x, ry, 17)
            else:
                wick_lamp(L, Lhalo, x, ry, s)
                pos['lamp%d_%d' % (r, i)] = (x, ry, 11)
            if o and turn:                          # r3: the Turn's plan number at its upper left (-16, -16)
                T.draw(L, x - 16, ry - 16 + 4.5, str(o), T.font('alegreya-sans-800', 12), GOLD, 1.0, align='center',
                       halo=(3, 1.0, DARK))
            elif o:
                rr = 11
                T.draw(L, x + rr * 0.62 + 4, ry - rr * 0.62 - 1, str(o), T.font('alegreya-sans-800', 12), GOLD, 1.0,
                       halo=(3, 0.8, DARK))
        tn = st['turn']
        crossed = tn.get('crossed')
        if tn.get('card_state'):                    # r3: the focused Turn's one home: name, line (<= 2), the card's state
            lines = T.wrap(tn['line'], fl, txt_w)[:2]
            T.draw(L, txt_x, ry - 16, tn['name'], T.font('alegreya-700', 18), INK, 1.0)
            for j, ln in enumerate(lines):
                T.draw(L, txt_x, ry + 1 + j * 16, ln, fl, INK_BODY, 0.92)
            sy = ry + 1 + (len(lines) - 1) * 16 + 17
            cs = tn['card_state']
            parts = cs.split(' · ')
            if T.width(cs, fs) > txt_w and len(parts) > 1:      # break at a separator, the balanced one that fits
                cuts = [(' · '.join(parts[:k]), ' · '.join(parts[k:])) for k in range(1, len(parts))]
                cuts = [c for c in cuts if T.width(c[0], fs) <= txt_w and T.width(c[1], fs) <= txt_w] or [None]
                sl = list(min(cuts, key=lambda c: abs(T.width(c[0], fs) - T.width(c[1], fs)))) if cuts[0] else                     T.wrap(cs, fs, txt_w)
            else:
                sl = T.wrap(cs, fs, txt_w)
            for j, ln in enumerate(sl[:2]):
                T.draw(L, txt_x, sy + j * 15, ln, fs, FOCUS, 1.0)
        else:
            T.draw(L, txt_x, ry - 2, tn['name'], T.font('alegreya-700', 18), INK if not crossed else INK_DIM, 1.0)
            for j, ln in enumerate(T.wrap(tn['line'], fl, txt_w)[:2]):
                T.draw(L, txt_x, ry + 16 + j * 16, ln, fl, INK_BODY if not crossed else INK_DIM, 0.9)
    if not boxless and not w.get('smoke'):
        rule(L, x0 + 16, x1 - 16, y1 - 32, 0.22)
    scx = (x0 + x1) / 2 if lay['sum_cx'] is None else x0 + lay['sum_cx']
    T.draw(L, scx, y1 - lay['sum_dy'], w['sum'], T.font('alegreya-sans-500', 14), INK_BODY, 0.95, align='center')
    return pos


def wick_lamp(L, Lhalo, x, y, s):
    """22 px: lit burns, planned = cold glass + the ember rim, else cold"""
    lamp(L, Lhalo, x, y, 'wick', 'lit' if s == 'lit' else 'available' if s == 'planned' else 'unlit', 'road')


def wick_turn(L, Lhalo, x, y, s, crossed):
    R = 17
    st = 'lit' if s == 'lit' else 'available' if s == 'planned' else 'unlit'
    lamp(L, Lhalo, x, y, 'turn', st, 'road', dim=crossed)
    # the flame crown: three small tongues over the top
    P = Patch(x - R, y - R - 12, x + R, y - R + 6)
    col = hexc('#ffd98a') if st == 'lit' else hexc('#8a8f98')
    al = 0.95 if st == 'lit' else 0.55 * (0.5 if crossed else 1)
    for dx, h in ((-6.5, 7.0), (0, 10.0), (6.5, 7.0)):
        P.fill(D.teardrop(P, x + dx, y - R - h / 2 + 3, h, 4.2), col, al)
    P.stamp(L)
    if st == 'lit':
        D.glow_spot(Lhalo, x, y - R - 3, 6, LIT_HALO, 0.35)
    if crossed:                                    # a thin dark bar
        P = Patch(x - R - 6, y - R - 6, x + R + 6, y + R + 6)
        ds, _, _ = D.segment(P, x - R - 2, y + R + 2, x + R + 2, y - R - 2)
        P.fill(ds - 1.6, hexc('#050607'), 0.9)
        P.fill(np.abs(ds - 2.1) - 0.4, hexc('#9aa4b2'), 0.25)
        P.stamp(L)


def seat_ring(L, Lhalo, seat, panel_bottom):
    """the chosen seat's gold ring and the wick stem rising to the panel"""
    x, y, r = seat
    P = Patch(x - r - 8, panel_bottom - 2, x + r + 8, y + r + 8)
    P.fill(D.ring(D.circle(P, x, y, r + 1.5), 2.0), FOCUS, 1.0)
    ds, _, _ = D.segment(P, x, panel_bottom, x, y - r - 2.5)
    P.fill(ds - 1.0, FOCUS, 1.0)
    P.stamp(L)
    G = Patch(P.x0 - 8, P.y0 - 8, P.x1 + 8, P.y1 + 8)
    G.fill(np.minimum(D.ring(D.circle(G, x, y, r + 1.5), 2.0), D.segment(G, x, panel_bottom, x, y - r - 2.5)[0] - 1.0),
           LIT_HALO, 0.55, soft=5.0)
    G.stamp(Lhalo, 1.0, 'add')
