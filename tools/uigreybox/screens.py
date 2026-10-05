"""The greyboxes: Self, Pack, Storeroom, Trader and the bench, at 1920x1080, drawn plain in the
game's own type before any art (docs/design/UI_RESEARCH.md).

    python tools/uigreybox/screens.py OUTDIR

Panels hug what they hold. A surface that has to run on (a page's sheet, a full-height side
panel) tapers out into what is behind it. Grids show the rows in use and one more, not every
cell they could hold; the count says the rest ("8 of 24"). The world between panels is live
(her, the keeper, the smith) and is kept."""
import os
import sys
from gb import *

BOOK = ['Pack', 'Self', 'Arts', 'Journal', 'Map']
KEYS = ['I', 'C', 'K', 'J', 'M']
BACK = (50, 52, 56)  # the blurred world behind a page
GOLD = (230, 196, 120)


def rows_for(items, cols, cap):
    """The rows in use and one more (at least two), up to the capacity's rows."""
    last = max((r for (_, r) in items), default=-1)
    return max(2, min(cap, last + 2))


def grid_block(c, x, y, items, title, count, cols=6, cap=4, s=72, right=None, w=None):
    """A section head and its grid; returns the y under it."""
    rows = rows_for(items, cols, cap)
    gw = cols * s + (cols - 1) * 8 + 12
    if right == 'Sort':
        # Sort and the item filter, side by side at the head's end.
        c.section(x, y, (w or gw) - 64, title, count, 'Filter', INK2)
        c.text(x + (w or gw), y - 1, 'Sort', UI_B, 15, INK2, anchor='ra')
    else:
        c.section(x, y, w or gw, title, count, right, INK2)
    _, gh = c.grid(x, y + 30, cols, rows, items=items, s=s, gap=8, pad=6)
    return y + 30 + gh


def pouch(c, x, y, stacks, w=484):
    """The slotless stores, as tabs over one row: what never takes a place in the pack (materials
    in the pouch, manuals and tomes in the satchel, quest things on the key ring). Stacks stack."""
    tx = c.tabs(x, y - 2, ['Pouch · 3', 'Satchel · 2', 'Key ring · 1'], 0, size=15)
    c.text(x + w, y, 'never in the pack', TEXT_I, 14, FAINT, anchor='ra')
    for i, (n, q, r) in enumerate(stacks):
        c.slot(x + i * 64, y + 34, 56, item=n, rarity=r, qty=q)
    return y + 34 + 56


PACK_ITEMS = {(0, 0): dict(item='dr', rarity=0, qty=3), (1, 0): dict(item='ch', rarity=2), (2, 0): dict(item='hm', rarity=3, focus=True),
              (3, 0): dict(item='rg', rarity=1), (4, 0): dict(item='bw', rarity=1), (5, 0): dict(item='st', rarity=2),
              (0, 1): dict(item='am', rarity=0), (1, 1): dict(item='cl', rarity=3)}
POUCH = [('pl', 4, 0), ('sh', 6, 1), ('hd', 2, 0)]


def world(c, label=True, figures=()):
    c.rect(0, 0, 1920, 1080, WORLD)
    if label:
        c.text(960, 40, 'THE WORLD, LIVE', UI_H, 16, (86, 90, 94), anchor='ma')
    for (x, y, h, name) in figures:
        c.figure(x, y, h, label=None, fill=(92, 94, 98))
        if name:
            c.text(x, y + h + 12, name, UI_B, 15, (112, 116, 120), anchor='ma')


def fitted(c, x, y, w, h, title=None, close=False):
    """A fitted panel: the screen's one frame, as tall as what it holds."""
    c.rect(x, y, w, h, PANEL)
    c.frame(x, y, w, h)
    if title:
        c.text(x + w / 2, y + 22, title, DISPLAY, 30, INK, anchor='ma')
    if close:
        c.button(x + w - 120, y + 18, 'Close', key='Esc', w=100)


