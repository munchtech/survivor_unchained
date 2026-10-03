"""The ornament vocabulary: what a smith in the Waystation has to hand.

Not a jeweller's filigree: Brannoc's work. Tapered bars drawn out under the
hammer and curled into scrolls (the lamp-irons' brackets), strap ends,
hand-set rivets, punched dot rows, the binders' square coin, chain links
(one of them always opened: the survivor, unchained), and the veins of
ember that sleep in the iron's cracks by day and wake where there is power.

Every function draws into a forge.Surface: height (max-combined, so pieces
sit on top of what is there), material, alpha. Sizes in canvas pixels.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

import forge as F

EMBER = F.hexc("#ff8a3a")
EMBER_HI = F.hexc("#ffd07a")
EMBER_DEEP = F.hexc("#c8401a")
ASH = F.hexc("#5a2010")


def put(s, cov, hgt, mat, albedo_mul=None, base=0.0, mode="max"):
    """Lay a piece on the surface: its height on top of what is there where it covers."""
    top = base + hgt
    if mode == "max":
        new = np.maximum(s.height, top)
    elif mode == "add":
        new = s.height + hgt
    else:
        new = top
    s.height = s.height * (1 - cov) + new * cov
    if mat is not None:
        s.paint(cov, mat, albedo_mul=albedo_mul)
    s.alpha = np.maximum(s.alpha, cov)


def surface_at(s, x, y):
    """Height of the surface under a point (for pieces that sit on it)."""
    xi = int(np.clip(x, 0, s.w - 1))
    yi = int(np.clip(y, 0, s.h - 1))
    return float(s.height[yi, xi])


# ------------------------------------------------------------- forged bars --

def polyline_field(xx, yy, pts):
    """Distance to a polyline and the arc-length parameter (0..1) of the nearest point."""
    pts = np.asarray(pts, np.float32)
    seg = np.diff(pts, axis=0)
    seglen = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0], np.cumsum(seglen)])
    total = max(cum[-1], 1e-6)
    best = np.full(xx.shape, 1e9, np.float32)
    par = np.zeros(xx.shape, np.float32)
    # Only the bounding box matters: callers pass cropped grids.
    for i in range(len(seg)):
        a = pts[i]
        ex, ey = seg[i]
        L2 = ex * ex + ey * ey + 1e-9
        t = np.clip(((xx - a[0]) * ex + (yy - a[1]) * ey) / L2, 0, 1)
        d = np.hypot(xx - a[0] - ex * t, yy - a[1] - ey * t)
        closer = d < best
        best = np.where(closer, d, best)
        par = np.where(closer, (cum[i] + t * seglen[i]) / total, par)
    return best, par


def forged_bar(s, pts, w0, w1, height, mat="iron", base=None, taper_end=True, facet=0.25, bbox_pad=None, round_cap=True):
    """A bar of iron drawn out under the hammer along a path: wide at w0, narrowing to w1,
    rounded on top with faint hammer facets. Returns its coverage."""
    pts = np.asarray(pts, np.float32)
    pad = int(max(w0, w1) + 4) if bbox_pad is None else bbox_pad
    x0, y0 = np.floor(pts.min(0) - pad).astype(int)
    x1, y1 = np.ceil(pts.max(0) + pad).astype(int)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(s.w, x1), min(s.h, y1)
    if x1 <= x0 or y1 <= y0:
        return np.zeros((s.h, s.w), np.float32)
    xx = s.xx[y0:y1, x0:x1]
    yy = s.yy[y0:y1, x0:x1]
    d, t = polyline_field(xx, yy, pts)
    half = (w0 + (w1 - w0) * t) * 0.5
    sd = half - d
    cov = F.coverage(sd, 1.0)
    prof = np.sqrt(np.clip(sd / np.maximum(half, 1e-3), 0, 1))
    # Hammer facets along the bar: a slow ripple of flats.
    if facet > 0:
        L = np.hypot(*np.diff(pts, axis=0).T).sum()
        prof = prof * (1 - facet * 0.5 * (1 + np.cos(t * L / (max(w0, 4) * 0.9) * 2 * math.pi)) * 0.25)
    hgt = prof * height * (0.75 + 0.25 * (half / max(w0 * 0.5, 1e-3)))
    full_cov = np.zeros((s.h, s.w), np.float32)
    full_cov[y0:y1, x0:x1] = cov
    full_h = np.zeros((s.h, s.w), np.float32)
    b = surface_at(s, *pts[len(pts) // 2]) if base is None else base
    full_h[y0:y1, x0:x1] = hgt + b
    s.height = np.where(full_cov > 0, s.height * (1 - full_cov) + np.maximum(s.height, full_h) * full_cov, s.height)
    if mat:
        s.paint(full_cov, mat)
    s.alpha = np.maximum(s.alpha, full_cov)
    return full_cov


def spiral(cx, cy, r0, r1, a0, turns, n=80):
    """Points of a scroll: from radius r0 at angle a0, curling `turns` times in to r1."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        a = a0 + turns * 2 * math.pi * t
        r = r0 + (r1 - r0) * t
        out.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return out


