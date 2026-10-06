p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\emblems.py'
s = open(p, encoding='utf-8').read()


def replace_fn(name, code):
    global s
    i0 = s.index(f'def d_{name}():')
    i1 = s.index('\ndef ', i0 + 10)
    s = s[:i0] + code.strip('\n') + '\n\n' + s[i1:]


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


# An emission colour of its own (a red drop on a violet tendril).
rep('''    def lay(self, sd, mat_, height=3.0, bevel=2.0, round_=True, tint=None, light=0.0, z=None, grain=0.0, kind="rough"):''',
    '''    def lay(self, sd, mat_, height=3.0, bevel=2.0, round_=True, tint=None, light=0.0, z=None, grain=0.0, kind="rough",
            hue=None):''')
rep('''        if isinstance(mat_, str) and mat_.startswith("glow"):
            core, edge = SCHOOL[self.school]''', '''        if isinstance(mat_, str) and mat_.startswith("glow"):
            core, edge = (hue, hue) if hue else SCHOOL[self.school]''')

rep('''def resample(pts, step):''', '''def crack_web(cx, cy, rx, ry, rot_, n=7, seed=3, rings=(0.38, 0.7)):
    """Glass broken from a point: cracks running out to the rim, and broken rings between
    them. Returns polylines (design units)."""
    rng = np.random.default_rng(seed)
    c, s_ = math.cos(math.radians(rot_)), math.sin(math.radians(rot_))
    angs = np.sort(np.linspace(0, 2 * math.pi, n, endpoint=False) + rng.uniform(-0.3, 0.3, n) + rng.uniform(0, 1))
    radials = []
    for a in angs:
        ca, sa = math.cos(a), math.sin(a)
        R = 1 / math.sqrt((ca / rx) ** 2 + (sa / ry) ** 2)
        pts = []
        for f in np.linspace(0.06, 1.02, 7):
            j = a + rng.uniform(-0.1, 0.1) * (f > 0.1)
            lx, ly = R * f * math.cos(j), R * f * math.sin(j)
            pts.append((cx + lx * c - ly * s_, cy + lx * s_ + ly * c))
        radials.append(pts)
    lines = list(radials)
    for f in rings:
        k = int(f * 6)
        for i in range(len(radials)):
            if rng.random() < 0.7:
                a, b = radials[i][k], radials[(i + 1) % len(radials)][k]
                mid = ((a[0] + b[0]) / 2 + rng.uniform(-1, 1), (a[1] + b[1]) / 2 + rng.uniform(-1, 1))
                lines.append([a, mid, b])
    return lines


def resample(pts, step):''')

replace_fn('mirror', '''
def d_mirror():
    """Mirror Step: a hand mirror of the binders' gold, its dark glass broken from one blow
    and a piece of it flying loose (a reflection bursts when it breaks)."""
    e = Emblem("arcane", 0.9, (50, 50))
    a = -24

    def R(pts):
        return rot(pts, a, 46, 40)

    glass = ellipse(46, 40, 21, 27, a)
    frame = cut(ellipse(46, 40, 27, 33, a), ellipse(46, 40, 21.5, 27.5, a))
    e.lay(stroke(R([(46, 72), (46, 95)]), 9.5, 7.5), "leather", 4, 3.5, grain=0.5, kind="fine")
    for y in (79, 85, 91):
        e.rope(R([(41.5, y), (51, y)]), 2.0, "gold_dim", 4.6)
    e.lay(circle(*R([(46, 97)])[0], 5.2), "gold_dim", 5, 3, grain=0.4, kind="hammer")
    e.lay(stroke(R([(46, 70), (46, 75)]), 14), "gold_dim", 5, 2, grain=0.4, kind="hammer")
    # Dark glass with the other side's light deep in it; the cracks let it out.
    e.lay(glass, mat("#140a20", 0.0, 0.04), 2, 8, light=0.1)
    e.lay(ellipse(*R([(36, 24)])[0], 4, 9, a - 20), mat("#d8c8ff", 0.0, 0.1), 0.5, 1, z=2, light=0.25)
    hit = R([(52, 48)])[0]
    for i, line in enumerate(crack_web(hit[0], hit[1], 21, 27, a, n=8, seed=4)):
        w = 1.8 if i < 8 else 1.0
        e.lay(inter(stroke(line, w, w * 0.45), glass), "glow", 0.5, 0.6, light=2.0 if i < 8 else 1.4, z=2)
    e.lay(circle(hit[0], hit[1], 2.2), "glow", 0.5, 1, light=2.6, z=2)
    hole = poly([(hit[0] + 1, hit[1] + 2), (hit[0] + 9, hit[1] + 3), (hit[0] + 6, hit[1] + 10)])
    e.lay(hole, mat("#030105", 0.0, 0.9), 0.3, 0.5, z=0.5)
    e.lay(frame, "gold", 5, 2.5, grain=0.35, kind="hammer")
    e.rope(ellipse_pts(46, 40, 24.2, 30.2, a, 160), 2.1, "gold", 6.2)
    for t in (45, 135, 225, 315):
        p = R([(46 + 24 * math.sin(math.radians(t)), 40 - 30 * math.cos(math.radians(t)))])[0]
        e.lay(circle(p[0], p[1], 2.8), "gold", 8, 2)
    shard = poly([(76, 70), (88, 64), (84, 80)])
    e.lay(shard, mat("#2a1440", 0.0, 0.05), 2, 2, round_=False, light=0.3)
    e.lay(stroke([(77, 70), (87, 65)], 1.2), "glow", 0.5, 0.5, light=1.8, z=2)
    for x, y, r in ((70, 64, 1.1), (92, 74, 0.9), (80, 86, 0.8)):
        e.lay(circle(x, y, r), "glow", 0.5, 0.5, light=1.6)
    return e
''')

