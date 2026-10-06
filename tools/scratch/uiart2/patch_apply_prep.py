p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\kit.py'
s = open(p, encoding='utf-8').read()
# Empty slots lifted (seen in the game: too faint to read as places).
s = s.replace('''    "slot": Slice("frames/slot.png", 10, 10, 10, 10, False, 0, G, (0.5, 0.47, 0.5, 0.8)),''',
              '''    "slot": Slice("frames/slot.png", 10, 10, 10, 10, False, 0, G, (0.66, 0.63, 0.66, 0.86)),''')
s = s.replace('''    "frames/slot.png": lambda: sunk(80, 80, depth=0.9),''',
              '''    "frames/slot.png": lambda: sunk(80, 80, depth=0.8, rim=1.8),''')
# The tabs' hover and press: the faintest underline, grey (only the open tab is ember).
s = s.replace('''    "tab_on": Slice("frames/tab_on.png", 18, 10, 18, 6, True),''',
              '''    "tab_on": Slice("frames/tab_on.png", 18, 10, 18, 6, True),
    "tab_hover": Slice("frames/tab_hover.png", 18, 10, 18, 6, True),
    "tab_pressed": Slice("frames/tab_pressed.png", 18, 10, 18, 6, True),''')
s = s.replace('''    "frames/tab_on.png": lambda: underline(96, 34),''',
              '''    "frames/tab_on.png": lambda: underline(96, 34),
    "frames/tab_hover.png": lambda: underline(96, 34, col=F.hexc("#b8ab98", lin=False), glow=0.0, a=0.35),
    "frames/tab_pressed.png": lambda: underline(96, 34, col=F.hexc("#d8c8b0", lin=False), glow=0.0, a=0.55),''')
s = s.replace('''def underline(Ws=96, Hs=34, col=EMBER, end=16):''', '''def underline(Ws=96, Hs=34, col=EMBER, end=16, glow=0.10, a=0.95):''')
s = s.replace('''    line = np.clip(1 - np.abs(y - (Hs - 2.5)) / 1.0, 0, 1) * fade * 0.95
    halo = np.exp(-((Hs - 2.5 - y) / 9.0) ** 2) * fade * 0.10 * (y < Hs - 2)''', '''    line = np.clip(1 - np.abs(y - (Hs - 2.5)) / 1.0, 0, 1) * fade * a
    halo = np.exp(-((Hs - 2.5 - y) / 9.0) ** 2) * fade * glow * (y < Hs - 2)''')
open(p, 'w', encoding='utf-8').write(s)
print('ok', s.count('tab_hover'))
