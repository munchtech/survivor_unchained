"""Direction C, The Day's Book: the board in the book's right-hand panel. A's lamp, road, label, card and wick language
(imported from skins/a.py) on the panel's own dark ground; no world grade, no pools (the panel is the ground).
Overrides: grade, pools, header (laid out in the panel's content rect), the book's key caps, the wick tabs."""
import os
import numpy as np
import cv2
from skins.a import *                      # noqa: F401,F403  A's light language
import skins.a as A
import draw as D
import text as T
from draw import hexc, Patch

NAME = 'C'
CAP_FILL = hexc('#0c0b0a'); CAP_INK = hexc('#f3d9a0'); BOOK_WORD = hexc('#8c867c')


def grade(rgb, tod):
    return rgb


def pools(graded, world, pts, stop):
    return graded


# ================================================================= the book's key caps
def cap_width(text, h=28):
    f = T.font('alegreya-sans-800', 15 if h >= 26 else 13)
    return int(round(max(T.width(text, f) + (14 if h >= 26 else 11), h * 0.82)))


def cap(L, text, x, cy, h=28):
    """the book's key cap (as its prompt row draws it): a near-black plate, square-cornered, the key in warm cream"""
    w = cap_width(text, h)
    y0 = int(round(cy - h / 2))
    P = Patch(x, y0, x + w, y0 + h)
    P.fill(D.rbox(P, x + w / 2, y0 + h / 2, w / 2, h / 2, 1.0), CAP_FILL, 0.78)
    P.stamp(L)
    f = T.font('alegreya-sans-800', 15 if h >= 26 else 13)
    T.draw(L, x + w / 2, y0 + h / 2 + (5 if h >= 26 else 4.5), text, f, CAP_INK, 1.0, align='center')
    return w


_stamp_icon_a = A.stamp_icon


def stamp_icon(L, name, x, cy, h=22, alpha=1.0):
    """'key:<text>' draws the book's cap (the card's prompts use the device in hand: keyboard and mouse here)"""
    if name.startswith('key:'):
        return cap(L, name[4:], int(round(x)), cy, max(h, 20))
    return _stamp_icon_a(L, name, x, cy, h, alpha)


A.stamp_icon = stamp_icon                 # A's card and wick draw their prompts through this


# ================================================================= header (the content rect's top row)
def header(L, Lhalo, h, rect):
    """h: count, sub, post, night, coins, layout_name, keys [(cap text, word)]; rect = the content rect"""
    x0, y0, x1, _ = rect
    cx = (x0 + x1) / 2
    fnum, fw = T.font('cinzel-700', 30), T.font('cinzel-600', 16)
    num, words = str(h['count']), 'LAMPS TO LIGHT'
    wn, ww = T.width(num, fnum), T.width(words, fw, 0.16)
    gap = 10
    xs = cx - (wn + gap + ww) / 2
    yb = y0 + 28
    T.draw(L, xs, yb, num, fnum, GOLD, 1.0)
    T.draw(L, xs + wn + gap, yb - 1, words, fw, GOLD, 0.95, track=0.16)
    T.draw(L, cx, yb + 19, h['sub'], T.font('alegreya-sans-400', 14), INK_DIM, 1.0, align='center')
    if h.get('post'):
        T.draw(L, cx, yb + 38, h['post'], T.font('alegreya-400-italic', 15), hexc('#e8b36a'), 0.95, align='center')
    if h.get('night'):
        T.draw(L, cx, yb + 38, h['night'], T.font('alegreya-400-italic', 15), INK_DIM, 0.85, align='center')
    # left: the layouts
    ccy = yb - 9
    for i, n in enumerate(['I', 'II', 'III']):
        coin(L, Lhalo, x0 + 16 + i * 40, ccy, n, i == h['coins'])
    T.draw(L, x0 + 16 + 2 * 40 + 28, ccy + 6, h['layout_name'], T.font('alegreya-700', 17), INK, 0.95)
    # right: the keys, word then cap (as the book's head draws "K Close": cap, then word)
    f = T.font('alegreya-sans-500', 16)
    x = x1
    for key, word in reversed(h['keys']):
        x -= T.width(word, f)
        T.draw(L, x, ccy + 6, word, f, INK_BODY, 0.95)
        x -= 9 + cap_width(key)
        cap(L, key, x, ccy, 28)
        x -= 22


# ================================================================= the wick tabs (the panel's foot)
_TAB_CACHE = {}


def seat_disc(rgb_foot, seat_xy, mirror_chip=(24.5, -24.5, 9.0), r_out=36.6, px=56):
    """a HUD seat as a 56 px RGBA tab: the seat (art + bronze rim) cropped from the foot, the rank chip replaced by the
    mirrored rim, the disc masked with an anti-aliased edge, area-downsampled"""
    sx, sy = seat_xy
    R = 38
    x0, y0 = int(round(sx)) - R, int(round(sy)) - R
    crop = rgb_foot[y0:y0 + 2 * R, x0:x0 + 2 * R].copy()
    mir = crop[:, ::-1].copy()                                  # flip about the seat's vertical axis
    yy, xx = np.mgrid[0:2 * R, 0:2 * R].astype(np.float32)
    X, Y = x0 + xx + 0.5, y0 + yy + 0.5
    ccx, ccy, cr = sx + mirror_chip[0], sy + mirror_chip[1], mirror_chip[2]
    chip = np.clip(cr + 2.0 - np.hypot(X - ccx, Y - ccy), 0, 1)[..., None]
    crop = crop * (1 - chip) + mir * chip
    # 4x upsample then area-down to px
    s = px / (2 * r_out)
    big = cv2.resize(crop, (2 * R * 4, 2 * R * 4), interpolation=cv2.INTER_CUBIC)
    gy, gx = np.mgrid[0:2 * R * 4, 0:2 * R * 4].astype(np.float32)
    d = np.hypot(x0 + (gx + 0.5) / 4 - sx, y0 + (gy + 0.5) / 4 - sy)
    a = np.clip((r_out - d) * 4 + 0.5, 0, 1)
    rgba = np.concatenate([big * a[..., None], a[..., None]], -1)
    out_w = int(round(2 * R * s))
    out = cv2.resize(rgba, (out_w, out_w), interpolation=cv2.INTER_AREA)
    return np.clip(out, 0, 1)


