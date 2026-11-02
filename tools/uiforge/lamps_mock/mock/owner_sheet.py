"""the owner's Lamps sheet (r3): title, options, 1:1 centerpieces (2 per row), the five frames at half (2 per row)"""
import os, shutil
from PIL import Image, ImageDraw
import text as T
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
DST = r'C:\Users\munch\Desktop\survivorsunchained_inputs\ui25_lamps'
BG, INK, DIM = (14, 14, 16), (0xe6, 0xdc, 0xcb), (0xa9, 0x9f, 0x8d)
G = 24
f_title = T.font('cinzel-700', 30); f_opt = T.font('alegreya-sans-400', 20)
f_cap = T.font('alegreya-sans-500', 18); f_cap2 = T.font('alegreya-sans-400', 17)
CENTER = [
    ('C_day', (1000, 140, 1910, 1000), 'C, day, 1:1: the board lives in the book\u2019s panel, like the Journal and the Map. '
     'The gold dashes lead to the lamp you point at.'),
    ('C_night', (1000, 140, 1910, 1000), 'C, night, 1:1: a skill\u2019s wick open. The wick rises from the skill and braids '
     'into three strands; the night lights them in the order you plan.'),
    ('A_day', None, 'A, day, 1:1 (Open wide): the world dims to dusk, and each lit lamp gives the cobbles back their color. '
     'Your build lights the valley.'),
    ('A_night', None, 'A, night, 1:1: the same wick panel between the Drowned Girl and the keeper; the board is light on '
     'the dark.'),
]
# A crops: A day = the lit cluster, her and the card + 60 px; A night = the lit cluster down to the wick panel and both
# statues' heads (measured on the r3 frames)
A_DAY = (640, 236, 1700, 806)       # UI 26: widened so no label is sliced at the crop's edge
A_NIGHT = (480, 228, 1540, 1000)    # UI 26: same
CENTER[2] = ('A_day', A_DAY, CENTER[2][2]); CENTER[3] = ('A_night', A_NIGHT, CENTER[3][2])
HALF = [('C_day', ['C, The Day\u2019s Book (default), day.', 'Half panel: she and the town stay in full color on the left.',
                   'Matches your half-window choice for the Journal and the Map.']),
        ('C_night', ['C, night, the wick open on Sunder.', 'The board slides up; the Turn\u2019s words live in its row.',
                     'By night the board is read-only: the wick is the night\u2019s growth.']),
        ('A_day', ['A, Nightfall (Open wide), day.', 'Full screen over a dusk grade; the HUD\u2019s seats become the wick tabs.',
                   'Her lit lamps\u2019 pools are the soul: her build lights the world.']),
        ('A_night', ['A, night, the wick open.', 'A cool night grade; the pools keep full color.',
                     'The keeper\u2019s fire is the Flare\u2019s tab.']),
        ('A_valley', ['A, the whole board (the Valley stop).', 'Four callings around the Ford, the Old Roads at the rim.',
                      'Her build reads as one lit path.'])]


def wrap(s, f, w):
    return T.wrap(s, f, w)


def build():
    frames = {n: Image.open(os.path.join(OUT, n + '.png')).convert('RGB') for n in
              ('C_day', 'C_night', 'A_day', 'A_night', 'A_valley')}
    crops = [(frames[n].crop(r), cap) for n, r, cap in CENTER]
    rows = [crops[0:2], crops[2:4]]
    W = max(G + sum(im.width for im, _ in r) + G * (len(r) - 1) + G for r in rows)
    W = max(W, G * 3 + 960 * 2)
    items, y = [], G
    items.append(('t', (G, y + 30), 'THE LAMPS SCREEN: PICK A DIRECTION', f_title, INK)); y += 30 + 18
    for ln in ['Option 1 (recommended): C, The Day\u2019s Book, as the default, with A, Nightfall, as its Open wide (Z).',
               'Option 2: A only, full screen.', 'B, The Lamplighter\u2019s Wheel: tried, far behind: cut.',
               'A\u2019s frames show today\u2019s HUD foot; your statue change (UI 27) swaps in when it lands.']:
        y += 26; items.append(('t', (G, y), ln, f_opt, INK if ln.startswith('Option') else DIM))
    y += G
    for r in rows:
        x = G
        capl = [wrap(cap, f_cap, im.width) for im, cap in r]
        ch = max(len(c) for c in capl) * 23
        for (im, cap), cl in zip(r, capl):
            for j, ln in enumerate(cl):
                items.append(('t', (x, y + 18 + j * 23), ln, f_cap, INK))
            items.append(('i', (x, y + ch + 8), im))
            x += im.width + G
        y += ch + 8 + max(im.height for im, _ in r) + G
    for k in range(0, 5, 2):
        x = G
        for n, caps in HALF[k:k + 2]:
            im = frames[n].resize((960, 540), Image.LANCZOS)
            items.append(('i', (x, y), im))
            for j, ln in enumerate(caps):
                items.append(('t', (x, y + 540 + 22 + j * 22), ln, f_cap2, INK if j == 0 else DIM))
            x += 960 + G
        y += 540 + 22 + 3 * 22 + G
    sheet = Image.new('RGB', (W, y), BG)
    d = ImageDraw.Draw(sheet)
    for it in items:
        if it[0] == 'i':
            sheet.paste(it[2], it[1])
        else:
            d.text(it[1], it[2], font=it[3], fill=it[4], anchor='ls')
    os.makedirs(DST, exist_ok=True)
    sheet.save(os.path.join(DST, 'lamps_owner_sheet.jpg'), quality=93)
    sheet.resize((W // 2, y // 2), Image.LANCZOS).save(os.path.join(HERE, 'lamps_owner_sheet_half.jpg'), quality=90)
    for n in frames:
        shutil.copy(os.path.join(OUT, n + '.png'), os.path.join(DST, n + '.png'))
    print('sheet', W, y)


if __name__ == '__main__':
    build()
