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


replace_fn('horns', '''
def d_horns():
    """Bull Rush: a forged iron bull-helm coming straight at you, its great horns lowered,
    a ring of the binders' gold through its nose, the air rushing past it."""
    e = Emblem("physical", 0.92, (50, 50))
    for ang in range(0, 360, 24):
        a = math.radians(ang + 7)
        r0, r1 = 37 + (ang % 48) / 12, 47
        e.lay(stroke([(50 + r0 * math.sin(a), 50 - r0 * math.cos(a)), (50 + r1 * math.sin(a), 50 - r1 * math.cos(a))], 0.4, 2.0),
              "glow", 0.5, 1, light=0.6)
    for sx in (-1, 1):
        horn = bez((50 + sx * 16, 40), (50 + sx * 34, 36), (50 + sx * 44, 22), (50 + sx * 34, 8), 40)
        e.lay(stroke(horn, 10, 2.0), "bone", 6, 5, grain=0.6)
        for t in (0.15, 0.3):
            p, q = horn[int(t * 39)], horn[int(t * 39) + 2]
            e.lay(stroke([p, q], 9.6 - t * 10), mat("#a89878", 0.0, 0.6), 6.4, 0.6)
    e.lay(ellipse(50, 50, 21, 25), "iron", 6, 6, grain=0.6, kind="hammer")
    e.lay(stroke([(50, 26), (50, 70)], 6, 4.4), "iron_dark", 7, 2, grain=0.4, kind="hammer")
    for sx in (-1, 1):
        e.lay(ellipse(50 + sx * 10, 50, 6.5, 2.2, sx * -10), mat("#020102", 0.0, 0.9), 0.5, 0.6, z=6)
        for y in (34, 42, 58, 64):
            e.lay(circle(50 + sx * 5.5, y, 1.2), "steel", 8, 0.6)
        e.lay(circle(50 + sx * 15, 40, 4.5), "gold_dim", 7.5, 2, grain=0.3, kind="hammer")
    e.lay(cut(circle(50, 76, 7), circle(50, 76, 4.4)), "gold", 9, 1.5, grain=0.3, kind="hammer")
    return e
''')

replace_fn('chain', '''
def d_chain():
    """Grapple Chain: the binders' chain flung out, its links running to an iron grapple
    whose hooks are about to bite."""
    e = Emblem("physical", 0.9, (50, 52))
    path = bez((12, 92), (22, 64), (40, 74), (54, 50), 80)
    P = resample(path, 9.6)
    for i, (x, y) in enumerate(P):
        a, b = P[max(i - 1, 0)], P[min(i + 1, len(P) - 1)]
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if i % 2 == 0:
            e.lay(cut(ellipse(x, y, 7.4, 4.8, ang), ellipse(x, y, 4.6, 2.0, ang)), "iron", 4, 1.8, grain=0.5, kind="hammer")
        else:
            e.lay(ellipse(x, y, 7.4, 2.0, ang), "iron", 5, 1.2, grain=0.4, kind="hammer")
    e.lay(cut(circle(57, 46, 5), circle(57, 46, 2.6)), "iron", 5.5, 1.4, grain=0.4, kind="hammer")
    e.lay(stroke([(60, 43), (74, 29)], 6, 5), "iron", 6, 2.2, grain=0.5, kind="hammer")
    for ang in (-75, 15, 105):
        a = math.radians(ang)
        c, s_ = math.cos(a), math.sin(a)
        b0 = (74 + 2 * c, 29 + 2 * s_)
        hook = bez(b0, (b0[0] + 16 * c, b0[1] + 16 * s_), (b0[0] + 18 * c + 9 * s_, b0[1] + 18 * s_ - 9 * c),
                   (b0[0] + 9 * c + 10 * s_, b0[1] + 9 * s_ - 10 * c), 30)
        e.lay(stroke(hook, 5.0, 1.2), "steel", 6.5, 1.8, grain=0.3, kind="hammer")
    e.lay(circle(74, 29, 5), "iron_dark", 7, 2)
    for x, y in ((84, 40), (66, 14), (88, 22)):
        e.lay(stroke([(x - 4, y + 2), (x + 2, y - 2)], 1.4, 0.3), "glow", 0.5, 0.6, light=1.4)
    return e
''')

replace_fn('wing', '''
def d_wing():
    """Vault: a heron's wing of the fen thrown up in the spring away, and the snares left on
    the ground where you stood."""
    e = Emblem("physical", 0.92, (50, 50))
    for x, y, sz in ((28, 88, 6), (50, 92, 5.4), (72, 87, 6)):
        caltrop(e, x, y, sz)
    pale, grey, dark = mat("#e4dcd0", 0.0, 0.6), mat("#a8a298", 0.0, 0.6), mat("#5a5650", 0.0, 0.6)
    arm = bez((22, 74), (30, 40), (52, 18), (86, 14), 40)
    # Primaries from the far end of the arm, longest at the tip; the secondaries nearer in.
    for k in range(16):
        t = 0.28 + k * 0.045
        root = arm[min(int(t * 39), 39)]
        length = 22 + 24 * t ** 1.4
        ang = 196 - 50 * t
        m = dark if k >= 12 else (grey if k >= 8 else pale)
        feather(e, root, ang, length, 8.5, m)
    e.lay(stroke(arm, 8, 4.4), pale, 5.5, 3.5, grain=0.6, kind="fine")
    for k in range(10):
        t = 0.1 + k * 0.07
        root = arm[int(t * 39)]
        feather(e, (root[0] - 1, root[1] + 2), 200 - 40 * t, 12, 6.5, pale)
    for x, y0 in ((14, 14), (8, 32), (22, 4)):
        e.lay(stroke([(x + 4, y0 + 24), (x, y0)], 2.0, 0.3), "glow", 0.5, 1, light=0.6)
    return e
''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
