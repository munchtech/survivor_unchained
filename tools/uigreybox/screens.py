"""The greyboxes: Self, Pack, Storeroom, Trader and the bench, at 1920x1080.
python screens.py OUTDIR [--notes]"""
import os
import sys
from gb import *

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
NOTES = '--notes' in sys.argv
BOOK = ['Pack', 'Self', 'Arts', 'Journal', 'Map']
KEYS = ['I', 'C', 'K', 'J', 'M']


def page_head(c, title, sub, on):
    """A page of the day's book: its head band (with the foot band, the screen's one frame)."""
    c.rect(0, 0, 1920, 88, BAND)
    c.rule(0, 88, 1920, (96, 90, 80))
    c.text(36, 30, '[', UI_B, 16, DIM)
    x = c.tabs(60, 28, BOOK, on, KEYS)
    c.text(x - 6, 30, ']', UI_B, 16, DIM)
    c.text(960, 22, title, DISPLAY, 34, INK, anchor='ma')
    if sub:
        c.text(960, 64, sub, TEXT_I, 16, DIM, anchor='ma')
    c.button(1784, 26, 'Close', key='Esc', w=100)
    c.rect(0, 1040, 1920, 40, BAND)
    c.rule(0, 1040, 1920, (96, 90, 80))


def side_panel(c, x, w, title, on=None, close=True):
    """A side panel: the screen's one frame; the world stays in view beside it."""
    c.rect(x, 16, w, 1048, PANEL)
    c.frame(x, 16, w, 1048)
    if on is not None:
        c.tabs(x + 28, 38, BOOK, on, KEYS, size=16)
    if close:
        c.button(x + w - 128, 32, 'Close', key='I' if on == 0 else 'Esc', w=100)
    c.text(x + w / 2, 84, title, DISPLAY, 30, INK, anchor='ma')


def world(c, x0, x1, figure_at=None):
    c.rect(x0, 0, x1 - x0, 1080, WORLD)
    c.text((x0 + x1) / 2, 60, 'THE WORLD, LIVE', UI_H, 16, (86, 90, 94), anchor='ma')
    if figure_at:
        c.figure(figure_at[0], figure_at[1], 150, label=None, fill=(92, 94, 98))