replace_fn('wraith', '''
def d_wraith():
    """Wraith Walk: an empty hood leaning into its walk, its shroud sweeping back and torn
    to rags that thin into the barrow's light, two points of light where a face should be."""
    e = Emblem("shadow", 0.94, (47, 52))
    cloth = mat("#1c1626", 0.0, 0.75)
    shroud = poly([(52, 9), (66, 14), (76, 26), (80, 42), (78, 56), (72, 66), (68, 78), (60, 92), (55, 82), (49, 95), (45, 80),
                   (36, 90), (34, 76), (22, 84), (25, 70), (10, 74), (18, 62), (5, 58), (17, 52), (8, 42), (22, 40), (20, 30),
                   (32, 28), (36, 17)])
    e.lay(shroud, cloth, 6, 7, grain=1.0)
    # The folds: the cloth's creases running back from the hood into the rags.
    for pts in (bez((50, 60), (40, 62), (28, 64), (16, 64), 20), bez((54, 70), (46, 76), (40, 80), (36, 86), 20),
                bez((46, 50), (36, 48), (26, 46), (14, 44), 20), bez((62, 72), (60, 80), (56, 84), (52, 90), 16)):
        e.lay(stroke(pts, 2.6, 0.6), mat("#0a080e", 0.0, 0.8), 0.3, 1.2, z=5.2)
        e.lay(stroke([(x + 1.6, y - 1.6) for x, y in pts], 1.6, 0.4), mat("#3a3050", 0.0, 0.7), 6.4, 0.8)
    e.lay(cut(ellipse(64, 40, 13, 17, 14), ellipse(65, 41, 9.5, 13.5, 14)), mat("#3a3050", 0.0, 0.6), 8, 2.4, grain=0.6)
    e.lay(ellipse(65, 41, 9.5, 13.5, 14), mat("#000000", 0.0, 0.9), 0.5, 1, z=0.5)
    for x, y in ((61.5, 39), (69, 40.5)):
        e.lay(ellipse(x, y, 1.9, 1.2, 10), "glow", 1, 1, light=2.6, z=1)
    # Where the rags end they are not cloth any more but light.
    for x, y, dx, dy in ((60, 92, 0, 1), (49, 95, -0.3, 1), (36, 90, -0.6, 1), (22, 84, -1, 0.6), (10, 74, -1, 0.3),
                         (5, 58, -1, 0), (8, 42, -1, -0.2)):
        e.lay(stroke([(x - dx * 6, y - dy * 6), (x + dx * 3, y + dy * 3)], 1.6, 0.2), "glow", 0.5, 0.6, light=0.8)
    return e
''')

