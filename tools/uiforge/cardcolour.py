"""The uncommon and rare cards made loud: their colour laid into the guide before the paint.

Painted from words alone (batch.cards2) the bramble stayed brown and the rime stayed on the
top bar, so at a glance both read as the common's grey iron. Here the common card is
dressed first: for the uncommon, the Verge's bramble wound up both sides with green leaves
on it and wet moss in the lower corners; for the rare, the Low Ford's rime crusting every
edge of the strap, icicles under the bars and a cold sheen on the iron. Krea then paints
over the dressed card at a middling denoise, so the colour is the painting's own.

    python tools/uiforge/cardcolour.py [uncommon|rare ...]   # guides and paintings
"""
from __future__ import annotations

import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(ROOT, "tools", "comfy", "out", "uiforge")
BASE = os.path.join(RAW, "guides", "card_common_black.png")
INTERIOR = (86, 96, 650, 918)    # the card's calm middle, file px (cards.BASE)
SS = 2                           # drawn at twice the size, then reduced (clean edges)


def load():
    return np.asarray(Image.open(BASE).convert("RGB"), np.float32) / 255


def strap_mask(rgb):
    """The iron: what is lit, outside the calm middle."""
    v = rgb.max(axis=2)
    m = (v > 0.07).astype(np.float32)
    x0, y0, x1, y1 = INTERIOR
    m[y0 + 6:y1 - 6, x0 + 6:x1 - 6] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return cv2.GaussianBlur(m, (0, 0), 1.0)


def over(rgb, layer):
    """A drawn RGBA layer (at SS) laid over the picture."""
    lay = np.asarray(layer.resize((rgb.shape[1], rgb.shape[0]), Image.LANCZOS), np.float32) / 255
    a = lay[..., 3:4]
    return rgb * (1 - a) + lay[..., :3] * a


def wiggle(x, y0, y1, amp, period, phase, n=120):
    ys = np.linspace(y0, y1, n)
    xs = x + amp * np.sin(ys / period * 2 * math.pi + phase) + amp * 0.35 * np.sin(ys / period * 5.1 + phase * 2)
    return list(zip(xs, ys))


def leaf(d, cx, cy, ang, L, W, col, rib):
    """A bramble leaf: pointed at both ends, toothed a little, folded along its midrib so
    one half takes the light (upper left) and the other is in shade."""
    c, s = math.cos(ang), math.sin(ang)

    def half(sign):
        pts = [(-L / 2, 0)]
        for t in np.linspace(0, math.pi, 16)[1:-1]:
            r = W / 2 * math.sin(t) ** 0.8 * (1 + 0.14 * math.sin(t * 11))
            pts.append((-L / 2 * math.cos(t), sign * r))
        pts.append((L / 2, 0))
        return [((cx + u * c - v * s) * SS, (cy + u * s + v * c) * SS) for u, v in pts]

    # Which half faces the light: the one whose outward normal points up and left.
    lit = 1 if s - c > 0 else -1
    light = tuple(min(255, int(v * 1.35)) for v in col[:3]) + (255,)
    dark = tuple(int(v * 0.62) for v in col[:3]) + (255,)
    d.polygon(half(lit), fill=light)
    d.polygon(half(-lit), fill=dark)
    d.line([((cx - L / 2 * c) * SS, (cy - L / 2 * s) * SS), ((cx + L / 2 * c) * SS, (cy + L / 2 * s) * SS)], fill=rib, width=SS)