# ---------------------------------------------------------------------------------------- Self
def self_page():
    c = Canvas(BACK)
    c.text(960, 1004, 'the blurred world behind the page', UI_B, 14, (80, 82, 88), anchor='ma')
    # The sheet: the page's ground under what it holds, tapering into the world below.
    c.taper(0, 88, 1920, 900, GROUND, fade=130, frame=False)
    c.rect(0, 0, 1920, 88, BAND)
    c.rule(0, 88, 1920, (96, 90, 80))
    c.text(36, 30, '[', UI_B, 16, DIM)
    x = c.tabs(60, 28, BOOK, 1, KEYS)
    c.text(x - 6, 30, ']', UI_B, 16, DIM)
    c.text(960, 14, 'WREN', DISPLAY, 34, INK, anchor='ma')
    c.text(960, 54, 'Level 4  ·  Warden  ·  Hunter, who knows Beastlore', TEXT_I, 16, DIM, anchor='ma')
    c.rect(860, 78, 200, 4, (24, 24, 26), r=2)
    c.rect(860, 78, 113, 4, (120, 160, 210), r=2)
    c.text(1068, 72, '340 / 600', UI_B, 13, DIM)
    c.button(1784, 26, 'Close', key='Esc', w=100)
    # Her, large: the page's hero; her feet go into the taper.
    c.figure(290, 112, 840)
    X, W = 560, 1320
    # Attributes: one tight row, with the spend and its preview.
    c.section(X, 112, W, 'Attributes', 'more with each level', '2 points to spend')
    attrs = [('Might', 6, '+2.5% damage, +4 health a point'), ('Finesse', 3, '+0.6% critical chance, +1% speed'),
             ('Wits', 3, '+1% weapon speed, +2% area and ember'), ('Resolve', 6, '+3 health, +0.5 armour, +0.08 regeneration')]
    cw = (W - 3 * 16) / 4
    for i, (n, v, per) in enumerate(attrs):
        x = X + i * (cw + 16)
        c.panel(x, 140, cw, 120)
        pv = i == 0
        c.text(x + 22, 148, f'{v}', DISPLAY, 46, INK)
        if pv:
            ax = x + 22 + c.width(f'{v}', DISPLAY, 46) + 10
            c.arrow(ax, 182, 22, GOOD, 3)
            c.text(ax + 36, 160, '7', DISPLAY, 32, GOOD)
        c.text(x + 22, 206, n.upper(), DISPLAY_L, 18, (210, 196, 160))
        c.text(x + 22, 232, per, UI, 14, DIM)
        c.rect(x + cw - 52, 152, 34, 34, (64, 46, 28), outline=EMBER, r=17)
        c.text(x + cw - 35, 169, '+', UI_H, 22, (255, 228, 190), anchor='mm')
        if pv:
            c.rect(x + cw - 92, 152, 34, 34, (46, 46, 50), outline=(80, 80, 86), r=17)
            c.text(x + cw - 75, 169, '–', UI_H, 22, INK2, anchor='mm')
    c.text(X, 278, 'Spending shows every number it changes, green where it rises, until you confirm.', TEXT_I, 15, DIM)
    c.button(X + W - 254, 270, 'Undo', w=110)
    c.button(X + W - 132, 270, 'Confirm', primary=True, w=132)
    # Traits: a level track, taken, next, later; deeds' traits as chips beside it.
    ty = 334
    c.section(X, ty, W, 'Traits', 'one of three at every second level, and some given for what you do')
    levels = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    x0, x1, yy = X + 30, X + 900, ty + 60
    c.rule(x0, yy, x1, (70, 70, 76))
    step = (x1 - x0) / (len(levels) - 1)
    for i, lv in enumerate(levels):
        x = x0 + i * step
        if lv == 2:
            c.d.ellipse((x - 21, yy - 21, x + 21, yy + 21), fill=(110, 100, 84), outline=(200, 180, 130), width=2)
            c.text(x, yy, 'ic', UI_H, 13, (40, 36, 30), anchor='mm')
            c.text(x, yy + 30, 'Steady Hand', UI_B, 15, INK, anchor='ma')
        elif lv == 4:
            c.d.ellipse((x - 21, yy - 21, x + 21, yy + 21), fill=(40, 30, 22), outline=EMBER, width=3)
            c.text(x, yy, '4', DISPLAY, 18, (255, 220, 170), anchor='mm')
            c.text(x, yy + 30, 'Next: one of three', UI_B, 15, EMBER, anchor='ma')
        else:
            c.d.ellipse((x - 6, yy - 6, x + 6, yy + 6), fill=(56, 56, 62))
            c.text(x, yy + 16, f'{lv}', UI_B, 13, FAINT, anchor='ma')
    c.text(X + 960, ty + 32, 'GIVEN FOR DEEDS', UI_H, 13, DIM)
    cx = X + 960
    for n in ('Wolfsbane', 'Lamp-lit'):
        cx += c.chip(cx, ty + 52, n) + 8
    # Stats: four aligned columns, so none runs long.
    sy = 462
    c.section(X, sy, W, 'Standing', 'hover a number: where it comes from')
    cols = [
        [('STAYING ALIVE', [('Health', '212', '+4'), ('Armour', '8 · 29%', None), ('Regeneration', '0.7/s', None), ('Healing', '+18%', None), ('Dodge', '0%', None)])],
        [('DEALING DEATH', [('Damage', '+15%', '+2.5%'), ('Critical chance', '6%', None), ('Critical damage', '×1.5', None), ('Weapon speed', '+3%', None), ('Area', '+6%', None)])],
        [('WARDING', [('Fire', '12%', None), ('Frost', '22%', None), ('Storm', '0%', None), ('Venom', '0%', None)]),
         ('FORTUNE', [('Experience', '+6%', None), ('Gold found', '0%', None)])],
        [('MOVING', [('Speed', '5.2', None), ('Dashes', '2', None), ('Reach', '2.4 m', None)]),
         ('THE ART IN HAND', [('Shield Bash', 'rank II', None), ('Strength', '+6%', None), ('Wait', '7 s', None)])],
    ]
    colw = (W - 3 * 36) / 4
    end = 0
    for ci, groups in enumerate(cols):
        x = X + ci * (colw + 36)
        y = sy + 34
        for gname, rows in groups:
            c.text(x, y, gname, UI_H, 13, (200, 186, 150))
            y += 24
            for (label, val, delta) in rows:
                c.text(x, y, label, UI, 17, INK2)
                c.text(x + colw - 50, y, val, UI_B, 17, INK, anchor='ra')
                if delta:
                    c.text(x + colw, y, delta, UI_B, 15, GOOD, anchor='ra')
                c.rule(x, y + 26, x + colw, (40, 40, 44))
                y += 31
            y += 14
        end = max(end, y)
    # Who she is, in the page's own words, under what she can do.
    oy = end + 10
    c.section(X, oy, W, 'Calling and origin')
    for i, (k, n, t) in enumerate([('CALLING', 'Warden', 'Hold the line.'), ('ORIGIN', 'Hunter', 'You read the ground and the animals on it.'),
                                    ('KNOWS', 'Beastlore', 'It opens words and ways others miss.'), ('RENOWN', 'A stranger', 'The Waystation has not decided about you.')]):
        x = X + i * (colw + 36)
        c.text(x, oy + 32, k, UI_H, 13, (200, 186, 150))
        c.text(x, oy + 54, n, TEXT_B, 19, INK)
        c.wrap(x, oy + 82, t, TEXT_I, 15, DIM, colw)
    c.prompts(960, 1040, [('Arrows', 'Move'), ('Enter', 'Spend a point'), ('Bksp', 'Take it back'), ('[ ]', 'Turn the page'), ('Esc', 'Close')])
    return c


