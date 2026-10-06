p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\pages.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''    """The ember asleep in a coin's hole: a dull red-orange, hottest low in the hole."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    n = F.fbm(R.h, R.w, scale=max(8, R.w / 6), octaves=3, seed=seed) * 0.5 + 0.5
    d = np.hypot(X - cx, Y - (cy + size * 0.06)) / (size * 0.18)
    g = hole_mask * np.exp(-d ** 2 * 1.2) * (0.6 + 0.6 * n)
    return (g[..., None] * (F.hexc("#ff7a2a") * 1.1 + F.hexc("#9a2004") * 0.8)).astype(np.float32)''',
    '''    """The ember asleep in a coin's hole: a coal deep in the dark, hot where it is not crusted
    over, dull red at the hole's rim, black between (never a flat orange disc)."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    n = F.fbm(R.h, R.w, scale=max(4, R.w / 14), octaves=3, seed=seed) * 0.5 + 0.5
    d = np.hypot(X - cx, Y - (cy + size * 0.04)) / (size * 0.15)
    core = np.exp(-d ** 2 * 1.6)
    crust = np.clip((n - 0.38) * 3.0, 0, 1)
    hot = hole_mask * core * crust
    dull = hole_mask * np.exp(-d ** 2 * 0.5) * 0.35
    return (hot[..., None] * F.hexc("#ffa040") * 1.6 + dull[..., None] * F.hexc("#9a2004")).astype(np.float32)''')
rep('''    R.mat[col > 0.5] = RL.IDS["iron_dark"]''', '''    R.mat[col > 0.5] = RL.IDS["gold_dim"]''')
rep('''    hh, cm, hm = RL.coin(R, c, c, W * 0.86, 1.0, hole=0.34, rot=rot)''', '''    # Set on its point the square's diagonal is what must fit: 0.62 of the side leaves a margin.
    hh, cm, hm = RL.coin(R, c, c, W * 0.62, 1.0, hole=0.36, rot=rot)''')
rep('''    R.emit = ember_light(R, hm, c, c, W * 0.86, seed=103) * glow''', '''    R.emit = ember_light(R, hm, c, c, W * 0.62, seed=103) * glow''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
