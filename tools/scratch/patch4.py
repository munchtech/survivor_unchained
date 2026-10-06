p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\emblems.py'
s = open(p, encoding='utf-8').read()


def replace_fn(name, code):
    global s
    i0 = s.index(f'def d_{name}():')
    i1 = s.index('\ndef ', i0 + 10)
    s = s[:i0] + code.strip('\n') + '\n\n' + s[i1:]


replace_fn('leap', '''
def d_leap():
    """Crashing Leap: the leap's arc coming down hard, the ground split open where it lands,
    slabs of it thrust up and lit from the break, stones thrown."""
    e = Emblem("physical", 0.94, (50, 50))
    gx, gy = 56, 74
    stone = mat("#9a8a70", 0.0, 0.75)
    e.lay(ellipse(gx - 2, gy + 4, 42, 12), mat("#3a3228", 0.0, 0.9), 2, 3, grain=1.0)
    e.lay(ellipse(gx, gy + 1, 15, 4.6), "glow", 1, 2, light=2.4)
    for ang in (-100, -60, -25, 15, 50, 85, 120, 160, -150):
        a = math.radians(ang)
        pts = [(gx + 8 * math.sin(a), gy + 1 + 2.4 * math.cos(a)), (gx + 22 * math.sin(a), gy + 1 + 6.5 * math.cos(a) + 1),
               (gx + 38 * math.sin(a), gy + 1 + 11 * math.cos(a))]
        e.lay(stroke(pts, 2.0, 0.4), "glow", 0.5, 0.6, light=1.2, z=2.5)
    # The slabs: the ground's own plates, broken and stood up on end round the break.
    for j, (dx, h, w, lean) in enumerate(((-24, 16, 9, -10), (-13, 22, 8, -5), (13, 20, 8, 6), (25, 15, 9, 12),
                                         (-4, 12, 6, -2), (5, 13, 6, 3))):
        bx, by = gx + dx, gy + (2 if abs(dx) > 10 else -1)
        pts = [(bx - w / 2, by), (bx - w / 2 + lean * 0.4, by - h * 0.7), (bx + lean * 0.6 - w * 0.1, by - h),
               (bx + w / 2 + lean * 0.5, by - h * 0.8), (bx + w / 2, by)]
        e.lay(poly(pts), stone, 5, 2.2, round_=False, grain=0.9)
        e.lay(stroke([pts[0], pts[1], pts[2]], 1.2), mat("#d8c8a8", 0.0, 0.6), 5.4, 0.5)
    for j, (dx, dy, sz) in enumerate(((-34, -18, 3.4), (-20, -32, 2.8), (32, -24, 3.6), (18, -36, 2.4), (40, -10, 2.6),
                                      (-6, -40, 2.0), (6, -30, 1.8))):
        e.lay(rock(gx + dx, gy + dy, sz, 30 + j), stone, 3, 1.5, grain=0.6)
    # The leap: an arc of rushing air from the take-off to the blow.
    path = bez((8, 66), (10, 14), (44, 0), (gx - 2, gy - 16), 60)
    e.lay(stroke(path, 0.6, 8.0), "glow", 1, 3, light=1.0)
    for off in (-5, 5):
        side = [(x + off * 0.7, y + off * 0.5) for x, y in bez((14, 60), (16, 18), (44, 6), (gx - 2 + off * 0.3, gy - 22), 50)]
        e.lay(stroke(side, 0.4, 2.4), "glow", 0.5, 1, light=0.6)
    return e
''')
s = s.replace('''    "leap": "a bright arc of white light leaping high and crashing down into the ground, the ground breaking in a "
            "crater with glowing cracks, rocks and dust thrown up",''', '''    "leap": "a streak of rushing air arcing high and crashing down into the ground, the ground split open in a "
            "glowing crater, broken slabs of stone thrust up on end round it, stones and dust thrown up",''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