# ---------------------------------------------------------------------------------------- Pack
PX, PW = 864, 1040


def pack_page():
    c = Canvas(WORLD)
    world(c, figures=[(430, 420, 150, None)])
    # A full-height side panel would end in empty iron: it hugs what it holds, then tapers.
    c.taper(PX, 16, PW, 930, PANEL, fade=110)
    c.tabs(PX + 28, 38, BOOK, 0, KEYS, size=16)
    c.button(PX + PW - 128, 32, 'Close', key='I', w=100)
    c.text(PX + PW / 2, 84, 'Pack', DISPLAY, 30, INK, anchor='ma')
    # The doll: her figure with her gear where it is worn.
    dx, dw = PX + 32, 470
    c.panel(dx, 136, dw, 664, (31, 31, 34))
    c.figure(dx + dw / 2, 156, 624, label='her, live 3D')
    s = 76
    left = [('HEAD', 160, None), ('CLOAK', 268, dict(item='cl', rarity=1)), ('BODY', 376, dict(item='ch', rarity=0)), ('RELIC', 484, None)]
    right = [('AMULET', 212, None), ('WEAPON', 320, dict(item='sw', rarity=1)), ('OFF-HAND', 428, dict(item='sh', rarity=0)),
             ('RING', 536, None), ('RING', 644, None)]
    for name, y, it in left:
        c.slot(dx + 16, y, s, label=name, **(it or {}))
    for name, y, it in right:
        c.slot(dx + dw - 16 - s, y, s, label=name, **(it or {}))
    # Beside it: what she carries, the pouch, the purse and the numbers that matter.
    gx = PX + 534
    y = grid_block(c, gx, 136, PACK_ITEMS, 'Carried', '8 of 24', right='Sort', w=484)
    y = pouch(c, gx, y + 30, POUCH)
    c.section(gx, y + 30, 484, 'Standing', None, '25 gold', GOLD)
    nums = [('Health', '212'), ('Armour', '8 · 29%'), ('Damage', '+15%'), ('Critical', '6%'), ('Speed', '5.2'), ('Regeneration', '0.7/s')]
    for i, (n, v) in enumerate(nums):
        col, row = i % 2, i // 2
        x = gx + col * 252
        yy = y + 62 + row * 33
        c.text(x, yy, n, UI, 17, DIM)
        c.text(x + 232, yy, v, UI_B, 17, INK, anchor='ra')
        c.rule(x, yy + 26, x + 232, (44, 44, 48))
    c.text(gx, y + 62 + 3 * 33 + 10, 'Self (C): every number, and where it comes from.', TEXT_I, 15, FAINT)
    c.prompts(PX + PW / 2, 822, [('Rclick', 'Wear or use'), ('Drag', 'Move'), ('Shift', 'Compare'), ('Del', 'Hold: break down')])
    # Hovering the helm: the cards open on the world's side, so the doll stays in view.
    c.tooltip(PX - 14 - 330, 196, 330, 'Iron Helm of the Salamander', 3, 'Epic helm · level 4', ['Armour 7', '+33% fire resistance', '+8 health'],
              foot='Rclick: wear   ·   Hold Del: break down', deltas=['+4', '+21%', '+8'])
    c.tooltip(PX - 14 - 330 - 16 - 290, 224, 290, 'Leather Cap', 0, 'Common helm', ['Armour 3', '+12% fire resistance'], head='Worn now')
    return c