replace_fn('leap', '''
def d_leap():
    """Crashing Leap: the leap's arc of light coming down hard into the ground, the ground
    breaking in a ring, its cracks glowing, stones thrown up."""
    e = Emblem("physical", 0.95, (50, 50))
    gx, gy = 60, 78
    e.lay(ellipse(gx - 4, gy + 2, 40, 11), mat("#3a3228", 0.0, 0.9), 2, 3, grain=1.0)
    e.lay(cut(ellipse(gx, gy, 26, 8), ellipse(gx, gy - 0.5, 18.5, 5)), mat("#7a6a54", 0.0, 0.8), 3.4, 2, grain=0.9)
    e.lay(ellipse(gx, gy, 18.5, 5), mat("#1a1612", 0.0, 0.9), 0.5, 1, z=0.4)
    for ang in (-80, -50, -20, 10, 40, 70, 100, 130, -110, -140):
        a = math.radians(ang)
        pts = [(gx + 4 * math.sin(a), gy + 1.2 * math.cos(a)), (gx + 18 * math.sin(a) + 1, gy + 5 * math.cos(a)),
               (gx + 34 * math.sin(a), gy + 9.5 * math.cos(a) + 1)]
        e.lay(stroke(pts, 1.8, 0.4), "glow", 0.5, 0.6, light=1.1, z=2.5)
    for j, (dx, dy, s) in enumerate(((-26, -12, 4.6), (-18, -24, 3.4), (-32, -2, 3.0), (22, -14, 5.0), (30, -26, 3.4),
                                     (14, -30, 2.6), (34, -6, 2.8), (-8, -34, 2.2))):
        e.lay(rock(gx + dx, gy + dy, s, j * 7), mat("#8a7a62", 0.0, 0.75), 3, 2, grain=0.6)
    path = bez((8, 70), (12, 18), (46, 2), (gx, gy - 4), 60)
    e.lay(stroke(path, 0.6, 11), "glow", 1, 4, light=1.2)
    e.lay(stroke(path[20:], 0.4, 4.5), "glow", 1, 2, light=2.0, z=1)
    e.lay(ellipse(gx, gy - 1, 11, 4), "glow", 1, 2, light=2.6)
    return e
''')

replace_fn('feint', '''
def d_feint():
    """Fen Step: the thrust that meets nothing: a blade driven in, and over its point the
    swerve of what it missed, gone by in three streaks of fen-mist."""
    e = Emblem("physical", 0.88, (50, 52))
    for k, (dr, w, li) in enumerate(((0, 6.5, 1.1), (7, 3.6, 0.8), (13, 2.2, 0.55))):
        pts = bez((92 + dr * 0.2, 80), (104 + dr, 40), (80 + dr * 0.4, 6 - dr), (40 - dr * 0.6, 14 - dr * 0.8), 40)
        e.lay(swell(pts, w, 0.3), "glow", 1, 2, light=li)
    blade = poly([(26, 80), (21, 75), (58, 42), (68, 33), (63, 45)])
    e.lay(blade, "steel", 5, 3, grain=0.3, kind="hammer")
    e.lay(stroke([(23, 78), (60, 44)], 1.2), "iron_dark", 5.5, 0.6)
    e.lay(stroke([(14, 70), (30, 86)], 5.5), "gold_dim", 6, 2.5, grain=0.4, kind="hammer")
    e.lay(stroke([(22, 78), (12, 88)], 6, 5), "leather", 5, 3, grain=0.5, kind="fine")
    e.rope([(20, 80), (13, 87)], 2.0, "gold_dim", 6)
    e.lay(circle(10, 90, 4), "gold_dim", 6, 2.5, grain=0.4, kind="hammer")
    return e
''')

replace_fn('smoke', '''
def d_smoke():
    """Smoke Bomb: a clay smoke-pot of the Dig, burst open, its smoke boiling up and out."""
    e = Emblem("shadow", 0.92, (50, 48))
    puffs = [(50, 56, 8), (43, 47, 10), (57, 41, 11), (45, 30, 12), (61, 24, 10), (34, 21, 9), (52, 13, 9), (71, 15, 6.5),
             (29, 35, 7), (68, 34, 7.5), (38, 10, 5), (78, 26, 4.5)]
    e.lay(soft_union([circle(x, y, r) for x, y, r in puffs], 7), mat("#6c6478", 0.0, 0.95), 3.5, 16, grain=1.8)
    # Each billow's crown catches more light than the hollows between them.
    for x, y, r in puffs:
        e.lay(circle(x - r * 0.25, y - r * 0.3, r * 0.55), mat("#8a8296", 0.0, 0.95), 1.2, r * 0.55, grain=0.8)
    pot = circle(50, 76, 16)
    e.lay(pot, mat("#5a3424", 0.0, 0.6), 8, 10, grain=0.6, kind="fine")
    lip = poly([(37, 66), (40, 59), (44, 63), (48, 57), (53, 62), (58, 57), (62, 62), (64, 66), (60, 68), (40, 68)])
    e.lay(lip, mat("#7a4a32", 0.0, 0.6), 8.5, 1.5, grain=0.4, kind="fine")
    e.lay(ellipse(50, 64.5, 10, 2.4), "glow", 1, 1, light=1.2, z=8)
    e.lay(stroke([(35, 75), (65, 75)], 2.4), mat("#2a1810", 0.0, 0.7), 1, 1, z=7.6)
    for crk in ([(42, 82), (46, 76), (44, 72), (50, 68)], [(58, 88), (60, 80), (64, 77)]):
        e.lay(stroke(crk, 1.8, 0.8), "glow", 0.5, 0.6, light=1.3, z=8)
    return e
''')