# ---------------------------------------------------------------------------------------- Self
def self_page(preview=True):
    c = Canvas()
    page_head(c, 'WREN', 'Level 4 Hunter Warden', 1)
    # Her, large: the page's hero, standing on the left.
    c.figure(330, 128, 820)
    c.text(330, 968, 'Level 4', DISPLAY, 24, INK, anchor='ma')
    c.rect(150, 1004, 360, 6, (24, 24, 26), r=3)
    c.rect(150, 1004, 204, 6, (120, 160, 210), r=3)
    c.text(520, 999, '340 / 600', UI_B, 14, DIM)
    c.text(330, 1016, 'Warden · Hunter · knows Beastlore', TEXT_I, 15, DIM, anchor='ma')
    X, W = 700, 1180

    # Attributes: one tight row, with the spend and its preview.
    c.section(X, 116, W, 'Attributes', 'more with each level', '2 points to spend' if preview else None)
    attrs = [('Might', 6, '+2.5% damage, +4 health a point'), ('Finesse', 3, '+0.6% critical chance, +1% speed'),
             ('Wits', 3, '+1% weapon speed, +2% area and ember'), ('Resolve', 6, '+3 health, +0.5 armour, +0.08 regeneration')]
    cw = (W - 3 * 16) / 4
    for i, (n, v, per) in enumerate(attrs):
        x = X + i * (cw + 16)
        c.panel(x, 144, cw, 128)
        pv = preview and i == 0
        c.text(x + 22, 154, f'{v}', DISPLAY, 50, INK)
        if pv:
            ax = x + 22 + c.width(f'{v}', DISPLAY, 50) + 10
            c.arrow(ax, 192, 22, GOOD, 3)
            c.text(ax + 36, 168, '7', DISPLAY, 34, GOOD)
        c.text(x + 22, 218, n.upper(), DISPLAY_L, 18, (210, 196, 160))
        c.text(x + 22, 244, per, UI, 14, DIM)
        if preview:
            # A free point: the plus, and (one pressed) the minus to take it back.
            c.rect(x + cw - 52, 158, 34, 34, (64, 46, 28), outline=EMBER, r=17)
            c.text(x + cw - 35, 175, '+', UI_H, 22, (255, 228, 190), anchor='mm')
            if pv:
                c.rect(x + cw - 92, 158, 34, 34, (46, 46, 50), outline=(80, 80, 86), r=17)
                c.text(x + cw - 75, 175, '–', UI_H, 22, INK2, anchor='mm')
    if preview:
        c.button(X + W - 254, 284, 'Undo', w=110)
        c.button(X + W - 132, 284, 'Confirm', primary=True, w=132)
        c.text(X, 294, 'Spending previews every number it changes below, green where it rises.', TEXT_I, 15, DIM)

    # Traits: a level track, taken, next, later; deeds' traits as chips.
    ty = 350
    c.section(X, ty, W, 'Traits', 'one of three at every second level, and some given for what you do')
    levels = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    x0, x1, yy = X + 40, X + 860, ty + 64
    c.rule(x0, yy, x1, (70, 70, 76))
    step = (x1 - x0) / (len(levels) - 1)
    for i, lv in enumerate(levels):
        x = x0 + i * step
        if lv == 2:
            c.d.ellipse((x - 22, yy - 22, x + 22, yy + 22), fill=(110, 100, 84), outline=(200, 180, 130), width=2)
            c.text(x, yy, 'ic', UI_H, 13, (40, 36, 30), anchor='mm')
            c.text(x, yy + 32, 'Steady Hand', UI_B, 15, INK, anchor='ma')
            c.text(x, yy + 52, 'level 2', UI, 13, DIM, anchor='ma')
        elif lv == 4:
            c.d.ellipse((x - 22, yy - 22, x + 22, yy + 22), fill=(40, 30, 22), outline=EMBER, width=3)
            c.text(x, yy, '4', DISPLAY, 18, (255, 220, 170), anchor='mm')
            c.text(x, yy + 32, 'Next: level 4', UI_B, 15, EMBER, anchor='ma')
            c.text(x, yy + 52, 'one of three', UI, 13, DIM, anchor='ma')
        else:
            c.d.ellipse((x - 7, yy - 7, x + 7, yy + 7), fill=(56, 56, 62))
            c.text(x, yy + 18, f'{lv}', UI_B, 13, FAINT, anchor='ma')
    c.text(X + 920, ty + 34, 'GIVEN FOR DEEDS', UI_H, 13, DIM)
    cx = X + 920
    for n in ('Wolfsbane', 'Lamp-lit'):
        cx += c.chip(cx, ty + 56, n) + 8

    # Stats: three aligned columns.
    sy = 490
    c.section(X, sy, W, 'Standing', 'hover a number: where it comes from')
    cols = [
        [('STAYING ALIVE', [('Health', '212', '+4'), ('Armour', '8 · 29% less', None), ('Regeneration', '0.7 a second', None), ('Healing', '+18%', None), ('Dodge', '0%', None)]),
         ('WARDING', [('Fire', '12%', None), ('Frost', '22%', None), ('Storm', '0%', None), ('Venom', '0%', None)])],
        [('DEALING DEATH', [('Damage', '+15%', '+2.5%'), ('Critical chance', '6%', None), ('Critical damage', '×1.5', None), ('Weapon speed', '+3% faster', None), ('Area', '+6%', None)]),
         ('THE ART IN HAND', [('Shield Bash', 'rank II', None), ('Strength', '+6%', None), ('Wait', '7 s', None)])],
        [('MOVING', [('Speed', '5.2', None), ('Dashes', '2', None), ('Reach for what falls', '2.4 m', None)]),
         ('FORTUNE', [('Experience', '+6%', None), ('Gold found', '0%', None)])],
    ]
    colw = (W - 2 * 48) / 3
    for ci, groups in enumerate(cols):
        x = X + ci * (colw + 48)
        y = sy + 36
        for gname, rows in groups:
            c.text(x, y, gname, UI_H, 13, (200, 186, 150))
            y += 26
            for (label, val, delta) in rows:
                c.d.rectangle((x, y + 4, x + 12, y + 16), fill=(70, 70, 76))
                c.text(x + 22, y, label, UI, 17, INK2)
                vx = x + colw - (52 if preview else 0)
                c.text(vx, y, val, UI_B, 17, INK, anchor='ra')
                if preview and delta:
                    c.text(x + colw, y, delta, UI_B, 15, GOOD, anchor='ra')
                c.rule(x, y + 27, x + colw, (40, 40, 44))
                y += 32
            y += 18
    c.prompts(960, 1049, [('Arrows', 'Move'), ('Enter', 'Spend a point'), ('Bksp', 'Take it back'), ('[ ]', 'Turn the page'), ('Esc', 'Close')])
    if NOTES:
        c.note(700, 1020, 'No frames inside: tone, spacing, type and rules only. The figure is the page.')
    return c


