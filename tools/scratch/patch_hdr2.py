p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\pages.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''    rail0, rail1 = 76.0, 89.0                    # the rail's top and foot, shown px''',
    '''    # The page writes across the band down to y 80 (the tabs, the title, its line under it),
    # so the rail is at the very foot and the tooling keeps to where nothing is written.
    rail0, rail1 = 85.0, 97.0                    # the rail's top and foot, shown px''')
rep('''    # Blind tooling: a double rule pressed in above the rail, and between the rules and the
    # rail a row of punched lozenges, the binders' square set on its point, every 16 px.
    tool = np.zeros_like(X)
    for yr, wd in ((60.0, 0.75), (64.0, 0.5)):
        tool = np.maximum(tool, np.clip((wd - np.abs(y - yr)) * K * ss * 0.5 + 0.5, 0, 1))
    xs = X / K
    u = ((xs + 8.0) % 16.0) - 8.0
    loz = np.clip((2.2 - (np.abs(u) + np.abs(y - 70.0))) * K * ss * 0.5 + 0.5, 0, 1)
    dot = np.clip((0.7 - np.hypot(u, y - 70.0)) * K * ss * 0.5 + 0.5, 0, 1)
    tool = np.maximum(tool, loz * (1 - dot * 0.7))''', '''    # Blind tooling: a fine rule pressed in just above the rail, and along the top (where the
    # band leaves the screen) a double rule with a row of punched lozenges between, the
    # binders' square set on its point, every 16 px.
    tool = np.zeros_like(X)
    for yr, wd in ((81.5, 0.5), (4.0, 0.6), (15.0, 0.6)):
        tool = np.maximum(tool, np.clip((wd - np.abs(y - yr)) * K * ss * 0.5 + 0.5, 0, 1))
    xs = X / K
    u = ((xs + 8.0) % 16.0) - 8.0
    loz = np.clip((2.4 - (np.abs(u) + np.abs(y - 9.5))) * K * ss * 0.5 + 0.5, 0, 1)
    dot = np.clip((0.7 - np.hypot(u, y - 9.5)) * K * ss * 0.5 + 0.5, 0, 1)
    tool = np.maximum(tool, loz * (1 - dot * 0.7))''')
rep('''        for (nx, ny, r, top) in (((k0 + 0.5) * 64, rail0 + 2.6, 2.1, 10.5), ((k0 + 1.0) * 64, 47.0, 1.5, 5.6)):''',
    '''        for (nx, ny, r, top) in (((k0 + 0.5) * 64, rail0 + 2.6, 2.1, 10.5),):''')
rep('''    fall = 0.42 + 0.58 * np.clip(y / rail0, 0, 1) ** 0.8
    tint = np.where(leather, (0.7 + 0.55 * cloud) * fall * (1 - tool * 0.35), 1.0)''', '''    fall = 0.5 + 0.5 * np.clip(y / rail0, 0, 1) ** 0.8
    tint = np.where(leather, (0.55 + 0.4 * cloud) * fall * (1 - tool * 0.35), 1.0)''')
rep('''    sh = np.clip(1 - (yy - rail1) / 10.0, 0, 1) ** 1.6 * 0.7 * (yy >= rail1)''',
    '''    sh = np.clip(1 - (yy - rail1) / 3.0, 0, 1) ** 1.2 * 0.75 * (yy >= rail1)''')
rep('''    R.alpha = (y < rail1 + 0.5).astype(np.float32)''', '''    R.alpha = (y < rail1).astype(np.float32)''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
