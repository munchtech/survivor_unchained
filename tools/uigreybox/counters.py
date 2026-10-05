"""The counters: the storeroom, the trader and the bench, as two fitted panels with the world
(and whoever keeps the counter) live between them. Theirs on the left, yours on the right."""
from gb import *
from screens import pack_grid, pouch, world, PACK_ITEMS, NOTES

TOP = 150  # the panels' top; they are as tall as what they hold, not the screen


def fitted(c, x, y, w, h, title=None, sub=None, close=False):
    """A fitted panel: the screen's one frame, as tall as its contents."""
    c.rect(x, y, w, h, PANEL)
    c.frame(x, y, w, h)
    if title:
        c.text(x + w / 2, y + 24, title, DISPLAY, 30, INK, anchor='ma')
    if sub:
        c.text(x + w / 2, y + 66, sub, TEXT_I, 16, DIM, anchor='ma')
    if close:
        c.button(x + w - 120, y + 20, 'Close', key='Esc', w=100)


def yours(c, x, w=600, top=TOP):
    """Your side of any counter: the pack, the pouch, the purse."""
    pad = (w - 484) / 2
    y = pack_grid(c, x + pad, top + 84, PACK_ITEMS)
    y = pouch(c, x + pad, y + 32, [('pl', 4, 0), ('sh', 6, 1), ('hd', 2, 0)])
    c.text(x + pad, y + 28, '25 gold', DISPLAY, 24, (230, 196, 120))
    return y + 28 + 30 + 28 - top


def counter(c, prompts):
    c.prompts(960, 1000, prompts)


def storeroom_page():
    c = Canvas(WORLD)
    world(c, 0, 1920, figure_at=(960, 420))
    LX, RX, W = 40, 1280, 600
    h = 650
    fitted(c, LX, TOP, W, 550, "Rook's storeroom")
    c.text(LX + W / 2, TOP + 66, 'Kept safe, whatever becomes of you', TEXT_I, 16, DIM, anchor='ma')
    stored = {(0, 0): dict(item='ax', rarity=2), (1, 0): dict(item='rg', rarity=3), (2, 0): dict(item='bt', rarity=1), (3, 0): dict(item='hm', rarity=0),
              (4, 0): dict(item='am', rarity=1), (5, 0): dict(item='bk', rarity=0), (0, 1): dict(item='cl', rarity=1), (1, 1): dict(item='st', rarity=2),
              (2, 1): dict(item='pt', rarity=0, qty=5), (3, 1): dict(item='ch', rarity=4), (4, 1): dict(item='rl', rarity=1)}
    y = pack_grid(c, LX + 58, TOP + 110, stored, 'Shelf I', '11 of 24', sort=True)
    c.text(LX + 58, y + 26, 'A second shelf', UI_B, 16, DIM)
    c.text(LX + 58 + 128, y + 27, 'from Rook, 300 gold', TEXT_I, 15, FAINT)
    fitted(c, RX, TOP, W, h, 'Your pack', close=True)
    yours(c, RX, W)
    counter(c, [('Rclick', 'Move across'), ('Drag', 'Move'), ('Shift', 'Compare'), ('[ ]', 'Shelf'), ('Esc', 'Close')])
    if NOTES:
        c.note(960, 1040, 'Theirs on the left, yours on the right, the same grid. Room grows by shelves, not empty cells.', anchor='ma')
    return c


def trader_page():
    c = Canvas(WORLD)
    world(c, 0, 1920, figure_at=(1000, 420))
    LX, W, RX = 40, 700, 1280
    h = 650
    fitted(c, LX, TOP, W, 590)
    # The merchant, compact: who, how they deal, what they last said.
    c.rect(LX + 28, TOP + 26, 96, 96, (64, 64, 70), r=48)
    c.text(LX + 76, TOP + 74, 'face', UI_B, 14, (100, 100, 108), anchor='mm')
    c.text(LX + 144, TOP + 28, 'Harlan Coyle', DISPLAY, 28, INK)
    c.text(LX + 144, TOP + 68, 'a stranger · his usual prices · new stock in 2 days', UI, 15, DIM)
    c.wrap(LX + 144, TOP + 92, '"His caravan never came. His nephew was driving it."', TEXT_I, 17, INK2, W - 180)
    c.tabs(LX + 28, TOP + 150, ['Wares', 'Buy back · 2'], 0)
    wares = {(0, 0): dict(item='dr', rarity=0, qty=4, price=30), (1, 0): dict(item='bd', rarity=0, qty=3, price=12), (2, 0): dict(item='vl', rarity=0, qty=2, price=45),
             (3, 0): dict(item='ck', rarity=1, price=120), (4, 0): dict(item='rg', rarity=1, price=160), (5, 0): dict(item='am', rarity=2, price=420, dear=True, focus=True),
             (6, 0): dict(item='bt', rarity=1, price=95), (0, 1): dict(item='bw', rarity=1, price=140), (1, 1): dict(item='hm', rarity=0, price=60),
             (2, 1): dict(item='sh', rarity=0, price=75), (3, 1): dict(item='lt', rarity=1, price=180), (4, 1): dict(item='tm', rarity=2, price=380, dear=True),
             (0, 2): dict(item='rp', rarity=0, qty=6, price=8), (1, 2): dict(item='sk', rarity=0, price=25)}
    gx = LX + 28
    gw, gh = c.grid(gx, TOP + 196, 7, 3, items=wares, s=80, gap=8, pad=6)
    yy = TOP + 196 + gh + 26
    c.text(gx, yy, 'He buys materials, draughts, trophies, rings, amulets and cloaks, at 35% of their worth;', TEXT_I, 15, DIM)
    c.text(gx, yy + 24, 'what he will not take is dimmed in your pack.', TEXT_I, 15, DIM)
    fitted(c, RX, TOP, 600, h, 'Your pack', close=True)
    yours(c, RX)
    # Hovering a ware: its card on the world's side, its price said plainly.
    th = c.tooltip(LX + W + 20, TOP + 190, 330, 'Bone Amulet of Dawn', 2, 'Rare amulet', ['+13% frost damage', '+6% experience'],
                   foot='420 gold: 395 more than you have', deltas=['+13%', '+6%'])
    c.tooltip(LX + W + 20, TOP + 190 + th + 14, 330, 'Wolf-tooth Amulet', 0, 'Common amulet', ['+5% gold found'], head='Worn now')
    counter(c, [('Rclick', 'Buy or sell'), ('Drag', 'Across'), ('Shift', 'Compare'), ('Tab', 'Buy back'), ('Esc', 'Close')])
    if NOTES:
        c.note(960, 1040, 'Prices on the tiles, red where you cannot pay. No inspect panel: the card and its compare.', anchor='ma')
    return c


