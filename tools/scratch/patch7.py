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


replace_fn('feint', '''
def d_feint():
    """Fen Step: the thrust that meets nothing: a blade standing point up, and the way the body
    went round it, over its point and down the far side, in a streak of fen-mist."""
    e = Emblem("physical", 0.92, (50, 50))
    path = bez((18, 78), (8, 20), (82, 0), (82, 62), 60)
    e.lay(stroke(path[:-4], 0.6, 7.0), "glow", 1, 2.5, light=1.1)
    P = np.asarray(path, np.float32)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Nn = np.stack([-T[:, 1], T[:, 0]], 1)
    for off, w, li in ((-6.5, 2.4, 0.6), (-12, 1.4, 0.4)):
        side = P[6:-10] + Nn[6:-10] * off * np.linspace(0.2, 1, len(P) - 16)[:, None]
        e.lay(stroke(side.tolist(), 0.3, w), "glow", 0.5, 1, light=li)
    tip, back = P[-1], P[-6]
    d = (tip - back) / np.linalg.norm(tip - back)
    n = np.array([-d[1], d[0]])
    e.lay(poly([tuple(tip + d * 7), tuple(back + n * 8), tuple(back - n * 8)]), "glow", 1, 2, light=1.5)
    e.lay(poly([(50, 22), (54.5, 32), (54, 66), (46, 66), (45.5, 32)]), "steel", 5, 3, grain=0.3, kind="hammer")
    e.lay(stroke([(50, 30), (50, 62)], 1.4), "iron_dark", 5.5, 0.6)
    e.lay(stroke([(36, 68), (64, 68)], 5), "gold_dim", 6, 2.4, grain=0.4, kind="hammer")
    for x in (36, 64):
        e.lay(circle(x, 68, 3.2), "gold_dim", 6.5, 2)
    e.lay(stroke([(50, 70), (50, 84)], 5.6, 5), "leather", 5, 3, grain=0.5, kind="fine")
    e.rope([(50, 71), (50, 83)], 2.0, "gold_dim", 6)
    e.lay(circle(50, 88, 4), "gold_dim", 6, 2.5, grain=0.4, kind="hammer")
    return e
''')

rep('''    e.lay(cloud, mat("#6c6478", 0.0, 0.95), 4, 18, grain=3.0, kind="cloud", soft=3.0)
    # Light on the crowns of the billows, from the upper left.
    for x, y, r in puffs:
        e.lay(circle(x - r * 0.3, y - r * 0.35, r * 0.6), mat("#9890a8", 0.0, 0.95), 0.8, r * 0.6, soft=r * 0.5)''',
    '''    e.lay(cloud, mat("#a49cb4", 0.0, 0.95), 4, 18, grain=3.0, kind="cloud", soft=3.0)
    # Light on the crowns of the billows, from the upper left; the pot's light in their feet.
    for x, y, r in puffs:
        e.lay(circle(x - r * 0.3, y - r * 0.35, r * 0.6), mat("#d0c8e0", 0.0, 0.95), 0.8, r * 0.6, soft=r * 0.5)
    e.lay(soft_union([circle(50, 56, 8), circle(43, 47, 7)], 4), mat("#b08ad8", 0.0, 0.9), 0.5, 6, soft=5, light=0.5)''')
rep('''    e.lay(ellipse(50, 64.5, 10, 2.4), "glow", 1, 1, light=1.2, z=8)''', '''    e.lay(ellipse(50, 64.5, 10, 2.4), "glow", 1, 1, light=1.8, z=8)''')
rep('''    "smoke": "a cracked round clay pot burst open at the top, thick billowing grey-violet smoke boiling up out of it",''',
    '''    "smoke": "a cracked round clay pot burst open at the top, thick billowing pale grey smoke boiling up out of it, "
             "violet light glowing from inside the pot",''')