# ------------------------------------------------------------------ pieces --

def rivet(s, cx, cy, r, mat="iron", base=None, ember=0.0):
    sd = F.sd_circle(s.xx, s.yy, cx, cy, r)
    cov = F.coverage(sd, 1.0)
    b = surface_at(s, cx, cy) if base is None else base
    dome = np.sqrt(np.clip(sd / r, 0, 1)) * r * 0.55
    put(s, cov, dome, mat, base=b)
    return cov


def quatrefoil_sd(xx, yy, cx, cy, r, rot=0.0):
    """A quatrefoil (four overlapping lobes), positive inside."""
    out = None
    for k in range(4):
        a = rot + k * math.pi / 2
        lx, ly = cx + math.cos(a) * r * 0.42, cy + math.sin(a) * r * 0.42
        d = F.sd_circle(xx, yy, lx, ly, r * 0.46)
        out = d if out is None else np.maximum(out, d)
    return out


def coin(s, cx, cy, size, mat="iron", base=None, rot=math.pi / 4, hole=0.32, rim=0.16, sigil=True, ember=None, foil=False):
    """The binders' square coin, set on its point: a raised rim, a hammered face,
    a square hole through which the light underneath shows. Returns (cov, hole_cov)."""
    c, sn = math.cos(rot), math.sin(rot)
    dx, dy = s.xx - cx, s.yy - cy
    u = dx * c + dy * sn
    v = -dx * sn + dy * c
    half = size / 2
    sd = -(np.maximum(np.abs(u), np.abs(v)) - half)  # positive inside the square
    sd = np.minimum(sd, half * 0.22 + (half * 0.92 - np.hypot(np.maximum(np.abs(u) - half * 0.7, 0), np.maximum(np.abs(v) - half * 0.7, 0))) * 3)  # nip the points
    cov = F.coverage(sd, 1.0)
    hsd = -(np.maximum(np.abs(u), np.abs(v)) - half * hole)
    if foil:
        hsd = quatrefoil_sd(s.xx, s.yy, cx, cy, half * hole * 1.25, rot=rot)
    hole_cov = F.coverage(hsd, 1.0)
    b = surface_at(s, cx, cy) if base is None else base
    thick = size * 0.10
    face = thick + np.clip(sd / (size * rim), 0, 1) * 0  # flat face
    rim_h = np.clip(1 - np.abs(sd - size * rim * 0.5) / (size * rim * 0.5), 0, 1) ** 0.6 * size * 0.05
    edge = F.bevel(sd, size * 0.04, size * 0.05)
    h = face + rim_h + edge
    # The hole: down through the coin.
    h = h * (1 - hole_cov) + (-size * 0.06) * hole_cov
    # Inner rim round the hole.
    hrim = np.clip(1 - np.abs(-hsd - size * 0.035) / (size * 0.035), 0, 1) ** 0.7 * size * 0.035
    h = h + hrim * (1 - hole_cov)
    put(s, cov, h, mat, base=b)
    if sigil:
        # Four short cuts toward the points: the binders' marks (no letters).
        for k in range(4):
            a = rot + k * math.pi / 2
            p0 = (cx + math.cos(a) * size * 0.27, cy + math.sin(a) * size * 0.27)
            p1 = (cx + math.cos(a) * size * 0.40, cy + math.sin(a) * size * 0.40)
            dline = F.sd_segment(s.xx, s.yy, p0, p1)
            cut = F.coverage(size * 0.022 - dline, 1.0) * cov * (1 - hole_cov)
            s.height -= cut * size * 0.02
            s.paint(cut, "gold")
    return cov, hole_cov


def link(s, cx, cy, length, width, thick, angle=0.0, gap=0.0, gap_at=0.0, mat="iron", base=None):
    """A chain link (a stadium ring) of round bar; with `gap` (radians of the ring) it is
    opened at `gap_at` (0 = the far end along its length). Returns (cov, break_points)."""
    c, sn = math.cos(angle), math.sin(angle)
    # The centreline of a stadium: two half circles joined by straights.
    r = width / 2
    straight = max(length - width, 0) / 2
    pts = []
    n = 64
    for i in range(n + 1):
        t = i / n * 2 * math.pi
        # Parameterise around the stadium.
        a = t
        if math.cos(a) >= 0:
            x = straight + r * math.cos(a)
        else:
            x = -straight + r * math.cos(a)
        y = r * math.sin(a)
        pts.append((x, y, t))
    keep = []
    breaks = []
    for x, y, t in pts:
        dt = (t - gap_at + math.pi) % (2 * math.pi) - math.pi
        if gap > 0 and abs(dt) < gap / 2:
            continue
        keep.append((x, y, t))
    # Split into runs where the gap cuts.
    runs, cur = [], []
    prev_t = None
    for x, y, t in keep:
        if prev_t is not None and t - prev_t > 2 * math.pi / n * 1.5:
            runs.append(cur)
            cur = []
        cur.append((x, y))
        prev_t = t
    if cur:
        runs.append(cur)
    if len(runs) > 1 and gap > 0 and abs(((runs[0][0][0] - runs[-1][-1][0]) ** 2 + (runs[0][0][1] - runs[-1][-1][1]) ** 2)) < (width * 0.2) ** 2:
        runs = [runs[-1] + runs[0]] + runs[1:-1]
    total = np.zeros((s.h, s.w), np.float32)
    for run in runs:
        wp = [(cx + x * c - y * sn, cy + x * sn + y * c) for x, y in run]
        if len(wp) < 2:
            continue
        b = surface_at(s, cx, cy) if base is None else base
        cov = forged_bar(s, wp, thick, thick, thick * 0.55, mat=mat, base=b, facet=0.0)
        total = np.maximum(total, cov)
        breaks += [wp[0], wp[-1]]
    return total, breaks


