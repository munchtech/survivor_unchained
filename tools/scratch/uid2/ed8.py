exec(open(__file__.replace('ed8.py', 'edlib.py')).read())
p = 'tools/assets/heroine_paint.py'
s = open(p, encoding='utf-8').read()
a = s.index('# -------------------------------------------------------------- designs --')
b = s.index("DESIGNS = {")
designs = r'''# -------------------------------------------------------------- designs --
# Sizes on the sheet: a pixel is 0.16 mm, so a fingertip's track is about 90
# pixels wide, a fine brush's line 6 to 10, an eye's opening about 185 long.

def ring_dist(hole):
    """Distance (pixels) from an eye's opening, outside it; inside it, 0."""
    return cv2.distanceTransform((~hole).astype(np.uint8), cv2.DIST_L2, 5)


def kohl(shape, f, smoky=1.0, seed=11):
    """Soot and tallow round the eyes: smoked out over the lids and toward the
    outer corners, under the lower lashes too; a dark line hard along the
    upper lashes, drawn out to a point toward the temple."""
    L = layer(shape)
    ink = hexc('#140d0c')
    for side, hole in enumerate(f['holes']):
        dist = ring_dist(hole)
        ys, xs = np.nonzero(hole)
        cy = ys.mean()
        yy = np.arange(shape[0], dtype=np.float32)[:, None] - cy
        top = np.clip(-yy / 30, 0, 1)
        # (her right eye's outer corner is toward the sheet's left, her left eye's toward its right)
        outer = 1 if side == 1 else -1
        xx = (np.arange(shape[1], dtype=np.float32)[None, :] - xs.mean()) * outer
        # The smoke: up over the lid to the crease, out toward the outer corner, a little under.
        reach = 22 + 58 * top + 34 * np.clip(xx / 80, 0, 1) * (0.4 + 0.6 * top)
        smoke = (np.clip(1 - dist / reach, 0, 1) ** 1.25 * (dist > 0)).astype(np.float32)
        smoke = blur(smoke, 7) * smoky
        lay(L, smoke, ink, 0.86, pigment(shape, seed + side, 26, 0.3))
        # The line along the upper lashes, thickening toward the outer corner; the lower ones smudged.
        thick = 7 + 6 * np.clip(xx / 80, 0, 1)
        upper = ((dist > 0) & (dist < thick) & (yy < 6)).astype(np.float32)
        lower = ((dist > 0) & (dist < 7) & (yy >= 6)).astype(np.float32)
        line = np.clip(blur(upper, 1.4) * 1.0 + blur(lower, 2.5) * 0.7, 0, 1)
        lay(L, line, ink, 1.0)
        # The wing: from the outer corner of the upper lid, up and out to a point.
        corner_x = xs.max() if outer > 0 else xs.min()
        near = np.abs(xs - corner_x) < 8
        cyc = ys[near].mean() if near.any() else cy
        pts = [(corner_x - outer * 40, cyc - 14), (corner_x - outer * 4, cyc - 6), (corner_x + outer * 40, cyc - 22), (corner_x + outer * 78, cyc - 44)]
        wing = stroke(shape, pts, [14, 14, 9, 1.0], dry=0.0, streaks=0.0, soft=0.22, seed=seed + 5 + side, taper=(0.02, 0.7), edge=0.04)
        lay(L, wing, ink, 1.0)
    return L


def rouge(shape, f, seed=21):
    """Kohl, and her lips stained the red of crushed rosehip (their lines kept),
    a flush high on her cheeks."""
    L = kohl(shape, f, smoky=0.8, seed=seed)
    lips = blur(f['lips'].astype(np.float32), 2.0)
    lay(L, lips, hexc('#8a1020'), 0.9, pigment(shape, seed, 14, 0.12), through=0.6)
    for c in (CHEEK_R, CHEEK_L):
        flush = np.zeros(shape, np.float32)
        cv2.ellipse(flush, (int(c[0]), int(c[1] - 30)), (130, 64), -14 if c[0] > MID else 14, 0, 360, 1.0, -1)
        lay(L, blur(flush, 44), hexc('#b8343c'), 0.2)
    return L


def woad(shape, f, seed=31):
    """The old blue of the hill people: the left half of her face painted, brow
    to jaw, its edge brushed down her middle and broken where the brush ran
    dry; the paint chalky, the skin's grain through it."""
    L = layer(shape)
    blue = hexc('#21407e')
    grain = pigment(shape, seed, 16, 0.32)
    # Down her middle, a little off it, then out along her jaw: the edge is the brush's.
    top, bottom = 600, 1560
    xs = MID + np.array([18, 6, -4, 10, 0, -10])
    ys = np.linspace(top, bottom, len(xs))
    for k, off in enumerate(np.arange(0, 760, 70)):
        pts = [(x + off + (k % 2) * 8, y) for x, y in zip(xs, ys)]
        w = [96, 104, 100, 104, 96, 70]
        c = stroke(shape, pts, w, dry=0.35 if k == 0 else 0.15, streaks=0.8, soft=0.16, seed=seed + k, taper=(0.02, 0.06), streak_px=2.6, edge=0.4 if k == 0 else 0.15)
        lay(L, c, blue, 0.95, grain, through=0.35)
    # (none of it in her eye's opening, where her eye shows; the brush ran over her lid)
    return L


def ochre(shape, f, seed=41):
    """A band of red earth across the eyes, temple to temple, laid on with two
    fingers: thick where they began at the bridge of her nose, thinning and
    breaking up as they were drawn out to each temple."""
    L = layer(shape)
    red = hexc('#7e2a14')
    grain = pigment(shape, seed, 20, 0.3)
    ey = (f['holes'][0].nonzero()[0].mean() + f['holes'][1].nonzero()[0].mean()) / 2
    for side, out in enumerate((-1, 1)):
        for k, dy in enumerate((-34, 30)):
            pts = [(MID - out * 20, ey + dy - 8), (MID + out * 200, ey + dy - 10), (MID + out * 420, ey + dy - 2), (MID + out * 620, ey + dy + 22)]
            c = stroke(shape, pts, [96, 92, 84, 50], dry=0.65, streaks=0.55, soft=0.3, seed=seed + side * 2 + k, taper=(0.02, 0.35), streak_px=8, edge=0.45)
            lay(L, c, red, 0.92, grain, through=0.45)
    return L


def ash(shape, f, seed=51):
    """Grey from a dead fire, thumbed under each eye and dragged down the cheek:
    thick where the thumb pressed, smeared thin as it was drawn down."""
    L = layer(shape)
    grey = hexc('#9a958e')
    for side, hole in enumerate(f['holes']):
        ys, xs = np.nonzero(hole)
        out = 1 if side == 1 else -1
        x, y = xs.mean() + out * 10, ys.max() + 18
        pts = [(x - out * 60, y + 4), (x, y + 18), (x + out * 30, y + 120), (x + out * 46, y + 230)]
        c = stroke(shape, pts, [96, 110, 92, 40], dry=0.7, streaks=0.5, soft=0.5, seed=seed + side, taper=(0.08, 0.6), streak_px=11, edge=0.55)
        lay(L, c, grey, 0.85, pigment(shape, seed + 5, 9, 0.55), through=0.5)
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
        c = stroke(shape, pts, [74, 78, 72, 62, 22], dry=0.55, streaks=0.4, soft=0.22, seed=seed + k, taper=(0.03, 0.5), streak_px=6, edge=0.35)
        lay(L, c, hexc('#5c0a0c'), 0.9, pigment(shape, seed + 7 + k, 12, 0.3), through=0.4)
        rim = np.clip(c * (1 - c) * 4, 0, 1) * (c > 0.05)
        lay(L, blur(rim.astype(np.float32), 1.0), hexc('#2e0405'), 0.6)
    return L


def gilt(shape, f, seed=71):
    """Flakes of gold leaf over her cheekbones and down the bridge of her nose:
    torn edges, the larger laid close on the bone, smaller scattered further out."""
    L = layer(shape)
    rng = np.random.default_rng(seed)
    gold = hexc('#d9aa4c')
    spots = []
    for c in (CHEEK_R, CHEEK_L):
        out = 1 if c[0] > MID else -1
        for _ in range(34):
            r = rng.random() ** 1.3
            a = rng.uniform(0, 2 * np.pi)
            spots.append((c[0] + out * 20 + np.cos(a) * r * 190, c[1] - 40 + np.sin(a) * r * 80 - out * np.cos(a) * r * 30, 10 + 42 * (1 - r) ** 1.5 * rng.uniform(0.4, 1)))
    for _ in range(12):
        spots.append((MID + rng.normal(0, 16), rng.uniform(900, 1080), 8 + 22 * rng.random()))
    for x, y, s in spots:
        n = rng.integers(6, 11)
        ang = np.sort(rng.uniform(0, 2 * np.pi, n))
        rad = s * rng.uniform(0.45, 1.0, n)
        squash = rng.uniform(0.55, 1.0)
        rot = rng.uniform(0, np.pi)
        px, py = np.cos(ang) * rad, np.sin(ang) * rad * squash
        poly = np.c_[x + px * np.cos(rot) - py * np.sin(rot), y + px * np.sin(rot) + py * np.cos(rot)].astype(np.int32)
        m = np.zeros(shape, np.uint8)
        cv2.fillPoly(m, [poly], 1, cv2.LINE_AA)
        tone = rng.uniform(0.82, 1.08)
        lay(L, m.astype(np.float32), [g * tone for g in gold], 1.0)
    return L


'''
s = s[:a] + designs + s[b:]
# The skin's own grain through paint laid thin: its light and dark about its local mean.
s = s.replace('''def lay(dst, cov, colour, alpha=1.0, grain=None):
    """Paint of a colour laid over what is there, as much as `cov` says."""
    a = np.clip(cov * alpha, 0, 1)
    if grain is not None:
        a = a * grain
    col = np.array(colour, np.float32)
    out_a = a + dst[..., 3] * (1 - a)
    rgb = (col[None, None, :3] * a[..., None] + dst[..., :3] * dst[..., 3:4] * (1 - a[..., None])) / np.maximum(out_a[..., None], 1e-6)''',
'''DETAIL = None   # her skin's grain (its light about its local mean), set from her paint


def lay(dst, cov, colour, alpha=1.0, grain=None, through=0.0):
    """Paint of a colour laid over what is there, as much as `cov` says; laid
    thin (`through`), her skin's grain (pores, freckles, the lines of her lips)
    shows in it."""
    a = np.clip(cov * alpha, 0, 1)
    if grain is not None:
        a = a * grain
    col = np.array(colour, np.float32)[None, None, :3]
    if through > 0 and DETAIL is not None:
        col = col * (1 + (DETAIL[..., None] - 1) * through)
    out_a = a + dst[..., 3] * (1 - a)
    rgb = (col * a[..., None] + dst[..., :3] * dst[..., 3:4] * (1 - a[..., None])) / np.maximum(out_a[..., None], 1e-6)''')
s = s.replace('''    shape = ref.shape[:2]
    f = features(ref, eyes)''', '''    shape = ref.shape[:2]
    f = features(ref, eyes)
    lum = (ref @ np.array([0.3, 0.59, 0.11], np.float32)).astype(np.float32)
    DETAIL = np.clip(lum / np.maximum(blur(lum, 12), 1e-3), 0.6, 1.4)''')
# The eyes' openings smoothed: the socket's paint is ragged, a lash line is not.
s = s.replace('''        hole = cv2.morphologyEx((lab == k).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        holes.append(hole.astype(bool))''', '''        hole = cv2.morphologyEx((lab == k).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        hole = blur(hole.astype(np.float32), 5) > 0.5
        holes.append(hole)''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