rep('''    for v in (-1, 1):
        e.lay(stroke(P((29, 0), (3, 12 * v)), 1.8, 0.9), "glow", 1, 0.8, light=1.9, z=7)
    e.lay(stroke(P((24, 0), (-2, 0)), 1.4, 0.4), "glow", 1, 0.6, light=1.2, z=7)''', '''    for v in (-1, 1):
        e.lay(stroke(P((29, 0), (3, 12 * v)), 2.8, 1.4), "glow", 1, 0.8, light=2.2, z=7)
    e.lay(stroke(P((24, 0), (-2, 0)), 1.8, 0.6), "glow", 1, 0.6, light=1.6, z=7)
    e.lay(stroke(P((-6, 0), (-40, 0)), 1.6, 0.4), "glow", 1, 0.6, light=1.2, z=5)''')

rep('''    e.lay(ellipse(gx, gy + 1, 15, 4.6), "glow", 1, 2, light=2.4, hue="#ffc070")''',
    '''    e.lay(ellipse(gx, gy + 1, 22, 6.5), "glow", 1, 3, light=2.6, hue="#ffc070")
    for ang in range(-80, 81, 20):
        a = math.radians(ang)
        e.lay(stroke([(gx + 6 * math.sin(a), gy - 2), (gx + 22 * math.sin(a), gy - 16 * math.cos(a) - 2)], 2.6, 0.3), "glow", 1, 1,
              light=1.6, hue="#ffd890")''')