# ---------------------------------------------------------------------------------------- Pack
PX, PW = 864, 1040  # the side panel


def pack_grid(c, x, y, items, title='Carried', count='8 of 24', sort=True):
    c.section(x, y, 484, title, count, 'Sort' if sort else None, INK2)
    w, h = c.grid(x, y + 30, 6, 4, items=items, s=72, gap=8, pad=6)
    return y + 30 + h


def pouch(c, x, y, stacks):
    c.section(x, y, 484, 'The pouch', 'materials, never in the pack')
    for i, (n, q, r) in enumerate(stacks):
        c.slot(x + i * 64, y + 30, 56, item=n, rarity=r, qty=q)
    return y + 30 + 56


PACK_ITEMS = {(0, 0): dict(item='dr', rarity=0, qty=3), (1, 0): dict(item='ch', rarity=2), (2, 0): dict(item='hm', rarity=3, focus=True),
              (3, 0): dict(item='rg', rarity=1), (4, 0): dict(item='bw', rarity=1), (5, 0): dict(item='st', rarity=2),
              (0, 1): dict(item='am', rarity=0), (1, 1): dict(item='cl', rarity=3)}


def pack_page(tooltip=True):
    c = Canvas(WORLD)
    world(c, 0, PX - 4, figure_at=(430, 470))
    side_panel(c, PX, PW, 'Pack', on=0)
    # The doll: her figure with her gear where it is worn.
    dx, dw = PX + 32, 470
    c.panel(dx, 140, dw, 740, (31, 31, 34))
    fx = dx + dw / 2
    c.figure(fx, 170, 680, label='her, live 3D')
    s = 76
    # Down her right side (screen left): head, cloak at the shoulders, body, the relic at her belt;
    # down her left: the amulet at her throat, the weapon and off-hand at her hands, the rings below.
    left = [('HEAD', 176, None), ('CLOAK', 296, dict(item='cl', rarity=1)), ('BODY', 416, dict(item='ch', rarity=0)), ('RELIC', 536, None)]
    right = [('AMULET', 236, None), ('WEAPON', 356, dict(item='sw', rarity=1)), ('OFF-HAND', 476, dict(item='sh', rarity=0)),
             ('RING', 596, None), ('RING', 696, None)]
    for name, y, it in left:
        c.slot(dx + 18, y, s, label=name, **(it or {}))
    for name, y, it in right:
        c.slot(dx + dw - 18 - s, y, s, label=name, **(it or {}))
    # Six numbers that matter, aligned.
    nums = [('Health', '212'), ('Armour', '8 · 29%'), ('Damage', '+15%'), ('Critical', '6%'), ('Speed', '5.2'), ('Regeneration', '0.7/s')]
    for i, (n, v) in enumerate(nums):
        col, row = i % 2, i // 2
        x = dx + 18 + col * 226
        y = 900 + row * 34
        c.text(x, y, n, UI, 17, DIM)
        c.text(x + 206, y, v, UI_B, 17, INK, anchor='ra')
        c.rule(x, y + 27, x + 206, (44, 44, 48))
    # The pack, beside the doll.
    gx = PX + 534
    y = pack_grid(c, gx, 140, PACK_ITEMS)
    y = pouch(c, gx, y + 36, [('pl', 4, 0), ('sh', 6, 1), ('hd', 2, 0)])
    c.section(gx, y + 36, 484, 'Purse')
    c.text(gx, y + 64, '25 gold', DISPLAY, 26, (230, 196, 120))
    c.prompts(PX + PW / 2, 1020, [('Rclick', 'Wear or use'), ('Drag', 'Move'), ('Shift', 'Compare'), ('Del', 'Hold: break down')])
    if tooltip:
        # Hovering the helm: the cards open on the world's side, so the doll stays in view; the
        # piece's card nearest, the one worn beside it.
        c.tooltip(PX - 14 - 330, 200, 330, 'Iron Helm of the Salamander', 3, 'Epic helm · level 4', ['Armour 7', '+33% fire resistance', '+8 health'],
                  foot='Rclick: wear   ·   Hold Del: break down', deltas=['+4', '+21%', '+8'])
        c.tooltip(PX - 14 - 330 - 16 - 290, 228, 290, 'Leather Cap', 0, 'Common helm', ['Armour 3', '+12% fire resistance'], head='Worn now')
    if NOTES:
        c.note(PX + 30, 1000, 'One frame: the panel. Empty slots: a quiet tile and the name of what goes there.')
    return c