replace_fn('tether', '''
def d_tether():
    """Grave Tether: a tendril of the barrow's shadow hooked into a heart, what it takes
    running back along it in drops of red."""
    e = Emblem("shadow", 0.92, (54, 52))
    e.lay(heart_shape(62, 58, 26), mat("#7a0c18", 0.0, 0.25), 7, 9, grain=0.5, kind="fine", light=0.35)
    e.lay(stroke(bez((54, 42), (50, 52), (54, 64), (62, 74), 20), 1.4, 0.6), mat("#2a0206", 0.0, 0.4), 7.6, 0.6)
    e.lay(ellipse(54, 46, 4, 6, -30), mat("#ff8a8a", 0.0, 0.1), 0.6, 1, z=7, light=0.2)
    t1 = bez((10, 14), (34, 6), (24, 46), (50, 54), 40)
    e.lay(stroke(t1, 3.0, 7.0), mat("#1c1428", 0.0, 0.6), 4, 2.5, grain=0.4, light=0.15)
    e.lay(stroke(t1, 0.8, 2.6), "glow", 0.5, 1.2, light=1.4, z=4)
    e.lay(poly([(46, 50), (58, 54), (50, 60)]), mat("#1c1428", 0.0, 0.5), 7.8, 1.5, light=0.2)
    t2 = bez((8, 46), (22, 40), (30, 70), (48, 70), 40)
    e.lay(stroke(t2, 1.6, 4.2), mat("#1c1428", 0.0, 0.6), 4, 2, grain=0.4)
    e.lay(stroke(t2, 0.4, 1.6), "glow", 0.5, 1, light=1.1, z=4)
    for i in (8, 18, 28):
        x, y = t1[i]
        e.lay(circle(x, y, 2.2), "glow", 1, 1, light=2.0, z=5, hue="#ff3a2a")
    for i in (12, 26):
        x, y = t2[i]
        e.lay(circle(x, y, 1.6), "glow", 1, 1, light=1.8, z=5, hue="#ff3a2a")
    return e
''')

replace_fn('expand', '''
def d_expand():
    """Ford Lamp: a lamp of the Waystation's lamp-iron, its light thrown wide round it."""
    e = Emblem("holy")
    for k in range(16):
        a = k * 22.5
        e.lay(stroke(arc(50, 50, 42, a - 7, a + 7, 10), 2.0, 2.0), "glow", 1, 1, light=0.45)
    e.lay(poly([(37, 34), (63, 34), (62, 70), (38, 70)]), "glow", 2, 6, light=0.8)
    e.lay(flame_tongue(50, 66, 13, 26, lean=1), "glow", 2, 3, light=2.0, z=2)
    for x0, x1 in ((36, 37), (50, 50), (64, 63)):
        e.lay(stroke([(x0, 32), (x1, 72)], 2.6), "iron", 6, 1.2, grain=0.4, kind="hammer")
    e.lay(poly([(32, 34), (68, 34), (60, 22), (40, 22)]), "iron", 6, 2, grain=0.5, kind="hammer")
    e.lay(stroke([(30, 34), (70, 34)], 3.6), "iron_dark", 7, 1.5)
    e.lay(cut(circle(50, 14, 7.5), circle(50, 14, 4.6)), "iron", 6, 1.4, grain=0.4, kind="hammer")
    e.lay(poly([(30, 72), (70, 72), (64, 82), (36, 82)]), "iron", 6, 2, grain=0.5, kind="hammer")
    e.lay(stroke([(28, 72), (72, 72)], 3.6), "iron_dark", 7, 1.5)
    for sx in (-1, 1):
        e.lay(stroke([(50 + sx * 17, 28), (50 + sx * 24, 24), (50 + sx * 27, 19), (50 + sx * 24, 15), (50 + sx * 21, 18)],
                     2.2, 1.2), "iron", 6, 1)
    e.lay(circle(50, 87, 2.4), "gold_dim", 6, 1.5)
    return e
''')

