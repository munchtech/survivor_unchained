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


rep('''        elif kind == "fine":''', '''        elif kind == "cloud":
            g = F.fbm(N, N, scale=110, octaves=4, gain=0.6, seed=13)
        elif kind == "fine":''')
rep('''            hue=None):''', '''            hue=None, soft=0.0):''')
rep('''        `grain` (units) roughens its face with the surface's grain of `kind`."""
        c = cov(sd)''', '''        `grain` (units) roughens its face with the surface's grain of `kind`. `soft` (units)
        feathers its edge (smoke, mist): it fades out over that width instead of ending."""
        c = cov(sd) if not soft else np.clip(sd / soft, 0, 1).astype(np.float32)''')
rep('''        self.s.height = np.where(c > 0.5, np.maximum(self.s.height if z is None else h * 0, h), self.s.height)''',
    '''        self.s.height = np.where(c > (0.02 if soft else 0.5), np.maximum(self.s.height if z is None else h * 0, h), self.s.height)''')

replace_fn('wraith', '''
def d_wraith():
    """Wraith Walk: an empty hood and its shroud, the hem torn to rags that stream aside
    and thin into the barrow's light, two points of light where a face should be."""
    e = Emblem("shadow", 0.95, (50, 51))
    cloth = mat("#201a2c", 0.0, 0.7)
    body = poly([(50, 6), (60, 12), (67, 24), (70, 38), (76, 48), (84, 60), (82, 70), (90, 80), (78, 80), (80, 92), (68, 84),
                 (62, 96), (56, 84), (46, 94), (42, 82), (32, 90), (32, 78), (20, 84), (24, 70), (16, 62), (24, 48), (30, 38),
                 (33, 24), (40, 12)])
    e.lay(body, cloth, 6, 9, grain=0.7, kind="cloud")
    # Folds falling from the shoulders into the rags.
    for pts in ([(36, 50), (32, 66), (28, 80)], [(44, 60), (42, 74), (40, 86)], [(56, 62), (58, 76), (60, 88)],
                [(64, 50), (70, 64), (76, 76)]):
        e.lay(stroke(pts, 3.2, 0.6), mat("#0a080e", 0.0, 0.8), 0.3, 1.6, z=5.6)
        e.lay(stroke([(x + 2.2, y) for x, y in pts], 2.0, 0.4), mat("#3c3252", 0.0, 0.6), 6.6, 1.0)
    # The hood's opening, its rolled edge, and the dark inside it.
    e.lay(cut(ellipse(50, 34, 14, 18), ellipse(50, 35.5, 10, 14)), mat("#3c3252", 0.0, 0.6), 8, 2.6, grain=0.3, kind="cloud")
    e.lay(ellipse(50, 35.5, 10, 14), mat("#000000", 0.0, 0.9), 0.5, 1, z=0.5)
    for x in (45.8, 54.2):
        e.lay(ellipse(x, 33, 2.0, 1.2, -10 if x < 50 else 10), "glow", 1, 1, light=2.6, z=1)
    # Where the rags end they are not cloth any more but light.
    for x, y, dx, dy in ((90, 80, 1, 0.3), (80, 92, 0.5, 1), (62, 96, 0, 1), (46, 94, -0.2, 1), (32, 90, -0.5, 1),
                         (20, 84, -1, 0.6), (16, 62, -1, 0)):
        e.lay(stroke([(x - dx * 7, y - dy * 7), (x + dx * 3, y + dy * 3)], 1.8, 0.2), "glow", 0.5, 0.6, light=0.9)
    return e
''')