# ----------------------------------------------------------------------------------- Storeroom
def two_panels(c, title_left, mid_figure=True):
    world(c, 0, 1920, figure_at=(960, 470) if mid_figure else None)


def storeroom_page():
    c = Canvas(WORLD)
    world(c, 0, 1920, figure_at=(960, 470))
    LX, RX, W = 16, 1304, 600
    side_panel(c, LX, W, "Rook's storeroom", close=False)
    c.text(LX + W / 2, 126, 'Kept safe, whatever becomes of you', TEXT_I, 16, DIM, anchor='ma')
    c.tabs(LX + 58, 168, ['Shelf I', 'Shelf II'], 0)
    stored = {(0, 0): dict(item='ax', rarity=2), (1, 0): dict(item='rg', rarity=3), (2, 0): dict(item='bt', rarity=1), (3, 0): dict(item='hm', rarity=0),
              (4, 0): dict(item='am', rarity=1), (5, 0): dict(item='bk', rarity=0), (0, 1): dict(item='cl', rarity=1), (1, 1): dict(item='st', rarity=2),
              (2, 1): dict(item='pt', rarity=0, qty=5), (3, 1): dict(item='ch', rarity=4), (4, 1): dict(item='rl', rarity=1)}
    y = pack_grid(c, LX + 58, 212, stored, 'Stored', '11 of 24')
    c.button(LX + 58, y + 24, 'A third shelf from Rook · 300 gold', w=484)
    side_panel(c, RX, W, 'Your pack')
    y = pack_grid(c, RX + 58, 140, PACK_ITEMS)
    y = pouch(c, RX + 58, y + 36, [('pl', 4, 0), ('sh', 6, 1), ('hd', 2, 0)])
    c.text(RX + 58, y + 30, '25 gold', DISPLAY, 24, (230, 196, 120))
    c.prompts(960, 1020, [('Rclick', 'Move across'), ('Drag', 'Move'), ('Shift', 'Compare'), ('[ ]', 'Shelf'), ('Esc', 'Close')])
    c.button(RX + W - 128, 32, 'Close', key='Esc', w=100)
    if NOTES:
        c.note(LX + 30, 1000, 'Theirs on the left, yours on the right, the same grid. Room grows by shelves, not empty cells.')
    return c