# The other arts, in the same family.
i = s.index('DESIGNS = {k[2:]: f for k, f in globals().items() if k.startswith("d_")}')
s = s[:i] + '''def feather(e, root, ang, length, width, m, z=None):
    """One feather: a long blade of vane round its quill, from `root` at `ang` (0 up, clockwise)."""
    a = math.radians(ang)
    ux, uy = math.sin(a), -math.cos(a)
    tip = (root[0] + ux * length, root[1] + uy * length)
    mid = ((root[0] + tip[0]) / 2, (root[1] + tip[1]) / 2)
    e.lay(ellipse(mid[0], mid[1], width / 2, length / 2, ang), m, 3, width * 0.4, grain=0.4, kind="fine", z=z)
    e.lay(stroke([root, tip], 0.9, 0.3), mat("#8a8070", 0.0, 0.5), 3.4, 0.4, z=z)


def caltrop(e, cx, cy, s):
    """A snare of the road: four iron spikes, one always up."""
    for ang in (0, 120, 240):
        a = math.radians(ang)
        e.lay(poly([(cx + s * math.sin(a), cy + s * 0.45 * math.cos(a)), (cx + s * 0.22 * math.sin(a + 1.6), cy),
                    (cx + s * 0.22 * math.sin(a - 1.6), cy)]), "iron", 3, 1, round_=False, grain=0.3, kind="hammer")
    e.lay(poly([(cx, cy - s * 1.1), (cx - s * 0.2, cy), (cx + s * 0.2, cy)]), "iron", 4, 1, round_=False)
    e.lay(stroke([(cx, cy - s * 1.0), (cx, cy - s * 0.4)], 0.5), "steel", 4.4, 0.3)


def d_boot():
    """Sprint: a road boot of the Waystation's leather, iron-shod, driving forward, the road's
    dust kicked up behind it and the wind of it streaming back."""
    e = Emblem("physical", 0.94, (52, 50))
    for y, x0, w, li in ((30, 6, 2.6, 0.7), (44, 2, 3.2, 0.9), (58, 8, 2.4, 0.6), (70, 16, 1.8, 0.5)):
        e.lay(stroke([(x0, y + 4), (x0 + 30, y)], 0.3, w), "glow", 0.5, 1, light=li)
    e.lay(soft_union([circle(30, 80, 7), circle(22, 76, 5), circle(38, 84, 5), circle(16, 72, 3.5)], 4),
          mat("#8a7a62", 0.0, 0.9), 2, 7, grain=1.6, kind="cloud", soft=3)
    boot = rotated(poly([(40, 12), (64, 12), (64, 54), (66, 60), (84, 64), (90, 70), (88, 78), (40, 78), (38, 62)]), -12, 60, 70)
    e.lay(boot, "leather", 6, 5, grain=0.7, kind="fine")
    e.lay(rotated(stroke([(38, 16), (66, 16)], 5), -12, 60, 70), mat("#5a3a26", 0.0, 0.6), 7, 2, grain=0.5, kind="fine")
    e.lay(rotated(poly([(38, 76), (90, 76), (88, 82), (40, 82)]), -12, 60, 70), "iron", 6.5, 1.5, grain=0.4, kind="hammer")
    e.lay(rotated(poly([(38, 82), (52, 82), (52, 88), (40, 88)]), -12, 60, 70), "iron", 6.5, 1.5, grain=0.4, kind="hammer")
    for y in (26, 34, 42, 50):
        e.lay(rotated(stroke([(56, y), (64, y + 3)], 1.4), -12, 60, 70), mat("#c8b090", 0.0, 0.6), 7.4, 0.6)
    e.lay(rotated(stroke([(40, 58), (66, 58)], 3.6), -12, 60, 70), mat("#2a1810", 0.0, 0.6), 7.2, 1.2)
    e.lay(rotated(poly([(44, 55), (50, 55), (50, 61), (44, 61)]), -12, 60, 70), "gold_dim", 8, 1, grain=0.3, kind="hammer")
    for x in (46, 58, 70, 82):
        e.lay(rotated(circle(x, 79, 1.1), -12, 60, 70), "steel", 7.6, 0.6)
    return e


def d_horns():
    """Bull Rush: a forged iron bull-helm, its great horns lowered, the barrier it charges
    behind standing before it in a curve of light."""
    e = Emblem("physical", 0.92, (50, 52))
    e.lay(stroke(arc(50, 40, 44, 120, 240, 60), 4.0), "glow", 1, 2, light=1.0)
    e.lay(stroke(arc(50, 40, 38, 135, 225, 40), 1.6), "glow", 0.5, 1, light=0.6)
    for sx in (-1, 1):
        horn = bez((50 + sx * 16, 40), (50 + sx * 34, 36), (50 + sx * 44, 22), (50 + sx * 34, 8), 40)
        e.lay(stroke(horn, 10, 2.0), "bone", 6, 5, grain=0.6)
        for t in (0.15, 0.3):
            p, q = horn[int(t * 39)], horn[int(t * 39) + 2]
            e.lay(stroke([p, q], 9.6 - t * 10), mat("#a89878", 0.0, 0.6), 6.4, 0.6)
    e.lay(ellipse(50, 50, 21, 25), "iron", 6, 6, grain=0.6, kind="hammer")
    e.lay(stroke([(50, 26), (50, 74)], 6, 4.4), "iron_dark", 7, 2, grain=0.4, kind="hammer")
    e.lay(cut(ellipse(50, 50, 21, 25), poly([(0, 0), (100, 0), (100, 62), (0, 62)])), "iron_dark", 7, 2, grain=0.4, kind="hammer")
    for sx in (-1, 1):
        e.lay(ellipse(50 + sx * 10, 50, 6.5, 2.2, sx * -10), mat("#020102", 0.0, 0.9), 0.5, 0.6, z=6)
        for y in (34, 44, 58, 68):
            e.lay(circle(50 + sx * 5.5, y, 1.2), "steel", 8, 0.6)
        e.lay(circle(50 + sx * 15, 40, 4.5), "gold_dim", 7.5, 2, grain=0.3, kind="hammer")
    return e


def d_chain():
    """Grapple Chain: the binders' chain flung out, its links running to an iron grapple
    whose hooks are about to bite."""
    e = Emblem("physical", 0.92, (50, 50))
    path = bez((10, 90), (24, 52), (44, 68), (60, 40), 80)
    P = resample(path, 7.2)
    for i, (x, y) in enumerate(P):
        a, b = P[max(i - 1, 0)], P[min(i + 1, len(P) - 1)]
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if i % 2 == 0:
            e.lay(cut(ellipse(x, y, 5.6, 3.6, ang), ellipse(x, y, 3.4, 1.5, ang)), "iron", 4, 1.4, grain=0.4, kind="hammer")
        else:
            e.lay(ellipse(x, y, 5.6, 1.5, ang), "iron", 5, 1.0, grain=0.3, kind="hammer")
    end = tuple(P[-1])
    e.lay(stroke([end, (66, 32)], 3.4), "iron", 5, 1.2)
    e.lay(cut(circle(62, 36, 4), circle(62, 36, 2)), "iron", 5.5, 1.2)
    shank = [(64, 34), (80, 18)]
    e.lay(stroke(shank, 5, 4), "iron", 6, 2, grain=0.5, kind="hammer")
    for ang in (-60, 30, 120):
        a = math.radians(ang)
        base = (80 + 3 * math.cos(a), 18 + 3 * math.sin(a))
        hook = bez(base, (base[0] + 14 * math.cos(a), base[1] + 14 * math.sin(a)),
                   (base[0] + 16 * math.cos(a) - 8 * math.cos(a + 1.2), base[1] + 16 * math.sin(a) - 8 * math.sin(a + 1.2)),
                   (base[0] + 8 * math.cos(a) - 9 * math.cos(a + 1.4), base[1] + 8 * math.sin(a) - 9 * math.sin(a + 1.4)), 30)
        e.lay(stroke(hook, 4.2, 1.0), "steel", 6.5, 1.6, grain=0.3, kind="hammer")
    e.lay(circle(80, 18, 4.4), "iron_dark", 7, 2)
    for x, y in ((86, 10), (92, 26), (72, 8)):
        e.lay(stroke([(x - 4, y + 2), (x + 2, y - 2)], 1.2, 0.3), "glow", 0.5, 0.6, light=1.4)
    return e


def d_shield():
    """Shield Bash: a round shield of the Watch, planked and iron-rimmed, driven into what is
    in front of it, the blow going out from its face."""
    e = Emblem("physical", 0.94, (52, 50))
    for k, (r, w, li) in enumerate(((30, 4.4, 1.2), (38, 3.0, 0.8), (45, 1.8, 0.5))):
        e.lay(stroke(arc(52, 50, r, 30, 150, 50), w, w * 0.6), "glow", 1, 1.4, light=li)
    sh = ellipse(42, 50, 24, 34)
    e.lay(sh, "wood", 5, 6, grain=0.9)
    for x in (30, 38, 46, 54):
        e.lay(inter(stroke([(x, 10), (x, 90)], 1.0), sh), mat("#120a06", 0.0, 0.8), 0.4, 0.4, z=4.6)
    e.lay(cut(ellipse(42, 50, 24, 34), ellipse(42, 50, 20, 30)), "iron", 6.4, 1.8, grain=0.5, kind="hammer")
    for t in range(0, 360, 36):
        a = math.radians(t)
        e.lay(circle(42 + 22 * math.sin(a), 50 - 32 * math.cos(a), 1.3), "steel", 7.4, 0.8)
    e.lay(ellipse(44, 50, 9, 12), "steel", 9, 6, grain=0.4, kind="hammer")
    e.lay(stroke([(30, 50), (34, 50)], 3), "iron", 6.4, 1)
    e.lay(ellipse(47, 46, 2.2, 3.6, 20), mat("#ffffff", 0.0, 0.1), 0.6, 1, z=9, light=0.4)
    return e


def d_mark():
    """Mark Prey: the hunter's mark daubed in red on the quarry's hide, and the arrow already
    in it."""
    e = Emblem("blood", 0.94, (50, 50))
    e.lay(ellipse(48, 52, 34, 32), mat("#4a3424", 0.0, 0.85), 2, 3, grain=1.0, kind="fine")
    ring = cut(circle(48, 52, 24), circle(48, 52, 18.5))
    e.lay(ring, "glow", 0.6, 1.5, light=1.4, z=2)
    for a, b in (((48, 22), (48, 36)), ((48, 68), (48, 82)), ((18, 52), (32, 52)), ((64, 52), (78, 52))):
        e.lay(stroke([a, b], 3.4, 1.4), "glow", 0.6, 1.2, light=1.4, z=2)
    for x, y0, L in ((40, 74, 8), (58, 72, 10), (30, 64, 6)):
        e.lay(stroke([(x, y0), (x + 0.4, y0 + L)], 2.2, 0.8), "glow", 0.6, 1, light=1.1, z=2)
    e.lay(stroke([(48, 52), (84, 16)], 2.8), "wood", 5, 1.4, grain=0.4)
    for sx in (-1, 1):
        e.lay(poly([(78, 22), (88 + sx * 4, 6 - sx * 4), (92 + sx * 2, 10 - sx * 2), (84, 26)]) if sx > 0 else
              poly([(78, 22), (72, 6), (78, 4), (84, 16)]), mat("#c8b8a0", 0.0, 0.7), 5.4, 1.2, grain=0.4, kind="fine")
    e.lay(stroke([(84, 16), (90, 10)], 2.2), mat("#6a1010", 0.0, 0.7), 5.6, 1)
    e.lay(circle(48, 52, 4.6), mat("#1a0c06", 0.0, 0.8), 3, 1.5, z=2)
    e.lay(circle(48, 52, 2.4), "glow", 1, 1, light=2.0, z=5)
    return e


def d_wing():
    """Vault: a heron's wing of the fen thrown up in the spring away, and the snares left on
    the ground where you stood."""
    e = Emblem("physical", 0.92, (50, 48))
    for x, y, sz in ((30, 86, 5), (52, 90, 4.4), (72, 84, 4.8)):
        caltrop(e, x, y, sz)
    root = (34, 70)
    pale, grey = mat("#e0d8cc", 0.0, 0.6), mat("#9a948c", 0.0, 0.6)
    for k in range(9):
        ang = 8 + k * 9
        feather(e, root, ang, 50 - abs(k - 3) * 3.2, 9.5, grey if k > 6 else pale)
    for k in range(7):
        ang = 20 + k * 10
        feather(e, (root[0] + 2, root[1] - 2), ang, 26, 9, pale)
    e.lay(ellipse(40, 64, 12, 8, 30), pale, 5, 5, grain=0.6, kind="fine")
    for x, y0 in ((20, 20), (12, 36), (26, 8)):
        e.lay(stroke([(x, y0 + 26), (x + 4, y0)], 0.3, 2.2), "glow", 0.5, 1, light=0.6)
    return e


''' + s[i:]

rep('''    "static": "a twisted iron rod with a gold ball at its tip, blue-white lightning crawling up round it and leaping "''',
    '''    "boot": "a worn leather road boot with an iron-shod sole and a buckled strap, driving forward, dust kicked up behind "
            "it, streaks of wind streaming back",
    "horns": "a forged black iron bull helm with great curved bone horns lowered, a curved shield of pale light before it",
    "chain": "an iron chain flung out in a curve, its end a four-hooked iron grappling hook about to bite",
    "shield": "a round wooden shield with an iron rim, rivets and a steel boss, driven forward, a blast of force going "
              "out from its face",
    "mark": "a hunter's mark daubed in glowing red paint on dark hide, a ringed cross, red drips, a fletched arrow "
            "driven into its centre",
    "wing": "a single pale grey heron's wing thrown up, long feathers spread, iron caltrops lying on the ground below it",
    "static": "a twisted iron rod with a gold ball at its tip, blue-white lightning crawling up round it and leaping "''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