replace_fn('feint', '''
def d_feint():
    """Fen Step: the thrust that meets nothing: a blade driven in, and the way round its point
    that the body took, in streaks of fen-mist ending in a point."""
    e = Emblem("physical", 0.88, (50, 52))
    path = bez((88, 84), (102, 46), (82, 8), (42, 14), 40)
    e.lay(stroke(path[:-3], 0.6, 6.0), "glow", 1, 2, light=1.1)
    for k, dr in enumerate((6.5, 12)):
        side = bez((88 + dr * 0.5, 80), (102 + dr, 44), (82 + dr * 0.3, 6 - dr), (48 - dr * 0.2, 10 - dr * 0.7), 40)
        e.lay(swell(side, 2.6 - k * 0.8, 0.3), "glow", 0.5, 1, light=0.7 - k * 0.2)
    tip, back = np.array(path[-1]), np.array(path[-5])
    dvec = (tip - back) / np.linalg.norm(tip - back)
    nvec = np.array([-dvec[1], dvec[0]])
    e.lay(poly([tuple(tip + dvec * 6), tuple(back + nvec * 7), tuple(back - nvec * 7)]), "glow", 1, 2, light=1.4)
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
    cloud = soft_union([circle(x, y, r) for x, y, r in puffs], 7)
    e.lay(cloud, mat("#6c6478", 0.0, 0.95), 4, 18, grain=3.0, kind="cloud", soft=3.0)
    # Light on the crowns of the billows, from the upper left.
    for x, y, r in puffs:
        e.lay(circle(x - r * 0.3, y - r * 0.35, r * 0.6), mat("#9890a8", 0.0, 0.95), 0.8, r * 0.6, soft=r * 0.5)
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

rep('''    t1 = bez((10, 14), (34, 6), (24, 46), (50, 54), 40)
    e.lay(stroke(t1, 3.0, 7.0), mat("#1c1428", 0.0, 0.6), 4, 2.5, grain=0.4, light=0.15)
    e.lay(stroke(t1, 0.8, 2.6), "glow", 0.5, 1.2, light=1.4, z=4)
    e.lay(poly([(46, 50), (58, 54), (50, 60)]), mat("#1c1428", 0.0, 0.5), 7.8, 1.5, light=0.2)''', '''    t1 = bez((10, 14), (34, 6), (24, 46), (50, 54), 40)
    e.lay(stroke(t1, 4.0, 9.0), mat("#1c1428", 0.0, 0.6), 4.5, 3, grain=0.4, light=0.15)
    e.lay(stroke(t1, 1.0, 3.0), "glow", 0.5, 1.2, light=1.4, z=4.5)
    e.lay(poly([(44, 48), (60, 54), (56, 58), (50, 62)]), mat("#1c1428", 0.0, 0.5), 7.8, 1.5, light=0.2)''')
rep('''    e.lay(ellipse(54, 46, 4, 6, -30), mat("#ff8a8a", 0.0, 0.1), 0.6, 1, z=7, light=0.2)
''', '''    e.lay(ellipse(55, 47, 2.4, 4, -30), mat("#ff9a9a", 0.0, 0.1), 0.4, 1, z=7.2)
''')
rep('''        e.lay(circle(x, y, 2.2), "glow", 1, 1, light=2.0, z=5, hue="#ff3a2a")''', '''        e.lay(circle(x, y, 1.7), "glow", 1, 1, light=2.0, z=5, hue="#ff3a2a")''')
rep('''        e.lay(circle(x, y, 1.6), "glow", 1, 1, light=1.8, z=5, hue="#ff3a2a")''', '''        e.lay(circle(x, y, 1.2), "glow", 1, 1, light=1.8, z=5, hue="#ff3a2a")''')
rep('''    "wraith": "an empty hooded shroud of tattered black cloth leaning forward as if walking, its torn hem streaming back "
              "and dissolving into violet light, a black void inside the hood with two small glowing violet eyes",''',
    '''    "wraith": "an empty hooded shroud of tattered dark cloth floating, its torn hem streaming into rags that dissolve "
              "into violet light, a black void inside the hood with two small glowing violet eyes",''')
rep('''    "feint": "a steel dagger thrusting up, three pale streaks of mist sweeping past in an arch over its point",''',
    '''    "feint": "a steel dagger thrusting up, a curved arrow of pale mist sweeping round past its point",''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