# -------------------------------------------------------------------------------------- Trader
def trader_page():
    c = Canvas(WORLD)
    world(c, 0, 1920, figure_at=(1010, 470))
    LX, W, RX = 16, 660, 1304
    c.rect(LX, 16, W, 1048, PANEL)
    c.frame(LX, 16, W, 1048)
    # The merchant, compact: who, how they deal, what they last said.
    c.rect(LX + 32, 40, 112, 112, (64, 64, 70), r=56)
    c.text(LX + 88, 96, 'face', UI_B, 14, (100, 100, 108), anchor='mm')
    c.text(LX + 164, 46, 'Harlan Coyle', DISPLAY, 28, INK)
    c.text(LX + 164, 88, 'Coyle Trading Post · a stranger · his usual prices', UI, 15, DIM)
    c.wrap(LX + 164, 112, '"His caravan never came. His nephew was driving it."', TEXT_I, 17, INK2, W - 200)
    c.tabs(LX + 32, 186, ['Wares', 'Buy back · 2'], 0)
    c.text(LX + W - 32, 190, 'new stock in 2 days', TEXT_I, 15, FAINT, anchor='ra')
    wares = {(0, 0): dict(item='dr', rarity=0, qty=4, price=30), (1, 0): dict(item='bd', rarity=0, qty=3, price=12), (2, 0): dict(item='vl', rarity=0, qty=2, price=45),
             (3, 0): dict(item='ck', rarity=1, price=120), (4, 0): dict(item='rg', rarity=1, price=160), (5, 0): dict(item='am', rarity=2, price=420, dear=True, focus=True),
             (0, 1): dict(item='bw', rarity=1, price=140), (1, 1): dict(item='hm', rarity=0, price=60)}
    gx = LX + 32
    c.grid(gx, 230, 7, 2, items=wares, s=76, gap=8, pad=6)
    c.text(gx, 430, 'He buys materials, draughts, trophies, rings, amulets and cloaks, at 35% of their worth.', TEXT_I, 15, DIM)
    c.text(gx, 456, 'What he will not buy is dimmed in your pack.', TEXT_I, 15, DIM)
    # Yours.
    c.rect(RX, 16, 600, 1048, PANEL)
    c.frame(RX, 16, 600, 1048)
    c.text(RX + 300, 40, 'Your pack', DISPLAY, 30, INK, anchor='ma')
    c.button(RX + 600 - 128, 32, 'Close', key='Esc', w=100)
    y = pack_grid(c, RX + 58, 110, PACK_ITEMS)
    y = pouch(c, RX + 58, y + 36, [('pl', 4, 0), ('sh', 6, 1), ('hd', 2, 0)])
    c.text(RX + 58, y + 30, '25 gold', DISPLAY, 24, (230, 196, 120))
    c.tooltip(gx + 6 + 5 * 84 + 84, 236, 330, 'Bone Amulet of Dawn', 2, 'Rare amulet', ['+13% frost damage', '+6% experience'],
              foot='420 gold: 395 more than you have')
    c.prompts(960, 1020, [('Rclick', 'Buy or sell'), ('Drag', 'Across'), ('Shift', 'Compare'), ('Tab', 'Buy back'), ('Esc', 'Close')])
    if NOTES:
        c.note(LX + 30, 1000, 'Prices sit on the tiles; red where you cannot pay. No inspect panel: the card and its compare.')
    return c