# ----------------------------------------------------------------------------------- the counters
def yours(c, x, top, w=600, title='Your pack'):
    """Your side of any counter, hugging what it holds: the pack, the pouch, the purse."""
    pad = (w - 484) / 2
    y = grid_block(c, x + pad, top + 72, PACK_ITEMS, 'Carried', '8 of 24', right='Sort', w=484)
    y = pouch(c, x + pad, y + 28, POUCH)
    c.text(x + w - pad, y - 44, '25 gold', DISPLAY, 24, GOLD, anchor='ra')
    h = y + 26 - top
    return h


def draw_yours(c, x, top, w=600, title='Your pack'):
    # measured first on a scratch canvas, then drawn on a panel of that height
    scratch = Canvas()
    h = yours(scratch, x, top, w)
    fitted(c, x, top, w, h, title, close=True)
    yours(c, x, top, w)
    return h


def storeroom_page():
    c = Canvas(WORLD)
    world(c, figures=[(960, 390, 150, 'her, at the storeroom')])
    top, LX, RX, W = 150, 40, 1280, 600
    stored = {(0, 0): dict(item='ax', rarity=2), (1, 0): dict(item='rg', rarity=3), (2, 0): dict(item='bt', rarity=1), (3, 0): dict(item='hm', rarity=0),
              (4, 0): dict(item='am', rarity=1), (5, 0): dict(item='bk', rarity=0), (0, 1): dict(item='cl', rarity=1), (1, 1): dict(item='st', rarity=2),
              (2, 1): dict(item='pt', rarity=0, qty=5), (3, 1): dict(item='ch', rarity=4), (4, 1): dict(item='rl', rarity=1)}
    h = 72 + 30 + (3 * 72 + 2 * 8 + 12) + 64
    fitted(c, LX, top, W, h, "Rook's storeroom")
    c.tabs(LX + 58, top + 68, ['Shelf I', 'Shelf II'], 0, size=15)
    c.text(LX + W - 58, top + 70, 'kept safe, whatever becomes of you', TEXT_I, 15, FAINT, anchor='ra')
    y = grid_block(c, LX + 58, top + 108, stored, 'On the shelf', '11 of 24', right='Sort', w=484)
    draw_yours(c, RX, top, W)
    c.prompts(960, 1000, [('Rclick', 'Move across'), ('Drag', 'Move'), ('Shift', 'Compare'), ('[ ]', 'Shelf'), ('Esc', 'Close')])
    return c