def tabs(L, Lhalo, spec):
    """spec: discs [rgba], names, chosen (index), y (center), x0, x1, all_learned (rgba of an empty seat)
    returns the tab centers"""
    discs, chosen, cy = spec['discs'], spec['chosen'], spec['y']
    n = len(discs)
    pitch = 70
    fl = T.font('alegreya-sans-500', 15)
    label = 'All learned'
    lw = T.width(label, fl)
    cap_t = T.font('alegreya-sans-700', 13)
    lead = 'WICKS'
    ldw = T.width(lead, cap_t, 0.14)
    total = ldw + 20 + n * 56 + (n - 1) * (pitch - 56) + 26 + 56 + 8 + lw
    x = (spec['x0'] + spec['x1']) / 2 - total / 2
    T.draw(L, x, cy + 5, lead, cap_t, INK_DIM, 0.95, track=0.14)
    x += ldw + 20
    centers = []
    for i, dsc in enumerate(discs):
        w = dsc.shape[1]
        D.stamp(L, int(round(x)), int(round(cy - w / 2)), dsc)
        centers.append((x + w / 2, cy))
        x += pitch if i < n - 1 else w
    # a hairline divider, then All learned (an empty seat holding the book's scroll glyph)
    x += 13
    P = Patch(x - 1, cy - 20, x + 1, cy + 20)
    P.fill(np.maximum(np.abs(P.X - x) - 0.5, np.abs(P.Y - cy) - 18), RIM_GOLD, 0.35)
    P.stamp(L)
    x += 13
    al = spec['all_learned']
    w = al.shape[1]
    D.stamp(L, int(round(x)), int(round(cy - w / 2)), al)
    stamp_glyph(L, 'glyph/scroll', x + w / 2, cy, 24, hexc('#d6c4a0'), 0.85, gain=1.1)
    centers.append((x + w / 2, cy))
    T.draw(L, x + w + 8, cy + 5, label, fl, INK_BODY, 0.95)
    return centers


def _stem_dist(P, x, y0, kx, ky, rad=20.0):
    """r3: the wick stem as the braid's root: up from the tab (x, y0) to ky + rad, a rad-px bend right, then straight
    into the braid's knot (kx, ky). Returns the distance to the centerline."""
    d1, _, _ = D.segment(P, x, y0, x, ky + rad)
    cx, cy = x + rad, ky + rad
    arc = np.abs(np.hypot(P.X - cx, P.Y - cy) - rad)
    q = (P.X <= cx) & (P.Y <= cy)                          # the upper-left quarter only
    arc = np.where(q, arc, 1e6)
    d3, _, _ = D.segment(P, cx, ky, kx, ky)
    return np.minimum(np.minimum(d1, arc), d3)


def tab_ring(L, Lhalo, xy, r=28.0, stem_to=None):
    """the chosen tab's gold ring; with stem_to = (kx, ky), the 2 px wick stem rising from the tab and bending into the
    braid's knot (r3: one continuous line, the wick rising from the skill)"""
    x, y = xy
    top = stem_to[1] - 4 if stem_to is not None else y - r - 6
    x1 = max(stem_to[0], x + 20) + 2 if stem_to is not None else x + r + 6
    P = Patch(x - r - 6, top - 2, max(x + r + 6, x1), y + r + 6)
    d = D.ring(D.circle(P, x, y, r + 1.5), 2.0)
    if stem_to is not None:
        d = np.minimum(d, _stem_dist(P, x, y - r - 2.5, *stem_to) - 1.0)
    P.fill(d, FOCUS, 1.0)
    P.stamp(L)
    G = Patch(P.x0 - 8, P.y0 - 8, P.x1 + 8, P.y1 + 8)
    g = D.ring(D.circle(G, x, y, r + 1.5), 2.0)
    if stem_to is not None:
        g = np.minimum(g, _stem_dist(G, x, y - r - 2.5, *stem_to) - 1.0)
    G.fill(g, LIT_HALO, 0.45, soft=5.0)
    G.stamp(Lhalo, 1.0, 'add')


def frame_line(L, rect, a=0.30):
    """the board window's 1 px edge, in the house's rule gold"""
    x0, y0, x1, y1 = rect
    P = Patch(x0 - 1, y0 - 1, x1 + 1, y1 + 1)
    box = np.maximum(np.maximum(x0 - P.X, P.X - x1), np.maximum(y0 - P.Y, P.Y - y1))
    P.fill(np.abs(box + 0.5) - 0.5, RIM_GOLD, a)
    P.stamp(L)


def band_rule(L, x0, x1, y, a=0.35):
    """C5: the wick band's one hairline (gold, 1 px), fading out over the last 80 px at each end"""
    P = Patch(x0, y - 1, x1, y + 2)
    d = np.maximum(np.abs(P.Y - (y + 0.5)) - 0.5, np.maximum(x0 - P.X, P.X - x1))
    fade = D.smoothstep(0, 80, np.minimum(P.X - x0, x1 - P.X))
    c = P.cov(d) * a * fade
    P.a = np.concatenate([RIM_GOLD * c[..., None], c[..., None]], -1)
    P.stamp(L)