# --------------------------------------------------------------------------------------- Bench
def bench_page():
    c = Canvas()
    c.rect(0, 0, 1920, 88, BAND)
    c.rule(0, 88, 1920, (96, 90, 80))
    c.text(960, 22, "BRANNOC'S SMITHY", DISPLAY, 34, INK, anchor='ma')
    c.text(960, 64, 'Brannoc, blacksmith', TEXT_I, 16, DIM, anchor='ma')
    c.button(1784, 26, 'Close', key='Esc', w=100)
    c.rect(0, 1040, 1920, 40, BAND)
    c.rule(0, 1040, 1920, (96, 90, 80))
    # The person, compact.
    X0 = 40
    c.rect(X0, 116, 400, 300, (64, 64, 70), r=4)
    c.text(X0 + 200, 266, 'portrait (live 3D)', UI_B, 14, (100, 100, 108), anchor='mm')
    c.text(X0, 432, 'Brannoc', DISPLAY, 28, INK)
    c.text(X0, 472, 'warm to you · his usual prices', UI, 15, DIM)
    c.wrap(X0, 504, '"Forge is hot. Show me." He wipes his hands on the apron, and the apron makes them dirtier. (the story\'s narration runs to about 250 letters)', TEXT_I, 17, INK2, 400)
    c.section(X0, 640, 400, 'His terms', 'his respect 5')
    for i, (t, l) in enumerate([('He takes his time over it.', 'His crafts cost up to 1 heat less, at respect 20'), ('He has iron to spare for you.', 'Tempering takes 1 old iron less, at respect 40')]):
        c.text(X0 + 20, 676 + i * 56, t, TEXT_I, 16, DIM)
        c.text(X0 + 20, 698 + i * 56, l, UI, 14, FAINT)
    c.vrule(470, 116, 1020)
    # The anvil.
    AX, AW = 500, 900
    c.slot(AX, 116, 96, item='sw', rarity=1)
    c.text(AX + 116, 118, 'Worn Oathblade', TEXT_B, 26, RARITY[1])
    c.text(AX + 116, 154, 'Uncommon sword', UI, 15, DIM)
    for i in range(6):
        c.rect(AX + 116 + i * 70, 184, 64, 12, EMBER if i < 4 else (50, 44, 40), r=2)
    c.text(AX + 116 + 6 * 70 + 10, 182, 'Heat 4 of 6', UI_B, 15, INK2)
    c.section(AX, 236, AW, 'Its seams', 'choose one to work')
    seams = [('Prefix', 'of the Wolf: +10% damage to beasts', True), ('Suffix', 'open: a seam waiting', False), ('Socket', 'locked: remake on a better pattern', False)]
    for i, (k, t, on) in enumerate(seams):
        y = 268 + i * 52
        c.rect(AX, y, AW, 46, (44, 40, 36) if on else (32, 32, 35), outline=EMBER if on else None, r=3)
        c.text(AX + 18, y + 23, k.upper(), UI_H, 13, DIM, anchor='lm')
        c.text(AX + 120, y + 23, t, UI_B if on else UI, 17, INK if on else DIM, anchor='lm')
    c.section(AX, 448, AW, 'What he can do with it')
    for i, (n, before, after, cost) in enumerate([('Temper', '+10%', '+14%', '1 old iron · 40 gold · 1 heat'),
                                                   ('Rework', 'of the Wolf', 'another of three', '2 old iron · 60 gold · 2 heat'),
                                                   ('Break down', '', 'old iron ×2', 'it is gone')]):
        x = AX + i * (AW / 3 + 4)
        w = AW / 3 - 12
        c.panel(x, 480, w, 196)
        c.text(x + 18, 496, n, TEXT_B, 20, INK)
        if before:
            c.text(x + 18, 534, before, UI, 16, DIM)
            c.text(x + 18 + c.width(before, UI, 16) + 8, 534, '→ ' + after, UI_B, 16, GOOD)
        else:
            c.text(x + 18, 534, 'gives ' + after, UI_B, 16, INK2)
        c.text(x + 18, 566, cost, UI, 14, DIM)
        if n == 'Break down':
            c.rect(x + 18, 620, w - 36, 38, (60, 30, 28), outline=BAD, r=4)
            c.rect(x + 18, 620, (w - 36) * 0.45, 38, (150, 60, 50), r=4)
            c.text(x + w / 2, 639, 'Hold: break down', UI_B, 16, INK, anchor='mm')
        else:
            c.button(x + 18, 620, n, primary=(i == 0), w=w - 36)
    c.vrule(1430, 116, 1020)
    GX = 1460
    c.section(GX, 116, 420, 'What you wear', 'choose a piece')
    for i, n in enumerate(['WEAPON', 'OFF-HAND', 'HEAD', 'BODY', 'CLOAK', 'AMULET', 'RING', 'RING', 'RELIC']):
        it = dict(item='sw', rarity=1, focus=True) if i == 0 else (dict(item='ch', rarity=0) if i == 3 else {})
        c.slot(GX + (i % 5) * 84, 148 + (i // 5) * 84, 76, label=None if it else n, **it)
    c.section(GX, 340, 420, 'Your pack', '8 of 24')
    c.grid(GX, 370, 5, 2, items={(0, 0): dict(item='hm', rarity=3), (1, 0): dict(item='ch', rarity=2), (2, 0): dict(item='rg', rarity=1)}, s=76, gap=8, pad=0)
    c.text(GX, 556, '+ 2 more rows: scrolls', TEXT_I, 14, FAINT)
    c.section(GX, 596, 420, 'The pouch')
    for i, (n, q) in enumerate([('ir', 4), ('pl', 4), ('sh', 6)]):
        c.slot(GX + i * 64, 626, 56, item=n, rarity=0, qty=q)
    c.text(GX, 980, '25 gold', DISPLAY, 26, (230, 196, 120))
    c.prompts(960, 1049, [('Click', 'Put on the anvil'), ('Enter', 'Work it'), ('Hold Del', 'Break down'), ('Esc', 'Close')])
    return c


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [('self', self_page), ('pack', pack_page), ('storeroom', storeroom_page), ('trader', trader_page), ('bench', bench_page)]:
        fn().save(os.path.join(OUT, f'greybox_{name}.png'))
        print('drew', name)