def trader_page():
    c = Canvas(WORLD)
    world(c, figures=[(1010, 390, 150, 'Harlan, at his stall')])
    top, LX, W, RX = 150, 40, 700, 1280
    wares = {(0, 0): dict(item='dr', rarity=0, qty=4, price=30), (1, 0): dict(item='bd', rarity=0, qty=3, price=12), (2, 0): dict(item='vl', rarity=0, qty=2, price=45),
             (3, 0): dict(item='ck', rarity=1, price=120), (4, 0): dict(item='rg', rarity=1, price=160), (5, 0): dict(item='am', rarity=2, price=420, dear=True, focus=True),
             (6, 0): dict(item='bt', rarity=1, price=95), (0, 1): dict(item='bw', rarity=1, price=140), (1, 1): dict(item='hm', rarity=0, price=60),
             (2, 1): dict(item='sh', rarity=0, price=75), (3, 1): dict(item='lt', rarity=1, price=180), (4, 1): dict(item='tm', rarity=2, price=380, dear=True)}
    rows = 2
    gh = rows * 80 + (rows - 1) * 8 + 12
    h = 150 + 46 + gh + 60
    fitted(c, LX, top, W, h)
    c.rect(LX + 28, top + 24, 96, 96, (64, 64, 70), r=48)
    c.text(LX + 76, top + 72, 'face', UI_B, 14, (100, 100, 108), anchor='mm')
    c.text(LX + 144, top + 26, 'Harlan Coyle', DISPLAY, 28, INK)
    c.text(LX + 144, top + 66, 'a stranger · his usual prices · new stock in 2 days', UI, 15, DIM)
    c.wrap(LX + 144, top + 90, '"His caravan never came. His nephew was driving it."', TEXT_I, 17, INK2, W - 180)
    c.tabs(LX + 28, top + 146, ['Wares', 'Buy back · 2'], 0)
    gx = LX + 28
    c.grid(gx, top + 190, 7, rows, items=wares, s=80, gap=8, pad=6)
    yy = top + 190 + gh + 18
    c.text(gx, yy, 'He buys materials, draughts, trophies, rings, amulets and cloaks, at 35%; the rest is dimmed.', TEXT_I, 15, DIM)
    draw_yours(c, RX, top)
    th = c.tooltip(LX + W + 20, top + 186, 330, 'Bone Amulet of Dawn', 2, 'Rare amulet', ['+13% frost damage', '+6% experience'],
                   foot='420 gold: 395 more than you have', deltas=['+13%', '+6%'])
    c.tooltip(LX + W + 20, top + 186 + th + 14, 330, 'Wolf-tooth Amulet', 0, 'Common amulet', ['+5% gold found'], head='Worn now')
    c.prompts(960, 1000, [('Rclick', 'Buy or sell'), ('Drag', 'Across'), ('Shift', 'Compare'), ('Tab', 'Buy back'), ('Esc', 'Close')])
    return c


