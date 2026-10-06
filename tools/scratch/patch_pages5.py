p = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\patch_pages4.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''    """The rule between a page's columns (frames/column_divider.png, 48x1024, 24x512 shown,
    slice 0 24 0 24, the middle tiled): a rod of the binders' twisted iron, two strands, with a
    forged collar every 128 px; its ends fade into the page. The stone at its middle is a piece
    of its own (column_divider_stone)."""
    TW, TH = 48, 1024
    tiles = 3
    R = RL.Relief(TW, TH * tiles, ss)
    X, Y = R.xx / ss, R.yy / ss
    cx = TW / 2
    across = X - cx
    th = 4.6 * K
    pitch = 5.2 * K
    s_ = Y / pitch''', '''    """The rule between a page's columns (frames/column_divider.png, 48x1120, 24x560 shown,
    slice 0 24 0 24, the middle tiled): a rod of the binders' twisted iron, two strands, with a
    forged collar every 128 px; its ends fade into the page. The slice repeats only the middle
    (512 shown), so the twist and the collars are periodic over exactly that, and the ends
    carry on the same pattern. The stone at its middle is a piece of its own."""
    TW, END, PER = 48, 48, 1024            # file px: width, each end, the repeating middle
    TH = PER + 2 * END
    PAD = 256                              # rendered past both ends, cropped (the light's edge)
    R = RL.Relief(TW, TH + 2 * PAD, ss)
    X, Y = R.xx / ss, R.yy / ss
    Yp = Y - PAD - END                     # 0 where the repeating middle starts
    cx = TW / 2
    across = X - cx
    th = 4.6 * K
    pitch = PER / 98.0
    s_ = Yp / pitch''')
rep('''    for k0 in range(int(TH * tiles / K / 128)):
        yc = (k0 + 0.5) * 128 * K
        dy = np.abs(Y - yc)''', '''    for k0 in range(-2, int((TH + 2 * PAD) / K / 128) + 2):
        yc = (k0 + 0.5) * 128 * K
        dy = np.abs(Yp - yc)''')
rep('''    small = R.file_size(img)
    mid = small[TH:2 * TH].copy()''', '''    small = R.file_size(img)
    mid = small[PAD:PAD + TH].copy()''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
