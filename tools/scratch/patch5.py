p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\emblems.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep('''    for j, (dx, h, w, lean) in enumerate(((-24, 16, 9, -10), (-13, 22, 8, -5), (13, 20, 8, 6), (25, 15, 9, 12),
                                         (-4, 12, 6, -2), (5, 13, 6, 3))):
        bx, by = gx + dx, gy + (2 if abs(dx) > 10 else -1)
        pts = [(bx - w / 2, by), (bx - w / 2 + lean * 0.4, by - h * 0.7), (bx + lean * 0.6 - w * 0.1, by - h),
               (bx + w / 2 + lean * 0.5, by - h * 0.8), (bx + w / 2, by)]
        e.lay(poly(pts), stone, 5, 2.2, round_=False, grain=0.9)
        e.lay(stroke([pts[0], pts[1], pts[2]], 1.2), mat("#d8c8a8", 0.0, 0.6), 5.4, 0.5)''', '''    # Each slab: a broken plate heaved up and tipped out from the break, no two alike.
    for j, (dx, dy, h, w, tip) in enumerate(((-22, 3, 14, 16, -38), (-8, -2, 22, 12, -14), (12, -1, 18, 14, 22),
                                             (27, 4, 12, 15, 48))):
        bx, by = gx + dx, gy + dy
        c_, s_ = math.cos(math.radians(tip)), math.sin(math.radians(tip))
        rng = np.random.default_rng(j + 5)
        local = [(-w / 2, 0), (-w / 2 + rng.uniform(-2, 1), -h * 0.6), (-w * 0.15 + rng.uniform(-2, 2), -h),
                 (w * 0.25 + rng.uniform(-2, 2), -h * rng.uniform(0.75, 0.95)), (w / 2, -h * rng.uniform(0.3, 0.6)), (w / 2, 0)]
        pts = [(bx + x * c_ - y * s_, by + x * s_ + y * c_) for x, y in local]
        e.lay(poly(pts), stone, 5, 2.2, round_=False, grain=1.0)
        e.lay(stroke(pts[1:4], 1.4, 0.8), mat("#e0d0b0", 0.0, 0.6), 5.4, 0.6)''')
rep('''    for off in (-5, 5):
        side = [(x + off * 0.7, y + off * 0.5) for x, y in bez((14, 60), (16, 18), (44, 6), (gx - 2 + off * 0.3, gy - 22), 50)]
        e.lay(stroke(side, 0.4, 2.4), "glow", 0.5, 1, light=0.6)''', '''    P = np.asarray(path, np.float32)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Nn = np.stack([-T[:, 1], T[:, 0]], 1)
    for off in (-6, 6):
        side = P[8:-6] + Nn[8:-6] * off * np.linspace(0.3, 1, len(P) - 14)[:, None]
        e.lay(stroke(side.tolist(), 0.4, 2.2), "glow", 0.5, 1, light=0.55)''')
rep('''    e = Emblem("physical", 0.94, (50, 50))
    gx, gy = 56, 74''', '''    e = Emblem("physical", 0.94, (50, 50))
    e.glow = 0.5
    gx, gy = 56, 74''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