def uncommon_guide(dst):
    rgb = load()
    h, w = rgb.shape[:2]
    m = strap_mask(rgb)
    yy = np.mgrid[0:h, 0:w][0] / h
    # Wet moss over the lower iron, thickest in the corners.
    n = F.fbm(h, w, scale=40, octaves=5, seed=21)
    low = np.clip((yy - 0.4) / 0.5, 0, 1)
    xx = np.mgrid[0:h, 0:w][1] / w
    corner = np.clip(1 - np.minimum(xx, 1 - xx) / 0.2, 0, 1) * np.maximum(low, np.clip((0.2 - yy) / 0.12, 0, 1) * 0.6)
    moss = np.clip((n + 0.4 - (1 - low) * 0.8) * 2.5, 0, 1) * m * np.maximum(low * 0.7, corner)
    nf = F.fbm(h, w, scale=6, octaves=2, seed=22)
    tone = F.hexc("#3c6a22", lin=False) * (0.55 + 0.6 * np.clip(n[..., None] + 0.5, 0, 1)) * (0.85 + 0.3 * nf[..., None])
    # The iron itself has taken the wood's green where it is wet: a verdigris in its lights.
    rgb = rgb * (1 - m[..., None] * 0.5) + np.clip(rgb * np.array([0.86, 1.08, 0.84], np.float32), 0, 1) * m[..., None] * 0.5
    rgb = rgb * (1 - moss[..., None] * 0.9) + tone * moss[..., None] * 0.9
    # The bramble: a stem up each side and along the top, leaves on it, thorns.
    layer = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = np.random.default_rng(5)
    stems = [wiggle(67, 940, 140, 13, 170, 0.4), wiggle(669, 940, 140, 13, 190, 2.1)]
    top = [(x, 72 + 10 * math.sin(x / 60)) for x in np.linspace(110, 300, 40)] + [(x, 72 + 10 * math.sin(x / 55 + 1)) for x in np.linspace(440, 626, 40)]
    for S in stems + [top[:40], top[40:]]:
        P = [(x * SS, y * SS) for x, y in S]
        d.line(P, fill=(40, 46, 22, 255), width=7 * SS, joint="curve")
        d.line([(x - SS, y - SS) for x, y in P], fill=(96, 110, 52, 255), width=2 * SS)
        for i in range(4, len(S) - 2, 5):
            x, y = S[i]
            sd = 1 if rng.random() < 0.5 else -1
            d.polygon([((x + sd * 3) * SS, (y - 3) * SS), ((x + sd * 10) * SS, (y - 7) * SS), ((x + sd * 3) * SS, (y + 2) * SS)],
                      fill=(120, 40, 26, 255))
    greens = [(66, 128, 44), (88, 156, 56), (112, 182, 70), (54, 110, 36)]
    for S in stems + [top[:40], top[40:]]:
        for i in range(3, len(S) - 3, 5):
            x, y = S[i]
            side = -1 if (i // 6) % 2 else 1
            ang = (-0.6 if side < 0 else 0.6) + math.pi * (side < 0) + rng.uniform(-0.4, 0.4)
            L, W = rng.uniform(18, 34), rng.uniform(9, 16)
            cx, cy = x + math.cos(ang) * L * 0.55, y + math.sin(ang) * L * 0.55
            g = greens[rng.integers(len(greens))]
            leaf(d, cx, cy, ang, L, W, g + (255,), (34, 60, 20, 255))
    rgb = over(rgb, layer)
    out = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    out.save(dst)
    return dst


def rare_guide(dst):
    rgb = load()
    h, w = rgb.shape[:2]
    m = strap_mask(rgb)
    # The iron gone cold: a blue sheen on its lights, its darks a little bluer.
    cold = rgb * np.array([0.78, 0.92, 1.18], np.float32) + np.array([0.0, 0.02, 0.05], np.float32)
    rgb = rgb * (1 - m[..., None] * 0.85) + np.clip(cold, 0, 1) * m[..., None] * 0.85
    # Rime: a crust along every edge of the iron, broken by the grain, heaviest on top faces.
    er = cv2.erode((m > 0.5).astype(np.uint8), np.ones((9, 9), np.uint8))
    edge = np.clip(m - er, 0, 1)
    edge = cv2.GaussianBlur(edge, (0, 0), 2.5)
    up = np.clip(cv2.Sobel(m, cv2.CV_32F, 0, 1, ksize=7) / 8, 0, 1)   # faces lit from above
    n = F.fbm(h, w, scale=14, octaves=4, seed=31)
    # Crystalline, not a paste: fine flecks where the crust is, thickest at the edges.
    fleck = np.clip((F.fbm(h, w, scale=2.5, octaves=2, seed=33) + 0.15) * 3, 0, 1)
    rime = np.clip((edge * 1.6 + up * 0.8) * (0.55 + n * 0.8), 0, 1) * (m > 0.2) * (0.45 + 0.55 * fleck)
    white = F.hexc("#e8f6ff", lin=False)
    rgb = rgb * (1 - rime[..., None] * 0.9) + white * rime[..., None] * 0.9
    # Frost crystals scattered over the strap, and icicles under the bars.
    layer = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = np.random.default_rng(9)
    ys, xs = np.nonzero(m > 0.6)
    for k in rng.choice(len(xs), 70, replace=False):
        x, y = xs[k], ys[k]
        r = rng.uniform(3, 7)
        for a in range(3):
            t = a * math.pi / 3 + rng.uniform(0, 0.4)
            d.line([((x - r * math.cos(t)) * SS, (y - r * math.sin(t)) * SS), ((x + r * math.cos(t)) * SS, (y + r * math.sin(t)) * SS)],
                   fill=(236, 248, 255, 230), width=SS)
    # Hoarfrost: needles grown out from the iron's outer edges into the air.
    outer = (cv2.dilate((m > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8)) - (m > 0.5)).astype(bool)
    ey, ex = np.nonzero(outer)
    gy_, gx_ = np.gradient(cv2.GaussianBlur(m, (0, 0), 3))
    for k in rng.choice(len(ex), 420, replace=False):
        x, y = ex[k], ey[k]
        nx_, ny_ = -gx_[y, x], -gy_[y, x]
        nn = math.hypot(nx_, ny_)
        if nn < 1e-3:
            continue
        nx_, ny_ = nx_ / nn, ny_ / nn
        L = rng.uniform(3, 9)
        a = math.atan2(ny_, nx_) + rng.uniform(-0.5, 0.5)
        d.line([(x * SS, y * SS), ((x + L * math.cos(a)) * SS, (y + L * math.sin(a)) * SS)], fill=(230, 244, 255, 220), width=SS)
    for y_bar, x0, x1 in ((98, 100, 636), (954, 100, 636)):
        x = x0
        while x < x1:
            L = rng.uniform(10, 46) * (1.0 if y_bar < 500 else 0.6)
            wd = rng.uniform(4, 8)
            d.polygon([((x - wd / 2) * SS, y_bar * SS), ((x + wd / 2) * SS, y_bar * SS), ((x + rng.uniform(-1, 1)) * SS, (y_bar + L) * SS)],
                      fill=(196, 228, 250, 240))
            d.line([((x - wd / 4) * SS, y_bar * SS), (x * SS, (y_bar + L * 0.8) * SS)], fill=(250, 254, 255, 255), width=SS)
            x += rng.uniform(10, 28)
    rgb = over(rgb, layer)
    out = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    out.save(dst)
    return dst


GUIDES = {"uncommon": uncommon_guide, "rare": rare_guide}
# Seeds 670 (uncommon) and 671 (rare); TAG card3_KIND, at each denoise.
SEED = {"uncommon": 690, "rare": 693}
# The bramble paints well from words at a middling denoise; the rime does not (the paint takes
# it for the iron's own light), so the rare is painted lower and keeps its dressing.
DENOISE = {"uncommon": (0.46, 0.54), "rare": (0.3, 0.38)}
# Even at 0.3 the paint cleans most of the rime away: the rare's painting is laid back over
# its dressing's light and colour (merge, keeping 0.6 of the dressing's). The bramble needs none.
KEEP = {"uncommon": None, "rare": 0.6}


def prompt(kind):
    import batch
    more = {
        "uncommon": ("thorny bramble stems with vivid green leaves winding up both sides of the strap and along the top, "
                     "thick wet green moss in the lower corners, "),
        "rare": ("the whole strap crusted with white rime frost and sharp frost crystals, icicles hanging under the top "
                 "and bottom bars, the iron cold blue-silver, "),
    }[kind]
    # The base words asked for "a few" leaves, "faint" light and rime "along the top": the
    # paintings did just that, and stayed quiet.
    words = (batch.RARITY[kind].replace("a few small green leaves", "many vivid green bramble leaves")
             .replace("faint green light", "glowing green light")
             .replace("grown over the brackets and along the top", "grown over the brackets and along every edge of the strap"))
    return words.replace("the inside plain flat dark iron", more + "the inside plain flat dark iron") + ". " + batch.S


def paint(kinds=None, n=2):
    """Every take of the dressed cards on black, as cards.fit cuts them: card3/card3po_* the
    paintings, card3/card3m_* the rare's laid back over its dressing."""
    import krea
    jobs, guides = [], {}
    for k in kinds or list(GUIDES):
        g = GUIDES[k](os.path.join(RAW, "guides", f"card_{k}_dressed.png"))
        guides[k] = g
        for dn in DENOISE[k]:
            jobs.append((f"card3po_{k}_{int(dn * 100)}", g, prompt(k), dn, SEED[k]))
    res = krea.i2i_many(jobs, n=n, out=os.path.join(RAW, "card3"))
    made = []
    for tag, paths in res.items():
        k = tag.split("_")[1]
        if KEEP[k] is None:
            made += paths
            continue
        base = np.asarray(Image.open(guides[k]).convert("RGB"), np.float32) / 255
        for p in paths:
            out = p.replace("card3po_", "card3m_")
            Image.fromarray((np.clip(merge(base, p, KEEP[k]), 0, 1) * 255 + 0.5).astype(np.uint8)).save(out)
            made.append(out)
    return made


def merge(base, painted_path, keep=0.7):
    """The painting's detail and hue over the guide's large light and colour (paintover.py's
    rule): what the dressing put there stays there, with the painting's hand."""
    painted = np.asarray(Image.open(painted_path).convert("RGB"), np.float32) / 255
    painted = cv2.resize(painted, (base.shape[1], base.shape[0]), interpolation=cv2.INTER_AREA)
    sgm = 6.0
    lb = cv2.GaussianBlur(F.srgb_to_lin(base), (0, 0), sgm)
    lp = cv2.GaussianBlur(F.srgb_to_lin(painted), (0, 0), sgm)
    lin_p = F.srgb_to_lin(painted)
    mixed = lin_p * (1 - keep) + (lin_p / np.maximum(lp, 1e-4) * lb) * keep
    return F.lin_to_srgb(np.clip(mixed, 0, 1))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--guides":
        for k in args[1:] or list(GUIDES):
            print(GUIDES[k](os.path.join(RAW, "guides", f"card_{k}_dressed.png")))
    else:
        for path in paint(args or None):
            print(path)