def bench_page():
    c = Canvas(WORLD)
    world(c, 0, 1920, figure_at=(1060, 420))
    c.text(1060, 610, 'Brannoc at the anvil', UI_B, 15, (110, 114, 118), anchor='ma')
    LX, W, RX = 40, 860, 1280
    h = 790
    top = 100
    fitted(c, LX, top, W, h)
    # Who: a strip, not a column (he is in the world beside you).
    c.rect(LX + 28, top + 24, 84, 84, (64, 64, 70), r=42)
    c.text(LX + 132, top + 24, "Brannoc's smithy", DISPLAY, 28, INK)
    c.text(LX + 132, top + 62, 'warm to you · his usual prices · respect 5', UI, 15, DIM)
    c.wrap(LX + 132, top + 86, '"Forge is hot. Show me." He wipes his hands on the apron, and the apron makes them dirtier.', TEXT_I, 16, INK2, W - 170)
    # The anvil: the piece, its seams, what can be done.
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
    c.section(LX + 28, cy, W - 56, 'What he can do with it', 'for the prefix')
    cw = (W - 56 - 2 * 14) / 3
    for i, (n, before, after, cost) in enumerate([('Temper', '+10%', '+14%', '1 old iron · 40 gold · 1 heat'),
                                                   ('Rework', 'of the Wolf', 'one of three', '2 old iron · 60 gold · 2 heat'),
                                                   ('Break down', '', 'old iron ×2', 'the piece is gone')]):
        x = LX + 28 + i * (cw + 14)
        c.rect(x, cy + 32, cw, 168, (31, 31, 34), r=3)
        c.text(x + 16, cy + 46, n, TEXT_B, 20, INK)
        if before:
            c.text(x + 16, cy + 80, before, UI, 16, DIM)
            ax = x + 16 + c.width(before, UI, 16) + 8
            c.arrow(ax, cy + 91, 14, GOOD)
            c.text(ax + 24, cy + 80, after, UI_B, 16, GOOD)
        else:
            c.text(x + 16, cy + 80, 'gives ' + after, UI_B, 16, INK2)
        c.text(x + 16, cy + 108, cost, UI, 14, DIM)
        if n == 'Break down':
            c.rect(x + 16, cy + 146, cw - 32, 38, (60, 30, 28), outline=BAD, r=4)
            c.rect(x + 16, cy + 146, (cw - 32) * 0.45, 38, (150, 60, 50), r=4)
            c.text(x + cw / 2, cy + 165, 'Hold: break down', UI_B, 16, INK, anchor='mm')
        else:
            c.button(x + 16, cy + 146, n, primary=(i == 0), w=cw - 32)
    # His terms, one line each, at the foot.
    ty = cy + 222
    c.section(LX + 28, ty, W - 56, 'His terms', 'his respect 5')
    c.text(LX + 28, ty + 30, 'At respect 20: his crafts cost up to 1 heat less.', UI, 15, DIM)
    c.text(LX + 28, ty + 54, 'At respect 40: tempering takes 1 old iron less.', UI, 15, DIM)
    # Yours: what you wear (choose a piece), then the pack, pouch and purse.
    fitted(c, RX, top, 600, h, 'Your gear', close=True)
    pad = 58
    c.section(RX + pad, top + 84, 484, 'Worn', 'choose a piece')
    for i, n in enumerate(['WEAPON', 'OFF-HAND', 'HEAD', 'BODY', 'CLOAK', 'AMULET', 'RING', 'RING', 'RELIC']):
        it = dict(item='sw', rarity=1, focus=True) if i == 0 else (dict(item='ch', rarity=0) if i == 3 else (dict(item='cl', rarity=1) if i == 4 else {}))
        c.slot(RX + pad + (i % 6) * 80, top + 116 + (i // 6) * 80, 72, label=None if it else n, **it)
    y = pack_grid(c, RX + pad, top + 300, PACK_ITEMS, sort=False)
    y = pouch(c, RX + pad, y + 28, [('ir', 4, 0), ('pl', 4, 0), ('sh', 6, 1)])
    c.text(RX + pad + 300, y - 40, '25 gold', DISPLAY, 24, (230, 196, 120))
    counter(c, [('Click', 'Put on the anvil'), ('Enter', 'Work it'), ('Hold Del', 'Break down'), ('Esc', 'Close')])
    if NOTES:
        c.note(960, 1040, 'Brannoc stands in the world between the panels; the bench is the anvil and your gear.', anchor='ma')
    return c


if __name__ == '__main__':
    import os
    import sys
    import screens
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, fn in [('self', screens.self_page), ('pack', screens.pack_page), ('storeroom', storeroom_page), ('trader', trader_page), ('bench', bench_page)]:
        fn().save(os.path.join(out, f'greybox_{name}.png'))
        print('drew', name)
