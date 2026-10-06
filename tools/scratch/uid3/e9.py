import sys, os
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit, W

edit('tools/assets/heroine_paint.py', [
    # kohl: the smoke thicker
    ("        lay(L, smoke, ink, 0.9, pigment(shape, seed + side, 26, 0.25))", "        lay(L, smoke, ink, 0.97, pigment(shape, seed + side, 26, 0.2))"),
    ("        smoke = (np.clip(1 - dist / reach, 0, 1) ** 0.75 * (dist > 0)).astype(np.float32)", "        smoke = (np.clip(1 - dist / reach, 0, 1) ** 0.6 * (dist > 0)).astype(np.float32)"),
    # woad: a truer blue under firelight, and rougher
    ("    blue = hexc('#183c9e')", "    blue = hexc('#0c48b4')"),
    ("[96, 118, 120, 118, 90], dry=0.45, streaks=0.6, soft=0.28, seed=seed, taper=(0.05, 0.1), streak_px=9, edge=0.5))",
     "[96, 124, 128, 122, 90], dry=0.6, streaks=0.7, soft=0.3, seed=seed, taper=(0.05, 0.12), streak_px=9, edge=0.7))"),
    # ochre: deeper earth
    ("    red = hexc('#a83614')", "    red = hexc('#922a10')"),
    # ash: paler, no mark on the brow
    ("    grey = hexc('#dcd8d0')", "    grey = hexc('#e8e4dc')"),
    ("""    pts = [(MID + 4, 830), (MID, 740), (MID - 6, 620)]
    cov = np.maximum(cov, stroke(shape, pts, [96, 90, 40], dry=0.5, streaks=0.5, soft=0.4, seed=seed + 9, taper=(0.1, 0.6), streak_px=11, edge=0.5))
""", ""),
    ('''    """Pale ash from a dead fire, thumbed under each eye and dragged down the
    cheek, and a thumb's smear up the middle of her brow: thick where the
    thumb pressed, smeared thin as it was drawn."""''', '''    """Pale ash from a dead fire, thumbed under each eye and dragged down the
    cheek: thick where the thumb pressed, smeared thin as it was drawn."""'''),
    ("    lay(L, cov, grey, 0.95, pigment(shape, seed + 5, 9, 0.45), through=0.45)", "    lay(L, cov, grey, 1.0, pigment(shape, seed + 5, 9, 0.35), through=0.3)"),
    # blood: crimson, not rust
    ("        lay(L, c, hexc('#8a0a12'), 0.95, pigment(shape, seed + 7 + k, 12, 0.25), through=0.3)", "        lay(L, c, hexc('#640510'), 0.97, pigment(shape, seed + 7 + k, 12, 0.2), through=0.25)"),
])

# Gilt: leaf pressed in a band along each cheekbone, close enough to read as one band with torn edges.
p = os.path.join(W, 'tools/assets/heroine_paint.py')
s = open(p, encoding='utf-8', newline='').read()
a = s.index('def gilt(shape, f, seed=71):')
b = s.index("DESIGNS = {")
new = '''def gilt(shape, f, seed=71):
    """Gold leaf pressed along the top of each cheekbone, from beside her nose
    out toward the temple: torn pieces laid edge to edge so they read as one
    band, broader at its middle, with a few flecks broken off around it."""
    L = layer(shape)
    rng = np.random.default_rng(seed)
    gold = hexc('#e8bc58')
    spots = []
    for side, hole in enumerate(f['holes']):
        ys, xs = np.nonzero(hole)
        out = 1 if side == 1 else -1
        # The band's line: under the eye's inner corner, along the bone, up toward the temple.
        x0, y0 = xs.mean() - out * 60, ys.max() + 70
        line = spline([(x0, y0), (x0 + out * 90, y0 + 14), (x0 + out * 200, y0 - 6), (x0 + out * 290, y0 - 60)], 200)
        for i in range(70):
            t = rng.random()
            px, py = line[min(int(t * len(line)), len(line) - 1)]
            wide = 26 + 30 * np.sin(np.pi * t)
            spots.append((px + rng.normal(0, 8), py + rng.normal(0, wide * 0.35), (14 + 26 * np.sin(np.pi * t)) * rng.uniform(0.6, 1.1)))
        for _ in range(14):
            t = rng.random()
            px, py = line[min(int(t * len(line)), len(line) - 1)]
            spots.append((px + rng.normal(0, 30), py + rng.normal(0, 40), rng.uniform(4, 10)))
    for x, y, s in spots:
        n = rng.integers(6, 11)
        ang = np.sort(rng.uniform(0, 2 * np.pi, n))
        rad = s * rng.uniform(0.55, 1.0, n)
        squash = rng.uniform(0.6, 1.0)
        rot = rng.uniform(0, np.pi)
        px, py = np.cos(ang) * rad, np.sin(ang) * rad * squash
        poly = np.c_[x + px * np.cos(rot) - py * np.sin(rot), y + px * np.sin(rot) + py * np.cos(rot)].astype(np.int32)
        m = np.zeros(shape, np.uint8)
        cv2.fillPoly(m, [poly], 1, cv2.LINE_AA)
        tone = rng.uniform(0.85, 1.08)
        lay(L, m.astype(np.float32), [g * tone for g in gold], 1.0)
    return L


'''
if '\r\n' in s:
    new = new.replace('\n', '\r\n')
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='').write(s)
print('gilt', len(s))
