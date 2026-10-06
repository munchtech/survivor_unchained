import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit, W
import os

p = os.path.join(W, 'tools/assets/heroine_paint.py')
s = open(p, encoding='utf-8', newline='').read()
a = s.index('def kohl(shape, f, smoky=1.0, seed=11):')
b = s.index('def gilt(shape, f, seed=71):')
new = '''def kohl(shape, f, smoky=1.0, seed=11):
    """Soot and tallow round the eyes: smoked thick over the lids to the crease
    and out toward the outer corners, under the lower lashes too; a dark line
    hard along the upper lashes, drawn out to a long point toward the temple.
    (Bold: the lid's margin rolls in under the lashes, so a line laid only
    there is hidden; the game sees her from metres away.)"""
    L = layer(shape)
    ink = hexc('#120b0b')
    for side, hole in enumerate(f['holes']):
        dist = ring_dist(hole)
        ys, xs = np.nonzero(hole)
        cy = ys.mean()
        yy = np.arange(shape[0], dtype=np.float32)[:, None] - cy
        top = np.clip(-yy / 30, 0, 1)
        # (her right eye's outer corner is toward the sheet's left, her left eye's toward its right)
        outer = 1 if side == 1 else -1
        xx = (np.arange(shape[1], dtype=np.float32)[None, :] - xs.mean()) * outer
        out = np.clip(xx / 80, 0, 1)
        # The smoke: thick up over the lid, fading at the crease; swept out toward the outer corner; a little under.
        reach = 26 + 70 * top + 46 * out * (0.4 + 0.6 * top)
        smoke = (np.clip(1 - dist / reach, 0, 1) ** 0.75 * (dist > 0)).astype(np.float32)
        smoke = blur(smoke, 6) * smoky
        lay(L, smoke, ink, 0.9, pigment(shape, seed + side, 26, 0.25))
        # The line along the upper lashes, thickening toward the outer corner; the lower ones smudged.
        thick = 15 + 9 * out
        upper = ((dist > 0) & (dist < thick) & (yy < 6)).astype(np.float32)
        lower = ((dist > 0) & (dist < 10) & (yy >= 6)).astype(np.float32)
        line = np.clip(blur(upper, 1.6) * 1.0 + blur(lower, 3.0) * 0.8, 0, 1)
        lay(L, line, ink, 1.0)
        # The wing: from the outer corner of the upper lid, up and out to a long point.
        corner_x = xs.max() if outer > 0 else xs.min()
        near = np.abs(xs - corner_x) < 8
        cyc = ys[near].mean() if near.any() else cy
        pts = [(corner_x - outer * 30, cyc - 22), (corner_x + outer * 6, cyc - 14), (corner_x + outer * 56, cyc - 34), (corner_x + outer * 112, cyc - 64)]
        wing = stroke(shape, pts, [20, 20, 13, 1.0], dry=0.0, streaks=0.0, soft=0.2, seed=seed + 5 + side, taper=(0.02, 0.75), edge=0.04)
        lay(L, wing, ink, 1.0)
    return L


def rouge(shape, f, seed=21):
    """Kohl, and her lips stained the deep red of crushed rosehip (their lines
    kept), a flush high on her cheeks."""
    L = kohl(shape, f, smoky=0.85, seed=seed)
    lips = blur(f['lips'].astype(np.float32), 2.0)
    lay(L, lips, hexc('#9a0c1c'), 0.95, pigment(shape, seed, 14, 0.1), through=0.5)
    for c in (CHEEK_R, CHEEK_L):
        flush = np.zeros(shape, np.float32)
        cv2.ellipse(flush, (int(c[0]), int(c[1] - 30)), (130, 64), -14 if c[0] > MID else 14, 0, 360, 1.0, -1)
        lay(L, blur(flush, 44), hexc('#c0303c'), 0.3)
    return L


def woad(shape, f, seed=31):
    """The old blue of the hill people: a band dragged across her brow, temple
    to temple, by the flat of three fingers; and under each eye two fingers
    drawn down her cheek to the jaw. Chalky, broken where the woad ran dry,
    the skin's grain through it."""
    L = layer(shape)
    blue = hexc('#183c9e')
    grain = pigment(shape, seed, 16, 0.18)
    cov = np.zeros(shape, np.float32)
    # The band over her brow (above her brows, below her hairline), a little higher at the temples.
    by = 700
    pts = [(TEMPLE_R[0] + 10, by + 40), (640, by + 6), (MID, by - 6), (1460, by + 6), (TEMPLE_L[0] - 10, by + 40)]
    cov = np.maximum(cov, stroke(shape, pts, [96, 118, 120, 118, 90], dry=0.45, streaks=0.6, soft=0.28, seed=seed, taper=(0.05, 0.1), streak_px=9, edge=0.5))
    # Two fingers down each cheek, from under the eye's outer half to the jaw, splaying a little.
    for side, hole in enumerate(f['holes']):
        ys, xs = np.nonzero(hole)
        out = 1 if side == 1 else -1
        x0, y0 = xs.mean() + out * 12, ys.max() + 46
        for k, dx in enumerate((-34, 40)):
            x = x0 + out * dx
            pts = [(x, y0), (x + out * 6, y0 + 130), (x + out * (14 + k * 8), y0 + 290), (x + out * (20 + k * 14), y0 + 470)]
            cov = np.maximum(cov, stroke(shape, pts, [56, 60, 52, 26], dry=0.55, streaks=0.5, soft=0.26, seed=seed + 3 + side * 2 + k,
                                         taper=(0.05, 0.45), streak_px=6, edge=0.45))
    lay(L, cov, blue, 0.96, grain, through=0.3)
    return L


def ochre(shape, f, seed=41):
    """A band of red earth across the eyes, temple to temple, laid on with two
    fingers drawn from her right temple to her left: thick where they began,
    thinning and breaking up as the earth ran out."""
    L = layer(shape)
    red = hexc('#a83614')
    grain = pigment(shape, seed, 20, 0.22)
    ey = (f['holes'][0].nonzero()[0].mean() + f['holes'][1].nonzero()[0].mean()) / 2
    # (the two fingers' tracks one band: where they overlap it is no thicker)
    cov = np.zeros(shape, np.float32)
    for k, dy in enumerate((-30, 30)):
        pts = [(TEMPLE_R[0] + 20, ey + dy + 26), (650, ey + dy - 2), (MID, ey + dy - 12), (1450, ey + dy - 2), (TEMPLE_L[0] - 20, ey + dy + 24)]
        c = stroke(shape, pts, [100, 106, 104, 100, 76], dry=0.4, streaks=0.5, soft=0.28, seed=seed + k, taper=(0.04, 0.12), streak_px=8, edge=0.45)
        cov = np.maximum(cov, c)
    lay(L, cov, red, 0.95, grain, through=0.35)
    return L


def ash(shape, f, seed=51):
    """Pale ash from a dead fire, thumbed under each eye and dragged down the
    cheek, and a thumb's smear up the middle of her brow: thick where the
    thumb pressed, smeared thin as it was drawn."""
    L = layer(shape)
    grey = hexc('#dcd8d0')
    cov = np.zeros(shape, np.float32)
    for side, hole in enumerate(f['holes']):
        ys, xs = np.nonzero(hole)
        out = 1 if side == 1 else -1
        x, y = xs.mean() + out * 10, ys.max() + 22
        pts = [(x - out * 70, y + 4), (x, y + 20), (x + out * 30, y + 130), (x + out * 46, y + 250)]
        cov = np.maximum(cov, stroke(shape, pts, [110, 124, 100, 44], dry=0.45, streaks=0.5, soft=0.4, seed=seed + side, taper=(0.08, 0.6), streak_px=11, edge=0.55))
    pts = [(MID + 4, 830), (MID, 740), (MID - 6, 620)]
    cov = np.maximum(cov, stroke(shape, pts, [96, 90, 40], dry=0.5, streaks=0.5, soft=0.4, seed=seed + 9, taper=(0.1, 0.6), streak_px=11, edge=0.5))
    lay(L, cov, grey, 0.95, pigment(shape, seed + 5, 9, 0.45), through=0.45)
    return L


def blood(shape, f, seed=61):
    """Three fingers of blood drawn down over her left eye, brow to jaw: dark
    where it pooled at the start, thinning as the fingers dragged, darker
    at its edges where it dried first."""
    L = layer(shape)
    ys, xs = np.nonzero(f['holes'][1])
    cx = xs.mean()
    for k, off in enumerate((-92, 0, 90)):
        x = cx + off
        pts = [(x - 4, 690), (x, 800), (x + 8, 960), (x + 20, 1130), (x + 30, 1290)]
        c = stroke(shape, pts, [62, 68, 62, 54, 18], dry=0.5, streaks=0.4, soft=0.24, seed=seed + k, taper=(0.03, 0.5), streak_px=6, edge=0.45)
        lay(L, c, hexc('#8a0a12'), 0.95, pigment(shape, seed + 7 + k, 12, 0.25), through=0.3)
        rim = np.clip(c * (1 - c) * 4, 0, 1) * (c > 0.05)
        lay(L, blur(rim.astype(np.float32), 2.0), hexc('#3a0406'), 0.35)
    return L


'''
new = new.replace('\n', '\r\n') if '\r\n' in s else new
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok', len(s))
