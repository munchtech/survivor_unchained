exec(open(__file__.replace('ed9.py', 'edlib.py')).read())
p = 'tools/assets/heroine_paint.py'
s = open(p, encoding='utf-8').read()
def between(s, a, b, new):
    i = s.index(a); j = s.index(b, i)
    return s[:i] + new + s[j:]
s = between(s, 'def woad(', 'def ochre(', r'''def woad(shape, f, seed=31):
    """The old blue of the hill people: the left half of her face painted, brow
    to jaw, solid but for the brush's grain; its edge brushed down her middle
    and broken where the brush ran dry; chalky, the skin's grain through it."""
    L = layer(shape)
    blue = hexc('#21407e')
    grain = pigment(shape, seed, 16, 0.3)
    h, w = shape
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    wob = noise((h, 1), 90, seed)[:, :1] * 30 - 15
    edge = MID + 6 + wob
    # The half: right of her middle (her left), from her brow's top to under her jaw.
    inside = np.clip((xx - edge) / 6, 0, 1) * np.clip((yy - 640) / 50, 0, 1) * np.clip((1560 - yy) / 60, 0, 1)
    # The brush's strokes, down her face: streaks of thicker and thinner paint.
    streak = noise((h, w), 14, seed + 1)
    streak = cv2.resize(cv2.resize(streak, (w, h // 8)), (w, h))
    fill = inside * (0.86 + 0.14 * streak)
    lay(L, fill.astype(np.float32), blue, 0.95, grain, through=0.35)
    # The edge: one dry stroke down her middle, its bristles broken.
    pts = [(MID + 10 + float(wob[int(y)]), y) for y in np.linspace(640, 1560, 6)]
    c = stroke(shape, pts, [60, 64, 60, 64, 60, 40], dry=0.9, streaks=0.9, soft=0.18, seed=seed + 2, taper=(0.03, 0.08), streak_px=2.4, edge=0.5)
    lay(L, c, blue, 0.9, grain, through=0.35)
    return L


''')
s = between(s, 'def ochre(', 'def ash(', r'''def ochre(shape, f, seed=41):
    """A band of red earth across the eyes, temple to temple, laid on with two
    fingers drawn from her right temple to her left: thick where they began,
    thinning and breaking up as the earth ran out."""
    L = layer(shape)
    red = hexc('#7e2a14')
    grain = pigment(shape, seed, 20, 0.3)
    ey = (f['holes'][0].nonzero()[0].mean() + f['holes'][1].nonzero()[0].mean()) / 2
    for k, dy in enumerate((-36, 32)):
        pts = [(TEMPLE_R[0] + 30, ey + dy + 26), (650, ey + dy - 2), (MID, ey + dy - 12), (1450, ey + dy - 2), (TEMPLE_L[0] - 30, ey + dy + 24)]
        c = stroke(shape, pts, [92, 98, 96, 92, 70], dry=0.55, streaks=0.5, soft=0.3, seed=seed + k, taper=(0.04, 0.12), streak_px=8, edge=0.45)
        lay(L, c, red, 0.9, grain, through=0.45)
    return L


''')
s = between(s, 'def ash(', 'def blood(', r'''def ash(shape, f, seed=51):
    """Grey from a dead fire, thumbed under each eye and dragged down the cheek:
    thick where the thumb pressed, smeared thin as it was drawn down."""
    L = layer(shape)
    grey = hexc('#a6a19a')
    for side, hole in enumerate(f['holes']):
        ys, xs = np.nonzero(hole)
        out = 1 if side == 1 else -1
        x, y = xs.mean() + out * 10, ys.max() + 18
        pts = [(x - out * 60, y + 4), (x, y + 18), (x + out * 30, y + 120), (x + out * 46, y + 230)]
        c = stroke(shape, pts, [96, 110, 92, 40], dry=0.6, streaks=0.5, soft=0.45, seed=seed + side, taper=(0.08, 0.6), streak_px=11, edge=0.55)
        lay(L, c, grey, 1.0, pigment(shape, seed + 5, 9, 0.5), through=0.5)
    return L


''')
s = s.replace('''        c = stroke(shape, pts, [74, 78, 72, 62, 22], dry=0.55, streaks=0.4, soft=0.22, seed=seed + k, taper=(0.03, 0.5), streak_px=6, edge=0.35)
        lay(L, c, hexc('#5c0a0c'), 0.9, pigment(shape, seed + 7 + k, 12, 0.3), through=0.4)
        rim = np.clip(c * (1 - c) * 4, 0, 1) * (c > 0.05)
        lay(L, blur(rim.astype(np.float32), 1.0), hexc('#2e0405'), 0.6)''', '''        c = stroke(shape, pts, [60, 66, 60, 52, 18], dry=0.6, streaks=0.4, soft=0.24, seed=seed + k, taper=(0.03, 0.5), streak_px=6, edge=0.45)
        lay(L, c, hexc('#5c0a0c'), 0.9, pigment(shape, seed + 7 + k, 12, 0.3), through=0.4)
        rim = np.clip(c * (1 - c) * 4, 0, 1) * (c > 0.05)
        lay(L, blur(rim.astype(np.float32), 2.0), hexc('#2e0405'), 0.3)''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