def bench_page():
    c = Canvas(WORLD)
    world(c, figures=[(1080, 380, 150, 'Brannoc, at the anvil')])
    top, LX, W, RX = 100, 40, 860, 1280
    h = 800
    fitted(c, LX, top, W, h)
    c.rect(LX + 28, top + 24, 84, 84, (64, 64, 70), r=42)
    c.text(LX + 132, top + 24, "Brannoc's smithy", DISPLAY, 28, INK)
    c.text(LX + 132, top + 62, 'warm to you · his usual prices · respect 5', UI, 15, DIM)
    c.wrap(LX + 132, top + 86, '"Forge is hot. Show me." He wipes his hands on the apron, and the apron makes them dirtier.', TEXT_I, 16, INK2, W - 170)
    ay = top + 156
    c.rule(LX + 28, ay - 12, LX + W - 28)
    c.slot(LX + 28, ay + 6, 88, item='sw', rarity=1)
    c.text(LX + 136, ay + 6, 'Worn Oathblade', TEXT_B, 26, RARITY[1])
    c.text(LX + 136, ay + 42, 'Uncommon sword', UI, 15, DIM)
    for i in range(6):
        c.rect(LX + 136 + i * 62, ay + 72, 56, 10, EMBER if i < 4 else (50, 44, 40), r=2)
    c.text(LX + 136 + 6 * 62 + 10, ay + 68, 'Heat 4 of 6', UI_B, 15, INK2)
    c.section(LX + 28, ay + 118, W - 56, 'Its seams', 'choose one to work')
    seams = [('Prefix', 'of the Wolf: +10% damage to beasts', True), ('Suffix', 'open: a seam waiting', False), ('Socket', 'locked: remake on a better pattern', False)]
    for i, (k, t, on) in enumerate(seams):
        y = ay + 148 + i * 50
        c.rect(LX + 28, y, W - 56, 44, (46, 41, 36) if on else (31, 31, 34), outline=EMBER if on else None, r=3)
        c.text(LX + 46, y + 22, k.upper(), UI_H, 13, DIM, anchor='lm')
        c.text(LX + 140, y + 22, t, UI_B if on else UI, 17, INK if on else DIM, anchor='lm')
    cy = ay + 318
    c.section(LX + 28, cy, W - 56, 'What he can do with it', 'for the prefix · two to a row, scrolling down')
    cw = (W - 56 - 14) / 2
    crafts = [('Temper', '+10%', '+14%', '1 old iron · 40 gold · 1 heat'), ('Rework', 'of the Wolf', 'one of three', '2 old iron · 60 gold · 2 heat'),
              ('Work in: Wolfbane', '', 'damage to beasts', '3 wolf pelts · 80 gold · 2 heat'), ('Break down', '', 'old iron ×2', 'the piece is gone')]
    for i, (n, before, after, cost) in enumerate(crafts):
        x = LX + 28 + (i % 2) * (cw + 14)
        y = cy + 32 + (i // 2) * 120
        c.rect(x, y, cw, 108, (31, 31, 34), r=3)
        c.text(x + 16, y + 12, n, TEXT_B, 19, INK)
        if before:
            c.text(x + 16, y + 44, before, UI, 16, DIM)
            ax = x + 16 + c.width(before, UI, 16) + 8
            c.arrow(ax, y + 55, 14, GOOD)
            c.text(ax + 24, y + 44, after, UI_B, 16, GOOD)
        else:
            c.text(x + 16, y + 44, ('gives ' if n == 'Break down' else '+ ') + after, UI_B, 16, INK2)
        c.text(x + 16, y + 72, cost, UI, 14, DIM)
        bx, bw = x + cw - 168, 152
        if n == 'Break down':
            c.rect(bx, y + 60, bw, 36, (60, 30, 28), outline=BAD, r=4)
            c.rect(bx, y + 60, bw * 0.45, 36, (150, 60, 50), r=4)
            c.text(bx + bw / 2, y + 78, 'Hold: break down', UI_B, 15, INK, anchor='mm')
        else:
            c.button(bx, y + 60, n.split(':')[0], primary=(i == 0), w=bw)
    ty = cy + 32 + 2 * 120 + 6
    c.text(LX + 28, ty, 'His terms', UI_H, 14, (200, 186, 150))
    c.text(LX + 120, ty, 'respect 20: crafts cost up to 1 heat less  ·  respect 40: tempering takes 1 old iron less', UI, 15, DIM)
    # Yours: what you wear (choose a piece), then the pack, pouch and purse; hugging them.
    pad = 58
    worn_h = 30 + 2 * 80
    scratch = Canvas()
    yh = yours(scratch, RX, top + worn_h + 24)
    fitted(c, RX, top, 600, yh + worn_h + 24, 'Your gear', close=True)
    c.section(RX + pad, top + 72, 484, 'Worn', 'choose a piece')
    for i, n in enumerate(['WEAPON', 'OFF-HAND', 'HEAD', 'BODY', 'CLOAK', 'AMULET', 'RING', 'RING', 'RELIC']):
        it = dict(item='sw', rarity=1, focus=True) if i == 0 else (dict(item='ch', rarity=0) if i == 3 else (dict(item='cl', rarity=1) if i == 4 else {}))
        c.slot(RX + pad + (i % 6) * 80, top + 102 + (i // 6) * 80, 72, label=None if it else n, **it)
    yours(c, RX, top + worn_h + 24)
    c.prompts(960, 1000, [('Click', 'Put on the anvil'), ('Enter', 'Work it'), ('Hold Del', 'Break down'), ('Esc', 'Close')])
    return c


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, fn in [('self', self_page), ('pack', pack_page), ('storeroom', storeroom_page), ('trader', trader_page), ('bench', bench_page)]:
        fn().save(os.path.join(out, f'greybox_{name}.png'))
        print('drew', name)