def cracks(s, region, seed=0, count=6, length=40.0, step=2.0, width=1.2, depth=1.2, branch=0.25, start_pts=None):
    """Hairline cracks wandering through `region` (a 0..1 mask): returns their mask.
    The ember veins: carve them, then light them with `vein_light`."""
    rng = np.random.default_rng(seed)
    m = np.zeros((s.h, s.w), np.float32)
    ys, xs = np.nonzero(region > 0.5)
    if len(xs) == 0:
        return m
    starts = start_pts or [(xs[i], ys[i]) for i in rng.integers(0, len(xs), count)]

    def walk(x, y, a, L, w):
        pts = [(x, y)]
        n = int(L / step)
        for _ in range(n):
            a += rng.normal() * 0.45
            x += math.cos(a) * step
            y += math.sin(a) * step
            if not (0 <= int(x) < s.w and 0 <= int(y) < s.h) or region[int(y), int(x)] < 0.5:
                break
            pts.append((x, y))
            if rng.random() < branch * step / L * 3:
                walk(x, y, a + rng.choice([-1, 1]) * rng.uniform(0.5, 1.1), L * 0.45, w * 0.7)
        if len(pts) > 1:
            P = np.round(np.asarray(pts) * 4).astype(np.int32)
            # Taper: thick at the start, thin at the end, drawn in pieces.
            k = len(P)
            for i in range(k - 1):
                ww = max(1, int(w * 4 * (1 - i / k * 0.8)))
                cv2.line(m, tuple(P[i]), tuple(P[i + 1]), 1.0, ww, cv2.LINE_AA, shift=2)

    for (x, y) in starts:
        walk(float(x), float(y), rng.random() * 2 * math.pi, length * rng.uniform(0.6, 1.2), width)
    m = np.clip(m, 0, 1)
    s.height -= m * depth
    s.paint(m, "black")
    return m


def vein_light(mask, awake=0.0, sleeping=0.35, spread=3.0):
    """Ember in the cracks (linear RGB to add): asleep it smoulders dull red, awake it burns."""
    core = mask[..., None]
    halo = F.blur(mask, spread)[..., None]
    asleep = core * ASH * 0.9 * sleeping + halo * ASH * 0.25 * sleeping
    lit = core * (EMBER_HI * 1.6) + halo * EMBER * 1.1 + F.blur(mask, spread * 3)[..., None] * EMBER_DEEP * 0.5
    return asleep * (1 - awake) + lit * awake


def punch_dots(s, pts, r, depth=None):
    """A row of punched dots (a smith's chasing punch)."""
    depth = depth or r * 0.6
    for (x, y) in pts:
        sd = F.sd_circle(s.xx, s.yy, x, y, r)
        cov = F.coverage(sd, 1.0)
        bowl = np.sqrt(np.clip(sd / r, 0, 1))
        s.height -= bowl * depth * cov
        s.paint(cov * 0.5, "iron_dark")


def hammer_mark(s, cx, cy, size, depth=None):
    """Brannoc's mark, stamped: a hammer struck across a bar (no letter: the B is his alone)."""
    depth = depth or size * 0.08
    xx, yy = s.xx, s.yy
    # Haft (diagonal) and head (across its top), then the struck bar.
    a = -math.pi / 4
    c, sn = math.cos(a), math.sin(a)
    u = (xx - cx) * c + (yy - cy) * sn
    v = -(xx - cx) * sn + (yy - cy) * c
    haft = -(np.maximum(np.abs(u) - size * 0.42, np.abs(v) - size * 0.06))
    head = -(np.maximum(np.abs(u - size * 0.36) - size * 0.10, np.abs(v) - size * 0.24))
    bar = -(np.maximum(np.abs(xx - cx) - size * 0.05, np.abs(yy - cy) - size * 0.44))
    sd = np.maximum(np.maximum(haft, head), bar)
    # A tiny frame: a punched square border round it.
    box = np.abs(np.maximum(np.abs(xx - cx), np.abs(yy - cy)) - size * 0.56) - size * 0.035
    cov = np.maximum(F.coverage(sd, 1.0), F.coverage(-box, 1.0))
    s.height -= cov * depth
    s.paint(cov * 0.6, "iron_dark")
    return cov