replace_fn('umbral', '''
def d_umbral():
    """Umbral Bolt: a bolt of shadow tearing straight through, barbed in black iron, the dark
    streaming behind it and the air torn round it in rings."""
    e = Emblem("shadow", 0.92, (48, 52))
    o, d, n = np.array([60.0, 40.0]), np.array([1, -1]) / math.sqrt(2), np.array([1, 1]) / math.sqrt(2)

    def P(*uv):
        return [tuple(o + u * d + v * n) for u, v in uv]

    dark = mat("#141020", 0.4, 0.4)
    e.lay(poly(P((-24, 0), (-66, -14), (-56, -3), (-70, 0), (-56, 3), (-66, 14))), mat("#1a1428", 0.0, 0.8), 3, 5, grain=1.2,
          light=0.15)
    for v in (-1, 1):
        e.lay(stroke(P((-26, 4 * v), (-64, 13 * v)), 1.6, 0.3), "glow", 0.5, 0.8, light=0.9)
    e.lay(stroke(P((-28, 0), (-70, 0)), 1.4, 0.3), "glow", 0.5, 0.8, light=0.7)
    for u, r in ((-14, 12), (-30, 9)):
        c = P((u, 0))[0]
        e.lay(cut(ellipse(c[0], c[1], 3.4, r, -45), ellipse(c[0], c[1], 2.0, r - 2.0, -45)), "glow", 0.5, 0.6, light=0.9)
    e.lay(stroke(P((-40, 0), (-4, 0)), 5.6), dark, 5, 2.4, grain=0.4, kind="hammer")
    for v in (-1, 1):
        e.lay(poly(P((-42, 0), (-36, 8 * v), (-26, 8 * v), (-30, 0))), mat("#241a34", 0.0, 0.7), 5.5, 1.5, grain=0.6)
    head = poly(P((30, 0), (2, -13), (7, -4.5), (-6, -4), (-6, 4), (7, 4.5), (2, 13)))
    e.lay(head, mat("#141020", 0.6, 0.3), 7, 4, grain=0.4, kind="hammer", light=0.12)
    for v in (-1, 1):
        e.lay(stroke(P((29, 0), (3, 12 * v)), 1.8, 0.9), "glow", 1, 0.8, light=1.9, z=7)
    e.lay(stroke(P((24, 0), (-2, 0)), 1.4, 0.4), "glow", 1, 0.6, light=1.2, z=7)
    return e
''')

s = s.replace('''    "wraith": "an empty hooded shroud of tattered black cloth leaning forward, its rags streaming back and dissolving "
              "into violet mist, a black void inside the hood with two small glowing violet eyes",''', '''    "wraith": "an empty hooded shroud of tattered black cloth leaning forward as if walking, its torn hem streaming back "
              "and dissolving into violet light, a black void inside the hood with two small glowing violet eyes",''')
s = s.replace('''    "leap": "a heavy forged iron spike driven down into cracked ground, the ground breaking in a ring with glowing "
            "cracks, rocks and dust thrown up either side",''', '''    "leap": "a bright arc of white light leaping high and crashing down into the ground, the ground breaking in a "
            "crater with glowing cracks, rocks and dust thrown up",''')
s = s.replace('''    "feint": "a steel dagger thrusting into a curling wisp of pale mist that swirls away round its point",''',
              '''    "feint": "a steel dagger thrusting up, three pale streaks of mist sweeping past in an arch over its point",''')
s = s.replace('''    "smoke": "a cracked round clay pot burst open at the top, thick grey-violet smoke boiling up out of it in great curls",''',
              '''    "smoke": "a cracked round clay pot burst open at the top, thick billowing grey-violet smoke boiling up out of it",''')
s = s.replace('''    "tether": "a dark red heart bound in a spiralling coil of glowing violet shadow, the coil reaching away",''',
              '''    "tether": "a dark red heart pierced by a hooked tendril of black shadow with violet light along it, red drops of "
              "blood running back along the tendril",''')
s = s.replace('''    "expand": "an old forged iron lantern with a ring handle, a bright golden flame inside its glass panes, its light "
              "thrown wide in rings round it",''', '''    "expand": "an old forged black iron lantern with a ring handle and scrolled arms, a bright golden flame inside its "
              "glass panes, its light thrown wide in a ring of rays round it",''')
s = s.replace('''    "mirror": "an ornate hand mirror with a twisted gold wire frame and a leather-wrapped handle, its dark violet glass "
              "cracked across with glowing violet light in the cracks, a shard of glass breaking away",''', '''    "mirror": "an ornate hand mirror with a twisted gold wire frame and a leather-wrapped handle, its dark glass "
              "shattered from one point in a web of cracks glowing violet, a shard of glass flying away",''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
